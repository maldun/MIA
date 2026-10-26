"""
TC-CHA-007 / REQ-CHA-007
Run with: python tests/test_voice_lines.py
"""

import json
import os
import random
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark
from voice_lines import VoiceLines, mood_names


class VoiceLinesTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.folder = os.path.join(self.dir, "expressions")
        os.makedirs(self.folder)
        self.path = os.path.join(self.dir, "voice_lines.json")
        self.logged = []

    def files(self, *names):
        for name in names:
            with open(os.path.join(self.folder, name), "wb") as fp:
                fp.write(b"RIFF")

    def config(self, lines, silent=()):
        with open(self.path, "w", encoding="utf-8") as fp:
            json.dump({"lines": lines, "silent": list(silent)}, fp)

    def voice(self, moods=("happy", "sad"), seed=1):
        return VoiceLines(self.path, self.folder, moods, rng=random.Random(seed), log=self.logged.append)

    @mark.req("REQ-CHA-007")
    def test_one_of_the_lines_is_chosen_at_random(self):
        self.files("a.wav", "b.wav", "c.wav")
        self.config({"happy": ["a.wav", "b.wav", "c.wav"]})
        voice = self.voice()
        picks = {voice.pick("happy") for _ in range(60)}
        self.assertEqual(picks, {os.path.join(self.folder, name) for name in ("a.wav", "b.wav", "c.wav")})

    @mark.req("REQ-CHA-007")
    def test_a_mood_without_a_line_is_silent(self):
        self.files("a.wav")
        self.config({"happy": ["a.wav"]})
        self.assertIsNone(self.voice().pick("sad"))
        self.assertIsNone(self.voice().pick("unknown mood"))

    @mark.req("REQ-CHA-007")
    def test_a_missing_file_is_logged_and_skipped(self):
        self.files("a.wav")
        self.config({"happy": ["a.wav", "gone.wav"]})
        voice = self.voice()
        picks = {voice.pick("happy") for _ in range(20)}
        self.assertEqual(picks, {os.path.join(self.folder, "a.wav")})
        self.assertTrue(any("gone.wav" in message for message in self.logged))
        self.config({"happy": ["gone.wav"]})
        self.assertIsNone(self.voice().pick("happy"))

    @mark.req("REQ-CHA-007")
    def test_the_mood_is_found_in_any_case(self):
        self.files("a.wav")
        self.config({"Happy": ["a.wav"]})
        self.assertEqual(self.voice().pick("HAPPY"), os.path.join(self.folder, "a.wav"))

    @mark.req("REQ-CHA-007")
    def test_every_mood_has_a_line_or_is_declared_silent(self):
        self.config({"happy": ["a.wav"]}, silent=["Sad"])
        self.assertEqual(self.voice(moods=("happy", "sad", "angry", "neutral")).uncovered(), ["angry", "neutral"])

    @mark.req("REQ-CHA-007")
    def test_a_broken_or_missing_config_is_silence(self):
        self.assertIsNone(self.voice().pick("happy"))
        with open(self.path, "w") as fp:
            fp.write("{broken")
        self.assertIsNone(self.voice().pick("happy"))

    @mark.req("REQ-CHA-007")
    def test_the_real_mood_map_is_covered(self):
        moods = mood_names(os.path.join(ROOT, "moods.json"))
        voice = VoiceLines(os.path.join(ROOT, "library", "voice_lines.json"), os.path.join(ROOT, "voice", "expressions"), moods)
        self.assertEqual(voice.uncovered(), [])
        self.assertIn("waiting", moods)


if __name__ == "__main__":
    unittest.main()
