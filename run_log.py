"""
The log of the runs (ui/REQUIREMENTS_CORE.md 9, EL1): every run of a skill is stored as one JSON line with its input, the events of all nodes with timings,
the result and (later) the feedback of the user. The file is append-only, one file per month (`runs-YYYY-MM.jsonl`); feedback is a separate line that refers to the
run, read() joins both. This is the data for the evaluation harness and for everything that learns.
"""
import json
import os
import secrets
import threading
import time

MAX_TEXT = 20000       # longer texts in the log are cut (the page texts of research runs can be huge)


def _clip(value, limit=MAX_TEXT):
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "…[+%d characters]" % (len(value) - limit)
    if isinstance(value, dict):
        return {str(k): _clip(v, limit) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clip(v, limit) for v in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _clip(str(value), limit)


def utc_stamp(now=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now if now is not None else time.time()))


class Run:
    """one run in progress: collects the events and writes the record when it ends"""

    def __init__(self, log, record):
        self._log = log
        self.record = record
        self.id = record["id"]
        self.events = record["events"]
        self._lock = threading.Lock()

    def event(self, event):
        with self._lock:
            self.events.append(_clip(event))

    def finish(self, status, output=None, seconds=0.0, error=None):
        self.record.update({"status": status, "output": _clip(output), "seconds": round(seconds, 3), "error": error})
        self._log._write(self.record)


class RunLog:
    def __init__(self, folder, clock=time.time):
        self.folder = folder
        self._clock = clock
        self._lock = threading.Lock()

    def _file(self, when=None):
        return os.path.join(self.folder, "runs-%s.jsonl" % time.strftime("%Y-%m", time.gmtime(when if when is not None else self._clock())))

    def _write(self, record):
        os.makedirs(self.folder, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False)
        with self._lock, open(self._file(), "a", encoding="utf-8") as fp:
            fp.write(line + "\n")

    def start(self, task, skill=None, skill_version=None, pipeline=None, pipeline_version=None, model=None, input=None, uses=None):
        now = self._clock()
        record = {"kind": "run", "id": "r-%s-%s" % (time.strftime("%Y%m%d%H%M%S", time.gmtime(now)), secrets.token_hex(2)),
                  "created": utc_stamp(now), "task": task, "skill": skill, "skill_version": skill_version,
                  "pipeline": pipeline, "pipeline_version": pipeline_version, "uses": list(uses or []), "model": model, "input": _clip(input), "events": []}
        return Run(self, record)

    def add_feedback(self, run_id, kind, value=None, note=""):
        """thumbs up/down, a correction, a free note ... refers to the run by its id"""
        self._write({"kind": "feedback", "run": run_id, "created": utc_stamp(self._clock()), "type": kind, "value": _clip(value), "note": _clip(note)})

    def add_signal(self, run_id, rule, sign="penalty", node=None, detail="", **fields):
        """a reward or a penalty for a rule (ui/REQUIREMENTS_CORE.md 13a, BF2): which run, which node, which rule, which sign; read() joins the signals to their run as "signals"
        and signals_by_rule() counts them. Extra fields (span, text, severity) are kept."""
        self._write({"kind": "signal", "run": run_id, "created": utc_stamp(self._clock()), "rule": rule, "sign": sign, "node": node, "detail": _clip(detail), **{k: _clip(v) for k, v in fields.items()}})

    def signals_by_rule(self):
        """{rule: {"penalty": n, "reward": n, "runs": number of runs}} over the whole log"""
        table, runs = {}, {}
        if not os.path.isdir(self.folder):
            return table
        for name in sorted(os.listdir(self.folder)):
            if not (name.startswith("runs-") and name.endswith(".jsonl")):
                continue
            with open(os.path.join(self.folder, name), encoding="utf-8") as fp:
                for line in fp:
                    try:
                        record = json.loads(line)
                    except ValueError:
                        continue
                    if record.get("kind") == "signal":
                        row = table.setdefault(record["rule"], {"penalty": 0, "reward": 0, "runs": 0})
                        row[record.get("sign", "penalty")] = row.get(record.get("sign", "penalty"), 0) + 1
                        runs.setdefault(record["rule"], set()).add(record.get("run"))
        for rule, ids in runs.items():
            table[rule]["runs"] = len(ids)
        return table

    def read(self, limit=None):
        """the runs (oldest first) with their feedback joined as "feedback": [..]"""
        runs, order, feedback, signals = {}, [], [], []
        if not os.path.isdir(self.folder):
            return []
        for name in sorted(os.listdir(self.folder)):
            if not (name.startswith("runs-") and name.endswith(".jsonl")):
                continue
            with open(os.path.join(self.folder, name), encoding="utf-8") as fp:
                for line in fp:
                    try:
                        record = json.loads(line)
                    except ValueError:
                        continue          # a half written last line must not hide the rest
                    if record.get("kind") == "run":
                        runs[record["id"]] = record
                        order.append(record["id"])
                    elif record.get("kind") == "feedback":
                        feedback.append(record)
                    elif record.get("kind") == "signal":
                        signals.append(record)
        for item in feedback:
            if item.get("run") in runs:
                runs[item["run"]].setdefault("feedback", []).append(item)
        for item in signals:
            if item.get("run") in runs:
                runs[item["run"]].setdefault("signals", []).append(item)
        result = [runs[i] for i in order]
        return result[-limit:] if limit else result
