"""
TC-LOG-001, TC-LOG-002, TC-LOG-003, TC-IF-401 (REQ-LOG-001 to -003, IF-401): the provider of the run event log, `run_events.RunEvents`: typed events with one run id and the starting user, secrets
removed, an order that can be checked, the account of a run from its events only, two runs compared, and the events kept as append-only files (REQ-LOG-005, A-28), one file per run.
The golden cases of the contract suite (tests/acceptance/contract/test_if_401_run_events.py) are repeated here on the real provider until the adapter of the suite is installed.
Run: python tests/test_run_events.py
"""
import json
import os
import re
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers", "mocks"))

import if_401_run_events as mock  # noqa: E402  (the list of types of the contract)
from run_events import RunEvents, RunEventsError, TYPES  # noqa: E402


def code_of(call):
    try:
        call()
    except RunEventsError as err:
        return err.code
    raise AssertionError("no RunEventsError raised")


class Provider(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = os.path.join(self.tmp.name, "runs")
        self.log = RunEvents(self.folder)

    def test_the_types_are_those_of_the_contract(self):
        self.assertEqual(TYPES, mock.TYPES)

    def test_events_have_run_id_user_and_a_sequence_and_the_account_lists_the_plain_texts(self):          # TC-IF-401-01, TC-LOG-001
        self.assertEqual(self.log.emit("r1", "run_start", {"workflow": "lookup"}, "anna", plain="Starting lookup"), {"seq": 1})
        self.log.emit("r1", "model_call", {"model": "MP-light"}, "anna", actor="runner")
        self.log.emit("r1", "run_end", {"status": "done"}, "anna", plain="Done")
        events = self.log.events("r1")
        self.assertEqual([e["seq"] for e in events], [1, 2, 3])
        self.assertTrue(all(e["run_id"] == "r1" and e["user"] == "anna" for e in events))
        self.assertEqual(events[1]["actor"], "runner")
        self.assertEqual([a["plain"] for a in self.log.account("r1")], ["Starting lookup", "Done"])
        self.assertEqual([a["seq"] for a in self.log.account("r1")], [1, 3])
        self.assertEqual(self.log.check_order("r1"), [])

    def test_the_account_is_built_from_the_logged_plain_texts_only(self):                                 # TC-LOG-001: equals a rendering of the events, no model-written part
        self.log.emit("r1", "run_start", {}, "anna", plain="One")
        self.log.emit("r1", "tool_call", {"tool": "web_search", "plain": "this key of the payload is no plain text"}, "anna")
        self.log.emit("r1", "run_end", {}, "anna", plain="Two")
        self.assertEqual(self.log.account("r1"), [{"seq": 1, "plain": "One"}, {"seq": 3, "plain": "Two"}])

    def test_an_unknown_type_is_refused_and_nothing_is_written_and_secrets_are_removed(self):             # TC-IF-401-02, TC-LOG-002
        self.log.emit("r1", "run_start", {}, "anna")
        self.assertEqual(code_of(lambda: self.log.emit("r1", "nonsense", {}, "anna")), "unknown_type")
        self.assertEqual(len(self.log.events("r1")), 1)
        self.log.emit("r1", "tool_call", {"tool": "web_search", "api_key": "sk-123", "nested": {"password": "hunter2", "query": "q"}}, "anna", plain="Mail me@example.org")
        payload = self.log.events("r1")[1]["payload"]
        self.assertEqual((payload["api_key"], payload["nested"]["password"], payload["nested"]["query"]), ("[removed]", "[removed]", "q"))
        self.assertEqual(code_of(lambda: self.log.events("none")), "unknown_run")
        with open(self.log.path("r1"), encoding="utf-8") as handle:
            raw = handle.read()
        for secret in ("sk-123", "hunter2", "me@example.org"):
            self.assertNotIn(secret, raw)                                                                 # not in the file either: the writer never had them in a line

    def test_the_payload_must_be_an_object_and_the_run_id_a_plain_name(self):
        self.assertEqual(code_of(lambda: self.log.emit("r1", "run_start", "text", "anna")), "invalid_payload")
        for bad in ("", "../x", "a/b", ".hidden", "x" * 200, None):
            self.assertEqual(code_of(lambda: self.log.emit(bad, "run_start", {}, "anna")), "invalid_run", bad)
        self.assertEqual(os.listdir(self.folder) if os.path.isdir(self.folder) else [], [])

    def test_a_broken_order_is_reported(self):                                                            # TC-IF-401-03, TC-LOG-002
        self.log.emit("r1", "run_start", {}, "anna")
        self.inject("r1", {"seq": 3, "type": "run_end", "run_id": "r1", "user": "anna", "actor": None, "plain": "", "payload": {}, "time": 9})
        self.assertTrue(self.log.check_order("r1"))
        self.inject("r2", {"seq": 1, "type": "check_run", "run_id": "r2", "user": "anna", "actor": None, "plain": "", "payload": {}, "time": 1})
        self.assertTrue(any("run_start" in p for p in self.log.check_order("r2")))

    def test_a_half_written_last_line_hides_nothing_and_is_reported(self):
        self.log.emit("r1", "run_start", {}, "anna")
        self.log.emit("r1", "run_end", {}, "anna")
        with open(self.log.path("r1"), "a", encoding="utf-8") as fp:
            fp.write('{"seq": 3, "type": "error", "run_')                                                 # a crash in the middle of a write
        self.assertEqual([e["seq"] for e in self.log.events("r1")], [1, 2])
        self.assertEqual(self.log.check_order("r1"), [])                                                  # nothing is missing before the cut
        self.log.emit("r1", "error", {"message": "after the crash"}, "anna")
        self.assertEqual([e["seq"] for e in self.log.events("r1")], [1, 2, 3])

    def test_two_runs_can_be_compared(self):                                                              # TC-IF-401-04, TC-LOG-003
        for run in ("a", "b"):
            self.log.emit(run, "run_start", {"workflow": "lookup"}, "anna")
            self.log.emit(run, "run_end", {"status": "done"}, "anna")
        self.assertEqual(self.log.compare("a", "b"), {"same": True, "differences": []})
        self.log.emit("c", "run_start", {"workflow": "lookup"}, "ben")
        self.log.emit("c", "check_run", {"name": "number_check"}, "ben")
        self.log.emit("c", "run_end", {"status": "done"}, "ben")
        result = self.log.compare("a", "c")
        self.assertFalse(result["same"])
        self.assertTrue(result["differences"])
        self.assertEqual(code_of(lambda: self.log.compare("a", "none")), "unknown_run")

    def test_the_events_are_append_only_files_one_per_run_and_a_new_instance_goes_on_where_the_old_stopped(self):      # REQ-LOG-005
        self.log.emit("r1", "run_start", {}, "anna")
        self.log.emit("r2", "run_start", {}, "ben")
        self.assertEqual(sorted(os.listdir(self.folder)), ["r1.jsonl", "r2.jsonl"])
        with open(self.log.path("r1"), "rb") as fp:
            before = fp.read()
        again = RunEvents(self.folder)                                                                    # a restart
        self.assertEqual(again.emit("r1", "run_end", {}, "anna"), {"seq": 2})
        with open(self.log.path("r1"), "rb") as fp:
            after = fp.read()
        self.assertTrue(after.startswith(before) and len(after) > len(before))                            # what was written stays as it was
        self.assertEqual([e["type"] for e in self.log.events("r1")], ["run_start", "run_end"])

    def test_events_of_threads_get_distinct_numbers_without_a_gap(self):
        self.log.emit("r1", "run_start", {}, "anna")

        def work():
            for _ in range(25):
                self.log.emit("r1", "tool_call", {"tool": "t"}, "anna")
        threads = [threading.Thread(target=work) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual([e["seq"] for e in self.log.events("r1")], list(range(1, 102)))
        self.assertEqual(self.log.check_order("r1"), [])

    def test_each_line_is_a_complete_json_object_with_the_fields_of_the_contract(self):
        self.log.emit("r1", "run_start", {"workflow": "lookup"}, "anna", actor="runner", plain="Go")
        with open(self.log.path("r1"), encoding="utf-8") as fp:
            line = json.loads(fp.readline())
        self.assertEqual(sorted(line), ["actor", "payload", "plain", "run_id", "seq", "time", "type", "user"])
        self.assertTrue(re.fullmatch(r"[0-9.]+", repr(line["time"])))

    def inject(self, run_id, event):
        """a raw line, bypassing emit (to build a broken log)"""
        os.makedirs(self.folder, exist_ok=True)
        with open(self.log.path(run_id), "a", encoding="utf-8") as fp:
            fp.write(json.dumps(event) + "\n")


if __name__ == "__main__":
    unittest.main()
