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

import checkout_copy  # noqa: E402  (MIA from a temporary copy: nothing is written into the checkout, D-169)
_LINK_DIR = checkout_copy.use()
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

    def wait(self, should_stop=None):
        pass


class SpokenStreamer(FakeStreamer):
    """records what the wait for the voice saw: the answer is complete (finish), then the user presses Stop while it is spoken"""
    last = None

    def __init__(self, *args, **kwargs):
        SpokenStreamer.last = self
        self.finished, self.stopped_while_spoken = False, None

    def finish(self, text):
        self.finished = True

    def wait(self, should_stop=None):
        self.stopped_while_spoken = should_stop is not None and should_stop()

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


    @mark.req("REQ-VPB-002", "REQ-FE-012")
    def test_a_stop_while_the_answer_is_spoken_reaches_the_wait_for_the_voice(self):
        """A3 (D-154): the chat's stop reaches the wait for the voice of a complete answer, so the speech process can end the stream.

        Example: the answer is complete, Stop is pressed while it is spoken -> the streamer's wait sees should_stop() == True.
        """
        # Given: a converse whose stop becomes true once the whole answer went to the voice
        w.SpeechStreamer = SpokenStreamer
        w.chat_service.show_behaviour = lambda name: True
        # When: the answer is spoken
        w.converse("hi", should_stop=lambda: SpokenStreamer.last.finished)
        # Then: the wait for the voice was told about the stop
        self.assertTrue(SpokenStreamer.last.stopped_while_spoken)

    @mark.req("REQ-CHV-006")
    def test_the_reaction_of_the_chat_shows_the_expression_and_says_its_line(self):
        """REQ-CHV-006 (D-143): the reaction the chat service asks for after a minus shows `shocked` and plays the shocked line of the voice lines.

        Example: chat_service._react("shocked") -> express_and_reload("shocked", sound=True, line="/lines/shocked.wav")
        """
        # Given voice lines with a shocked line (the return to the mood's face is left in the background, TC-CHV-006 checks it)
        w.voice_lines.pick = lambda mood: "/lines/%s.wav" % mood
        saved = w.socketio.start_background_task
        self.addCleanup(setattr, w.socketio, "start_background_task", saved)
        w.socketio.start_background_task = lambda target, *args, **kwargs: None
        # When the chat service lets the character react
        w.chat_service._react("shocked")
        # Then the character shows shocked and says its line
        self.assertEqual(self.played, [("shocked", True, "/lines/shocked.wav")])


class ShockedAfterAMinus(unittest.TestCase):
    """TC-CHV-006 (REQ-CHV-006, D-143, D-155): the backend side of the shocked reaction, from the vote to the wire."""

    def record_the_app(self):
        """the app's chat service on a fresh votes table, a happy mood, a shocked line of 0.5 s, and the socket, the sound player and the background
        recorded; returns (the faces sent so far, the sounds played, the background tasks, the sleeps, the line)"""
        import tempfile
        import wave
        folder = tempfile.mkdtemp()
        line = os.path.join(folder, "shocked_default.wav")
        with wave.open(line, "wb") as fp:
            fp.setnchannels(1)
            fp.setsampwidth(2)
            fp.setframerate(8000)
            fp.writeframes(b"\0\0" * 4000)
        sent, played, background, slept = [], [], [], []
        saved = (w.socketio.emit, w.socketio.start_background_task, w.socketio.sleep, w.play_sound, w.chat_service._votes, w.voice_lines.pick, w.mood)
        self.addCleanup(lambda: (setattr(w.socketio, "emit", saved[0]), setattr(w.socketio, "start_background_task", saved[1]), setattr(w.socketio, "sleep", saved[2]),
                                 setattr(w, "play_sound", saved[3]), setattr(w.chat_service, "_votes", saved[4]), setattr(w.voice_lines, "pick", saved[5]),
                                 setattr(w, "mood", saved[6])))
        w.socketio.emit = lambda event, payload=None, **kw: sent.append((event, payload))
        w.socketio.start_background_task = lambda target, *args, **kwargs: background.append(lambda: target(*args, **kwargs))
        w.socketio.sleep = slept.append
        w.play_sound = lambda path, url=None: played.append(path)
        w.voice_lines.pick = lambda mood: line if mood == "shocked" else None
        w.chat_service._votes = w.Storage(w.FileBackend(folder))          # the app's own storage classes
        w.mood = type("Mood", (), {"status": lambda self: {"emotion": "happy"}})()
        faces = lambda: [p["name"] for e, p in sent if e == "expression"]
        return faces, played, background, slept, line

    @mark.req("REQ-CHV-006")
    def test_a_minus_vote_sends_the_shocked_expression_and_plays_the_shocked_line(self):
        """TC-CHV-006 (D-156): a minus through the chat service of the app sends `expression {name: "shocked"}` to the pages and plays the shocked line; in the
        background, after the length of the line, the face of the current mood follows; a plus does none of it.

        Example: mood "happy", line of 0.5 s; vote(anna, "voice", "service", -1) -> ("expression", shocked), play_sound(line), sleep 0.5 in the background,
        ("expression", happy)
        """
        # Given the app's chat service on a fresh votes table, a happy mood, a shocked line of 0.5 s, and the socket, the sound player and the background recorded
        faces, played, background, slept, line = self.record_the_app()
        # When anna gives a plus
        w.chat_service.vote("anna", "voice", "service", 1)
        # Then nothing happens to the character
        self.assertEqual((faces(), played, background), ([], [], []))
        # When anna gives a minus
        w.chat_service.vote("anna", "voice", "service", -1)
        # Then she is shocked and says the line at once, and the return waits in the background
        self.assertEqual((faces(), played), (["shocked"], [line]))
        self.assertEqual(len(background), 1)
        background.pop()()
        # and after the length of the line she shows the face of her mood again
        self.assertEqual(slept, [0.5])
        self.assertEqual(faces(), ["shocked", "happy"])
        self.assertEqual(played, [line])

    @mark.req("REQ-CHV-006")
    def test_a_second_minus_within_the_line_keeps_the_face_shocked_to_its_end(self):
        """R4 of the N-1.2 re-verification (D-167): a new shocked reaction cancels the pending return to the mood, so the face returns only after the last line.

        Example: two minus votes within one line -> two background returns; the first, after its 0.5 s, sends nothing; the second sends happy.
        """
        # Given the app recorded, a happy mood and a shocked line of 0.5 s
        faces, played, background, slept, line = self.record_the_app()
        # When anna and ben give a minus within the length of one line
        w.chat_service.vote("anna", "voice", "service", -1)
        w.chat_service.vote("ben", "voice", "service", -1)
        self.assertEqual((faces(), len(background)), (["shocked", "shocked"], 2))
        # Then the first return ends without changing the face
        background.pop(0)()
        self.assertEqual(faces(), ["shocked", "shocked"])
        # and the return of the second line brings the face of the mood
        background.pop(0)()
        self.assertEqual(faces(), ["shocked", "shocked", "happy"])

if __name__ == "__main__":
    unittest.main()
