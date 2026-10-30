"""
The model of the pipelines: MIA's Ollama server behind the small interface the runner uses, chat(messages, schema, model, profile, options) -> text.
The skill names a model profile ("full", "light", "current" = what the chat uses right now) or a model name; answers with a schema are requested as
constrained JSON (Ollama's `format`). The conversation history of MIA is not touched: the stages are separate, narrow requests.

One model server serves everybody (CON-2: one model loaded on the 16 GB card): ModelTurns lets one call run at a time (REQ-RUN-010), the waiting ones
in the order they came, and a waiting chat call before any waiting background call, so a long task yields the server between its calls (REQ-RUN-009).
TurnClient puts an ollama client behind those turns: the chat's client takes chat turns, the runner's background turns.
"""
import collections
import itertools
import threading

KINDS = ("chat", "background")


class ModelTurns:
    def __init__(self):
        self._cond = threading.Condition()
        self._queues = {kind: collections.deque() for kind in KINDS}
        self._tickets = itertools.count()
        self._holder, self._depth = None, 0

    def waiting(self):
        with self._cond:
            return {kind: len(queue) for kind, queue in self._queues.items()}

    def _next(self):
        """the ticket whose turn is next: the oldest chat call, else the oldest background call"""
        return next((queue[0] for queue in (self._queues[k] for k in KINDS) if queue), None)

    def acquire(self, kind):
        me = threading.get_ident()
        with self._cond:
            # the holder calling again (a repair during a streamed answer) must not wait for itself
            if self._holder == me:
                self._depth += 1
                return
            ticket = next(self._tickets)
            self._queues[kind].append(ticket)
            while self._holder is not None or self._next() != ticket:
                self._cond.wait()
            self._queues[kind].popleft()
            self._holder, self._depth = me, 1

    def release(self):
        with self._cond:
            self._depth -= 1
            if self._depth == 0:
                self._holder = None
                self._cond.notify_all()


class TurnClient:
    """an ollama client whose chat and generate calls wait for a turn of `kind`; a streamed answer holds its turn until it is read to the end or closed"""

    def __init__(self, client, turns, kind):
        self._client, self._turns, self.kind = client, turns, kind

    def __getattr__(self, name):
        return getattr(self._client, name)

    def chat(self, *args, **kwargs):
        return self._call(self._client.chat, args, kwargs)

    def generate(self, *args, **kwargs):
        return self._call(self._client.generate, args, kwargs)

    def _call(self, method, args, kwargs):
        if kwargs.get("stream"):
            return self._stream(method, args, kwargs)
        self._turns.acquire(self.kind)
        try:
            return method(*args, **kwargs)
        finally:
            self._turns.release()

    def _stream(self, method, args, kwargs):
        self._turns.acquire(self.kind)
        try:
            yield from method(*args, **kwargs)
        finally:
            self._turns.release()


class OllamaModel:
    def __init__(self, client, profile_lookup, current, keep_alive=None, think=False):
        """client: ollama Client; profile_lookup(profile) -> (model name, options) or None; current() -> (model name, options)"""
        self.client = client
        self._profile = profile_lookup
        self._current = current
        self.keep_alive = keep_alive
        self.think = think

    def resolve(self, model=None, profile=None):
        if model:
            return model, (self._current()[1] if self._current()[0] == model else None)
        found = self._profile(profile) if profile and profile != "current" else None
        return found if found else self._current()

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        return self.chat_with_usage(messages, schema, model, profile, options)[0]

    def chat_with_usage(self, messages, schema=None, model=None, profile=None, options=None):
        """(text, {"tokens_in", "tokens_out"} as the server counted them, or None): the runner counts them against the budget tokens (REQ-RUN-008)"""
        name, base = self.resolve(model, profile)
        merged = {**(base or {}), **(options or {})}
        reply = self.client.chat(model=name, messages=messages, format=schema, stream=False, options=merged or None,
                                 think=self.think, keep_alive=self.keep_alive)
        counts = [reply.get(key) for key in ("prompt_eval_count", "eval_count")]
        usage = {"tokens_in": counts[0], "tokens_out": counts[1]} if all(isinstance(c, int) for c in counts) else None
        return reply["message"]["content"], usage
