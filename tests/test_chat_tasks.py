"""
TC-WFM-030/031/033/035/036 in the chat service: the tasks come from a registry (no skill is named in the core), their options reach the run, every task has a status card, a task can be
paused and resumed, the result of a task that asks questions is the newest message, and the hooks for the class of a model (prepare_task) and for commands with an argument (/model) work.
Run in the image: bash tools/run_in_image.sh tests/test_chat_tasks.py
"""
import importlib
import os
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

MOODS = os.path.join(REPO, "moods.json")


def wait_for(condition, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.01)
    return False


class ChatTasks(unittest.TestCase):
    def setUp(self):
        self.chat_log = importlib.import_module("MIA.chat_log")
        self.service_module = importlib.import_module("MIA.chat_service")
        self.registry_module = importlib.import_module("MIA.task_registry")
        self.moods = importlib.import_module("MIA.moods")
        self.tmp = tempfile.TemporaryDirectory()
        self.log = self.chat_log.ChatLog(os.path.join(self.tmp.name, "log.jsonl"))
        self.events, self.seen, self.steps = [], [], []
        self.first, self.release = threading.Event(), threading.Event()

    def tearDown(self):
        self.release.set()
        self.tmp.cleanup()

    def make(self, tasks, **kwargs):
        registry = self.registry_module.TaskRegistry()
        for task in tasks:
            registry.register(task)
        return self.service_module.ChatService(lambda event, payload: self.events.append((event, payload)), self.log, self.moods.MoodTracker(MOODS), lambda *a: "chat",
                                               model_info=lambda: ("m", "light"), tasks=registry, user_limit=2, queue_size=3, **kwargs)

    def task(self, run, id="demo", needs=(), options=()):
        return self.registry_module.Task(id, run, "A demo task", "your question", "/%s something" % id, options=options, needs=needs)

    def idle(self, service):
        return wait_for(lambda: not service.status()["busy"])

    def statuses(self):
        return [p for e, p in self.events if e == "task_status"]

    def test_options_reach_the_run_and_the_configured_defaults_apply(self):                   # TC-WFM-030
        def run(argument, on_delta, on_emotion, should_stop, options=None):
            self.seen.append((argument, dict(options)))
            return "done"
        slice_option = self.registry_module.Option("slice", "flag", False, "work in slices")
        service = self.make([self.task(run, needs=("options",), options=(slice_option,))], skill_options={"demo": {"slice": False}})
        service.send("/demo options slice -- the question", author="anna")
        self.assertTrue(self.idle(service))
        service.send("/demo plain", author="anna")
        self.assertTrue(self.idle(service))
        self.assertEqual(self.seen, [("the question", {"slice": True}), ("plain", {"slice": False})])

    def test_options_alone_is_answered_by_a_note_and_an_unknown_option_runs_nothing(self):   # TC-WFM-030
        service = self.make([self.task(lambda *a: "x", options=(self.registry_module.Option("slice", "flag", False, "work in slices"),))])
        ack = service.send("/demo options", author="anna")
        self.assertEqual((ack["ok"], ack["queued"]), (True, False))
        self.assertIn("slice", self.log.history(limit=5)[0][-1]["text"])
        ack = service.send("/demo options fast -- q", author="anna")
        self.assertFalse(ack["ok"])
        self.assertIn("slice", ack["error"])
        self.assertEqual(service.status()["queue"], 0)

    def test_every_task_has_a_status_card_that_ends_with_done_and_names_the_mode(self):        # TC-WFM-031
        slice_option = self.registry_module.Option("slice", "flag", False, "work in slices")

        def run(argument, on_delta, on_emotion, should_stop, monitor=None):
            monitor.update(phase="working", counts={"on_list": 4}, budget={"calls": {"used": 1, "limit": 150}})
            return "done"
        service = self.make([self.task(run, needs=("monitor",), options=(slice_option,))])
        service.send("/demo options slice -- q", author="anna")
        self.assertTrue(self.idle(service))
        last = self.statuses()[-1]
        self.assertEqual((last["task"], last["done"], last["mode"], last["counts"]), ("demo", True, "slice", {"on_list": 4}))
        self.assertEqual(last["budget"]["calls"], {"used": 1, "limit": 150})
        self.assertEqual(last["id"], [p for e, p in self.events if e == "chat_done"][-1]["id"])
        service.send("/demo again", author="anna")
        self.assertTrue(self.idle(service))
        self.assertEqual(self.statuses()[-1]["mode"], "run")

    def test_a_task_that_reports_nothing_still_has_a_card_with_the_time(self):                 # TC-WFM-031
        service = self.make([self.task(lambda *a: "done")])
        service.send("/demo q", author="anna")
        self.assertTrue(self.idle(service))
        self.assertIn("used", self.statuses()[-1]["budget"]["seconds"])

    def _pausing_run(self):
        def run(argument, on_delta, on_emotion, should_stop):
            self.steps.append(0)
            self.first.set()
            self.release.wait(5)
            if should_stop():                           # blocks while the task is paused
                return "as it stands"
            self.steps.append(1)
            return "done"
        return run

    def test_a_paused_task_starts_no_step_and_resume_goes_on(self):                             # TC-WFM-033
        service = self.make([self.task(self._pausing_run())])
        service.send("/demo q", author="anna")
        self.assertTrue(self.first.wait(5))
        self.assertTrue(service.pause())
        self.release.set()
        time.sleep(0.3)
        self.assertEqual(self.steps, [0])
        self.assertTrue(self.statuses()[-1]["paused"])
        self.assertTrue(service.resume())
        self.assertTrue(self.idle(service))
        self.assertEqual(self.steps, [0, 1])
        self.assertFalse(service.pause())               # nothing runs

    def test_stop_ends_a_paused_task_with_the_result_as_it_stands(self):                        # TC-WFM-033
        service = self.make([self.task(self._pausing_run())])
        service.send("/demo q", author="anna")
        self.assertTrue(self.first.wait(5))
        service.pause()
        self.release.set()
        time.sleep(0.2)
        self.assertTrue(service.stop())
        self.assertTrue(self.idle(service))
        self.assertEqual(self.steps, [0])
        done = [p for e, p in self.events if e == "chat_done"][-1]
        self.assertEqual((done["text"], done["status"]), ("as it stands", "stopped"))

    def test_the_result_of_a_task_that_asks_is_the_newest_message(self):                         # TC-WFM-036
        def run(argument, on_delta, on_emotion, should_stop, ask=None):
            self.seen.append(ask("First?"))
            on_delta("a progress line")
            return "the report"
        service = self.make([self.task(run, needs=("ask",))])
        service.send("/demo q", author="anna")
        self.assertTrue(wait_for(lambda: any(e == "chat_message" and p["role"] == "assistant" for e, p in self.events)))
        service.send("yes", author="anna")
        self.assertTrue(self.idle(service))
        names = [e for e, _ in self.events]
        self.assertNotIn("chat_delta", names[:names.index("chat_start")])
        self.assertGreater(names.index("chat_start"), max(i for i, (e, p) in enumerate(self.events) if e == "chat_message"))
        records = self.log.history(limit=20)[0]
        self.assertEqual([r["role"] for r in records], ["user", "assistant", "user", "assistant"])
        self.assertEqual(records[-1]["text"], "the report")
        self.assertEqual([p["text"] for e, p in self.events if e == "chat_delta"][-1], "the report")

    def test_prepare_task_may_ask_and_change_the_options(self):                                  # TC-WFM-035
        def run(argument, on_delta, on_emotion, should_stop, options=None):
            self.seen.append(dict(options))
            return "done"
        asked = []

        def prepare(task, options, ask):
            asked.append(ask("Is this a paid model?"))
            return dict(options, slice=True)
        slice_option = self.registry_module.Option("slice", "flag", False, "work in slices")
        service = self.make([self.task(run, needs=("options",), options=(slice_option,))], prepare_task=prepare)
        service.send("/demo q", author="anna")
        self.assertTrue(wait_for(lambda: any(e == "chat_message" and p["role"] == "assistant" for e, p in self.events)))
        service.send("yes", author="anna")
        self.assertTrue(self.idle(service))
        self.assertEqual((asked, self.seen), (["yes"], [{"slice": True}]))

    def test_a_command_with_an_argument_is_answered_by_a_note_and_not_queued(self):             # TC-WFM-035
        service = self.make([], argument_commands={"model": lambda argument: "model class set: " + argument})
        ack = service.send("/model paid big-model", author="anna")
        self.assertEqual((ack["ok"], ack["queued"], ack["command"]), (True, False, True))
        self.assertEqual(self.log.history(limit=5)[0][-1]["text"], "model class set: paid big-model")
        self.assertFalse(service.status()["busy"])


if __name__ == "__main__":
    unittest.main()
