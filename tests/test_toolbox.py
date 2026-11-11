"""
Toolbox import checks beyond the acceptance tests (REQ-WFM-052, 053, 055): every malformed exchange file is refused as invalid_file and stores nothing.
Run: python tests/test_toolbox.py
"""
import json
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO, os.path.join(REPO, "tests", "helpers"), os.path.join(REPO, "tests", "helpers", "mocks")):
    sys.path.insert(0, path)

from if_203_transforms import TransformLibraryMock     # noqa: E402
from toolbox_fakes import EventRecord, exchange_file    # noqa: E402
from toolbox import Toolbox, ToolboxError               # noqa: E402


class ImportChecks(unittest.TestCase):
    def setUp(self):
        self.library = TransformLibraryMock()
        self.box = Toolbox(self.library, lambda account: True, EventRecord())

    def test_malformed_files_are_refused_and_store_nothing(self):
        """Example: text that is not JSON, a JSON list, version 0, version true and an `inputs` that is a text."""
        good = json.loads(exchange_file("t.one"))
        bad = ["not json", "[]", json.dumps(dict(good, version=0)), json.dumps(dict(good, version=True)), json.dumps(dict(good, inputs="x")), json.dumps(dict(good, id=""))]
        for text in bad:
            with self.subTest(text=text[:30]):
                with self.assertRaises(ToolboxError) as caught:
                    self.box.import_transform(text, "anna")
                self.assertEqual(caught.exception.code, "invalid_file")
        self.assertEqual(self.library.list_ids("transforms"), [])
        self.assertEqual(self.box.import_transform(json.dumps(good), "anna"), "t.one")      # the twin is accepted


if __name__ == "__main__":
    unittest.main()
