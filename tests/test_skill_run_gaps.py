"""
Unit tests for the gaps the mutants of the first Verify run of G-V3.PANEL showed (F-06, REQ-WFM-131, -134, -136, REQ-API-015): the phase filter and the phase
progress through the observer (M11, M12), no reason for a done run in the record and in the status (M04, M21), the paused state in the status (M20),
the 204 on the wire when no run exists (M22) and the order of runs that started in the same second (M02). Run with: python tests/test_skill_run_gaps.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from flask import Flask, g                                   # noqa: E402
from chat_ops_api import create_chat_ops_blueprint           # noqa: E402
from chat_service import ChatService                         # noqa: E402
from skill_run_observer import SkillRunObserver              # noqa: E402
from skill_runs import SkillRunRecorder                      # noqa: E402
from skill_runs_fakes import FakeClock, FakeSkillRunStorage  # noqa: E402


def make():
    clock = FakeClock()
    return SkillRunRecorder(FakeSkillRunStorage(), lambda event, payload: None, clock=clock.monotonic, now=clock.now), clock


def states(recorder, run):
    return [(p["name"], p["state"]) for p in recorder.record(run)["phases"]]


class TestObserverPhases(unittest.TestCase):
    def test_only_declared_phases_are_recorded_and_the_earlier_ones_are_done(self):
        """Example: declared (a, b, c); the skill says "hello" (ignored), "b": a done, b running, c waiting"""
        # Given: a run with three declared phases
        recorder, _ = make()
        observer = SkillRunObserver(recorder, "r1", "review", "1", "carl", phases=("a", "b", "c"))
        observer.start()
        # When: the skill says a text that is no phase name
        observer.phase("hello")
        # Then: no phase changes
        self.assertEqual(states(recorder, "r1"), [("a", "waiting"), ("b", "waiting"), ("c", "waiting")])
        # When: it says a declared name
        observer.phase("b")
        # Then: the earlier phases are done and that one runs
        self.assertEqual(states(recorder, "r1"), [("a", "done"), ("b", "running"), ("c", "waiting")])


    def test_an_undeclared_text_never_reaches_the_recorder(self):
        """Example: declared (a,), the skill says "hello" and "a": the recorder is told "a" only"""
        class Spy:
            def __init__(self):
                self.phases = []

            def phase(self, run, name):
                self.phases.append(name)
        # Given: an observer with one declared phase over a recorder that only notes what it is told
        spy = Spy()
        observer = SkillRunObserver(spy, "r1", "review", "1", "carl", phases=("a",))
        # When: the skill says "hello" and then "a"
        observer.phase("hello")
        observer.phase("a")
        # Then: the recorder heard "a" only
        self.assertEqual(spy.phases, ["a"])


class TestReasonOfDoneRun(unittest.TestCase):
    def test_a_done_run_keeps_no_reason_a_failed_one_does(self):
        """Example: end(done, reason="x") has no reason in the record; end(failed, reason="x") has"""
        # Given: two runs
        recorder, _ = make()
        # When: one ends done and one ends failed, both with a reason
        for run, state in (("ok", "done"), ("bad", "failed")):
            recorder.start(run, "review", "1", "carl", phases=("a",))
            recorder.end(run, state, reason="x")
        # Then: only the failed one keeps the reason
        self.assertNotIn("reason", recorder.record("ok"))
        self.assertEqual(recorder.record("bad")["reason"], "x")


class FakeRecorder:
    def __init__(self, state, reason):
        self._record = {"skill": "review", "version": "1", "started": "t", "phases": [], "state": state, "reason": reason}

    def record(self, run, account=None):
        return self._record


class Probe:
    def __init__(self, state, reason):
        self._recorder, self.sent = FakeRecorder(state, reason), []

    def _emit(self, event, payload):
        self.sent.append(payload)


class TestStatusWire(unittest.TestCase):
    def status(self, record_state, reason, **flags):
        probe = Probe(record_state, reason)
        ChatService._emit_status(probe, "task_status", dict({"id": "r1", "done": False, "paused": False}, **flags))
        return probe.sent[0]

    def test_a_paused_run_says_paused(self):
        """Example: not done, paused: the state is paused"""
        self.assertEqual(self.status("running", None, paused=True)["state"], "paused")

    def test_the_reason_goes_out_for_failed_and_stopped_only(self):
        """Example: done with a stored reason sends none; failed and stopped send it"""
        self.assertNotIn("reason", self.status("done", "x", done=True))
        self.assertEqual(self.status("failed", "x", done=True)["reason"], "x")
        self.assertEqual(self.status("stopped", "x", done=True)["reason"], "x")


class TestShownRoute(unittest.TestCase):
    def test_no_run_yet_is_204_without_a_body(self):
        """Example: GET /api/skill-runs/shown before any run answers 204 and an empty body"""
        # Given: a backend that has no run yet
        class Chat:
            def shown_run(self, account):
                return None
        app = Flask(__name__)

        @app.before_request
        def who():
            g.account = "anna"
        app.register_blueprint(create_chat_ops_blueprint(Chat()))
        # When: the view asks for the run that is shown
        got = app.test_client().get("/api/skill-runs/shown")
        # Then: 204 and no body
        self.assertEqual((got.status_code, got.data), (204, b""))


class TestShownTie(unittest.TestCase):
    def test_runs_started_in_the_same_second_the_larger_id_is_shown(self):
        """Example: r1 and r2 started at the same time and running: r2; both ended at the same time: r2"""
        # Given: two runs of one account that started at the same time
        recorder, _ = make()
        for run in ("r2", "r1"):
            recorder.start(run, "review", "1", "carl")
        # When: both run, and then both end at the same time
        # Then: the larger id is shown in both cases
        self.assertEqual(recorder.shown("carl"), "r2")
        for run in ("r1", "r2"):
            recorder.end(run, "done")
        self.assertEqual(recorder.shown("carl"), "r2")


if __name__ == "__main__":
    unittest.main()
