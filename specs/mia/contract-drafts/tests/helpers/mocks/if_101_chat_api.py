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
ITEM_KINDS = ("tasks", "memos", "memory")             # v1
CATEGORIES = ("answer_quality", "reactions", "character_behaviour", "service")
TRUST = {"example.org": 0.5, "wikipedia.org": 0.8}
MIN_PASSWORD = 8


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
        self._votes = []                              # v1: {"user", "subject", "category", "value", "created"}
        self._items = {kind: {} for kind in ITEM_KINDS}    # v1: kind -> id -> {"id", "text", "source"?, "created", "author"}
        self._trust = dict(TRUST)                     # v1: source id -> value 0..1
        self._persona = {"text": "MIA is a friendly, curious assistant."}
        self._variant = None
        self._regenerate = set()                      # ids of queued user messages whose answer is a new try

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
        if client_id:
            message["client_id"] = client_id              # v1: the page finds its own message again by the id it made up
        self._broadcast("chat_message", message)
        self._queue.append(message["id"])
        self._owner[message["id"]] = user
        self._broadcast("chat_status", self._status())
        return {"id": message["id"], "position": len(self._queue), "message": dict(message)}

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

    # ------------------------------------------------------------ v1: account, answers, votes, records, trust, persona
    def whoami(self, session):
        """The account of a kept session (the page asks after a reload)."""
        return {"user": self._user(session)}

    def logout(self, session):
        """v2: end the session; the same token is unauthenticated afterwards."""
        self._user(session)
        del self._sessions[session]
        self._events.pop(session, None)
        return {"loggedOut": True}

    def change_password(self, session, old, new):
        """The user's own password: the old one must be right; the new one has at least MIN_PASSWORD characters."""
        user = self._user(session)
        if self.accounts.get(user) != old:
            raise ApiError(401, "bad_credentials")
        if not isinstance(new, str) or len(new) < MIN_PASSWORD:
            raise ApiError(422, "weak_password")
        self.accounts[user] = new
        return {"changed": True}

    def regenerate(self, session, message_id):
        """A new try for the last answer: queued like a message; the answer is a new message, the old one stays in the history."""
        user = self._user(session)
        if message_id not in [m["id"] for m in self._history]:
            raise ApiError(404, "not_found")
        answers = [m for m in self._history if m["role"] == "assistant"]
        if not answers or answers[-1]["id"] != message_id:
            raise ApiError(422, "not_the_last_answer")
        if len(self._queue) >= self.queue_limit or sum(1 for i in self._queue if self._owner.get(i) == user) >= self.user_limit:
            raise ApiError(503, "queue_full")
        asked = [m for m in self._history if m["role"] == "user"][-1]["id"]
        key = "r%d" % (self._ids + 1)
        self._queue.append(key)
        self._owner[key] = user
        self._regenerate.add(key)
        self._broadcast("chat_status", self._status())
        return {"position": len(self._queue), "asked": asked}

    def speak_again(self, session, message_id):
        """The spoken form of any answer: one audio_chunk per sentence for every connected page (the one that owns the voice plays them)."""
        self._user(session)
        record = next((m for m in self._history if m["id"] == message_id and m["role"] == "assistant"), None)
        if record is None:
            raise ApiError(404, "not_found")
        sentences = [s for s in record["text"].replace("?", "?|").replace(".", ".|").replace("!", "!|").split("|") if s.strip()]
        for index, sentence in enumerate(sentences):
            self._broadcast("audio_chunk", {"id": record["id"], "index": index, "sentence": sentence.strip()})
        return {"sentences": len(sentences)}

    def account(self, session, message_id):
        """The step-by-step account of an answer: plain sentences in order (from the run log, IF-401)."""
        self._user(session)
        record = next((m for m in self._history if m["id"] == message_id and m["role"] == "assistant"), None)
        if record is None:
            raise ApiError(404, "not_found")
        return [{"seq": 1, "plain": "Read the question."}, {"seq": 2, "plain": "Answered from what I know."}]

    def vote(self, session, message_id, category, value):
        """A plus or a minus on an answer (or a reaction, a behaviour, the service) with its category; every vote is kept with user and time."""
        user = self._user(session)
        if category not in CATEGORIES or value not in (1, -1) or isinstance(value, bool):
            raise ApiError(422, "invalid_vote", rule="category" if category not in CATEGORIES else "value")
        if category == "answer_quality" and message_id not in [m["id"] for m in self._history]:
            raise ApiError(404, "not_found")
        self._votes.append({"user": user, "subject": message_id, "category": category, "value": value, "created": "t%d" % int(self.now)})
        score = self.score(session)
        self._broadcast("score", score)
        return {"stored": True, "score": score}

    def score(self, session):
        """The scores per category and overall."""
        self._user(session)
        categories = {c: sum(v["value"] for v in self._votes if v["category"] == c) for c in CATEGORIES}
        return {"overall": sum(categories.values()), "categories": categories, "votes": len(self._votes)}

    def items(self, session, kind):
        """All records of tasks, memos or memory, oldest first; every user sees and may change all of them (CON-6)."""
        self._user(session)
        return [dict(i) for i in self._kind(kind).values()]

    def save_item(self, session, kind, item_id, text, source=None):
        """A new record (item_id None) or a change of one; memory records need a source. The others see it at once (event item_changed)."""
        user = self._user(session)
        records = self._kind(kind)
        if not isinstance(text, str) or not text.strip():
            raise ApiError(422, "empty_text")
        if kind == "memory" and not source:
            raise ApiError(422, "invalid_item", rule="source")
        if item_id is not None and item_id not in records:
            raise ApiError(404, "not_found")
        if item_id is None:
            self._ids += 1
            item_id = "%s%d" % (kind[0], self._ids)
        record = {"id": item_id, "text": text, "author": user, "created": "t%d" % int(self.now)}
        if source:
            record["source"] = source
        records[item_id] = record
        self._broadcast("item_changed", {"kind": kind, "id": item_id, "author": user, "deleted": False})
        return dict(record)

    def delete_item(self, session, kind, item_id):
        user = self._user(session)
        records = self._kind(kind)
        if item_id not in records:
            raise ApiError(404, "not_found")
        del records[item_id]
        self._broadcast("item_changed", {"kind": kind, "id": item_id, "author": user, "deleted": True})
        return {"deleted": True}

    def set_trust(self, session, source, value):
        """The trust value of a source (0 to 1); the event carries the old and the new value and the author."""
        user = self._user(session)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
            raise ApiError(422, "invalid_trust")
        old = self._trust.get(source)
        if old is None:
            raise ApiError(404, "not_found")
        self._trust[source] = value
        self._broadcast("trust_changed", {"source": source, "old": old, "new": value, "author": user})
        return {"source": source, "old": old, "new": value}

    def trust(self, session):
        self._user(session)
        return dict(self._trust)

    def persona(self, session):
        self._user(session)
        return dict(self._persona)

    def save_persona(self, session, doc):
        """The shared persona file as data; everybody sees the change without a reload (event persona_changed)."""
        user = self._user(session)
        if not isinstance(doc, dict) or not str(doc.get("text", "")).strip():
            raise ApiError(422, "invalid_persona")
        self._persona = dict(doc)
        self._broadcast("persona_changed", {"author": user})
        return dict(self._persona)

    def run_with_variant(self, variant):
        """Test adapter: the next answer comes from a workflow with a character variant (None = the chat's variant)."""
        self._variant = variant

    def _kind(self, kind):
        if kind not in ITEM_KINDS:
            raise ApiError(404, "unknown_kind")
        return self._items[kind]

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
        self._broadcast("variant", {"name": self._variant})        # v1: the character variant of the workflow that answers, or null
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
