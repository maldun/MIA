"""
Unit test (F-02 of the first Verify run of G-V3.PANEL, REQ-WFM-136): a storage error while the status is enriched with the run record does not reach the
skill through the monitor; the plain status goes out. Run with: python tests/test_emit_status_storage_error.py
"""
import os
import sys
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


if __name__ == "__main__":
    unittest.main()
