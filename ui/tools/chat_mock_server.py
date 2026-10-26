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
sys.path.insert(0, os.path.join(repo, "tests", "helpers", "mocks"))

from flask import jsonify, request  # noqa: E402
from flask_socketio import emit  # noqa: E402

from socketio.exceptions import ConnectionRefusedError  # noqa: E402,A004  (the one the Socket.IO server turns into connect_error)

from errors import ApiError  # noqa: E402
from if_101_chat_api import ChatApiMock  # noqa: E402
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
    if request.path.startswith("/api/chat/") and request.path != "/api/chat/commands":
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
            turn["n"] += 1
            api._answer(api._queue.popleft())
            api._broadcast("chat_status", api._status())
    deliver()
    answering.clear()


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
            message = [m for m in api.history(token, limit=200) if m["id"] == ack["id"]][0]
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
