"""
TC-WFM-041 (REQ-WFM-041) at the extension loader: a skill with a record is registered under the record's command and its task carries the record's workflow graph ID;
a skill without a record is registered as before; a record-only skill is not made runnable; web_app.py builds the catalog over the Storage and passes it.
The record store is the real Storage layer (file backend in a temp folder).
Run: python tests/test_skill_catalog_loader.py
"""
import ast
import json
import os
import random
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
from skill_record import SkillCatalog, SkillRecords, command_problem           # noqa: E402
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

    def reset(self):
        """a fresh folder of skills, fresh records and a fresh registry inside one test (for subTests)"""
        for name in os.listdir(self.folder):
            if os.path.isdir(os.path.join(self.folder, name)):
                shutil.rmtree(os.path.join(self.folder, name))
        shutil.rmtree(os.path.join(self.root, "db"), True)
        self.records = SkillRecords(Storage(FileBackend(os.path.join(self.root, "db"))), "anna")
        self.catalog = SkillCatalog(self.records)
        self.registry = TaskRegistry()

    def add(self, name, aliases=()):
        folder = os.path.join(self.folder, name)
        os.makedirs(folder)
        open(os.path.join(folder, "__init__.py"), "w").close()
        doc = {"id": name, "text": "Do " + name, "argument": "your question", "example": "/%s x" % name, "entry": "entry:make", "aliases": list(aliases)}
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
    def test_a_stored_bad_command_is_skipped_with_a_problem_and_never_raises(self):
        """F-03 (REQ-WFM-041): a record whose command cannot be registered (written around the record store) skips that skill and adds a problem; the others stay.

        Example: records `alpha` with "/" and `delta` with "/Delta" (stored raw), manifest-only `beta`: `beta` is a task, `alpha` and `delta` are not, two problems name them, `/lookup`-style parse does not raise.
        """
        # Given: three extension folders; two have records that the record store would refuse, put into the Storage directly
        for name in ("alpha", "beta", "delta"):
            self.add(name)
        for skill_id, command in (("alpha", "/"), ("delta", "/Delta")):
            self.records.tables.put("skills", skill_id, {"id": skill_id, "data": {"command": command, "workflow_graph_id": "wf-" + skill_id,
                                                                                  "context_graph_id": "ctx-" + skill_id}}, "anna")
        # When: the extensions are loaded with the catalog
        problems = self.load(catalog=self.catalog)
        # Then: only the manifest-only skill is registered, no empty ID, and the two skills are named in the problems
        self.assertEqual(self.registry.ids(), ["beta"])
        self.assertEqual(sorted(p.split(":")[0] for p in problems), ["alpha", "delta"])
        self.assertIsNone(self.registry.parse("/ text"))
        self.assertEqual(self.registry.parse("/delta x"), None)

    @mark.req("REQ-WFM-042")
    def test_a_record_command_that_is_a_manifest_only_skill_is_refused_by_the_loader(self):
        """F-02 (REQ-WFM-042): the record store cannot know manifest-only skills, so the loader refuses the record command with a problem; both skills keep their own form.

        Example: record `alpha` with `/beta` and manifest-only `beta`: `alpha` is skipped with a problem, `beta` is registered and answers `/beta x`.
        """
        # Given: alpha with a record whose command is the id of the manifest-only skill beta
        self.add("alpha")
        self.add("beta")
        self.record("alpha", "/beta", "wf-alpha")
        # When: the extensions are loaded with the catalog
        problems = self.load(catalog=self.catalog)
        # Then: beta is registered as itself, alpha is skipped and named in a problem
        self.assertEqual(self.registry.ids(), ["beta"])
        self.assertEqual([p.split(":")[0] for p in problems], ["alpha"])
        self.assertEqual(self.registry.parse("/beta x")["task"], "beta")

    @mark.req("REQ-WFM-041")
    def test_a_catalog_that_fails_does_not_stop_the_loader_and_the_skills_load_as_the_manifest_says(self):
        """F-13 (REQ-WFM-041): a catalog whose `start` raises (storage down) gives one problem per skill, the skills are registered as the manifests say, nothing is raised.

        Example: `alpha` and `beta` with a record for `alpha` (`/alpha2`) and a catalog that raises ConnectionError("storage down"): load returns two problems naming alpha and beta, the tasks are `alpha` and `beta`.
        """
        # Given: two extension folders, a record for one, and a catalog whose lookup fails
        self.add("alpha")
        self.add("beta")
        self.record("alpha", "/alpha2", "wf-alpha")

        class Down(SkillCatalog):
            def start(self, skill_id):
                raise ConnectionError("storage down")

        # When: the extensions are loaded
        problems = self.load(catalog=Down(self.records))
        # Then: no exception, both skills are registered as the manifest says, one problem each
        self.assertEqual(self.registry.ids(), ["alpha", "beta"])
        self.assertEqual([self.registry.get(i).workflow_graph_id for i in ("alpha", "beta")], [None, None])
        self.assertEqual(sorted(p.split(":")[0] for p in problems), ["alpha", "beta"])
        self.assertTrue(all("storage down" in p for p in problems))

    @mark.req("REQ-WFM-041")
    def test_a_failing_lookup_of_one_skill_leaves_the_other_skills_with_their_records(self):
        """F-13 (REQ-WFM-041): the lookup of one skill fails, the others are not affected: a skill with a record still takes the command of the record.

        Example: the lookup of `alpha` raises, `beta` has the record `/beta2`: tasks `alpha` (manifest) and `beta2`, one problem naming alpha.
        """
        # Given: two folders with records for both, and a catalog that fails for alpha only
        self.add("alpha")
        self.add("beta")
        self.record("alpha", "/alpha2", "wf-alpha")
        self.record("beta", "/beta2", "wf-beta")

        class Flaky(SkillCatalog):
            def start(self, skill_id):
                if skill_id == "alpha":
                    raise ConnectionError("storage down")
                return super().start(skill_id)

        # When: loaded
        problems = self.load(catalog=Flaky(self.records))
        # Then: alpha is the manifest's, beta is the record's with its graph, one problem for alpha
        self.assertEqual(self.registry.ids(), ["alpha", "beta2"])
        self.assertEqual(self.registry.get("beta2").workflow_graph_id, "wf-beta")
        self.assertEqual([p.split(":")[0] for p in problems], ["alpha"])

    def alias_case(self, record_skill):
        # Given: a skill with a record whose command is an alias of the manifest-only skill lookup (the folder order is by name)
        self.add(record_skill)
        self.add("lookup", aliases=("research",))
        self.record(record_skill, "/research", "wf-" + record_skill)
        # When: loaded with the catalog
        problems = self.load(catalog=self.catalog)
        # Then: lookup keeps its alias, the record skill is skipped and the problem names the command
        self.assertEqual(self.registry.ids(), ["lookup"])
        self.assertEqual(self.registry.parse("/research x")["task"], "lookup")
        self.assertEqual([p.split(":")[0] for p in problems], [record_skill])
        self.assertIn("research", problems[0].lower())

    @mark.req("REQ-WFM-042")
    def test_a_record_command_that_is_an_alias_of_a_manifest_skill_is_refused_when_the_record_skill_sorts_first(self):
        """F-14 (REQ-WFM-042): a record command equal to an alias of another skill's manifest skips the record skill, the manifest skill keeps its alias.

        Example: `alpha` with the record `/research` and `lookup` (alias `research`, no record): `lookup` is registered and answers `/research x`, `alpha` is skipped with a problem naming `research`.
        """
        self.alias_case("alpha")

    @mark.req("REQ-WFM-042")
    def test_a_record_command_that_is_an_alias_of_a_manifest_skill_is_refused_when_the_record_skill_sorts_last(self):
        """F-14 (REQ-WFM-042): the same with the record skill sorted after the manifest skill.

        Example: `zeta` with the record `/research` and `lookup` (alias `research`, no record): `lookup` is registered, `zeta` is skipped with a problem naming `research`.
        """
        self.alias_case("zeta")

    @mark.req("REQ-WFM-042")
    def test_a_record_command_equal_to_an_alias_of_its_own_manifest_registers_the_skill(self):
        """F-17 (REQ-WFM-042, regression of T-09): a record does not clash with its own manifest; the skill is registered with the record's command and its alias still resolves.

        Example: `lookup` (alias `research`, no other skill) with the record `{"id": "lookup", "command": "/research"}`: the registry holds `research`, no problem; `/research x` and the old `/lookup x` both answer.
        """
        # Given: the skill lookup with the alias research and a record whose command is that alias
        self.add("lookup", aliases=("research",))
        self.record("lookup", "/research", "wf-lookup")
        # When: loaded with the catalog
        problems = self.load(catalog=self.catalog)
        # Then: no problem, the skill carries the record's command and graph, and the alias still resolves to it
        self.assertEqual(problems, [])
        self.assertEqual(self.registry.ids(), ["research"])
        self.assertEqual(self.registry.get("research").workflow_graph_id, "wf-lookup")
        self.assertEqual(self.registry.parse("/research x")["task"], "research")

    @mark.req("REQ-WFM-042")
    def test_a_record_command_that_clashes_with_another_skill_names_that_cause_and_not_a_missing_record(self):
        """F-17 (REQ-WFM-042): a real clash with a skill without a record or with the alias of another skill is skipped with a problem that says so; the skill with the record is named.

        Example: `alpha` with `/beta` and manifest-only `beta`: the problem names `beta`; `alpha` with `/research` and `lookup` (alias `research`): the problem names `lookup`; neither says "record" is missing.
        """
        for command, other, aliases in (("/beta", "beta", ()), ("/research", "lookup", ("research",))):
            with self.subTest(command=command):
                # Given: alpha with a record whose command is the folder name or an alias of the manifest-only skill `other`
                self.reset()
                self.add("alpha")
                self.add(other, aliases=aliases)
                self.record("alpha", command, "wf-alpha")
                # When: loaded
                problems = self.load(catalog=self.catalog)
                # Then: alpha is skipped, one problem names alpha, the command and the other skill, and does not claim a missing record
                self.assertEqual(self.registry.ids(), [other])
                self.assertEqual(len(problems), 1)
                self.assertTrue(problems[0].startswith("alpha:"))
                self.assertIn(other, problems[0])
                self.assertIn(command.lstrip("/"), problems[0])
                self.assertNotIn("without a record", problems[0])

    @mark.req("REQ-WFM-042")
    def test_the_own_alias_of_a_record_skill_does_not_hide_the_clash_with_another_skill_with_that_alias(self):
        """F-17 (REQ-WFM-042): the own folder name and the own alias are left out of the comparison, the other skills' are not.

        Example: `alpha` (alias `research`) with the record `/research` and `zeta` (alias `research`, no record), in both folder orders: alpha is skipped with a problem, zeta keeps `research`.
        """
        for first, second in (("alpha", "zeta"), ("zeta", "alpha")):
            with self.subTest(record_skill=first):
                # Given: a record skill whose command is its own alias, and another manifest-only skill with the same alias
                self.reset()
                self.add(first, aliases=("research",))
                self.add(second, aliases=("research",))
                self.record(first, "/research", "wf-" + first)
                # When: loaded
                problems = self.load(catalog=self.catalog)
                # Then: the record skill is skipped with a problem, the other skill is registered and answers /research
                self.assertEqual(self.registry.ids(), [second])
                self.assertEqual([p.split(":")[0] for p in problems], [first])
                self.assertEqual(self.registry.parse("/research x")["task"], second)

    @mark.req("REQ-WFM-042")
    def test_the_folder_name_of_a_skill_with_a_record_is_free_for_another_record_command(self):
        """T-10 gap (REQ-WFM-042, mutant: folder names of skills with a record also taken): swapping commands between two skills with records is allowed.

        Example: `alpha` with `/zeta` and `zeta` with `/other`: both load, `/zeta x` runs alpha's graph, `/other x` zeta's.
        """
        # Given: alpha takes the folder name of zeta, which has moved to another command
        self.add("alpha")
        self.add("zeta")
        self.record("alpha", "/zeta", "wf-alpha")
        self.record("zeta", "/other", "wf-zeta")
        # When: loaded
        problems = self.load(catalog=self.catalog)
        # Then: no problem, both are registered under their record commands
        self.assertEqual(problems, [])
        self.assertEqual(sorted(self.registry.ids()), ["other", "zeta"])
        self.assertEqual(self.registry.get("zeta").workflow_graph_id, "wf-alpha")
        self.assertEqual(self.registry.get("other").workflow_graph_id, "wf-zeta")

    @mark.req("REQ-WFM-042")
    def test_the_alias_of_a_skill_with_a_record_still_counts_for_the_commands_of_other_records(self):
        """T-10 gap (REQ-WFM-042, mutant: aliases of skills with a record not taken): the alias of a skill with a record keeps resolving to it, so another record cannot take it.

        Example: `lookup` (alias `research`) with the record `/ask` and `alpha` with `/research`: alpha is skipped with a problem; `/research x` still reaches lookup (as `ask`).
        """
        # Given: lookup with a record under another command, alpha with a record on lookup's alias
        self.add("alpha")
        self.add("lookup", aliases=("research",))
        self.record("lookup", "/ask", "wf-lookup")
        self.record("alpha", "/research", "wf-alpha")
        # When: loaded
        problems = self.load(catalog=self.catalog)
        # Then: alpha is skipped, lookup keeps the alias
        self.assertEqual(self.registry.ids(), ["ask"])
        self.assertEqual([p.split(":")[0] for p in problems], ["alpha"])
        self.assertEqual(self.registry.parse("/research x")["task"], "ask")

    @mark.req("REQ-WFM-042")
    def test_aliases_and_folder_names_are_compared_in_the_form_the_registry_looks_them_up(self):
        """T-10 gap (REQ-WFM-042, mutants: alias or folder name compared without the normal form): capitals and a slash in an alias or in a folder name do not hide a clash.

        Example: manifest alias `/Research` and record `/research` clash; folder `Beta` (manifest-only, id = folder) and record `/beta` clash.
        """
        for name, aliases, command in (("lookup", ("/Research",), "/research"), ("Beta", (), "/beta")):
            with self.subTest(other=name):
                # Given: a manifest-only skill with a capital in its alias or its folder name, and alpha with a record on the lower case form
                self.reset()
                self.add("alpha")
                self.add(name, aliases=aliases)
                self.record("alpha", command, "wf-alpha")
                # When: loaded
                problems = self.load(catalog=self.catalog)
                # Then: alpha is skipped with one problem, the other skill is registered
                self.assertEqual(self.registry.ids(), [name])
                self.assertEqual([p.split(":")[0] for p in problems], ["alpha"])

    @mark.req("REQ-WFM-041")
    def test_a_command_with_an_underscore_is_skipped_with_a_problem(self):
        """T-10 gap (REQ-WFM-041, mutant: `_` allowed): only ASCII letters and digits are commands, an underscore is not.

        Example: a record written around the store with the command `/a_b` skips the skill with a problem; `command_problem("/a_b")` gives a reason, `command_problem("/ab")` gives None.
        """
        # Given: a skill with a record whose command has an underscore (written around the store)
        self.add("alpha")
        self.records.tables.put("skills", "alpha", {"id": "alpha", "data": {"command": "/a_b", "workflow_graph_id": "wf-alpha", "context_graph_id": "ctx-alpha"}}, "anna")
        # When: the command is judged and the extensions are loaded
        problems = self.load(catalog=self.catalog)
        # Then: the reason is given, the skill is skipped with a problem
        self.assertTrue(command_problem("/a_b"))
        self.assertIsNone(command_problem("/ab"))
        self.assertEqual(self.registry.ids(), [])
        self.assertEqual([p.split(":")[0] for p in problems], ["alpha"])

    @mark.req("REQ-WFM-029")
    def test_a_command_followed_by_a_non_ascii_space_is_no_task_command(self):
        """F-18 (REQ-WFM-029), accepted side effect of `re.A` on the registry (owner decision 2026-11-08): the separator must be an ASCII space; `parse` gives None, no error.

        Example: `/lookup\\u00a0x`, `/lookup\\u2003x` (em space) and `/lookup\\u3000x` (ideographic space) give None; `/lookup x` gives the task.
        """
        # Given: the registry with the skill lookup
        self.add("lookup")
        self.load()
        # When/Then: a non-breaking, em and ideographic space after the command do not make a command (re.A makes \s ASCII only); the plain space does
        for space in (" ", " ", "　"):
            with self.subTest(space=repr(space)):
                self.assertIsNone(self.registry.parse("/lookup%sx y" % space))
        self.assertEqual(self.registry.parse("/lookup x y")["argument"], "x y")

    @mark.req("REQ-WFM-041")
    def test_no_command_with_a_character_the_registry_cannot_look_up_is_registered_and_parse_never_raises(self):
        """F-15 (REQ-WFM-041): a record command is ASCII lower case letters and digits; a Unicode lower case letter whose upper case is another letter is skipped with a problem and `parse` does not raise.

        Example: records `/ς`, `/µ`, `/ſ`, `/ı` and `/ab1` (the last is fine): only `ab1` is registered; `/Σ x`, `/ſearch x`, and 20000 random texts give None or a result, never a KeyError.
        """
        # Given: skills whose record commands hold characters the registry cannot look up again, one good skill, and the manifest skill search
        names = ["alpha", "beta", "delta", "gamma", "search", "good"]
        for name in names:
            self.add(name)
        for name, command in zip(names, ("/ς", "/µ", "/ſ", "/ı", None, "/ab1")):
            if command is not None:
                self.records.tables.put("skills", name, {"id": name, "data": {"command": command, "workflow_graph_id": "wf-" + name,
                                                                             "context_graph_id": "ctx-" + name}}, "anna")
        # When: the extensions are loaded and many texts are parsed
        problems = self.load(catalog=self.catalog)
        rng = random.Random(15)
        texts = ["/Σ x", "/ς x", "/ſearch x", "/SEARCH x", "/ab1 x", "/AB1 x"]
        texts += ["/" + "".join(chr(rng.randrange(0x110000)) for _ in range(rng.randrange(1, 5))) + " x" for _ in range(20000)]
        texts += ["/" + "".join(rng.choice("sſkKiIıİab1 ") for _ in range(rng.randrange(1, 6))) + " x" for _ in range(20000)]
        for text in texts:
            self.registry.parse(text)       # must not raise a KeyError (or anything else but TaskCommandError)
        # Then: only the good skills are tasks, four problems name the others
        self.assertEqual(self.registry.ids(), ["ab1", "search"])
        self.assertEqual(sorted(p.split(":")[0] for p in problems), ["alpha", "beta", "delta", "gamma"])
        self.assertEqual(self.registry.parse("/AB1 x")["task"], "ab1")
        self.assertEqual(self.registry.parse("/ſearch x"), None)

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
