"""
Findings of the Verify of G-V3.REPORT (V-1, V-2, V-3; task T-06, REQ-WFM-139, 140, 141): the name of a report that the files volume takes for any question, an address with balanced parentheses
that stays whole, and addresses that are no web addresses (ftp, mail, www) that no Markdown reader can make a link of, in the runtime report, in the /review report and in the /lookup and /search reports.
Run with the MIA virtualenv: python tests/test_run_report_hardening.py
"""
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))

import research_chat                                         # noqa: E402
import run_report as R                                       # noqa: E402
from chat_log import ChatLog                                 # noqa: E402
from chat_service import ChatService                         # noqa: E402
from extensions.review import review_chat as rc              # noqa: E402
from file_store import FileStore                             # noqa: E402
from moods import MoodTracker                                # noqa: E402
from skill_runs import SkillRunRecorder                      # noqa: E402
from skill_runs_fakes import FakeClock, FakeSkillRunStorage  # noqa: E402
from task_registry import Task, TaskRegistry                 # noqa: E402

OTHER_ADDRESSES = ["ftp://files.example/x", "FTP://FILES.EXAMPLE/x", "a@b.example", "mailto:a@b.example", "www.evil.example/x", "WWW.EVIL.EXAMPLE", "see www.evil.example."]


def reachable(text):
    """True where a Markdown reader could still make a link of an address in the (escaped) text: a scheme with //, an at sign or a www. that is not written with a backslash"""
    return bool(re.search(r"(?<!\\):(?=//)|(?<!\\)@|www\.", text, re.I))


class NameOfTheReport(unittest.TestCase):
    def test_a_long_word_in_the_question_gives_a_name_the_files_volume_takes(self):
        """V-1: a question with one very long word (a long address) gives a report name that the files volume takes.
        Example: a question that is one word of 130 letters gives `lookup-2026-11-17-<the word cut>.md` of at most 100 characters."""
        # Given: questions with a very long word, with many long words, with only punctuation and with nothing
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        store = FileStore(folder)
        for question in ("x" * 130, " ".join(["abcdefghij" * 5] * 8), "?!?! ...", "", None, "https://example.org/" + "a" * 200):
            # When: the report is named and stored
            name = R.report_name("lookup", "2026-11-17", question)
            # Then: the name is short and the volume takes it
            self.assertLessEqual(len(name), 100, question)
            self.assertTrue(name.startswith("lookup-2026-11-17-") and name.endswith(".md"), name)
            store.put(name, "# Done\n")


class AddressesInTheReport(unittest.TestCase):
    def test_balanced_parentheses_stay_in_the_address(self):
        """V-3: an address with balanced parentheses is one link, a parenthesis that closes the sentence is not part of it.
        Example: `https://en.wikipedia.org/wiki/Foo_(bar)` stays whole, `(see https://a.example/x)` ends the link before the `)`."""
        # Given: addresses with and without balanced parentheses, and with sentence punctuation
        # When / Then: the links are written as the reader should take them
        self.assertEqual(R.link_addresses("https://en.wikipedia.org/wiki/Foo_(bar)"), "<https://en.wikipedia.org/wiki/Foo_(bar)>")
        self.assertEqual(R.link_addresses("see https://en.wikipedia.org/wiki/Foo_(bar) now"), "see <https://en.wikipedia.org/wiki/Foo_(bar)> now")
        self.assertEqual(R.link_addresses("(see https://a.example/x)"), "\\(see <https://a.example/x>\\)")
        self.assertEqual(R.link_addresses("https://a.example/x."), "<https://a.example/x>.")
        self.assertEqual(R.link_addresses("https://a.example/x, and"), "<https://a.example/x>, and")


class OtherAddressesCannotBecomeLinks(unittest.TestCase):
    def test_the_runtime_report_defangs_ftp_mail_and_www(self):
        """V-2: in the report of the runtime an ftp address, a mail address and a www address are text that no Markdown reader can make a link of.
        Example: `a@b.example` is written `a\\@b.example`, `ftp://x` is `ftp\\://x`, `www.x` is `www\\.x`."""
        for text in OTHER_ADDRESSES:
            self.assertFalse(reachable(R.escape(text)), R.escape(text))
            self.assertFalse(reachable(R.link_addresses(text)), R.link_addresses(text))
        self.assertEqual(R.escape("a@b.example"), "a\\@b.example")
        self.assertEqual(R.escape("see www.x.example"), "see www\\.x.example")
        # And: an http address is still the one link
        self.assertEqual(R.link_addresses("https://ok.example/a and www.evil.example"), "<https://ok.example/a> and www\\.evil.example")

    def test_the_review_report_defangs_them_too(self):
        """V-2: the escape of the /review report (titles, notes, keywords) leaves no ftp, mail or www address that could become a link.
        Example: the title `Contact a@b.example or www.evil.example` has escaped at sign and dot."""
        for text in OTHER_ADDRESSES:
            self.assertFalse(reachable(rc._md(text)), rc._md(text))
        self.assertEqual(rc._md("Smith & Jones (2020)"), "Smith & Jones (2020)")          # the minimal set stays minimal for everything else

    def test_the_lookup_and_search_reports_defang_them_too(self):
        """V-2: the text of a source in the /lookup report and of a result in the /search text leaves no ftp, mail or www address that could become a link.
        Example: the quote `write to a@b.example` has an escaped at sign."""
        # Given: an answer with a source whose quote and title hold such addresses, and a search result with a title and a snippet that do
        answer = {"answer": "see www.evil.example", "status": "answered", "sources": [{"url": "https://a.example/", "quote": "write to a@b.example or ftp://x.example", "title": "www.evil.example"}]}
        result = {"results": [{"title": "www.evil.example", "url": "https://a.example/x", "snippet": "mail a@b.example"}]}
        # When: the report of the lookup and the text of the search are made
        report = research_chat.format_report("question with a@b.example", answer)
        text = research_chat.format_results(result)
        # Then: no address that is not an http or https address is left to link (the one source address is the link)
        self.assertFalse(reachable(report.replace("<https://a.example/>", "")), report)
        self.assertFalse(reachable(re.sub(r"https?://\S+", "", text)), text)


class ALongQuestionStillGetsItsReport(unittest.TestCase):
    def test_a_run_whose_question_is_one_long_word_ends_with_a_report(self):
        """V-1 (REQ-WFM-139, 140): a /lookup-like run whose question is one very long word still has a report that the record names.
        Example: the question `x` times 130 gives a report file and `report` in the record."""
        # Given: the real chat service with a scripted skill and the real files volume
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        events, clock = [], FakeClock()
        files, recorder = FileStore(os.path.join(folder, "files")), None
        recorder = SkillRunRecorder(FakeSkillRunStorage(), lambda event, payload: None, clock=clock.monotonic, now=clock.now)
        tasks = TaskRegistry()
        tasks.register(Task("lookup", lambda argument, on_delta, on_emotion, should_stop: "found it", "A scripted skill", "your question", "/lookup a question", needs=(), version="1"))
        chat = ChatService(lambda event, payload: events.append((event, payload)), ChatLog(os.path.join(folder, "log.jsonl")), MoodTracker(os.path.join(REPO, "moods.json")),
                           lambda *args: "", queue_size=5, spawn=lambda target: target(), clock=lambda: 100.0, tasks=tasks, recorder=recorder, files=files)
        # When: it runs with a question of one very long word
        chat.send("/lookup " + "x" * 130, sender="anna", author="anna")
        run = [payload["id"] for event, payload in events if event == "chat_done"][-1]
        # Then: the record names a report that is in the volume
        record = recorder.record(run)
        self.assertTrue(record["report"], "the record of the run names no report")
        self.assertIn(record["report"], [entry["name"] for entry in files.list()])


if __name__ == "__main__":
    unittest.main()
