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
}


def each_provider(interface, make=None):
    """Decorator: run the test once with the mock and once with the real provider (skipped until integrated).
    `make` may build the mock differently for a test (for example with a short queue): make(kind) -> subject."""
    def wrap(test):
        def run(self):
            for kind in ("mock", "real"):
                with self.subTest(kind):
                    test(self, make(kind) if make else subject_for(interface, kind))
        run.__name__, run.__doc__ = test.__name__, test.__doc__
        run.req_ids = getattr(test, "req_ids", ())
        return run
    return wrap


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
        raise KeyError(interface)
    raise unittest.SkipTest(REAL_NOT_READY[interface])
