"""
The run recorder of the Workflow management (REQ-WFM-130 to 138, G-V3.PANEL): one record per skill run in the table skill_runs, the figures, answers, files,
result and reason of the run, the run that is shown, and the deletion with the chat history. Interface note: specs/mia/goals/G-V3.PANEL/run-recorder-interface.md.
Texts (result, material, answers, reason, elements) are stored and returned as they came and never interpreted (REQ-WFM-137).
"""
import datetime
import threading
import time

try:
    from task_monitor import TaskMonitor
except ImportError:                                              # imported as part of the package MIA
    from .task_monitor import TaskMonitor

AUTHOR = "skill_runs"                                            # the recorder writes in its own name; the account is a field of the record


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class SkillRunRecorder:

    def __init__(self, storage, emit, clock=time.monotonic, now=utc_now):
        self._storage, self._emit, self._clock, self._now = storage, emit, clock, now
        self._monitors = {}
        self._lock = threading.RLock()                           # answers (HTTP thread) and reports (skill thread) both load, change and save a record (REQ-WFM-133)
        storage.subscribe("history", self._history_changed)

    def start(self, run, skill, version, account, phases=()):
        doc = {"run": run, "skill": skill, "skill_version": version, "account": account, "started": self._now(), "state": "running",
               "phases": [{"name": name, "state": "waiting"} for name in phases], "budget": {}, "counts": {}, "elements": [],
               "answers": [], "result": "", "material": [], "files": []}
        self._save(doc)
        self._monitors[run] = monitor = TaskMonitor(self._emit, run, skill, clock=self._clock)
        monitor.update()
        self._changed(run)

    def phase(self, run, name):
        with self._lock:
            doc = self._load(run)
            names = [p["name"] for p in doc["phases"]]
            if name in names:
                for index, entry in enumerate(doc["phases"]):
                    if index < names.index(name):
                        entry["state"] = "done"
                    elif index == names.index(name):
                        entry["state"] = "running"
                self._save(doc)
            self._monitor(run).update(phase=name)

    def report(self, run, budget=None, counts=None, elements=None):
        monitor = self._monitor(run)
        monitor.update(budget=budget, counts=counts, elements=elements)
        self._keep_figures(run, monitor)

    def answer(self, run, text):
        with self._lock:
            doc = self._load(run)
            doc["answers"].append({"text": text, "time": self._now()})
            self._save(doc)
            self._changed(run)

    def file(self, run, name):
        with self._lock:
            doc = self._load(run)
            doc["files"].append(name)
            self._save(doc)
            self._changed(run)

    def end(self, run, state, reason=None, result="", material=()):
        with self._lock:
            monitor = self._monitor(run)
            monitor.finish()
            doc = self._load(run)
            doc.update(state=state, ended=self._now(), result=result, material=list(material), budget=monitor.state()["budget"], counts=dict(monitor.counts),
                       elements=list(monitor.elements))
            if reason is not None and state != "done":
                doc["reason"] = reason
            if state == "done":
                for entry in doc["phases"]:
                    entry["state"] = "done"
            else:
                open_phases = [entry for entry in doc["phases"] if entry["state"] != "done"]
                for entry in [e for e in open_phases if e["state"] == "running"] or open_phases[:1]:
                    entry["state"] = state                           # the phase that was current when the run failed or was stopped (IF-101 v16)
            self._save(doc)
            self._monitors.pop(run, None)
            self._changed(run)

    def record(self, run, account=None):
        """the run record of IF-101 v16; with `account` only the record of that account (the view of another account's run is not found)"""
        try:
            doc = self._load(run)
        except KeyError:
            return None
        if account is not None and doc["account"] != account:
            return None
        record = {"id": doc["run"], "skill": doc["skill"], "version": doc["skill_version"], "started": doc["started"], "ended": doc.get("ended"), "state": doc["state"]}
        record.update({field: doc.get(field) for field in ("phases", "budget", "counts", "elements", "answers", "result", "material", "files")})
        if "reason" in doc:
            record["reason"] = doc["reason"]
        return record

    def shown(self, account):
        """The run started last while runs of the account run, else the one ended last (REQ-WFM-134)."""
        docs = [doc for doc in (self._load_or_none(run) for run in self._storage.ids("skill_runs")) if doc and doc["account"] == account]
        running = [doc for doc in docs if doc["state"] == "running"]
        if running:
            return max(running, key=lambda doc: (doc["started"], doc["run"]))["run"]
        return max(docs, key=lambda doc: (doc["ended"] or "", doc["run"]))["run"] if docs else None

    def _history_changed(self, notice):
        """A delete in the history (version None) removes the run records of the account named as author (REQ-WFM-135)."""
        with self._lock:
            if notice.get("version") is not None:
                return
            for run in list(self._storage.ids("skill_runs")):
                doc = self._load_or_none(run)
                if doc and doc["account"] == notice.get("author"):
                    self._storage.delete("skill_runs", run, AUTHOR)
                    self._monitors.pop(run, None)
            self._emit("skill_run_changed", {"id": None})

    def _keep_figures(self, run, monitor):
        with self._lock:
            doc = self._load(run)
            doc.update(budget=monitor.state()["budget"], counts=dict(monitor.counts), elements=list(monitor.elements))
            self._save(doc)

    def _monitor(self, run):
        if run not in self._monitors:
            raise KeyError(run)
        return self._monitors[run]

    def _load(self, run):
        try:
            return self._storage.get("skill_runs", run)["doc"]
        except Exception as error:                               # StorageError(code) of IF-102
            if getattr(error, "code", None) != "not_found":
                raise
            raise KeyError(run) from error

    def _load_or_none(self, run):
        try:
            return self._load(run)
        except KeyError:
            return None

    def _save(self, doc):
        self._storage.put("skill_runs", doc["run"], doc, AUTHOR)

    def _changed(self, run):
        self._emit("skill_run_changed", {"id": run})
