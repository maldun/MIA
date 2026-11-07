"""Record and replay of an old run: model replies and tool results (T-CV-01, REQ-WFM-058, D-260 C). Helper of G-V2.CONVERT.

A converted skill must make the same model calls as the old runner (order, prompt text, options). To check that without a model, one old run is
recorded once (what the model answered, what each tool returned) and then replayed as often as needed against the converted skill, which
sees the same answers in the same order and whose calls are written down for the comparison.

    rec = Recording()
    model = RecordingModel(scripted_or_real_model, rec); tool = RecordingTool("web_search", fn, rec)
    ... run the old skill ...
    rec.save(path)

    replay = Replay(Recording.load(path))                 # a fresh replay per run: replay.model, replay.tools
    ... run the converted skill ...
    first_difference(rec.model_calls(), replay.model_calls())   # None, or the first call that differs and how

The replay answers by order, not by matching the prompt: a converted skill that asks something else gets the old answer and the difference
shows in the call list instead of being hidden. A call beyond the recording raises ReplayExhausted and is still listed.
Standard library only. It is not a model server and never decides an eval criterion (TR-CONVERT-006).
"""

import json

MODEL_FIELDS = ("messages", "schema", "model", "profile", "options")


class ReplayExhausted(Exception):
    """the converted skill made more calls than the old run did"""


def _copy(value):
    return json.loads(json.dumps(value))


class Recording:
    def __init__(self, events=None, tools=()):
        self.events = list(events or [])           # in run order: {"kind": "model", ...} and {"kind": "tool", ...}
        self.tool_names = set(tools or ())         # the tools the old run had, also those it never called: the converted run needs them registered

    def add(self, event):
        self.events.append(event)

    def model_calls(self):
        """the model calls without the replies, as compared between the old and the converted run"""
        return [{k: e.get(k) for k in MODEL_FIELDS} for e in self.events if e["kind"] == "model"]

    def tool_calls(self):
        return [{"name": e["name"], "args": e["args"]} for e in self.events if e["kind"] == "tool"]

    def save(self, path):
        with open(path, "w", encoding="utf-8") as fp:
            json.dump({"version": 1, "tools": sorted(self.tool_names), "events": self.events}, fp, indent=1, sort_keys=True)

    @staticmethod
    def load(path):
        with open(path, encoding="utf-8") as fp:
            data = json.load(fp)
        return Recording(data["events"], data.get("tools", ()))


class RecordingModel:
    """wraps a model with chat(messages, schema=None, model=None, profile=None, options=None) and records every call with its reply"""

    def __init__(self, model, recording):
        self.model, self.recording = model, recording

    def chat(self, messages, schema=None, model=None, profile=None, options=None, **more):
        reply = self.model.chat(messages, schema=schema, model=model, profile=profile, options=options, **more)
        self.recording.add({"kind": "model", "messages": _copy(messages), "schema": schema, "model": model, "profile": profile, "options": options,
                            "reply": reply})
        return reply


class RecordingTool:
    def __init__(self, name, fn, recording):
        self.name, self.fn, self.recording = name, fn, recording
        recording.tool_names.add(name)

    def __call__(self, *args, **kwargs):
        result = self.fn(*args, **kwargs)
        self.recording.add({"kind": "tool", "name": self.name, "args": _copy({"args": list(args), "kwargs": kwargs}), "result": result})
        return result


class Replay:
    """answers a run from a recording; `model` and `tools` plug into the runner, `calls` holds what the replayed run asked"""

    def __init__(self, recording):
        self._replies = [e["reply"] for e in recording.events if e["kind"] == "model"]
        self._results = {}
        for e in recording.events:
            if e["kind"] == "tool":
                self._results.setdefault(e["name"], []).append(e["result"])
        self.calls = Recording()
        self.model = _ReplayModel(self)
        self.tools = {name: _ReplayTool(self, name) for name in sorted(set(self._results) | set(recording.tool_names))}

    def model_calls(self):
        return self.calls.model_calls()

    def tool_calls(self):
        return self.calls.tool_calls()


class _ReplayModel:
    def __init__(self, replay):
        self.replay, self.used = replay, 0

    def chat(self, messages, schema=None, model=None, profile=None, options=None, **more):
        self.replay.calls.add({"kind": "model", "messages": _copy(messages), "schema": schema, "model": model, "profile": profile, "options": options})
        if self.used >= len(self.replay._replies):
            raise ReplayExhausted("model call %d, the recording holds %d" % (self.used + 1, len(self.replay._replies)))
        self.used += 1
        return self.replay._replies[self.used - 1]


class _ReplayTool:
    def __init__(self, replay, name):
        self.replay, self.name, self.used = replay, name, 0

    def __call__(self, *args, **kwargs):
        self.replay.calls.add({"kind": "tool", "name": self.name, "args": _copy({"args": list(args), "kwargs": kwargs})})
        results = self.replay._results.get(self.name, [])
        if self.used >= len(results):
            raise ReplayExhausted("call %d of tool %s, the recording holds %d" % (self.used + 1, self.name, len(results)))
        self.used += 1
        return results[self.used - 1]


def first_difference(old_calls, new_calls):
    """None when both lists of model calls are equal, else {"call": 1-based number, "field", "old", "new"}; a call missing on one side has field "missing"."""
    for i in range(max(len(old_calls), len(new_calls))):
        if i >= len(old_calls) or i >= len(new_calls):
            return {"call": i + 1, "field": "missing", "old": old_calls[i] if i < len(old_calls) else None, "new": new_calls[i] if i < len(new_calls) else None}
        for field in MODEL_FIELDS:
            if old_calls[i].get(field) != new_calls[i].get(field):
                return {"call": i + 1, "field": field, "old": old_calls[i].get(field), "new": new_calls[i].get(field)}
    return None


def schema_reply(schema):
    """a reply that fits a JSON schema with the plainest values (short text padded to minLength, empty list, false, the minimum or 0, first enum value); scripts an old run without a model"""
    if schema is None:
        return "ok"
    return json.dumps(_plain(schema))


def _plain(schema):
    if "enum" in schema:
        return schema["enum"][0]
    kind = schema.get("type", "object")
    if kind == "object":
        return {key: _plain(schema.get("properties", {}).get(key, {"type": "string"})) for key in schema.get("required", [])}
    if kind == "string":
        return "plain text".ljust(int(schema.get("minLength", 0)), ".")
    if kind in ("number", "integer"):
        return schema.get("minimum", 0)
    return {"array": [], "boolean": False}.get(kind)


class ScriptedModel:
    """answers from a list (a text or a function of the messages), then with a schema-fitting plain reply"""

    def __init__(self, replies=()):
        self.replies = list(replies)

    def chat(self, messages, schema=None, model=None, profile=None, options=None, **more):
        if self.replies:
            reply = self.replies.pop(0)
            return reply(messages) if callable(reply) else reply
        return schema_reply(schema)
