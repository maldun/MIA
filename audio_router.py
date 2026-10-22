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
Who plays MIA's voice. Every open page (tabs, phone, computer) is a socket client; if all of them played every line, the voice would be
heard twice or three times at slightly different moments (an echo), and every page would delete the file the others are about to play.

Exactly one page plays: the one the user is using. A page claims the voice when it is visible and when the user touches it (audio_claim);
the server tells the others (audio_owner) and sends each new line (audio_reload: url and serial number) only to the owner. Without a claim
the page that connected last gets it, so the voice is never lost.
"""
import threading


class AudioRouter:
    def __init__(self, emit):
        """emit(event, payload, to=None): to a single client, or to all when `to` is None"""
        self._emit = emit
        self._lock = threading.RLock()
        self._connected = []        # session ids in the order they connected
        self.owner = None
        self.serial = 0

    def connect(self, sid):
        with self._lock:
            if sid not in self._connected:
                self._connected.append(sid)

    def disconnect(self, sid):
        with self._lock:
            if sid in self._connected:
                self._connected.remove(sid)
            was_owner = self.owner == sid
            if was_owner:
                self.owner = None
        if was_owner:
            self._emit("audio_owner", {"sid": self.target()})

    def claim(self, sid):
        """the page of sid plays the voice from now on; everybody is told"""
        with self._lock:
            if sid not in self._connected:
                return False
            changed = self.owner != sid
            self.owner = sid
        if changed:
            self._emit("audio_owner", {"sid": sid})
        return True

    def target(self):
        """the session that plays the voice: the owner, else the page that connected last, else nobody"""
        with self._lock:
            if self.owner in self._connected:
                return self.owner
            return self._connected[-1] if self._connected else None

    def next_serial(self, after=0):
        """the next serial number, above `after` too (the highest line already on disk: after a restart the count would start at 1 again)"""
        with self._lock:
            self.serial = max(self.serial, after) + 1
            return self.serial

    def announce(self, url, serial, message=""):
        """tells the playing page that a new line is ready; returns the session that got it (None: nobody is connected)"""
        sid = self.target()
        if sid is not None:
            self._emit("audio_reload", {"url": url, "serial": serial, "message": message}, to=sid)
        return sid
