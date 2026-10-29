"""Mock of IF-401, the run event log (protected). Complexity 2: an in-memory log with run ids, order and the account.
It does not persist and does not know the full event schema of events.py, only the list of types."""
import copy
import re

try:
    from .errors import ServiceError
except ImportError:
    from errors import ServiceError

TYPES = ("run_start", "run_end", "model_call", "tool_call", "check_run", "query_issued", "source_found", "passage_extracted", "claim_made",
         "claim_verified", "stop_decision", "budget_spent", "router_decision", "error")
SECRET_WORDS = ("password", "token", "api_key", "secret")
RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")   # a plain name (v1, A-30): the real log makes a file of it


def _clean(value):
    if isinstance(value, dict):
        return {k: "[removed]" if any(w in k.lower() for w in SECRET_WORDS) else _clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


class RunEventsMock:
    def __init__(self):
        self._runs = {}
        self._tick = 0

    @staticmethod
    def _check_run_id(run_id):
        if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id) or ".." in run_id:
            raise ServiceError("invalid_run")

    def emit(self, run_id, type, payload, user, actor=None, plain=""):
        self._check_run_id(run_id)
        if type not in TYPES:
            raise ServiceError("unknown_type")
        if not isinstance(payload, dict):
            raise ServiceError("invalid_payload")
        if not isinstance(user, str) or not user:
            raise ServiceError("invalid_user")
        events = self._runs.setdefault(run_id, [])
        self._tick += 1
        events.append({"seq": len(events) + 1, "type": type, "run_id": run_id, "user": user, "actor": actor, "plain": plain,
                       "payload": _clean(copy.deepcopy(payload)), "time": self._tick})
        return {"seq": len(events)}

    def _run(self, run_id):
        self._check_run_id(run_id)
        if run_id not in self._runs:
            raise ServiceError("unknown_run")
        return self._runs[run_id]

    def events(self, run_id):
        return copy.deepcopy(self._run(run_id))

    def account(self, run_id):
        return [{"seq": e["seq"], "plain": e["plain"]} for e in self._run(run_id) if e["plain"]]

    def check_order(self, run_id):
        events, problems = self._run(run_id), []
        if not events or events[0]["type"] != "run_start":
            problems.append("run_start is not first")
        for position, event in enumerate(events, 1):
            if event["seq"] != position:
                problems.append("seq %s at position %s" % (event["seq"], position))
        return problems

    def compare(self, run_a, run_b):
        view = lambda run: [(e["type"], e["payload"]) for e in self._run(run)]
        a, b = view(run_a), view(run_b)
        differences = ["at %d: %s != %s" % (i + 1, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
        if len(a) != len(b):
            differences.append("length %d != %d" % (len(a), len(b)))
        return {"same": not differences, "differences": differences}

    def inject_event(self, run_id, event):
        """Test adapter: write a raw event and bypass emit (to build a broken log)."""
        self._runs.setdefault(run_id, []).append(dict(event))
