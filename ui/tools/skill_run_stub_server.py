"""
Stub server for the browser checks of the Skill run view (G-V3.PANEL, TC-CLV-030 to 047; interface note specs/mia/goals/G-V3.PANEL/skill-run-view-interface-note.md):
the page on the IF-101 mock of tests/helpers/mocks (as chat_mock_server.py) plus the routes of IF-101 v16 and one control route, so that a check puts the page into a
state without a skill that knows the view (TR-PANEL-002): the scripted skill is a list of steps, it sends only the events of IF-101 and the v16 fields.
  GET  /api/skill-runs/shown      the run record that the script named as shown, 204 when none
  GET  /api/skill-runs/<id>       the run record that the script gave for this id, 404 when none
  POST /stub/script               {"steps": [...]} with the steps
       {"emit": "<event>", "payload": {...}}   an event to every connected page (task_status, skill_run_changed, chat_message, files_changed)
       {"shown": <run record or null>}         what GET /api/skill-runs/shown answers from now on
       {"run": <run record>}                   what GET /api/skill-runs/<record id> answers from now on
       {"history_deleted": true}               no run is shown, no run is known, skill_run_changed with id null goes out
       {"sleep": seconds}                      at most 3 s
Run in the container of the MIA image like chat_mock_server.py: python MIA/ui/tools/skill_run_stub_server.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chat_mock_server as mock  # noqa: E402
from flask import jsonify, request  # noqa: E402

state = {"shown": None, "runs": {}}
app = mock.w.app


def signed_in():
    return request.cookies.get(mock.COOKIE) in mock.api._sessions


@app.route("/api/skill-runs/shown")
def shown_run():
    if not signed_in():
        return jsonify({"error": "unauthenticated"}), 401
    return ("", 204) if state["shown"] is None else jsonify(state["shown"])


@app.route("/api/skill-runs/<run_id>")
def skill_run(run_id):
    if not signed_in():
        return jsonify({"error": "unauthenticated"}), 401
    return (jsonify(state["runs"][run_id]) if run_id in state["runs"] else (jsonify({"error": "not_found"}), 404))


@app.route("/stub/script", methods=["POST"])
def script():
    for step in (request.get_json(silent=True) or {}).get("steps", []):
        if "emit" in step:
            mock.w.socketio.emit(step["emit"], step.get("payload", {}))
        elif "shown" in step:
            state["shown"] = step["shown"]
        elif "run" in step:
            state["runs"][step["run"]["id"]] = step["run"]
        elif step.get("history_deleted"):
            state["shown"], state["runs"] = None, {}
            mock.w.socketio.emit("skill_run_changed", {"id": None})
        elif "sleep" in step:
            time.sleep(min(float(step["sleep"]), 3))
    return jsonify({"ok": True})


if __name__ == "__main__":
    mock.w.socketio.run(app, host=os.environ.get("MIA_STUB_HOST", "127.0.0.1"), port=int(os.environ.get("MIA_MOCK_PORT", "8686")), allow_unsafe_werkzeug=True)
