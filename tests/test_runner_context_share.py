"""
TC-RUN-005 (REQ-RUN-005): a model input estimated over half of the context window (4 characters a token) is refused before the call, with a plain error
that names the step, the estimate and the limit; the refused call is not counted. The limit is half of num_ctx, 4096 by default. The model is a fake.
Run with: python tests/test_runner_context_share.py
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                         # noqa: E402
from pipeline import Runner                      # noqa: E402
from skill_store import parse_skill              # noqa: E402

SKILL = """---
name: sized
version: 1
description: one model step
budget: {steps: 5, seconds: 60}
model: {profile: light}
pipeline: sized
---
## prompts
### ask
Read this: {{input.text}}
"""
GRAPH = {"name": "sized", "version": 1, "result": "a", "nodes": [{"id": "a", "kind": "model", "prompt": "ask", "output": "a"}]}


class TextModel:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        self.calls += 1
        return "ok"


def run(model, text, **runner_options):
    return Runner(model=model, **runner_options).run(parse_skill(SKILL, "sized.md"), GRAPH, {"text": text})


class ContextShareTests(unittest.TestCase):

    @mark.req("REQ-RUN-005")
    def test_an_input_over_half_the_window_is_refused_before_the_call(self):
        """TC-RUN-005: an input over half the window is refused before the call.

        Example: "x" * 20000 -> status error, error contains 4096, calls 0
        """
        # Given: model = TextModel()
        model = TextModel()
        # When: result = run(model, "x" * 20000)
        result = run(model, "x" * 20000)
        # Then:
        self.assertEqual(result.status, "error")
        self.assertIn("4096", result.error)
        self.assertTrue(result.error.startswith("a: "))
        self.assertEqual(model.calls, 0)

    @mark.req("REQ-RUN-005")
    def test_an_input_inside_the_window_is_asked(self):
        """TC-RUN-005: an input inside the window is asked.

        Example: "how high is the tower?" -> status done, calls 1
        """
        # Given: model = TextModel()
        model = TextModel()
        # When: result = run(model, "how high is the tower?")
        result = run(model, "how high is the tower?")
        # Then:
        self.assertEqual((result.status, model.calls), ("done", 1))

    @mark.req("REQ-RUN-005")
    def test_the_refused_call_is_not_counted(self):
        """TC-RUN-005: the refused call is not counted.

        Example: "x" * 20000 -> cost calls 0
        """
        # Given:
        # When: result = run(TextModel(), "x" * 20000)
        result = run(TextModel(), "x" * 20000)
        # Then:
        self.assertEqual(result.cost["calls"], 0)

    @mark.req("REQ-RUN-005")
    def test_the_limit_can_be_set_for_another_window(self):
        """TC-RUN-005: the limit can be set for another window.

        Example: "x" * 600 with max_input_tokens=100 -> error; "x" * 200 -> done
        """
        # Given: model = TextModel()
        model = TextModel()
        # When: refused = run(model, "x" * 600, max_input_tokens=100); asked = run(model, "x" * 200, max_input_tokens=100)
        refused = run(model, "x" * 600, max_input_tokens=100)
        asked = run(model, "x" * 200, max_input_tokens=100)
        # Then:
        self.assertEqual((refused.status, asked.status, model.calls), ("error", "done", 1))
        self.assertIn("100", refused.error)


if __name__ == "__main__":
    unittest.main()
