"""IF-401 run event log (Pipeline runner and Tools to Run log): the contract suite runs against the mock (stage 1) and the real Run log (stage 2,
skipped until N-2.4.3 is integrated). Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_401_run_events.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider  # noqa: E402
from markers import mark                      # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from errors import ServiceError               # noqa: E402

IF = "IF-401"


def code_of(call):
    try:
        call()
    except ServiceError as err:
        return err.code
    raise AssertionError("no ServiceError raised")


@contract
class RunEventsContract(unittest.TestCase):
    @mark.req("IF-401", "REQ-BE-058")
    @each_provider(IF)
    def test_events_have_run_id_user_and_a_sequence(self, log):
        """TC-IF-401-01 golden 1: three events give seq 1, 2, 3, each with the run id and the starting user; the account lists the events with a plain text."""
        self.assertEqual(log.emit("r1", "run_start", {"workflow": "lookup"}, "anna", plain="Starting lookup"), {"seq": 1})
        log.emit("r1", "model_call", {"model": "MP-light"}, "anna", actor="runner")
        log.emit("r1", "run_end", {"status": "done"}, "anna", plain="Done")
        events = log.events("r1")
        self.assertEqual([e["seq"] for e in events], [1, 2, 3])
        self.assertTrue(all(e["run_id"] == "r1" and e["user"] == "anna" for e in events))
        self.assertEqual([a["plain"] for a in log.account("r1")], ["Starting lookup", "Done"])
        self.assertEqual(log.check_order("r1"), [])

    @mark.req("IF-401", "REQ-BE-058")
    @each_provider(IF)
    def test_unknown_type_and_secrets(self, log):
        """TC-IF-401-02 golden 2: an unknown type is refused and nothing is written; secrets in the payload are stored as [removed]."""
        log.emit("r1", "run_start", {}, "anna")
        self.assertEqual(code_of(lambda: log.emit("r1", "nonsense", {}, "anna")), "unknown_type")
        self.assertEqual(len(log.events("r1")), 1)
        log.emit("r1", "tool_call", {"tool": "web_search", "api_key": "sk-123", "nested": {"password": "x", "query": "q"}}, "anna")
        payload = log.events("r1")[1]["payload"]
        self.assertEqual((payload["api_key"], payload["nested"]["password"], payload["nested"]["query"]), ("[removed]", "[removed]", "q"))
        self.assertEqual(code_of(lambda: log.events("none")), "unknown_run")

    @mark.req("IF-401", "REQ-BE-059")
    @each_provider(IF)
    def test_a_broken_order_is_reported(self, log):
        """TC-IF-401-03: a log whose first event is not run_start, or whose seq has a gap, is reported."""
        log.emit("r1", "run_start", {}, "anna")
        log.inject_event("r1", {"seq": 3, "type": "run_end", "run_id": "r1", "user": "anna", "actor": None, "plain": "", "payload": {}, "time": 9})
        self.assertTrue(log.check_order("r1"))
        log.inject_event("r2", {"seq": 1, "type": "check_run", "run_id": "r2", "user": "anna", "actor": None, "plain": "", "payload": {}, "time": 1})
        self.assertTrue(any("run_start" in p for p in log.check_order("r2")))

    @mark.req("IF-401", "REQ-BE-059")
    @each_provider(IF)
    def test_two_runs_can_be_compared(self, log):
        """TC-IF-401-04 golden 3: the same steps differ only in time and run id (same); one extra check_run is a difference."""
        for run in ("a", "b"):
            log.emit(run, "run_start", {"workflow": "lookup"}, "anna")
            log.emit(run, "run_end", {"status": "done"}, "anna")
        self.assertEqual(log.compare("a", "b"), {"same": True, "differences": []})
        log.emit("c", "run_start", {"workflow": "lookup"}, "ben")
        log.emit("c", "check_run", {"name": "number_check"}, "ben")
        log.emit("c", "run_end", {"status": "done"}, "ben")
        result = log.compare("a", "c")
        self.assertFalse(result["same"])
        self.assertTrue(result["differences"])


if __name__ == "__main__":
    unittest.main()
