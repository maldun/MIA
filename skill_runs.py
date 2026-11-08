"""
The run recorder of the Workflow management (REQ-WFM-130 to 138, G-V3.PANEL): one record per skill run in the table skill_runs, the figures, answers, files,
result and reason of the run, the run that is shown, and the deletion with the chat history. Interface note: specs/mia/goals/G-V3.PANEL/run-recorder-interface.md.
STUB of Plan Step 4: the constructor only keeps its arguments; every method raises NotImplementedError until Implement writes it.
"""
import time


class SkillRunRecorder:
    def __init__(self, storage, emit, clock=time.monotonic, now=None):
        self._storage, self._emit, self._clock, self._now = storage, emit, clock, now

    def start(self, run, skill, version, account, phases=()):
        raise NotImplementedError("REQ-WFM-130")

    def phase(self, run, name):
        raise NotImplementedError("REQ-WFM-130")

    def report(self, run, budget=None, counts=None, elements=None):
        raise NotImplementedError("REQ-WFM-031, 131, 138")

    def answer(self, run, text):
        raise NotImplementedError("REQ-WFM-133")

    def file(self, run, name):
        raise NotImplementedError("REQ-WFM-132")

    def end(self, run, state, reason=None, result="", material=()):
        raise NotImplementedError("REQ-WFM-131, 132")

    def record(self, run):
        raise NotImplementedError("REQ-WFM-130")

    def shown(self, account):
        raise NotImplementedError("REQ-WFM-134")
