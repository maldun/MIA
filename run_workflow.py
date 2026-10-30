"""
Run a workflow of the library (IF-202) and the evaluation access of the harness (IF-105), realised by the Pipeline runner (REQ-RUN-014, REQ-RUN-015).

  run(workflow, version, inputs, budget, user, options=None)   {"run_id", "status", "outputs", "missing", "events", "cost"}
  costs(workflow, node_id)                                     the median {"seconds", "calls", "tokens"} of a node over the recorded runs, or None
  workflows()  run_case(workflow, version, inputs, options)  events(run_id)      IF-105: the same run, attributed to the user "harness", with a pinned model

A workflow is a graph document of the library (IF-203). It runs because it names its skill (`"skill"`) and may pin a pipeline of library.py (`"pipeline":
"id@version"`) other than the skill's (D-112); its process nodes carry the ids of the pipeline's nodes, so the measured costs of a node fill the estimate.
A run whose estimate exceeds the budget is refused before any model call; a run that exceeds a budget ends with what it has (REQ-RUN-008). Besides the three
statuses of IF-202 v0 a run can end `stopped` (the user) or `error` (a failing step, with `error`): a failure is a visible result, not a missing one.
"""
import statistics

try:
    from .pipeline import PipelineError
except ImportError:  # used as plain script / in tests
    from pipeline import PipelineError

KEYS = ("steps", "seconds", "calls", "tokens")
STATUS = {"done": "done", "budget": "budget_exhausted", "stopped": "stopped", "error": "error"}
REQUIRED = ("model_pin", "seed", "temperature")
HARNESS = "harness"


class RunWorkflowError(Exception):
    def __init__(self, code, detail=None):
        super().__init__("%s%s" % (code, ": %s" % detail if detail is not None else ""))
        self.code, self.detail = code, detail


class WorkflowRuns:
    def __init__(self, library, core, pins=None, held=None):
        """library: the workflow library (IF-203); core: core.Core (skills, library.py, runner, run log); pins: {pin id: {"name", "digest"}} (eval-spec.md,
        Model pins); held(): {model name: digest} the model server holds now (ollama list)"""
        self.library, self.core = library, core
        self.pins, self._held = dict(pins or {}), held or (lambda: {})
        self._events = {}                                  # run id -> the events of a run of this instance, for IF-105 events()

    # -- IF-202 ----
    def run(self, workflow, version, inputs, budget, user, options=None):
        skill, graph = self._runnable(workflow, version)
        budget = dict(budget or {})
        if options and options.get("model_pin") is not None:
            self._check_pin(options["model_pin"])
        too_big = self.library.check_budget(workflow, budget, version)["exceeded"]
        if too_big:
            return self._refused(workflow, version, user, options, too_big)
        skill = dict(skill, budget={**skill["budget"], **{k: v for k, v in budget.items() if k in KEYS}}, model=self._model(skill, options))
        result = self.core.runner.run(skill, graph, inputs, task=workflow)
        status = STATUS.get(result.status, "error")
        events = [self._event(e, result.run_id, user) for e in result.events]
        events[0].update(workflow=workflow, version=version, options=dict(options) if options else None)
        events[-1].update(status=status, missing=list(result.missing))
        self._events[result.run_id] = events
        found = {"run_id": result.run_id, "status": status, "outputs": self._outputs(result), "missing": list(result.missing), "events": events,
                 "cost": dict(result.cost)}
        if status == "error":
            found["error"] = result.error
        return found

    def costs(self, workflow, node_id):
        return self._median([run for run in self.core.run_log.read() if run.get("task") == workflow], node_id)

    def node_costs(self):
        """{node id: median costs} over all recorded runs: the costs the workflow library builds its estimate from (IF-203 `estimate`)"""
        runs = self.core.run_log.read()
        nodes = {e.get("node") for run in runs for e in run.get("events", []) if e.get("kind") == "start"}
        return {node: self._median(runs, node) for node in nodes if node}

    # -- IF-105 ----
    def workflows(self):
        ids = self.library.list_ids("workflows")
        return [{"id": i, "versions": [h["version"] for h in self.library.history("workflows", i)], "status": self.library.read("workflows", i)["status"]}
                for i in ids]

    def run_case(self, workflow, version, inputs, options):
        missing = [k for k in REQUIRED if not isinstance(options, dict) or k not in options]
        if missing:
            raise RunWorkflowError("bad_options", missing)
        result = self.run(workflow, version, inputs, options.get("budget"), HARNESS, options={k: options[k] for k in REQUIRED})
        return dict(result, options=dict(options))

    def events(self, run_id):
        if run_id not in self._events:
            raise RunWorkflowError("unknown_run")
        return list(self._events[run_id])

    # -- parts ----
    def _runnable(self, workflow, version):
        """(skill, graph of the runner) of a workflow that names a skill; anything else is unknown_workflow, before any event"""
        try:
            doc = self.library.read("workflows", workflow, version)["doc"]
        except Exception as exc:                            # the library's not_found (and a wrong kind) mean the same here
            if getattr(exc, "code", None) == "not_found":
                raise RunWorkflowError("unknown_workflow", workflow) from exc
            raise
        skill = self.core.skills.get(doc.get("skill")) if doc.get("skill") else None
        if skill is None:
            raise RunWorkflowError("unknown_workflow", "%s names no skill" % workflow)
        if doc.get("pipeline"):
            skill = dict(skill, pipeline=doc["pipeline"])
        try:
            return skill, self.core.graph(skill)[0]
        except PipelineError as exc:
            raise RunWorkflowError("unknown_workflow", str(exc)) from exc

    def _check_pin(self, pin):
        wanted, held = self.pins.get(pin), self._held()
        digest = held.get(wanted["name"]) if wanted else None
        if digest is None or not (digest.startswith(wanted["digest"]) or wanted["digest"].startswith(digest)):
            raise RunWorkflowError("pin_unavailable", pin)        # never a silent fallback to another model (IF-105)

    def _model(self, skill, options):
        model = dict(skill.get("model") or {})
        if not options:
            return model
        if options.get("model_pin") is not None:
            model["name"] = self.pins[options["model_pin"]]["name"]
        given = {k: options[k] for k in ("seed", "temperature") if options.get(k) is not None}
        if given:
            model["options"] = {**(model.get("options") or {}), **given}
        return model

    def _refused(self, workflow, version, user, options, missing):
        """a run over its estimate is logged as refused, with two events and no work (IF-202 golden 3)"""
        run = self.core.run_log.start(workflow, input=None)
        run.finish("refused", None, 0.0, "estimate over the budget: %s" % ", ".join(missing))
        frame = {"run_id": run.id, "user": user, "actor": "runner", "node": None, "payload": {}}
        events = [dict(frame, seq=1, type="run_start", plain="", workflow=workflow, version=version, options=dict(options) if options else None),
                  dict(frame, seq=2, type="run_end", plain="refused", status="refused", missing=list(missing))]
        self._events[run.id] = events
        return {"run_id": run.id, "status": "refused", "outputs": {}, "missing": list(missing), "events": events, "cost": {k: 0 for k in KEYS}}

    @staticmethod
    def _event(event, run_id, user):
        kind = event.get("kind")
        return {"seq": event.get("seq"), "type": event.get("type") if kind == "event" else kind, "run_id": run_id, "user": user, "node": event.get("node"),
                "actor": event.get("actor"), "plain": event.get("plain", ""), "payload": event.get("payload") or {}}

    @staticmethod
    def _outputs(result):
        if isinstance(result.answer, dict):
            return dict(result.answer)
        if result.answer is not None:
            return {"answer": result.answer}
        return {k: v for k, v in result.context.items() if k != "input"}     # a run that ended early keeps what its steps produced

    @staticmethod
    def _median(runs, node_id):
        found = []
        for run in runs:
            events = [e for e in run.get("events", []) if e.get("node") == node_id or e.get("actor") == node_id]
            if not any(e.get("kind") == "start" for e in events):
                continue
            calls = [e for e in events if e.get("type") == "model_call"]
            times = [e["at"] for e in events if isinstance(e.get("at"), (int, float))]
            found.append({"seconds": (max(times) - min(times)) if times else 0.0, "calls": len(calls),
                          "tokens": sum((c["payload"].get("tokens_in") or 0) + (c["payload"].get("tokens_out") or 0) for c in calls)})
        if not found:
            return None
        return {key: statistics.median(f[key] for f in found) for key in ("seconds", "calls", "tokens")}
