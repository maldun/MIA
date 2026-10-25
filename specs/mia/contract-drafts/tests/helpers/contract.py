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
    "IF-201": "N-2.2 Chat agent not integrated yet",
    "IF-202": "N-2.4 Workflow execution not integrated yet",
    "IF-203": "N-2.3 Workflow management not integrated yet",
    "IF-204": "N-2.5 Voice synthesis not integrated yet",
    "IF-301": "N-3.2 Graph tables not integrated yet",
    "IF-302": "N-3.3 Record tables not integrated yet",
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
        raise KeyError(interface)
    raise unittest.SkipTest(REAL_NOT_READY[interface])
