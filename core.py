"""
The core of MIA's tasks (ui/REQUIREMENTS_CORE.md): skills (skills/*.md), the library of nodes and pipelines (library.py), the runner and the run log together.
`Core.run("research", {"text": ...})` loads the skill, takes its pipeline from the library (the highest tested or trusted version, or the one the skill pins as "id@version"),
expands it into the graph of the runner, checks that the skill may use what the pipeline needs (web access, code), runs it and logs the run with the library entries it used.
"""
import time

try:
    from . import behaviour, checks, extraction, number_gate, research, verification
    from . import skill_converter
    from .library import LibraryError
    from .pipeline import PipelineError, RunResult, Runner, Tool, reaches_internet, validate_pipeline
    from .run_log import RunLog
    from .skill_store import SkillStore
except ImportError:  # used as plain script / in tests
    import skill_converter
    import checks
    import extraction
    import behaviour
    import number_gate
    import research
    import verification
    from library import LibraryError
    from pipeline import PipelineError, RunResult, Runner, Tool, reaches_internet, validate_pipeline
    from run_log import RunLog
    from skill_store import SkillStore


class Core:
    def __init__(self, skills_dir, library, runs_dir, model=None, tools=None, functions=None, rng=None, sandbox=None, broker_factory=None, environment=None, store=None, store_texts=None,
                 tool_calls=None, door_tools=None, run_events=None, conversion_dir=None):
        """conversion_dir: the folder of the acceptance records (accept_conversion.py, D-256): a skill with a record runs on the graph path, see run; None = every skill on the old runner;
        sandbox: a sandbox.SandboxRouter (None = no scripts can run); broker_factory: makes a web broker per script (broker.WebBroker), None = scripts have no web"""
        self.skills = SkillStore(skills_dir)
        self.conversion_dir = conversion_dir
        self.library = library
        self.run_log = RunLog(runs_dir)
        tools = dict(tools or {})
        tools.setdefault("library_select", Tool(self._select, None))
        tools.setdefault("library_describe", Tool(self._describe, None))
        self.sandbox = sandbox
        functions = {**checks.OFFLINE_FUNCTIONS, **extraction.FUNCTIONS, **behaviour.FUNCTIONS, **verification.FUNCTIONS, **number_gate.FUNCTIONS, **research.FUNCTIONS, **checks.build_script_checks(sandbox, broker_factory), **(functions or {})}
        self.runner = Runner(model=model, tools=tools, functions=functions, run_log=self.run_log, rng=rng, sandbox=sandbox, broker_factory=broker_factory,
                             environment=environment, store=store,
                             store_texts=store_texts,
                             tool_calls=tool_calls, door_tools=door_tools, run_events=run_events)
        # the hard checks of the library, picked per claim (checks.CheckRunner); the web variant needs a skill that may read the web
        self.checks = checks.CheckRunner(library, lambda: self.runner.functions, lambda: list(self.runner.tools), sandbox=sandbox)
        self.runner.functions.setdefault("hard_checks_offline", lambda claim, fail_fast=True: self.checks.run(claim, include_web=False, fail_fast=fail_fast))
        self.runner.functions.setdefault("hard_checks_web", lambda claim, fail_fast=True: self.checks.run(claim, include_web=True, fail_fast=fail_fast))

    # -- the library as tools for planning steps (reading only; new entries are drafts made by people or on request) --
    def _select(self, entry_type="pipeline", tags=(), applies_to=None, max_seconds=None, task=None):
        return self.library.select(entry_type, tags=tags, applies_to=applies_to, max_seconds=max_seconds, task=task, tools=self.runner.tools,
                                   sandbox=self.sandbox is not None and self.sandbox.available)

    def _describe(self, ref, entry_type="pipeline"):
        entry = self.library.resolve(ref, entry_type, allow_draft=True)
        return {k: v for k, v in entry.items() if not k.startswith("_")}

    def graph(self, skill):
        """(graph, uses, safety) of the pipeline the skill names; raises PipelineError"""
        try:
            entry = self.library.resolve(skill["pipeline"], "pipeline")
            graph, uses, safety = self.library.expand(entry)
        except LibraryError as exc:
            raise PipelineError(str(exc))
        allowed = skill.get("max_safety") or {}
        for flag, needed in safety.items():
            if needed and not allowed.get(flag):
                raise PipelineError("the pipeline '%s' needs '%s', which the skill '%s' does not allow (max_safety)" % (skill["pipeline"], flag, skill["name"]))
        return graph, uses, safety

    def check(self, functions=None):
        """the problems of every skill with its pipeline: {skill name: [problems]} (skills without problems are left out); file errors under their path"""
        self.skills.reload()
        found = {path: [message] for path, message in self.skills.errors.items()}
        found.update({path: [message] for path, message in self.library.errors.items()})
        all_functions = {**self.runner.functions, **(functions or {})}
        for name in self.skills.names():
            skill = self.skills.skills[name]
            try:
                graph = self.graph(skill)[0]
                problems = validate_pipeline(graph, tools=self.runner.tools, functions=all_functions, skill=skill)
            except PipelineError as exc:
                problems = [str(exc)]
            if problems:
                found[name] = problems
        return found

    def run(self, task, inputs, pipeline=None, **kwargs):
        """runs the skill of the task; `pipeline` ("research.decompose@1") runs another pipeline of the library under the skill's settings"""
        skill = self.skills.get(task)
        if skill is None:
            raise PipelineError("there is no skill '%s'" % task)
        if pipeline:
            skill = dict(skill, pipeline=pipeline)
        graph = self.graph(skill)[0]
        # a skill with an acceptance record that still fits the skill file, the pipeline and the run file runs as a graph (D-257, F-02); a variant (`pipeline=`) is not the accepted skill, so it stays on the old runner
        if not pipeline and self.conversion_dir and task in skill_converter.bound_checks(self.conversion_dir, self.skills.folder, self.library.shipped_dir):
            converted = self._run_converted(task, skill, graph, inputs, **kwargs)
            if converted is not None:
                return converted
        return self.runner.run(skill, graph, inputs, task=task, **kwargs)

    def _run_converted(self, task, skill, graph, inputs, on_event=None, should_stop=None, ask=None, functions=None, tools=None, started_by="message", user="mia", **unused):
        """the run of an accepted skill on the graph path with the guards and the record of the old runner: the trust rule of REQ-RUN-001, the validation of the pipeline, a run log record, a
        result of the old shape. What it lacks so far: the events of single nodes (only run_start, run_end and the tool events), a stop in the middle of a top-level step, the
        cost of tokens and steps. A pipeline that cannot be converted gives None: the old runner runs the skill."""
        if started_by == "message" and reaches_internet(skill):
            raise PipelineError("'%s' reaches the internet and starts only by a command, not by a chat message" % skill.get("name"))
        all_tools = {**self.runner.tools, **{k: v if isinstance(v, Tool) else Tool(v, None) for k, v in (tools or {}).items()}}
        problems = validate_pipeline(graph, tools=all_tools, functions={**self.runner.functions, **(functions or {})}, skill=skill)
        if problems:
            raise PipelineError("; ".join(problems))
        if ask is not None and any(node.get("kind") == "ask_user" for node in graph["nodes"]):
            return None
        started = time.monotonic()
        record = self.run_log.start(task, skill["name"], skill["version"], skill["pipeline"], None, (skill["model"] or {}).get("name") or (skill["model"] or {}).get("profile"), inputs)
        if should_stop is not None and should_stop():
            ended = None
        else:
            try:
                ended = skill_converter.run_converted(task, inputs, model=self.runner.model, tools=all_tools, skills_dir=self.skills.folder, library_dir=self.library.shipped_dir,
                                                      sandbox=self.sandbox, broker_factory=self.runner.broker_factory, tool_calls=self.runner.tool_calls,
                                                      door_tools=self.runner.door_tools, should_stop=should_stop, run_id=record.id)
            except skill_converter.ConversionError:
                return None
        seconds = time.monotonic() - started
        status, error, missing, answer, events = "stopped", None, [], None, []
        if ended is not None:
            answer, events = ended.answer, list(ended.events)
            if ended.status == "done":
                status = "done"
            elif ended.status == "budget":
                key = (ended.error or "").split(":", 1)[-1].strip()
                status, error, missing = "budget", "budget exceeded: %s" % key, [key]
            elif should_stop is not None and should_stop():
                status = "stopped"
            else:
                status, error = "error", ended.error
        if on_event is not None:
            for event in [{"kind": "run_start", "plain": skill.get("description", skill["name"]), "payload": {"skill": skill["name"], "show": skill["status_block"], "nodes": []}}] + \
                    events + [{"kind": "run_end", "plain": status, "payload": {"status": status, "seconds": round(seconds, 3)}}]:
                on_event(dict(event, run=record.id))
        record.finish(status, {"answer": answer}, seconds, error)
        return RunResult(record.id, status, answer, {"input": inputs}, seconds, error, events, missing, {"seconds": round(seconds, 3), "converted": True})
