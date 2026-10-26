"""Mock of IF-201, the chat turn service of the Chat agent (protected). Complexity 3: a queue and an event stream.
Built on the mock of IF-101 with one internal session; it does not model persona, mood, memory or model latency."""
try:
    from .errors import ApiError, ServiceError
    from .if_101_chat_api import ChatApiMock
except ImportError:
    from errors import ApiError, ServiceError
    from if_101_chat_api import ChatApiMock

CODES = {"empty_text": "empty_text", "queue_full": "queue_full"}


class ChatTurnMock:
    def __init__(self, answers=None, queue_limit=5):
        self._api = ChatApiMock(accounts={"anna": "pw", "ben": "pw"}, answers=answers, queue_limit=queue_limit)
        self._sessions = {name: self._api.login(name, "pw") for name in ("anna", "ben")}
        self._observer = self._sessions["ben"]
        self._api.connect(self._observer)
        self._callbacks = []
        self._api.events(self._observer)

    def _call(self, fn):
        try:
            return fn()
        except ApiError as err:
            raise ServiceError(CODES.get(err.code, err.code))

    def _forward(self):
        for event in self._api.events(self._observer):
            for callback in list(self._callbacks):
                callback(event)

    def send(self, account, text, client_id=None):
        result = self._call(lambda: self._api.send(self._sessions[account], text, client_id))
        self._forward()
        return result

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
