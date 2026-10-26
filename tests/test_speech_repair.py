"""
TC-CHA-014b / REQ-CHA-014
Run with: python tests/test_speech_repair.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "helpers"))
sys.path.insert(0, os.path.dirname(HERE))

from markers import mark  # noqa: E402
from speech_stream import SpeechStreamer  # noqa: E402


def shout(text):
    return text.replace("darn", "oh dear")


def settle(text):
    """the part up to the last full stop, like chat_service.settled"""
    cut = text.rfind(".")
    return text[:cut + 1] if cut >= 0 else ""


class Spoken(SpeechStreamer):
    """records the sentences instead of opening a socket"""

    def __init__(self, **kwargs):
        super().__init__("localhost", 0, **kwargs)
        self.sent_sentences = []

    def _send(self, sentences):
        self.sent_sentences.extend(sentences)
        self._sent += len(sentences)


class SpeechRepair(unittest.TestCase):

    @mark.req('REQ-CHA-014')
    def test_update_speaks_only_the_settled_repaired_part(self):
        s = Spoken(repair=shout, settle=settle)
        s.update("Well darn. It is darn good. And then the dar")
        self.assertEqual(s.sent_sentences, ["Well oh dear."])

    @mark.req('REQ-CHA-014')
    def test_finish_speaks_the_repaired_rest_once(self):
        s = Spoken(repair=shout, settle=settle)
        s.update("Well darn. It is darn good. And then the dar")
        s.finish("Well darn. It is darn good. And then the darn end.")
        self.assertEqual(s.sent_sentences, ["Well oh dear.", "It is oh dear good.", "And then the oh dear end."])

    @mark.req('REQ-CHA-014')
    def test_without_repair_the_raw_text_is_spoken(self):
        s = Spoken()
        s.update("Well darn. It is good. And then")
        s.finish("Well darn. It is good. And then more.")
        self.assertEqual(s.sent_sentences, ["Well darn.", "It is good.", "And then more."])


if __name__ == '__main__':
    unittest.main()
