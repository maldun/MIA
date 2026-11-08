"""
Acceptance test of the runs of skills without knowledge of the view (N-2.3, G-V3.PANEL): TC-WFM-136 (REQ-WFM-136, with REQ-WFM-130 and 131) against the real ChatService with a
scripted task, the SkillRunRecorder on the fake storage of skill_runs and a fake clock (TR-PANEL-002, TR-PANEL-003). The scripted skill does only what skills do today: it reports
through `monitor.update` and returns its result; it has no entry for the view. Note: specs/mia/goals/G-V3.PANEL/skill-events-today.md (D-309).
Run with: python tests/acceptance/test_skill_run_observer.py
"""

import inspect
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                     # noqa: E402
from chat_log import ChatLog                                 # noqa: E402
from chat_service import ChatService                         # noqa: E402
from moods import MoodTracker                                # noqa: E402
from skill_runs import SkillRunRecorder                      # noqa: E402
from skill_runs_fakes import FakeClock, FakeSkillRunStorage  # noqa: E402
from task_registry import Task, TaskRegistry                 # noqa: E402

VIEW_WORDS = ("Skill run view", "skill_run", "SkillRun", "srv-")       # what no skill and no manifest may name


def scripted(argument, on_delta, on_emotion, should_stop, monitor):
    """a skill as they are today: figures through the monitor, one result text"""
    monitor.update(phase="working", budget={"calls": {"used": 2, "limit": 10}}, counts={"found": 3})
    return "Found 3 works."


MANIFEST = {"id": "scripted", "text": "A scripted skill", "argument": "your question", "example": "/scripted a question", "needs": ["monitor"], "options": [], "version": "1"}


class RunsWithoutKnowledgeOfTheView(unittest.TestCase):
    @mark.req("REQ-WFM-136", "REQ-WFM-130", "REQ-WFM-131")
    def test_a_skill_that_knows_nothing_of_the_view_gets_a_run_record_and_status_events(self):
        """TC-WFM-136: a scripted skill that sends only what skills send today leaves a run record and task_status events, and no file of a skill and no manifest names the view.
        Example: the scripted skill reports found 3 and 2 of 10 calls and returns "Found 3 works."; the record of its run has counts {"found": 3} and state done."""
        # Given: a scripted skill that sends only today's events and has no entry for the view, the real chat service and the recorder on the fake storage
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        events, clock, storage = [], FakeClock(), FakeSkillRunStorage()
        recorder = SkillRunRecorder(storage, lambda event, payload: None, clock=clock.monotonic, now=clock.now)
        tasks = TaskRegistry()
        tasks.register(Task(MANIFEST["id"], scripted, MANIFEST["text"], MANIFEST["argument"], MANIFEST["example"], needs=("monitor",), version=MANIFEST["version"]))
        chat = ChatService(lambda event, payload: events.append((event, payload)), ChatLog(os.path.join(folder, "log.jsonl")), MoodTracker(os.path.join(REPO, "moods.json")),
                           lambda *args: "", queue_size=5, spawn=lambda target: target(), clock=lambda: 100.0, tasks=tasks, recorder=recorder)
        # When: it runs and ends
        chat.send("/scripted canary", sender="anna", author="anna")
        run = [payload["id"] for event, payload in events if event == "chat_done"][0]
        # Then: a run record exists, one for this run
        self.assertEqual(storage.ids("skill_runs"), [run])
        record = recorder.record(run)
        self.assertEqual((record["skill"], record["version"], record["state"], record["phases"]), ("scripted", "1", "done", []))
        # And: the figures the skill reported through the monitor are in it
        self.assertEqual(record["counts"], {"found": 3})
        self.assertEqual(record["budget"]["calls"], {"used": 2, "limit": 10})
        # And: task_status events are sent for the run, the last one with done true
        statuses = [payload for event, payload in events if event == "task_status"]
        self.assertTrue(statuses and all(status["id"] == run for status in statuses))
        self.assertTrue(statuses[-1]["done"])
        # And: no file of the skill and no manifest names the view (inspection)
        sources = [inspect.getsource(scripted), json.dumps(MANIFEST)]
        for name in sorted(os.listdir(os.path.join(REPO, "extensions"))):
            for dirpath, _, files in os.walk(os.path.join(REPO, "extensions", name)):
                sources += [open(os.path.join(dirpath, f), encoding="utf-8").read() for f in files if f.endswith((".py", ".json"))]
        self.assertEqual([word for word in VIEW_WORDS if any(word in source for source in sources)], [])


if __name__ == "__main__":
    unittest.main()
