"""
TC-WFM-035 (REQ-WFM-035): the class of a model (local or paid) is kept in a file, asked once for a new model that is not clearly local, and changed only by set().
Run: python tests/test_model_class.py
"""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from model_class import ModelClasses  # noqa: E402


class ModelClassTest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "model_classes.json")
        self.classes = ModelClasses(self.path)

    def test_a_new_model_on_a_remote_host_is_asked_once(self):
        self.assertTrue(self.classes.needs_question("big-model", host="api.example.com"))
        self.assertIsNone(self.classes.class_of("big-model", host="api.example.com"))
        self.classes.set("big-model", "paid")
        self.assertFalse(self.classes.needs_question("big-model", host="api.example.com"))
        self.assertEqual(self.classes.class_of("big-model"), "paid")

    def test_a_model_on_this_machine_is_local_and_not_asked(self):
        self.assertFalse(self.classes.needs_question("gemma4:12b", host="localhost"))
        self.assertEqual(self.classes.class_of("gemma4:12b", host="127.0.0.1"), "local")

    def test_the_class_survives_a_restart_and_is_changed_by_set(self):
        self.classes.set("big-model", "paid")
        again = ModelClasses(self.path)
        self.assertEqual(again.class_of("big-model"), "paid")
        again.set("big-model", "local")
        self.assertEqual(ModelClasses(self.path).class_of("big-model"), "local")

    def test_only_local_or_paid_are_accepted(self):
        with self.assertRaises(ValueError):
            self.classes.set("big-model", "free")
        self.assertTrue(self.classes.needs_question("big-model", host="api.example.com"))


if __name__ == '__main__':
    unittest.main()
