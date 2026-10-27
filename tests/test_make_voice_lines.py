"""tools/make_voice_lines.py (REQ-VOI-004): the default voice lines are rendered by our own engine and listed in the config. Fake Speaker, no model."""
import json
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))
from make_voice_lines import make_lines  # noqa: E402


class FakeSpeaker:
    def __init__(self, silent=()):
        self.said, self.silent = [], silent

    def render_voice(self, msg, output_file):
        self.said.append(msg)
        if msg in self.silent:
            return 0
        with open(output_file, "wb") as fp:
            fp.write(b"RIFF")
        return 0.5


class MakeLinesTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.config = os.path.join(self.folder, "voice_lines.json")
        with open(self.config, "w") as fp:
            json.dump({"note": "x", "lines": {"annoyed": ["annoyed.wav"], "happy": []}}, fp)

    def lines(self):
        with open(self.config) as fp:
            return json.load(fp)

    def test_clips_are_rendered_and_listed_and_the_rest_is_kept(self):
        speaker = FakeSpeaker()
        done = make_lines({"happy": "Hooray.", "sad": "Oh."}, speaker, self.folder, self.config)
        self.assertEqual(done, ["happy", "sad"])
        self.assertEqual(speaker.said, ["Hooray.", "Oh."])
        for mood in done:
            self.assertTrue(os.path.isfile(os.path.join(self.folder, mood + "_default.wav")))
        data = self.lines()
        self.assertEqual(data["lines"], {"annoyed": ["annoyed.wav"], "happy": ["happy_default.wav"], "sad": ["sad_default.wav"]})
        self.assertEqual(data["note"], "x")

    def test_a_text_that_renders_nothing_gets_no_entry(self):
        done = make_lines({"happy": "..."}, FakeSpeaker(silent=("...",)), self.folder, self.config)
        self.assertEqual(done, [])
        self.assertEqual(self.lines()["lines"]["happy"], [])

    def test_the_shipped_texts_cover_the_moods_to_be_made(self):
        with open(os.path.join(REPO, "library", "voice_line_texts.json"), encoding="utf-8") as fp:
            texts = json.load(fp)
        self.assertEqual(set(texts), {"happy", "neutral", "angry", "surprised", "smug", "disagree", "embarrassed", "thinking", "sad"})
        self.assertTrue(all(text.strip() and text.isascii() for text in texts.values()))


if __name__ == "__main__":
    unittest.main()
