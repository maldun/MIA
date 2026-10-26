"""subject_for(interface, kind): the provider of an interface for a contract suite (protected).

kind "mock" gives the mock of the interface (green from the start, stage 1). kind "real" is skipped until the provider node is
integrated (stage 2); the integration step of that node replaces the skip with the real adapter and removes the reason below.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "mocks"))

REAL_NOT_READY = {
    "IF-101": "N-2 Backend not integrated yet",
    "IF-102": "N-3 Database not integrated yet",
    "IF-103": "the real model server is only used in stage 2",
    "IF-104": "N-2 Backend not integrated yet",
    "IF-105": "N-2 Backend not integrated yet",
    "IF-201": "N-2.2 Chat agent not integrated yet",
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


def subject_for(interface, kind):
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
    real = real_subject(interface)
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


def real_subject(interface):
    """The real provider of an interface once its node is integrated (amendment A-02: IF-301, IF-302, IF-102 of the Database); None until then."""
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
    return None
