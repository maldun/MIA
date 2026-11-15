"""
Unit tests of the first Verify run of G-V3.CHAT (findings F-01 to F-04, F-08, F-09 of verification-report.md): the live path of a task through ChatService (a question is a skill turn,
a failed or stopped run, a recorder or a repair that raises, the phases of the entry), the wiring of web_app.py and the removal of markup in the digest step.
Run with: python tests/test_chat_verify_fixes.py
"""
import ast
import os
import re
import shutil
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from chat_log import ChatLog                                 # noqa: E402
from chat_service import ChatService                         # noqa: E402
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
        """F-03: a storage error in the recorder never stops the status messages or the summary.
        Example: recorder.phase raises: the chat still holds "Collecting." and the summary."""
        # Given: a recorder whose phase raises and a skill with one declared phase
        def runs(argument, on_delta, on_emotion, should_stop, monitor):
            monitor.update(phase="collect")
            return "Done"
        chat, _, _ = chat_with(self, runs, recorder_phase_raises=True)
        # When: the user starts the skill
        chat.send("/go x", sender="anna", author="anna")
        # Then: the status message and the summary are in the chat
        self.assertEqual([r["text"] for r in mia(chat)][0], "Collecting.")
        self.assertEqual([r.get("kind") for r in mia(chat)], ["phase", "done"])

    @mark.req("REQ-CHA-041", "REQ-WFM-039")
    def test_without_declared_phases_the_phases_of_the_entry_count(self):
        """F-03: a service that has no `declared_phases` uses the phases of the entry (run_phases).
        Example: entry phases ("collect",): one status message "Collecting." and the summary."""
        # Given: a service without declared_phases and an entry that declares collect
        def runs(argument, on_delta, on_emotion, should_stop, monitor):
            monitor.update(phase="collect")
            return "Done"
        chat, _, _ = chat_with(self, runs, phases=("collect",), declared=None)
        # When: the user starts the skill
        chat.send("/go x", sender="anna", author="anna")
        # Then: the phase is told and the summary follows
        self.assertEqual([r.get("kind") for r in mia(chat)], ["phase", "done"])

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
        """TC-CHA-070 (A-152, F-06): the step of the app runs on the model profile light, the pin of the evals, for a status, a summary, a failure and a stop message.
        Example: a status call and a summary call both reach the chat function with profile="light"."""
        # Given: the live step on a recording chat function and a persona provider
        seen = []

        def chat(messages, profile=None):
            seen.append(profile)
            return "ok"
        step = LiveDigest(chat, lambda: "You are MIA.")
        # When: the four wordings are asked
        step.status("collect"), step.summary("result"), step.failure("why"), step.stopped("who")
        # Then: every call named the profile light
        self.assertEqual(seen, ["light"] * 4)

    @mark.req("REQ-CHA-066")
    def test_a_link_to_a_run_in_a_status_message_of_the_model_is_cut(self):
        """TC-CHA-071 (A-152, F-10): a link of the form of the run link is removed from every message the step words, a status message too.
        Example: "Fine [Open in the Skill run view](#run=evil) bye" gives "Fine  bye" (the link only at the end messages, added by code)."""
        # Given: a skill with one declared phase whose status wording holds a link
        def runs(argument, on_delta, on_emotion, should_stop, monitor):
            monitor.update(phase="collect")
            return "Done"
        chat, spoken, _ = chat_with(self, runs, replies={"collect": "Fine [Open in the Skill run view](#run=evil) bye", "Done": "All done."})
        # When: the user starts it
        chat.send("/go x", sender="anna", author="anna")
        # Then: the status message and its speech hold no link, the summary ends with the real one
        records = mia(chat)
        self.assertNotIn("#run=evil", records[0]["text"])
        self.assertFalse([s for s in spoken if "Skill run view" in s])
        self.assertTrue(records[1]["text"].endswith("(#run=%s)" % records[1]["id"]))


class SecondVerifyRun(unittest.TestCase):
    """findings F-15, F-16, F-18 and the observations of the second Verify run (verification-report-run2.md)"""

    def run_ids(self, text):
        return [m.group(0) for m in re.finditer(r"#run=[^)\s]*", text, re.I)]

    @mark.req("REQ-CHA-066")
    def test_a_run_link_that_is_built_from_what_is_left_is_cut_too(self):
        """F-15: the cut repeats until nothing changes and covers nested brackets, capitals and a space; no `#run=` is left in a message or its speech except the real link.
        Example: `Fine [a](#ru[b](#run=1)n=evil) bye`, `[a [b]](#run=evil)`, `[a](#RUN=evil)`, `[a]( #run=evil)`."""
        for hostile in ("Fine [a](#ru[b](#run=1)n=evil) bye", "Fine [a [b]](#run=evil) bye", "Fine [a](#RUN=evil) bye", "Fine [a]( #run=evil) bye", "Fine [a](<#run=evil>) bye"):
            # Given: a skill with one phase whose status wording holds the hostile link and whose summary holds it too
            def runs(argument, on_delta, on_emotion, should_stop, monitor):
                monitor.update(phase="collect")
                return "Done"
            chat, spoken, _ = chat_with(self, runs, replies={"collect": hostile, "Done": hostile})
            # When: the run is started
            chat.send("/go x", sender="anna", author="anna")
            # Then: the status message and all speech hold no run link; the summary holds only the real one, once
            records = mia(chat)
            self.assertEqual(self.run_ids(records[0]["text"]), [], hostile)
            self.assertEqual(self.run_ids(" ".join(spoken)), [], hostile)
            self.assertEqual(self.run_ids(records[1]["text"]), ["#run=%s" % records[1]["id"]], hostile)

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
        step = LiveDigest(lambda messages, profile=None: seen.append(messages[0]["content"]) or "ok", lambda: personas.pop(0))
        # When: two messages are worded
        step.status("x"), step.status("y")
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


if __name__ == "__main__":
    unittest.main()
