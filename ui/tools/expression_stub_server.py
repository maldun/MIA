"""
MIA's web app with a fake language model for expressions (no Ollama needed), on port 8685, for the live test of the expression generator:
  python ui/tools/expression_stub_server.py
  MIA_URL=http://127.0.0.1:8685 MIA_TOKEN_FILE=data/editor_token.txt MIA_EXPRESSION_LIVE=1 \\
    godot --headless --path ui/godot --script res://tools/test_editor_live.gd
"""
import json
import os
import sys
import tempfile

repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
link_dir = tempfile.mkdtemp()
os.symlink(repo, os.path.join(link_dir, "MIA"))
sys.path.insert(0, link_dir)

from MIA import web_app as w  # noqa: E402

w.app.config["EXPRESSION_GENERATOR"]._chat = lambda messages, schema: json.dumps({
    "description": "a sly grin", "weights": {"Fcl_MTH_Fun": 0.6, "Fcl_EYE_Joy": 0.4}, "bones": {"head_roll": 4}, "tags": ["smug", "sly"], "gesture": ""})
w.app.config["EXPRESSION_GENERATOR"].log_path = os.path.join(tempfile.mkdtemp(), "feedback.jsonl")
w.socketio.server.eio.cors_allowed_origins = "*"
w.scheduler.shutdown(wait=False)
w.socketio.run(w.app, host="127.0.0.1", port=8685, allow_unsafe_werkzeug=True)
