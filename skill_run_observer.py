"""
The observer of one task run (REQ-WFM-136, G-V3.PANEL T-04; note specs/mia/goals/G-V3.PANEL/skill-events-today.md, D-309): ChatService._do_chat makes one for every task run and calls it at six places
(start, phase, report, answer, file, end); it passes them on to the SkillRunRecorder, so that a run record exists for every skill from the events the skill sends today, without a change of the skill.
A phase is recorded only when its text equals a declared phase name. A recorder that fails never takes the answer of the run with it: the failure is logged and the run goes on.
"""
try:
    from .mia_logger import logger
except ImportError:  # used as plain script / in tests
    from mia_logger import logger


class SkillRunObserver:
    def __init__(self, recorder, run, skill, version, account, phases=()):
        self._recorder, self.run, self.skill, self.version, self.account, self.phases = recorder, run, skill, version, account, tuple(phases)

    def start(self):
        self._call(self._recorder.start, self.run, self.skill, self.version, self.account, phases=self.phases)

    def phase(self, text):
        if text in self.phases:
            self._call(self._recorder.phase, self.run, text)

    def report(self, budget=None, counts=None, elements=None):
        self._call(self._recorder.report, self.run, budget=budget, counts=counts, elements=elements)

    def tell(self, phase=None, budget=None, counts=None, elements=None):
        """what TaskMonitor.update heard: a phase text and/or figures"""
        if phase is not None:
            self.phase(phase)
        if budget or counts or elements is not None:
            self.report(budget, counts, elements)

    def answer(self, text):
        self._call(self._recorder.answer, self.run, text)

    def file(self, name):
        self._call(self._recorder.file, self.run, name)

    def end(self, state, reason=None, result=""):
        self._call(self._recorder.end, self.run, state, reason=reason, result=result)

    def _call(self, method, *args, **kwargs):
        try:
            method(*args, **kwargs)
        except Exception as exc:
            logger.warning("run record of %s: %s", self.run, exc)
