"""
Self-test of the helper tests/helpers/call_recording.py (T-CV-01, TR-CONVERT-006): one old run (skill plan_question, research with two tools) is recorded once, saved,
loaded and replayed twice with the same list of calls (prompt, options, order). GREEN from the start: the helper is finished here, the product code is not involved.
Run with: python tests/acceptance/test_call_recording.py
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from call_recording import Recording, RecordingModel, RecordingTool, Replay, ReplayExhausted, ScriptedModel, first_difference, schema_reply   # noqa: E402
from core import Core                                                           # noqa: E402
from library import Library                                                     # noqa: E402

SKILLS, LIBRARY = os.path.join(REPO, "skills"), os.path.join(REPO, "library")


def run(core, skill, inputs):
    result = core.run(skill, inputs, started_by="command")
    assert result.status == "done", result.error
    return result


class CallRecording(unittest.TestCase):
    def record_research(self, folder):
        rec = Recording()
        tools = {"web_search": RecordingTool("web_search", lambda **kw: [], rec), "fetch_page": RecordingTool("fetch_page", lambda **kw: {"text": ""}, rec)}
        core = Core(SKILLS, Library(LIBRARY), folder, model=RecordingModel(ScriptedModel(), rec), tools=tools)
        run(core, "research", {"question": "When did the Rivertown Bridge open to traffic?"})
        return rec

    def test_one_recorded_run_replays_twice_with_the_same_calls(self):
        with tempfile.TemporaryDirectory() as folder:
            rec = self.record_research(folder)
            path = os.path.join(folder, "research.recording.json")
            rec.save(path)
            loaded = Recording.load(path)
            self.assertEqual(loaded.events, rec.events)
            self.assertEqual(loaded.tool_names, {"web_search", "fetch_page"})
            self.assertGreaterEqual(len(rec.model_calls()), 2)
            lists = []
            for _ in range(2):
                replay = Replay(loaded)
                run(Core(SKILLS, Library(LIBRARY), folder, model=replay.model, tools=replay.tools), "research", {"question": "When did the Rivertown Bridge open to traffic?"})
                self.assertIsNone(first_difference(rec.model_calls(), replay.model_calls()))
                self.assertEqual(replay.tool_calls(), rec.tool_calls())
                lists.append(replay.model_calls())
            self.assertEqual(lists[0], lists[1])

    def test_a_second_old_run_gives_the_same_list_of_calls(self):
        """the recording is only useful if the old run is deterministic"""
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            self.assertIsNone(first_difference(self.record_research(a).model_calls(), self.record_research(b).model_calls()))

    def test_first_difference_names_the_call_and_the_field(self):
        base = [{"messages": [{"role": "user", "content": "q"}], "schema": None, "model": None, "profile": "light", "options": None}] * 2
        changed = [dict(base[0]), dict(base[1], options={"temperature": 0.2})]
        self.assertIsNone(first_difference(base, list(base)))
        self.assertEqual(first_difference(base, changed), {"call": 2, "field": "options", "old": None, "new": {"temperature": 0.2}})
        self.assertEqual(first_difference(base, base[:1])["field"], "missing")

    def test_a_call_beyond_the_recording_raises_and_is_listed(self):
        replay = Replay(Recording([{"kind": "model", "messages": [], "schema": None, "model": None, "profile": None, "options": None, "reply": "x"}]))
        replay.model.chat([{"role": "user", "content": "a"}])
        with self.assertRaises(ReplayExhausted):
            replay.model.chat([{"role": "user", "content": "b"}])
        self.assertEqual(len(replay.model_calls()), 2)

    def test_schema_reply_fits_minlength(self):
        self.assertEqual(schema_reply({"type": "object", "required": ["a"], "properties": {"a": {"type": "string", "minLength": 12}}}), '{"a": "plain text.."}')


if __name__ == "__main__":
    unittest.main()
