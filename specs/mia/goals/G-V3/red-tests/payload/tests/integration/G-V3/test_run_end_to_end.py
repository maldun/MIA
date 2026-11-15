"""
Integration check of a skill run in the backend (G-V3, AC-39 backend part): TC-CHA-068 (FR-34, FR-35, FR-46; REQ-BE-078, REQ-WFM-130, 136, REQ-CHA-041, 042, 043, 046, 058) with the real
ChatService, the real SkillRunRecorder and SkillRunObserver, the SkillDigestStep on the fake model of TR-CHAT-006 and the fake storage of TR-PANEL-003 (TR-CHAT-009): no model server, no browser.
Run with: python tests/integration/G-V3/test_run_end_to_end.py
"""

import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from markers import mark                                     # noqa: E402
from chat_log import ChatLog                                 # noqa: E402
from chat_service import ChatService                         # noqa: E402
from fake_model import FakeModel                             # noqa: E402
from moods import MoodTracker                                # noqa: E402
from skill_digest import SkillDigestStep                     # noqa: E402
from skill_runs import SkillRunRecorder                      # noqa: E402
from skill_runs_fakes import FakeClock, FakeSkillRunStorage  # noqa: E402
from task_registry import Task, TaskRegistry                 # noqa: E402

PHASES = ("collect", "rank", "report")
RESULT = ("Works screened: 130.\n| work | decision |\n|---|---|\n" + "\n".join("| Work %d | include |" % n for n in range(1, 40))
          + "\n" + "".join("Finding %03d: the works agree on lower cost. " % n for n in range(1, 131)))


def scripted(argument, on_delta, on_emotion, should_stop, monitor):
    """a skill as they are today: its phases and figures through the monitor, one long result"""
    for phase in PHASES + ("cleanup",):                       # the fourth phase is not declared
        monitor.update(phase=phase, counts={"found": 130})
    return RESULT


class RunEndToEnd(unittest.TestCase):
    @mark.req("REQ-BE-078", "REQ-WFM-130", "REQ-WFM-136", "REQ-CHA-041", "REQ-CHA-042", "REQ-CHA-043", "REQ-CHA-046", "REQ-CHA-058")
    def test_the_chat_holds_the_status_messages_and_one_summary_and_the_record_the_full_result(self):
        """TC-CHA-068: the chat holds one status message per declared phase and one summary with the link of the run and nothing else of the run; the run record holds the full result; the history for the chat model ends with the last status and the summary.
        Example: phases collect, rank, report give "Collecting.", "Ranking.", "Writing it up.", then "Found 130 findings." and the link; the table is not in the chat."""
        # Given: the chat service with the recorder, the digest step on the fake model and a recording speech route; a scripted task with three declared phases and a long result
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        clock, storage, spoken = FakeClock(), FakeSkillRunStorage(), []
        recorder = SkillRunRecorder(storage, lambda event, payload: None, clock=clock.monotonic, now=clock.now)
        model = FakeModel({"collect": "Collecting.", "rank": "Ranking.", "report": "Writing it up.", "Finding": "Found 130 findings."})
        tasks = TaskRegistry()
        tasks.register(Task("scripted", scripted, "A scripted skill", "your question", "/scripted a question", needs=("monitor",), version="1"))
        events = []
        chat = ChatService(lambda event, payload: events.append((event, payload)), ChatLog(os.path.join(folder, "log.jsonl")), MoodTracker(os.path.join(REPO, "moods.json")),
                           lambda *args: "", queue_size=5, spawn=lambda target: target(), clock=lambda: 100.0, tasks=tasks, recorder=recorder,
                           digest=SkillDigestStep(model), declared_phases=lambda run: PHASES, speak=lambda sentence, should_stop: spoken.append(sentence))
        # When: the user starts the task and it ends
        chat.send("/scripted canary", sender="anna", author="anna")
        records = chat.log.history(limit=200)[0]
        runs = [r["skill_run"] for r in records if r.get("skill_run")]
        self.assertTrue(runs, "no message of the chat carries the marker skill_run of a run")
        run = runs[0]
        link = " [Open in the Skill run view](#run=%s)" % run
        # Then: the chat holds exactly four messages of MIA: a status message per declared phase in order, then the summary that ends with the link of the run
        mia = [r["text"] for r in records if r["role"] == "assistant"]
        self.assertEqual(mia, ["Collecting.", "Ranking.", "Writing it up.", "Found 130 findings." + link])
        # And: no message holds the table or the full result, and every message was sent to speech once
        self.assertTrue(all("|---|" not in r["text"] and RESULT not in r["text"] for r in records))
        for text in ("Collecting.", "Ranking.", "Writing it up.", "Found 130 findings."):
            self.assertEqual(sum(1 for sentence in spoken if text in sentence), 1, text)
        # And: the run record holds the full result, the state done and the figures
        record = recorder.record(run)
        self.assertEqual((record["result"], record["state"], record["counts"]), (RESULT, "done", {"found": 130}))
        # And: the history for the chat model ends with the third status message and the summary
        self.assertEqual([m["text"] for m in chat.model_history()][-2:], ["Writing it up.", "Found 130 findings." + link])


if __name__ == "__main__":
    unittest.main()
