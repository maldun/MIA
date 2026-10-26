"""TC-CHA-014 (REQ-CHA-014), the part that code can check: a violation of a behaviour rule is repaired silently, BEFORE the page sees it. The stream is held back to the last
settled point (a sentence or line end without an open emphasis, code or bracket span), what is released is repaired, and the answer is repaired as a whole at the end; so
every text the page ever gets is a prefix of the final repaired text, nothing is shown and taken back, no message tells about the correction, and the correction is not part
of any message. The signal in the run log is made by web_app (behaviour.record_signals, on the text the model wrote). That the detectors keep their precision and recall
(AC-25) is the eval on eval/suites/behaviour, not decided here. Run with: python tests/test_chat_repair.py"""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

import behaviour                                          # noqa: E402
from markers import mark                                  # noqa: E402
from chat_log import ChatLog                              # noqa: E402
from chat_service import ChatService, settled             # noqa: E402
from moods import MoodTracker                             # noqa: E402

CASES = os.path.join(ROOT, "eval", "suites", "behaviour", "cases.jsonl")      # read only: the protected cases are only used as input texts


def suite_texts():
    with open(CASES, encoding="utf-8") as fp:
        return [(case["id"], case["input"]["text"]) for case in map(json.loads, fp) if isinstance(case.get("input", {}).get("text"), str)]


def repair(text):
    return behaviour.apply_rules(text)["text"]


class StreamTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.events, self.tick = [], [0.0]
        self.log = ChatLog(os.path.join(self.dir, "log.jsonl"))

    def service(self, raw, step, repair_with=repair, lookup=None):
        def stream(text, on_delta, on_emotion, should_stop):
            for end in range(step, len(raw) + step, step):
                on_delta(raw[:end])
            return raw

        def clock():
            self.tick[0] += 1.0                           # every delta passes the throttle of 20 per second
            return self.tick[0]

        return ChatService(lambda event, payload: self.events.append((event, payload)), self.log, MoodTracker(os.path.join(ROOT, "moods.json")), stream, spawn=lambda t: t(),
                           clock=clock, repair=repair_with, run_lookup=lookup)

    def shown(self):
        deltas = [p["text"] for e, p in self.events if e == "chat_delta"]
        done = [p["text"] for e, p in self.events if e == "chat_done"]
        return deltas, done[-1] if done else None

    @mark.req("REQ-CHA-014")
    def test_nothing_uncorrected_is_ever_shown(self):
        """for every text of the behaviour suite, at three chunk sizes: each delta the page gets is a prefix of the final repaired text, the deltas only grow, and the final
        text is the repair of the whole text"""
        for case_id, raw in suite_texts():
            for step in (1, 4, 11):
                with self.subTest(case=case_id, step=step):
                    self.events.clear()
                    self.service(raw, step).send("hi", author="anna")
                    deltas, final = self.shown()
                    self.assertEqual(final, repair(raw))
                    for delta in deltas:
                        self.assertTrue(final.startswith(delta), "%r is shown but is not part of %r" % (delta, final))
                    for before, after in zip(deltas, deltas[1:]):
                        self.assertTrue(after.startswith(before))
                    self.assertEqual(self.log.last("assistant")["text"], final)

    @mark.req("REQ-CHA-014")
    def test_the_repair_is_silent(self):
        """no message about the correction: the log has the question and the repaired answer, the page got no note and no error"""
        raw = "This is **really** important. It is 2*3 here."
        self.assertNotEqual(repair(raw), raw)                              # the test means something: there is a violation to repair
        self.service(raw, 5).send("hi", author="anna")
        self.assertEqual([(m["role"], m["text"]) for m in self.log.history(limit=50)[0]], [("user", "hi"), ("assistant", repair(raw))])
        self.assertNotIn("chat_error", [e for e, _ in self.events])
        self.assertEqual([p["role"] for e, p in self.events if e == "chat_message"], ["user"])

    @mark.req("REQ-CHA-014")
    def test_a_clean_text_still_streams_sentence_by_sentence(self):
        """holding back is limited to the unsettled tail: the first sentence reaches the page while the second is still being written"""
        self.service("The first sentence is done. The second is still being wri", 4).send("hi", author="anna")
        self.assertIn("The first sentence is done.", self.shown()[0])
        self.assertEqual(self.shown()[1], "The first sentence is done. The second is still being wri")

    @mark.req("REQ-CHA-014")
    def test_without_a_repair_function_the_text_is_streamed_as_before(self):
        self.service("This is **bold**.", 3, repair_with=None).send("hi", author="anna")
        deltas, final = self.shown()
        self.assertEqual(final, "This is **bold**.")
        self.assertIn("This is **bo", deltas)                              # the raw text, as it came (3 characters per step)

    @mark.req("REQ-CHA-014")
    def test_lookup_answers_with_quotes_are_not_repaired(self):
        quote = "He wrote: **never** do this *really*."
        service = self.service("", 1, lookup=lambda text, on_delta, on_emotion, should_stop: quote)
        service.send("/lookup what did he write", author="anna")
        self.assertEqual(self.log.last("assistant")["text"], quote)

    @mark.req("REQ-CHA-014")
    def test_settled_is_the_prefix_that_no_rule_can_still_change(self):
        for text, expected in (("Hello there. I *wa", "Hello there."), ("Hi **bo", ""), ("One. Two! Three? Fo", "One. Two! Three?"), ("Line one\nline tw", "Line one"),
                               ("Done. See `code. here", "Done."), ("Done. (smiles", "Done."), ("No end here", ""), ("Pure *action* here. And", "Pure *action* here."),
                               ("", "")):
            with self.subTest(text=text):
                self.assertEqual(settled(text), expected)


if __name__ == "__main__":
    unittest.main()
