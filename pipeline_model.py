"""
The model of the pipelines: MIA's Ollama server behind the small interface the runner uses, chat(messages, schema, model, profile, options) -> text.
The skill names a model profile ("full", "light", "current" = what the chat uses right now) or a model name; answers with a schema are requested as
constrained JSON (Ollama's `format`). The conversation history of MIA is not touched: the stages are separate, narrow requests.
"""


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
        name, base = self.resolve(model, profile)
        merged = {**(base or {}), **(options or {})}
        reply = self.client.chat(model=name, messages=messages, format=schema, stream=False, options=merged or None,
                                 think=self.think, keep_alive=self.keep_alive)
        return reply["message"]["content"]
