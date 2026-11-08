"""The storage stand-in of the G-V2.STORE acceptance tests (TR-GTB-002) and the gate that it passes IF-102 first.

GraphStoreStandIn is the IF-102 mock (versions, immutability, errors as the contract suite fixes them) plus the four record tables of IF-301 v2.
Like the Storage layer it calls check_record of the Graph tables before every write to those tables and writes nothing when that gives a rule
(REQ-GTB-016); the version counter is the mock's, changed only by a write that passed. Known gap: no transactions across tables, no real database
(IF-102 itself is run on postgres:16 at stage 3, contract-postgres).
"""
import importlib.util
import io
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "mocks"))   # appended: the mocks have their own graph_rules, which must not hide the real one

from errors import StorageError          # noqa: E402
from if_102_storage import StorageMock   # noqa: E402

RECORD_TABLES = ("graph_nodes", "graph_edges", "graphs", "skills", "context_nodes", "context_edges")


class GraphStoreStandIn(StorageMock):
    def __init__(self):
        super().__init__()
        for table in RECORD_TABLES:
            self._rows[table], self._listeners[table] = {}, []

    def stored(self):
        """What the caller has stored, in the form check_record takes: {"nodes": {id: [versions]}, "edges": {id: [versions]}}."""
        return {"nodes": {i: [v["version"] for v in vs] for i, vs in self._rows["graph_nodes"].items()},
                "edges": {i: [v["version"] for v in vs] for i, vs in self._rows["graph_edges"].items()},
                "context_nodes": {i: [v["version"] for v in vs] for i, vs in self._rows["context_nodes"].items()},
                "context_edges": {i: [v["version"] for v in vs] for i, vs in self._rows["context_edges"].items()}}

    def put(self, table, record_id, doc, author, expected_version=None, categories=None):
        if table in RECORD_TABLES:
            import graph_tables
            refused = graph_tables.check_record(table, doc, categories=categories, stored=self.stored(), record_id=record_id)
            if refused:
                raise StorageError("invalid", rule=refused["rule"], detail=refused["detail"])
        return super().put(table, record_id, doc, author, expected_version)

    def delete(self, table, record_id, author):
        if table in RECORD_TABLES:               # versioned records are never deleted (definitions of IF-301 v2)
            raise StorageError("immutable")
        return super().delete(table, record_id, author)


def if_102_suite_problems(make_store):
    """Runs the stage 1 cases (_mock) of the IF-102 contract suite with stores from make_store as the provider; returns a list of problems (empty: it passes)."""
    import contract
    path = os.path.join(os.path.dirname(HERE), "acceptance", "contract", "test_if_102_storage.py")
    spec = importlib.util.spec_from_file_location("if_102_suite_for_the_standin", path)
    suite_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(suite_module)
    loader = unittest.TestLoader()
    tests = [t for t in loader.loadTestsFromTestCase(suite_module.StorageContract) if t.id().endswith("_mock")]
    with mock.patch.object(contract, "subject_for", lambda interface, kind, **options: make_store()):
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(unittest.TestSuite(tests))
    problems = ["%s: %s" % (case.id(), text.strip().splitlines()[-1]) for case, text in result.failures + result.errors]
    problems += ["skipped: %s" % case.id() for case, _ in result.skipped]
    if result.testsRun == 0:
        problems.append("no IF-102 case ran")
    return problems
