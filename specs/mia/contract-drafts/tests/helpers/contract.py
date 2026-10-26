"""subject_for(interface, kind): the provider of an interface for a contract suite (protected).

kind "mock" gives the mock of the interface (green from the start, stage 1). kind "real" is skipped until the provider node is
integrated (stage 2); the integration step of that node replaces the skip with the real adapter and removes the reason below.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "mocks"))

REAL_NOT_READY = {
    "IF-101": "N-2 Backend not integrated yet",       # real_subject: A-05 login, session, logout; A-07 the routes and the chat service; only the unbuilt events skip
    "IF-102": "N-3 Database not integrated yet",
    "IF-103": "the real model server is only used in stage 2",
    "IF-104": "N-2 Backend not integrated yet",
    "IF-105": "N-2 Backend not integrated yet",
    "IF-201": "N-2.2 Chat agent not integrated yet",       # real_subject since A-07 (ChatService); stop and the expression/audio events skip
    "IF-202": "N-2.4 Workflow execution not integrated yet",
    "IF-203": "N-2.3 Workflow management not integrated yet",
    "IF-204": "N-2.5 Voice synthesis not integrated yet",
    "IF-301": "N-3.2 Graph tables not integrated yet",
    "IF-302": "N-3.3 Record tables not integrated yet",
    "IF-401": "N-2.4.3 Run log not integrated yet",
    "IF-402": "N-2.4.2 Tools and sandbox not integrated yet",
    "IF-404": "the real web client and SearXNG are only used in stage 2",
    "IF-405": "the real scholarly APIs are only used in stage 2",
}


def each_provider(interface, make=None):
    """Marks a test of a contract suite. `make(kind)` may build the subject differently for this test (for example with a
    short queue); without it subject_for(interface, kind) is used. The class decorator `contract` turns every marked test
    into two: <name>_mock (stage 1, must pass) and <name>_real (stage 2, skipped until the provider is integrated)."""
    def tag(test):
        test.contract_interface, test.contract_make = interface, make
        return test
    return tag


def contract(cls):
    for name, test in list(vars(cls).items()):
        interface = getattr(test, "contract_interface", None)
        if interface is None:
            continue
        delattr(cls, name)
        for kind in ("mock", "real"):
            def run(self, test=test, kind=kind, interface=interface):
                make = test.contract_make
                test(self, make(kind) if make else subject_for(interface, kind))
            run.__name__, run.__doc__ = "%s_%s" % (name, kind), test.__doc__
            run.req_ids = getattr(test, "req_ids", ())
            setattr(cls, run.__name__, run)
    return cls


def subject_for(interface, kind, **options):
    if kind == "mock":
        if interface == "IF-101":
            from if_101_chat_api import ChatApiMock
            return ChatApiMock()
        if interface == "IF-102":
            from if_102_storage import StorageMock
            return StorageMock()
        if interface == "IF-103":
            from if_103_model_server import ModelServerMock
            return ModelServerMock()
        if interface == "IF-104":
            from if_104_graph_api import GraphApiMock
            return GraphApiMock()
        if interface == "IF-105":
            from if_105_evaluation_access import EvaluationAccessMock
            return EvaluationAccessMock()
        if interface == "IF-201":
            from if_201_chat_turn import ChatTurnMock
            return ChatTurnMock()
        if interface == "IF-202":
            from if_202_run_workflow import RunWorkflowMock
            return RunWorkflowMock()
        if interface == "IF-203":
            from if_203_workflow_library import WorkflowLibraryMock
            return WorkflowLibraryMock()
        if interface == "IF-204":
            from if_204_speech import SpeechMock
            return SpeechMock()
        if interface == "IF-301":
            from if_301_graph_tables import GraphTablesMock
            return GraphTablesMock()
        if interface == "IF-302":
            from if_302_record_tables import RecordTablesMock
            return RecordTablesMock()
        if interface == "IF-401":
            from if_401_run_events import RunEventsMock
            return RunEventsMock()
        if interface == "IF-402":
            from if_402_tool_calls import ToolCallsMock
            return ToolCallsMock()
        if interface == "IF-404":
            from if_404_web import WebMock
            return WebMock()
        if interface == "IF-405":
            from if_405_scholarly_sources import ScholarMock
            return ScholarMock()
        raise KeyError(interface)
    real = real_subject(interface, **options)
    if real is not None:
        return real
    raise unittest.SkipTest(REAL_NOT_READY[interface])


REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class _StorageAdapter:
    """IF-102 on the real Storage layer: the file backend in a fresh folder (stage 2), or PostgreSQL when MIA_TEST_DATABASE_URL is set (stage 3). The
    adapter only turns the error class of the layer into the one of the mock, which the suite expects; production code does not import from tests/."""

    def __init__(self):
        import tempfile
        from errors import StorageError
        from storage import Storage
        url = os.environ.get("MIA_TEST_DATABASE_URL")
        if url:
            from storage_postgres import PostgresBackend
            backend = PostgresBackend(url)
            backend._query("TRUNCATE records")
        else:
            from storage_files import FileBackend
            backend = FileBackend(tempfile.mkdtemp())
        self._store, self._error = Storage(backend), StorageError

    def __getattr__(self, name):
        from storage import StorageError as LayerError
        method = getattr(self._store, name)

        def call(*args, **kwargs):
            try:
                return method(*args, **kwargs)
            except LayerError as err:
                raise self._error(err.code, rule=err.rule, detail=err.detail)
        return call


class _ChatApiAdapter:
    """IF-101 on the real Backend as far as it exists (amendment A-05: login, throttling, whoami, change_password, logout; amendment A-07: the operations over the
    routes of the Backend). The sessions run on the Storage layer in a fresh folder and a clock that `advance_time` moves (it also moves the time of a vote, so
    its ISO week). The records, the trust of sources, the persona, the votes and the operations on answers go through the REAL routes (items_api, trust_persona_api,
    chat_ops_api) of a Flask app whose guard reads the session like accounts_api does; the answers come from the real ChatService with a scripted model and a worker
    that runs when the test calls `settle` (so the queue can be seen). The Backend refuses every request without a valid session with 401. What is not built yet
    (the streaming events of an answer, the queue limits inside the agent, `stop`, the variant event: N-2.1 T-03 rest, N-2.2, N-2.5) skips the test with the name of
    the operation. The adapter turns the error class of the service into the one of the mock, which the suite expects; production code does not import from tests/."""

    ACCOUNTS = {"anna": "pw-anna", "ben": "pw-ben"}                 # the accounts of the mock, so that the same suite runs on both
    TRUST_SOURCES = {"example.org": 0.5}                            # a source the mock has and the default table does not: seeded through the override file
    START = 1767571200                                              # 2026-01-05 00:00 UTC, a Monday: the clock 0 of the mock

    def __init__(self, answers=None, queue_limit=5, user_limit=2):
        import tempfile
        from errors import ApiError
        from storage import Storage
        from storage_files import FileBackend
        import accounts
        import api_sessions
        from chat_log import ChatLog
        from chat_ops_api import create_chat_ops_blueprint
        from chat_service import ChatService
        from flask import Flask, g, jsonify, request
        from items_api import create_items_blueprint
        from moods import MoodTracker
        from trust_persona_api import create_trust_persona_blueprint
        folder = tempfile.mkdtemp()
        store = Storage(FileBackend(os.path.join(folder, "db")))
        for name, password in self.ACCOUNTS.items():
            accounts.create(store, name, password, "contract suite")
        self._now, self._events, self._pending = 0.0, {}, []
        self._answers = list(answers or [])                         # the same scripts as the mock: a list of sentences, or {"sentences": [...], "emotion": ...}
        if any(isinstance(a, dict) and a.get("emotion") for a in self._answers):
            raise unittest.SkipTest("IF-101 expression and audio_chunk events of an answer are not in the real Backend yet (N-2.5)")
        self._service, self._service_error, self._error = api_sessions.SessionService(store, clock=lambda: self._now), api_sessions.ApiError, ApiError
        trust_file = os.path.join(folder, "source_trust.json")
        with open(trust_file, "w", encoding="utf-8") as fp:
            json.dump({"classes": {name: {"prior": value, "reason": "contract suite"} for name, value in self.TRUST_SOURCES.items()}}, fp)
        self._chat = ChatService(self._broadcast, ChatLog(os.path.join(folder, "chat.jsonl")), MoodTracker(os.path.join(REPO, "moods.json")),
                                 self._scripted_answer, queue_size=queue_limit, user_limit=user_limit, spawn=self._pending.append,
                                 votes=store, wall_clock=lambda: self.START + self._now)
        app = Flask(__name__)

        @app.before_request
        def guard():
            try:
                g.account = self._service.whoami(request.headers.get("X-Session"))["user"]
            except self._service_error as err:
                return jsonify({"error": err.code}), err.status

        for blueprint in (create_items_blueprint(store, self._broadcast), create_trust_persona_blueprint(trust_file, os.path.join(folder, "persona.json"), self._broadcast),
                          create_chat_ops_blueprint(self._chat)):
            app.register_blueprint(blueprint)
        self._http = app.test_client()

    def advance_time(self, seconds):
        self._now += seconds

    def _scripted_answer(self, text, on_delta, on_emotion, should_stop):
        sentences = self._answers.pop(0) if self._answers else ["Hello."]
        shown = ""
        for sentence in sentences:
            shown = (shown + " " + sentence).strip()
            on_delta(shown)
        return shown

    def settle(self):
        """runs the worker of the chat agent until the queue is empty"""
        while self._pending:
            self._pending.pop(0)()

    def _broadcast(self, event, payload):
        for session in self._events:
            self._events[session].append({"event": event, "payload": payload})

    def _call(self, name, *args):
        try:
            return getattr(self._service, name)(*args)
        except self._service_error as err:
            raise self._error(err.status, err.code, err.rule)

    def _route(self, method, path, session, **kwargs):
        got = getattr(self._http, method)(path, headers={"X-Session": session or ""}, **kwargs)
        body = got.get_json(silent=True)
        if got.status_code >= 400:
            raise self._error(got.status_code, (body or {}).get("error"), (body or {}).get("rule"))
        return body

    def login(self, user, password):
        token = self._call("login", user, password)
        self._events[token] = []
        return token

    def whoami(self, session):
        return self._call("whoami", session)

    def change_password(self, session, old, new):
        return self._call("change_password", session, old, new)

    def logout(self, session):
        result = self._call("logout", session)
        self._events.pop(session, None)
        return result

    def connect(self, session):
        """opening the socket is checking the session (the connect guard of the Backend)"""
        self._call("whoami", session)
        self._events.setdefault(session, [])

    def events(self, session):
        self._call("whoami", session)
        out, self._events[session] = self._events.get(session, []), []
        return out

    def send(self, session, text, client_id=None):
        user = self._call("whoami", session)["user"]
        ack = self._chat.send(text, client_id=client_id, sender=user, author=user)
        if not ack["ok"]:
            raise self._error({"empty_text": 422, "queue_full": 503}.get(ack.get("code"), 429), ack.get("code") or "rate_limited")
        return {"id": ack["id"], "position": ack["position"], "message": ack["message"]}

    def history(self, session, limit=50):
        self._call("whoami", session)
        return [dict(r, sender=r.get("sender") or "MIA") for r in self._chat.log.history(limit=limit)[0]]

    def items(self, session, kind):
        return self._route("get", "/api/items?kind=%s" % kind, session)

    def save_item(self, session, kind, item_id, text, source=None):
        return self._route("post", "/api/items", session, json={"kind": kind, "id": item_id, "text": text, "source": source})

    def delete_item(self, session, kind, item_id):
        return self._route("delete", "/api/items?kind=%s&id=%s" % (kind, item_id), session)

    def trust(self, session):
        return self._route("get", "/api/trust", session)

    def set_trust(self, session, source, value):
        return self._route("post", "/api/trust", session, json={"source": source, "value": value})

    def persona(self, session):
        return self._route("get", "/api/persona", session)

    def save_persona(self, session, doc):
        return self._route("post", "/api/persona", session, json={"doc": doc})

    def vote(self, session, message_id, category, value):
        return self._route("post", "/api/vote", session, json={"subject": message_id, "category": category, "value": value})

    def score(self, session):
        return self._route("get", "/api/score", session)

    def regenerate(self, session, message_id):
        return self._route("post", "/api/regenerate", session, json={"message_id": message_id})

    def speak_again(self, session, message_id):
        return self._route("post", "/api/speak_again", session, json={"message_id": message_id})

    def account(self, session, message_id):
        return self._route("get", "/api/account?message_id=%s" % message_id, session)

    def run_with_variant(self, variant):
        raise unittest.SkipTest("IF-101 no workflow picks a character variant yet (REQ-CHV-008)")

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)

        def not_built(session=None, *args, **kwargs):
            self._call("whoami", session)                            # an unknown session is 401 unauthenticated, as for every request of the real Backend
            raise unittest.SkipTest("IF-101 %s is not in the real Backend yet" % name)
        return not_built


class _ChatTurnAdapter:
    """IF-201 on the real chat agent (amendment A-07): the ChatService with a scripted model and a worker that runs when the test calls `settle`. The accounts are
    plain names (the Backend has checked them). What is not built yet (expression and audio_chunk of an answer: N-2.5; `stop` of an answer that has not started:
    N-2.2 T-01) skips the test. The adapter turns the error class of the service into the one of the mock; production code does not import from tests/."""

    START = 1767571200                                              # 2026-01-05 00:00 UTC, a Monday: the clock 0 of the mock

    def __init__(self, answers=None, queue_limit=5):
        import tempfile
        from errors import ServiceError
        from chat_log import ChatLog
        from chat_service import ChatError, ChatService
        from moods import MoodTracker
        from storage import Storage
        from storage_files import FileBackend
        self._answers, self._now, self._pending, self._callbacks = list(answers or []), 0.0, [], []
        if any(isinstance(a, dict) and a.get("emotion") for a in self._answers):
            raise unittest.SkipTest("IF-201 expression and audio_chunk events of an answer are not in the real chat agent yet (N-2.5)")
        folder = tempfile.mkdtemp()
        self._error, self._chat_error = ServiceError, ChatError
        self._chat = ChatService(self._deliver, ChatLog(os.path.join(folder, "chat.jsonl")), MoodTracker(os.path.join(REPO, "moods.json")), self._scripted_answer,
                                 queue_size=queue_limit, spawn=self._pending.append, votes=Storage(FileBackend(os.path.join(folder, "db"))),
                                 wall_clock=lambda: self.START + self._now)

    def _deliver(self, event, payload):
        for callback in list(self._callbacks):
            callback({"event": event, "payload": payload})

    def _scripted_answer(self, text, on_delta, on_emotion, should_stop):
        sentences = self._answers.pop(0) if self._answers else ["Hello."]
        shown = ""
        for sentence in sentences:
            shown = (shown + " " + sentence).strip()
            on_delta(shown)
        return shown

    def _call(self, fn):
        try:
            return fn()
        except self._chat_error as err:
            raise self._error(err.code, rule=err.rule)

    def send(self, account, text, client_id=None):
        ack = self._chat.send(text, client_id=client_id, sender=account, author=account)
        if not ack["ok"]:
            raise self._error(ack.get("code") or "rate_limited")
        return {"id": ack["id"], "position": ack["position"]}

    def regenerate(self, account, message_id):
        return self._call(lambda: self._chat.regenerate(account, message_id))

    def speak_again(self, message_id):
        return self._call(lambda: self._chat.speak_again(message_id))

    def account(self, message_id):
        return self._call(lambda: self._chat.account(message_id))

    def vote(self, account, subject, category, value):
        return self._call(lambda: self._chat.vote(account, subject, category, value))

    def score(self):
        return self._chat.score()

    def advance_time(self, seconds):
        self._now += seconds

    def stop(self):
        raise unittest.SkipTest("IF-201 stop of an answer that has not started is not in the real chat agent yet (N-2.2 T-01)")

    def history(self, limit=50):
        return [dict(r, sender=r.get("sender") or "MIA") for r in self._chat.log.history(limit=limit)[0]]

    def status(self):
        return self._chat.status()

    def subscribe(self, callback):
        self._callbacks.append(callback)
        return lambda: self._callbacks.remove(callback)

    def settle(self):
        while self._pending:
            self._pending.pop(0)()


def real_subject(interface, **options):
    """The real provider of an interface once its node is integrated (amendment A-02: IF-301, IF-302, IF-102 of the Database; amendment A-05, A-07: IF-101 and IF-201 as far as built); None until then."""
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    if interface == "IF-301":
        import graph_tables
        return graph_tables
    if interface == "IF-302":
        import record_tables
        return record_tables
    if interface == "IF-102":
        return _StorageAdapter()
    if interface == "IF-101":
        return _ChatApiAdapter(**options)
    if interface == "IF-201":
        return _ChatTurnAdapter(**options)
    return None
