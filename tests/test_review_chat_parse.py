"""TC-WFM-019 (REQ-WFM-019): the review waits for the user's answer; the user's reply to a question of the review is read by code
Run with: python tests/test_review_chat_parse.py"""
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from extensions.review.review_chat import parse_request, parse_reply


class TestParse(unittest.TestCase):
    def test_request_with_a_date(self):
        self.assertEqual(parse_request("Do canary releases help? until 2024-06-30"), ("Do canary releases help?", "2024-06-30"))
        self.assertEqual(parse_request("Is X true? UNTIL 2020-01-02 "), ("Is X true?", "2020-01-02"))

    def test_request_without_a_date(self):
        self.assertEqual(parse_request("  Do canary releases help?  "), ("Do canary releases help?", None))
        self.assertEqual(parse_request("until the end of time"), ("until the end of time", None))

    def test_yes_words(self):
        for word in ["yes", "Y", "OK.", "Okay!", "go", "continue", "sure", "ja", "ALL"]:
            self.assertEqual(parse_reply(word), {"answer": "yes", "items": []})

    def test_no_words(self):
        for word in ["no", "N", "stop.", "none", "Nein!", "cancel"]:
            self.assertEqual(parse_reply(word), {"answer": "no", "items": []})

    def test_a_list_is_split_and_cleaned(self):
        self.assertEqual(parse_reply('"canary release", failed rollout;  \nbig-bang release,,'), {"answer": "items", "items": ["canary release", "failed rollout", "big-bang release"]})

    def test_long_items_are_dropped_and_the_list_is_capped(self):
        self.assertEqual(parse_reply("a" * 61 + ", ok item"), {"answer": "items", "items": ["ok item"]})
        items = ", ".join("k%d" % i for i in range(20))
        self.assertEqual(len(parse_reply(items)["items"]), 12)


if __name__ == '__main__':
    unittest.main()
