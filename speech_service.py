"""Speech synthesis for the Chat agent (IF-204, REQ-VOI-001, REQ-VOI-002): one sentence in, one wav chunk out.

The text is filtered first (speech_text.py), so that no markup or stage direction reaches the engine; the engine is the Speaker
(Kokoro and the voice effect) behind this one interface. Voice lines are read from a folder by name. Errors are the codes of
contracts/IF-204-speech.md: empty_text, unavailable, no_line.
"""
import os
import tempfile

try:
    from .speech_text import speech_text
    from .mia_logger import logger
except ImportError:
    from speech_text import speech_text
    from mia_logger import logger


class SpeechError(Exception):
    """code: empty_text | unavailable | no_line"""

    def __init__(self, code, detail=None):
        super().__init__(code)
        self.code, self.detail = code, detail


class SpeechService:
    def __init__(self, speaker, lines_folder, lines=None):
        # lines: the VoiceLines of the mood map (REQ-VOI-003); without it a name is a file <name>.wav in the folder
        self._speaker, self._folder, self._lines = speaker, lines_folder, lines

    def synthesize(self, sentence):
        spoken = " ".join(speech_text(sentence).split())
        if not spoken:
            raise SpeechError("empty_text")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sentence.wav")
            try:
                seconds = self._speaker.render_voice(spoken, path)
                with open(path, "rb") as fp:
                    audio = fp.read()
            except Exception as exc:                  # the chat continues without voice (IF-204)
                logger.error("speech: engine failed: %s" % exc)
                raise SpeechError("unavailable", str(exc)) from exc
        if not audio:
            raise SpeechError("unavailable", "no audio rendered")
        return {"audio": audio, "format": "wav", "spoken_text": spoken, "seconds": round(seconds, 2)}

    def voice_line(self, name):
        if self._lines is not None:
            path = self._lines.pick(name)             # a missing file is logged and skipped there; None = silent mood
            if path is None:
                raise SpeechError("no_line")
            with open(path, "rb") as fp:
                return {"audio": fp.read(), "format": "wav"}
        path = os.path.join(self._folder, str(name) + ".wav")
        if not name or os.path.basename(str(name)) != str(name) or not os.path.isfile(path):
            logger.warning("speech: voice line %r not found" % (name,))
            raise SpeechError("no_line")
        with open(path, "rb") as fp:
            return {"audio": fp.read(), "format": "wav"}
