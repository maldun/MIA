"""Mock of IF-103, the model server (protected). Complexity 3: scripted replies, token counts and errors.
It does not reproduce the quality of a real model: eval criteria are decided on the pinned model, never on this mock."""
import json

try:
    from .errors import ModelServerError
except ImportError:
    from errors import ModelServerError


class ModelServerMock:
    def __init__(self, replies=None, down=False, timeout=False):
        self.replies = list(replies or [])
        self.down, self.timeout = down, timeout
        self.calls = []

    def chat(self, messages, schema=None, model="MP-light", options=None):
        """Returns {"message", "model", "tokens_in", "tokens_out"}. With a schema the message is a dict with the schema's required keys."""
        if not messages:
            raise ValueError("messages must not be empty")
        self.calls.append({"messages": messages, "schema": schema, "model": model, "options": options})
        if self.down:
            raise ModelServerError("unreachable")
        if self.timeout:
            raise ModelServerError("timeout")
        reply = self.replies.pop(0) if self.replies else "ok"
        reply = reply(messages) if callable(reply) else reply
        if schema is not None:
            reply = self._as_dict(reply, schema)
        tokens_in = sum(len(str(m.get("content", "")).split()) for m in messages)
        tokens_out = len(json.dumps(reply).split()) if not isinstance(reply, str) else len(reply.split())
        return {"message": reply, "model": model, "tokens_in": tokens_in, "tokens_out": tokens_out}

    @staticmethod
    def _as_dict(reply, schema):
        if isinstance(reply, str):
            try:
                reply = json.loads(reply)
            except ValueError:
                raise ModelServerError("bad_output", detail=reply)
        if not isinstance(reply, dict) or any(key not in reply for key in schema.get("required", [])):
            raise ModelServerError("bad_output", detail=reply)
        return reply
