"""
Tests for what MIA's voice says (speech_text.py): markdown marks and *actions* are removed; also through the streaming path
(speech_stream.py) and the request of the hourly time check. Run with the MIA virtualenv: python tests/test_speech_text.py
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


class FilterTest(unittest.TestCase):
    def setUp(self):
        self.say = importlib.import_module("MIA.speech_text").speech_text

    def test_plain_text_is_unchanged(self):
        self.assertEqual(self.say("Hello there. How are you?"), "Hello there. How are you?")

    def test_actions_in_single_asterisks_are_not_spoken(self):
        self.assertEqual(self.say("*smiles* Hello there!"), "Hello there!")
        self.assertEqual(self.say("Hello *waves happily* how are you?"), "Hello how are you?")
        self.assertEqual(self.say("Sure *nods*, I can do that *grins*."), "Sure, I can do that.")
        self.assertEqual(self.say("*laughs*"), "")

    def test_an_action_may_span_a_line_break_but_not_a_paragraph(self):
        self.assertEqual(self.say("*smiles and\nwaves* Hi"), "Hi")
        self.assertEqual(self.say("a *b\n\nc* d"), "a b\nc d")      # not an action: stray marks are only removed

    def test_strong_emphasis_keeps_the_words(self):
        self.assertEqual(self.say("This is **really** important."), "This is really important.")
        self.assertEqual(self.say("This is __really__ important."), "This is really important.")
        self.assertEqual(self.say("A ***big*** deal"), "A big deal")

    def test_underscore_italics_keep_the_words_but_names_with_underscores_stay(self):
        self.assertEqual(self.say("an _italic_ word"), "an italic word")
        self.assertEqual(self.say("the file my_file_name is here"), "the file my_file_name is here")

    def test_lists_headings_quotes_rules(self):
        text = "# Title\n\n- one\n* two\n+ three\n> quoted words\n---\n1. first"
        self.assertEqual(self.say(text), "Title\none\ntwo\nthree\nquoted words\n1. first")

    def test_links_images_urls_and_code(self):
        self.assertEqual(self.say("See [the docs](https://example.org/a) now."), "See the docs now.")
        self.assertEqual(self.say("Look ![a cat](https://x.org/cat.png) here"), "Look here")
        self.assertEqual(self.say("Go to https://example.org/page today."), "Go to today.")
        self.assertEqual(self.say("Use `ls -l` please"), "Use ls -l please")
        self.assertEqual(self.say("Before\n```python\nprint(1)\n```\nAfter"), "Before\nAfter")

    def test_strikethrough_and_tables(self):
        self.assertEqual(self.say("~~old~~ new"), "old new")
        self.assertEqual(self.say("| a | b |\n|---|---|\n| 1 | 2 |"), "a b\n1 2")

    def test_stray_asterisks_and_spacing(self):
        self.assertEqual(self.say("2 * 3 = 6"), "2 3 = 6")
        self.assertEqual(self.say("Wait *"), "Wait")
        self.assertEqual(self.say("Hello *smiles* ."), "Hello.")

    def test_nothing_left_gives_empty_text(self):
        for text in ["", None, "***", "*sighs* *shrugs*", "  \n  "]:
            self.assertEqual(self.say(text), "")

    def test_an_unfinished_action_is_cut_while_streaming(self):
        self.assertEqual(self.say("Hello *waves", final=False), "Hello")
        self.assertEqual(self.say("Hello *", final=False), "Hello")
        self.assertEqual(self.say("Hello *waves* there *sm", final=False), "Hello there")
        self.assertEqual(self.say("I love **bold", final=False), "I love bold")
        self.assertEqual(self.say("Hello *waves", final=True), "Hello waves")      # at the end only the mark goes

    def test_it_can_be_applied_twice(self):
        for text in ["*smiles* Hello **there**, [x](http://y.z)!", "# A\n- b\n> c", "plain", "a * b"]:
            once = self.say(text)
            self.assertEqual(self.say(once), once, text)


class StreamTest(unittest.TestCase):
    def setUp(self):
        self.stream = importlib.import_module("MIA.speech_stream")

    def run_stream(self, chunks):
        """feeds growing text like the model does; returns the sentences that were sent, in order"""
        sent = []
        streamer = self.stream.SpeechStreamer("localhost", 1)
        streamer._send = lambda sentences: (sent.extend(sentences), setattr(streamer, "_sent", streamer._sent + len(sentences)))
        text = ""
        for chunk in chunks:
            text += chunk
            streamer.update(text)
        streamer.finish(text)
        return sent

    def test_actions_never_reach_the_voice_even_when_split_over_chunks(self):
        chunks = ["*smi", "les and wa", "ves* Hello the", "re! I am *gri", "nning* glad. ", "You **are** back", ". *waves*"]
        sent = self.run_stream(chunks)
        self.assertEqual(sent, ["Hello there!", "I am glad.", "You are back."])
        self.assertFalse([s for s in sent if "*" in s])

    def test_a_long_action_over_several_sentences(self):
        sent = self.run_stream(["*She looks at you. Then she smiles. ", "Very slowly.* ", "Welcome back. ", "How was your day?"])
        self.assertEqual(sent, ["Welcome back.", "How was your day?"])

    def test_markdown_answer(self):
        sent = self.run_stream(["# Plan\n\n", "- first **thing**.\n", "- second thing.\n"])
        self.assertEqual(sent, ["Plan", "first thing.", "second thing."])

    def test_nothing_is_sent_for_an_answer_of_only_actions(self):
        self.assertEqual(self.run_stream(["*sighs* ", "*shrugs*"]), [])


class TimeCheckTest(unittest.TestCase):
    def test_the_voice_request_of_the_time_check_is_filtered(self):
        os.environ.setdefault("MIA_TEST", "1")
        wa = importlib.import_module("MIA.web_app")
        sent = []

        class FakeSocket:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def connect(self, address):
                pass

            def sendall(self, data):
                sent.append(data.decode())

            def recv(self, size):
                return b'{"SOUND": "played", "TIME": "x"}'

        original = wa.socket.socket
        wa.socket.socket = lambda *a, **k: FakeSocket()
        try:
            wa.send_voice_request("*yawns* It is **noon** already.")
            wa.send_voice_request("*sighs*")
        finally:
            wa.socket.socket = original
        self.assertEqual(len(sent), 1)
        self.assertIn("It is noon already.", sent[0])
        self.assertNotIn("*", sent[0])


class PromptTest(unittest.TestCase):
    def test_the_model_is_told_the_rule(self):
        communicator = importlib.import_module("MIA.communicator")
        text = communicator.EMOTION_QUESTION
        self.assertIn("single asterisks", text)
        self.assertIn("not spoken", text)
        self.assertIn("emphasis", text)


if __name__ == "__main__":
    unittest.main()
