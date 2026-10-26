"""Mock of IF-201, the chat turn service of the Chat agent (protected). Complexity 3: a queue and an event stream.
Built on the mock of IF-101 with one internal session; it does not model persona, mood, memory or model latency."""
try:
    from .errors import ApiError, ServiceError
    from .if_101_chat_api import ChatApiMock
except ImportError:
    from errors import ApiError, ServiceError
    from if_101_chat_api import ChatApiMock

CODES = {"empty_text": "empty_text", "queue_full": "queue_full"}      # every other code of IF-101 (not_found, not_the_last_answer, invalid_vote) keeps its name


class ChatTurnMock:
    def __init__(self, answers=None, queue_limit=5):
        names = ("anna", "ben", "carl", "dora", "emil")                   # v2: five voters for the counters
        self._api = ChatApiMock(accounts={name: "pw" for name in names}, answers=answers, queue_limit=queue_limit)
        self._sessions = {name: self._api.login(name, "pw") for name in names}
        self._observer = self._sessions["ben"]
        self._api.connect(self._observer)
        self._callbacks = []
        self._api.events(self._observer)

    def _call(self, fn):
        try:
            return fn()
        except ApiError as err:
            raise ServiceError(CODES.get(err.code, err.code), rule=err.rule)

    def _forward(self):
        for event in self._api.events(self._observer):
            for callback in list(self._callbacks):
                callback(event)

    def send(self, account, text, client_id=None):
        result = self._call(lambda: self._api.send(self._sessions[account], text, client_id))
        self._forward()
        return {"id": result["id"], "position": result["position"]}       # IF-201 has no `message` in the ack (the IF-101 v1 mock adds it)

    # v1 (amendment A-06): the operations on answers and votes; the records, trust and persona go through the Database (IF-102), not through the chat agent
    def regenerate(self, account, message_id):
        result = self._call(lambda: self._api.regenerate(self._sessions[account], message_id))
        self._forward()
        return result

    def speak_again(self, message_id):
        result = self._call(lambda: self._api.speak_again(self._observer, message_id))
        self._forward()
        return result

    def account(self, message_id):
        return self._call(lambda: self._api.account(self._observer, message_id))

    def vote(self, account, subject, category, value):
        result = self._call(lambda: self._api.vote(self._sessions[account], subject, category, value))
        self._forward()
        return result

    def score(self):
        return self._api.score(self._observer)

    def counters(self):                                                   # v2 (amendment A-08)
        return self._api.counters(self._observer)

    def reset_counter(self, account, name):
        result = self._call(lambda: self._api.reset_counter(self._sessions[account], name))
        self._forward()
        return result

    def advance_time(self, seconds):
        """Test adapter: move the clock of the chat agent (the weeks of the score)."""
        self._api.advance_time(seconds)

    def stop(self):
        return self._api.stop(self._observer)

    def history(self, limit=50):
        return self._api.history(self._observer, limit)

    def status(self):
        return self._api._status()

    def subscribe(self, callback):
        self._callbacks.append(callback)
        return lambda: self._callbacks.remove(callback)

    def settle(self):
        """Test adapter: let the chat agent finish all queued work and deliver the events."""
        self._api.settle()
        self._forward()
