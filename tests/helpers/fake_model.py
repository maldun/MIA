"""The fake model of the checks of the Chat agent (TR-CHAT-006, protected): scripted replies and a recorder of every call. It is no evidence for any eval
criterion: it shows the code paths, not the quality of the text, which is decided on the real pin only.

FakeModel(replies): `replies` is a list (the next reply per call), a dict {substring of the last user text: reply} (the first key that occurs answers) or a
function `messages -> str`. `.calls` holds every call as the list of messages {"role", "content"}; `.sizes(count_tokens)` the size of each call."""


class FakeModel:
    def __init__(self, replies):
        self._replies, self.calls = replies, []

    def __call__(self, messages):
        self.calls.append([dict(m) for m in messages])
        replies = self._replies
        if callable(replies):
            return replies(messages)
        if isinstance(replies, dict):
            last_user = [m["content"] for m in messages if m["role"] == "user"][-1]
            for key, reply in replies.items():
                if key in last_user:
                    return reply
            raise AssertionError("the fake model has no reply for: %r" % last_user[:80])
        return replies.pop(0)

    def sizes(self, count_tokens):
        return [sum(count_tokens(m["content"]) for m in call) for call in self.calls]

    def users(self, call):
        return [m["content"] for m in call if m["role"] == "user"]

    def systems(self, call):
        return [m["content"] for m in call if m["role"] == "system"]
