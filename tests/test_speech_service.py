"""
IF-204 provider (speech_service.py), REQ-VOI-001, REQ-VOI-002: one sentence in, one wav chunk out, markup removed first,
the errors of contracts/IF-204-speech.md. The engine is a fake Speaker: no TTS packages needed.
Run: python tests/test_speech_service.py
"""
import importlib
import os
import sys
import tempfile
import unittest
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)


class FakeSpeaker:
    """writes a 0.5 s silent wav like Speaker.render_voice; records what it was asked to say"""
    def __init__(self, down=False):
        self.said, self.down = [], down

    def render_voice(self, msg, output_file):
        if self.down:
            raise RuntimeError("model missing")
        self.said.append(msg)
        with wave.open(output_file, "wb") as fp:
            fp.setnchannels(1)
            fp.setsampwidth(2)
            fp.setframerate(8000)
            fp.writeframes(b"\0\0" * 4000)
        return 0.5


class SpeechTextMarkupTest(unittest.TestCase):
    def test_html_tags_are_not_spoken(self):
        say = importlib.import_module("MIA.speech_text").speech_text
        self.assertEqual(say("<b>Hi</b> *smiles* there"), "Hi there")
        self.assertEqual(say("a < b and c > d"), "a < b and c > d")      # no tag: stays


class SpeechServiceTest(unittest.TestCase):
    def setUp(self):
        self.mod = importlib.import_module("MIA.speech_service")
        self.folder = tempfile.mkdtemp()
        with open(os.path.join(self.folder, "hello.wav"), "wb") as fp:
            fp.write(b"RIFFhello")

    def service(self, **kw):
        self.speaker = FakeSpeaker(**kw)
        return self.mod.SpeechService(self.speaker, self.folder)

    def test_a_sentence_becomes_one_wav_chunk(self):          # REQ-VOI-001
        out = self.service().synthesize("Hello there.")
        self.assertEqual((out["format"], out["spoken_text"], out["seconds"]), ("wav", "Hello there.", 0.5))
        self.assertEqual(out["audio"][:4], b"RIFF")

    def test_five_sentences_five_chunks(self):                # AC-13
        service = self.service()
        for sentence in ["One.", "Two.", "Three.", "Four.", "Five."]:
            service.synthesize(sentence)
        self.assertEqual(self.speaker.said, ["One.", "Two.", "Three.", "Four.", "Five."])

    def test_markup_never_reaches_the_engine(self):           # REQ-VOI-002
        service = self.service()
        for text in ["<b>Hi</b> *smiles* there", "**Hi** `there`", "# Hi there", "[Hi there](http://x.org)"]:
            self.assertEqual(service.synthesize(text)["spoken_text"], "Hi there")
        self.assertEqual(set(self.speaker.said), {"Hi there"})

    def test_only_a_stage_direction_is_empty_text(self):
        with self.assertRaises(self.mod.SpeechError) as ctx:
            self.service().synthesize("*smiles*")
        self.assertEqual(ctx.exception.code, "empty_text")
        self.assertEqual(self.speaker.said, [])

    def test_engine_failure_is_unavailable(self):
        with self.assertRaises(self.mod.SpeechError) as ctx:
            self.service(down=True).synthesize("Hello.")
        self.assertEqual(ctx.exception.code, "unavailable")

    def test_voice_line_and_missing_line(self):
        service = self.service()
        self.assertEqual(service.voice_line("hello"), {"audio": b"RIFFhello", "format": "wav"})
        for name in ["missing", "../hello", ""]:
            with self.assertRaises(self.mod.SpeechError) as ctx:
                service.voice_line(name)
            self.assertEqual(ctx.exception.code, "no_line")


class MoodLineDeliveryTest(unittest.TestCase):
    """REQ-VOI-003: a name given by the Chat agent is a mood of library/voice_lines.json; its audio is delivered, a missing file is skipped"""
    def setUp(self):
        self.mod = importlib.import_module("MIA.speech_service")
        self.folder = tempfile.mkdtemp()
        self.logged = []
        config = os.path.join(self.folder, "voice_lines.json")
        with open(config, "w") as fp:
            fp.write('{"lines": {"annoyed": ["grr.wav", "gone.wav"], "happy": []}, "silent": ["neutral"]}')
        with open(os.path.join(self.folder, "grr.wav"), "wb") as fp:
            fp.write(b"RIFFgrr")
        lines = importlib.import_module("MIA.voice_lines").VoiceLines(config, self.folder, ["annoyed", "happy", "neutral"], log=self.logged.append)
        self.service = self.mod.SpeechService(FakeSpeaker(), self.folder, lines=lines)

    def test_the_audio_of_a_mood_is_delivered_and_the_missing_file_is_skipped(self):
        for _ in range(10):
            self.assertEqual(self.service.voice_line("annoyed"), {"audio": b"RIFFgrr", "format": "wav"})
        self.assertTrue(any("gone.wav" in message for message in self.logged))

    def test_a_silent_mood_has_no_line(self):
        for mood in ["happy", "neutral", "unknown"]:
            with self.assertRaises(self.mod.SpeechError) as ctx:
                self.service.voice_line(mood)
            self.assertEqual(ctx.exception.code, "no_line")


if __name__ == "__main__":
    unittest.main()
