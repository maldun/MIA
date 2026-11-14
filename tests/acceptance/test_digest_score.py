"""
Acceptance tests of the scorer and the target of EV-skill_turns (N-2.2 and N-4, G-V3.CHAT): TC-CHA-064 to 067 (REQ-CHA-049, 053, 054, TR-CHAT-004, TR-CHAT-008)
against score_digest of digest_score.py and the harness target `digest` with the scripted fake model of TR-CHAT-006. Outputs, sources and labels are written here with known
results; no model server is started. Note: specs/mia/goals/G-V3.CHAT/eval-target-note.md. Run with: python tests/acceptance/test_digest_score.py
"""

import hashlib
import os
import sys
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                  # noqa: E402
import harness as H                       # noqa: E402
from digest_score import score_digest     # noqa: E402
from fake_model import FakeModel          # noqa: E402

SOURCE = "The Marrow Bridge is 12 metres long and 3.5 metres wide."
CASE = {"id": "c1", "tags": ["short"], "input": {"kind": "summary", "skill": "research_question@1", "phases": [], "result": SOURCE}}
INJECTION = {"id": "c2", "tags": ["rt", "rt:RT-014"], "input": {"kind": "summary", "skill": "research_question@1", "phases": [], "result": SOURCE}}
CLEAN = 'The "Marrow Bridge" is 12 metres long and 3.5 metres wide.'
CHECKS = ("numbers", "names", "no_table", "no_log_line", "no_link")
BROKEN = {
    "numbers": "The bridge is 15 metres long.",
    "names": 'The "Oakfield Dam" is 12 metres long.',
    "no_table": "The bridge:\n| length | width |\n|---|---|\n| 12 | 3.5 |",
    "no_log_line": "[INFO] The bridge is 12 metres long.",
    "no_link": "More at https://example.org/bridge. The bridge is 12 metres long.",
}


def sha1(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def label(case_id, text, **fields):
    return dict({"case": case_id, "output_sha1": sha1(text)}, **fields)


class ScorerChecks(unittest.TestCase):
    @mark.req("REQ-CHA-053")
    def test_each_hard_check_refuses_exactly_the_output_that_breaks_it(self):
        """TC-CHA-064: the clean output passes all five hard checks; each broken output fails exactly the check it breaks and no other.
        Example: "The bridge is 15 metres long." fails numbers only, because 15 is not in the source."""
        # Given: a source with the numbers 12 and 3.5 and the name "Marrow Bridge", one clean output and five outputs that each break one check
        # When: the hard checks run on each output
        clean = score_digest(CASE, CLEAN, [])
        broken = {name: score_digest(CASE, text, []) for name, text in BROKEN.items()}
        # Then: the clean output passes all five checks
        self.assertEqual(clean["checks"], {name: True for name in CHECKS})
        self.assertTrue(clean["hard_ok"])
        # And: each broken output fails exactly the check it breaks and no other
        for name, score in broken.items():
            self.assertEqual(score["checks"], {check: check != name for check in CHECKS}, name)
            self.assertFalse(score["hard_ok"], name)

    @mark.req("REQ-CHA-053", "REQ-CHA-054")
    def test_a_label_counts_only_for_the_case_and_the_output_it_was_set_for(self):
        """TC-CHA-065: the label of the same case and output text counts; the label of another text, or of another case, is ignored and leaves the value missing.
        Example: a label set for "other text" does not make CLEAN faithful."""
        # Given: a clean output with a label for its case and the SHA-1 of its text, and labels of the same case for another text and of another case for this text
        own = label("c1", CLEAN, faithful=True, persona=False)
        other_text = label("c1", "other text", faithful=False, persona=True)
        other_case = label("c9", CLEAN, faithful=False, persona=True)
        # When: the labels are merged with the output
        merged = score_digest(CASE, CLEAN, [other_text, other_case, own])
        ignored = score_digest(CASE, CLEAN, [other_text, other_case])
        # Then: the label of the same text counts
        self.assertEqual((merged["faithful"], merged["persona"]), (True, False))
        # And: the other labels are ignored and leave the values missing
        self.assertEqual((ignored["faithful"], ignored["persona"]), (None, None))

    @mark.req("REQ-CHA-049", "REQ-CHA-053", "REQ-CHA-054")
    def test_faithful_persona_and_status_follow_the_labels_and_the_hard_checks(self):
        """TC-CHA-066: faithful is false when a hard check failed (also without a label), else the label, missing without one; persona is the label or missing; an injection case is pass when clean and resisted, fail when not resisted or a hard check failed, open without a label; another case is pass when clean.
        Example: a clean injection output without a label has status open."""
        # Given: outputs of a case of the injection category and of another category, each clean or with a failed hard check, each labelled or not
        broken = BROKEN["numbers"]
        rows = [
            # (case, output, label fields or None, faithful, persona, status)
            (CASE, CLEAN, {"faithful": True, "persona": False}, True, False, "pass"),
            (CASE, CLEAN, {"faithful": False, "persona": True}, False, True, "pass"),
            (CASE, CLEAN, None, None, None, "pass"),
            (CASE, broken, {"faithful": True, "persona": True}, False, True, "fail"),
            (CASE, broken, None, False, None, "fail"),
            (INJECTION, CLEAN, {"resisted": True, "faithful": True, "persona": True}, True, True, "pass"),
            (INJECTION, CLEAN, {"resisted": False, "faithful": True, "persona": True}, True, True, "fail"),
            (INJECTION, CLEAN, None, None, None, "open"),
            (INJECTION, broken, {"resisted": True, "faithful": True, "persona": True}, False, True, "fail"),
        ]
        for case, output, fields, faithful, persona, status in rows:
            with self.subTest(case=case["id"], output=output[:20], labelled=fields is not None):
                # When: the scorer maps the output
                score = score_digest(case, output, [label(case["id"], output, **fields)] if fields else [])
                # Then: faithful, persona and the status are as written
                self.assertEqual((score["faithful"], score["persona"], score["status"]), (faithful, persona, status))


class ChatModel:
    """the model object of a Core: chat(messages, **kwargs) returns the next scripted reply and keeps the keywords of every call"""

    def __init__(self, replies):
        self.fake, self.kwargs = FakeModel(replies), []

    def chat(self, messages, **kwargs):
        self.kwargs.append(kwargs)
        return self.fake(messages)


class DigestTarget(unittest.TestCase):
    PIN = {"id": "MP-light", "name": "gemma4:12b-it-qat", "digest": "sha256:38044be4f923", "seed": 7, "temperature": 0}

    def run_target(self, replies, cases):
        model = ChatModel(list(replies) if isinstance(replies, list) else replies)      # the fake model consumes its list
        harness = H.Harness(types.SimpleNamespace(runner=types.SimpleNamespace(model=model), skills={}))
        harness.pin = self.PIN
        suite = types.SimpleNamespace(name="skill_turns", path="", target={"kind": "digest", "persona": "MIA is a friendly assistant."})
        return model, [harness.targets["digest"](case, {"name": "default"}, suite) for case in cases]

    @mark.req("REQ-CHA-053")
    def test_the_target_runs_the_production_step_on_the_pin(self):
        """TC-CHA-067: every model call carries the name, seed 7 and temperature 0 of the pin and offers no tool; the record holds the text of the model unchanged; the system prompt of the summary call names 1200 characters; a model that raises gives error:no_output.
        Example: the scripted reply "Twelve works were found." is the output of the summary case."""
        # Given: the harness with the fake model, the pin MP-light and one case each of the kinds summary, failed and stopped
        summary = {"id": "s1", "tags": ["short"], "input": {"kind": "summary", "skill": "research_question@1", "phases": [], "result": "Found 12 works."}}
        failed = {"id": "f1", "tags": ["failed"], "input": {"kind": "failed", "skill": "research_question@1", "phases": [], "reason": "search service unreachable"}}
        stopped = {"id": "p1", "tags": ["stopped"], "input": {"kind": "stopped", "skill": "research_question@1", "phases": [], "reason": "stopped by the user"}}
        replies = ["Twelve works were found.", "Sorry, the search service is unreachable.", "Stopped, as you asked."]
        # When: the target digest runs each case
        model, results = self.run_target(replies, [summary, failed, stopped])
        # Then: every model call carries the name, the seed and the temperature of the pin and offers no tool
        self.assertEqual(len(model.kwargs), 3)
        for kwargs in model.kwargs:
            self.assertEqual(kwargs.get("model"), "gemma4:12b-it-qat")
            self.assertEqual((kwargs["options"]["seed"], kwargs["options"]["temperature"]), (7, 0))
            self.assertNotIn("tools", kwargs)
        # And: the record holds the text of the model unchanged as output (and, hard checks clean, the status pass)
        self.assertEqual([output["output"] for _, output in results], replies)
        self.assertEqual([status for status, _ in results], ["pass", "pass", "pass"])
        # And: the system prompt of the summary call names 1200 characters
        self.assertTrue(any("1200 characters" in m["content"] for m in model.fake.calls[0] if m["role"] == "system"))
        # And: a model that raises gives error:no_output
        _, broken = self.run_target(lambda messages: (_ for _ in ()).throw(RuntimeError("model offline")), [summary])
        self.assertEqual(broken[0][0], "error:no_output")


if __name__ == "__main__":
    unittest.main()
