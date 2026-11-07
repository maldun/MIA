"""Conversion of the skills onto the new records (part skillConverter, FR-45, G-V2.CONVERT). STUBS until the tasks T-CV-02 to T-CV-08 of plan.md.

The stubs never raise and return values outside the real vocabulary (None, empty), so that the acceptance tests of G-V2.CONVERT fail on an assertion.
The signatures are the ones the red tests assume (to be confirmed by the owner at the review of the tests).
"""


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
    """Versioned configuration of the equivalence check (REQ-WFM-069, D-187): margin, repeats and rule, kept in the folder `path`. STUB."""

    def __init__(self, path):
        self.path = path

    def current(self):
        """STUB: {"version": 1, "margin": 0.10, "repeats": 3, "rule": "threshold"} at the start"""
        return {}

    def versions(self):
        """STUB: every version, oldest first"""
        return []

    def update(self, **changes):
        """STUB: a change creates the next version and returns it (earlier versions stay)"""
        return {}

    def record_result(self, skill, verdict):
        """STUB: stores a result that names the settings version used and returns it"""
        return {}

    def results(self):
        """STUB: the results in the order they were recorded; a stored result is never changed afterwards"""
        return []
