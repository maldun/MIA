"""
Stub server for the end-to-end check of the chat page (no Ollama needed): MIA's web app on port 8685 with a fake model
that streams slowly (say "slow" in the message), fails on "error", and a seeded history of 130 messages over 3 days.
Run with the MIA virtualenv, then:
  python ui/tools/browser_check.py "http://127.0.0.1:8685/?character=0" shot.png --eval "$(cat ui/tools/chat_e2e.js)"
"""
import os
import sys
import tempfile
import time

repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
link_dir = tempfile.mkdtemp()
os.symlink(repo, os.path.join(link_dir, "MIA"))
sys.path.insert(0, link_dir)

from MIA import web_app as w  # noqa: E402

w.play_intro_sound = lambda: None
w.socketio.server.eio.cors_allowed_origins = "*"

log = w.chat_log
log.path = os.path.join(tempfile.mkdtemp(), "log.jsonl")
log.clear()
# 130 messages over 3 days, ids sortable
now = time.time()
for i in range(130):
    day = 2 - i // 50
    created = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - day * 86400 - (130 - i) * 60))
    if i % 2 == 0:
        log.append("user", "Question %d with a link https://example.org/%d" % (i, i), created=created)
    else:
        log.append("assistant", "Answer %d: **bold** and a list\n\n- one\n- two" % i, created=created, emotion="happy" if i % 4 == 1 else "smug")

ANSWER = ["Sure! ", "Here is **a streamed answer**. ", "It has `code`, ", "a list:\n\n- first\n", "- second\n", "- third\n\n", "And a [link](https://example.org). ", "Done."]


def fake(text, on_delta, on_emotion, should_stop):
    if "error" in text:
        raise ConnectionError("model offline")
    on_emotion("surprised")
    shown = ""
    for part in ANSWER:
        for _ in range(3):
            if should_stop():
                return shown
            time.sleep(0.4 if "slow" in text else 0.1)
        shown += part
        on_delta(shown)
    return shown


w.chat_service._run_exchange = fake
w.chat_service._rate_count = 0
# MIA_STUB_HOST=0.0.0.0 only inside a container whose port is published to 127.0.0.1 of the host (tools/start_testing.sh)
w.socketio.run(w.app, host=os.environ.get("MIA_STUB_HOST", "127.0.0.1"), port=8685, allow_unsafe_werkzeug=True)
