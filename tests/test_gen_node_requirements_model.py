"""The model generator keeps the parents of a goal's requirements after the merge moves them into a node file (D-420, RULES Commit)."""
import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("gen_node_requirements_model", ROOT / "tools/gen_node_requirements_model.py")
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)

HLS = "# High-level spec\n\n### HR-001 – One place\n- Parent: FR-63, FR-64\n"
REQ = ("# Requirements\n\n### REQ-GTB-900 – Moved item\n- Level: low   Subject: Persistence\n- Text: The Graph tables shall x.\n"
       "- Parent: HR-001\n- Verification method: Test\n- Status: {status}\n- History: G-T.RULES Plan step 1b, 2026-11-22, new; moved here at the merge\n")


class HighLevelParentsAfterTheMerge(unittest.TestCase):
    def build(self, where, status):
        root = pathlib.Path(self.enterContext(tempfile.TemporaryDirectory()))
        (root / "specs/mia/goals/G-T.RULES").mkdir(parents=True)
        (root / "specs/mia/goals/G-T.RULES/high-level-spec.md").write_text(HLS, encoding="utf-8")
        target = root / where / "requirements.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(REQ.format(status=status), encoding="utf-8")
        return root

    def parents(self, root):
        return {r["id"]: r["parent"] for r in gen.read(root)}["REQ-GTB-900"]

    def test_an_hr_parent_in_a_goal_file_stands_for_its_own_parents(self):
        root = self.build("specs/mia/goals/G-T.RULES", "Approved")
        self.assertEqual(self.parents(root), ["FR-63", "FR-64"])

    def test_an_hr_parent_in_a_node_file_is_resolved_through_the_goal_in_its_history(self):
        root = self.build("specs/mia/nodes/N-3/nodes/N-3.2", "Verified")
        self.assertEqual(self.parents(root), ["FR-63", "FR-64"])

    def test_a_node_item_without_a_goal_keeps_its_parent(self):
        root = self.build("specs/mia/nodes/N-3/nodes/N-3.2", "Verified")
        p = root / "specs/mia/nodes/N-3/nodes/N-3.2/requirements.md"
        p.write_text(p.read_text(encoding="utf-8").replace("G-T.RULES Plan step 1b", "Plan"), encoding="utf-8")
        self.assertEqual(self.parents(root), ["HR-001"])


if __name__ == "__main__":
    unittest.main()
