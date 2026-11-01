"""IF-401 run event log (Pipeline runner and Tools to Run log): the contract suite runs against the mock (stage 1) and the real Run log (stage 2,
run_events.RunEvents since A-29). Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_401_run_events.py"""
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
        """TC-IF-401-01 golden 1: three events give seq 1, 2, 3, each with the run id and the starting user; the account lists the events with a plain text.
        Example: run_start (plain "Starting lookup"), model_call, run_end (plain "Done") by anna in r1 give seq 1, 2, 3 and the account ["Starting lookup", "Done"]."""
        # Given a run r1 with three events of anna, two of them with a plain text
        self.assertEqual(log.emit("r1", "run_start", {"workflow": "lookup"}, "anna", plain="Starting lookup"), {"seq": 1})
        log.emit("r1", "model_call", {"model": "MP-light"}, "anna", actor="runner")
        log.emit("r1", "run_end", {"status": "done"}, "anna", plain="Done")
        # When its events are read
        events = log.events("r1")
        # Then they count 1, 2, 3, carry the run id and the user, and the account lists the plain texts in order
        self.assertEqual([e["seq"] for e in events], [1, 2, 3])
        self.assertTrue(all(e["run_id"] == "r1" and e["user"] == "anna" for e in events))
        self.assertEqual([a["plain"] for a in log.account("r1")], ["Starting lookup", "Done"])
        self.assertEqual(log.check_order("r1"), [])

    @mark.req("IF-401", "REQ-BE-058")
    @each_provider(IF)
    def test_unknown_type_and_secrets(self, log):
        """TC-IF-401-02 golden 2 (v2, A-53): an unknown type is refused and nothing is written; a value under a secret-like key is stored as [removed] whatever its type
        (text, number, null, list, object, at any depth), an empty text "" stays "" (D-144, D-146); other keys keep their values.
        Example: {"api_key": "sk-123", "password": 123456, "token": ""} is stored as {"api_key": "[removed]", "password": "[removed]", "token": ""}."""
        # Given a run with one event
        log.emit("r1", "run_start", {}, "anna")
        # When an unknown type is emitted, Then it is refused and nothing is written
        self.assertEqual(code_of(lambda: log.emit("r1", "nonsense", {}, "anna")), "unknown_type")
        self.assertEqual(len(log.events("r1")), 1)
        # When a payload with secret-like keys of every kind of value is emitted
        log.emit("r1", "tool_call", {"tool": "web_search", "api_key": "sk-123", "password": 123456, "token": "", "secret": ["a", "b"],
                                     "nested": {"password": {"pin": 1}, "api_key": None, "query": "q", "count": 3}}, "anna")
        payload = log.events("r1")[1]["payload"]
        # Then every secret-like value is [removed] except the empty text, and the other values stay
        self.assertEqual((payload["api_key"], payload["password"], payload["secret"]), ("[removed]", "[removed]", "[removed]"))
        self.assertEqual((payload["nested"]["password"], payload["nested"]["api_key"]), ("[removed]", "[removed]"))
        self.assertEqual(payload["token"], "")
        self.assertEqual((payload["tool"], payload["nested"]["query"], payload["nested"]["count"]), ("web_search", "q", 3))
        self.assertEqual(code_of(lambda: log.events("none")), "unknown_run")

    @mark.req("IF-401", "REQ-BE-059")
    @each_provider(IF)
    def test_a_broken_order_is_reported(self, log):
        """TC-IF-401-03: a log whose first event is not run_start, or whose seq has a gap, is reported.
        Example: run_start with seq 1 followed by run_end with seq 3 gives a problem; a run r2 that starts with check_run gives a problem naming run_start."""
        # Given a run whose seq jumps from 1 to 3, When its order is checked, Then a problem is reported
        log.emit("r1", "run_start", {}, "anna")
        log.inject_event("r1", {"seq": 3, "type": "run_end", "run_id": "r1", "user": "anna", "actor": None, "plain": "", "payload": {}, "time": 9})
        self.assertTrue(log.check_order("r1"))
        # Given a run that starts with check_run, When its order is checked, Then the problem names run_start
        log.inject_event("r2", {"seq": 1, "type": "check_run", "run_id": "r2", "user": "anna", "actor": None, "plain": "", "payload": {}, "time": 1})
        self.assertTrue(any("run_start" in p for p in log.check_order("r2")))

    @mark.req("IF-401", "REQ-BE-059")
    @each_provider(IF)
    def test_two_runs_can_be_compared(self, log):
        """TC-IF-401-04 golden 3 (v2, A-53): the same steps differ only in time and run id (same); one extra check_run is a difference, so are the same types with
        another payload and one extra event at the end (D-144).
        Example: run_start, run_end {"status": "done"} against run_start, run_end {"status": "failed"} is {"same": False, "differences": [...]} with differences."""
        # Given two runs a and b with the same steps
        for run in ("a", "b"):
            log.emit(run, "run_start", {"workflow": "lookup"}, "anna")
            log.emit(run, "run_end", {"status": "done"}, "anna")
        # Then they compare as the same
        self.assertEqual(log.compare("a", "b"), {"same": True, "differences": []})
        # Given a run c with an extra check_run in the middle, a run d with the same types but another payload, a run e with an extra event at the end
        log.emit("c", "run_start", {"workflow": "lookup"}, "ben")
        log.emit("c", "check_run", {"name": "number_check"}, "ben")
        log.emit("c", "run_end", {"status": "done"}, "ben")
        log.emit("d", "run_start", {"workflow": "lookup"}, "anna")
        log.emit("d", "run_end", {"status": "failed"}, "anna")
        for type, payload in (("run_start", {"workflow": "lookup"}), ("run_end", {"status": "done"}), ("check_run", {"name": "number_check"})):
            log.emit("e", type, payload, "anna")
        # When each is compared with a, Then each is a difference that is named
        for other in ("c", "d", "e"):
            result = log.compare("a", other)
            self.assertFalse(result["same"], other)
            self.assertTrue(result["differences"], other)

    @mark.req("IF-401", "REQ-BE-058")
    @each_provider(IF)
    def test_malformed_calls_are_refused_and_write_nothing(self, log):
        """TC-IF-401-05 (v1, A-30): a run id that is not a plain name is invalid_run in every operation, a payload that is not an object is invalid_payload, an empty user is
        invalid_user; the run id is checked before the type, the type before the payload, the payload before the user; none of them writes an event.
        Example: emit("../x", "run_start", {}, "anna") is invalid_run; emit("r1", "run_end", "done", "anna") is invalid_payload and r1 keeps its one event."""
        # Given a run with one event
        log.emit("r1", "run_start", {}, "anna")
        # When malformed calls are made, Then each names its error
        for bad_run in ("../x", "a/b", "", ".hidden", "x" * 101, 7):
            self.assertEqual(code_of(lambda: log.emit(bad_run, "run_start", {}, "anna")), "invalid_run", bad_run)
        self.assertEqual(code_of(lambda: log.events("a/b")), "invalid_run")
        self.assertEqual(code_of(lambda: log.emit("r1", "run_end", "done", "anna")), "invalid_payload")
        self.assertEqual(code_of(lambda: log.emit("r1", "run_end", {}, "")), "invalid_user")
        self.assertEqual(code_of(lambda: log.emit("r1", "run_end", {}, None)), "invalid_user")
        self.assertEqual(code_of(lambda: log.emit("../x", "nonsense", "done", "")), "invalid_run")
        self.assertEqual(code_of(lambda: log.emit("r1", "nonsense", "done", "")), "unknown_type")
        self.assertEqual(code_of(lambda: log.emit("r1", "run_end", "done", "")), "invalid_payload")
        # Then nothing was written: r1 has its one event and the malformed run ids made no run
        self.assertEqual([e["seq"] for e in log.events("r1")], [1])
        self.assertEqual(code_of(lambda: log.events("x" * 100)), "unknown_run")


if __name__ == "__main__":
    unittest.main()
