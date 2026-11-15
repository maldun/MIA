"""Conversion of the skills onto the new records (part skillConverter, FR-45, G-V2.CONVERT). STUBS (EquivalenceSettings is real since T-CV-02) until the tasks T-CV-03 to T-CV-08 of plan.md.

The stubs never raise and return values outside the real vocabulary (None, empty), so that the acceptance tests of G-V2.CONVERT fail on an assertion.
The signatures are the ones the red tests assume (to be confirmed by the owner at the review of the tests).
"""
import json
import os


class ConversionError(Exception):
    """a skill is marked converted without a passed equivalence check (REQ-WFM-057)"""


class SkillConverter:
    """Chooses per skill between the old runner and the converted record (REQ-WFM-057).

    old_loader(name) and converted_loader(name) give (skill, graph); runner.run(skill, graph, inputs, **kwargs) runs one. The converted loader is
    called only for a skill that is marked converted. A skill starts unconverted."""

    def __init__(self, old_loader, converted_loader, runner):
        self.old_loader, self.converted_loader, self.runner = old_loader, converted_loader, runner

    def state(self, name):
        """STUB: "unconverted" or "converted" """
        return None

    def mark_converted(self, name, check):
        """STUB: `check` is the result of decide_acceptance; anything but accepted is refused with ConversionError and the state stays"""

    def run(self, name, inputs, **kwargs):
        """STUB: runs the old skill file and pipeline of an unconverted skill, the converted record of a converted one"""
        return None


def run_converted(name, inputs, model=None, tools=None, skills_dir=None, library_dir=None, runs_dir=None, skill_changes=None):
    """STUB (REQ-WFM-058, REQ-WFM-115): runs the converted version of skill `name` on the new path with the given model and tools and returns the run
    result of the runner (status, answer, ...). `skill_changes` is merged into the skill record first (a test plants a changed option with it)."""
    return None


def decide_acceptance(run_path, criterion, rerun_path=None):
    """STUB (REQ-WFM-059): decides the criterion line on the run files with eval_decide.py of the agent-app skill and applies the acceptance rule.
    Returns {"verdict": "PASS" | "FAIL" | "NOT DECIDED", "accepted": bool, "reason": str}; only PASS is accepted; a FAIL counts after the re-run (`rerun_path`)."""
    return {"verdict": None, "accepted": False, "reason": "stub"}


def conversion_records(skills_dir):
    """STUB (REQ-WFM-060): {skill name: {"form": "old" | "converted", and either "suite", "run", "pins", "verdict" or "reason"}} for every skill file of the folder"""
    return {}


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
