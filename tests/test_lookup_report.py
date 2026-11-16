"""
Tests for the report file of /lookup (FB-08): the sources of an answer are kept in a Markdown file of the files volume, where every http(s) address is a link, so the Skill run view
lists the file as a download and no text of a run has to become a link there (REQ-CLV-043 stays). Web text is untrusted: only http and https addresses become links.
Run with the MIA virtualenv: python tests/test_lookup_report.py
"""
import json
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

import harness as H                                   # noqa: E402
import research_chat as RC                            # noqa: E402
import test_research as TR                            # noqa: E402
from core import Core                                 # noqa: E402
from library import Library                           # noqa: E402

WORLD = json.load(open(os.path.join(REPO, "eval", "suites", "research", "web.json"), encoding="utf-8"))
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}")        # the rule of file_store.py
ANSWER = {"answer": "It opened on 3 May 2021.", "status": "answered", "sources": [{"url": "https://gazette.example/x?a=1&b=2", "quote": "opened to traffic on 3 May 2021"}]}


def live(text):
    """the text as a Markdown reader sees it: a backslash-escaped character is only a character"""
    return re.sub(r"\\.", "", text)


class Report(unittest.TestCase):
    def test_a_web_address_is_a_link_with_its_quote(self):
        text = RC.format_report("When did it open?", ANSWER)
        self.assertIn("<https://gazette.example/x?a=1&b=2>", text)
        self.assertIn("opened to traffic on 3 May 2021", text)
        self.assertIn("It opened on 3 May 2021.", text)

    def test_a_source_without_an_address_stays_text(self):
        text = RC.format_report("q", {"answer": "a", "status": "answered", "sources": [{"quote": "a quote", "title": "A book"}]})
        self.assertIn("a quote", text)
        self.assertNotIn("<", text.split("Sources")[1])

    def test_only_http_and_https_become_links(self):                       # red team: web text is data (TB-web)
        hostile = ["javascript:alert(1)", "data:text/html,<script>alert(1)</script>", "file:///etc/passwd", "https://ok.example/a> [x](javascript:alert(1)) <b", "HTTPS://UP.example/"]
        answer = {"answer": "a", "status": "answered", "sources": [{"url": url, "quote": "q"} for url in hostile]}
        text = live(RC.format_report("q", answer))
        links = re.findall(r"<([^<>\s]*)>", text)
        self.assertTrue(all(re.match(r"https?://", link, re.I) for link in links), links)
        self.assertNotIn("](javascript", text)
        self.assertNotIn("<script", text)
        self.assertNotIn("<javascript", text)
        self.assertNotIn("<file", text)

    def test_a_quote_cannot_add_markup_or_links(self):
        answer = {"answer": "a", "status": "answered", "sources": [{"url": "https://a.example/", "quote": "[click](javascript:alert(1)) <img src=x onerror=alert(1)>"}]}
        text = live(RC.format_report("q", answer))
        self.assertNotIn("](", text)
        self.assertNotIn("<img", text)


class Run(unittest.TestCase):
    def core(self, script="reader"):
        return Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), tempfile.mkdtemp(), model=TR.Scripted(script), tools=H.fixture_tools(WORLD)[0])

    def test_an_answer_with_sources_puts_the_report_into_the_files_volume(self):
        kept = {}
        text = RC.run_research(self.core(), "When did the Rivertown Bridge open to traffic?", files=lambda name, data: kept.update({name: data}))
        (name, data), = kept.items()
        self.assertTrue(NAME.fullmatch(name) and name.endswith(".md"), name)
        self.assertIn("<https://gazette.rivertown.example/bridge-opens>", data)
        self.assertIn("Sources:\n- https://gazette.rivertown.example/bridge-opens", text)      # the chat text is as before

    def test_a_files_volume_that_fails_does_not_take_the_answer_away(self):
        def broken(name, data):
            raise RuntimeError("volume full")
        text = RC.run_research(self.core(), "When did the Rivertown Bridge open to traffic?", files=broken)
        self.assertIn("3 May 2021", text)
        self.assertIn("volume full", text)

    def test_without_an_answer_no_file_is_made(self):
        kept = {}
        RC.run_research(self.core("unknown"), "Who designed the Rivertown Bridge?", pipeline="research.baseline@1", files=lambda name, data: kept.update({name: data}))
        self.assertEqual(kept, {})

    def test_the_skill_asks_for_the_files_volume(self):
        manifest = json.load(open(os.path.join(REPO, "extensions", "lookup", "manifest.json"), encoding="utf-8"))
        self.assertIn("files", manifest["needs"])


if __name__ == "__main__":
    unittest.main()
