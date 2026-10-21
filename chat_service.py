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
import re
import threading
import time

try:
    from .chat_log import utc_now
except ImportError:  # used as plain script / in tests
    from chat_log import utc_now

MAX_LENGTH = 8000
TASK_COMMAND = re.compile(r"/(lookup|research|search)(?:\s+(.*))?", re.I | re.S)        # /lookup question, /search query; /research is the old name of /lookup
DELTA_INTERVAL = 0.05          # at most about 20 deltas per second per message
CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

COMMANDS = (
    {"command": "/light!", "description": "Switch to the small model (saves GPU memory)", "confirm": False},
    {"command": "/full!", "description": "Switch back to the large model", "confirm": False},
    {"command": "/dream!", "description": "Sort and summarize MIA's memory", "confirm": False},
    {"command": "/time!", "description": "Send the current time to MIA", "confirm": False},
    {"command": "/lookup ", "description": "Look something up on the web and answer with sources: /lookup your question", "confirm": False},
    {"command": "/search ", "description": "Show the top web results for a query, no answer: /search your query", "confirm": False},
    {"command": "/goodnight!", "description": "Dream, then shut MIA down", "confirm": True},
    {"command": "/break!", "description": "Shut MIA down", "confirm": True},
)


def normalize_text(text):
    """strips control characters and surrounding blanks; returns "" for anything that is not text"""
    if not isinstance(text, str):
        return ""
    return CONTROL_CHARACTERS.sub("", text).strip()


class ChatService:
    def __init__(self, emit, log, mood, run_exchange, run_command=None, model_info=None, queue_size=1,
                 rate_limit=(10, 60), spawn=None, clock=time.monotonic, run_lookup=None, run_search=None):
        self._emit = emit
        self._run_lookup = run_lookup          # (question, on_delta, on_emotion, should_stop) -> the answer, for /lookup
        self._run_search = run_search              # (query, on_delta, on_emotion, should_stop) -> the list of results, for /search
        self.log = log
        self.mood = mood
        self._run_exchange = run_exchange
        self._run_command = run_command
        self._model_info = model_info or (lambda: (None, None))
        self.queue_size = max(0, int(queue_size))
        self._rate_count, self._rate_window = rate_limit
        self._spawn = spawn or (lambda target: threading.Thread(target=target, daemon=True).start())
        self._clock = clock
        self._lock = threading.RLock()
        self._queue = collections.deque()
        self._running = False
        self._current = None
        self._stop = threading.Event()
        self._hits = collections.defaultdict(collections.deque)
        self._commands = {c["command"] for c in COMMANDS}
        self._message_id = None          # the answer in progress: pipeline events belong to it
        self._pipeline = []
        self._show_pipeline = False

    # --- state -----------------------------------------------------------------------------------
    def is_command(self, text):
        return text.strip().lower() in self._commands

    @staticmethod
    def task_command(text):
        """("lookup" | "search", the argument) for "/lookup question" and "/search query" (argument "" for the bare command), None for any other text.
        "/research" is the old name of "/lookup" and gives the same task; the name is kept for the literature review that is being built (ui/REQUIREMENTS_RESEARCH.md)"""
        match = TASK_COMMAND.fullmatch(text.strip())
        if match is None:
            return None
        name = match.group(1).lower()
        return ("lookup" if name == "research" else name, (match.group(2) or "").strip())

    @classmethod
    def lookup_question(cls, text):
        """the question of "/lookup question" ("" for a bare /lookup), None when the text is no lookup command"""
        found = cls.task_command(text)
        return found[1] if found and found[0] == "lookup" else None

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

    def send(self, text, client_id=None, sender="page"):
        """accepts a message; returns the acknowledgement for the page: {"ok", "message" | "error", "queued"}"""
        text = normalize_text(text)
        if not text:
            return {"ok": False, "error": "The message is empty."}
        if len(text) > MAX_LENGTH:
            return {"ok": False, "error": "The message is too long (at most %d characters)." % MAX_LENGTH}
        if self._rate_limited(sender):
            return {"ok": False, "error": "Too many messages, please wait a moment."}
        with self._lock:
            if self._running and len(self._queue) >= self.queue_size:
                return {"ok": False, "error": "MIA is busy, please wait until she has answered."}
            command = self.is_command(text)
            task, argument = self.task_command(text) or (None, None)
            if task is not None and not argument:
                example = "/lookup how tall is the Eiffel Tower" if task == "lookup" else "/search Eiffel Tower height"
                return {"ok": False, "error": "Write %s after /%s, for example: %s" % ("your question" if task == "lookup" else "what to search for", task, example)}
            if task is not None and (self._run_lookup if task == "lookup" else self._run_search) is None:
                return {"ok": False, "error": "%s is not available." % task.capitalize()}
            record = None
            if not command:
                record = self.log.append("user", text, client_id=client_id) if client_id else self.log.append("user", text)
                self._emit("chat_message", record)
            queued = self._running
            self._queue.append(("command" if command else task if task is not None else "chat", argument if task is not None else text))
            self._start_worker()
        self.publish_status()
        if text.strip().lower().startswith("/research"):
            self.note("/research is now called /lookup: the quick look-up with sources. The name /research is kept for the literature review that is being built.")
        return {"ok": True, "message": record, "queued": queued, "command": command}

    def stop(self):
        """stops the running answer (the text received so far stays)"""
        with self._lock:
            running = self._running and self._current == "chat"
        if running:
            self._stop.set()
        return running

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
                kind, text = self._queue.popleft()
                self._current = kind
                self._stop.clear()
            try:
                self._do_command(text) if kind == "command" else self._do_chat(text, kind)
            except Exception as exc:       # the worker must survive anything
                self._emit("chat_error", {"message": "Something went wrong: %s" % exc})
        self.publish_status()

    def _do_command(self, text):
        command = text.strip().lower()
        if command in ("/dream!", "/goodnight!"):
            self.set_activity("dreaming")
        try:
            result = self._run_command(command) if self._run_command else None
        finally:
            self.set_activity(None)
        self.note(result or "Command %s done." % command, command=command)

    def _do_chat(self, text, task="chat"):
        message_id = self.log.new_id()
        created = utc_now()
        with self._lock:
            self._message_id, self._pipeline, self._show_pipeline = message_id, [], False
        model = self._model_info()[0]
        self._emit("chat_start", {"id": message_id, "role": "assistant", "created": created, **({"task": task} if task != "chat" else {})})
        self.set_activity("thinking")
        state = {"text": "", "emotion": None, "emotions": [], "last": 0.0, "first": True}

        def on_delta(current):
            state["text"] = current
            if state["first"] and current:
                state["first"] = False
                self.set_activity("speaking")
            now = self._clock()
            if now - state["last"] >= DELTA_INTERVAL:
                state["last"] = now
                self._emit("chat_delta", {"id": message_id, "text": current})

        def on_emotion(emotion):
            state["emotions"].append(emotion)
            state["emotion"] = emotion
            if self.mood.set_emotion(emotion):
                self.publish_status()

        status = "done"
        try:
            run = {"chat": self._run_exchange, "lookup": self._run_lookup, "search": self._run_search}[task]
            final = run(text, on_delta, on_emotion, self._stop.is_set)
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
        extra = {"emotions": state["emotions"]} if len(state["emotions"]) > 1 else {}
        if task != "chat":
            extra["task"] = task
        with self._lock:
            steps, self._message_id = self._pipeline, None
        if steps:
            extra["pipeline"] = steps
        record = self.log.append("assistant", state["text"], id=message_id, created=created, emotion=state["emotion"],
                                 status=status, model=model, **extra)
        self._emit("chat_done", {"id": message_id, "text": record["text"], "emotion": record["emotion"], "status": status})
