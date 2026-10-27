"""
REQ-WFM-017 (the search command is a library entry that lists the findings of the metasearch: title, address, short text; it composes and verifies no answer and
starts no pipeline; AC-23). The command itself is old (research_chat.run_search, routed by ChatService; tests/test_research_command.py); these tests carry the workflow
requirement over the recorded web of the research suite. Run with the MIA virtualenv: python tests/test_search_command.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

import harness as H                                   # noqa: E402
import research_chat as RC                            # noqa: E402
from core import Core                                 # noqa: E402
from library import Library                           # noqa: E402
from markers import mark                              # noqa: E402

WORLD = json.load(open(os.path.join(REPO, "eval", "suites", "research", "web.json"), encoding="utf-8"))


def search_function(tools):
    tool = tools["web_search"]
    return tool.func if hasattr(tool, "func") else tool[0]


class SearchCommand(unittest.TestCase):
    @mark.req("REQ-WFM-017")
    def test_the_search_tool_is_a_trusted_library_entry(self):
        entry = Library(os.path.join(REPO, "library")).resolve("tool.web_search", "node")
        self.assertEqual((entry["status"], entry["body"]["tool"]), ("trusted", "web_search"))

    @mark.req("REQ-WFM-017")
    def test_every_finding_shows_title_address_and_short_text(self):
        tools = H.fixture_tools(WORLD)[0]
        found = search_function(tools)("Rivertown Bridge")
        self.assertTrue(found["results"])
        text = RC.run_search(search_function(tools), "Rivertown Bridge")
        shown = [r for r in found["results"] if r["url"].startswith(("http://", "https://"))][:RC.MAX_RESULTS]
        for number, result in enumerate(shown, 1):
            self.assertIn("%d. " % number, text)
            self.assertIn(result["url"], text)
            if result.get("title"):
                self.assertIn(result["title"].split()[0], text)
            if result.get("snippet"):
                self.assertIn(result["snippet"].split()[0], text)

    @mark.req("REQ-WFM-017")
    def test_nothing_is_composed_or_verified_and_no_pipeline_starts(self):
        calls = []

        class NoModel:
            def chat(self, *args, **kwargs):
                calls.append(args)
                raise AssertionError("the search command must not call a model")

        tools = H.fixture_tools(WORLD)[0]
        runs = tempfile.mkdtemp()
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), runs, model=NoModel(), tools=tools)
        text = RC.run_search(search_function(tools), "Rivertown Bridge")
        self.assertEqual((calls, os.listdir(runs)), ([], []))                  # no model call, no run in the run log: no pipeline
        for composed in ("Sources:", "verdict", "supported", "refuted", "Answer"):
            self.assertNotIn(composed, text)
        self.assertEqual(core.run_log.__class__.__name__, "RunLog")


if __name__ == "__main__":
    unittest.main()
