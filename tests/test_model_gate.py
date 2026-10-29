"""
TC-WFM-035 (REQ-WFM-035): the gate before a task asks once whether a new model is paid, warns for a paid model and makes the slices its default; /model paid|local <name> changes the class.
Run: python tests/test_model_gate.py
"""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from model_class import ModelClasses  # noqa: E402
from model_gate import make_model_command, make_prepare  # noqa: E402


class Opt:
    def __init__(self, name):
        self.name = name


class FakeTask:
    def __init__(self, *option_names):
        self.options = tuple(Opt(n) for n in option_names)


class ModelGateTest(unittest.TestCase):
    def setUp(self):
        self.classes = ModelClasses(os.path.join(tempfile.mkdtemp(), "model_classes.json"))
        self.notes, self.questions, self.replies = [], [], []
        self.host = "api.example.com"
        self.prepare = make_prepare(self.classes, lambda: "big-model", lambda: self.host, self.notes.append)

    def ask(self, text):
        self.questions.append(text)
        return self.replies.pop(0) if self.replies else None

    def test_a_paid_answer_is_stored_warned_about_and_makes_slice_the_default(self):
        self.replies.append("yes")
        options = self.prepare(FakeTask("slice"), {"slice": False}, self.ask)
        self.assertEqual(options, {"slice": True})
        self.assertEqual(len(self.questions), 1)
        self.assertIn("big-model", self.questions[0])
        self.assertEqual(self.classes.class_of("big-model"), "paid")
        self.assertEqual(len(self.notes), 1)
        self.assertIn("paid", self.notes[0])

    def test_a_known_model_is_never_asked_again(self):
        self.classes.set("big-model", "paid")
        options = self.prepare(FakeTask("slice"), {"slice": False}, self.ask)
        self.assertEqual(options, {"slice": True})
        self.assertEqual(self.questions, [])
        self.assertEqual(len(self.notes), 1)

    def test_a_local_answer_changes_nothing(self):
        self.replies.append("no")
        options = self.prepare(FakeTask("slice"), {"slice": False}, self.ask)
        self.assertEqual(options, {"slice": False})
        self.assertEqual(self.classes.class_of("big-model"), "local")
        self.assertEqual(self.notes, [])

    def test_no_answer_is_not_stored_and_counts_as_paid_for_this_run(self):
        options = self.prepare(FakeTask("slice"), {"slice": False}, self.ask)
        self.assertEqual(options, {"slice": True})
        self.assertTrue(self.classes.needs_question("big-model", host=self.host))

    def test_a_model_on_this_machine_is_not_asked(self):
        self.host = "localhost"
        options = self.prepare(FakeTask("slice"), {"slice": False}, self.ask)
        self.assertEqual((options, self.questions, self.notes), ({"slice": False}, [], []))

    def test_a_task_without_the_option_slice_keeps_its_options(self):
        self.classes.set("big-model", "paid")
        options = self.prepare(FakeTask(), {}, self.ask)
        self.assertEqual(options, {})
        self.assertEqual(len(self.notes), 1)

    def test_the_command_model_changes_the_class_and_explains_wrong_use(self):
        command = make_model_command(self.classes, lambda: "big-model", lambda: self.host)
        self.assertIn("paid", command("paid big-model"))
        self.assertEqual(self.classes.class_of("big-model"), "paid")
        self.assertIn("local", command("local big-model"))
        self.assertEqual(self.classes.class_of("big-model"), "local")
        with self.assertRaises(ValueError) as caught:
            command("free big-model")
        self.assertIn("/model paid", str(caught.exception))
        self.assertIn("big-model", command(""))

if __name__ == '__main__':
    unittest.main()
