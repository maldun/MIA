"""Mock of IF-101, the chat, expression, audio and REST API of the Backend (protected).
Complexity 3: a stream of events, a queue and a clock. It does not reproduce real model latency, budgets or persistence."""
import collections

try:
    from .errors import ApiError
except ImportError:
    from errors import ApiError

MAX_FAILED_LOGINS = 5
THROTTLE_SECONDS = 60
MAX_TEXT = 4000


class ChatApiMock:
    def __init__(self, accounts=None, answers=None, queue_limit=5, user_limit=2):
        self.accounts = accounts or {"anna": "pw-anna", "ben": "pw-ben"}
        self.answers = list(answers or [])            # each: a list of sentences, or {"sentences": [...], "emotion": "..."}
        self.queue_limit, self.user_limit = queue_limit, user_limit
        self._owner = {}                              # message id -> account of the queued user message
        self.now = 0.0
        self._failed = collections.defaultdict(list)  # account -> times of failed logins
        self._sessions = {}                           # token -> account
        self._events = {}                             # token -> events not yet read
        self._history, self._queue, self._stop_next, self._ids = [], collections.deque(), False, 0

    # ------------------------------------------------------------ test adapter
    def advance_time(self, seconds):
        self.now += seconds

    def settle(self):
        """Answer everything that is queued."""
        while self._queue:
            self._answer(self._queue.popleft())
            self._broadcast("chat_status", self._status())

    # ------------------------------------------------------------ the interface
    def login(self, user, password):
        failures = [t for t in self._failed[user] if self.now - t < THROTTLE_SECONDS]
        self._failed[user] = failures
        if len(failures) >= MAX_FAILED_LOGINS:
            raise ApiError(429, "throttled")
        if self.accounts.get(user) != password:
            self._failed[user].append(self.now)
            raise ApiError(401, "bad_credentials")
        token = "t%d" % (len(self._sessions) + 1)
        self._sessions[token] = user
        return token

    def connect(self, session):
        self._user(session)
        self._events[session] = [{"event": "chat_status", "payload": self._status()}]

    def send(self, session, text, client_id=None):
        user = self._user(session)
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT:
            raise ApiError(422, "empty_text")
        if len(self._queue) >= self.queue_limit or sum(1 for i in self._queue if self._owner.get(i) == user) >= self.user_limit:
            raise ApiError(503, "queue_full")
        message = self._record("user", user, text)
        self._broadcast("chat_message", message)
        self._queue.append(message["id"])
        self._owner[message["id"]] = user
        self._broadcast("chat_status", self._status())
        return {"id": message["id"], "position": len(self._queue)}

    def stop(self, session):
        self._user(session)
        if not self._queue:
            return {"stopped": False}
        self._stop_next = True
        return {"stopped": True}

    def history(self, session, limit=50):
        self._user(session)
        return [dict(m) for m in self._history[-limit:]]

    def events(self, session):
        self._user(session)
        out, self._events[session] = self._events.get(session, []), []
        return out

    # ------------------------------------------------------------ inside
    def _user(self, session):
        if session not in self._sessions:
            raise ApiError(401, "unauthenticated")
        return self._sessions[session]

    def _record(self, role, sender, text):
        self._ids += 1
        record = {"id": "m%d" % self._ids, "role": role, "sender": sender, "text": text, "created": "t%d" % int(self.now)}
        self._history.append(record)
        return record

    def _status(self):
        return {"busy": bool(self._queue), "queue": len(self._queue)}

    def _broadcast(self, event, payload):
        for session in self._sessions:
            self._events.setdefault(session, []).append({"event": event, "payload": payload})

    def _answer(self, _asked_id):
        script = self.answers.pop(0) if self.answers else ["Hello."]
        sentences = script["sentences"] if isinstance(script, dict) else script
        emotion = script.get("emotion", "neutral") if isinstance(script, dict) else "neutral"
        record = self._record("assistant", "MIA", "")
        self._broadcast("chat_start", {"id": record["id"], "role": "assistant"})
        self._broadcast("expression", {"name": emotion})
        text, status = "", "done"
        for index, sentence in enumerate(sentences):
            if self._stop_next:
                status = "stopped"
                break
            text = (text + " " + sentence).strip()
            self._broadcast("chat_delta", {"id": record["id"], "text": text})
            self._broadcast("audio_chunk", {"id": record["id"], "index": index, "sentence": sentence})
        self._stop_next = False
        record["text"] = text
        self._broadcast("chat_done", {"id": record["id"], "text": text, "emotion": emotion, "status": status})
