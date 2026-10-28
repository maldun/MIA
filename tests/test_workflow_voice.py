"""The voice of the workflows (owner 2026-10-29): one general switch for every task that speaks (/lookup, /review and the ones to come), and an optional switch per task over it.
Run with: python tests/test_workflow_voice.py"""
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from workflow_voice import speaker_for


def speak(text):
    return text


class TestSpeakerFor(unittest.TestCase):
    def test_the_voice_is_on_by_default_for_every_task(self):
        self.assertIs(speaker_for({}, "lookup", speak), speak)
        self.assertIs(speaker_for({}, "review", speak), speak)
        self.assertIs(speaker_for({}, "a_task_that_does_not_exist_yet", speak), speak)

    def test_the_general_switch_turns_every_task_off(self):
        cfg = {"workflow_speak": False}
        for task in ("lookup", "review", "next"):
            self.assertIsNone(speaker_for(cfg, task, speak))

    def test_a_switch_per_task_wins_over_the_general_one(self):
        self.assertIsNone(speaker_for({"workflow_speak_tasks": {"review": False}}, "review", speak))
        self.assertIs(speaker_for({"workflow_speak_tasks": {"review": False}}, "lookup", speak), speak)
        self.assertIs(speaker_for({"workflow_speak": False, "workflow_speak_tasks": {"lookup": True}}, "lookup", speak), speak)
        self.assertIsNone(speaker_for({"workflow_speak": False, "workflow_speak_tasks": {"lookup": True}}, "review", speak))

    def test_a_value_that_is_not_a_boolean_is_ignored(self):
        self.assertIs(speaker_for({"workflow_speak_tasks": {"review": "no"}}, "review", speak), speak)
        self.assertIs(speaker_for({"workflow_speak_tasks": None}, "review", speak), speak)
        self.assertIs(speaker_for({"workflow_speak": "off"}, "review", speak), speak)

    def test_without_a_voice_there_is_none(self):
        self.assertIsNone(speaker_for({}, "review", None))


if __name__ == "__main__":
    unittest.main()
