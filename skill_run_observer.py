"""
The observer of one task run (REQ-WFM-136, G-V3.PANEL T-04; note specs/mia/goals/G-V3.PANEL/skill-events-today.md, D-309): ChatService._do_chat makes one for every task run and calls it at six places
(start, phase, report, answer, file, end); it passes them on to the SkillRunRecorder, so that a run record exists for every skill from the events the skill sends today, without a change of the skill.
A phase is recorded only when its text equals a declared phase name. STUB of Plan Step 4: the methods raise NotImplementedError until T-04 writes them.
"""


class SkillRunObserver:
    def __init__(self, recorder, run, skill, version, account, phases=()):
        self._recorder, self.run, self.skill, self.version, self.account, self.phases = recorder, run, skill, version, account, tuple(phases)

    def start(self):
        raise NotImplementedError("REQ-WFM-130, 136")

    def phase(self, text):
        raise NotImplementedError("REQ-WFM-130, 136")

    def report(self, budget=None, counts=None, elements=None):
        raise NotImplementedError("REQ-WFM-031, 131, 138")

    def answer(self, text):
        raise NotImplementedError("REQ-WFM-133")

    def file(self, name):
        raise NotImplementedError("REQ-WFM-132")

    def end(self, state, reason=None, result=""):
        raise NotImplementedError("REQ-WFM-131, 132")
