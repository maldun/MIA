"""
The chat page on the MOCK of the Backend interface IF-101 (contracts/IF-101-chat-api.md): a login with accounts, messages with their sender,
positions in the queue, scripted answers. For trying the page by hand and for the browser tests of N-1; no Ollama, no voice, no database.

  python ui/tools/chat_mock_server.py          then open http://127.0.0.1:8686/?character=0
  accounts: anna / pw-anna, ben / pw-ben, carl / pw-carl   (a sixth wrong login within a minute is throttled)
  a message waits ANSWER_DELAY seconds, so the queue positions can be seen: send two or three quickly, from two browsers if you like.

It is the real page (templates/, served by web_app.py) with the chat handlers replaced by the mock of the protected helper
tests/helpers/mocks/if_101_chat_api.py. The session is a cookie (HttpOnly, same site); the page keeps no token.
"""
import os
import sys
import tempfile
import threading
import time

repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
link_dir = tempfile.mkdtemp()
os.symlink(repo, os.path.join(link_dir, "MIA"))
sys.path.insert(0, link_dir)
# the protected mock of IF-101 (v2 since amendment A-04); until A-04 is installed the draft next to it is used
for candidate in (os.path.join(repo, "tests", "helpers", "mocks"), os.path.join(repo, "specs", "mia", "contract-drafts", "tests", "helpers", "mocks")):
    with open(os.path.join(candidate, "if_101_chat_api.py"), encoding="utf-8") as handle:
        if "def logout" in handle.read():
            break
sys.path.insert(0, candidate)

from flask import jsonify, request  # noqa: E402
from flask_socketio import emit  # noqa: E402

from socketio.exceptions import ConnectionRefusedError  # noqa: E402,A004  (the one the Socket.IO server turns into connect_error)

from errors import ApiError  # noqa: E402
from if_101_chat_api import ChatApiMock  # noqa: E402
# The mock server must not depend on the private configuration of the machine (setup_cfg.json: accounts, tokens, ports, models): with `accounts_enabled` the real login guard would answer
# instead of the mock. web_app reads its configuration through config.ensure(), so the tracked example (every option at its default, accounts off) is handed to it from a temporary folder.
import json  # noqa: E402
from MIA import config as _config  # noqa: E402

_example = os.path.join(repo, _config.EXAMPLE)
_cfg_dir = tempfile.mkdtemp()
with open(_example, encoding="utf-8") as _handle:
    _cfg = json.load(_handle)
_cfg["accounts_enabled"] = False
with open(os.path.join(_cfg_dir, _config.NAME), "w", encoding="utf-8") as _handle:
    json.dump(_cfg, _handle)
_config.ensure = lambda folder: (os.path.join(_cfg_dir, _config.NAME), False)

from MIA import web_app as w  # noqa: E402

ACCOUNTS = {"anna": "pw-anna", "ben": "pw-ben", "carl": "pw-carl"}
ANSWER_DELAY = float(os.environ.get("ANSWER_DELAY", "4"))      # seconds a message waits before it is answered
EVENT_GAP = float(os.environ.get("EVENT_GAP", "0.25"))          # seconds between the events of one answer (streaming)
COOKIE = "mia_session"
ANSWERS = [
    {"sentences": ["Hello {user}.", "How are you today?"], "emotion": "happy"},
    {"sentences": ["That is interesting.", "Tell me more."], "emotion": "neutral"},
    {"sentences": ["I am a mock of the Backend, so I only read from a script."], "emotion": "thinking"},
    {"sentences": ["Hmm.", "I am not sure about that one."], "emotion": "sad"},
]

w.play_intro_sound = lambda: None
w.socketio.server.eio.cors_allowed_origins = "*"

api = ChatApiMock(accounts=dict(ACCOUNTS), answers=[])
lock = threading.RLock()
sids = {}              # session token -> set of socket ids
tokens = {}            # socket id -> session token
turn = {"n": 0}
answering = threading.Event()


def session():
    token = request.cookies.get(COOKIE)
    try:
        api.history(token, limit=1)
    except ApiError:
        return None
    return token


@w.app.before_request
def guard():
    """IF-101: a request without a session is 401 unauthenticated (the login and the static files stay open)."""
    open_paths = ("/api/login", "/api/chat/commands")
    if request.path.startswith("/api/") and request.path not in open_paths:
        if session() is None:
            return jsonify({"error": "unauthenticated"}), 401
        if request.path == "/api/chat/history":
            with lock:
                messages = api.history(session(), limit=int(request.args.get("limit", 50)))
            return jsonify({"messages": messages, "older": False})
    return None


@w.app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    try:
        with lock:
            token = api.login(str(data.get("user", "")), str(data.get("password", "")))
    except ApiError as err:
        return jsonify({"error": err.code}), err.status
    response = jsonify({"ok": True})
    response.set_cookie(COOKIE, token, httponly=True, samesite="Strict", secure=request.is_secure)
    return response


def deliver():
    """Every connected session gets the events the mock has for it, one by one, so that the answer streams."""
    with lock:
        batches = {token: api.events(token) for token in list(sids)}
    pending = [(token, event) for token, events in batches.items() for event in events]
    for token, event in pending:
        for sid in list(sids.get(token, ())):
            w.socketio.emit(event["event"], event["payload"], to=sid)
        if event["event"] in ("chat_delta", "audio_chunk"):
            time.sleep(EVENT_GAP)


def answer_later():
    time.sleep(ANSWER_DELAY)
    with lock:
        while api._queue:                                  # the mock answers the whole queue; one scripted answer per message
            owner = api._owner.get(api._queue[0], "you")
            script = dict(ANSWERS[turn["n"] % len(ANSWERS)])
            script["sentences"] = [s.format(user=owner) for s in script["sentences"]]
            api.answers.append(script)
            api.run_with_variant("summer" if turn["n"] % 3 == 2 else None)         # every third answer comes from a workflow with a character variant
            turn["n"] += 1
            api._answer(api._queue.popleft())
            api._broadcast("chat_status", api._status())
    deliver()
    answering.clear()


def run_api(operation):
    """One call of the mock for the session of the request: its answer as JSON, an ApiError as {error, rule} with the status; the events it caused go out."""
    try:
        with lock:
            result = operation(session())
        status = 200
    except ApiError as err:
        result, status = {"error": err.code, "rule": err.rule}, err.status
    deliver()
    if status == 200 and answering.is_set() is False and api._queue:
        answering.set()
        w.socketio.start_background_task(answer_later)           # a regenerated answer waits like a message
    return jsonify(result), status


def body():
    return request.get_json(silent=True) or {}


@w.app.get("/api/whoami")
def r_whoami():
    return run_api(lambda s: api.whoami(s))


@w.app.post("/api/logout")
def r_logout():
    """IF-101 v2: the session ends, its sockets are closed and the cookie is cleared."""
    token = session()
    response, status = run_api(lambda s: api.logout(s))
    if status == 200:
        for sid in sids.pop(token, set()):
            tokens.pop(sid, None)
            w.socketio.server.disconnect(sid)
        response.set_cookie(COOKIE, "", max_age=0, httponly=True, samesite="Strict", secure=request.is_secure)
    return response, status


@w.app.post("/api/change_password")
def r_change_password():
    return run_api(lambda s: api.change_password(s, body().get("old"), body().get("new")))


@w.app.post("/api/regenerate")
def r_regenerate():
    return run_api(lambda s: api.regenerate(s, body().get("message_id")))


@w.app.post("/api/speak_again")
def r_speak_again():
    return run_api(lambda s: api.speak_again(s, body().get("message_id")))


@w.app.get("/api/account")
def r_account():
    return run_api(lambda s: api.account(s, request.args.get("message_id")))


@w.app.post("/api/vote")
def r_vote():
    return run_api(lambda s: api.vote(s, body().get("subject"), body().get("category"), body().get("value")))


@w.app.get("/api/score")
def r_score():
    return run_api(lambda s: api.score(s))


@w.app.get("/api/counters")
def r_counters():
    return run_api(lambda s: api.counters(s))


@w.app.post("/api/reset_counter")
def r_reset_counter():
    return run_api(lambda s: api.reset_counter(s, body().get("name")))


# web_app registers the real routes of the same paths first and they would win: the mock answers on their endpoints
for _name, _view in (("vote", r_vote), ("score", r_score), ("regenerate", r_regenerate), ("speak_again", r_speak_again), ("account_of", r_account),
                     ("counters", r_counters), ("reset_counter", r_reset_counter)):
    w.app.view_functions["chat_ops_api." + _name] = _view


@w.app.get("/api/items")
def r_items():
    return run_api(lambda s: api.items(s, request.args.get("kind")))


@w.app.post("/api/items")
def r_save_item():
    return run_api(lambda s: api.save_item(s, body().get("kind"), body().get("id"), body().get("text"), body().get("source"), **({"due": body()["due"]} if body().get("due") else {})))      # IF-101 v6 (A-09); an older mock has no due


@w.app.delete("/api/items")
def r_delete_item():
    return run_api(lambda s: api.delete_item(s, request.args.get("kind"), request.args.get("id")))


for _name, _view in (("items", r_items), ("save", r_save_item), ("delete", r_delete_item)):            # as above, for the real routes of items_api
    w.app.view_functions["items_api." + _name] = _view


@w.app.get("/api/trust")
def r_trust():
    return run_api(lambda s: api.trust(s))


@w.app.post("/api/trust")
def r_set_trust():
    return run_api(lambda s: api.set_trust(s, body().get("source"), body().get("value")))


@w.app.get("/api/persona")
def r_persona():
    return run_api(lambda s: api.persona(s))


@w.app.post("/api/persona")
def r_save_persona():
    return run_api(lambda s: api.save_persona(s, body().get("doc")))


for _name, _view in (("trust", r_trust), ("set_trust", r_set_trust), ("persona", r_persona), ("save_persona", r_save_persona)):    # as above, for trust_persona_api
    w.app.view_functions["trust_persona_api." + _name] = _view


@w.socketio.on("connect")
def connect(_auth=None):
    token = session()
    if token is None:
        raise ConnectionRefusedError("unauthenticated")
    with lock:
        api.connect(token)
        sids.setdefault(token, set()).add(request.sid)
        tokens[request.sid] = token
        status = api._status()
    emit("chat_status", {"busy": status["busy"], "queue": status["queue"], "activity": "idle", "model": "mock", "profile": "light"})


@w.socketio.on("disconnect")
def disconnect(_reason=None):
    token = tokens.pop(request.sid, None)
    if token:
        sids.get(token, set()).discard(request.sid)


@w.socketio.on("chat_send")
def chat_send(data=None):
    data = data if isinstance(data, dict) else {"text": data}
    token = tokens.get(request.sid)
    if token is None:
        return {"ok": False, "error": "unauthenticated"}
    try:
        with lock:
            ack = api.send(token, data.get("text"), data.get("id"))
            message = ack["message"]
    except ApiError as err:
        return {"ok": False, "error": {"queue_full": "The queue is full: wait for an answer.", "empty_text": "There is no text to send."}.get(err.code, err.code)}
    deliver()                                              # the broadcast of the message itself and the new queue status
    if not answering.is_set():
        answering.set()
        w.socketio.start_background_task(answer_later)
    return {"ok": True, "id": ack["id"], "position": ack["position"], "message": message}


@w.socketio.on("chat_stop")
def chat_stop(_=None):
    token = tokens.get(request.sid)
    with lock:
        return {"stopped": api.stop(token)["stopped"] if token else False}


if __name__ == "__main__":
    print("accounts:", ", ".join("%s / %s" % item for item in ACCOUNTS.items()))
    w.socketio.run(w.app, host=os.environ.get("MIA_STUB_HOST", "127.0.0.1"), port=int(os.environ.get("MIA_MOCK_PORT", "8686")), allow_unsafe_werkzeug=True)
