"""
Returning to idle after an answer is silent (the voice clip of "idle" is not played), unless "idle_sound" is set.
Run with the MIA virtualenv: python tests/test_idle_sound.py
"""
import importlib
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)


class IdleSoundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("MIA_TEST", "1")
        cls.wa = importlib.import_module("MIA.web_app")

    def setUp(self):
        wa = self.wa
        self.expressed = []
        self.saved = {"express": wa.express_and_reload, "exchange": wa.comm.exchange, "sleep": wa.time.sleep,
                      "voice": wa.send_voice_request, "time_update": wa.comm.time_update, "idle": wa.IDLE_SOUND}
        wa.express_and_reload = lambda expression, sound=True: self.expressed.append((expression, sound))
        wa.comm.exchange = lambda message, **kw: ("happy\nHello.", "Hello.", None)
        wa.comm.time_update = lambda **kw: ("happy\nIt is noon.", "It is noon.", None)
        wa.send_voice_request = lambda msg: None
        wa.time.sleep = lambda seconds: None

    def tearDown(self):
        wa = self.wa
        wa.express_and_reload = self.saved["express"]
        wa.comm.exchange = self.saved["exchange"]
        wa.time.sleep = self.saved["sleep"]
        wa.send_voice_request = self.saved["voice"]
        wa.comm.time_update = self.saved["time_update"]
        wa.IDLE_SOUND = self.saved["idle"]

    def test_default_is_silent_after_an_answer(self):
        self.assertFalse(self.wa.IDLE_SOUND)
        self.wa.converse("hi")
        self.assertEqual(self.expressed[-1], ("idle", False))

    def test_default_is_silent_after_the_time_check(self):
        self.wa.time_update()
        self.assertEqual(self.expressed[-1], ("idle", False))

    def test_the_old_behavior_can_be_switched_on(self):
        self.wa.IDLE_SOUND = True
        self.wa.converse("hi")
        self.assertEqual(self.expressed[-1], ("idle", True))
        self.wa.time_update()
        self.assertEqual(self.expressed[-1], ("idle", True))

    def test_the_reaction_to_the_answers_emotion_keeps_its_sound(self):
        self.wa.comm.exchange = lambda message, emotion_reaction=None, **kw: (emotion_reaction("happy"), ("happy\nHello.", "Hello.", None))[1]
        self.wa.converse("hi")
        self.assertEqual(self.expressed[0][1], True)          # the first reaction may play its clip
        self.assertEqual(self.expressed[-1], ("idle", False))


if __name__ == "__main__":
    unittest.main()
