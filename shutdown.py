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
Orderly shutdown of MIA.

Before, Ctrl+C reached MIA and all its helper processes (speech, https proxy) in the very same instant, and the
commands /break! and /goodnight! killed the whole process group with SIGTERM. Now the helper processes run in their own
session (Ctrl+C reaches only MIA), and MIA stops them one after the other with a short pause in between:
Ctrl+C, /break!, /goodnight! and SIGTERM all end up in the same orderly path.
"""
import os
import signal
import subprocess
import time

try:
    from .mia_logger import logger
except ImportError:  # used as plain script / in tests
    from mia_logger import logger

STOP_TIMEOUT = 10.0     # seconds a helper process gets to end after SIGTERM, then it is killed
DEFAULT_PAUSE = 1.0     # seconds between two shutdown steps

def request_shutdown():
    """
    Asks MIA to shut down in an orderly way. Same as Ctrl+C: the main thread gets a KeyboardInterrupt.
    Only this process is signalled, not a whole process group. Can be called from any thread.
    """
    os.kill(os.getpid(), signal.SIGINT)

def install_term_handler():
    """
    SIGTERM (kill, systemd, ...) takes the same orderly path as Ctrl+C. Call it in the main thread.
    """
    def handler(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, handler)

def stop_process(proc, name="process", timeout=STOP_TIMEOUT, group=False):
    """
    Asks a helper process to end (SIGTERM), waits for it and kills it only after the timeout.
    group=True: also its helpers; only for processes started with start_new_session=True,
    which are the leader of their own process group (nothing else is in that group).
    Returns True if the process ended on its own (or was not running), False if it had to be killed.
    """
    if proc is None or proc.poll() is not None:
        return True
    sig_target = (lambda sig: os.killpg(proc.pid, sig)) if group else proc.send_signal
    try:
        sig_target(signal.SIGTERM)
    except ProcessLookupError:
        return True
    try:
        proc.wait(timeout=timeout)
        logger.info(f"{name} stopped")
        return True
    except subprocess.TimeoutExpired:
        logger.warning(f"{name} did not stop within {timeout} s, killing it")
        try:
            sig_target(signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
        return False

def graceful_shutdown(steps, pause=DEFAULT_PAUSE):
    """
    Runs the shutdown steps one after the other, with a pause in between.
    steps: list of (name, function). A failing step is logged and does not stop the others.
    Ctrl+C and SIGTERM are ignored meanwhile (all steps have a time limit), so that a second
    press cannot interrupt the shutdown halfway.
    """
    old_int = signal.signal(signal.SIGINT, signal.SIG_IGN)
    old_term = signal.signal(signal.SIGTERM, signal.SIG_IGN)
    try:
        for i, (name, step) in enumerate(steps):
            if i > 0 and pause > 0:
                time.sleep(pause)
            logger.info(f"shutdown: {name}")
            try:
                step()
            except Exception as exc:
                logger.error(f"shutdown step '{name}' failed: {exc}")
    finally:
        signal.signal(signal.SIGINT, old_int)
        signal.signal(signal.SIGTERM, old_term)
