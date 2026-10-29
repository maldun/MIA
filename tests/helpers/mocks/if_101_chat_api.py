"""Mock of IF-101, the chat, expression, audio and REST API of the Backend (protected).
Complexity 3: a stream of events, a queue and a clock. It does not reproduce real model latency, budgets or persistence."""
import collections
import datetime
import re

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
BEHAVIOURS = ("greet", "idle", "no", "talk", "yes")        # v5: the names of `character_behaviour` that can be voted on (the real list is library/behaviours.json)
MIN_PASSWORD = 8
START = datetime.datetime(2026, 1, 5, tzinfo=datetime.timezone.utc)      # a Monday: the mock's clock 0; v4 groups the votes by the ISO week of their time


class ChatApiMock:
    def __init__(self, accounts=None, answers=None, queue_limit=5, user_limit=2, review=("Shall I go on?",)):
        self.accounts = accounts or {"anna": "pw-anna", "ben": "pw-ben", "carl": "pw-carl", "dora": "pw-dora", "emil": "pw-emil"}      # v5: five voters for the counters
        self.answers = list(answers or [])            # each: a list of sentences, or {"sentences": [...], "emotion": "..."}
        self.queue_limit, self.user_limit = queue_limit, user_limit
        self._owner = {}                              # message id -> account of the queued user message
        self.now = 0.0
        self._failed = collections.defaultdict(list)  # account -> times of failed logins
        self._sessions = {}                           # token -> account
        self._events = {}                             # token -> events not yet read
        self._history, self._queue, self._stop_next, self._ids = [], collections.deque(), False, 0
        self._resets = {}                             # v5: behaviour name -> mock time of its last counter reset
        self._votes = []                              # v1: {"user", "subject", "category", "value", "created"}
        self._items = {kind: {} for kind in ITEM_KINDS}    # v1: kind -> id -> {"id", "text", "source"?, "created", "author"}
        self._trust = dict(TRUST)                     # v1: source id -> value 0..1
        self._persona = {"text": "MIA is a friendly, curious assistant."}
        self._variant = None
        self._regenerate = set()                      # ids of queued user messages whose answer is a new try
        self._review_questions = tuple(review)        # v7: the questions a scripted /review asks one after the other before its report "the report"
        self._review = None                           # v7: the running review {"author", "asked", "waiting", "replies", "stop", "id"}
        self._texts = {}                              # id of a queued user message -> its text
        self._options = {}                            # v8: id of a queued /review -> its options
        self._files = {}                              # v8: name -> {"data", "created", "task"}: the files volume

    # ------------------------------------------------------------ test adapter
    def advance_time(self, seconds):
        self.now += seconds

    def settle(self):
        """Answer everything that is queued."""
        while True:
            if self._review is not None:
                if not self._advance_review():
                    self._broadcast("chat_status", self._status())
                    break                                     # v7: the review waits for the answer of its user
            elif self._queue:
                asked = self._queue.popleft()
                if re.match(r"/review\s+\S", self._texts.get(asked, ""), re.I):
                    self._ids += 1
                    self._review = {"author": self._owner.get(asked), "asked": 0, "waiting": False, "replies": [], "stop": False, "id": "m%d" % self._ids, "paused": False,
                                    "mode": "slice" if self._options.get(asked, {}).get("slice") else "run", "files": []}
                    self._card()                                  # v8: the status card; the result (chat_start) comes at the end
                else:
                    self._answer(asked)
            else:
                break
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
        queue_text, queue_options = text, {}
        if re.match(r"/review\s+options\b", text.strip(), re.I):         # v8/v9: `/review options` lists the options, `/review options slice -- q` sets them, a bad one is refused
            head, separator, argument = text.strip()[len("/review"):].strip()[len("options"):].partition("--")
            if not head.strip() and not separator:
                note = self._record("system", "MIA", "Options of /review: slice (flag, default False): work in time slices")
                self._broadcast("chat_message", note)
                return {"id": None, "position": 0, "queued": False, "message": dict(note)}
            if not separator or not argument.strip() or any(token != "slice" for token in head.split()):
                raise ApiError(422, "invalid_command")
            queue_text, queue_options = "/review " + argument.strip(), {"slice": bool(head.split())}      # the stored message keeps the text as it was typed
        review = self._review
        if review is not None and review["waiting"] and user == review["author"] and not text.strip().startswith("/"):
            message = self._record("user", user, text)           # v7: the answer to a waiting review: stored and sent like a message, not queued, not counted for queue_full
            if client_id:
                message["client_id"] = client_id
            self._broadcast("chat_message", message)
            review["replies"].append(text)
            return {"id": message["id"], "position": 0, "queued": False, "message": dict(message)}
        message = self._record("user", user, text)
        if client_id:
            message["client_id"] = client_id              # v1: the page finds its own message again by the id it made up
        self._broadcast("chat_message", message)
        queued = bool(self._queue) or self._review is not None
        self._queue.append(message["id"])
        self._owner[message["id"]] = user
        self._texts[message["id"]] = queue_text
        self._options[message["id"]] = queue_options
        self._broadcast("chat_status", self._status())
        return {"id": message["id"], "position": len(self._queue), "queued": queued, "message": dict(message)}

    def stop(self, session):
        self._user(session)
        if self._review is not None:
            self._review["stop"] = True                       # v7: also while the review waits for an answer
            return {"stopped": True}
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
        if category == "character_behaviour" and message_id not in BEHAVIOURS:
            raise ApiError(422, "invalid_vote", rule="subject")
        # one vote per user, category and subject (REQ-CHA-015): a repeat or a changed mind replaces the earlier one
        self._votes = [v for v in self._votes if (v["user"], v["category"], v["subject"]) != (user, category, message_id)]
        self._votes.append({"user": user, "subject": message_id, "category": category, "value": value, "created": "t%d" % int(self.now), "at": self.now})
        score = self.score(session)
        self._broadcast("score", score)
        return {"stored": True, "score": score}

    def _counter(self, name):
        since = self._resets.get(name)
        values = [v["value"] for v in self._votes if v["category"] == "character_behaviour" and v["subject"] == name and (since is None or v["at"] > since)]
        net = sum(values)
        return {"net": net, "votes": len(values), "chance": 0.002 if net <= -5 else 1.0, "reset_at": None if since is None else "t%d" % int(since)}

    def counters(self, session):
        """v5: the adaptation counters of every behaviour of the list (REQ-BE-030, REQ-BE-031): the net of the votes since the last reset and the chance of showing it."""
        self._user(session)
        return {name: self._counter(name) for name in BEHAVIOURS}

    def reset_counter(self, session, name):
        """v5: back to the default rate; the votes stay, only later ones count."""
        user = self._user(session)
        if name not in BEHAVIOURS:
            raise ApiError(404, "not_found")
        self._resets[name] = self.now
        self._broadcast("counters_changed", {"name": name, "author": user})
        return self._counter(name)

    def score(self, session):
        """The scores per category and overall, and v4: the same sums per ISO week (`series`, oldest first, only weeks with a vote)."""
        self._user(session)
        def sums(votes):
            categories = {c: sum(v["value"] for v in votes if v["category"] == c) for c in CATEGORIES}
            return {"overall": sum(categories.values()), "categories": categories}
        weeks = {}
        for v in self._votes:
            year, week, _ = (START + datetime.timedelta(seconds=v["at"])).isocalendar()
            weeks.setdefault("%d-W%02d" % (year, week), []).append(v)
        series = [dict(week=name, **sums(votes)) for name, votes in sorted(weeks.items())]
        return dict(sums(self._votes), votes=len(self._votes), series=series)

    def items(self, session, kind):
        """All records of tasks, memos or memory, oldest first; every user sees and may change all of them (CON-6)."""
        self._user(session)
        return [dict(i) for i in self._kind(kind).values()]

    def save_item(self, session, kind, item_id, text, source=None, due=None):
        """A new record (item_id None) or a change of one; memory records need a source. The others see it at once (event item_changed)."""
        user = self._user(session)
        records = self._kind(kind)
        if not isinstance(text, str) or not text.strip():
            raise ApiError(422, "empty_text")
        if kind == "memory" and not source:
            raise ApiError(422, "invalid_item", rule="source")
        if due is not None and (kind != "tasks" or not self._valid_due(due)):
            raise ApiError(422, "invalid_item", rule="due")                       # v6: only a task falls due, as UTC to the second
        if item_id is not None and item_id not in records:
            raise ApiError(404, "not_found")
        if item_id is None:
            self._ids += 1
            item_id = "%s%d" % (kind[0], self._ids)
        record = {"id": item_id, "text": text, "author": user, "created": "t%d" % int(self.now)}
        if source:
            record["source"] = source
        if due:
            record["due"] = due
        records[item_id] = record
        self._broadcast("item_changed", {"kind": kind, "id": item_id, "author": user, "deleted": False})
        return dict(record)

    @staticmethod
    def _valid_due(due):
        if not isinstance(due, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", due):
            return False
        try:
            datetime.datetime.strptime(due, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return False
        return True

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

    def _advance_review(self):
        """v7: one step of the scripted review: end it on stop, take a waiting reply, ask the next question, or give the report. False = it waits for the answer."""
        review = self._review
        if review["stop"]:
            return self._end_review("stopped")                # the report as it stands
        if review["paused"]:
            return False                                      # v8: a paused task starts no step
        if review["waiting"]:
            if not review["replies"]:
                return False
            review["replies"].pop(0)
            review["waiting"] = False
        if review["asked"] < len(self._review_questions):
            question = self._record("assistant", "MIA", self._review_questions[review["asked"]])
            review["asked"] += 1
            review["waiting"] = True
            self._broadcast("chat_message", question)
            return False
        return self._end_review("done")

    def _end_review(self, status):
        name = "review-contract.md"
        self._files[name] = {"data": b"# the report\n", "created": "t%d" % int(self.now), "task": "review", "message_id": self._review["id"]}
        self._broadcast("files_changed", {"name": name, "task": "review"})
        self._review["files"].append(name)
        record = {"id": self._review["id"], "role": "assistant", "sender": "MIA", "text": "the report", "created": "t%d" % int(self.now)}
        self._history.append(record)
        self._broadcast("chat_start", {"id": record["id"], "role": "assistant", "task": "review"})      # v8: the result is the newest message
        self._broadcast("chat_delta", {"id": record["id"], "text": "the report"})
        self._broadcast("chat_done", {"id": record["id"], "text": "the report", "emotion": "neutral", "status": status, "files": list(self._review["files"])})
        self._card(done=True)
        self._review = None
        return True

    def _card(self, done=False):
        """v8: the status card of the running task"""
        review = self._review
        self._broadcast("task_status", {"id": review["id"], "task": "review", "phase": "working", "mode": review["mode"], "paused": review["paused"], "done": done,
                                        "budget": {"seconds": {"used": round(self.now, 1)}}, "counts": {}})

    def pause(self, session):
        """v8: pauses the running task; False when nothing runs"""
        self._user(session)
        if self._review is None or self._review["paused"]:
            return {"paused": False}
        self._review["paused"] = True
        self._card()
        return {"paused": True}

    def resume(self, session):
        self._user(session)
        if self._review is not None and self._review["paused"]:
            self._review["paused"] = False
            self._card()
        return {"paused": False}

    def files(self, session):
        """v8: the files of the files volume, newest first"""
        self._user(session)
        return [{"name": n, "size": len(f["data"]), "created": f["created"], "task": f["task"], "message_id": f.get("message_id")} for n, f in reversed(list(self._files.items()))]

    def file(self, session, name):
        self._user(session)
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}", name) or ".." in name:
            raise ApiError(422, "invalid_file_name")
        if name not in self._files:
            raise ApiError(404, "not_found")
        return self._files[name]["data"]

    def _status(self):
        waiting = self._review is not None and self._review["waiting"]
        return {"busy": bool(self._queue) or self._review is not None, "activity": "waiting" if waiting else "idle", "queue": len(self._queue)}

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
