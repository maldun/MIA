"""
The run report of /review (REQ-WFM-139, G-V3.REPORT T-02): the review hands the report that the chat shows to the runtime, next to its .md and .tex files, and a report that cannot be handed
over does not take the review away. Scripted skills, a fake scholar and a scripted user as in test_review_chat.py; the last test runs the whole chain with the real chat service and files volume.
Run with the MIA virtualenv: python tests/test_review_report.py
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from extensions.review import review_chat as rc  # noqa: E402
import test_review_chat as T          # noqa: E402  (the scripted skills, the fake scholar, the works, the scripted user)
import test_review_chain as Chain     # noqa: E402  (the real chat service with the real extension)


def first_line(path):
    with open(path, encoding="utf-8") as handle:
        return handle.readline().strip()


class ReportOfAReview(unittest.TestCase):
    def test_the_report_the_chat_shows_is_handed_over_once(self):
        """TC-WFM-139: the text handed to `run_report` is the report of the chat, once.
        Example: the review of "How to schedule?" hands over a text that starts with `## Literature review` and is what the result starts with."""
        # Given: a scripted review with one question to the user and a place that takes the report
        handed = []
        # When: it runs to its end
        out, _calls, _events, _searcher = T.review(T.Conversation("yes", "no"), files=None, reports=None, run_report=handed.append)
        # Then: exactly one report is handed over, and the chat text starts with it
        self.assertEqual(len(handed), 1)
        self.assertTrue(handed[0].startswith("## Literature review"))
        head = out.split("\n\n### How the works were selected")[0]            # A-160, REQ-WFM-142: the result is the head of the report and its flow count
        self.assertTrue(handed[0].startswith(head))

    def test_a_report_that_cannot_be_handed_over_does_not_take_the_review_away(self):
        """TC-WFM-139: a failing `run_report` leaves the report in the chat text with a note.
        Example: run_report raises "report store full": the result still starts with `## Literature review` and names the reason."""
        # Given: a place for the report that fails
        def broken(markdown):
            raise RuntimeError("report store full")
        # When: the review runs to its end
        out, _calls, _events, _searcher = T.review(T.Conversation("yes", "no"), run_report=broken)
        # Then: the report is in the result and the reason is told
        self.assertTrue(out.startswith("## Literature review"))
        self.assertIn("report store full", out)

    def test_without_a_place_for_the_report_the_review_runs_as_before(self):
        """TC-WFM-139: a review whose caller asks for no run report (run_report None) gives the same text as before.
        Example: no run_report: the result starts with `## Literature review` and has no note."""
        # Given / When: the review runs without a place for the report
        out, _calls, _events, _searcher = T.review(T.Conversation("yes", "no"))
        # Then: no note about a report is in the result
        self.assertTrue(out.startswith("## Literature review"))
        self.assertNotIn("could not be handed over", out)


class HostileTitles(unittest.TestCase):
    def test_a_title_from_a_scholarly_source_cannot_become_a_link_or_markup_in_the_report(self):
        """TC-WFM-141 (red-team case for /review, finding F-1 of T-02, decided by the owner 2026-11-16: T-02b): a work whose title is `[x](javascript:alert(1)) <img ...>` leaves no live link or tag in the report.
        Example: the title is written with escaped brackets and angle brackets, so `[x](...)` and `<img ...>` are only characters."""
        # Given: a scholarly source that returns a hostile title
        works = [T.work("10.1/a", "[x](javascript:alert(1)) <img src=x onerror=alert(1)>")]
        # When: the review runs to its end and hands over its report
        handed = []
        T.review(T.Conversation("yes", "no"), works=works, run_report=handed.append)
        text = re.sub(r"\\.", "", handed[0])
        # Then: no link target and no tag is live
        self.assertNotIn("](", text)
        self.assertNotIn("<img", text.lower())


BAD = "[x](javascript:alert(1)) <img src=x onerror=alert(1)>"
FLOW = {"found": 9, "duplicates": 2, "dropped": 1, "screened": 6, "included": 4, "maybe": 1, "excluded_abstract": 1, "excluded_full": 0, "undecided": 0}


def a_report(title="A title", note="a note", reason="a reason", keyword="canary", gap="a gap", point="a point"):
    """a finished report with the text of every kind that comes from outside, as the review gives it"""
    work = {"title": title, "doi": "10.1/a", "grade": 3, "abstract_only": False, "notes": [note], "decision": "include", "reason": reason}
    return {"ended_by": "complete", "flow": dict(FLOW), "keywords": [{"keyword": keyword, "origin": "user", "hits": 3}], "gaps": [keyword],
            "works": [work, dict(work, title=title + " (excluded)", decision="exclude")], "dropped": [{"work": {"title": title, "doi": "10.1/d"}, "reason": reason}],
            "summary": {"coverage": BAD, "figures": {"level": "moderate", "included": 4}, "found": [{"point": point, "works": ["10.1/a"]}], "gaps": [{"gap": gap, "works": []}], "dropped_points": 0}}


def inert(text):
    """the text as a Markdown reader sees it: a backslash-escaped character is only a character"""
    return re.sub(r"\\.", "", text)


class EscapedOutsideText(unittest.TestCase):
    def test_a_usual_title_stays_readable_in_the_report(self):
        """TC-WFM-141: only backslash, brackets and angle brackets are escaped; a title with an ampersand, parentheses, an underscore and asterisks is in the report unchanged.
        Example: "Smith & Jones (2020): a_b *c*" is in the chat report and in the file as it is."""
        # Given: a report with a usual title
        title = "Smith & Jones (2020): a_b *c*"
        # When: the report of the chat and the file are made
        chat, full = rc.format_report(a_report(title=title), "How to schedule?", "2026-01-01"), rc.format_report_full(a_report(title=title), "How to schedule?", "2026-01-01")
        # Then: the title is in both as it is
        self.assertIn("**%s** (10.1/a" % title, chat)
        self.assertIn("**%s** (10.1/a" % title, full)

    def test_brackets_and_angle_brackets_are_written_with_a_backslash(self):
        """TC-WFM-141: `[`, `]`, `<`, `>` and a backslash of a title are written with a backslash in front.
        Example: the title "a [b] <c> \\d" is written as `a \\[b\\] \\<c\\> \\\\d`."""
        # Given: a title with the characters that can start a link or a tag
        report = a_report(title="a [b] <c> \\d")
        # When: the report is made
        text = rc.format_report(report, "q", "2026-01-01")
        # Then: each is written with a backslash in front
        self.assertIn("**a \\[b\\] \\<c\\> \\\\d**", text)

    def test_hostile_text_of_every_kind_leaves_no_link_or_tag_in_the_chat_report(self):
        """TC-WFM-141: hostile text in a note, a reason of a dropped work, a keyword, the question, a point and a gap of the summary leaves no live link and no tag in the report of the chat.
        Example: the note `[x](javascript:alert(1)) <img ...>` is only characters."""
        # Given: a report whose notes, reasons, keywords and summary hold the hostile text
        report = a_report(title=BAD, note=BAD, reason=BAD, keyword=BAD, gap=BAD, point=BAD)
        # When: the report of the chat is made
        text = inert(rc.format_report(report, BAD, "2026-01-01"))
        # Then: no link target and no tag is live
        self.assertNotIn("](", text)
        self.assertNotIn("<img", text.lower())
        # And: the table of keywords keeps its shape (one row for the one keyword)
        self.assertEqual(len([line for line in text.splitlines() if line.startswith("| ") and "canary" not in line and "Keyword" not in line]), 1)

    def test_hostile_text_leaves_no_link_or_tag_in_the_file_either(self):
        """TC-WFM-141: the file holds the report of the chat and every screened work with its reason; hostile text in a title or a reason leaves no live link and no tag there.
        Example: the reason `[x](javascript:alert(1)) <img ...>` of an excluded work is only characters."""
        # Given: a report with hostile titles and reasons
        report = a_report(title=BAD, note=BAD, reason=BAD, keyword=BAD, gap=BAD, point=BAD)
        # When: the file is made
        text = inert(rc.format_report_full(report, BAD, "2026-01-01"))
        # Then: no link target and no tag is live in it, also below the line of all screened works
        self.assertNotIn("](", text)
        self.assertNotIn("<img", text.lower())
        self.assertIn("### All screened works", text)


class ChainOfAReview(Chain.Chain):
    """the real chat service, extension and files volume: the run report of a review is a third file after the .md and .tex of the review"""

    def test_the_run_report_of_a_review_is_a_file_that_names_the_state_and_holds_the_report(self):
        """TC-WFM-139: after a review through the real chain the record names a report file whose first line is `# Done` and that holds the review report.
        Example: the file starts with `# Done`, then the blank line, then `## Literature review`."""
        # Given: the real chain with scripted skills; When: a review runs to its end
        self.run_review()
        run = self.chat.shown_run("anna")
        # Then: the record names a report that is one of its files
        self.assertIsInstance(run["report"], str)
        self.assertIn(run["report"], run["files"])
        path = self.files.path(run["report"])
        # And: its first line names the state and the review report follows
        self.assertEqual(first_line(path), "# Done")
        with open(path, encoding="utf-8") as handle:
            self.assertIn("\n\n## Literature review", handle.read())


for _name in [n for n in dir(Chain.Chain) if n.startswith("test_")]:
    setattr(ChainOfAReview, _name, None)            # the tests of the chain run in their own file; here only the new one


if __name__ == "__main__":
    unittest.main()
