"""
Finding of 2026-10-29 (found while moving the review code): FullTextSource imported web_tools and pdf_text by plain name inside a method, which only works when the folder of MIA is on the
module path (the tests); under `python -m MIA` (only the parent folder on the path) the full-text stage of /review raised ModuleNotFoundError. This test runs the source the way the
application does: as part of the package, through a link, with only the parent folder on the path. Run in the image: bash tools/run_in_image.sh tests/test_fulltext_package_mode.py
"""
import importlib
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)                   # not REPO: the folder of MIA is NOT on the path, as under python -m MIA

WORK = {"oa_url": "https://x.example/paper", "doi": "10.1/a", "title": "A paper"}
HTML = "<html><body><h1>Abstract</h1><p>Graph methods for scheduling.</p><h1>Conclusion</h1><p>They work.</p></body></html>"


def module():
    for name in ("MIA.extensions.review.fulltext", "MIA.fulltext"):          # the code moved on 2026-10-29; the test follows it
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError as exc:
            if exc.name != name and not name.startswith(exc.name or "\0"):
                raise
    raise AssertionError("no fulltext module found")


class FullTextInThePackage(unittest.TestCase):
    def test_an_html_page_is_read_without_the_folder_of_mia_on_the_path(self):
        source = module().FullTextSource(lambda url, accept=None, max_bytes=None: {"content_type": "text/html", "text": HTML, "body": b"", "url": WORK["oa_url"], "truncated": False})
        found = source(WORK)
        self.assertIsNotNone(found, source.notes)
        self.assertIn("Graph methods", " ".join(s["text"] for s in found["sections"]))

    def test_a_pdf_without_the_pdf_library_stays_at_abstract_level_and_says_why(self):
        source = module().FullTextSource(lambda url, accept=None, max_bytes=None: {"content_type": "application/pdf", "text": "", "body": b"%PDF-1.4 not a pdf", "url": WORK["oa_url"]})
        self.assertIsNone(source(WORK))
        self.assertTrue(source.notes)                                           # the reason is kept, the review goes on


if __name__ == "__main__":
    unittest.main()
