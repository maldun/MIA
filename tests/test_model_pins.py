"""The model pins a snapshot records come from the configuration (G-V2.SNAPSHOT, IF-203 v2 `pins()`; owner decision 2026-11-19). Run with: python tests/test_model_pins.py"""
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import constants                                          # noqa: E402
from storage import Storage                               # noqa: E402
from storage_files import FileBackend                     # noqa: E402
from workflow_library import WorkflowLibrary, pins_from_config  # noqa: E402


class PinsFromConfig(unittest.TestCase):
    def test_the_keys_are_those_of_the_config(self):
        self.assertEqual((constants.MODEL_KEY, constants.MODEL_LIGHT_KEY), ("version", "version_light"))

    def test_the_light_and_the_full_model_become_the_two_pins(self):
        cfg = {"version": "gemma4:26b", "version_light": "gemma4:12b-it-qat", "other": 1}
        self.assertEqual(pins_from_config(cfg), {"MP-light": "gemma4:12b-it-qat", "MP-full": "gemma4:26b"})

    def test_a_missing_empty_or_non_text_entry_leaves_its_pin_out(self):
        self.assertEqual(pins_from_config({}), {})
        self.assertEqual(pins_from_config({"version": "", "version_light": None}), {})
        self.assertEqual(pins_from_config({"version": 5, "version_light": ["x"]}), {})
        self.assertEqual(pins_from_config({"version_light": "m"}), {"MP-light": "m"})

    def test_a_snapshot_of_the_real_library_holds_them(self):
        cfg = {"version": "gemma4:26b", "version_light": "gemma4:12b-it-qat"}
        lib = WorkflowLibrary(Storage(FileBackend(tempfile.mkdtemp())), is_owner=lambda a: True, pins=lambda: pins_from_config(cfg))
        lib.snapshot("a", "anna")
        self.assertEqual(lib.read_snapshot("a")["pins"], {"MP-light": "gemma4:12b-it-qat", "MP-full": "gemma4:26b"})
        cfg["version_light"] = "other:1"          # a later change is seen by the next snapshot, the stored one is not touched
        lib.snapshot("b", "anna")
        self.assertEqual((lib.read_snapshot("a")["pins"]["MP-light"], lib.read_snapshot("b")["pins"]["MP-light"]), ("gemma4:12b-it-qat", "other:1"))

    def test_the_app_gives_the_library_the_pins(self):
        """web_app.py cannot be imported in a test (it starts the service), so the line that builds the library is read as text"""
        text = open(os.path.join(os.path.dirname(HERE), "web_app.py"), encoding="utf-8").read()
        call = re.search(r"WorkflowLibrary\(([^\n]*)\)", text).group(1)
        self.assertIn("pins=lambda: pins_from_config(cfg)", call)


if __name__ == "__main__":
    unittest.main()
