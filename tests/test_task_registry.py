"""
TC-WFM-029 (REQ-WFM-029) and TC-WFM-030 (REQ-WFM-030): the id of a skill is its command, a second skill with the same id is refused, the commands are built from the registry, and the options
of a skill are declared by the skill and parsed by the registry: `/<id> options <name>[=<value>] ... -- <argument>`, `/<id> options` lists them.
Run: python tests/test_task_registry.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from task_registry import Option, Task, TaskCommandError, TaskRegistry  # noqa: E402


def noop(*args):
    return None


def make():
    registry = TaskRegistry()
    registry.register(Task("lookup", noop, "Look something up on the web and answer with sources", "your question", "/lookup how tall is the Eiffel Tower", aliases=("research",)))
    registry.register(Task("review", noop, "Literature review with sources", "your question", "/review do canary releases help? until 2024-06-30",
                           options=(Option("slice", "flag", False, "work in time slices and ask at each limit"), Option("cap_factor", "int", 10, "hard caps = limits times this"))))
    return registry


def error_of(call):
    try:
        call()
    except TaskCommandError as err:
        return str(err)
    raise AssertionError("no TaskCommandError raised")


class TaskRegistryTest(unittest.TestCase):
    def setUp(self):
        self.registry = make()

    def test_a_second_skill_with_the_same_id_is_refused_with_the_id_named(self):          # TC-WFM-029
        message = error_of_value(lambda: self.registry.register(Task("review", noop, "again", "q", "/review q")))
        self.assertIn("review", message)
        self.assertEqual(self.registry.ids(), ["lookup", "review"])

    def test_the_commands_are_built_from_the_registry(self):                              # TC-WFM-029
        commands = self.registry.commands()
        self.assertEqual([c["command"] for c in commands], ["/lookup ", "/review "])
        self.assertIn("Literature review", commands[1]["description"])
        self.registry.register(Task("verify", noop, "Check a claim", "the claim", "/verify the earth is flat"))
        self.assertEqual([c["command"] for c in self.registry.commands()][-1], "/verify ")

    def test_a_plain_command_gives_the_argument_and_the_default_options(self):            # TC-WFM-030
        found = self.registry.parse("/review do canary releases help? until 2024-06-30")
        self.assertEqual((found["task"], found["argument"], found["options"]), ("review", "do canary releases help? until 2024-06-30", {"slice": False, "cap_factor": 10}))
        self.assertEqual(self.registry.parse("/Research how tall?")["task"], "lookup")       # the old name is an alias
        self.assertIsNone(self.registry.parse("hello"))
        self.assertIsNone(self.registry.parse("/reviews are nice"))

    def test_options_are_set_before_the_separator(self):                                  # TC-WFM-030
        found = self.registry.parse("/review options slice cap_factor=5 -- the question -- with a dash")
        self.assertEqual((found["argument"], found["options"]), ("the question -- with a dash", {"slice": True, "cap_factor": 5}))

    def test_options_alone_lists_the_options_with_their_defaults(self):                   # TC-WFM-030
        found = self.registry.parse("/review options")
        self.assertTrue(found["help"])
        self.assertIn("slice", found["text"])
        self.assertIn("cap_factor", found["text"])
        self.assertIn("10", found["text"])

    def test_an_unknown_option_or_a_wrong_value_is_refused_with_the_options_named(self):  # TC-WFM-030
        message = error_of(lambda: self.registry.parse("/review options fast -- q"))
        self.assertIn("fast", message)
        self.assertIn("slice", message)
        self.assertIn("cap_factor", error_of(lambda: self.registry.parse("/review options cap_factor=abc -- q")))
        self.assertIn("--", error_of(lambda: self.registry.parse("/review options slice")))
        self.assertIn("no options", error_of(lambda: self.registry.parse("/lookup options slice -- q")))

    def test_a_configured_default_applies_and_the_call_overrides_it(self):                # TC-WFM-030
        defaults = {"review": {"slice": True}}
        self.assertTrue(self.registry.parse("/review q", defaults)["options"]["slice"])
        self.assertFalse(self.registry.parse("/review options slice=false -- q", defaults)["options"]["slice"])

    def test_a_bare_command_is_explained_with_the_example(self):
        self.assertIn("/lookup how tall is the Eiffel Tower", error_of(lambda: self.registry.parse("/lookup")))


def error_of_value(call):
    try:
        call()
    except ValueError as err:
        return str(err)
    raise AssertionError("no ValueError raised")


if __name__ == "__main__":
    unittest.main()
