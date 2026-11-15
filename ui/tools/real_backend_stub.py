"""
The real backend of MIA with a fake model, for the browser check of a restart (G-V3.PANEL, TC-CLV-038; note specs/mia/goals/G-V3.PANEL/skill-events-today.md, D-337): web_app with accounts ON,
its file storage in the folder MIA_STUB_DATA (a folder that a test mounts read-write into the container, so that the data survives a stop and a new start), a model that answers at once and no
sound. Seed the account and the data in that folder BEFORE the start with the code of the repository (accounts.create, Storage(FileBackend(folder)).put).
Run in a container of the MIA image like chat_mock_server.py:  python MIA/ui/tools/real_backend_stub.py   (port MIA_MOCK_PORT, default 8686; MIA_STUB_HOST for the address)
"""
import json
import os
import sys
import tempfile

repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importlib.util  # noqa: E402
if importlib.util.find_spec("MIA") is None:      # outside the image: a link named MIA to this checkout
    link_dir = tempfile.mkdtemp()
    os.symlink(repo, os.path.join(link_dir, "MIA"))
    sys.path.insert(0, link_dir)

from MIA import config as _config  # noqa: E402

DATA = os.environ.get("MIA_STUB_DATA") or tempfile.mkdtemp()
_cfg_dir = tempfile.mkdtemp()
with open(os.path.join(repo, _config.EXAMPLE), encoding="utf-8") as _handle:
    _cfg = json.load(_handle)
_cfg["accounts_enabled"] = True                  # the real login guard
_cfg["accounts_dir"] = DATA                      # an absolute path: web_app joins it to its own folder and keeps it
with open(os.path.join(_cfg_dir, _config.NAME), "w", encoding="utf-8") as _handle:
    json.dump(_cfg, _handle)
_config.ensure = lambda folder: (os.path.join(_cfg_dir, _config.NAME), False)

from MIA import web_app as w  # noqa: E402

w.play_intro_sound = lambda: None
for _origin in ("http://127.0.0.1:8686", "http://localhost:8686"):      # the browser container reaches the stub by this address; the guard refuses every other Origin (REQ-API-009)
    if _origin not in w.allowed_origins:
        w.allowed_origins.append(_origin)
w.socketio.server.eio.cors_allowed_origins = "*"


def fake(text, on_delta, on_emotion, should_stop):
    on_emotion("neutral")
    on_delta("Hello.")
    return "Hello."


w.chat_service._run_exchange = fake

if __name__ == "__main__":
    w.socketio.run(w.app, host=os.environ.get("MIA_STUB_HOST", "127.0.0.1"), port=int(os.environ.get("MIA_MOCK_PORT", "8686")), allow_unsafe_werkzeug=True)
