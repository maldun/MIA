"""
TC-WFM-041 (REQ-WFM-041) at the extension loader: a skill with a record is registered under the record's command and its task carries the record's workflow graph ID;
a skill without a record is registered as before; a record-only skill is not made runnable; web_app.py builds the catalog over the Storage and passes it.
The record store is the real Storage layer (file backend in a temp folder).
Run: python tests/test_skill_catalog_loader.py
"""
import ast
import json
import os
import shutil
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from extension_loader import load_extensions                  # noqa: E402
from skill_record import SkillCatalog, SkillRecords           # noqa: E402
from storage import Storage                                   # noqa: E402
from storage_files import FileBackend                         # noqa: E402
from task_registry import Task, TaskRegistry                  # noqa: E402
from markers import mark                                      # noqa: E402

ENTRY = "def make(services):\n    return lambda argument, on_delta, on_emotion, should_stop, **kw: services.prefix + argument\n"


class SkillCatalogLoader(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="catalog-loader-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.package = "exts_%d" % abs(hash(self.root))
        self.folder = os.path.join(self.root, self.package)
        os.makedirs(self.folder)
        open(os.path.join(self.folder, "__init__.py"), "w").close()
        sys.path.insert(0, self.root)
        self.addCleanup(lambda: sys.path.remove(self.root))
        self.records = SkillRecords(Storage(FileBackend(os.path.join(self.root, "db"))), "anna")
        self.catalog = SkillCatalog(self.records)
        self.registry = TaskRegistry()
        self.services = types.SimpleNamespace(prefix="got: ")

    def add(self, name):
        folder = os.path.join(self.folder, name)
        os.makedirs(folder)
        open(os.path.join(folder, "__init__.py"), "w").close()
        doc = {"id": name, "text": "Do " + name, "argument": "your question", "example": "/%s x" % name, "entry": "entry:make"}
        with open(os.path.join(folder, "manifest.json"), "w", encoding="utf-8") as handle:
            json.dump(doc, handle)
        with open(os.path.join(folder, "entry.py"), "w", encoding="utf-8") as handle:
            handle.write(ENTRY)

    def record(self, skill_id, command, graph):
        stored = self.records.store({"id": skill_id, "command": command, "workflow_graph_id": graph, "context_graph_id": "ctx-" + skill_id})
        self.assertTrue(stored.stored)

    def load(self, **kw):
        return load_extensions(self.package, self.folder, self.registry, self.services, **kw)

    @mark.req("REQ-WFM-041")
    def test_a_skill_with_a_record_is_registered_under_the_commands_of_the_record_with_its_graph(self):
        """TC-WFM-041: the record's command is registered and listed, the task carries the record's workflow graph ID, and it still runs.

        Example: manifest `alpha`, record command `/alpha2` with graph `wf-alpha`: the task id is `alpha2`, workflow_graph_id `wf-alpha`, `/alpha2 hi` runs to "got: hi".
        """
        # Given: an extension folder `alpha` and a record of `alpha` with another command
        self.add("alpha")
        self.record("alpha", "/alpha2", "wf-alpha")
        # When: the extensions are loaded with the catalog
        problems = self.load(catalog=self.catalog)
        # Then: the task is under the record's command, carries the graph ID, and is the same runner
        self.assertEqual(problems, [])
        self.assertEqual(self.registry.ids(), ["alpha2"])
        task = self.registry.get("alpha2")
        self.assertEqual(task.workflow_graph_id, "wf-alpha")
        self.assertEqual(task.run("hi", None, None, None), "got: hi")
        self.assertEqual(self.registry.parse("/alpha2 hi")["task"], "alpha2")
        self.assertIsNone(self.registry.parse("/alpha hi"))
        self.assertEqual([c["command"] for c in self.registry.commands()], ["/alpha2 "])

    @mark.req("REQ-WFM-041")
    def test_a_skill_without_a_record_is_registered_as_before(self):
        """TC-WFM-041: a skill without a record keeps its manifest command and has no graph ID, with a catalog or without.

        Example: manifest `beta`, records only for `alpha`: `beta` stays `beta` with workflow_graph_id None; without a catalog the same.
        """
        # Given: two extension folders and a record for one of them
        self.add("alpha")
        self.add("beta")
        self.record("alpha", "/alpha2", "wf-alpha")
        # When: loaded with the catalog, and (second registry) without
        self.load(catalog=self.catalog)
        plain = TaskRegistry()
        load_extensions(self.package, self.folder, plain, self.services)
        # Then: beta is unchanged in both; without a catalog even alpha is the manifest's
        self.assertEqual(self.registry.ids(), ["alpha2", "beta"])
        self.assertIsNone(self.registry.get("beta").workflow_graph_id)
        self.assertEqual(plain.ids(), ["alpha", "beta"])
        self.assertIsNone(plain.get("alpha").workflow_graph_id)

    @mark.req("REQ-WFM-041")
    def test_a_task_has_no_workflow_graph_id_unless_given(self):
        """TC-WFM-041: Task has the attribute workflow_graph_id, default None.

        Example: Task("x", run, "t", "a", "e") has workflow_graph_id None; with the argument "wf-x" it is "wf-x".
        """
        # Given/When: a task without and a task with the graph ID
        plain = Task("x", None, "t", "a", "e")
        with_graph = Task("x", None, "t", "a", "e", workflow_graph_id="wf-x")
        # Then: default None, given value kept
        self.assertIsNone(plain.workflow_graph_id)
        self.assertEqual(with_graph.workflow_graph_id, "wf-x")

    @mark.req("REQ-WFM-041")
    def test_a_record_only_skill_is_not_made_runnable(self):
        """TC-WFM-041: a record without a manifest folder is not invented as a task (A-107: listed, not runnable); no problem is reported.

        Example: record `gamma` with `/gamma` and no folder: no task `gamma`, `/gamma x` is no task command, the problems stay empty.
        """
        # Given: a record without any extension folder, and one extension with a record
        self.add("alpha")
        self.record("alpha", "/alpha", "wf-alpha")
        self.record("gamma", "/gamma", "wf-gamma")
        # When: the extensions are loaded with the catalog
        problems = self.load(catalog=self.catalog)
        # Then: only alpha is a task; gamma is still listed by the catalog
        self.assertEqual(problems, [])
        self.assertEqual(self.registry.ids(), ["alpha"])
        self.assertIsNone(self.registry.parse("/gamma x"))
        self.assertIn(("gamma", "/gamma"), [(s["id"], s["command"]) for s in self.catalog.list()])

    @mark.req("REQ-WFM-041")
    def test_web_app_creates_the_catalog_over_the_storage_and_passes_it_to_the_loader(self):
        """TC-WFM-041: web_app.py (not importable without the server) builds SkillCatalog(SkillRecords(<Storage>)) and passes catalog= to load_extensions.

        Example: the source has a SkillCatalog call over SkillRecords over `_votes_store`, defined before the load_extensions call that has a `catalog` keyword.
        """
        # Given: the parsed source of web_app.py
        with open(os.path.join(ROOT, "web_app.py"), encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        # When: the calls of interest are looked up
        catalogs = [c for c in calls if c.func.id == "SkillCatalog"]
        loads = [c for c in calls if c.func.id == "load_extensions"]
        # Then: one catalog over SkillRecords over the Storage, created before the load, which gets it as `catalog`
        self.assertEqual((len(catalogs), len(loads)), (1, 1))
        inner = catalogs[0].args[0]
        self.assertEqual(inner.func.id, "SkillRecords")
        self.assertEqual(inner.args[0].id, "_votes_store")
        keyword = {k.arg: k.value for k in loads[0].keywords}
        self.assertIn("catalog", keyword)
        self.assertLess(catalogs[0].lineno, loads[0].lineno)


if __name__ == "__main__":
    unittest.main()
