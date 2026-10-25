"""IF-103 model server: the contract suite runs against the mock (stage 1) and the real Ollama (stage 2, skipped until the model
server is part of the run). Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_103_model_server.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider, subject_for  # noqa: E402
from markers import mark                                    # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from errors import ModelServerError                         # noqa: E402
from if_103_model_server import ModelServerMock             # noqa: E402

IF = "IF-103"
ASK = [{"role": "user", "content": "2+2?"}]
SCHEMA = {"type": "object", "required": ["verdict", "reason"]}


def make(**options):
    """The mock is scripted per test; the real server cannot be scripted, so its test is skipped until stage 2 supplies a scripted proxy."""
    return lambda kind: ModelServerMock(**options) if kind == "mock" else subject_for(IF, kind)


@contract
class ModelServerContract(unittest.TestCase):
    @mark.req("IF-103", "REQ-BE-062")
    @each_provider(IF, make(replies=["4"]))
    def test_a_text_reply_comes_with_token_counts(self, model):
        """TC-IF-103-01 golden 1: message, model and token counts."""
        reply = model.chat(ASK, model="MP-light")
        self.assertEqual(reply["message"], "4")
        self.assertEqual(reply["model"], "MP-light")
        self.assertGreater(reply["tokens_in"], 0)
        self.assertGreater(reply["tokens_out"], 0)

    @mark.req("IF-103", "NFR-2")
    @each_provider(IF, make(replies=['{"verdict": "supported", "reason": "found"}', {"verdict": "unclear", "reason": "none"}]))
    def test_with_a_schema_the_message_is_a_dict(self, model):
        """TC-IF-103-02: a JSON text or a dict that has the required keys is returned as a dict."""
        self.assertEqual(model.chat(ASK, schema=SCHEMA)["message"], {"verdict": "supported", "reason": "found"})
        self.assertEqual(model.chat(ASK, schema=SCHEMA)["message"]["verdict"], "unclear")

    @mark.req("IF-103", "NFR-2")
    @each_provider(IF, make(replies=["not json", {"verdict": "supported"}]))
    def test_a_reply_that_breaks_the_schema_is_bad_output(self, model):
        """TC-IF-103-03 golden 2: text that is not JSON and JSON that lacks a required key are bad_output with the raw reply in detail."""
        for raw in ("not json", {"verdict": "supported"}):
            with self.assertRaises(ModelServerError) as caught:
                model.chat(ASK, schema=SCHEMA)
            self.assertEqual(caught.exception.code, "bad_output")
            self.assertEqual(caught.exception.detail, raw)

    @mark.req("IF-103", "REQ-BE-044")
    @each_provider(IF, make(down=True))
    def test_unreachable_server(self, model):
        """TC-IF-103-04 golden 2: a server that is not running is 'unreachable'; the caller can say so in plain words."""
        with self.assertRaises(ModelServerError) as caught:
            model.chat(ASK)
        self.assertEqual(caught.exception.code, "unreachable")

    @mark.req("IF-103")
    @each_provider(IF, make(timeout=True))
    def test_timeout(self, model):
        """TC-IF-103-05: no answer in time is 'timeout'."""
        with self.assertRaises(ModelServerError) as caught:
            model.chat(ASK)
        self.assertEqual(caught.exception.code, "timeout")

    @mark.req("IF-103")
    @each_provider(IF, make())
    def test_an_empty_message_list_is_a_caller_error(self, model):
        """TC-IF-103-06 golden 3: no messages is a ValueError of the caller, not a model error."""
        with self.assertRaises(ValueError):
            model.chat([])


if __name__ == "__main__":
    unittest.main()
