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
The chat log (ui/REQUIREMENTS_CHAT.md 6.2): every visible message of the conversation, one JSON object per line.
Independent of MIA's memory (memories.json): dreaming and summaries do not touch it. Calibration, time prompts,
summaries and penalties are never written here.

Ids are sortable (time based), so "before=<id>" pages through the history. The file is appended per message;
when it holds more than "max_messages" records the oldest are dropped (the file is rewritten atomically).
"""
import json
import os
import threading
import time

ROLES = ("user", "assistant", "system")
STATUSES = ("done", "stopped", "error")
DEFAULT_MAX_MESSAGES = 10000
MAX_PAGE = 200


def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class ChatLog:
    def __init__(self, path, max_messages=DEFAULT_MAX_MESSAGES):
        self.path = path
        self.max_messages = max(10, int(max_messages))
        self._lock = threading.RLock()
        self._last = ""
        self._count = None
        folder = os.path.dirname(os.path.abspath(path))
        os.makedirs(folder, exist_ok=True)
        records = self._read()
        self._count = len(records)
        if records:
            self._last = records[-1]["id"]

    # --- ids -----------------------------------------------------------------------------------
    def new_id(self):
        """time based and strictly increasing, so ids sort like the messages"""
        with self._lock:
            stamp = "%017d" % int(time.time() * 1_000_000)
            if stamp <= self._last:
                stamp = "%017d" % (int(self._last[:17]) + 1)
            self._last = stamp
            return stamp + "-" + os.urandom(2).hex()

    # --- reading -------------------------------------------------------------------------------
    def _read(self):
        records = []
        try:
            with open(self.path, encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except ValueError:
                        continue  # a half written line never breaks the history
                    if isinstance(record, dict) and "id" in record:
                        records.append(record)
        except FileNotFoundError:
            pass
        return records

    def history(self, before=None, limit=50):
        """the last `limit` messages (older than `before`), newest last; plus whether older ones exist"""
        limit = max(1, min(int(limit), MAX_PAGE))
        with self._lock:
            records = self._read()
        if before:
            records = [r for r in records if r["id"] < before]
        older = len(records) > limit
        return records[-limit:], older

    def last(self, role=None):
        with self._lock:
            records = self._read()
        for record in reversed(records):
            if role is None or record.get("role") == role:
                return record
        return None

    def __len__(self):
        with self._lock:
            return self._count

    # --- writing -------------------------------------------------------------------------------
    def append(self, role, text, **fields):
        """stores one finished message and returns the record"""
        if role not in ROLES:
            raise ValueError("unknown role %r" % (role,))
        record = {"id": fields.pop("id", None) or self.new_id(), "role": role, "text": str(text),
                  "markdown": bool(fields.pop("markdown", role != "user")), "emotion": fields.pop("emotion", None),
                  "auto": bool(fields.pop("auto", False)), "created": fields.pop("created", None) or utc_now(),
                  "status": fields.pop("status", "done")}
        if record["status"] not in STATUSES:
            raise ValueError("unknown status %r" % (record["status"],))
        record.update(fields)
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as fp:
                fp.write(line)
            self._count += 1
            if self._count > self.max_messages:
                self._trim()
        return record

    def _trim(self):
        records = self._read()[-self.max_messages:]
        self._write(records)

    def _write(self, records):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fp:
            for record in records:
                fp.write(json.dumps(record, ensure_ascii=False) + "\n")
        os.replace(tmp, self.path)
        self._count = len(records)

    def clear(self):
        """deletes the content of the log (the file stays, empty)"""
        with self._lock:
            self._write([])
