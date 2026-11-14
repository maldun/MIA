"""
Unit test (F-02 of the first Verify run of G-V3.PANEL, REQ-WFM-136): a storage error while the status is enriched with the run record does not reach the
skill through the monitor; the plain status goes out. Run with: python tests/test_emit_status_storage_error.py
"""
import os
import sys
import types
import unittest
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chat_service import ChatService  # noqa: E402


class BrokenRecorder:
    def record(self, run, account=None):
        raise OSError("disk read failed")


class Probe:
    _recorder = BrokenRecorder()

    def __init__(self):
        self.sent = []

    def _emit(self, event, payload):
        self.sent.append((event, payload))


class TestEmitStatus(unittest.TestCase):
    def test_storage_error_does_not_reach_the_monitor(self):
        """Example: record() raises OSError, the plain task_status is still emitted"""
        probe, payload = Probe(), {"id": "r1", "done": False, "paused": False}
        ChatService._emit_status(probe, "task_status", payload)
        self.assertEqual(probe.sent, [("task_status", payload)])

    def test_the_error_is_logged(self):
        """F-14 of the second Verify run: the plain status goes out, and the error is not hidden: one log record names it.
        Example: record() raises OSError("disk read failed"), the log line holds "disk read failed"."""
        # Given: a recorder whose storage raises
        probe, payload = Probe(), {"id": "r1", "done": True, "paused": False}
        # When: the end status is emitted
        with unittest.mock.patch("chat_service.logger") as log:
            ChatService._emit_status(probe, "task_status", payload)
        # Then: the plain status went out and one error line names the cause
        self.assertEqual(probe.sent, [("task_status", payload)])
        self.assertEqual(log.error.call_count, 1)
        self.assertIn("disk read failed", " ".join(str(a) for a in log.error.call_args.args))

    def test_a_status_that_is_not_a_dict_goes_out_unchanged(self):
        """F-18 of the third Verify run: a payload without get() is no reason to raise out of the status.
        Example: the payload "plain" is emitted as it is."""
        # Given: a payload that is not a dict and a recorder that raises
        probe = Probe()
        # When: the status is emitted
        ChatService._emit_status(probe, "task_status", "plain")
        # Then: it goes out unchanged and nothing is raised
        self.assertEqual(probe.sent, [("task_status", "plain")])

    def test_a_healthy_recorder_logs_nothing(self):
        """F-19 of the third Verify run: the log line belongs to the error only.
        Example: a recorder that answers with the run record leaves the log empty and the status enriched."""
        # Given: a recorder that answers with the record of the run
        record = {"skill": "review", "version": "1", "started": "t", "phases": [], "state": "running"}
        probe = Probe()
        probe._recorder = types.SimpleNamespace(record=lambda run, account=None: record)
        # When: a running status is emitted
        with unittest.mock.patch("chat_service.logger") as log:
            ChatService._emit_status(probe, "task_status", {"id": "r1", "done": False, "paused": False})
        # Then: nothing is logged and the status carries the state of the record
        self.assertEqual(log.error.call_count, 0)
        self.assertEqual(probe.sent[0][1]["state"], "running")


if __name__ == "__main__":
    unittest.main()
