"""Conversion of the skills onto the new records (part skillConverter, FR-45, G-V2.CONVERT). STUBS (EquivalenceSettings is real since T-CV-02; SkillConverter, decide_acceptance and conversion_records since T-CV-03) until the tasks T-CV-03 to T-CV-08 of plan.md.

The stubs never raise and return values outside the real vocabulary (None, empty), so that the acceptance tests of G-V2.CONVERT fail on an assertion.
The signatures are the ones the red tests assume (to be confirmed by the owner at the review of the tests).
"""
import json
import os
import subprocess
import sys

try:
    from .graph_run import Stage
    from .toolbox import ToolboxError
except ImportError:
    from graph_run import Stage
    from toolbox import ToolboxError


class ConversionError(Exception):
    """a skill is marked converted without a passed equivalence check (REQ-WFM-057)"""


class SkillConverter:
    """Chooses per skill between the old runner and the converted record (REQ-WFM-057).

    old_loader(name) and converted_loader(name) give (skill, graph); runner.run(skill, graph, inputs, **kwargs) runs one. The converted loader is
    called only for a skill that is marked converted. A skill starts unconverted."""

    def __init__(self, old_loader, converted_loader, runner):
        self.old_loader, self.converted_loader, self.runner = old_loader, converted_loader, runner

        self._converted = set()

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


def run_converted(name, inputs, model=None, tools=None, skills_dir=None, library_dir=None, runs_dir=None, skill_changes=None):
    """STUB (REQ-WFM-058, REQ-WFM-115): runs the converted version of skill `name` on the new path with the given model and tools and returns the run
    result of the runner (status, answer, ...). `skill_changes` is merged into the skill record first (a test plants a changed option with it)."""
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
    """STUB (REQ-WFM-115): `old` and `new` are {case id: output}; returns the list of {"case", "old", "new"} for every case whose outputs differ (empty = equal)"""
    return None


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
            return toolbox.run(tid, dict(inputs))
        return Stage(call)

    return {node_id: stage_of(tid) for node_id, tid in entries.items()}, lambda node_id: toolbox.look_up(entries[node_id])["trust"]
