"""
REQ-WFM-001 (each kind of work is a task: a skill file plus a pipeline, selectable) and REQ-WFM-005 (a pipeline proposed by a model stays a draft and cannot run
as trusted), on the existing Core, SkillStore and Library. No model needed. Run: python tests/test_skills_as_tasks.py
"""
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from core import Core                     # noqa: E402
from library import Library               # noqa: E402
from pipeline import PipelineError        # noqa: E402
from skill_store import SkillStore        # noqa: E402

PIPELINE = {"id": "demo.double", "version": 1, "title": "Checks a computable claim", "tags": ["demo"], "result": "out",
            "nodes": [{"id": "calc", "use": "code.hard_checks_offline@2", "wire": {"claim": "$input.claim"}, "output": "out"}]}
CLAIM = {"claim": {"type": "numeric", "data": {"expression": "2+2", "value": 4}}}


class SkillsAsTasks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.skills = os.path.join(self.tmp.name, "skills")
        os.makedirs(self.skills)
        self.library = Library(os.path.join(REPO, "library"), os.path.join(self.tmp.name, "user"))

    def tearDown(self):
        self.tmp.cleanup()

    def skill_file(self, name, pipeline):
        with open(os.path.join(self.skills, name + ".md"), "w") as fp:
            fp.write("---\nname: %s\npipeline: %s\nmax_safety: {runs_code: true}\n---\n" % (name, pipeline))

    def test_the_selectable_list_shows_every_skill_file(self):        # REQ-WFM-001, TC-WFM-001
        shipped = SkillStore(os.path.join(REPO, "skills"))
        files = sorted(f[:-3] for f in os.listdir(os.path.join(REPO, "skills")) if f.endswith(".md"))
        self.assertEqual(shipped.errors, {})
        self.assertEqual(shipped.names(), files)
        self.assertTrue(all(shipped.get(name)["pipeline"] for name in files))

    def test_a_selected_skill_runs_its_pipeline(self):                # REQ-WFM-001, TC-WFM-001
        self.library.add_draft("pipeline", PIPELINE)
        self.library.set_status("demo.double@1", "trusted")
        self.skill_file("double", "demo.double")
        core = Core(self.skills, self.library, self.tmp.name)
        self.assertIn("double", core.skills.names())
        result = core.run("double", CLAIM)
        self.assertEqual(result.answer["status"], "pass")
        self.assertTrue(any(e["kind"] == "start" and e["node"] == "calc" for e in result.events))
        with self.assertRaises(PipelineError):
            core.run("nothing", {})

    def test_a_proposed_pipeline_stays_a_draft_and_cannot_run_as_trusted(self):      # REQ-WFM-005, TC-WFM-005
        ref = self.library.add_draft("pipeline", PIPELINE, by="gemma4")
        self.assertEqual(self.library.resolve(ref, "pipeline", allow_draft=True)["status"], "draft")
        chosen = self.library.select("pipeline", tags=["demo"])
        self.assertEqual(chosen["selected"], [])
        self.assertIn({"ref": ref, "reason": "status is draft"}, chosen["dropped"])
        self.skill_file("double", "demo.double")
        core = Core(self.skills, self.library, self.tmp.name)
        with self.assertRaises(PipelineError):
            core.run("double", CLAIM)
        self.library.set_status(ref, "trusted", by="anna")            # only a person's decision changes it
        self.assertEqual(core.run("double", CLAIM).answer["status"], "pass")


if __name__ == "__main__":
    unittest.main()
