#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIA - MIA Is not an Assistant
#Copyright (C) 2024  Stefan Reiterer

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
Client for the sound server, which sends the sentences of an answer
while the answer is still being generated.
"""
import json
import socket

try:
    from .constants import SPEECH_REQ, SOUND_REQ, TIME_REQ, STREAM_REQ, STREAM_END_REQ, U8, MESSAGE_SIZE
    from .mia_logger import logger
    from .utils import split_into_lines_and_sentences, filter_symbol_sentences, get_timestamp
    from .speech_text import speech_text
except ImportError:
    from constants import SPEECH_REQ, SOUND_REQ, TIME_REQ, STREAM_REQ, STREAM_END_REQ, U8, MESSAGE_SIZE
    from mia_logger import logger
    from utils import split_into_lines_and_sentences, filter_symbol_sentences, get_timestamp
    from speech_text import speech_text


class SpeechStreamer:
    """
    Sends the sentences of a growing answer to the sound server, so that
    MIA starts to speak before the LLM has finished.
    Usage: call update(text) with the (emotion filtered) text so far, whenever it
    grows; then finish(text) with the complete text and wait() until it is spoken.
    """
    def __init__(self,host,port,repair=None,settle=None):
        # repair/settle: the voice speaks what the page shows (REQ-CHA-014): a growing text is cut to its settled part first, then repaired
        self._repair = repair
        self._settle = settle or (lambda text: text)
        self._host = host
        self._port = port
        self._sock = None
        self._failed = False
        self._timestamp = None
        self._sent = 0 # number of sentences sent so far

    @staticmethod
    def split(text, final=True):
        """sentences of the text for the voice: without markdown marks and without *actions* (see speech_text.py)"""
        return filter_symbol_sentences(split_into_lines_and_sentences(speech_text(text, final)))

    def _send_line(self,dic):
        self._sock.sendall(bytes(json.dumps(dic) + '\n',U8))

    def _send(self,sentences):
        if self._failed or len(sentences) == 0:
            return
        try:
            if self._sock is None:
                self._sock = socket.create_connection((self._host,self._port))
                self._timestamp = get_timestamp()
            for sentence in sentences:
                self._send_line({SPEECH_REQ:sentence,TIME_REQ:self._timestamp,STREAM_REQ:True})
                self._sent += 1
        except OSError as exc:
            logger.error(f"Sound server not reachable: {exc}")
            self._failed = True
            self.abort()

    def update(self,text):
        """
        Sends all sentences which are complete. The last sentence is kept
        back, since it may still grow (or be part of an emotion keyword).
        """
        if self._repair:
            text = self._repair(self._settle(text))
        self._send(self.split(text, final=False)[self._sent:-1])

    def finish(self,text):
        """
        Sends the rest of the final text and the end marker. Does not wait.
        """
        if self._repair:
            text = self._repair(text)
        self._send(self.split(text)[self._sent:])
        if self._sock is not None and not self._failed:
            try:
                self._send_line({STREAM_END_REQ:True,TIME_REQ:self._timestamp})
            except OSError as exc:
                logger.error(f"Sound server not reachable: {exc}")
                self._failed = True
                self.abort()

    def wait(self):
        """
        Waits until everything is spoken.
        """
        if self._sock is None:
            return
        try:
            received = json.loads(str(self._sock.recv(MESSAGE_SIZE),U8))
            if SOUND_REQ in received and received.get(TIME_REQ) == self._timestamp:
                logger.info("Speech played!")
            else:
                logger.info("Something went wrong on Sound Server Side!")
        except (OSError, ValueError) as exc:
            logger.error(f"No reply from sound server: {exc}")
        finally:
            self.abort()

    def abort(self):
        """
        Closes the connection (the sound server stops speaking after the rendered sentences).
        """
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
