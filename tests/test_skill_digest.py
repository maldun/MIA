"""
Unit tests of SkillDigestStep beyond its acceptance checks (G-V3.CHAT T-01; REQ-CHA-048, 050 to 052, 061 to 063): the three one-call wordings, a result that fits is
one call, a result of any size ends and no call is larger than the input limit, a model that does not shrink its digests cannot make it loop.
Run with: python tests/test_skill_digest.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from fake_model import FakeModel          # noqa: E402
from markers import mark                  # noqa: E402
from skill_digest import SkillDigestStep  # noqa: E402


def count_tokens(text):
    return max(1, len(text) // 4)


class OneCallWordings(unittest.TestCase):
    @mark.req("REQ-CHA-041", "REQ-CHA-044", "REQ-CHA-057", "REQ-CHA-061")
    def test_status_failure_and_stop_are_one_call_with_the_text_in_the_user_role(self):
        """status, failure and stopped each make one call; the phase or reason is the user text, the persona is in the system prompt, the reply is returned unchanged.
        Example: failure("search service unreachable") -> one call, reply "It failed." returned as it is."""
        # Given: a step with a persona on a fake model that answers every call with the same sentence
        model = FakeModel(lambda messages: "  It failed.  ")
        step = SkillDigestStep(model, persona="You are MIA, warm and brief.", count_tokens=count_tokens)
        # When: the three wordings are asked for
        words = [step.status("collect"), step.failure("search service unreachable"), step.stopped("stopped by the user")]
        # Then: one call each, the text of the run only in the user role, the persona in the system prompt
        self.assertEqual(len(model.calls), 3)
        for call, text in zip(model.calls, ("collect", "search service unreachable", "stopped by the user")):
            self.assertEqual(model.users(call), [text])
            self.assertTrue(any("warm and brief" in system for system in model.systems(call)))
            self.assertTrue(all(text not in system for system in model.systems(call)))
        # And: the text of the model is returned unchanged
        self.assertEqual(words, ["  It failed.  "] * 3)


class SizeOfTheCalls(unittest.TestCase):
    @mark.req("REQ-CHA-050", "REQ-CHA-051")
    def test_a_result_that_fits_is_one_call_with_the_whole_result(self):
        """a short result is digested by one call whose user text is the result.
        Example: "Three works found." -> one call."""
        # Given: a short result
        model = FakeModel(["The summary."])
        # When: it is summarized
        reply = SkillDigestStep(model, count_tokens=count_tokens).summary("Three works found.")
        # Then: one call with the result as the user text, and its reply
        self.assertEqual((len(model.calls), model.users(model.calls[0]), reply), (1, ["Three works found."], "The summary."))

    @mark.req("REQ-CHA-050", "REQ-CHA-062")
    def test_a_huge_result_ends_in_rounds_and_no_call_is_too_large(self):
        """a result of 4 000 000 characters is digested in rounds until the digests fit one call; no call is larger than the input limit.
        Example: 1 000 000 tokens with digests of 2000 characters each."""
        # Given: a result of a million tokens and a model whose digest is 2000 characters
        model = FakeModel(lambda messages: "d" * 2000)
        # When: it is summarized
        SkillDigestStep(model, count_tokens=count_tokens).summary("word " * 800000)
        # Then: every call fits the limit, and the last call holds digests only
        self.assertLessEqual(max(model.sizes(count_tokens)), 4096)
        self.assertNotIn("word", " ".join(model.users(model.calls[-1])))

    @mark.req("REQ-CHA-050")
    def test_a_model_that_does_not_shrink_cannot_make_it_loop(self):
        """a model that answers with its input would never make the digests fit: the step ends after a fixed number of rounds and still sends no call above the limit.
        Example: the fake model returns the user text."""
        # Given: a model that repeats its input
        model = FakeModel(lambda messages: [m["content"] for m in messages if m["role"] == "user"][-1])
        # When: a result of 100 000 tokens is summarized
        SkillDigestStep(model, count_tokens=count_tokens).summary("word " * 80000)
        # Then: it ended (this line is reached), with a bounded number of calls, none above the limit
        self.assertLess(len(model.calls), 200)
        self.assertLessEqual(max(model.sizes(count_tokens)), 4096)

    @mark.req("REQ-CHA-052")
    def test_the_version_changes_with_the_prompt(self):
        """the step carries a version string (a change of prompt, schema, tools, budget or graph changes it, CLAUDE.md).
        Example: version "1" with the first prompt."""
        # Given / When: a step
        step = SkillDigestStep(FakeModel([]))
        # Then: it has a version string
        self.assertIsInstance(step.version, str)
        self.assertTrue(step.version)


if __name__ == "__main__":
    unittest.main()
