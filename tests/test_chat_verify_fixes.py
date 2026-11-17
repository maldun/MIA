"""
Unit tests of the first Verify run of G-V3.CHAT (findings F-01 to F-04, F-08, F-09 of verification-report.md): the live path of a task through ChatService (a question is a skill turn,
a failed or stopped run, a recorder or a repair that raises, the phases of the entry), the wiring of web_app.py and the removal of markup in the digest step.
Run with: python tests/test_chat_verify_fixes.py
"""
import ast
import html
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from chat_log import ChatLog                                 # noqa: E402
from chat_service import ChatService, clean_model_text, cut_run_links    # noqa: E402
from fake_model import FakeModel                             # noqa: E402
from markers import mark                                     # noqa: E402
from moods import MoodTracker                                # noqa: E402
from skill_digest import LiveDigest, SkillDigestStep         # noqa: E402
from skill_runs import SkillRunRecorder                      # noqa: E402
from skill_runs_fakes import FakeClock, FakeSkillRunStorage  # noqa: E402
from task_registry import Task, TaskRegistry                 # noqa: E402

PHASES = ("collect", "rank")


def chat_with(test, run, needs=("monitor",), phases=None, declared=PHASES, repair=None, recorder_phase_raises=False, replies=None, spawn=None):
    """a ChatService with a recorder, a digest step on a fake model and one task `go` that does `run`; returns (chat, spoken, recorder)"""
    folder = tempfile.mkdtemp()
    test.addCleanup(shutil.rmtree, folder, True)
    clock, spoken = FakeClock(), []
    recorder = SkillRunRecorder(FakeSkillRunStorage(), lambda event, payload: None, clock=clock.monotonic, now=clock.now)
    if recorder_phase_raises:
        def broken(*args, **kwargs):
            raise RuntimeError("storage down")
        recorder.phase = broken
    tasks = TaskRegistry()
    tasks.register(Task("go", run, "A skill", "your question", "/go a question", needs=needs, version="1", **({"phases": phases} if phases else {})))
    model = FakeModel(replies or {"collect": "Collecting.", "rank": "Ranking.", "Done": "All done.", "boom": "It failed.", "user": "It was stopped.", "result": "All done."})
    chat = ChatService(lambda event, payload: None, ChatLog(os.path.join(folder, "log.jsonl")), MoodTracker(os.path.join(REPO, "moods.json")), lambda *args: "",
                       queue_size=5, spawn=spawn or (lambda target: target()), clock=lambda: 100.0, tasks=tasks, recorder=recorder, digest=SkillDigestStep(model),
                       declared_phases=(lambda run_id: declared) if declared is not None else None, repair=repair,
                       speak=lambda sentence, should_stop: spoken.append(sentence), review_timeout=5)
    return chat, spoken, recorder


def mia(chat):
    return [r for r in chat.log.history(limit=200)[0] if r["role"] == "assistant"]


class TaskThroughTheChat(unittest.TestCase):
    def wait_for(self, chat, condition):
        for _ in range(200):
            if condition(mia(chat)):
                return
            time.sleep(0.05)
        self.fail("the chat never reached the expected state: %r" % [r["text"] for r in mia(chat)])

    @mark.req("REQ-CHA-040", "REQ-CHA-045", "REQ-CHA-046")
    def test_a_question_of_a_skill_is_a_spoken_skill_turn_and_its_answer_is_in_the_history(self):
        """F-01: a question that a running skill asks is a message of kind question, sent to speech once; the answer follows it in the history for the chat model.
        Example: the skill asks "Which topic?", the user answers "quantum": records kind question; history "Which topic?" then "quantum"."""
        # Given: a skill that asks one question and ends with the answer
        def asks(argument, on_delta, on_emotion, should_stop, ask, monitor):
            return "Done " + ask("Which topic?")
        chat, spoken, _ = chat_with(self, asks, needs=("ask", "monitor"), spawn=lambda target: threading.Thread(target=target, daemon=True).start())     # as in the app: the run is a background task
        # When: the user starts it and answers the question from the page
        chat.send("/go x", sender="anna", author="anna")
        self.wait_for(chat, lambda records: any(r["text"] == "Which topic?" for r in records))
        chat.send("quantum", sender="anna", author="anna")
        self.wait_for(chat, lambda records: any(r.get("kind") == "done" for r in records))
        # Then: the question record is a skill turn of kind question, spoken once
        question = next(r for r in mia(chat) if r["text"] == "Which topic?")
        self.assertEqual(question.get("kind"), "question")
        self.assertEqual(sum(1 for sentence in spoken if "Which topic?" in sentence), 1)
        # And: the chat model sees the question and then the answer
        texts = [m["text"] for m in chat.model_history()]
        self.assertEqual(texts[:2], ["Which topic?", "quantum"])

    @mark.req("REQ-CHA-044", "REQ-CHA-043")
    def test_a_failing_skill_gives_one_failed_message_with_the_link(self):
        """F-03: a skill that raises leaves one message of kind failed with status error, the wording of the step and the link; no phase message before it.
        Example: the skill raises "boom early": "It failed." plus the link of the run."""
        # Given: a skill that raises before its first phase
        def raises(argument, on_delta, on_emotion, should_stop, monitor):
            raise RuntimeError("boom early")
        chat, _, _ = chat_with(self, raises)
        # When: the user starts it
        chat.send("/go x", sender="anna", author="anna")
        # Then: one failed message with the wording of the step and the link
        records = mia(chat)
        self.assertEqual([(r.get("kind"), r["status"]) for r in records], [("failed", "error")])
        self.assertEqual(records[0]["text"], "It failed. [Open in the Skill run view](#run=%s)" % records[0]["id"])

    @mark.req("REQ-CHA-057")
    def test_a_stopped_skill_gives_one_stopped_message(self):
        """F-03: a skill that is stopped leaves one message of kind stopped.
        Example: the skill calls stop, then returns: kind stopped, "It was stopped." and the link."""
        # Given: a skill that stops the service while it runs
        holder = {}

        def stops(argument, on_delta, on_emotion, should_stop, monitor):
            holder["chat"].stop()
            return "partial"
        chat, _, _ = chat_with(self, stops)
        holder["chat"] = chat
        # When: the user starts it
        chat.send("/go x", sender="anna", author="anna")
        # Then: one stopped message
        records = mia(chat)
        self.assertEqual([r.get("kind") for r in records], ["stopped"])
        self.assertTrue(records[0]["text"].startswith("It was stopped."))

    @mark.req("REQ-CHA-041", "REQ-WFM-136")
    def test_a_recorder_that_raises_on_a_phase_does_not_take_the_messages_with_it(self):
        """F-03: a storage error in the recorder never stops the end message (A-156: a phase is no chat message).
        Example: recorder.phase raises: the chat still holds the summary."""
        # Given: a recorder whose phase raises and a skill with one declared phase
        def runs(argument, on_delta, on_emotion, should_stop, monitor):
            monitor.update(phase="collect")
            return "Done"
        chat, _, _ = chat_with(self, runs, recorder_phase_raises=True)
        # When: the user starts the skill
        chat.send("/go x", sender="anna", author="anna")
        # Then: the summary is in the chat
        self.assertEqual([r.get("kind") for r in mia(chat)], ["done"])

    @mark.req("REQ-CHA-041", "REQ-WFM-039")
    def test_without_declared_phases_the_phases_of_the_entry_count(self):
        """F-03: a service that has no `declared_phases` uses the phases of the entry (run_phases).
        Example: entry phases ("collect",): no chat message for the phase, the summary only."""
        # Given: a service without declared_phases and an entry that declares collect
        def runs(argument, on_delta, on_emotion, should_stop, monitor):
            monitor.update(phase="collect")
            return "Done"
        chat, _, _ = chat_with(self, runs, phases=("collect",), declared=None)
        # When: the user starts the skill
        chat.send("/go x", sender="anna", author="anna")
        # Then: the phase is no chat message, the summary is
        self.assertEqual([r.get("kind") for r in mia(chat)], ["done"])

    @mark.req("REQ-CHA-043", "REQ-CHA-058")
    def test_the_message_of_a_run_with_a_digest_step_comes_once_at_the_end(self):
        """F-03: the result of the run is not streamed into the chat: no delta event carries it, the one message holds the wording.
        Example: a skill that streams "partial result" gives no chat_delta with that text."""
        # Given: a skill that streams a partial result
        events = []

        def streams(argument, on_delta, on_emotion, should_stop, monitor):
            on_delta("partial result")
            return "Done"
        chat, _, _ = chat_with(self, streams)
        chat._emit = lambda event, payload: events.append((event, payload))
        # When: the user starts it
        chat.send("/go x", sender="anna", author="anna")
        # Then: no delta event carries the partial result
        self.assertFalse([p for e, p in events if e == "chat_delta" and "partial result" in p.get("text", "")])

    @mark.req("REQ-CHA-047", "REQ-CHA-060")
    def test_a_repair_that_raises_leaves_a_closed_run_and_a_message(self):
        """F-08: a repair that raises must not leave a run record that stays running or a message id that stays set.
        Example: repair raises ZeroDivisionError: the record is ended and the chat holds one message."""
        # Given: a skill that ends at once and a repair that raises
        def runs(argument, on_delta, on_emotion, should_stop, monitor):
            return "Done"
        chat, _, recorder = chat_with(self, runs, repair=lambda text: 1 / 0)
        # When: the user starts it
        chat.send("/go x", sender="anna", author="anna")
        # Then: the message id is free, one message is in the chat and its run is closed
        self.assertIsNone(chat._message_id)
        records = mia(chat)
        self.assertEqual(len(records), 1)
        run = records[0]["skill_run"]
        self.assertNotEqual(recorder.record(run)["state"], "running")


class WebAppWiring(unittest.TestCase):
    @mark.req("REQ-CHA-046", "REQ-CHA-059")
    def test_the_chat_model_gets_the_history_of_the_skill_runs(self):
        """F-02: web_app.py hands `chat_service.model_history` to the communicator (`comm.skill_history`), and the service gets the digest step.
        Example: the source holds comm.skill_history = chat_service.model_history and digest=LiveDigest(...)."""
        # Given: the source of web_app.py (importing it would start the app)
        tree = ast.parse(open(os.path.join(REPO, "web_app.py"), encoding="utf-8").read())
        # When: its assignments to skill_history are read
        sets = [n for n in ast.walk(tree) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Attribute) and t.attr == "skill_history" for t in n.targets)]
        # Then: the communicator gets the history of the service and the service the digest step
        self.assertTrue(sets, "comm.skill_history is never set")
        self.assertEqual(ast.unparse(sets[0].value), "chat_service.model_history")
        self.assertIn("digest=LiveDigest(", open(os.path.join(REPO, "web_app.py"), encoding="utf-8").read())


def step_saying(*texts):
    replies = list(texts)
    return SkillDigestStep(lambda messages: replies.pop(0) if len(replies) > 1 else replies[0])


class MarkupRemoval(unittest.TestCase):
    @mark.req("REQ-CHA-064")
    def test_a_tag_built_from_what_is_left_is_removed_too(self):
        """F-04: the removal repeats until nothing changes, so a tag that the removal itself would rebuild does not survive.
        Example: `<<b>script>alert(1)<</b>/script>` gives a text without `<script`."""
        for hostile in ("<<b>script>alert(1)<</b>/script>", "<scr<b>ipt>alert(1)</scr<b>ipt>", "<<i><b>img src=x>"):
            text = step_saying(hostile).failure("x")
            self.assertNotRegex(text.lower(), r"</?[a-z!]", hostile)

    @mark.req("REQ-CHA-064")
    def test_the_name_of_a_script_or_style_element_is_taken_in_any_case(self):
        """F-09: `<STYLE>p{}</STYLE>x` gives `x`, `<Script>a()</SCRIPT>y` gives `y`.
        Example: those two."""
        self.assertEqual(step_saying("<STYLE>p{}</STYLE>x").failure("r"), "x")
        self.assertEqual(step_saying("<Script>a()</SCRIPT>y").failure("r"), "y")

    @mark.req("REQ-CHA-064")
    def test_comparisons_are_not_tags(self):
        """F-09: `5 < 6 and 7 > 3` is not a tag and stays as it is.
        Example: that sentence."""
        self.assertEqual(step_saying("5 < 6 and 7 > 3").failure("r"), "5 < 6 and 7 > 3")

    @mark.req("REQ-CHA-064")
    def test_many_unclosed_script_tags_cost_little(self):
        """F-05: 64 000 characters of `<script>` are handled within one second.
        Example: '<script>' * 8000."""
        started = time.monotonic()
        step_saying("<script>" * 8000).failure("r")
        self.assertLess(time.monotonic() - started, 1.0)


class StepModelAndLinks(unittest.TestCase):
    @mark.req("REQ-CHA-065")
    def test_every_call_of_the_step_asks_for_the_light_profile(self):
        """TC-CHA-070 (A-152, F-06): the step of the app runs on the model profile light, the pin of the evals, for a summary, a failure and a stop message.
        Example: a status call and a summary call both reach the chat function with profile="light"."""
        # Given: the live step on a recording chat function and a persona provider
        seen = []

        def chat(messages, profile=None, options=None):
            seen.append(profile)
            return "ok"
        step = LiveDigest(chat, lambda: "You are MIA.")
        # When: the three wordings are asked
        step.summary("result"), step.failure("why"), step.stopped("who")
        # Then: every call named the profile light
        self.assertEqual(seen, ["light"] * 3)

    @mark.req("REQ-CHA-066")
    def test_a_link_to_a_run_in_an_end_message_of_the_model_is_cut(self):
        """TC-CHA-071 (A-152, F-10; A-156: no status message any more): a link of the form of the run link is removed from the wording of the step; the end message ends with the real one.
        Example: "Fine [Open in the Skill run view](#run=evil) bye" gives "Fine  bye" (the link only at the end messages, added by code)."""
        # Given: a skill whose summary wording holds a link
        def runs(argument, on_delta, on_emotion, should_stop, monitor):
            return "Done"
        chat, spoken, _ = chat_with(self, runs, replies={"Done": "Fine [Open in the Skill run view](#run=evil) bye"})
        # When: the user starts it
        chat.send("/go x", sender="anna", author="anna")
        # Then: the message and its speech hold no foreign link, the summary ends with the real one
        records = mia(chat)
        self.assertNotIn("#run=evil", records[0]["text"])
        self.assertFalse([s for s in spoken if "Skill run view" in s])
        self.assertTrue(records[0]["text"].endswith("(#run=%s)" % records[0]["id"]))


class SecondVerifyRun(unittest.TestCase):
    """findings F-15, F-16, F-18 and the observations of the second Verify run (verification-report-run2.md)"""

    def run_ids(self, text):
        return [m.group(0) for m in re.finditer(r"#run=[^)\s]*", text, re.I)]

    @mark.req("REQ-CHA-066")
    def test_a_run_link_that_is_built_from_what_is_left_is_cut_too(self):
        """F-15: the cut repeats until nothing changes and covers nested brackets, capitals and a space; no `#run=` is left in a message or its speech except the real link.
        Example: `Fine [a](#ru[b](#run=1)n=evil) bye`, `[a [b]](#run=evil)`, `[a](#RUN=evil)`, `[a]( #run=evil)`."""
        for hostile in ("Fine [a](#ru[b](#run=1)n=evil) bye", "Fine [a [b]](#run=evil) bye", "Fine [a](#RUN=evil) bye", "Fine [a]( #run=evil) bye", "Fine [a](<#run=evil>) bye"):
            # Given: a skill whose summary holds the hostile link
            def runs(argument, on_delta, on_emotion, should_stop, monitor):
                return "Done"
            chat, spoken, _ = chat_with(self, runs, replies={"Done": hostile})
            # When: the run is started
            chat.send("/go x", sender="anna", author="anna")
            # Then: all speech holds no run link; the summary holds only the real one, once
            records = mia(chat)
            self.assertEqual(self.run_ids(" ".join(spoken)), [], hostile)
            self.assertEqual(self.run_ids(records[0]["text"]), ["#run=%s" % records[0]["id"]], hostile)

    @mark.req("REQ-CHA-066")
    def test_a_link_in_a_failure_or_stop_message_is_cut_and_the_real_one_follows(self):
        """F-18: failed and stopped wordings are cut like the others, also when the repair itself adds a link.
        Example: the failure wording holds [x](#run=evil): the message ends with the real link once."""
        def raises(argument, on_delta, on_emotion, should_stop, monitor):
            raise RuntimeError("boom")
        # Given: a failing skill whose wording has a link, and a repair that adds another
        chat, spoken, _ = chat_with(self, raises, replies={"boom": "It failed [x](#run=evil)."}, repair=lambda text: text + " [y](#run=evil2)")
        # When: the user starts it
        chat.send("/go x", sender="anna", author="anna")
        # Then: one run link in the message, the real one, and none in the speech
        record = mia(chat)[0]
        self.assertEqual(self.run_ids(record["text"]), ["#run=%s" % record["id"]])
        self.assertEqual(self.run_ids(" ".join(spoken)), [])

    @mark.req("REQ-CHA-064")
    def test_markup_nested_deeper_than_any_fixed_number_of_rounds_is_removed(self):
        """F-16: the removal stops when nothing changes, not after a fixed number of rounds.
        Example: a tag hidden 25 levels deep leaves no tag; `<script><script>a</script>b</script>c` gives `bc`."""
        # Given: a tag hidden 25 levels deep, nested script elements and 1 MB of unclosed script tags
        deep = "<scr" + "<b" * 25 + ">" * 25 + "ipt>alert(1)"
        # When: the step returns them
        out = step_saying(deep).failure("r")
        # Then: no tag is left, the nested elements go whole and the cost stays small
        self.assertNotRegex(out.lower(), r"</?[a-z!]")
        self.assertEqual(step_saying("<script><script>a</script>b</script>c").failure("r"), "bc")
        started = time.monotonic()
        step_saying("<script>" * 125000).failure("r")
        self.assertLess(time.monotonic() - started, 2.0)

    @mark.req("REQ-CHA-008")
    def test_the_persona_is_read_at_every_call(self):
        """F-18: a persona saved on the page counts for the next message.
        Example: the provider says A, then B: the second call carries B."""
        # Given: a live step whose persona provider answers A, then B
        personas, seen = ["A", "B"], []
        step = LiveDigest(lambda messages, profile=None, options=None: seen.append(messages[0]["content"]) or "ok", lambda: personas.pop(0))
        # When: two messages are worded
        step.failure("x"), step.failure("y")
        # Then: each call carries the persona of its time
        self.assertTrue(seen[0].startswith("A") and seen[1].startswith("B"))

    @mark.req("REQ-CHA-041", "REQ-WFM-136")
    def test_a_phase_turn_that_raises_does_not_stop_the_run(self):
        """F-03, F-18: if the chat cannot add a status message, the run still ends with its summary.
        Example: post_assistant raises for kind phase; the summary is in the chat."""
        def runs(argument, on_delta, on_emotion, should_stop, monitor):
            monitor.update(phase="collect")
            return "Done"
        # Given: a chat that fails to add a status message
        chat, _, _ = chat_with(self, runs)
        original = chat.post_assistant

        def failing(text, **fields):
            if fields.get("kind") == "phase":
                raise OSError("log down")
            return original(text, **fields)
        chat.post_assistant = failing
        # When: the user starts the run
        chat.send("/go x", sender="anna", author="anna")
        # Then: the summary is there
        self.assertEqual([r.get("kind") for r in mia(chat)], ["done"])

    @mark.req("REQ-CHA-040")
    def test_a_question_that_cannot_be_posted_leaves_no_waiter_behind(self):
        """F-18 (observation): if the question cannot be added, the next message of the author is not swallowed as an answer.
        Example: post_assistant raises in ask; _waiter is None afterwards."""
        # Given: a skill that asks and a chat whose log is down
        def asks(argument, on_delta, on_emotion, should_stop, ask, monitor):
            return ask("Which topic?")
        chat, _, _ = chat_with(self, asks, needs=("ask", "monitor"))
        chat.post_assistant = lambda text, **fields: (_ for _ in ()).throw(OSError("log down"))
        # When: the run asks its question
        chat.send("/go x", sender="anna", author="anna")
        # Then: no waiter is left behind
        self.assertIsNone(chat._waiter)


class ThirdVerifyRun(unittest.TestCase):
    """findings F-19 to F-24 of the third Verify run (verification-report-run3.md): the end of both cuts fails closed"""

    @mark.req("REQ-CHA-066")
    def test_a_link_with_an_encoded_destination_is_not_left_to_the_page(self):
        """F-19: an HTML character reference in a link destination decodes to `#run=` in the browser, so what the cut leaves must not decode to it.
        Example: `[x](&#35;run=e)`, `[x](&#x23;run=e)`, `[x](&num;run=e)`, `[x](#&#114;un=e)`, `[x](#run&#61;e)`, `[r]: &#35;run=e`."""
        for hostile in ("A [x](&#35;run=e) B", "A [x](&#x23;run=e) B", "A [x](&num;run=e) B", "A [x](#&#114;un=e) B", "A [x](#run&#61;e) B", "A [x](<&#35;run=e>) B", "A\n\n[r]: &#35;run=e\n\n[x][r]"):
            # Given: a wording with the encoded link
            # When: the links of the model are cut
            out = cut_run_links(hostile)
            # Then: nothing in it decodes to a run link
            self.assertNotIn("#run=", html.unescape(out).lower(), hostile)

    @mark.req("REQ-CHA-066")
    def test_the_rest_of_a_cut_is_made_plain_even_when_no_link_form_matches(self):
        """F-24: three levels of brackets and a destination with its own parenthesis leave no `#run=`.
        Example: `[x [y [z]]](#run=e)` and `[a](#run=e(1))`."""
        for hostile in ("[x [y [z]]](#run=e)", "[a](#run=e(1))", "plain #run=e text"):
            self.assertNotIn("#run=", html.unescape(cut_run_links(hostile)).lower(), hostile)

    @mark.req("REQ-CHA-066")
    def test_the_cut_of_degenerate_text_costs_little(self):
        """F-20: 40 000 blanks and a chain of 4000 joined links are handled within one second each.
        Example: ' ' * 40000 + 'x'; '[a](#ru' * 4000 + '[b](#run=1)' + 'n=e)' * 4000."""
        # Given: three degenerate texts of tens of thousands of characters
        for hostile in (" " * 40000 + "x", "[a](#ru" * 4000 + "[b](#run=1)" + "n=e)" * 4000, "[a" * 40000):
            started = time.monotonic()
            # When: the links are cut
            # Then: no run link is left and it took under one second
            self.assertNotIn("#run=", html.unescape(cut_run_links(hostile)).lower())
            self.assertLess(time.monotonic() - started, 1.0)

    @mark.req("REQ-CHA-064")
    def test_deeply_nested_tags_cost_little_and_leave_no_tag(self):
        """F-21: `<a` repeated 8000 times, a letter and 8000 `>`: no tag is left and it takes under one second.
        Example: that text."""
        # Given: a text of 8000 nested tag openings and as many closings
        started = time.monotonic()
        # When: the step returns it
        out = step_saying("<a" * 8000 + "b" + ">" * 8000).failure("r")
        # Then: no tag is left and it took under one second
        self.assertNotRegex(out.lower(), r"</?[a-z!]")
        self.assertLess(time.monotonic() - started, 1.0)

    @mark.req("REQ-CHA-064")
    def test_the_text_after_a_script_element_stays_for_every_kind_of_letter(self):
        """F-22: a letter whose lower case is longer (the dotted capital I) in front of a script element does not move the cut.
        Example: `\u0130\u0130\u0130\u0130<script>a</script>KEEP` gives the four letters and KEEP; a second script after eight of them loses its content."""
        # Given: the dotted capital I before one script element, and eight of them before two
        # When: the step returns the texts
        # Then: the text after the script stays and the content of the second script goes
        self.assertEqual(step_saying("\u0130" * 4 + "<script>a</script>KEEP").failure("r"), "\u0130" * 4 + "KEEP")
        out = step_saying("\u0130" * 8 + "<script>a</script><script>EVIL</script>KEEP").failure("r")
        self.assertNotIn("EVIL", out)
        self.assertTrue(out.endswith("KEEP"))

    @mark.req("REQ-CHA-064")
    def test_an_end_tag_with_attributes_or_a_slash_closes_the_element(self):
        """F-23: `</script foo>` and `</script/>` end a script element like `</script>`.
        Example: `<script>a</script foo>b` and `<script>a</script/>b` give `b`."""
        self.assertEqual(step_saying("<script>a</script foo>b").failure("r"), "b")
        self.assertEqual(step_saying("<script>a</script/>b").failure("r"), "b")


def seen_by_a_browser(text):
    """what the page makes of a text before it looks at a link: entities decoded, backslash escapes of punctuation resolved, tab and newline dropped by the URL parser, lower case"""
    text = html.unescape(text)
    text = re.sub(r"\\(?=[!-/:-@\[-`{-~])", "", text)
    return re.sub(r"[\t\n\r]", "", text).lower()


class FourthVerifyRun(unittest.TestCase):
    """findings F-25 to F-32 of the fourth Verify run (verification-report-run4.md): the guarantee is by construction, at the end of the cleaning of a model text"""

    HOSTILE_LINKS = (r"A [x](#run\=evil) B", r"A [x](<#run\=evil>) B", "A\n\n[r]: #run\\=evil\n\n[x][r]", r"A [x](#r&#117;n\=e) B", "A [x](#ru&#10;n=e) B", "A [x](#ru&#9;n=e) B", "A [x](&#35;RUN=e) B",
                     "A [x](#run=e) B", "A [x](&#35;run=e) B", "see #RUN=e", "A [a](#ru[b](#run=1)n=e) B")

    @mark.req("REQ-CHA-066")
    def test_no_form_of_a_run_link_survives_the_cleaning(self):
        """F-25, F-31: a backslash escape, a tab or a newline in the destination, an entity, capitals: nothing that a browser reads as `#run=` is left.
        Example: `[x](#run\\=evil)` and `[x](#ru&#10;n=e)`."""
        for hostile in self.HOSTILE_LINKS:
            self.assertNotIn("#run=", seen_by_a_browser(clean_model_text(hostile)), hostile)

    @mark.req("REQ-CHA-066")
    def test_ordinary_text_with_an_ampersand_is_not_touched(self):
        """F-25 (mutant gap): the fail-closed rewrite fires only for a text that holds a run link.
        Example: `Tom & Jerry <3 5 < 6` stays as it is."""
        self.assertEqual(clean_model_text("Tom & Jerry 5 < 6 and 7 > 3"), "Tom & Jerry 5 < 6 and 7 > 3")

    @mark.req("REQ-CHA-066")
    def test_a_link_that_is_built_from_parts_is_cut_whole(self):
        """F-26 (mutant gap): the nicer path removes a joined link completely.
        Example: `[a](#ru[b](#run=1)n=e)` gives an empty text."""
        self.assertEqual(clean_model_text("[a](#ru[b](#run=1)n=e)"), "")

    @mark.req("REQ-CHA-064", "REQ-CHA-066")
    def test_cutting_a_link_cannot_rebuild_a_tag_and_cutting_a_tag_cannot_rebuild_a_link(self):
        """F-26: the cleaning joins nothing that either cut would remove.
        Example: `<[x](#run=1)script>EVIL</[x](#run=1)script>` leaves no tag and no `EVIL` as markup; `[x](#ru<b>n=e)` leaves no run link."""
        out = clean_model_text("<[x](#run=1)script>EVIL</[x](#run=1)script>")
        self.assertNotRegex(out, r"<[A-Za-z!/]")
        self.assertNotIn("#run=", seen_by_a_browser(clean_model_text("[x](#ru<b>n=e)")))

    @mark.req("REQ-CHA-064")
    def test_a_tag_with_a_less_than_sign_in_an_attribute_is_not_left_as_a_tag(self):
        """F-27: after the cleaning no `<` is followed by a letter, `!` or `/`.
        Example: `<script a="<">alert(1)`, `<b title="<">x</b>`, `<svg onload="<">`, `<!-- unclosed`."""
        for hostile in ('<script a="<">alert(1)', '<b title="<">x</b>', '<img src="/x" alt="<">', '<svg onload="<">', "x <!-- unclosed", "<script a=<>alert(1)</script>"):
            self.assertNotRegex(step_saying(hostile).failure("r"), r"<[A-Za-z!/]", hostile)

    @mark.req("REQ-CHA-064")
    def test_letters_that_match_a_script_name_only_in_unicode_do_not_break_the_step(self):
        """F-28: `<\u017fcript>` (long s), `<scr\u0130pt>` and `<scr\u0131pt>` are no script tags and raise nothing.
        Example: step_saying("<\u017fcript>x</script>y") returns text."""
        for hostile in ("<\u017fcript>x</script>y", "<scr\u0130pt>x", "<scr\u0131pt>x", "<\u017ftyle>x"):
            self.assertIsInstance(step_saying(hostile).failure("r"), str)

    @mark.req("REQ-CHA-064")
    def test_a_run_of_blanks_costs_little_in_the_markup_removal(self):
        """F-29: 100 000 blanks and 100 000 tabs take under one second.
        Example: ' ' * 100000, '\t' * 100000."""
        # Given: 100 000 blanks and 100 000 tabs
        for hostile in (" " * 100000, "\t" * 100000):
            started = time.monotonic()
            # When: the step returns them
            step_saying(hostile).failure("r")
            # Then: it took under one second
            self.assertLess(time.monotonic() - started, 1.0)

    @mark.req("REQ-CHA-056")
    def test_the_real_link_stays_clickable_after_text_that_ends_in_an_open_block(self):
        """F-30: a comment or a code fence that the model leaves open must not swallow the link that code adds.
        Example: `x` then `<!--`, and `x` then an open fence."""
        # Given: a summary that ends in an open comment and one that ends in an open code fence
        for ending in ("x\n\n<!--", "Done\n\n```\ncode"):
            def runs(argument, on_delta, on_emotion, should_stop, monitor, ending=ending):
                return "Done"
            chat, _, _ = chat_with(self, runs, replies={"Done": ending})
            # When: the run ends
            chat.send("/go x", sender="anna", author="anna")
            text = mia(chat)[0]["text"]
            # Then: the block is closed and the message ends with the real link
            self.assertNotIn("<!--", text)
            self.assertEqual(text.count("```") % 2, 0, text)
            self.assertTrue(text.endswith("(#run=%s)" % mia(chat)[0]["id"]))

    @mark.req("REQ-CHA-064", "REQ-CHA-066")
    def test_degenerate_texts_cost_little_in_both_cuts(self):
        """F-20, F-29 (mutant gaps): `[a][` repeated 30 000 times, `[x](#run=` repeated 11 000 times, 100 000 `<script ` take under one second each.
        Example: those texts."""
        # Given: three degenerate texts
        for hostile in ("[a][" * 30000, "[x](#run=" * 11000, "<script " * 12500):
            started = time.monotonic()
            # When: the model text is cleaned
            clean_model_text(hostile)
            # Then: it took under one second
            self.assertLess(time.monotonic() - started, 1.0)

    @mark.req("REQ-CHA-064")
    def test_the_nesting_boundary_and_the_ends_of_the_removal(self):
        """F-32 and mutant gaps: nesting 8 and 9 deep leaves no tag and no lost `5 < 6`; style end tags with attributes; comments and doctype go; a capital left-over of a run link is plain.
        Example: `5 < 6 ` then 9 nested openings; `<style>a</style foo>b`; `<!-- x -->y`."""
        # Given: nested openings 7 to 10 deep behind a comparison
        # When: the step returns them
        # Then: no tag is left and the comparison stays; the end tags, the comment and the capital left-over behave
        for depth in (7, 8, 9, 10):
            out = step_saying("5 < 6 " + "<a" * depth + "b" + ">" * depth).failure("r")
            self.assertNotRegex(out, r"<[A-Za-z!/]")
            self.assertIn("5 < 6", out)
        self.assertEqual(step_saying("<style>a</style foo>b").failure("r"), "b")
        self.assertEqual(step_saying("<!-- x -->y").failure("r"), "y")
        self.assertNotIn("#run=", seen_by_a_browser(clean_model_text("see #RUN=e")))


class FifthVerifyRun(unittest.TestCase):
    """findings F-33 to F-37 of the fifth Verify run (verification-report-run5.md): the cleaning never raises, and the real link is always a paragraph of its own"""

    FENCE_OPENER = re.compile(r"^[ >*+\-]*(`{3,}|~{3,})", re.M)

    @mark.req("REQ-CHA-064", "REQ-CHA-066")
    def test_the_cleaning_returns_text_for_every_text(self):
        """F-33: a character reference with more than 4300 digits made `int()` raise inside the cleaning.
        Example: `a &#` + 5000 digits + `;` gives a text, and the run ends with its message."""
        # Given: texts that make the standard library raise
        for hostile in ("a &#" + "1" * 5000 + ";", "a &#" + "1" * 5000, "&#x" + "f" * 5000 + ";", "&#" * 3000):
            # When: they are cleaned
            out = clean_model_text(hostile)
            # Then: the result is a text without a way to a run link
            self.assertIsInstance(out, str)
            self.assertNotIn("#run=", seen_by_a_browser(out))

    @mark.req("REQ-CHA-043", "REQ-CHA-044")
    def test_a_run_whose_summary_holds_such_a_reference_still_ends_with_its_message(self):
        """F-33: the end of the run is outside any guard, so a failing cleaning must not leave the run open.
        Example: the summary `All done &#` + 5000 digits + `;`: one done message with the link, the observer closed."""
        def runs(argument, on_delta, on_emotion, should_stop, monitor):
            return "Done"
        # Given: a run whose summary holds the long reference
        chat, _, _ = chat_with(self, runs, replies={"Done": "All done &#" + "1" * 5000 + ";"})
        # When: the user starts it
        chat.send("/go x", sender="anna", author="anna")
        # Then: one done message that ends with the real link, the run is closed
        records = mia(chat)
        self.assertEqual([r.get("kind") for r in records], ["done"])
        self.assertTrue(records[0]["text"].endswith("(#run=%s)" % records[0]["id"]))
        self.assertIsNone(chat._observer)
        self.assertIsNone(chat._message_id)

    @mark.req("REQ-CHA-056")
    def test_the_real_link_is_a_paragraph_of_its_own_after_any_block(self):
        """F-34: an open fence, an indented code block, a quote, a list or a table must not swallow the link: it ends the text, no fence can open before it, and an indented line or a table row is separated from it by a blank line.
        Example: `x` + a fence + `code`, `~~~`, four backticks, `> ` + a fence, a list item with a fence, an indented line, a table row."""
        for ending in ("x\n```\ncode", "x\n~~~\ncode", "x\n````\ncode", "x\n```js\ncode", "> ```\n> code", "- ```\n  code", "x\n\n    code", "| a |\n|---|\n| 1 |"):
            def runs(argument, on_delta, on_emotion, should_stop, monitor, ending=ending):
                return "Done"
            # Given: a summary that ends in the block
            chat, spoken, _ = chat_with(self, runs, replies={"Done": ending})
            # When: the run ends
            chat.send("/go x", sender="anna", author="anna")
            text = mia(chat)[0]["text"]
            # Then: no fence can open before the link, the link ends the text, and an indented line or a table row is separated from it by a blank line
            link = "[Open in the Skill run view](#run=%s)" % mia(chat)[0]["id"]
            self.assertTrue(text.endswith(link), repr(ending))
            self.assertIsNone(self.FENCE_OPENER.search(text), repr(ending))
            if ending.startswith(("x\n\n    ", "| a")):
                self.assertTrue(text.endswith("\n\n" + link), repr(ending))

    @mark.req("REQ-CHA-064")
    def test_a_question_mark_after_the_angle_bracket_is_markup_too(self):
        """F-35: a browser reads `<?` as a comment and marked passes it on as a raw block.
        Example: `x` then `<?` and `<?x>y` leave no `<?`."""
        for hostile in ("x\n\n<?", "<?x>y", "<? a ?> text"):
            self.assertNotIn("<?", clean_model_text(hostile), hostile)

    @mark.req("REQ-CHA-056")
    def test_the_id_of_the_run_is_encoded_in_the_link(self):
        """F-36: a run id with a space or a parenthesis must not break the link.
        Example: id `a b)` gives `#run=a%20b%29`; the usual id is unchanged."""
        def runs(argument, on_delta, on_emotion, should_stop, monitor):
            return "Done"
        # Given: a chat and two run ids, one with a space and a parenthesis
        chat, _, _ = chat_with(self, runs)
        # When: the end message of each run is made
        text, _ = chat._turn_text("a b)", "done", "x")
        # Then: the odd id is percent-encoded and the usual id is unchanged

        self.assertTrue(text.endswith("(#run=a%20b%29)"), text)
        self.assertTrue(chat._turn_text("01794783217634342-fc25", "done", "x")[0].endswith("(#run=01794783217634342-fc25)"))

    @mark.req("REQ-CHA-064", "REQ-CHA-066")
    def test_the_last_strip_and_the_order_of_the_two_nets_matter(self):
        """F-37 (mutants that survived): tags and links built from several joined parts are gone at the end, in either order of discovery.
        Example: `<[x](#ru<[x](#ru<[x](#run=1)b>n=1)b>n=1)b>` leaves no `<b`; the same shape with links leaves no run link."""
        # Given: tags and links that are built from several joined parts, a `</b` without `>` and a carriage return in a destination
        tags = "<[x](#ru<[x](#ru<[x](#run=1)b>n=1)b>n=1)b>"
        links = "[x](#ru<[x](#ru<[x](#ru<[x](#run=1)b>n=1)b>n=1)b>n=1)"
        # When: they are cleaned
        # Then: no tag and no way to a run link is left
        self.assertNotRegex(clean_model_text(tags), r"<[A-Za-z!/?]")
        self.assertNotIn("#run=", seen_by_a_browser(clean_model_text(links)))
        self.assertNotRegex(clean_model_text("a </b"), r"<[A-Za-z!/?]")
        for hostile in ("[x](#ru&#13;n=e)", "[x](#ru\rn=e)"):
            self.assertNotIn("#run=", seen_by_a_browser(clean_model_text(hostile)), hostile)


class Margin(unittest.TestCase):
    @mark.req("REQ-CHA-050")
    def test_a_tokenizer_that_counts_five_percent_more_still_stays_below_the_limit(self):
        """F-09: the calls stay below 95 % of the limit, so a count of the caller that is 5 % higher is still within 4096 tokens.
        Example: a result of 80 000 characters, the step counts len // 4, the check counts 1.05 times that."""
        # Given: a step on a fake model that answers short digests
        model = FakeModel(lambda messages: "digest " * 50)
        step = SkillDigestStep(model, count_tokens=lambda text: max(1, len(text) // 4))
        # When: a result of 80 000 characters is summarized
        step.summary("word " * 16000)
        # Then: every call is within 4096 tokens counted 5 % higher
        self.assertTrue(model.calls)
        self.assertLessEqual(max(model.sizes(lambda text: int(len(text) / 4 * 1.05) + 1)), 4096)


class RunSpeaksOnce(unittest.TestCase):
    @mark.req("REQ-CHA-067")
    def test_a_service_with_recorder_and_digest_step_has_end_messages(self):
        """A-156: `has_end_messages` is what the voice rule of the app asks; it is true only where the run ends with a message of the Chat agent.
        Example: recorder and digest step -> True; neither -> False."""
        # Given: a service with a recorder and a digest step, and one without both
        with_digest, _, _ = chat_with(self, lambda argument, on_delta, on_emotion, should_stop, monitor: "Done")
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        plain = ChatService(lambda event, payload: None, ChatLog(os.path.join(folder, "log.jsonl")), MoodTracker(os.path.join(REPO, "moods.json")), lambda *args: "", spawn=lambda target: target())
        # When / Then: only the first has end messages
        self.assertTrue(with_digest.has_end_messages())
        self.assertFalse(plain.has_end_messages())

    @mark.req("REQ-CHA-067")
    def test_a_run_through_the_chat_is_spoken_once_by_its_end_message(self):
        """A-156: a skill that speaks its answer through the voice rule of the app is silent where the run has end messages; the summary is the one spoken text.
        Example: the skill asks speaker_for for its voice, gets None, and the recorded speech is "All done." only."""
        # Given: a skill that would speak its answer through the voice rule, wired to the service as the app does
        from workflow_voice import speaker_for
        holder, own = [], []

        def runs(argument, on_delta, on_emotion, should_stop, monitor):
            voice = speaker_for({}, "go", own.append, end_messages=holder[0].has_end_messages())
            if voice is not None:
                voice("the whole answer")
            return "the whole answer"
        chat, spoken, _ = chat_with(self, runs, replies={"the whole answer": "All done."})
        holder.append(chat)
        # When: the user starts it
        chat.send("/go x", sender="anna", author="anna")
        # Then: the skill said nothing itself, the end message was spoken once
        self.assertEqual(own, [])
        self.assertEqual(spoken, ["All done."])

    @mark.req("REQ-CHA-041")
    def test_an_unchanged_phase_is_noted_once_by_the_observer(self):
        """A-156: the same phase twice in a row reaches the recorder once; a phase that returns later is noted again.
        Example: collect, collect, rank, collect -> collect, rank, collect."""
        # Given: an observer over a recorder that lists the phases it was told
        from skill_run_observer import SkillRunObserver
        noted = []
        recorder = types.SimpleNamespace(start=lambda *a, **k: None, phase=lambda run, text: noted.append(text))
        observer = SkillRunObserver(recorder, "r1", "go", 1, "anna", phases=PHASES)
        # When: the phases come in
        for phase in ("collect", "collect", "rank", "collect"):
            observer.phase(phase)
        # Then: a repeat in a row is noted once
        self.assertEqual(noted, ["collect", "rank", "collect"])


if __name__ == "__main__":
    unittest.main()
