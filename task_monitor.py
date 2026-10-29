"""
The monitor of a running task (REQ-WFM-031, REQ-WFM-033): a task reports its phase, its budget figures and its counts; the monitor merges them, counts the active seconds
itself (paused time does not count) and emits `task_status` for the status card of the page, at most every `min_interval` seconds and once more at the end.
Nothing here knows a task: a skill reports whatever budgets and counts it has and the page shows them all.
"""
import time


class TaskMonitor:
    def __init__(self, emit, task_id, task, mode="run", clock=time.monotonic, min_interval=0.5):
        self._emit, self._clock, self._interval = emit, clock, min_interval
        self.id, self.task, self.mode = task_id, task, mode
        self.phase, self.budget, self.counts = None, {}, {}
        self.done, self._paused_at, self._paused_total = False, None, 0.0
        self._started, self._last = clock(), None

    @property
    def paused(self):
        return self._paused_at is not None

    def active_seconds(self):
        """the time since the start without the paused time"""
        now = self._paused_at if self._paused_at is not None else self._clock()
        return now - self._started - self._paused_total

    def update(self, phase=None, budget=None, counts=None):
        if phase is not None:
            self.phase = phase
        for name, figures in (budget or {}).items():
            self.budget.setdefault(name, {}).update(figures)
        self.counts.update(counts or {})
        if self._last is None or self._clock() - self._last >= self._interval:
            self._send()

    def pause(self):
        if self._paused_at is None:
            self._paused_at = self._clock()
            self._send()

    def resume(self):
        if self._paused_at is not None:
            self._paused_total += self._clock() - self._paused_at
            self._paused_at = None
            self._send()

    def finish(self):
        self.done = True
        self._send()

    def state(self):
        budget = {name: dict(figures) for name, figures in self.budget.items()}
        budget.setdefault("seconds", {})["used"] = round(self.active_seconds(), 1)       # the monitor counts the time, a task only reports the limit
        return {"id": self.id, "task": self.task, "phase": self.phase, "mode": self.mode, "paused": self.paused, "done": self.done, "budget": budget, "counts": dict(self.counts)}

    def _send(self):
        self._last = self._clock()
        self._emit("task_status", self.state())
