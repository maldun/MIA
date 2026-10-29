"""
The whole chain of /review as the application builds it, without a model and without the network: the real extension (loaded by the loader), the real ChatService, the real files volume
and storage; only the skills (core.run) and the scholar are scripted. Found by the hand test of 2026-10-29: "the report does not appear afterwards and there are no download links".
Run in the image: bash tools/run_in_image.sh tests/test_review_chain.py
"""
import importlib
import os
import sys
import tempfile
import threading
import time
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)          # the application's way: only the parent folder of MIA on the path

import test_review_chat as T          # noqa: E402  (the scripted skills, the fake scholar, the works)


def wait_for(condition, timeout=8.0):
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.01)
    return False


class Chain(unittest.TestCase):
    def setUp(self):
        mod = lambda name: importlib.import_module("MIA." + name)
        self.tmp = tempfile.TemporaryDirectory()
        self.store = mod("storage").Storage(mod("storage_files").FileBackend(os.path.join(self.tmp.name, "db")))
        self.files = mod("file_store").FileStore(os.path.join(self.tmp.name, "files"))
        self.events, self.calls = [], []
        skills = T.skills(self.calls)

        def run(name, inputs, should_stop=None):
            return types.SimpleNamespace(status="done", answer=skills(name, inputs), error=None)
        self.services = types.SimpleNamespace(
            core=types.SimpleNamespace(run=run), cfg={}, scholar=T.FakeScholar([T.work("10.1/a", "Colouring"), T.work("10.1/b", "Timetabling")]), web_get=lambda *a, **k: None,
            library=mod("workflow_library").WorkflowLibrary(self.store), pipeline_event=lambda e: None, note_sources=lambda s: None, speaker=lambda task: None,
            trust_for_url=lambda: None)
        self.registry = mod("task_registry").TaskRegistry()
        self.problems = mod("extension_loader").load_extensions("MIA.extensions", os.path.join(REPO, "extensions"), self.registry, self.services)
        log = mod("chat_log").ChatLog(os.path.join(self.tmp.name, "log.jsonl"))
        self.log = log
        self.chat = mod("chat_service").ChatService(lambda event, payload: self.events.append((event, payload)), log, mod("moods").MoodTracker(os.path.join(REPO, "moods.json")),
                                                    lambda *a: "chat", model_info=lambda: ("m", "light"), tasks=self.registry, votes=self.store, files=self.files, review_timeout=30,
                                                    user_limit=2, queue_size=3)

    def tearDown(self):
        self.tmp.cleanup()

    def asked(self, count):
        return wait_for(lambda: len([e for e, p in self.events if e == "chat_message" and p["role"] == "assistant"]) >= count)

    def run_review(self, text="/review how to schedule? until 2026-01-01", replies=("yes", "yes")):
        self.chat.send(text, author="anna")
        for i, reply in enumerate(replies):
            self.assertTrue(self.asked(i + 1), "the question %d did not come: %s" % (i + 1, [e for e, _ in self.events][-6:]))
            self.chat.send(reply, author="anna")
        self.assertTrue(wait_for(lambda: not self.chat.status()["busy"]), "the review did not end")

    def test_the_extensions_load_without_a_problem(self):
        self.assertEqual(self.problems, [])
        self.assertEqual(self.registry.ids(), ["lookup", "review", "search"])

    def test_the_report_is_the_newest_message_with_download_links_and_the_files_exist(self):
        self.run_review()
        last = self.log.history(limit=20)[0][-1]
        self.assertEqual(last["role"], "assistant")
        self.assertTrue(last["text"].startswith("## Literature review"), last["text"][:200])
        names = [f["name"] for f in self.files.list()]
        self.assertEqual(sorted(n.rsplit(".", 1)[1] for n in names), ["md", "tex"])
        for name in names:
            self.assertIn("(/api/files/%s)" % name, last["text"])                 # a link that downloads the file, in the result itself
        done = [p for e, p in self.events if e == "chat_done"][-1]
        self.assertEqual(sorted(done["files"]), sorted(names))
        self.assertEqual(done["id"], last["id"])

    def test_the_report_is_also_a_record_with_its_origin(self):
        self.run_review()
        done = [p for e, p in self.events if e == "chat_done"][-1]
        doc = self.store.get("reports", done["id"])["doc"]
        self.assertEqual((doc["task"], doc["account"], doc["question"]), ("review", "anna", "how to schedule?"))      # the question without the cut-off, which the report states
        self.assertEqual(len(doc["report"]["works"]), 2)

    def test_a_review_that_fails_leaves_a_result_that_says_why(self):
        self.services.scholar = types.SimpleNamespace(search=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("the scholarly service is down")))
        self.run_review(replies=("yes",))
        last = self.log.history(limit=20)[0][-1]
        self.assertEqual(last["role"], "assistant")
        self.assertIn("the scholarly service is down", last["text"])             # not only a toast that can be missed
        self.assertIn("/review", last["text"])


if __name__ == "__main__":
    unittest.main()
