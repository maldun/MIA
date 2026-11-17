"""Conversion of the skills onto the new records (part skillConverter, FR-45, G-V2.CONVERT). STUBS (EquivalenceSettings is real since T-CV-02; SkillConverter, decide_acceptance and conversion_records since T-CV-03) until the tasks T-CV-03 to T-CV-08 of plan.md.

The stubs never raise and return values outside the real vocabulary (None, empty), so that the acceptance tests of G-V2.CONVERT fail on an assertion.
The signatures are the ones the red tests assume (to be confirmed by the owner at the review of the tests).
"""
import glob
import json
import os
import subprocess
import sys
import tempfile
import uuid

try:
    from . import checks, common_operations, control_flow, pipeline_graph
    from .graph_run import GraphRunner, Stage
    from .library import Library
    from .skill_store import load_skill
    from .storage import Storage
    from .storage_files import FileBackend
    from .toolbox import Toolbox, ToolboxError
    from .workflow_library import WorkflowLibrary
except ImportError:
    import checks
    import common_operations
    import control_flow
    import pipeline_graph
    from graph_run import GraphRunner, Stage
    from library import Library
    from skill_store import load_skill
    from storage import Storage
    from storage_files import FileBackend
    from toolbox import Toolbox, ToolboxError
    from workflow_library import WorkflowLibrary


class ConversionError(Exception):
    """a skill is marked converted without a passed equivalence check (REQ-WFM-057)"""


class SkillConverter:
    """Chooses per skill between the old runner and the converted record (REQ-WFM-057).

    old_loader(name) and converted_loader(name) give (skill, graph); runner.run(skill, graph, inputs, **kwargs) runs one. The converted loader is
    called only for a skill that is marked converted. A skill starts unconverted."""

    def __init__(self, old_loader, converted_loader, runner, records_dir=None):
        self.old_loader, self.converted_loader, self.runner = old_loader, converted_loader, runner
        # a skill is converted at start only when its record file says PASS (D-256); no folder, nothing converted
        self._converted = set(load_checks(records_dir)) if records_dir else set()

    def state(self, name):
        """"unconverted" or "converted" """
        return "converted" if name in self._converted else "unconverted"

    def mark_converted(self, name, check):
        """`check` is the result of decide_acceptance; anything but accepted is refused with ConversionError and the state stays"""
        if not (check.get("accepted") and check.get("verdict") == "PASS"):
            raise ConversionError("%s is not converted: its equivalence check is %s, not an accepted PASS" % (name, check.get("verdict")))
        self._converted.add(name)

    def run(self, name, inputs, **kwargs):
        """runs the old skill file and pipeline of an unconverted skill, the converted record of a converted one"""
        # the converted record is read only for a converted skill: an unproven one must not even be loaded
        loader = self.converted_loader if self.state(name) == "converted" else self.old_loader
        skill, graph = loader(name)
        return self.runner.run(skill, graph, inputs, **kwargs)


class ConvertedRun:
    """what run_converted returns: `status` of the runner, `answer` (the value of the conversion's result node), `values` (all data nodes), `named` (the refused nodes); `error` and `events` have the shape of the old
    run result (no run events yet on this path)"""
    def __init__(self, result, answer, events=None, budget_end=None):
        self.status, self.answer, self.values, self.named = result.status, answer, result.values, getattr(result, "named", None)
        self.error, self.events = (None if result.status == "done" else "the graph run ended with %s %s" % (result.status, self.named or "")), list(events or [])
        if result.status == "failed" and budget_end:       # a budget end is no failure (T-CV-06a): the status of the old runner, the key as the reason
            self.status, self.error = "budget", "budget: %s" % budget_end


def _latest_nodes(nodes_dir):
    """{node id: JSON of its highest version} of library/nodes"""
    latest = {}
    for path in sorted(glob.glob(os.path.join(nodes_dir, "*", "*.json"))):
        with open(path, encoding="utf-8") as handle:
            node = json.load(handle)
        if node["version"] > latest.get(node["id"], {"version": 0})["version"]:
            latest[node["id"]] = node
    return latest


def run_converted(name, inputs, model=None, tools=None, skills_dir=None, library_dir=None, runs_dir=None, skill_changes=None, functions=None, sandbox=None, broker_factory=None, tool_calls=None, door_tools=None, should_stop=None, run_id=None):
    """REQ-WFM-058, REQ-WFM-115 (A-125, D-253): runs skill `name` as a graph on the toolbox with the given model and tools. The pipeline is converted in memory at every call,
    bound to the skill and run by the GraphRunner; `skill_changes` is merged into the skill first (a test plants a changed option with it). `runs_dir` stays unused:
    this path writes no run record yet. `run_id` (F-06) is the id the IF-402 door sees: the app gives the id of the run log record, so the door's events tie to it. Returns a ConvertedRun; a pipeline that cannot be converted raises ConversionError (the skill stays on the old runner)."""
    skill = load_skill(os.path.join(skills_dir, name + ".md"))
    pipeline = Library(library_dir).resolve(skill["pipeline"], "pipeline")
    nodes = _latest_nodes(os.path.join(library_dir, "nodes"))
    found = pipeline_graph.convert({k: v for k, v in pipeline.items() if not k.startswith("_")}, nodes, (skill.get("budget") or {}).get("seconds", 300))
    if found["graph"] is None:
        raise ConversionError("%s cannot be converted: %s" % (name, found["refused"]))
    graph = pipeline_graph.bind_skill(found["graph"], nodes, skill, skill_changes)
    setting = {**(skill.get("model") or {}), **((skill_changes or {}).get("model") or {})}
    # the registries are process-wide: a run starts from what this call hands over
    common_operations.reset()
    if model is not None:
        common_operations.register_model(setting.get("profile"), model)
    # a tool is a function or a Tool(func, budget_key) as the old runner takes it; a tool of the IF-402 door (`tool_calls`, `door_tools` = {name: budget key}) has no function here
    keys = dict(door_tools or {})
    for tool_name, function in (tools or {}).items():
        if hasattr(function, "budget_key"):
            keys.setdefault(tool_name, function.budget_key)
            function = function.func
        if function is not None:
            common_operations.register_tool(tool_name, function)
    budget = {**(skill.get("budget") or {}), **((skill_changes or {}).get("budget") or {})}
    common_operations.register_run(budget=budget, tool_keys={n: k for n, k in keys.items() if k}, door=tool_calls, door_tools=door_tools, run_id=run_id or "converted-" + uuid.uuid4().hex[:8])
    # script_check is the function of the old runner (checks.make_script_check) on the router the caller hands over (T-CV-07a, D-259): no router, no script runs and the check says so;
    # `functions` binds more app-built functions (and may replace these) for this run only
    for function_name, function in {**checks.build_script_checks(sandbox, broker_factory), **(functions or {})}.items():
        common_operations.bind(function_name, function)
    with tempfile.TemporaryDirectory(prefix="converted-run-") as folder:
        box = Toolbox(WorkflowLibrary(Storage(FileBackend(folder))), lambda account: True, _NoEvents())
        box.seed_shipped(os.path.join(library_dir, "nodes"))
        box.seed_controls()
        common_operations.register_control(_node_call(box, nodes, setting), control_flow.Limits(seconds=budget.get("seconds"), steps=budget.get("steps"), should_stop=should_stop))
        stages, trust = stages_from_toolbox(graph, box)
        result = GraphRunner(trust).run(graph, stages, {"input." + field: value for field, value in (inputs or {}).items()})
    return ConvertedRun(result, result.values.get(found["result"]), common_operations.run_events(), common_operations.budget_end())


def _node_call(box, library_nodes, model_setting):
    """`call(use, args)` of the controllers (D-258): runs the library node `use` through its toolbox entry, so trust and lifecycle count, with the descriptor of the model or the tool
    that a top-level step gets from bind_skill"""
    def call(use, args):
        tid = str(use).split("@")[0]
        library = library_nodes[tid]
        inputs = dict(args)
        if library.get("kind") == "model":
            inputs["model"] = {"model": model_setting.get("profile"), "options": model_setting.get("options") or {}}
        elif library.get("kind") == "tool":
            inputs["tool"] = {"tool": library["body"]["tool"], "settings": {}}
        try:
            return box.run_stage(tid, inputs, {}, {})
        except ToolboxError as error:
            if error.code != "no_stage":
                raise
        return box.run(tid, inputs)
    return call


class _NoEvents:
    """the toolbox reports changes to its events; a converted run in memory has no listener"""
    def record(self, event):
        return None


EVAL_DECIDE = os.path.expanduser("~/.claude/skills/agent-app/scripts/eval_decide.py")


def decide_acceptance(run_path, criterion, rerun_path=None):
    """decides the criterion line on the run files with eval_decide.py of the agent-app skill and applies the acceptance rule (REQ-WFM-059).
    Returns {"verdict": "PASS" | "FAIL" | "NOT DECIDED", "accepted": bool, "reason": str}; only PASS is accepted; a FAIL counts after the re-run (`rerun_path`)."""
    command = [sys.executable, EVAL_DECIDE, "--run", str(run_path), "--criterion", criterion, "--json"]
    if rerun_path:
        command += ["--rerun", str(rerun_path)]
    done = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if not done.stdout.strip():
        # a decision that cannot be made never accepts
        return {"verdict": "NOT DECIDED", "accepted": False, "reason": "eval_decide.py failed: " + (done.stderr.strip() or "no output")[-200:]}
    out = json.loads(done.stdout)
    verdict = out["verdict"]
    reason = "; ".join("%s: %s" % (name, text) for name, text, _ in out["checks"]) or "all checks passed"
    if verdict == "FAIL" and not rerun_path:
        reason += " (first run: a FAIL counts only after one re-run)"
    return {"verdict": verdict, "accepted": verdict == "PASS", "reason": reason}


# skill -> (suite that decides, requirement), eval-spec.md "Which suite belongs to which skill"
SUITE_OF = {"research": ("EV-research", "REQ-WFM-110"), "plan_question": ("EV-plans", "REQ-WFM-111"), "verify_claim": ("EV-verdicts", "REQ-WFM-112"),
            "verify_computable": ("EV-computable", "REQ-WFM-113"), "extract_claims": ("EV-extraction", "REQ-WFM-114"),
            "extract_claims_rules": ("EV-extraction", "REQ-WFM-115")}
# the owner's one reason for the nine skills without an equivalence requirement (2026-11-07)
UI_REASON = "old runner: part of the user interface (owner 2026-11-07), revisited in another goal"


def _record_file(folder, skill):
    # the skill name becomes a file name: only plain names (D-256)
    if not skill or not all(c.isalnum() or c in "_-" for c in skill):
        raise ConversionError("%r is not a skill name" % (skill,))
    return os.path.join(folder, skill + ".json")


def save_check(folder, skill, check):
    """D-256: writes the acceptance record of a skill, one JSON file per skill; only a PASS is written (REQ-WFM-057, 059)"""
    if check.get("verdict") != "PASS":
        raise ConversionError("%s is not recorded as converted: its check is %s, not PASS" % (skill, check.get("verdict")))
    path = _record_file(folder, skill)
    os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(check, fp, indent=1, ensure_ascii=False)


def load_checks(folder):
    """{skill: check} of the records in the folder; a missing folder, a damaged file, one without suite, run, pins and PASS counts as no record, so the skill stays on the old runner"""
    checks = {}
    for path in sorted(glob.glob(os.path.join(folder, "*.json"))):
        try:
            with open(path, encoding="utf-8") as fp:
                check = json.load(fp)
        except (OSError, ValueError):
            continue
        if isinstance(check, dict) and check.get("verdict") == "PASS" and all(check.get(k) for k in ("suite", "run", "pins")):
            checks[os.path.splitext(os.path.basename(path))[0]] = check
    return checks


def pipeline_ref(pipeline):
    """"id@version" of a pipeline entry of the library (what a reference without a version resolves to today)"""
    return "%s@%s" % (pipeline["id"], pipeline["version"])


def bound_checks(folder, skills_dir, library_dir):
    """F-02: the records of `load_checks` that still describe what runs: skill file at the recorded version, the same pipeline reference, a reference without a version still
    resolving to what it resolved to when the record was made (`pipeline_resolved`, written by accept_conversion.py; an older record has none and is checked on the reference
    alone), and the run file of the record on disk. Anything else counts as no record, so the skill goes back to the old runner until the owner accepts it again."""
    root = os.path.dirname(os.path.abspath(__file__))
    library = Library(library_dir)
    bound = {}
    for name, check in load_checks(folder).items():
        try:
            skill = load_skill(os.path.join(skills_dir, name + ".md"))
            if check.get("skill_version") != skill["version"] or check.get("pipeline") != skill["pipeline"]:
                continue
            if check.get("pipeline_resolved") and check["pipeline_resolved"] != pipeline_ref(library.resolve(skill["pipeline"], "pipeline")):
                continue
        except Exception:                                  # a skill file or pipeline that cannot be read is no match
            continue
        if not os.path.isfile(os.path.join(root, check["run"])):         # an absolute path stays absolute
            continue
        bound[name] = check
    return bound


def criterion_of(requirement, requirements_path):
    """the `Eval criterion:` line of a requirement such as REQ-WFM-111 in the requirements file of the node"""
    with open(requirements_path, encoding="utf-8") as fp:
        text = fp.read()
    start = text.find("### %s " % requirement)
    if start < 0:
        raise ConversionError("%s is not in %s" % (requirement, requirements_path))
    section = text[start:].split("\n### ", 1)[0]
    for line in section.splitlines():
        if line.startswith("- Eval criterion:"):
            return line.split(":", 1)[1].strip()
    raise ConversionError("%s has no Eval criterion line" % requirement)


def conversion_records(skills_dir, checks=None):
    """{skill name: {"form": "old" | "converted", and either "suite", "run", "pins", "verdict" or "reason"}} for every skill file of the folder (REQ-WFM-060).

    `checks` = {skill: {"suite", "run", "pins", "verdict"}} are the recorded equivalence checks; a skill is converted only with a PASS among them."""
    checks = checks or {}
    records = {}
    for file_name in sorted(os.listdir(skills_dir)):
        name, ext = os.path.splitext(file_name)
        if ext != ".md":
            continue
        if name not in SUITE_OF:
            records[name] = {"form": "old", "reason": UI_REASON}
            continue
        suite, requirement = SUITE_OF[name]
        check = checks.get(name)
        if check and all(check.get(k) for k in ("suite", "run", "pins", "verdict")):
            records[name] = {"form": "converted" if check["verdict"] == "PASS" else "old", **{k: check[k] for k in ("suite", "run", "pins", "verdict")}}
        else:
            records[name] = {"form": "old", "reason": "not converted yet: the equivalence check of %s on %s has not been run" % (requirement, suite)}
    return records


def compare_outputs(old, new):
    """REQ-WFM-115: `old` and `new` are {case id: output}; returns the list of {"case", "old", "new"} for every case whose outputs differ (empty = equal), sorted by case; a case
    that one side lacks differs, its missing output is None"""
    return [{"case": case, "old": old.get(case), "new": new.get(case)} for case in sorted(set(old) | set(new)) if case not in old or case not in new or old[case] != new[case]]


class EquivalenceSettings:
    """Versioned configuration of the equivalence check (REQ-WFM-069, D-187): margin, repeats and rule, kept in the folder `path`.

    One file per version (settings-<n>.json) and one results file; both are only appended to, so a change never reaches a result already seen (M19)."""

    DEFAULTS = {"margin": 0.10, "repeats": 3, "rule": "threshold"}      # version 1, starting guesses of the owner (2026-11-07)

    def __init__(self, path):
        self.path = path
        os.makedirs(path, exist_ok=True)
        if not self.versions():
            self._write_version({"version": 1, **self.DEFAULTS})

    def _version_file(self, number):
        return os.path.join(self.path, "settings-%d.json" % number)

    def _write_version(self, record):
        # mode "x": an existing version is never overwritten
        with open(self._version_file(record["version"]), "x", encoding="utf-8") as fp:
            json.dump(record, fp)

    def current(self):
        """the newest version, e.g. {"version": 1, "margin": 0.10, "repeats": 3, "rule": "threshold"}"""
        return self.versions()[-1]

    def versions(self):
        """every version, oldest first"""
        found = []
        number = 1
        while os.path.exists(self._version_file(number)):
            with open(self._version_file(number), encoding="utf-8") as fp:
                found.append(json.load(fp))
            number += 1
        return found

    def update(self, **changes):
        """a change creates the next version and returns it (earlier versions stay); only margin, repeats and rule can change"""
        unknown = set(changes) - set(self.DEFAULTS)
        if unknown:
            raise ValueError("unknown setting: " + ", ".join(sorted(unknown)))
        latest = self.current()
        record = {**latest, **changes, "version": latest["version"] + 1}
        self._write_version(record)
        return record

    def record_result(self, skill, verdict):
        """stores a result that names the settings version used and returns it"""
        result = {"skill": skill, "verdict": verdict, "settings_version": self.current()["version"]}
        with open(os.path.join(self.path, "results.jsonl"), "a", encoding="utf-8") as fp:
            fp.write(json.dumps(result) + "\n")
        return result

    def results(self):
        """the results in the order they were recorded; a stored result is never changed afterwards"""
        try:
            with open(os.path.join(self.path, "results.jsonl"), encoding="utf-8") as fp:
                return [json.loads(line) for line in fp if line.strip()]
        except FileNotFoundError:
            return []


def stages_from_toolbox(graph, toolbox):
    """(nodes, trust) for GraphRunner.run (A-125 Q4, D-253): `nodes` = {node id: Stage(function)} for each transform or master node, built from the toolbox entry named by its
    `toolbox_id`; `trust(node id)` = the trust of that entry. The entry is looked up when the node runs, so a trust change between two runs counts."""
    entries = {n["id"]: n["data"]["toolbox_id"] for n in graph["nodes"] if n["data"].get("type") != "data"}

    def stage_of(tid):
        def call(inputs, outputs, node):
            # an entry with `stage` wants the three-argument call; one with `run` only the inputs (the code text is never read here, the entry decides)
            try:
                return toolbox.run_stage(tid, inputs, outputs, node)
            except ToolboxError as error:
                if error.code != "no_stage":
                    raise
            return toolbox.run(tid, dict(inputs), settings=node)
        return Stage(call)

    return {node_id: stage_of(tid) for node_id, tid in entries.items()}, lambda node_id: toolbox.look_up(entries[node_id])["trust"]
