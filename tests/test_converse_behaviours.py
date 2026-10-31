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
        w.express_and_reload = lambda name, sound=True, line=None: self.played.append((name, sound) if line is None else (name, sound, line))
        self.saved_pick = w.voice_lines.pick
        w.voice_lines.pick = lambda mood: None
        w.penalize = lambda penalty: None
        w.time.sleep = lambda seconds: None
        self.addCleanup(self.restore)

    def restore(self):
        for name, value in self.saved.items():
            setattr(w, name, value)
        w.chat_service.show_behaviour, w.time.sleep = self.saved_show, self.saved_sleep
        w.voice_lines.pick = self.saved_pick

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

    @mark.req("REQ-CHA-007")
    def test_the_mood_of_the_first_gesture_says_its_line_and_a_mood_without_one_is_silent_about_it(self):
        w.chat_service.show_behaviour = lambda name: True
        w.voice_lines.pick = lambda mood: "/lines/%s.wav" % mood if mood == "agree" else None
        w.converse("hi")
        self.assertEqual(self.played[:2], [("yes", True, "/lines/agree.wav"), ("no", False)])


    @mark.req("REQ-CHV-006")
    def test_the_reaction_of_the_chat_shows_the_expression_and_says_its_line(self):
        """REQ-CHV-006 (D-143): the reaction the chat service asks for after a minus shows `shocked` and plays the shocked line of the voice lines.

        Example: chat_service._react("shocked") -> express_and_reload("shocked", sound=True, line="/lines/shocked.wav")
        """
        # Given voice lines with a shocked line
        w.voice_lines.pick = lambda mood: "/lines/%s.wav" % mood
        # When the chat service lets the character react
        w.chat_service._react("shocked")
        # Then the character shows shocked and says its line
        self.assertEqual(self.played, [("shocked", True, "/lines/shocked.wav")])


class ShockedAfterAMinus(unittest.TestCase):
    """TC-CHV-006 (REQ-CHV-006, D-143, D-155): the backend side of the shocked reaction, from the vote to the wire."""

    @mark.req("REQ-CHV-006")
    def test_a_minus_vote_sends_the_shocked_expression_and_plays_the_shocked_line(self):
        """TC-CHV-006: a minus through the chat service of the app sends `expression {name: "shocked"}` to the pages and plays the shocked line; a plus does neither.

        Example: vote(anna, "voice", "service", -1) -> socket event ("expression", {"name": "shocked"}), play_sound(".../shocked_default.wav")
        """
        import tempfile
        # Given the app's chat service on a fresh votes table, with the socket and the sound player recorded
        sent, played = [], []
        saved = (w.socketio.emit, w.play_sound, w.chat_service._votes, w.voice_lines.pick)
        self.addCleanup(lambda: (setattr(w.socketio, "emit", saved[0]), setattr(w, "play_sound", saved[1]), setattr(w.chat_service, "_votes", saved[2]),
                                 setattr(w.voice_lines, "pick", saved[3])))
        w.socketio.emit = lambda event, payload=None, **kw: sent.append((event, payload))
        w.play_sound = lambda path, url=None: played.append(path)
        w.voice_lines.pick = lambda mood: "/voice/expressions/%s_default.wav" % mood
        w.chat_service._votes = w.Storage(w.FileBackend(tempfile.mkdtemp()))          # the app's own storage classes
        # When anna gives a plus and then a minus
        w.chat_service.vote("anna", "voice", "service", 1)
        self.assertNotIn(("expression", {"name": "shocked"}), sent)
        w.chat_service.vote("anna", "voice", "service", -1)
        # Then the pages get the shocked expression and the shocked line is played once
        self.assertIn(("expression", {"name": "shocked"}), sent)
        self.assertEqual(played, ["/voice/expressions/shocked_default.wav"])

if __name__ == "__main__":
    unittest.main()
