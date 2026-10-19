"""
Tests for the /research command: the chat service routes "/research question" to the research task (and nothing else does), the answer is shown with its sources, the voice speaks the answer without the
sources, a search that cannot be reached becomes a message a person can act on, and the whole way from the command to the chat message over the recorded web. Run with the MIA virtualenv:
python tests/test_research_command.py
"""
import importlib
import json
import os
import sys
import tempfile
import time
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
import test_research as TR                             # noqa: E402
from core import Core                                 # noqa: E402
from library import Library                           # noqa: E402

MOODS = os.path.join(REPO, "moods.json")
WORLD = json.load(open(os.path.join(REPO, "eval", "suites", "research", "web.json"), encoding="utf-8"))


def wait_for(condition, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.01)
    return False


class Formatting(unittest.TestCase):
    ANSWER = {"answer": "It opened on 3 May 2021.", "status": "answered", "sources": [{"url": "https://gazette.example/x", "quote": "opened to traffic on 3 May 2021"}]}

    def test_the_answer_comes_with_its_sources(self):
        text = RC.format_answer(self.ANSWER)
        self.assertTrue(text.startswith("It opened on 3 May 2021."))
        self.assertIn("Sources:\n- https://gazette.example/x: “opened to traffic on 3 May 2021”", text)
        self.assertNotIn("**", text)

    def test_unknown_has_no_sources_and_says_so_in_words(self):
        text = RC.format_answer({"answer": "The pages do not say who designed it.", "status": "unknown", "sources": [{"url": "u", "quote": "q"}]})
        self.assertEqual(text, "The pages do not say who designed it.")

    def test_long_quotes_are_shortened_and_odd_answers_survive(self):
        long_quote = "word " * 200
        text = RC.format_answer(dict(self.ANSWER, sources=[{"url": "u", "quote": long_quote}]))
        self.assertLess(len(text), 400)
        self.assertIn(" ...", text)
        for odd in (None, {}, "text", {"answer": "  "}):
            self.assertEqual(RC.format_answer(odd), RC.NO_ANSWER)

    def test_only_an_answer_is_spoken_never_the_sources(self):
        self.assertEqual(RC.spoken_text(self.ANSWER), "It opened on 3 May 2021.")
        self.assertEqual(RC.spoken_text({"answer": "No idea.", "status": "unknown"}), "")
        self.assertEqual(RC.spoken_text(None), "")

    def test_errors_a_person_can_act_on(self):
        self.assertIn("SearXNG", RC.friendly_error("search: SearchError: searxng: connection refused; duckduckgo: timeout"))
        self.assertIn("connection refused", RC.friendly_error("search: SearchError: searxng: connection refused"))
        self.assertIn("budget", RC.friendly_error("budget exceeded: steps"))
        self.assertEqual(RC.friendly_error("something else"), "something else")


class Way(unittest.TestCase):
    """from the question to the chat text, over the recorded web, with a scripted model"""

    def core(self, model, tools=None):
        tmp = tempfile.mkdtemp()
        return Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), tmp, model=model, tools=tools or H.fixture_tools(WORLD)[0])

    def test_the_baseline_answers_with_sources_and_speaks_the_answer(self):
        spoken = []
        text = RC.run_research(self.core(TR.Scripted("reader")), "When did the Rivertown Bridge open to traffic?", speak=spoken.append)
        self.assertIn("3 May 2021", text)
        self.assertIn("Sources:\n- https://gazette.rivertown.example/bridge-opens", text)
        self.assertEqual(len(spoken), 1)
        self.assertNotIn("Sources", spoken[0])
        self.assertNotIn("https://", spoken[0])

    def test_a_pipeline_can_be_chosen(self):
        plan = {"subquestions": [{"question": "When did the Rivertown Bridge open to traffic?", "query": "Rivertown Bridge opened traffic"}], "needs_calculation": True}
        model = TR.Decompose.Model(plan, calc={"op": "weekday", "a": "2021-05-03"}, needles={"When did the Rivertown Bridge open to traffic?": "opened to traffic"})
        text = RC.run_research(self.core(model), "On which day of the week did the Rivertown Bridge open to traffic?", pipeline="research.decompose@1")
        self.assertIn("Monday", text)
        self.assertEqual(model.calls, ["plan", "answer", "calc", "compose"])

    def test_a_voice_that_fails_does_not_take_the_answer_away(self):
        def broken(text):
            raise OSError("no sound server")
        text = RC.run_research(self.core(TR.Scripted("reader")), "When did the Rivertown Bridge open to traffic?", speak=broken)
        self.assertIn("3 May 2021", text)

    def test_a_question_without_an_answer_is_said_honestly_and_not_spoken_as_fact(self):
        spoken = []
        text = RC.run_research(self.core(TR.Scripted("unknown")), "Who designed the Rivertown Bridge?", pipeline="research.baseline@1", speak=spoken.append)
        self.assertNotIn("Sources:", text)
        self.assertEqual(spoken, [])

    def test_a_search_that_cannot_be_reached_is_explained(self):
        from web_tools import SearchError

        def down(query, **kwargs):
            raise SearchError("searxng: connection refused; duckduckgo: timeout")
        tools = H.fixture_tools(WORLD)[0]
        tools["web_search"] = type(tools["web_search"])(down, None)
        with self.assertRaises(RuntimeError) as caught:
            RC.run_research(self.core(TR.Scripted("reader"), tools), "anything")
        self.assertIn("SearXNG", str(caught.exception))
        self.assertIn("connection refused", str(caught.exception))

    def test_stopping_gives_no_text(self):
        self.assertEqual(RC.run_research(self.core(TR.Scripted("reader")), "When did the Rivertown Bridge open to traffic?", should_stop=lambda: True), "")


class SearchFormatting(unittest.TestCase):
    RESULT = {"query": "eiffel tower", "backend": "searxng", "results": [
        {"title": "Eiffel Tower - Encyclopedia", "url": "https://encyclopedia.example/eiffel", "snippet": "completed on 31 March 1889"},
        {"title": "Tower facts", "url": "https://facts.example/tower", "snippet": ""},
        {"title": "Travel Guide", "url": "https://travel.example/paris", "snippet": "330 metres tall"}]}

    def test_numbered_results_with_title_address_and_snippet(self):
        text = RC.format_results(self.RESULT)
        self.assertTrue(text.startswith("Results for \u201ceiffel tower\u201d (searxng):"))
        self.assertIn("1. Eiffel Tower - Encyclopedia\n   https://encyclopedia.example/eiffel\n   completed on 31 March 1889", text)
        self.assertIn("2. Tower facts\n   https://facts.example/tower\n\n3.", text)

    def test_the_count_limits_the_list(self):
        text = RC.format_results(self.RESULT, count=2)
        self.assertIn("2. Tower facts", text)
        self.assertNotIn("3.", text)

    def test_markup_and_control_characters_from_the_web_cannot_come_through(self):
        evil = {"query": "q", "backend": "x", "results": [{"title": "**Bold** [click](javascript:alert(1)) <script>x</script>\x00\x1b", "url": "https://a.example/p",
                                                         "snippet": "# Heading\n> quote `code` | table | ![img](https://t.example/x.png)"}]}
        text = RC.format_results(evil)
        for char in ("\x00", "\x1b"):
            self.assertNotIn(char, text)
        for escaped in ("\\*\\*Bold\\*\\*", "\\[click\\]\\(javascript", "\\<script\\>", "\\# Heading", "\\!\\[img\\]\\(", "\\`code\\`"):
            self.assertIn(escaped, text)
        self.assertNotIn("<script>", text)

    def test_only_web_addresses_are_listed(self):
        odd = {"query": "q", "backend": "x", "results": [{"title": "a", "url": "javascript:alert(1)"}, {"title": "b", "url": "file:///etc/passwd"}, {"title": "c", "url": "https://ok.example/"}, "junk", {"url": 3}]}
        text = RC.format_results(odd)
        self.assertEqual(text.count("https://"), 1)
        self.assertNotIn("javascript", text)
        self.assertIn("1. c", text)
        self.assertIn("No usable results", RC.format_results({"query": "q", "results": [{"title": "a", "url": "ftp://x"}]}))

    def test_no_results_and_odd_answers(self):
        self.assertEqual(RC.format_results({"query": "zzz", "results": []}), "No results for \u201czzz\u201d.")
        for odd in (None, {}, "text", {"results": "x"}):
            self.assertTrue(RC.format_results(odd).startswith("No results"))

    def test_long_titles_and_snippets_are_cut(self):
        long = {"query": "q", "backend": "x", "results": [{"title": "word " * 100, "url": "https://a.example/", "snippet": "text " * 200}]}
        for line in RC.format_results(long).splitlines():
            self.assertLess(len(line), 260)


class SearchRun(unittest.TestCase):
    def test_the_search_tool_over_the_recorded_web(self):
        tools = H.fixture_tools(WORLD)[0]
        text = RC.run_search(tools["web_search"].func if hasattr(tools["web_search"], "func") else tools["web_search"][0], "Rivertown Bridge")
        self.assertIn("Results for \u201cRivertown Bridge\u201d", text)
        self.assertIn("https://gazette.rivertown.example/bridge-opens", text)

    def test_a_search_that_cannot_be_reached_is_explained(self):
        from web_tools import SearchError

        def down(query):
            raise SearchError("searxng: connection refused; duckduckgo: timeout")
        with self.assertRaises(RuntimeError) as caught:
            RC.run_search(down, "anything")
        self.assertIn("SearXNG", str(caught.exception))
        self.assertIn("connection refused", str(caught.exception))

    def test_stopping_gives_no_text_and_no_search(self):
        calls = []
        self.assertEqual(RC.run_search(lambda q: calls.append(q), "x", should_stop=lambda: True), "")
        self.assertEqual(calls, [])


class Routing(unittest.TestCase):
    def setUp(self):
        self.chat_log = importlib.import_module("MIA.chat_log")
        self.service_module = importlib.import_module("MIA.chat_service")
        self.moods = importlib.import_module("MIA.moods")
        self.tmp = tempfile.TemporaryDirectory()
        self.log = self.chat_log.ChatLog(os.path.join(self.tmp.name, "log.jsonl"))
        self.events, self.questions, self.chats, self.queries = [], [], [], []

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, research=True):
        def exchange(text, on_delta, on_emotion, should_stop):
            self.chats.append(text)
            on_delta("hello")
            return "hello"

        def run_research(question, on_delta, on_emotion, should_stop):
            self.questions.append(question)
            return "Answer.\n\nSources:\n- https://x.example: “q”"
        def run_search(query, on_delta, on_emotion, should_stop):
            self.queries.append(query)
            return "Results for \u201c%s\u201d (searxng):\n\n1. A title\n   https://x.example" % query
        return self.service_module.ChatService(lambda event, payload: self.events.append((event, payload)), self.log, self.moods.MoodTracker(MOODS), exchange,
                                               model_info=lambda: ("m", "light"), clock=time.monotonic, run_research=run_research if research else None,
                                               run_search=run_search if research else None)

    def idle(self, service):
        return wait_for(lambda: not service.status()["busy"])

    def test_the_command_runs_the_research_with_the_question_only(self):
        service = self.make()
        ack = service.send("/research how tall is the Eiffel Tower?")
        self.assertTrue(ack["ok"])
        self.assertTrue(self.idle(service))
        self.assertEqual((self.questions, self.chats), (["how tall is the Eiffel Tower?"], []))
        user, answer = self.log.history(limit=10)[0][-2:]
        self.assertEqual(user["text"], "/research how tall is the Eiffel Tower?")
        self.assertEqual((answer["role"], answer["task"]), ("assistant", "research"))
        self.assertIn("Sources:", answer["text"])
        start = [p for e, p in self.events if e == "chat_start"][0]
        self.assertEqual(start["task"], "research")

    def test_the_command_is_case_insensitive_and_keeps_line_breaks_of_the_question(self):
        service = self.make()
        service.send("/Research  two\nlines")
        self.assertTrue(self.idle(service))
        self.assertEqual(self.questions, ["two\nlines"])

    def test_search_shows_the_results_without_any_model(self):
        service = self.make()
        self.assertTrue(service.send("/search Eiffel Tower height")["ok"])
        self.assertTrue(self.idle(service))
        self.assertEqual((self.queries, self.questions, self.chats), (["Eiffel Tower height"], [], []))
        user, answer = self.log.history(limit=10)[0][-2:]
        self.assertEqual(user["text"], "/search Eiffel Tower height")
        self.assertEqual((answer["role"], answer["task"]), ("assistant", "search"))
        self.assertIn("Results for", answer["text"])
        self.assertEqual([p["task"] for e, p in self.events if e == "chat_start"], ["search"])

    def test_search_without_a_query_or_without_search_says_how_or_why(self):
        service = self.make()
        ack = service.send("/search")
        self.assertFalse(ack["ok"])
        self.assertIn("/search", ack["error"])
        self.assertEqual(self.queries, [])
        ack = self.make(research=False).send("/search cats")
        self.assertEqual((ack["ok"], ack["error"]), (False, "Search is not available."))

    def test_without_a_question_the_user_is_told_how(self):
        service = self.make()
        for bare in ("/research", "/research   "):
            ack = service.send(bare)
            self.assertFalse(ack["ok"])
            self.assertIn("/research", ack["error"])
        self.assertEqual((self.questions, len(self.log)), ([], 0))

    def test_a_server_without_research_says_so(self):
        service = self.make(research=False)
        ack = service.send("/research anything")
        self.assertEqual((ack["ok"], ack["error"]), (False, "Research is not available."))

    def test_other_messages_never_start_a_research(self):
        service = self.make()
        for text in ("how tall is the Eiffel Tower?", "please research this for me", "research: cats", "//research x", "/researcher x", "/searcher x", "search for cats", "/searching x"):
            service.send(text)
            self.assertTrue(self.idle(service))
        self.assertEqual((self.questions, self.queries), ([], []))
        self.assertEqual(len(self.chats), 8)

    def test_the_command_is_listed_for_the_palette(self):
        entry = [c for c in self.service_module.COMMANDS if c["command"].startswith("/research")]
        self.assertEqual(len(entry), 1)
        self.assertFalse(entry[0]["confirm"])
        self.assertFalse(self.make().is_command("/research"))

    def test_a_failure_of_the_research_is_reported_like_a_failure_of_the_chat(self):
        service = self.make()
        service._run_research = lambda *a: (_ for _ in ()).throw(RuntimeError("The web search is not reachable (x)."))
        service.send("/research anything")
        self.assertTrue(self.idle(service))
        self.assertIn("chat_error", [e for e, _ in self.events])
        error = [p for e, p in self.events if e == "chat_error"][0]
        self.assertIn("web search is not reachable", error["message"])


if __name__ == "__main__":
    unittest.main()
