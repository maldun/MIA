"""Chat agent N-2.2 T-04, the parts without a model (D-78): the records of the structured memory (TC-CHA-011 structure), no record from untrusted text (TC-CHA-012, exact),
retrieval within a token budget with abstention. The writer step that produces the candidates is a model step and is measured on the dev cases of
specs/mia/eval-drafts/memory_sample.jsonl, not here. Run with: python tests/test_memory_records.py"""
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark                                  # noqa: E402
from memory_records import MemoryRecords, MemoryRefused, tokens   # noqa: E402
from storage import Storage                               # noqa: E402
from storage_files import FileBackend                     # noqa: E402

DAY = 86400
START = 1767571200          # 2026-01-05 00:00 UTC


class MemoryTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.now = START
        self.storage = Storage(FileBackend(os.path.join(self.dir, "db")))
        self.memory = MemoryRecords(self.storage, clock=lambda: self.now, budget_tokens=40)

    def add(self, items, source_kind="user", account="anna", message_id="m1"):
        return self.memory.add(account, message_id, items, source_kind)

    def stored(self):
        return [self.storage.get("memory", i)["doc"] for i in self.storage.ids("memory")]

    @mark.req("REQ-CHA-011")
    def test_a_record_has_kind_text_source_subject_and_times_and_the_text_is_kept(self):
        text = "Zoë  allergic to\tpeanuts ✓"
        [record_id] = self.add([{"kind": "fact", "text": text}], message_id="m42")
        doc = self.storage.get("memory", record_id)["doc"]
        self.assertEqual((doc["kind"], doc["text"], doc["source"], doc["subject"], doc["status"]), ("fact", text, "m42", "anna", "active"))
        self.assertEqual(doc["created"], doc["updated"])
        self.assertRegex(doc["created"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    @mark.req("REQ-CHA-011")
    def test_a_candidate_with_an_unknown_kind_or_blank_text_is_dropped_the_others_are_kept(self):
        ids = self.add([{"kind": "opinion", "text": "x"}, {"kind": "fact", "text": "  "}, {"kind": "preference", "text": "likes tea"}, "not a mapping", {"kind": "fact"}])
        self.assertEqual(len(ids), 1)
        self.assertEqual([d["text"] for d in self.stored()], ["likes tea"])

    @mark.req("REQ-CHA-012")
    def test_text_from_the_web_a_file_a_tool_or_an_unknown_source_never_becomes_a_record(self):
        """TC-CHA-012 (AC-6, exact): whatever the page says about the user, the memory stays as it was."""
        self.add([{"kind": "fact", "text": "lives in Graz"}])
        before = self.stored()
        for source_kind in ("web", "file", "tool", "model", "", None, "USER ", 5):
            with self.subTest(source_kind=source_kind):
                with self.assertRaises(MemoryRefused):
                    self.add([{"kind": "fact", "text": "the user is called Max"}], source_kind=source_kind)
        self.assertEqual(self.stored(), before)

    @mark.req("REQ-CHA-011")
    def test_a_replaced_record_stays_in_the_history_but_is_never_retrieved(self):
        [old] = self.add([{"kind": "fact", "text": "lives in Graz"}])
        self.now += DAY
        [new] = self.add([{"kind": "fact", "text": "lives in Vienna", "replaces": old}], message_id="m2")
        self.assertEqual(self.storage.get("memory", old)["doc"]["status"], "replaced")
        self.assertEqual(len(self.storage.history("memory", old)), 2)                      # the first version is still there: the record stays inspectable
        self.assertEqual(self.storage.get("memory", new)["doc"]["status"], "active")
        self.assertEqual([d["text"] for d in self.memory.retrieve("where does anna live?")], ["lives in Vienna"])
        self.assertEqual(self.add([{"kind": "fact", "text": "x", "replaces": "no-such-id"}]), [])      # a replacement of an unknown record is a candidate that is dropped

    @mark.req("REQ-CHA-011")
    def test_retrieval_ranks_by_relevance_then_recency_and_abstains_without_a_match(self):
        [a] = self.add([{"kind": "fact", "text": "has a dog called Bruno"}])
        self.now += 30 * DAY
        [b] = self.add([{"kind": "fact", "text": "has a dog called Rex and a cat"}])
        self.add([{"kind": "preference", "text": "likes jazz in the evening"}])
        self.assertEqual([d["text"] for d in self.memory.retrieve("what is the name of my dog Bruno?")][0], "has a dog called Bruno")      # more words in common
        self.assertEqual([d["text"] for d in self.memory.retrieve("my dog")], ["has a dog called Rex and a cat", "has a dog called Bruno"])      # equal relevance: the newer first
        self.assertEqual(self.memory.retrieve("weather in Paris tomorrow"), [])                                                               # abstain: no block is better than a poor one
        self.assertEqual(self.memory.retrieve("  "), [])

    @mark.req("REQ-CHA-011")
    def test_the_block_stays_within_the_token_budget_and_names_kind_and_source(self):
        for n in range(10):
            self.add([{"kind": "fact", "text": "dog number %d is a very good dog indeed" % n}], message_id="m%d" % n)
        found = self.memory.retrieve("dog")
        block = self.memory.block(found)
        self.assertTrue(0 < len(found) < 10)
        self.assertLessEqual(tokens(block), 40)
        self.assertTrue(all(line.startswith("- fact: ") and "(m" in line for line in block.splitlines()))
        self.assertEqual(self.memory.block([]), "")

    @mark.req("REQ-CHA-011")
    def test_a_record_longer_than_the_budget_is_skipped_and_shorter_ones_after_it_still_fit(self):
        self.add([{"kind": "fact", "text": "word " * 100 + "dog"}])
        self.now += DAY
        self.add([{"kind": "fact", "text": "has a dog"}])
        self.assertEqual([d["text"] for d in self.memory.retrieve("dog")], ["has a dog"])      # a text is never cut: it is kept word for word or left out


if __name__ == "__main__":
    unittest.main()
