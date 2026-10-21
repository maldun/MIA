"""
The events of a run (ui/REQUIREMENTS_CORE.md 13d, CG11 to CG16): the envelope of the pipeline event, the typed domain events with a schema each, the removal of secrets,
and the run id / actor that travel to everything that logs (web log, scholar log, model calls, checks) by a context variable.

  V1  one format: the lifecycle events of pipeline.py (kind: run_start, start, done, retry, error, note, run_end) and the domain events (type: query_issued, source_found, ...)
      are the same dict. A domain event has kind "event", a type, a payload that fits the schema of that type, an actor (the node or the role) and a parent (the seq it follows from)
  V2  an event that does not fit its schema is never written as it is: strict mode (tests) raises EventError, normal mode writes a log_error event with the problem. Nothing is dropped silently
  V3  secrets never reach a log (LG4): fields named like token, password, secret, key, authorization, cookie, e-mail are replaced, and e-mail addresses and bearer tokens in text are removed
  V4  seq is strictly increasing within a run and shared by both kinds of events; parent is always an earlier seq (checked by check_log)
  V6  an event inside an agent session carries the round (communication step) it belongs to; the trace of a session is the series of its rounds (4b of the core requirements)
  V5  text is not in the events when it is big: they carry a hash (digest()) and an excerpt; the content store (a later step) keeps the texts
"""
import contextlib
import contextvars
import hashlib
import json
import platform
import re
import subprocess
import threading
import time

try:
    from .schema_check import check as check_schema
except ImportError:  # used as plain script / in tests
    from schema_check import check as check_schema

ENVELOPE_VERSION = 1
REDACTED = "[removed]"
MAX_EXCERPT = 300

_SECRET_KEY = re.compile(r"(^|[_\-.])(token|password|passwd|secret|authorization|cookie|mailto|email|e-mail|apikey|api[_\-]key|[a-z]+[_\-]key)$", re.I)
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+")
_BEARER = re.compile(r"\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=\-]{8,}")


class EventError(ValueError):
    pass


# --- secrets, hashes ----------------------------------------------------------------------------------------------------------------------

def redact(value, _depth=0):
    """a copy without secrets (V3): values of fields with a secret-like name, e-mail addresses and bearer tokens in strings"""
    if _depth > 12:
        return REDACTED
    if isinstance(value, dict):
        return {k: (REDACTED if isinstance(k, str) and _SECRET_KEY.search(k) and not isinstance(v, (bool, int, float, type(None))) and v != "" else redact(v, _depth + 1))
                for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v, _depth + 1) for v in value]
    if isinstance(value, str):
        return _BEARER.sub(REDACTED, _EMAIL.sub(REDACTED, value))
    return value


def digest(value):
    """a short name for content: the hash of a text, or of the canonical JSON of anything else"""
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return "h:" + hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:24]


def excerpt(text, limit=MAX_EXCERPT):
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[:limit - 1] + "…"


_commit_cache = {}


def _git_commit(root):
    if root not in _commit_cache:
        try:
            out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=3)
            _commit_cache[root] = out.stdout.strip() if out.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            _commit_cache[root] = None
    return _commit_cache[root]


def environment(cfg=None, root=None, models=None, versions=None):
    """what a run needs to be reproduced (13d, run_start): the code version, the python version, a hash of the configuration (secrets removed first), the models with their
    digests (a tag can be pulled again and change, so the digest matters) and the versions of skill, pipeline and library entries"""
    return {"commit": _git_commit(root) if root else None, "python": platform.python_version(), "config_hash": digest(redact(cfg)) if cfg is not None else None,
            "models": list(models or []), "versions": dict(versions or {})}


def model_digests(client, names):
    """[{"name", "digest"}] for the models of a run, read from an Ollama client's list; the digest is None when the server cannot be asked or does not know the model
    (a tag can be pulled again and change, so the name alone does not say which model answered)"""
    known = {}
    try:
        for entry in client.list().get("models", []):
            name = entry.get("model") if isinstance(entry, dict) else getattr(entry, "model", None)
            digest_ = entry.get("digest") if isinstance(entry, dict) else getattr(entry, "digest", None)
            if name:
                known[name] = digest_
    except Exception:
        known = {}
    return [{"name": n, "digest": known.get(n) or known.get(n + ":latest")} for n in names if n]


# --- the vocabulary: one schema per type ----------------------------------------------------------------------------------------------------

def _t(kind, limit=None, nullable=False):
    schema = {"type": [kind, "null"] if nullable else kind}
    if kind == "string":
        schema["maxLength"] = limit or 2000
    return schema


STR, SHORT, TEXT, REF = _t("string", 400), _t("string", 120), _t("string", 8000), _t("string", 1000)
INT, NUM, BOOL = {"type": "integer", "minimum": 0}, {"type": "number"}, {"type": "boolean"}


def _obj(required, **props):
    return {"type": "object", "properties": props, "required": list(required), "additionalProperties": False}


def _arr(item, limit=200):
    return {"type": "array", "items": item, "maxItems": limit}


def _maybe(schema):
    return {**schema, "type": [schema["type"], "null"]}


DROP_REASONS = ["off_topic", "after_cutoff", "no_date", "retracted", "notice", "duplicate", "low_trust", "no_text", "fetch_failed", "blocked", "budget", "other"]
VERDICTS = ["supported", "contradicted", "not_found"]
STOP_REASONS = ["sufficient", "budget", "user", "error", "no_more_sources"]
SUBTASK = {"type": ["string", "integer", "null"], "maxLength": 120}

SCHEMAS = {
    "plan_made": _obj(["origin", "plan"], origin={"enum": ["template", "free", "typed", "single"], "type": "string"}, template=_maybe(SHORT), plan={"type": "object"},
                      checks=_arr(_obj(["name", "result"], name=SHORT, result={"enum": ["pass", "fail"], "type": "string"}, detail=STR)), subtasks=INT),
    "router_decision": _obj(["strategy"], strategy=SHORT, markers=_arr(SHORT, 50)),
    "query_issued": _obj(["query", "backend"], query=STR, backend=SHORT, purpose=STR, subtask=SUBTASK),
    "source_found": _obj(["ref", "title", "backend"], ref=REF, title=STR, date=_maybe(SHORT), source_class=SHORT, trust=_maybe(NUM), backend=SHORT, rank=_maybe(INT)),
    "source_dropped": _obj(["ref", "stage", "reason"], ref=REF, stage=SHORT, reason={"enum": DROP_REASONS, "type": "string"}, detail=STR),
    "page_fetched": _obj(["ref", "hash", "bytes"], ref=REF, hash=SHORT, bytes=INT, truncated=BOOL, status=_maybe(INT)),
    "passage_extracted": _obj(["id", "source", "quote", "anchor_ok"], id=SHORT, source=REF, quote=TEXT, start=INT, end=INT, anchor_ok=BOOL, subtask=SUBTASK, by=SHORT),
    "claim_made": _obj(["id", "text"], id=SHORT, text=TEXT, subtask=SUBTASK, passages=_arr(SHORT), by=SHORT),
    "claim_verified": _obj(["claim", "verdict", "style", "judge", "confidence"], claim=SHORT, verdict={"enum": VERDICTS, "type": "string"}, style=SHORT, passage=SHORT,
                           judge=_obj(["actor"], actor=SHORT, model=_maybe(SHORT)), confidence={"type": ["number", "null"], "minimum": 0, "maximum": 1}),
    "conflict_found": _obj(["claims", "rule", "resolution"], claims=_arr(SHORT, 20), rule=SHORT, resolution={"enum": ["newer_source", "both_shown", "open"], "type": "string"}),
    "slot_opened": _obj(["subtask", "target"], subtask=SUBTASK, target=STR, why=STR),
    "slot_closed": _obj(["subtask"], subtask=SUBTASK, by_claim=SHORT),
    "draft_sentence": _obj(["text", "claims"], text=TEXT, claims=_arr(SHORT)),
    "check_run": _obj(["name", "result"], name=SHORT, target=STR, result={"enum": ["pass", "fail", "skipped"], "type": "string"}, detail=STR),
    "template_used": _obj(["template", "version", "problem_class"], template=SHORT, version=SHORT, problem_class=SHORT, test_passed={"type": ["boolean", "null"]}),
    "escalation": _obj(["from", "to", "trigger"], **{"from": SHORT, "to": SHORT, "trigger": STR}),
    "budget_spent": _obj(["name", "amount", "used", "limit"], name=SHORT, amount=NUM, used=NUM, limit=NUM),
    "checkpoint": _obj(["sources_checked", "decision"], sources_checked=INT, report_hash=_maybe(SHORT), decision={"enum": ["continue", "stop", "pending"], "type": "string"}),
    "stop_decision": _obj(["reason"], reason={"enum": STOP_REASONS, "type": "string"}, limit=SHORT, detail=STR),
    "model_call": _obj(["prompt_hash", "response_hash", "seconds", "valid", "attempt"], model=_maybe(SHORT), profile=_maybe(SHORT), digest=_maybe(SHORT), options={"type": ["object", "null"]},
                       prompt_hash=SHORT, response_hash=SHORT, prompt_chars=INT, response_chars=INT, seconds=NUM, tokens_in=_maybe(INT), tokens_out=_maybe(INT),
                       schema=_maybe(SHORT), valid=BOOL, attempt=INT),
    "user_feedback": _obj(["kind"], kind=SHORT, value={}, note=TEXT, claim=SHORT),
    "log_error": _obj(["problem", "original_type"], problem=TEXT, original_type=SHORT),
}


def validate(type_, payload):
    """readable problems (empty list: the payload fits)"""
    if type_ not in SCHEMAS:
        return ["unknown event type %r" % (type_,)]
    if not isinstance(payload, dict):
        return ["payload must be an object"]
    return check_schema(payload, SCHEMAS[type_])


# --- the stream of one run ----------------------------------------------------------------------------------------------------------------------

class EventStream:
    """the events of one run: sequence numbers (shared by lifecycle and domain events), the envelope, the schema check, the removal of secrets, and where they go (sink: a
    run_log.Run or anything with .event(dict); on_event: the display). strict=True raises on an event that does not fit (tests)."""

    def __init__(self, run_id=None, sink=None, on_event=None, clock=time.monotonic, t0=None, strict=False):
        self.run_id, self.sink, self.on_event, self.clock, self.strict = run_id, sink, on_event, clock, strict
        self.t0 = clock() if t0 is None else t0
        self._seq = 0
        self._lock = threading.Lock()
        self.problems = []

    def record(self, event):
        """a lifecycle event built by the pipeline: gets run, seq and time, loses secrets, goes to the sink and the display"""
        with self._lock:
            self._seq += 1
            seq = self._seq
        event = redact(dict(event))
        event.update({"run": self.run_id, "seq": seq, "at": round(self.clock() - self.t0, 3)})
        if self.sink is not None:
            self.sink.event(event)
        if self.on_event is not None:
            try:
                self.on_event(event)
            except Exception:
                pass                                # the display must not break a run
        return event

    def emit(self, type_, payload=None, actor=None, parent=None, node=None, item=None, plain="", round=None):
        """a domain event. Returns the event written (a log_error event if the payload did not fit and strict is off)."""
        payload = {} if payload is None else payload
        _, ctx_actor, ctx_parent, ctx_node, ctx_round = _context()
        problems = validate(type_, payload)
        if problems:
            self.problems.append((type_, problems))
            if self.strict:
                raise EventError("%s: %s" % (type_, "; ".join(problems[:3])))
            original = type_
            type_, payload = "log_error", {"problem": "; ".join(problems[:3])[:7000], "original_type": str(original)[:120]}
        event = {"kind": "event", "type": type_, "schema": ENVELOPE_VERSION, "node": node or ctx_node, "node_kind": None, "library": None, "item": item, "playful": "",
                 "plain": excerpt(plain), "payload": payload, "actor": actor or ctx_actor, "parent": parent if parent is not None else ctx_parent,
                 "round": round if round is not None else ctx_round}
        return self.record(event)


def check_log(events):
    """problems in the events of one run (V4): seq strictly increasing, parent an earlier seq, domain events with a known type and a payload that fits"""
    problems, last = [], 0
    seen = set()
    for event in events:
        seq = event.get("seq")
        if not isinstance(seq, int) or seq <= last:
            problems.append("seq %r after %r is not increasing" % (seq, last))
        else:
            last = seq
        parent = event.get("parent")
        if parent is not None and parent not in seen:
            problems.append("event %r points to a parent %r that is not an earlier event" % (seq, parent))
        seen.add(seq)
        if event.get("kind") == "event":
            found = validate(event.get("type"), event.get("payload"))
            if found:
                problems.append("event %r (%s): %s" % (seq, event.get("type"), found[0]))
    return problems


# --- the context: which stream, which actor ------------------------------------------------------------------------------------------------------

_current = contextvars.ContextVar("mia_events", default=None)


def _context():
    value = _current.get()
    return value if value else (None, None, None, None, None)


@contextlib.contextmanager
def activate(stream):
    token = _current.set((stream, None, None, None, None))
    try:
        yield stream
    finally:
        _current.reset(token)


@contextlib.contextmanager
def acting(actor, parent=None, node=None, round=None):
    """inside an active stream: events emitted here belong to this actor (a node, or a role) and follow from parent. round: the communication step of an agent session
    (the trace of a session is the series of its rounds, as in a co-simulation); nested actors inherit it unless they give their own"""
    stream, _, _, _, outer_round = _context()
    token = _current.set((stream, actor, parent, node if node is not None else actor, round if round is not None else outer_round)) if stream is not None else None
    try:
        yield
    finally:
        if token is not None:
            _current.reset(token)


def emit(type_, payload=None, **kwargs):
    """emit a domain event into the active stream; does nothing (returns None) outside a run, so tools work without one"""
    stream = _context()[0]
    return stream.emit(type_, payload, **kwargs) if stream is not None else None


def current_ids():
    """{"run", "actor"} of the active stream for the other logs (CG12); empty outside a run"""
    stream, actor, _, _, _ = _context()
    if stream is None:
        return {}
    ids = {"run": stream.run_id} if stream.run_id else {}
    if actor:
        ids["actor"] = actor
    return ids
