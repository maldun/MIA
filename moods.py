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
MIA's mood line (ui/REQUIREMENTS_CHAT.md 4.3, 6.4): a short first person sentence about how she feels or what she does.

The mood is the emotion keyword of MIA's latest message; an activity (thinking, dreaming, offline, ...) overrides it while
it lasts. Phrases come from moods.json (several variants per emotion, random but never the same twice in a row); the file is
read again when it changes. A mood stays for "hold" minutes, then the line returns to "ready".
"""
import json
import os
import random
import threading
import time

DEFAULT_HOLD_MINUTES = 10
DEFAULT_SCORE_SCALE = 20      # an overall score of +-20 moves the offset all the way
FALLBACK = {"emoji": "😊", "texts": ["Ready when you are."]}


class MoodTracker:
    def __init__(self, path, hold_minutes=DEFAULT_HOLD_MINUTES, clock=time.time, rng=None):
        self.path = path
        self.hold = float(hold_minutes) * 60
        self._clock = clock
        self._rng = rng or random.Random()
        self._lock = threading.RLock()
        self._data = {}
        self._mtime = None
        self._emotion = None      # None = ready
        self._since = clock()
        self._activity = None
        self._offset = 0.0        # -1..1, from the overall feedback score (set_score)
        self._phrase = None       # (key, emoji, text) of the current mood, chosen when it changed
        self._last_text = {}
        self._reload()

    # --- phrases -------------------------------------------------------------------------------
    def _reload(self):
        try:
            mtime = os.path.getmtime(self.path)
        except OSError:
            mtime = None
        if mtime == self._mtime and self._data:
            return
        try:
            with open(self.path, encoding="utf-8") as fp:
                data = json.load(fp)
            if not isinstance(data, dict):
                raise ValueError("moods.json must be an object")
        except (OSError, ValueError):
            data = self._data or {}      # a broken edit keeps the phrases that worked
        self._data, self._mtime = data, mtime

    def _entry(self, group, key):
        entries = self._data.get(group, {})
        wanted = str(key).lower()
        for name, entry in entries.items():
            if name.lower() == wanted and isinstance(entry, dict):
                return entry
        return None

    def _pick(self, key, entry):
        texts = [t for t in (entry or {}).get("texts", []) if isinstance(t, str) and t]
        if not texts:
            return ""
        if len(texts) > 1:
            texts = [t for t in texts if t != self._last_text.get(key)] or texts
        text = self._rng.choice(texts)
        self._last_text[key] = text
        return text

    def _ready(self):
        entry = self._data.get("ready") or FALLBACK
        return "ready", entry.get("emoji", FALLBACK["emoji"]), self._pick("ready", entry) or FALLBACK["texts"][0]

    def _mood_phrase(self, emotion):
        if emotion is None:
            return self._ready()
        entry = self._entry("emotions", emotion)
        if entry is None:      # unknown emotions use the neutral phrases
            entry = self._entry("emotions", "neutral") or self._data.get("ready") or FALLBACK
            emotion = "neutral"
        return emotion, entry.get("emoji", FALLBACK["emoji"]), self._pick("emotion:" + emotion, entry) or FALLBACK["texts"][0]

    # --- changes -------------------------------------------------------------------------------
    def set_emotion(self, emotion):
        """the emotion keyword of the latest message; returns True when the line changed"""
        with self._lock:
            self._reload()
            before = self.status()
            new = emotion.lower() if emotion else None
            if new == self._emotion and self._phrase is not None:
                self._since = self._clock()      # the same mood again: the hold time restarts, the line stays
                return False
            self._emotion = new
            self._since = self._clock()
            self._phrase = self._mood_phrase(self._emotion)
            return self.status() != before

    def set_activity(self, activity):
        """None ends the activity; returns True when the line changed"""
        with self._lock:
            self._reload()
            before = self.status()
            self._activity = activity or None
            return self.status() != before

    def enter(self, situation):
        """holds the mood that the mood map assigns to a situation (REQ-CHA-009): the section "situations" of moods.json maps idle, thinking, speaking, waiting, greeting,
        error and offline to {"activity": name} or {"emotion": name} (null = the ready line); an unknown situation changes nothing; returns True when the line changed"""
        with self._lock:
            self._reload()
            entry = self._data.get("situations", {}).get(situation)
            if not isinstance(entry, dict):
                return False
            before = self.status()
            if "activity" in entry:
                self._activity = entry["activity"] or None
            else:
                self._activity = None
                self.set_emotion(entry.get("emotion"))
            return self.status() != before

    def set_score(self, overall):
        """the overall feedback score shifts the general mood (REQ-CHA-010): the offset is the score over the scale of moods.json ("score_scale", default 20),
        kept between -1 and 1; a plus moves it up, a minus down"""
        with self._lock:
            self._reload()
            scale = self._data.get("score_scale", DEFAULT_SCORE_SCALE)
            scale = scale if isinstance(scale, (int, float)) and not isinstance(scale, bool) and scale > 0 else DEFAULT_SCORE_SCALE
            self._offset = max(-1.0, min(1.0, float(overall) / scale))

    # --- state ---------------------------------------------------------------------------------
    def _expire(self):
        if self._emotion is not None and self.hold > 0 and self._clock() - self._since > self.hold:
            self._emotion = None
            self._since = self._clock()
            self._phrase = None

    def status(self):
        """{"emotion", "emoji", "text", "since", "activity"}: what the mood line shows"""
        with self._lock:
            self._expire()
            if self._phrase is None:
                self._phrase = self._mood_phrase(self._emotion)
            key, emoji, text = self._phrase
            activity = self._activity
            if activity:
                entry = self._entry("activities", activity)
                activity_text = self._activity_text(activity, entry)
                if activity_text:      # "speaking" has no text of its own: the mood stays (the page adds a sound icon)
                    emoji, text = (entry or {}).get("emoji", emoji), activity_text
            return {"emotion": None if key == "ready" else key, "emoji": emoji, "text": text,
                    "since": self._since, "activity": activity, "offset": round(self._offset, 3)}

    def _activity_text(self, activity, entry):
        texts = [t for t in (entry or {}).get("texts", []) if isinstance(t, str) and t]
        if not texts:
            return ""
        cached = self._last_text.get("activity:" + activity)
        return cached if cached in texts else self._pick("activity:" + activity, entry)
