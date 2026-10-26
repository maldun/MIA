"""TC-CHA-017b (REQ-CHA-017): the character's gesture of an answer is one opportunity of a behaviour: a behaviour with many net minus votes is skipped (the page still gets the mood).
Needs the app and its packages: bash tools/run_in_image.sh tests/test_converse_behaviours.py"""
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))
os.environ.update({"ANSWER_DELAY": "0.3", "EVENT_GAP": "0", "MIA_TEST": "1"})

from markers import mark  # noqa: E402

spec = importlib.util.spec_from_file_location("chat_mock_server", os.path.join(REPO, "ui", "tools", "chat_mock_server.py"))
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
w = server.w


class FakeStreamer:
    def __init__(self, *args, **kwargs):
        pass

    def update(self, text):
        pass

    def finish(self, text):
        pass

    def wait(self):
        pass

    def abort(self):
        pass


class FakeComm:
    """the model says two things: the character reacts to each emotion"""

    @staticmethod
    def map_emotion(emotion):
        return {"agree": "yes", "disagree": "no"}[emotion]

    def exchange(self, message, emotion_reaction=None, update_message=None, **kwargs):
        emotion_reaction("agree")
        emotion_reaction("disagree")
        return "text", "text", None


class ConverseBehaviours(unittest.TestCase):
    def setUp(self):
        self.played, self.heard = [], []
        self.saved = {name: getattr(w, name) for name in ("comm", "SpeechStreamer", "express_and_reload", "penalize")}
        self.saved_show, self.saved_sleep = w.chat_service.show_behaviour, w.time.sleep
        w.comm, w.SpeechStreamer = FakeComm(), FakeStreamer
        w.express_and_reload = lambda name, sound=True: self.played.append((name, sound))
        w.penalize = lambda penalty: None
        w.time.sleep = lambda seconds: None
        self.addCleanup(self.restore)

    def restore(self):
        for name, value in self.saved.items():
            setattr(w, name, value)
        w.chat_service.show_behaviour, w.time.sleep = self.saved_show, self.saved_sleep

    @mark.req("REQ-CHA-017")
    def test_a_gesture_that_is_not_shown_is_skipped_and_the_mood_still_reaches_the_page(self):
        w.chat_service.show_behaviour = lambda name: name != "no"
        w.converse("hi", on_emotion=self.heard.append)
        self.assertEqual(self.played, [("yes", True), ("idle", True)])         # "no" is skipped; the last one is the return to idle
        self.assertEqual(self.heard, ["agree", "disagree"])

    @mark.req("REQ-CHA-017")
    def test_the_first_gesture_that_is_shown_plays_the_sound(self):
        w.chat_service.show_behaviour = lambda name: name != "yes"
        w.converse("hi")
        self.assertEqual(self.played[0], ("no", True))


if __name__ == "__main__":
    unittest.main()
