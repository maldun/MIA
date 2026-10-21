"""
Tests for the content store (content_store.py, ui/REQUIREMENTS_CORE.md CG14): put and get by hash, secrets removed before hashing, idempotence, a store that cannot write,
retention, and the link to the model_call events of the pipeline runner. Run with the MIA virtualenv: python tests/test_content_store.py
"""
import json
import os
import random
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

import events as E                                       # noqa: E402
import test_pipeline as TP                               # noqa: E402
from content_store import ContentStore                   # noqa: E402
from pipeline import Runner                              # noqa: E402


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.clock = [1_000_000.0]
        self.store = ContentStore(os.path.join(self.tmp.name, "store"), clock=lambda: self.clock[0])

    def tearDown(self):
        self.tmp.cleanup()

    def test_put_get_and_the_hash_is_the_digest(self):
        hash_ = self.store.put("A page about squared squares.")
        self.assertEqual(hash_, E.digest("A page about squared squares."))
        self.assertEqual(self.store.get(hash_), "A page about squared squares.")
        self.assertTrue(self.store.has(hash_))
        self.assertIsNone(self.store.get("h:" + "0" * 24))
        self.assertFalse(self.store.has("h:" + "0" * 24))

    def test_json_values_are_stored_as_canonical_json(self):
        a = self.store.put({"b": 2, "a": [1, "ä"]})
        b = self.store.put({"a": [1, "ä"], "b": 2})
        self.assertEqual(a, b)
        self.assertEqual(self.store.get_json(a), {"a": [1, "ä"], "b": 2})
        self.assertIsNone(self.store.get_json(self.store.put("not json {")))

    def test_secrets_are_removed_before_hashing_and_storing(self):
        hash_ = self.store.put("write to me@example.org with Bearer abcdefgh12345678")
        text = self.store.get(hash_)
        self.assertNotIn("me@example.org", text)
        self.assertNotIn("abcdefgh12345678", text)
        self.assertEqual(hash_, E.digest("write to me@example.org with Bearer abcdefgh12345678"))
        self.assertEqual(self.store.get_json(self.store.put({"editor_token": "abc", "q": "x"})), {"editor_token": E.REDACTED, "q": "x"})

    def test_idempotent_and_atomic(self):
        first = self.store.put("same")
        second = self.store.put("same")
        self.assertEqual(first, second)
        self.assertEqual(self.store.stats()["files"], 1)
        leftovers = [n for _, _, names in os.walk(self.store.folder) for n in names if n.endswith(".tmp")]
        self.assertEqual(leftovers, [])

    def test_a_store_that_cannot_write_does_not_break_anything(self):
        blocked = os.path.join(self.tmp.name, "file")
        with open(blocked, "w") as fp:
            fp.write("x")
        broken = ContentStore(os.path.join(blocked, "inside"))                  # a folder below a file: cannot be made
        hash_ = broken.put("text")
        self.assertEqual(hash_, E.digest("text"))
        self.assertEqual(broken.failures, 1)
        self.assertIsNone(broken.get(hash_))
        nothing = ContentStore(None)
        self.assertEqual(nothing.put("text"), E.digest("text"))
        self.assertIsNone(nothing.get(E.digest("text")))

    def test_bad_hash_is_refused_quietly(self):
        self.assertIsNone(self.store.get("../../etc/passwd"))
        self.assertFalse(self.store.has("h:zz/../.."))

    def test_prune_by_age_with_keep_and_renewal(self):
        old = self.store.put("old text")
        kept = self.store.put("old but kept")
        renewed = self.store.put("old but stored again")
        self.clock[0] += 100 * 86400
        self.store.put("old but stored again")                                    # renews its age
        young = self.store.put("young text")
        removed = self.store.prune(90, keep=[kept])
        self.assertEqual(removed, 1)
        self.assertFalse(self.store.has(old))
        for hash_ in (kept, renewed, young):
            self.assertTrue(self.store.has(hash_))
        self.assertEqual(self.store.prune(90), 1)                                 # `kept` is not protected the second time
        self.assertEqual(ContentStore(None).prune(10), 0)

    def test_stats(self):
        self.store.put("a" * 100)
        self.store.put("b" * 50)
        stats = self.store.stats()
        self.assertEqual((stats["files"], stats["bytes"], stats["failures"]), (2, 150, 0))


class InThePipeline(unittest.TestCase):
    def go(self, store, name="demo", **kw):
        nodes = [{"id": "plan", "kind": "model", "prompt": "plan", "schema": "queries", "output": "out"}]
        events = []
        runner = Runner(model=TP.FakeModel([json.dumps({"queries": ["a"]})]), rng=random.Random(1), store=store, **kw)
        runner.run(TP.skill(name=name), TP.graph(nodes), {"text": "why? write to me@example.org"}, on_event=events.append)
        return [e for e in events if e.get("type") == "model_call"]

    def test_prompt_and_answer_are_in_the_store_under_the_hashes_of_the_event(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ContentStore(folder)
            calls = self.go(store)
            self.assertEqual(len(calls), 1)
            payload = calls[0]["payload"]
            messages = store.get_json(payload["prompt_hash"])
            self.assertEqual(messages[-1]["role"], "user")
            self.assertIn("why?", messages[-1]["content"])
            self.assertNotIn("me@example.org", messages[-1]["content"])           # nothing the log must not hold
            self.assertEqual(json.loads(store.get(payload["response_hash"])), {"queries": ["a"]})

    def test_a_conversation_is_not_stored_unless_asked(self):
        with tempfile.TemporaryDirectory() as folder:
            store = ContentStore(folder)
            calls = self.go(store, name="chat")
            self.assertEqual(store.stats()["files"], 0)
            self.assertTrue(calls[0]["payload"]["prompt_hash"].startswith("h:"))             # the hash is in the event all the same
            self.go(ContentStore(folder), name="chat", store_texts=lambda name: True)
            self.assertEqual(ContentStore(folder).stats()["files"], 2)

    def test_no_store_no_files_and_the_run_is_unchanged(self):
        calls = self.go(None)
        self.assertEqual(calls[0]["payload"]["valid"], True)


if __name__ == "__main__":
    unittest.main()
