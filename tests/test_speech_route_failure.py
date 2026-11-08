"""Voice route of speak again with no sound server (A-132; verification report F1; REQ-CHA-033, TR-VOICE-001): the route built from the real SpeechStreamer on a closed
port raises, so the chat service logs one error line for the request and tries one connection, not one per sentence.
`speak_text` is the body of web_app.speak_answer (web_app starts the whole app and is not imported here). Run with: python tests/test_speech_route_failure.py"""
import logging
import os
import shutil
import socket
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark                                  # noqa: E402
import speech_stream                                      # noqa: E402
from chat_log import ChatLog                              # noqa: E402
from chat_service import ChatService                      # noqa: E402
from moods import MoodTracker                             # noqa: E402


def closed_port():
    """a port on which nothing listens"""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Records(logging.Handler):
    def __init__(self):
        super().__init__(logging.ERROR)
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


class RouteFailureTest(unittest.TestCase):
    def setUp(self):
        self.port = closed_port()
        self.records = Records()
        speech_stream.logger.addHandler(self.records)
        self.addCleanup(speech_stream.logger.removeHandler, self.records)

    @mark.req("REQ-CHA-033")
    def test_the_route_raises_when_the_sound_server_is_not_reachable(self):
        """REQ-CHA-033: the real streamer on a closed port does not hide the failure from its caller.
        Example: speak_text("127.0.0.1", closed port, "One.") raises OSError."""
        # Given a closed port, When one text is sent through the route, Then OSError is raised
        with self.assertRaises(OSError):
            speech_stream.speak_text("127.0.0.1", self.port, "One.")

    @mark.req("REQ-CHA-033")
    def test_a_failed_repeat_of_five_sentences_makes_one_connection_attempt_and_one_chat_service_line(self):
        """REQ-CHA-033: one error line of the chat service and one connection attempt for a repeat of five sentences on a closed port.
        Example: "One. Two. Three. Four. Five." on a closed port: 1 create_connection call, 1 line "Speak again: the voice route failed"."""
        # Given a chat service whose voice route is built from the real SpeechStreamer on a closed port, and an answer of five sentences
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        log = ChatLog(os.path.join(directory, "log.jsonl"))
        route = lambda sentence, should_stop: speech_stream.speak_text("127.0.0.1", self.port, sentence, should_stop)
        chat = ChatService(lambda event, payload: None, log, MoodTracker(os.path.join(ROOT, "moods.json")), lambda *a: "", queue_size=5, user_limit=2,
                           spawn=lambda target: target(), speak=route)
        answer = log.append("assistant", "One. Two. Three. Four. Five.")["id"]
        ours = Records()
        import chat_service
        chat_service.logger.addHandler(ours)
        self.addCleanup(chat_service.logger.removeHandler, ours)
        # When the user asks to speak it again
        with mock.patch.object(speech_stream.socket, "create_connection", wraps=socket.create_connection) as connect:
            chat.speak_again(answer)
        # Then one connection was tried, and the chat service logged its line once
        self.assertEqual(connect.call_count, 1)
        self.assertEqual(sum("Speak again: the voice route failed" in line for line in ours.lines), 1)
        self.assertEqual(len(self.records.lines), 2)         # honestly two ERROR records: the streamer's "Sound server not reachable" and the chat service's line
        self.assertFalse(chat.status()["busy"])


if __name__ == "__main__":
    unittest.main()
