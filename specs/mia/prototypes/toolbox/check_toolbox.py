"""PROTOTYPE checks against OC-1..OC-3 and AC-32 (the agent's own cases, not protected, never eval cases). Run: python check_toolbox.py"""
import json
import os
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from toolbox import ToolboxError, Toolbox   # noqa: E402

NODES = pathlib.Path(__file__).resolve().parents[4] / "library" / "nodes"
MARKER = os.path.join(tempfile.gettempdir(), "toolbox_prototype_marker")


def outside_file(tid="ext.double", status="trusted"):
    code = "open(%r, 'w').write('ran')\ndef run(a):\n    return a['x'] * 2\n" % MARKER      # side effect at import time = the marker of AC-32
    return json.dumps({"id": tid, "version": 1, "status": status, "inputs": {"type": "object"}, "outputs": {"type": "object"}, "code": code})


class ToolboxChecks(unittest.TestCase):
    def setUp(self):
        if os.path.exists(MARKER):
            os.remove(MARKER)
        self.tb = Toolbox()

    def test_oc1_outside_step_is_untrusted_with_reason_and_does_not_run(self):
        self.tb.import_transform(outside_file(status="trusted"))        # the file lies about its status
        item = self.tb.look_up("ext.double")
        self.assertEqual(item["trust"], "untrusted")
        self.assertTrue(item["reason"])
        self.assertFalse(os.path.exists(MARKER))
        with self.assertRaises(ToolboxError) as ctx:
            self.tb.run("ext.double", {"x": 2})
        self.assertEqual(ctx.exception.code, "untrusted")
        self.assertFalse(os.path.exists(MARKER))

    def test_oc2_only_owner_trusts_then_it_runs(self):
        self.tb.import_transform(outside_file())
        with self.assertRaises(ToolboxError) as ctx:
            self.tb.set_trust("ext.double", "trusted", "guest")
        self.assertEqual(ctx.exception.code, "owner_only")
        self.assertIn("untrusted", ctx.exception.why)
        self.assertEqual(self.tb.look_up("ext.double")["trust"], "untrusted")
        self.tb.set_trust("ext.double", "trusted", "owner")
        self.assertEqual(self.tb.run("ext.double", {"x": 2}), 4)
        self.assertTrue(os.path.exists(MARKER))

    def test_oc3_retired_not_offered_but_usable_as_baseline(self):
        self.tb.import_transform(outside_file())
        self.tb.set_trust("ext.double", "trusted", "owner")
        self.assertIn("ext.double", self.tb.offer())
        self.tb.set_lifecycle("ext.double", "retired", "owner")
        self.assertNotIn("ext.double", self.tb.offer())
        with self.assertRaises(ToolboxError):
            self.tb.run("ext.double", {"x": 1})
        self.assertEqual(self.tb.run("ext.double", {"x": 1}, as_baseline=True), 2)

    def test_trust_and_lifecycle_are_independent_and_tested_needs_evidence(self):
        self.tb.import_transform(outside_file())
        with self.assertRaises(ToolboxError):
            self.tb.set_lifecycle("ext.double", "tested", "owner")
        self.tb.set_lifecycle("ext.double", "tested", "owner", evidence="run-17")
        item = self.tb.look_up("ext.double")
        self.assertEqual((item["trust"], item["lifecycle"]), ("untrusted", "tested"))
        for bad in ("fine", ""):
            with self.assertRaises(ToolboxError):
                self.tb.set_trust("ext.double", bad, "owner")

    def test_duplicate_id_refused_and_bad_file_refused(self):
        self.tb.import_transform(outside_file())
        with self.assertRaises(ToolboxError) as ctx:
            self.tb.import_transform(outside_file())
        self.assertEqual(ctx.exception.code, "duplicate_id")
        with self.assertRaises(ToolboxError) as ctx:
            self.tb.import_transform('{"id": "x"}')
        self.assertEqual(ctx.exception.code, "invalid_file")

    def test_export_import_round_trip(self):
        self.tb.import_transform(outside_file())
        text = self.tb.export_transform("ext.double")
        other = Toolbox()
        other.import_transform(text)
        a, b = self.tb.look_up("ext.double"), other.look_up("ext.double")
        self.assertEqual([a[k] for k in ("id", "version", "inputs", "outputs")], [b[k] for k in ("id", "version", "inputs", "outputs")])

    def test_shipped_nodes_are_seeded_trusted(self):
        self.tb.seed_shipped(NODES)
        ids = self.tb.offer()
        self.assertGreater(len(ids), 50)
        self.assertTrue(all(self.tb.look_up(i)["trust"] == "trusted" for i in ids))


if __name__ == "__main__":
    unittest.main()
