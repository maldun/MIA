"""
TC-RUN-002 (REQ-RUN-002) and TC-RUN-003 (REQ-RUN-003): /light! and /full! ask for confirmation, the switch applies to all and unloads the previous model
from the GPU; a model server that does not answer is said in one plain sentence, by the client of the chat and of the runner alike and as the error of a run.
The Ollama client is a fake.
Run with: python tests/test_runner_model_server.py
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                                        # noqa: E402
import chat_service                                                             # noqa: E402
from communicator import Communicator                                           # noqa: E402
from pipeline import Runner                                                     # noqa: E402
from pipeline_model import UNREACHABLE, ModelServerUnreachable, ModelTurns, OllamaModel, TurnClient  # noqa: E402
from skill_store import parse_skill                                             # noqa: E402

SKILL = """---
name: asking
version: 1
description: one model step
budget: {steps: 5, seconds: 60}
model: {profile: light}
pipeline: asking
---
## prompts
### ask
Say something about {{input.text}}.
"""
GRAPH = {"name": "asking", "version": 1, "result": "a", "nodes": [{"id": "a", "kind": "model", "prompt": "ask", "output": "a"}]}
MESSAGE = [{"role": "user", "content": "hi"}]


class DownClient:
    """an ollama client of a server that is not running: the error the ollama library raises"""

    def chat(self, **kwargs):
        if kwargs.get("stream"):
            return self._stream()
        raise ConnectionError("Failed to connect to Ollama. Please check that Ollama is downloaded, running and accessible.")

    def _stream(self):
        raise ConnectionError("Failed to connect to Ollama. Please check that Ollama is downloaded, running and accessible.")
        yield None


class RecordingClient:
    def __init__(self):
        self.generated = []

    def generate(self, **kwargs):
        self.generated.append(kwargs)
        return {}


def communicator(client):
    comm = Communicator.__new__(Communicator)
    comm.client = client
    comm._profiles = {"full": ("big:26b", {"num_ctx": 8192}), "light": ("small:12b", {"num_ctx": 8192})}
    comm.version, comm.llm_options, comm.profile = "big:26b", {"num_ctx": 8192}, "full"
    return comm


class ModelServerTests(unittest.TestCase):

    @mark.req("REQ-RUN-003")
    def test_a_down_server_is_one_plain_sentence(self):
        """TC-RUN-003: a down server is reported as a plain sentence.

        Example: chat(model="m") -> ModelServerUnreachable(UNREACHABLE)
        """
        # Given: a TurnClient using DownClient
        client = TurnClient(DownClient(), ModelTurns(), "chat")
        # When: the client tries to chat
        with self.assertRaises(ModelServerUnreachable) as caught:
            client.chat(model="m", messages=MESSAGE)
        # Then: the exception message is exactly UNREACHABLE
        self.assertEqual(str(caught.exception), UNREACHABLE)
        self.assertNotIn("Error", UNREACHABLE)

    @mark.req("REQ-RUN-003")
    def test_a_down_server_while_a_stream_is_read_is_the_same_sentence(self):
        """TC-RUN-003: a down server during streaming is reported as a plain sentence.

        Example: next(stream) -> ModelServerUnreachable(UNREACHABLE)
        """
        # Given: a TurnClient using DownClient with streaming enabled
        stream = TurnClient(DownClient(), ModelTurns(), "chat").chat(model="m", messages=MESSAGE, stream=True)
        # When: the next item is read from the stream
        with self.assertRaises(ModelServerUnreachable) as caught:
            next(stream)
        # Then: the exception message is exactly UNREACHABLE
        self.assertEqual(str(caught.exception), UNREACHABLE)

    @mark.req("REQ-RUN-003")
    def test_a_run_with_the_server_down_ends_with_the_plain_sentence(self):
        """TC-RUN-003: a run against a down server ends with the plain sentence as the error.

        Example: Runner.run() -> (error, UNREACHABLE)
        """
        # Given: a Runner with a model that uses a DownClient
        model = OllamaModel(TurnClient(DownClient(), ModelTurns(), "background"), lambda profile: ("small:12b", None), lambda: ("small:12b", None))
        # When: the run is executed
        result = Runner(model=model).run(parse_skill(SKILL, "asking.md"), GRAPH, {"text": "towers"})
        # Then: the run status is error and the error message is UNREACHABLE
        self.assertEqual((result.status, result.error), ("error", UNREACHABLE))

    @mark.req("REQ-RUN-002")
    def test_light_and_full_ask_for_confirmation(self):
        """TC-RUN-002: the /light! and /full! commands both require confirmation.

        Example: chat_service.COMMANDS -> both confirm fields are True
        """
        # Given: the list of commands from chat_service
        confirm = {c["command"]: c["confirm"] for c in chat_service.COMMANDS}
        # Then: both confirmation fields are True
        self.assertEqual((confirm["/light!"], confirm["/full!"]), (True, True))

    @mark.req("REQ-RUN-002")
    def test_the_switch_unloads_the_previous_model(self):
        """TC-RUN-002: switching to the light profile unloads the previous full model.

        Example: communicator.set_profile("light") -> one generate call with keep_alive=0
        """
        # Given: a communicator with a RecordingClient
        client = RecordingClient()
        comm = communicator(client)
        # When: the profile is switched to light
        self.assertTrue(comm.set_profile("light"))
        # Then: the version is updated and the old model was unloaded
        self.assertEqual(comm.version, "small:12b")
        self.assertEqual(client.generated, [{"model": "big:26b", "keep_alive": 0}])

    @mark.req("REQ-RUN-002")
    def test_switching_to_the_same_model_unloads_nothing(self):
        """TC-RUN-002: switching to the same model does not trigger an unload.

        Example: communicator.set_profile("full") -> no generate calls
        """
        # Given: a communicator with a RecordingClient
        client = RecordingClient()
        comm = communicator(client)
        # When: the profile is switched to full (already full)
        comm.set_profile("full")
        # Then: no unload call was made
        self.assertEqual(client.generated, [])


if __name__ == "__main__":
    unittest.main()
