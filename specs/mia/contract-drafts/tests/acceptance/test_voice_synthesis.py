"""
Acceptance tests of the Voice synthesis (N-2.5: REQ-VOI-001 to REQ-VOI-003, AC-13) against the real SpeechService with a fake engine (no model, no TTS packages).
The engine is a Speaker that records what it is asked to say and writes a short silent wav. REQ-VOI-004 is an inspection (tools/make_voice_lines.py and
library/voice_line_texts.json), checked in Verify.
Protected after the Plan gate (amendment A-13). Run with: python tests/acceptance/test_voice_synthesis.py
"""
import json
import os
import re
import sys
import tempfile
import unittest
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                  # noqa: E402
from speech_service import SpeechError, SpeechService     # noqa: E402
from speech_stream import SpeechStreamer                  # noqa: E402
from voice_lines import VoiceLines, mood_names            # noqa: E402


class RecordingSpeaker:
    def __init__(self):
        self.said = []

    def render_voice(self, msg, output_file):
        self.said.append(msg)
        with wave.open(output_file, "wb") as fp:
            fp.setnchannels(1)
            fp.setsampwidth(2)
            fp.setframerate(8000)
            fp.writeframes(b"\0\0" * 400)
        return 0.05


FIVE_SENTENCES = "The first one is short. The second one asks why? The third is calm. The fourth says go! The fifth ends it."

MARKUP_ANSWERS = [
    "*smiles* Hello there. **Bold** words stay.",
    "# Heading\nSome text here.",
    "<b>Hi</b> there, <i>friend</i>.",
    "- one item\n- another item",
    "Use `code` sparingly.",
    "> a quoted line",
    "See [the page](http://example.org/x) now.",
    "Hello *waves happily* how are you?",
    "~~old~~ new text.",
    "| a | b |\n|---|---|\n| 1 | 2 |",
]
MARKS = re.compile(r"[*_#>`~|]|\]\(|</?[a-z]+>|https?://")


class VoiceSynthesisTest(unittest.TestCase):
    def service(self, lines=None, folder=None):
        self.speaker = RecordingSpeaker()
        return SpeechService(self.speaker, folder or tempfile.mkdtemp(), lines=lines)

    @mark.req("REQ-VOI-001")
    def test_tc_voi_001_each_sentence_yields_one_audio_chunk(self):
        service = self.service()
        sentences = SpeechStreamer.split(FIVE_SENTENCES)
        self.assertEqual(len(sentences), 5)
        chunks = [service.synthesize(sentence) for sentence in sentences]
        self.assertEqual(len(chunks), 5)
        self.assertTrue(all(c["format"] == "wav" and c["audio"][:4] == b"RIFF" for c in chunks))
        self.assertEqual(self.speaker.said, sentences)

    @mark.req("REQ-VOI-002")
    def test_tc_voi_002_the_synthesis_input_contains_no_markup(self):
        service = self.service()
        for answer in MARKUP_ANSWERS:
            for sentence in SpeechStreamer.split(answer):
                service.synthesize(sentence)
        self.assertTrue(self.speaker.said)
        for said in self.speaker.said:
            self.assertIsNone(MARKS.search(said), said)

    @mark.req("REQ-VOI-003")
    def test_tc_voi_003_every_mood_has_a_line_or_is_silent_and_a_missing_file_is_skipped(self):
        voice_lines = VoiceLines(os.path.join(REPO, "library", "voice_lines.json"), os.path.join(REPO, "voice", "expressions"),
                                 mood_names(os.path.join(REPO, "moods.json")))
        self.assertEqual(voice_lines.uncovered(), [])
        folder = tempfile.mkdtemp()
        config = os.path.join(folder, "voice_lines.json")
        with open(config, "w") as fp:
            json.dump({"lines": {"happy": ["gone.wav", "here.wav"]}}, fp)
        with open(os.path.join(folder, "here.wav"), "wb") as fp:
            fp.write(b"RIFFhere")
        logged = []
        service = self.service(lines=VoiceLines(config, folder, ["happy"], log=logged.append), folder=folder)
        self.assertEqual(service.voice_line("happy")["audio"], b"RIFFhere")
        self.assertTrue(any("gone.wav" in message for message in logged))
        with self.assertRaises(SpeechError):
            service.voice_line("sad")


if __name__ == "__main__":
    unittest.main()
