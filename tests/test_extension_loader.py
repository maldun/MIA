"""
TC-WFM-039 (REQ-WFM-039): a skill is a folder with a manifest and an entry; the loader registers it in the task registry without a change of the core; a broken or doubled
extension is skipped and named, the others still load; id = folder = command.
Run: python tests/test_extension_loader.py
"""
import json
import os
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from extension_loader import load_extensions, read_manifest, task_from_manifest  # noqa: E402
from task_registry import TaskRegistry  # noqa: E402

ENTRY = "def make(services):\n    return lambda argument, on_delta, on_emotion, should_stop, **kw: services.prefix + argument\n"


def manifest(**changes):
    base = {"id": "alpha", "text": "Do alpha", "argument": "your question", "example": "/alpha something", "entry": "entry:make"}
    base.update(changes)
    return base


class ExtensionLoader(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.package = "exts_%d" % abs(hash(self.root))
        self.folder = os.path.join(self.root, self.package)
        os.makedirs(self.folder)
        open(os.path.join(self.folder, "__init__.py"), "w").close()
        sys.path.insert(0, self.root)
        self.addCleanup(lambda: sys.path.remove(self.root))
        self.registry = TaskRegistry()
        self.services = types.SimpleNamespace(prefix="got: ")

    def add(self, name, doc=None, entry=ENTRY, raw=None):
        folder = os.path.join(self.folder, name)
        os.makedirs(folder)
        open(os.path.join(folder, "__init__.py"), "w").close()
        if doc is not None or raw is not None:
            with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as handle:
                handle.write(raw if raw is not None else json.dumps(doc))
        if entry is not None:
            with open(os.path.join(folder, "entry.py"), "w", encoding="utf-8") as handle:
                handle.write(entry)

    def load(self):
        return load_extensions(self.package, self.folder, self.registry, self.services)

    def test_a_folder_with_a_manifest_and_an_entry_becomes_a_task_that_runs_with_the_services(self):
        self.add("alpha", manifest(aliases=["a"], needs=["ask", "options"], version="3",
                                   options=[{"name": "slice", "kind": "flag", "default": False, "text": "slices"}, {"name": "cap_factor", "kind": "int", "default": 10, "text": "caps"}]))
        self.assertEqual(self.load(), [])
        task = self.registry.get("alpha")
        self.assertEqual((task.id, task.text, task.argument, task.example, task.aliases, task.needs, task.version), ("alpha", "Do alpha", "your question", "/alpha something", ("a",), ("ask", "options"), "3"))
        self.assertEqual([(o.name, o.kind, o.default) for o in task.options], [("slice", "flag", False), ("cap_factor", "int", 10)])
        self.assertEqual(task.run("question", None, None, None), "got: question")
        self.assertEqual(self.registry.parse("/a options slice -- q")["task"], "alpha")

    def test_the_tasks_are_registered_in_the_order_of_their_ids(self):
        self.add("beta", manifest(id="beta", example="/beta x"))
        self.add("alpha", manifest())
        self.load()
        self.assertEqual(self.registry.ids(), ["alpha", "beta"])

    def test_a_broken_extension_is_skipped_and_named_and_the_others_load(self):
        self.add("alpha", manifest())
        self.add("nomanifest", None)
        self.add("badjson", raw="{ not json")
        self.add("noid", {"text": "x", "argument": "q", "example": "/noid", "entry": "entry:make"})
        self.add("badkind", manifest(id="badkind", options=[{"name": "x", "kind": "blob", "default": 1, "text": "t"}]))
        self.add("noentry", manifest(id="noentry", entry="entry:make"), entry="x = 1\n")
        self.add("raises", manifest(id="raises"), entry="def make(services):\n    raise RuntimeError('no luck')\n")
        problems = self.load()
        self.assertEqual(self.registry.ids(), ["alpha"])
        for name in ("badjson", "noid", "badkind", "noentry", "raises"):
            self.assertTrue(any(name in p for p in problems), name)
        self.assertFalse(any("nomanifest" in p for p in problems))              # a folder without a manifest is no extension (for example __pycache__)
        self.assertTrue(any("no luck" in p for p in problems))

    def test_the_id_is_the_folder_name_and_a_doubled_id_is_refused(self):
        self.add("alpha", manifest())
        self.add("gamma", manifest(id="alpha"))
        problems = self.load()
        self.assertEqual(self.registry.ids(), ["alpha"])
        self.assertTrue(any("gamma" in p and "alpha" in p for p in problems))

    def test_read_manifest_checks_what_a_task_needs(self):
        folder = os.path.join(self.folder, "alpha")
        self.add("alpha", manifest(needs=["ask", "teleport"]))
        with self.assertRaises(ValueError) as caught:
            read_manifest(folder)
        self.assertIn("teleport", str(caught.exception))

    def test_a_task_can_be_made_from_a_manifest_with_a_run_function_given_from_outside(self):          # for the tests of the core
        task = task_from_manifest(manifest(needs=["monitor"]), lambda *a: "x")
        self.assertEqual((task.id, task.needs, task.run()), ("alpha", ("monitor",), "x"))


if __name__ == "__main__":
    unittest.main()
