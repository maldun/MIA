#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIA - MIA Is not an Assistant
#Copyright (C) 2017  Stefan Reiterer

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
The conversation as messages (ui/REQUIREMENTS_CHAT.md 6): the page sends text, the server runs the exchange in the
background (one at a time, one more may wait), and pushes the result to all connected pages:

  chat_message  a complete message (yours, system notes, automatic MIA messages)
  chat_start    MIA starts a message           chat_delta  the text so far (cumulative)
  chat_done     the message is finished        chat_status {busy, activity, model, profile, queue, mood}
  chat_pipeline {id, event}  a step of the pipeline that makes the answer (only for skills with a status block, see pipeline_event)
  chat_error    a human readable problem

The service knows nothing about Flask or the model: `emit(event, payload)` and `run_exchange(text, on_delta,
on_emotion, should_stop)` are given to it (web_app.py), which makes it testable with a fake model.
"""
import collections
import datetime
import json
import queue
import random
import re
import threading
import time

try:
    from .chat_log import utc_now, MAX_PAGE
    from .record_tables import CATEGORIES
    from .storage import StorageError
    from .speech_text import speech_text
    from .task_monitor import TaskMonitor
    from .task_registry import TaskCommandError, TaskRegistry
except ImportError:  # used as plain script / in tests
    from chat_log import utc_now, MAX_PAGE
    from record_tables import CATEGORIES
    from storage import StorageError
    from speech_text import speech_text
    from task_monitor import TaskMonitor
    from task_registry import TaskCommandError, TaskRegistry

MAX_LENGTH = 8000
DELTA_INTERVAL = 0.05          # at most about 20 deltas per second per message
CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

COMMANDS = (
    {"command": "/light!", "description": "Switch to the small model (saves GPU memory)", "confirm": False},
    {"command": "/full!", "description": "Switch back to the large model", "confirm": False},
    {"command": "/dream!", "description": "Sort and summarize MIA's memory", "confirm": False},
    {"command": "/time!", "description": "Send the current time to MIA", "confirm": False},
    {"command": "/tasks", "description": "Read all tasks back, word for word", "confirm": False},
    {"command": "/memos", "description": "Read all memos back, word for word", "confirm": False},
    {"command": "/goodnight!", "description": "Dream, then shut MIA down", "confirm": True},
    {"command": "/break!", "description": "Shut MIA down", "confirm": True},
)


SETTLED_END = re.compile(r"[.!?](?=\s|$)|(?=\n)")      # a sentence end, or the place of a line end


def settled(text):
    """the longest prefix of a growing answer that no behaviour rule can still change: it ends at a sentence or line end and has no open emphasis, code or bracket span"""
    for end in reversed([m.end() for m in SETTLED_END.finditer(text)]):
        prefix = text[:end]
        bold, single = prefix.count("**"), prefix.replace("**", "").count("*")      # an unclosed ** is as open as an unclosed *
        if bold % 2 == 0 and single % 2 == 0 and prefix.count("`") % 2 == 0 and prefix.count("(") <= prefix.count(")") and prefix.count("[") <= prefix.count("]"):
            return prefix
    return ""


RECITED_BY_COMMAND ={"/tasks": "tasks", "/memos": "memos"}
RECITED = tuple(RECITED_BY_COMMAND.values())


def normalize_text(text):
    """strips control characters and surrounding blanks; returns "" for anything that is not text"""
    if not isinstance(text, str):
        return ""
    return CONTROL_CHARACTERS.sub("", text).strip()
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


NET_NEGATIVE = 5               # REQ-CHA-017: from this many net negative votes a behaviour is shown only rarely
RARE_CHANCE = 0.002            # at most 1 % is required; a chance of exactly 1 % would break "at most 10 in 1000 opportunities" in about 4 of 10 checks


def show_chance(net):
    """the chance that a behaviour is shown at one opportunity: always, until it has NET_NEGATIVE net negative votes; plus votes raise the net and so the chance again"""
    return RARE_CHANCE if net <= -NET_NEGATIVE else 1.0


def behaviours_from_file(path):
    """() -> the names of the file {"behaviours": [...]}; read at every call so the list may change while MIA runs; a missing or broken file gives an empty list"""
    def read():
        try:
            with open(path, encoding="utf-8") as fp:
                names = json.load(fp).get("behaviours", [])
        except (OSError, ValueError, AttributeError):
            return []
        return [name for name in names if isinstance(name, str)] if isinstance(names, list) else []
    return read


class ChatError(Exception):
    """a refused operation of IF-201 (v1): `code` is not_found, not_the_last_answer, invalid_vote or queue_full; `rule` names what a vote broke"""
    def __init__(self, code, rule=None):
        super().__init__(code)
        self.code, self.rule = code, rule


class ChatService:
    def __init__(self, emit, log, mood, run_exchange, run_command=None, model_info=None, queue_size=1, user_limit=0,
                 rate_limit=(10, 60), spawn=None, clock=time.monotonic, votes=None, wall_clock=time.time,
                 behaviours=None, reputable=0.6, repair=None, remember=None, review_timeout=1800,
                 tasks=None, skill_options=None, prepare_task=None, argument_commands=None, files=None, unavailable=()):
        self._emit = emit
        self._tasks = tasks if tasks is not None else TaskRegistry()      # REQ-WFM-029: the tasks (lookup, search, review, ...) register themselves, the core names none of them
        self._unavailable = {str(n).lower() for n in unavailable}         # ids of extensions that did not load: their command says so instead of going to the model
        self._skill_options = skill_options or {}                          # config `skill_options`: {task id: {option: value}}, the defaults of the options
        self._prepare_task = prepare_task                                  # (task, options, ask) -> options: before a task runs, e.g. the class of the model; may ask the user
        self._argument_commands = {k.lower(): v for k, v in (argument_commands or {}).items()}      # {name: fn(argument) -> text}: commands with an argument, e.g. /model paid <name>
        self._files = files                                                # the files volume (file_store.FileStore), None = tasks cannot store files
        self._monitor = None                                               # the status card of the running task
        self._late = False                                                 # the running task gives its result at the end (it asks questions)
        self._task_files = []                                              # the names of the files that the running task stored: chat_done names them
        self._review_timeout = review_timeout      # seconds a review waits for the answer of the user; no answer in time is "no"
        self._waiter = None                        # {"author", "replies"}: the question of a running review that waits for its answer
        self._author = None                        # the account whose task runs
        self.log = log
        self.mood = mood
        self._run_exchange = run_exchange
        self._run_command = run_command
        self._model_info = model_info or (lambda: (None, None))
        self.queue_size = max(0, int(queue_size))
        self.user_limit = max(0, int(user_limit))          # waiting messages per account (IF-101: 2); 0 = no limit
        self._rate_count, self._rate_window = rate_limit
        self._spawn = spawn or (lambda target: threading.Thread(target=target, daemon=True).start())
        self._clock = clock
        self._votes = votes                    # the Storage layer (IF-102): the votes table
        self._wall_clock = wall_clock          # seconds since the epoch; the time of a vote and so its week
        self._repair = repair                  # text -> the text with the violations of the behaviour rules repaired (behaviour.py); None = answers are streamed as they come
        self._behaviours = behaviours          # () -> the names of the behaviours that can be voted on (REQ-CHA-017); read at every use, the list may change; None: no list
        self._remember = remember              # (account, message_id, text) -> ids: the structured memory (REQ-CHA-011); called after a plain chat turn is done, None = off
        self._reputable = reputable            # a source with at least this trust is reputable (owner 2026-10-27: a fact has at least one reputable source)
        self._lock = threading.RLock()
        self._queue = collections.deque()
        self._running = False
        self._current = None
        self._stop = threading.Event()
        self._unpaused = threading.Event()
        self._unpaused.set()
        self._hits = collections.defaultdict(collections.deque)
        self._commands = {c["command"] for c in COMMANDS}
        self._message_id = None          # the answer in progress: pipeline events belong to it
        self._pipeline = []
        self._sources = []
        self._show_pipeline = False

    # --- state -----------------------------------------------------------------------------------
    def is_command(self, text):
        return text.strip().lower() in self._commands

    def status(self):
        model, profile = self._model_info()
        mood = self.mood.status()
        with self._lock:
            return {"busy": self._running, "activity": mood["activity"] or "idle", "model": model, "profile": profile,
                    "queue": len(self._queue), "mood": mood}

    def publish_status(self):
        self._emit("chat_status", self.status())

    def set_activity(self, activity):
        if self.mood.set_activity(activity):
            self.publish_status()

    # --- the page sends -------------------------------------------------------------------------------
    def _rate_limited(self, key):
        if not self._rate_count:
            return False
        now = self._clock()
        hits = self._hits[key]
        while hits and now - hits[0] > self._rate_window:
            hits.popleft()
        if len(hits) >= self._rate_count:
            return True
        hits.append(now)
        return False

    def send(self, text, client_id=None, sender="page", author=None):
        """accepts a message; returns the acknowledgement for the page: {"ok", "message" | "error", "queued"}.
        sender is the key of the rate limit (a connection or an account); author the account that wrote it, stored as the `sender` of the message (IF-101)"""
        text = normalize_text(text)
        if not text:
            return {"ok": False, "error": "The message is empty.", "code": "empty_text"}
        if len(text) > MAX_LENGTH:
            return {"ok": False, "error": "The message is too long (at most %d characters)." % MAX_LENGTH, "code": "empty_text"}
        if self._rate_limited(sender):
            return {"ok": False, "error": "Too many messages, please wait a moment."}
        with self._lock:
            own = sum(1 for item in self._queue if author and item[2] == author)
            if self._running and (len(self._queue) >= self.queue_size or (self.user_limit and author and own >= self.user_limit)):
                return {"ok": False, "error": "MIA is busy, please wait until she has answered.", "code": "queue_full"}
            command = self.is_command(text)
            given = re.fullmatch(r"/(\w+)(?:\s+(.*))?", text.strip(), re.S)
            if given and given.group(1).lower() in self._argument_commands:
                try:
                    answer = self._argument_commands[given.group(1).lower()]((given.group(2) or "").strip())
                except ValueError as exc:
                    answer = str(exc)
                self.note(answer, command=text.strip())
                return {"ok": True, "message": None, "queued": False, "command": True, "id": None, "position": 0}
            try:
                parsed = self._tasks.parse(text, self._skill_options)
            except TaskCommandError as exc:
                return {"ok": False, "error": str(exc), "code": "invalid_command"}
            gone = re.match(r"/(\w+)", text.strip())
            if parsed is None and gone and gone.group(1).lower() in self._unavailable:
                return {"ok": False, "error": "%s is not available." % gone.group(1).capitalize()}
            if parsed is not None and parsed["help"]:
                self.note(parsed["text"], command=text.strip())
                return {"ok": True, "message": None, "queued": False, "command": True, "id": None, "position": 0}
            task, argument, options = (parsed["task"], parsed["argument"], parsed["options"]) if parsed else (None, None, None)
            waiter = self._waiter
            if waiter is not None and not command and task is None and (not waiter["author"] or author == waiter["author"]):
                fields = dict(({"client_id": client_id} if client_id else {}), **({"sender": author} if author else {}))
                record = self.log.append("user", text, **fields)             # the reply to a question of the review is a message like any other, but it is not queued behind the review
                self._emit("chat_message", record)
                waiter["replies"].put(text)
                return {"ok": True, "message": record, "queued": False, "command": False, "id": record["id"], "position": 0}
            record = None
            if not command:
                fields = dict(({"client_id": client_id} if client_id else {}), **({"sender": author} if author else {}))
                record = self.log.append("user", text, **fields)
                self._emit("chat_message", record)
            queued = self._running
            self._queue.append(("command" if command else task if task is not None else "chat", argument if task is not None else text, author, author, record["id"] if record else None, options))
            position = len(self._queue)
            self._start_worker()
        self.publish_status()
        if parsed is not None and parsed["name"] != parsed["task"]:
            self.note("/%s is now called /%s; the old name still works." % (parsed["name"], parsed["task"]))
        return {"ok": True, "message": record, "queued": queued, "command": command, "id": record["id"] if record else None, "position": position}

    def stop(self):
        """stops the running answer (the text received so far stays)"""
        with self._lock:
            running = self._running and self._current != "command"
        if running:
            self._stop.set()
            self._unpaused.set()                      # a paused task wakes up and sees the stop
        return running

    def _file_putter(self, task, message_id):
        def put(name, data):
            if self._files is None:
                raise RuntimeError("no files volume is configured")
            info = self._files.put(name, data, task=task, message_id=message_id, account=self._author)
            self._task_files.append(info["name"])
            self._emit("files_changed", {"name": info["name"], "task": task})
            return info["name"]
        return put

    def _report_saver(self, entry, message_id, model):
        def save(question, report):
            if self._votes is None:
                raise RuntimeError("no storage is configured")
            self._votes.put("reports", message_id, {"task": entry.id, "skill": entry.id, "skill_version": entry.version, "question": question, "account": self._author or "page",
                                                    "model_pin": model or "unknown", "report": report}, self._author or "page")
        return save

    def _stopped(self):
        """should_stop for a task: waits here while the task is paused (so it starts no new step), then says whether it was stopped"""
        while not self._unpaused.wait(0.1):
            if self._stop.is_set():
                break
        return self._stop.is_set()

    def pause(self):
        """pauses the running task: it starts no new step (its should_stop() waits) and its time stops (REQ-WFM-033); False when no task runs"""
        with self._lock:
            monitor = self._monitor
        if monitor is None or monitor.paused:
            return False
        self._unpaused.clear()
        monitor.pause()
        return True

    def resume(self):
        with self._lock:
            monitor = self._monitor
        if monitor is None or not monitor.paused:
            return False
        monitor.resume()
        self._unpaused.set()
        return True

    def commands(self):
        """the commands for the page: the fixed ones and one for each task of the registry"""
        tasks = self._tasks.commands()
        ids = {c["command"].strip() for c in tasks}
        return [c for c in COMMANDS if c["command"].strip() not in ids] + tasks

    # --- operations on answers and votes (IF-201 v1) --------------------------------------------------------
    def _find(self, message_id):
        before = None
        while True:
            records, older = self.log.history(before=before, limit=MAX_PAGE)
            for record in records:
                if record["id"] == message_id:
                    return record
            if not older:
                return None
            before = records[0]["id"]

    def _answer(self, message_id):
        record = self._find(message_id)
        if record is None or record["role"] != "assistant":
            raise ChatError("not_found")
        return record

    def regenerate(self, account, message_id):
        """a new try for the last answer, queued like a message; the old answer stays and the question is not stored again"""
        record = self._find(message_id)
        if record is None:
            raise ChatError("not_found")
        if record["role"] != "assistant" or self.log.last("assistant")["id"] != record["id"]:
            raise ChatError("not_the_last_answer")
        records = self.log.history(before=record["id"], limit=MAX_PAGE)[0]
        asked = next((m for m in reversed(records) if m["role"] == "user"), None)
        if asked is None:
            raise ChatError("not_found")
        with self._lock:
            own = sum(1 for item in self._queue if item[2] == account)
            if self._running and (len(self._queue) >= self.queue_size or (self.user_limit and own >= self.user_limit)):
                raise ChatError("queue_full")
            self._queue.append(("chat", asked["text"], account, asked.get("sender"), None, None))        # the answer names who asked, not who clicked
            position = len(self._queue)
            self._start_worker()
        self.publish_status()
        return {"position": position, "asked": asked["id"]}

    def speak_again(self, message_id):
        """one audio_chunk per sentence of any answer; the page that owns the voice plays them"""
        record = self._answer(message_id)
        sentences = [s for s in SENTENCE_END.split(speech_text(record["text"])) if s]
        for index, sentence in enumerate(sentences):
            self._emit("audio_chunk", {"id": record["id"], "index": index, "sentence": sentence})
        return {"sentences": len(sentences)}

    def account(self, message_id):
        """the plain steps kept with the answer, in order; the domain events of the run log (kind "event") are no steps"""
        record = self._answer(message_id)
        plain = [e["plain"] for e in record.get("pipeline", []) if e.get("kind") != "event" and e.get("plain")]
        return [{"seq": i, "plain": text} for i, text in enumerate(plain or ["No steps were kept for this answer."], 1)]

    def vote(self, account, subject, category, value):
        """a plus or a minus, kept with user, time, subject and category (REQ-CHA-015); the score event follows"""
        if category not in CATEGORIES:
            raise ChatError("invalid_vote", "category")
        if isinstance(value, bool) or value not in (1, -1):
            raise ChatError("invalid_vote", "value")
        record = self._answer(subject) if category == "answer_quality" else None
        if category == "character_behaviour" and self._behaviours is not None and subject not in self._behaviours():
            raise ChatError("invalid_vote", "subject")
        created = datetime.datetime.fromtimestamp(self._wall_clock(), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # one record per user, category and subject: a repeated click or a changed mind is a new version of it, not a second vote
        self._votes.put("votes", "%s|%s|%s" % (account, category, subject), {"user": account, "subject": subject, "category": category, "value": value, "created": created}, account)
        if record is not None and value == -1 and self.is_fact(record):
            self._open_case(record, account, created)
        if category == "character_behaviour" and self._behaviours is not None:
            self._keep_counter(subject, account)
        score = self.score()
        self._emit("score", score)
        self.mood.set_score(score["overall"])          # the feedback shifts the general mood (REQ-CHA-010)
        self.publish_status()
        return {"stored": True, "score": score}

    # --- tasks and memos read back from their records (REQ-CHA-019) ---------------------------------------------------
    def _item(self, kind, item_id):
        if kind not in RECITED:
            raise ChatError("not_found")
        try:
            return self._votes.get(kind, item_id)["doc"]
        except StorageError:
            raise ChatError("not_found")

    def recite(self, kind, item_id):
        """the text of a task or memo exactly as stored: code reads it, the model is never asked (FR-28)"""
        return {"id": item_id, "kind": kind, "text": self._item(kind, item_id)["text"]}

    def recite_all(self, kind):
        """every task or memo as a message of its own, oldest first; returns how many"""
        if kind not in RECITED:
            raise ChatError("not_found")
        ids = sorted(self._votes.ids(kind))
        for item_id in ids:
            self.post_assistant(self._item(kind, item_id)["text"])
        return len(ids)

    def recite_due(self):
        """says the text of every task that has fallen due (field `due`, ISO time) once and marks it `recited`; returns how many. Called by the time check."""
        now = datetime.datetime.fromtimestamp(self._wall_clock(), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        count = 0
        for item_id in sorted(self._votes.ids("tasks")):
            doc = self._item("tasks", item_id)
            if isinstance(doc.get("due"), str) and doc["due"] <= now and not doc.get("recited"):
                self.post_assistant(doc["text"], auto=True)
                self._votes.put("tasks", item_id, dict(doc, recited=now), "MIA")          # after the message: a crash in between says it twice, never not at all
                count += 1
        return count

    # --- a minus on a fact, adaptation, counters (REQ-CHA-016 to -018) ----------------------------------------------
    def note_sources(self, sources):
        """the sources behind the answer in progress, [{"url", "trust"}], reported by the lookup skill; kept with the answer"""
        with self._lock:
            if self._message_id is not None:
                self._sources = [dict(source) for source in sources]

    def is_fact(self, record):
        """an answer is factual when at least one of its sources is reputable; it can still be wrong, but it has a source"""
        return any(isinstance(s, dict) and s.get("trust", 0) >= self._reputable for s in record.get("sources") or [])

    def _open_case(self, record, account, created):
        """a proposed benchmark case, one per answer; the answer itself stays as it is. A person labels it later (the eval rules)."""
        asked = None
        for message in reversed(self.log.history(before=record["id"], limit=MAX_PAGE)[0]):
            if message["role"] == "user":
                asked = message["text"]
                break
        try:
            case = self._votes.get("cases", record["id"])["doc"]
        except StorageError:
            case = {"question": asked or "", "answer": record["text"], "sources": record.get("sources", []), "status": "proposed", "created": created, "voters": []}
        if account not in case["voters"]:
            case["voters"].append(account)
        self._votes.put("cases", record["id"], case, account)

    def _names(self):
        return list(self._behaviours()) if self._behaviours is not None else []

    def _state(self, name):
        """net, votes and chance of a behaviour, counted from the votes since its last reset (a vote of the same second as the reset counts as before it)"""
        try:
            reset_at = self._votes.get("behaviours", name)["doc"].get("reset_at")
        except StorageError:
            reset_at = None
        values = []
        for vote_id in self._votes.ids("votes"):
            vote = self._votes.get("votes", vote_id)["doc"]
            if vote["category"] == "character_behaviour" and vote["subject"] == name and (reset_at is None or vote["created"] > reset_at):
                values.append(vote["value"])
        return {"net": sum(values), "votes": len(values), "chance": show_chance(sum(values)), "reset_at": reset_at}

    def _keep_counter(self, name, author):
        state = self._state(name)
        self._votes.put("behaviours", name, {"name": name, "net": state["net"], "votes": state["votes"], "reset_at": state["reset_at"]}, author)

    def counters(self):
        """the adaptation counters of every behaviour of the list, for every user to see"""
        return {name: self._state(name) for name in self._names()}

    def reset_counter(self, account, name):
        """back to the default rate; the votes stay in the table, only those after the reset count"""
        if name not in self._names():
            raise ChatError("not_found")
        now = datetime.datetime.fromtimestamp(self._wall_clock(), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._votes.put("behaviours", name, {"name": name, "net": 0, "votes": 0, "reset_at": now}, account)
        self._emit("counters_changed", {"name": name, "author": account})
        return self._state(name)

    def show_behaviour(self, name, rng=random.random):
        """one opportunity to show a behaviour: True if it is shown. What is not on the list (a fact, a safety check) is always shown."""
        if name not in self._names():
            return True
        try:
            net = self._votes.get("behaviours", name)["doc"]["net"]            # the kept counter: an opportunity must not count all votes again
        except StorageError:
            net = 0
        return rng() < show_chance(net)

    def score(self):
        """sums per category and overall, and the same per ISO week of the vote (oldest first, only weeks with a vote)"""
        def sums(votes):
            categories = {c: sum(v["value"] for v in votes if v["category"] == c) for c in CATEGORIES}
            return {"overall": sum(categories.values()), "categories": categories}
        votes = [self._votes.get("votes", i)["doc"] for i in self._votes.ids("votes")]
        weeks = {}
        for vote in votes:
            year, week, _ = datetime.datetime.strptime(vote["created"], "%Y-%m-%dT%H:%M:%SZ").isocalendar()
            weeks.setdefault("%d-W%02d" % (year, week), []).append(vote)
        return dict(sums(votes), votes=len(votes), series=[dict(week=name, **sums(group)) for name, group in sorted(weeks.items())])

    # --- the steps of the pipeline behind an answer --------------------------------------------------------------
    def pipeline_event(self, event):
        """an event of the pipeline runner (pipeline.py); shown in the status block of the answer when the skill wants one, and kept in the log record"""
        if event.get("kind") == "event":
            return                              # domain events (events.py) belong to the run log; the block shows the steps
        with self._lock:
            message_id = self._message_id
            if message_id is None:
                return
            if event.get("kind") == "run_start":
                self._show_pipeline = bool((event.get("payload") or {}).get("show"))
            if self._late:
                if self._monitor is not None and event.get("plain"):
                    self._monitor.update(phase=event["plain"])          # the progress of a task with a card is the card, not a message
                return
            if not self._show_pipeline:
                return
            self._pipeline.append(event)
        self._emit("chat_pipeline", {"id": message_id, "event": event})

    # --- messages that do not come from the page -----------------------------------------------------------
    def note(self, text, **fields):
        record = self.log.append("system", text, markdown=False, **fields)
        self._emit("chat_message", record)
        return record

    def post_assistant(self, text, emotion=None, auto=False):
        """a finished message of MIA that was not an answer to the page (the hourly time check, ...)"""
        record = self.log.append("assistant", text, emotion=emotion, auto=auto, model=self._model_info()[0])
        self._emit("chat_message", record)
        if emotion and self.mood.set_emotion(emotion):
            self.publish_status()
        return record

    def ask(self, text):
        """a question of a running review: posts it as a message of MIA and waits for the next message of the same account (send() hands it over); None when the run is stopped or
        nothing came in review_timeout seconds"""
        waiter = {"author": self._author, "replies": queue.Queue()}
        with self._lock:
            self._waiter = waiter
        self.post_assistant(text)
        self.set_activity("waiting")
        reply, end = None, self._clock() + self._review_timeout
        try:
            while reply is None and not self._stop.is_set() and self._clock() < end:
                try:
                    reply = waiter["replies"].get(timeout=0.1)
                except queue.Empty:
                    pass
        finally:
            with self._lock:
                self._waiter = None
            self.set_activity("thinking")
        return reply

    # --- background work ------------------------------------------------------------------------------
    def _start_worker(self):
        if self._running:
            return
        self._running = True
        self._spawn(self._work)

    def _work(self):
        while True:
            with self._lock:
                if not self._queue:
                    self._running = False
                    self._current = None
                    break
                kind, text, _author, speaker, message_id, options = self._queue.popleft()
                self._current, self._author = kind, _author
                self._stop.clear()
            try:
                self._do_command(text) if kind == "command" else self._do_chat(text, kind, speaker, message_id, options)
            except Exception as exc:       # the worker must survive anything
                self.mood.enter("error")                   # reporting an error has its mood (REQ-CHA-009)
                self._emit("chat_error", {"message": "Something went wrong: %s" % exc})
        self.publish_status()

    def _do_command(self, text):
        command = text.strip().lower()
        if command in RECITED_BY_COMMAND:
            kind = RECITED_BY_COMMAND[command]
            if not self.recite_all(kind):
                self.note("No %s are stored." % kind, command=command)
            return
        if command in ("/dream!", "/goodnight!"):
            self.set_activity("dreaming")
        try:
            result = self._run_command(command) if self._run_command else None
        finally:
            self.set_activity(None)
        self.note(result or "Command %s done." % command, command=command)

    def _do_chat(self, text, task="chat", speaker=None, user_message_id=None, options=None):
        message_id = self.log.new_id()
        created = utc_now()
        entry = self._tasks.get(task) if task != "chat" else None
        late = entry is not None and "ask" in entry.needs            # REQ-WFM-036: the result of a task that asks questions is the newest message, its progress is the status card
        with self._lock:
            self._message_id, self._pipeline, self._sources, self._show_pipeline, self._late, self._task_files = message_id, [], [], False, late, []
        model = self._model_info()[0]
        if entry is not None:
            self.set_activity("thinking")
            if self._prepare_task is not None:
                try:
                    options = self._prepare_task(entry, dict(options or {}), self.ask)
                except Exception as exc:
                    self.note("Could not prepare /%s: %s" % (task, exc))
            self._monitor = TaskMonitor(self._emit, message_id, task, mode="slice" if (options or {}).get("slice") else "run")
            self._monitor.update(phase="starting")
        starter = {"id": message_id, "role": "assistant", "created": created, **({"task": task} if task != "chat" else {})}

        def start():
            self._emit("chat_start", starter)
            self._emit("variant", {"name": None})          # no workflow picks a character variant yet (REQ-CHV-008): the chat's variant stays
        if not late:
            start()
        self.set_activity("thinking")
        state = {"text": "", "emotion": None, "emotions": [], "last": 0.0, "first": True, "shown": ""}
        repairing = self._repair is not None and task == "chat"      # the answers of /lookup carry quotes: they are never changed

        def on_delta(current):
            state["text"] = current
            if late:
                return                                  # the text comes once, at the end
            if state["first"] and current:
                state["first"] = False
                self.set_activity("speaking")
            now = self._clock()
            if now - state["last"] >= DELTA_INTERVAL:
                state["last"] = now
                if not repairing:
                    self._emit("chat_delta", {"id": message_id, "text": current})
                    return
                # the stream is held back to the settled part, which is repaired before the page sees it (REQ-CHA-014); only a text that continues what was shown is released
                shown = self._repair(settled(current))
                if shown and shown != state["shown"] and shown.startswith(state["shown"]):
                    state["shown"] = shown
                    self._emit("chat_delta", {"id": message_id, "text": shown})

        def on_emotion(emotion):
            state["emotions"].append(emotion)
            state["emotion"] = emotion
            if self.mood.set_emotion(emotion):
                self.publish_status()

        status = "done"
        try:
            # the model knows who writes (accounts only); the log keeps the plain text. The argument of a task is data for a tool and stays as it is
            if entry is None:
                final = self._run_exchange("[%s] %s" % (speaker, text) if speaker else text, on_delta, on_emotion, self._stop.is_set)
            else:
                handed = {"ask": self.ask, "options": options or {}, "monitor": self._monitor, "files": self._file_putter(task, message_id), "reports": self._report_saver(entry, message_id, model)}
                final = entry.run(text, on_delta, on_emotion, self._stopped, **{name: handed[name] for name in entry.needs})
            if final is not None:
                state["text"] = final
            if self._stop.is_set():
                status = "stopped"
        except Exception as exc:
            status = "error"
            self.set_activity("offline")
            self._emit("chat_error", {"id": message_id, "message": "MIA could not answer: %s" % exc})
        else:
            self.set_activity(None)
        if repairing and state["text"]:
            state["text"] = self._repair(state["text"])                 # the whole answer, silently; the last delta equals the text of chat_done
            if state["text"] != state["shown"]:
                self._emit("chat_delta", {"id": message_id, "text": state["text"]})
        if late:
            start()
            if state["text"]:
                self._emit("chat_delta", {"id": message_id, "text": state["text"]})
        extra = {"emotions": state["emotions"]} if len(state["emotions"]) > 1 else {}
        if task != "chat":
            extra["task"] = task
        with self._lock:
            steps, sources, self._message_id, self._late = self._pipeline, self._sources, None, False
        if steps:
            extra["pipeline"] = steps
        if sources:
            extra["sources"] = sources
        record = self.log.append("assistant", state["text"], id=message_id, created=created, emotion=state["emotion"],
                                 status=status, model=model, **extra)
        self._emit("chat_done", {"id": message_id, "text": record["text"], "emotion": record["emotion"], "status": status, **({"files": list(self._task_files)} if self._task_files else {})})
        if self._monitor is not None:
            self._monitor.finish()                      # the card keeps the final figures
            self._monitor = None
        self._unpaused.set()
        if self._remember is not None and task == "chat" and status == "done" and user_message_id:
            try:
                self._remember(speaker or "page", user_message_id, text)       # after the answer is out: the page never waits for the memory; a failing memory costs nothing else
            except Exception:
                pass
