"""
Tests for the report of /lookup (FB-08, G-V3.REPORT T-02): the sources of an answer are handed to the runtime as the run report, where every http(s) address is a link, so the Skill run view
shows the report and no other text of a run has to become a link (REQ-CLV-043 stays). Web text is untrusted: only http and https addresses become links.
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
ANSWER = {"answer": "It opened on 3 May 2021.", "status": "answered", "sources": [{"url": "https://gazette.example/x?a=1&b=2", "quote": "opened to traffic on 3 May 2021"}]}


def live(text):
    """the text as a Markdown reader sees it: a backslash-escaped character is only a character"""
    return re.sub(r"\\.", "", text)


class Report(unittest.TestCase):
    def test_a_web_address_is_a_link_with_its_quote(self):
        """TC-WFM-139: an http or https source is written as a link with its quote below the answer.
        Example: the source https://gazette.example/x?a=1&b=2 becomes `<https://gazette.example/x?a=1&b=2>` with the quote after it."""
        # Given: an answered question with one web source; When: the report is written
        text = RC.format_report("When did it open?", ANSWER)
        # Then: the address is a link, and the quote and the answer are in the text
        self.assertIn("<https://gazette.example/x?a=1&b=2>", text)
        self.assertIn("opened to traffic on 3 May 2021", text)
        self.assertIn("It opened on 3 May 2021.", text)

    def test_a_source_without_an_address_stays_text(self):
        """TC-WFM-139: a source with no address has no link.
        Example: the source {"title": "A book", "quote": "a quote"} gives the quote and no `<`."""
        # Given: a source with a title and a quote but no address; When: the report is written
        text = RC.format_report("q", {"answer": "a", "status": "answered", "sources": [{"quote": "a quote", "title": "A book"}]})
        # Then: the quote is there and nothing below `Sources` is a link
        self.assertIn("a quote", text)
        self.assertNotIn("<", text.split("Sources")[1])

    def test_only_http_and_https_become_links(self):                       # red team: web text is data (TB-web)
        """TC-WFM-141: addresses that are javascript:, data:, file: or have a second link behind them are no links; only http and https are.
        Example: `javascript:alert(1)` as a source address leaves no `<javascript` in the report."""
        # Given: sources with hostile addresses and one with an upper-case scheme
        hostile = ["javascript:alert(1)", "data:text/html,<script>alert(1)</script>", "file:///etc/passwd", "https://ok.example/a> [x](javascript:alert(1)) <b", "HTTPS://UP.example/"]
        answer = {"answer": "a", "status": "answered", "sources": [{"url": url, "quote": "q"} for url in hostile]}
        # When: the report is written; Then: every link target is http or https and nothing else is live
        text = live(RC.format_report("q", answer))
        links = re.findall(r"<([^<>\s]*)>", text)
        self.assertTrue(all(re.match(r"https?://", link, re.I) for link in links), links)
        self.assertNotIn("](javascript", text)
        self.assertNotIn("<script", text)
        self.assertNotIn("<javascript", text)
        self.assertNotIn("<file", text)

    def test_a_quote_cannot_add_markup_or_links(self):
        """TC-WFM-141: a quote with a javascript: link and an image tag is only characters in the report.
        Example: the quote `[click](javascript:alert(1))` has escaped brackets."""
        # Given: a source whose quote holds a link and an image with an onerror handler; When: the report is written
        answer = {"answer": "a", "status": "answered", "sources": [{"url": "https://a.example/", "quote": "[click](javascript:alert(1)) <img src=x onerror=alert(1)>"}]}
        text = live(RC.format_report("q", answer))
        # Then: no link target and no tag is live
        self.assertNotIn("](", text)
        self.assertNotIn("<img", text)


class Run(unittest.TestCase):
    def core(self, script="reader"):
        return Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), tempfile.mkdtemp(), model=TR.Scripted(script), tools=H.fixture_tools(WORLD)[0])

    def test_an_answered_question_hands_its_report_to_the_runtime(self):
        """TC-WFM-139: an answered question hands its report to the runtime once, and the chat text keeps its sources.
        Example: the question about the Rivertown Bridge hands over one report with `<https://gazette.rivertown.example/bridge-opens>`."""
        # Given: a scripted research run; When: it ends with an answer
        handed = []
        text = RC.run_research(self.core(), "When did the Rivertown Bridge open to traffic?", run_report=handed.append)
        # Then: one report is handed over and the chat text is as before
        self.assertEqual(len(handed), 1)                                                          # the runtime names and stores the file (REQ-WFM-139)
        self.assertIn("<https://gazette.rivertown.example/bridge-opens>", handed[0])
        self.assertIn("Sources:\n- https://gazette.rivertown.example/bridge-opens", text)      # the chat text is as before

    def test_a_report_that_cannot_be_handed_over_does_not_take_the_answer_away(self):
        """TC-WFM-139: a place for the report that fails does not take the answer away; the chat text names the reason.
        Example: run_report raises "report store full": the text still has `3 May 2021` and the reason."""
        # Given: a place for the report that fails
        def broken(markdown):
            raise RuntimeError("report store full")
        text = RC.run_research(self.core(), "When did the Rivertown Bridge open to traffic?", run_report=broken)
        # When / Then: the answer is in the text and so is the reason
        self.assertIn("3 May 2021", text)
        self.assertIn("report store full", text)

    def test_without_an_answer_nothing_is_handed_over(self):
        """TC-WFM-139: a question without an answer hands nothing over (the runtime writes the report of such a run).
        Example: "Who designed the Rivertown Bridge?" is unknown: nothing is handed over."""
        # Given: a scripted research run that ends unknown; When: it ends
        handed = []
        RC.run_research(self.core("unknown"), "Who designed the Rivertown Bridge?", pipeline="research.baseline@1", run_report=handed.append)
        # Then: nothing is handed over
        self.assertEqual(handed, [])                                                               # the runtime writes the report of a run without an answer

    def test_the_skill_asks_for_the_run_report_and_no_longer_for_the_files_volume(self):
        """TC-WFM-139: the manifest of /lookup asks for the need run_report only and has the version 2.
        Example: needs ["run_report"], version "2"."""
        # Given / When: the manifest is read
        with open(os.path.join(REPO, "extensions", "lookup", "manifest.json"), encoding="utf-8") as handle:
            manifest = json.load(handle)
        # Then: it asks for run_report and carries the new version
        self.assertEqual(manifest["needs"], ["run_report"])
        self.assertEqual(manifest["version"], "2")                                                # the needs changed: a new version of the skill


if __name__ == "__main__":
    unittest.main()
