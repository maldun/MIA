"""
The run event log (IF-401, REQ-LOG-001 to -003, -005): the runner and the tools write the typed events of a run, and the step-by-step account of an answer is a view of them.

  emit(run_id, type, payload, user, actor=None, plain="")   one event; seq counts from 1 per run; secrets in the payload and e-mail addresses or bearer tokens in the plain text are removed
                                                            before the line is written (events.redact, events.clean_text)
  events(run_id)      the events in the order of seq        account(run_id)  [{"seq", "plain"}] of the events that have a plain text, never made by a model
  check_order(run_id) the problems of the order             compare(a, b)    {"same", "differences"} by the types and payloads, not by time and run id

The events of a run are an append-only file of their own, `<folder>/<run_id>.jsonl`, one JSON line per event (A-28: the events are a stream of logs, not shared state; no database driver is
used). A half-written last line (a crash) hides nothing: it is skipped and the next event starts on a line of its own. The vocabulary of the contract is coarse (14 types); the strict payload
schemas of events.py (EventStream) are the business of the runner that writes through this log. One writer per file: the numbers of seq are counted by this instance.
"""
import json
import os
import re
import threading
import time

try:
    from . import events as ev
except ImportError:  # used as plain script / in tests
    import events as ev

TYPES = ("run_start", "run_end", "model_call", "tool_call", "check_run", "query_issued", "source_found", "passage_extracted", "claim_made",
         "claim_verified", "stop_decision", "budget_spent", "router_decision", "error")
RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")


class RunEventsError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class RunEvents:
    def __init__(self, folder, clock=time.time):
        self.folder, self._clock = folder, clock
        self._lock = threading.Lock()
        self._next = {}                              # run id -> the seq of the next event, counted when the file is first used by this instance

    def path(self, run_id):
        if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id) or ".." in run_id:
            raise RunEventsError("invalid_run")
        return os.path.join(self.folder, run_id + ".jsonl")

    def _read(self, path):
        found = []
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue                          # a half-written line must not hide the rest
                if isinstance(event, dict):
                    found.append(event)
        return found

    def emit(self, run_id, type, payload, user, actor=None, plain=""):
        path = self.path(run_id)
        if type not in TYPES:
            raise RunEventsError("unknown_type")
        if not isinstance(payload, dict):
            raise RunEventsError("invalid_payload")
        if not isinstance(user, str) or not user:
            raise RunEventsError("invalid_user")
        with self._lock:
            if run_id not in self._next:
                seqs = [e.get("seq") for e in self._read(path)] if os.path.exists(path) else []
                self._next[run_id] = max([s for s in seqs if isinstance(s, int)] or [0]) + 1
            seq = self._next[run_id]
            event = {"seq": seq, "type": type, "run_id": run_id, "user": user, "actor": actor, "plain": ev.clean_text(plain or ""),
                     "payload": ev.redact(payload), "time": self._clock()}
            line = json.dumps(event, ensure_ascii=False, default=str) + "\n"
            os.makedirs(self.folder, exist_ok=True)
            with open(path, "ab+") as handle:
                handle.seek(0, os.SEEK_END)
                if handle.tell() and not self._ends_with_newline(handle):
                    handle.write(b"\n")               # the cut line stays a line of its own
                handle.write(line.encode("utf-8"))
            self._next[run_id] = seq + 1
        return {"seq": seq}

    @staticmethod
    def _ends_with_newline(handle):
        handle.seek(-1, os.SEEK_END)
        last = handle.read(1)
        handle.seek(0, os.SEEK_END)
        return last == b"\n"

    def events(self, run_id):
        path = self.path(run_id)
        if not os.path.exists(path):
            raise RunEventsError("unknown_run")
        return self._read(path)

    def account(self, run_id):
        return [{"seq": e["seq"], "plain": e["plain"]} for e in self.events(run_id) if e.get("plain")]

    def check_order(self, run_id):
        events, problems = self.events(run_id), []
        if not events or events[0].get("type") != "run_start":
            problems.append("run_start is not first")
        for position, event in enumerate(events, 1):
            if event.get("seq") != position:
                problems.append("seq %s at position %s" % (event.get("seq"), position))
        return problems

    def compare(self, run_a, run_b):
        view = lambda run: [(e.get("type"), e.get("payload")) for e in self.events(run)]
        a, b = view(run_a), view(run_b)
        differences = ["at %d: %s != %s" % (i + 1, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
        if len(a) != len(b):
            differences.append("length %d != %d" % (len(a), len(b)))
        return {"same": not differences, "differences": differences}
