"""IF-204 speech synthesis (Chat agent to Voice synthesis): the contract suite runs against the mock (stage 1) and the real Voice synthesis
(stage 2, skipped until N-2.5 is integrated). Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_204_speech.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider, subject_for  # noqa: E402
from markers import mark                                    # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from errors import ServiceError                             # noqa: E402
from if_204_speech import SpeechMock                        # noqa: E402

IF = "IF-204"


def make(**options):
    return lambda kind: SpeechMock(**options) if kind == "mock" else subject_for(IF, kind)


def code_of(call):
    try:
        call()
    except ServiceError as err:
        return err.code
    raise AssertionError("no ServiceError raised")


@contract
class SpeechContract(unittest.TestCase):
    @mark.req("IF-204", "REQ-BE-016")
    @each_provider(IF)
    def test_a_sentence_becomes_audio(self, voice):
        """TC-IF-204-01 golden 1: wav bytes, the spoken text equals the sentence."""
        out = voice.synthesize("Hello there.")
        self.assertEqual((out["format"], out["spoken_text"]), ("wav", "Hello there."))
        self.assertIsInstance(out["audio"], bytes)
        self.assertGreater(len(out["audio"]), 0)

    @mark.req("IF-204", "REQ-BE-017")
    @each_provider(IF)
    def test_markup_and_stage_directions_are_not_spoken(self, voice):
        """TC-IF-204-02 golden 3: '<b>Hi</b> *smiles* there' speaks 'Hi there'; a sentence that is only a stage direction is empty_text."""
        self.assertEqual(voice.synthesize("<b>Hi</b> *smiles* there")["spoken_text"], "Hi there")
        self.assertEqual(code_of(lambda: voice.synthesize("*smiles*")), "empty_text")

    @mark.req("IF-204", "REQ-BE-018")
    @each_provider(IF, make(engine_down=True))
    def test_unavailable_engine_and_missing_line(self, voice):
        """TC-IF-204-03 golden 2: engine down is unavailable; a voice line that does not exist is no_line and nothing else is affected."""
        self.assertEqual(code_of(lambda: voice.synthesize("Hello.")), "unavailable")
        self.assertEqual(code_of(lambda: voice.voice_line("missing")), "no_line")
        self.assertEqual(voice.voice_line("hello")["format"], "wav")


if __name__ == "__main__":
    unittest.main()
