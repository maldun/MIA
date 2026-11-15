"""Chat agent N-2.2, speak again (A-132, TD-11 option B; A-133): TC-CHA-030 to TC-CHA-034 and TC-CHA-037 with a fake voice route (TR-VOICE-001, TR-VOICE-003).
The fake is the injected `speak(text, should_stop)` of ChatService; it only proves the Chat agent's side of the call (the sound server's side is TC-CHA-036).
Run with: python tests/test_chat_speak_again.py"""
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark                                  # noqa: E402
from chat_log import ChatLog                              # noqa: E402
from chat_service import ChatService                      # noqa: E402
from moods import MoodTracker                             # noqa: E402

WAIT = 5            # seconds a test waits for something that must happen (a red run spends it once per wait)


class FakeVoice:
    """the fake voice route: records each text with its start and end, can block until told to stop, can fail (TR-VOICE-001)"""
    def __init__(self, delay=0.0, block=False, fail=False):
        self.delay, self.block, self.fail = delay, block, fail
        self.calls = []                       # [{"text", "start", "end"}], in the order the calls began
        self.started = threading.Event()      # the first call has begun
        self.stop_seen = threading.Event()    # a blocked call saw its should_stop become true
        self._lock = threading.Lock()

    def __call__(self, text, should_stop):
        call = {"text": text, "start": time.monotonic(), "end": None}
        with self._lock:
            self.calls.append(call)
        self.started.set()
        if self.fail:
            raise OSError("voice route down")
        if self.block:
            while not should_stop():
                time.sleep(0.05)              # the fake polls every 0.05 s (test-spec TC-CHA-032)
            self.stop_seen.set()
        else:
            time.sleep(self.delay)
        call["end"] = time.monotonic()

    @property
    def texts(self):
        return [call["text"] for call in self.calls]


class Asked:
    """one speak-again request in a thread of its own: it may return at once or only when the speech has ended, the test must not depend on which"""
    def __init__(self, chat, message_id):
        self.result = self.error = None
        self.thread = threading.Thread(target=self._run, args=(chat, message_id), daemon=True)
        self.thread.start()

    def _run(self, chat, message_id):
        try:
            self.result = chat.speak_again(message_id)
        except Exception as exc:                   # noqa: BLE001 - the test reports it
            self.error = exc

    def done(self, seconds=WAIT):
        self.thread.join(seconds)
        return not self.thread.is_alive()


class SpeakAgainTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.events = []
        self.answers = []
        self.log = ChatLog(os.path.join(self.dir, "log.jsonl"))
        self.voice = FakeVoice()

    def chat(self, voice=None):
        """the Chat agent with the fake voice route and a fake model that gives the scripted answers (ASM-N2-001); answers are made at once"""
        return ChatService(lambda event, payload: self.events.append((event, payload)), self.log, MoodTracker(os.path.join(ROOT, "moods.json")),
                           lambda text, on_delta, on_emotion, should_stop: self.answers.pop(0), queue_size=5, user_limit=2, spawn=lambda target: target(),
                           speak=voice or self.voice)

    def stored_answer(self, chat, text):
        """an answer of MIA in the log; the user's question is only the way it gets there"""
        self.answers.append(text)
        chat.send("hi", author="anna")
        return self.log.last("assistant")["id"]

    def chunks(self, message_id):
        """(index, sentence) of the audio_chunk events of one message, in the order they were sent"""
        return [(p["index"], p["sentence"]) for event, p in self.events if event == "audio_chunk" and p["id"] == message_id]

    def last_status(self):
        """the newest chat_status event since the last events.clear()"""
        published = [payload for event, payload in self.events if event == "chat_status"]
        self.assertTrue(published, "no chat_status was published")
        return published[-1]

    # TC-CHA-030
    @mark.req("REQ-CHA-030", "REQ-CHA-031")
    def test_speak_again_hands_the_spoken_sentences_in_order_to_the_voice_route(self):
        """TC-CHA-030 (REQ-CHA-030, REQ-CHA-031): speak again of a stored answer and of a stored question of a skill hands exactly their sentences, in order, to the voice route.
        Example: the answer "One. Two. Three." gives the calls "One.", "Two.", "Three."; the question "Shall I go on?" gives one call."""
        # Given a stored answer "One. Two. Three." and a stored question of a skill "Shall I go on?" (written by hand, not taken from the splitting code: TR-VOICE-003)
        chat = self.chat()
        answer = self.stored_answer(chat, "One. Two. Three.")
        question = self.log.append("assistant", "Shall I go on?")["id"]
        self.events.clear()
        # When the user asks to speak the answer again, and then the question
        first, second = Asked(chat, answer), None
        self.assertTrue(first.done(), "the first request did not end")
        second = Asked(chat, question)
        self.assertTrue(second.done(), "the second request did not end")
        # Then the fake got the four texts in this order and nothing else, the results and the events are as before
        self.assertEqual(self.voice.texts, ["One.", "Two.", "Three.", "Shall I go on?"])
        self.assertEqual((first.result, second.result), ({"sentences": 3}, {"sentences": 1}))
        self.assertEqual(self.chunks(answer) + self.chunks(question), [(0, "One."), (1, "Two."), (2, "Three."), (0, "Shall I go on?")])

    # TC-CHA-031
    @mark.req("REQ-CHA-030")
    def test_the_voice_route_gets_the_stored_text_after_the_speech_filter(self):
        """TC-CHA-031 (REQ-CHA-030): the voice route gets the stored text without marks and stage directions, as a live answer does.
        Example: "*waves* Hello **there**. Bye." gives the calls "Hello there." and "Bye.\""""
        # Given a stored answer with markup and a stage direction
        chat = self.chat()
        answer = self.stored_answer(chat, "*waves* Hello **there**. Bye.")
        # When the user asks to speak it again
        asked = Asked(chat, answer)
        self.assertTrue(asked.done(), "the request did not end")
        # Then the fake got the two sentences the page would show, no mark and no stage direction
        self.assertEqual(self.voice.texts, ["Hello there.", "Bye."])

    # TC-CHA-032
    @mark.req("REQ-CHA-032")
    def test_stop_ends_a_speak_again_that_is_running_when_no_answer_is_generated(self):
        """TC-CHA-032 (REQ-CHA-032): a stop request ends a spoken-again playback that is running, and no further sentence is handed over.
        Example: the fake blocks on "One." of "One. Two. Three."; stop; its should_stop turns true, its call ends, "Two." is never handed over."""
        # Given a stored answer of three sentences, a fake voice route that blocks until it is told to stop, and no answer being generated
        self.voice = FakeVoice(block=True)
        chat = self.chat()
        answer = self.stored_answer(chat, "One. Two. Three.")
        # When the user asks to speak it again, and then presses stop
        asked = Asked(chat, answer)
        self.assertTrue(self.voice.started.wait(WAIT), "the voice route was not called")
        chat.stop()
        # Then the fake was told to stop, its call and the request ended within 1 s, and no further sentence was handed over
        self.assertTrue(self.voice.stop_seen.wait(1), "the voice route was never told to stop")
        self.assertTrue(asked.done(1), "the request did not end within 1 s of the stop")
        time.sleep(0.3)                                    # a sentence handed over late would show now
        self.assertEqual(self.voice.texts, ["One."])

    @mark.req("REQ-CHA-032")
    def test_a_stop_with_nothing_speaking_changes_nothing(self):
        """TC-CHA-032 (REQ-CHA-032): a stop with nothing speaking is forgotten: the next speak again is spoken to the end.
        Example: stop, then speak again of "One. Two." gives the calls "One." and "Two.\""""
        # Given a stored answer of two sentences, nothing speaking, a stop pressed
        chat = self.chat()
        answer = self.stored_answer(chat, "One. Two.")
        chat.stop()
        # When the user asks to speak it again
        asked = Asked(chat, answer)
        self.assertTrue(asked.done(), "the request did not end")
        # Then both sentences are handed over: the earlier stop did not cancel it
        self.assertEqual(self.voice.texts, ["One.", "Two."])

    # TC-CHA-033
    @mark.req("REQ-CHA-033")
    def test_without_a_voice_route_the_request_still_answers_and_one_error_line_is_logged(self):
        """TC-CHA-033 (REQ-CHA-033): a failing voice route does not fail the request, the next message, or the page; one error line is logged.
        Example: the fake raises OSError for "Alpha. Beta."; the result is {"sentences": 2}, one ERROR record, no new event but audio_chunk and chat_status."""
        # Given a fake voice route that fails with a connection error and a stored answer of two sentences
        self.voice = FakeVoice(fail=True)
        chat = self.chat()
        answer = self.stored_answer(chat, "Alpha. Beta.")
        self.events.clear()
        stored = len(self.log)
        # When the user asks to speak it again, and then sends a normal message
        with self.assertLogs(level="ERROR") as logged:
            asked = Asked(chat, answer)
            self.assertTrue(asked.done(), "the request did not end")
        events_of_the_request = [event for event, _ in self.events]
        self.answers.append("Next answer.")
        chat.send("and now?", author="anna")
        # Then the request returned the count, one error line is in the log, nothing but audio_chunk and the status reached the page, nothing was stored, the message was answered
        self.assertEqual((asked.result, asked.error), ({"sentences": 2}, None))
        self.assertEqual(len(logged.records), 1)
        self.assertLessEqual(set(events_of_the_request), {"audio_chunk", "chat_status"})     # no chat_message or note; the status events are those of REQ-CHA-035 (A-133)
        self.assertFalse(chat.status()["busy"])                                                  # a failed repeat does not leave the stop button
        self.assertEqual(len(self.log), stored + 2)        # only the question and the answer of the normal message
        self.assertEqual(self.log.last("assistant")["text"], "Next answer.")

    # TC-CHA-034
    @mark.req("REQ-CHA-034")
    def test_two_speak_again_requests_do_not_overlap(self):
        """TC-CHA-034 (REQ-CHA-034): the second of two speak-again requests is spoken after the first has ended.
        Example: each call takes 0.2 s; "Second answer." starts no earlier than "First answer." ended."""
        # Given a fake voice route whose call takes 0.2 s and records its start and end, and two stored answers of one sentence each
        self.voice = FakeVoice(delay=0.2)
        chat = self.chat()
        first_id = self.stored_answer(chat, "First answer.")
        second_id = self.stored_answer(chat, "Second answer.")
        # When the user asks to speak answer 1 again and at once answer 2 again
        first = Asked(chat, first_id)
        self.assertTrue(self.voice.started.wait(WAIT), "the voice route was not called")
        second = Asked(chat, second_id)
        self.assertTrue(first.done() and second.done(), "a request did not end")
        # Then the call of answer 2 started after the call of answer 1 had ended
        self.assertEqual(self.voice.texts, ["First answer.", "Second answer."])
        self.assertGreaterEqual(self.voice.calls[1]["start"], self.voice.calls[0]["end"])


    # TC-CHA-037 (A-133)
    @mark.req("REQ-CHA-035")
    def test_the_status_is_busy_and_speaking_while_a_message_is_spoken_again(self):
        """TC-CHA-037 (REQ-CHA-035): while a speak again runs or waits, the status is busy with the activity speaking, so the page offers its stop button.
        Example: the fake blocks on "One."; a second request waits behind it; the last chat_status is {"busy": true, "activity": "speaking"}."""
        # Given a fake voice route that blocks until it is told to stop, a stored answer of two sentences, no answer being generated
        self.voice = FakeVoice(block=True)
        chat = self.chat()
        answer = self.stored_answer(chat, "One. Two.")
        self.events.clear()
        # When the user asks to speak it again, and a second request waits behind the first
        first = Asked(chat, answer)
        self.assertTrue(self.voice.started.wait(WAIT), "the voice route was not called")
        second = Asked(chat, answer)
        time.sleep(0.2)                                    # the second request is in line behind the first before the stop comes
        # Then the published status and the status of the service are busy and speaking
        status = self.last_status()
        self.assertEqual((status["busy"], status["activity"]), (True, "speaking"))
        self.assertEqual((chat.status()["busy"], chat.status()["activity"]), (True, "speaking"))
        chat.stop()
        self.assertTrue(first.done(1) and second.done(1), "a request did not end within 1 s of the stop")

    @mark.req("REQ-CHA-036")
    def test_the_status_is_as_before_after_a_stop_and_after_a_playback_that_ended_by_itself(self):
        """TC-CHA-037 (REQ-CHA-036): after a stop and after a playback that ended by itself, the status is not busy and not speaking.
        Example: stop of a blocked repeat, then a repeat of "One. Two." that ends alone: both times the last chat_status is {"busy": false, "activity": not "speaking"}."""
        # Given a fake voice route that blocks, a stored answer of two sentences, no answer being generated
        self.voice = FakeVoice(block=True)
        chat = self.chat()
        answer = self.stored_answer(chat, "One. Two.")
        self.events.clear()
        # When a repeat is stopped
        stopped = Asked(chat, answer)
        self.assertTrue(self.voice.started.wait(WAIT), "the voice route was not called")
        chat.stop()
        self.assertTrue(stopped.done(1), "the request did not end within 1 s of the stop")
        # Then the status is as before
        status = self.last_status()
        self.assertEqual((status["busy"], status["activity"] != "speaking"), (False, True))
        self.assertEqual((chat.status()["busy"], chat.status()["activity"] != "speaking"), (False, True))
        # When a repeat with a fake that does not block ends by itself
        self.voice = FakeVoice()
        chat = self.chat()
        answer = self.stored_answer(chat, "One. Two.")
        self.events.clear()
        ended = Asked(chat, answer)
        self.assertTrue(ended.done(), "the request did not end")
        # Then it was busy and speaking while it ran, and the last status is as before
        published = [payload for event, payload in self.events if event == "chat_status"]
        self.assertIn((True, "speaking"), [(p["busy"], p["activity"]) for p in published])
        self.assertEqual((published[-1]["busy"], published[-1]["activity"] != "speaking"), (False, True))


if __name__ == "__main__":
    unittest.main()
