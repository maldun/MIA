"""
The label tools of EV-skill_turns (G-V3.CHAT T-04, REQ-CHA-053, 054): the form generator, the apply script and the way the harness target reads the labels they write.
Synthetic run, cases and labels in a temporary folder; no real suite is read. Run: python tests/test_digest_label_tools.py
"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))

import harness as H                                   # noqa: E402
from markers import mark                              # noqa: E402


def tool(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, "tools", name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MAKE, APPLY = tool("make_digest_label_form"), tool("apply_digest_labels")
SOURCE = "The Marrow Bridge is 12 metres long."
OUTPUT = 'The "Marrow Bridge" is 12 metres long.'
SHA = hashlib.sha1(OUTPUT.encode("utf-8")).hexdigest()
CASES = [{"id": "c1", "tags": ["short"], "input": {"kind": "summary", "skill": "s@1", "phases": [], "result": SOURCE}, "expect": "pass"},
         {"id": "c2", "tags": ["rt"], "input": {"kind": "summary", "skill": "s@1", "phases": [], "result": SOURCE}, "expect": "pass"}]


def write_run(path):
    rows = [{"kind": "header", "suite": "skill_turns"}]
    for case in ("c1", "c1", "c2"):          # c1 twice with the same text: one card
        rows.append({"kind": "record", "case": case, "repeat": 0, "status": "pass", "output": {"output": OUTPUT, "score": {}}})
    rows.append({"kind": "record", "case": "c1", "repeat": 1, "status": "error:no_output", "output": {"error": "offline"}})
    with open(path, "w", encoding="utf-8") as fp:
        fp.writelines(json.dumps(row) + "\n" for row in rows)


class LabelTools(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run_path, self.cases_path = os.path.join(self.tmp.name, "run.jsonl"), os.path.join(self.tmp.name, "cases.jsonl")
        write_run(self.run_path)
        with open(self.cases_path, "w", encoding="utf-8") as fp:
            fp.writelines(json.dumps(case) + "\n" for case in CASES)

    @mark.req("REQ-CHA-053")
    def test_the_form_has_one_card_per_distinct_output_and_a_resisted_question_only_for_rt(self):
        """The form holds one card for each case and output text, none for a record without an output, and the question "resisted" only on a case tagged rt.
        Example: c1 appears twice in the run with the same text and gets one card."""
        # Given: a run with c1 twice with one text, c2 once, and one record without an output
        out = os.path.join(self.tmp.name, "form.html")
        # When: the form is built
        count = MAKE.build(self.run_path, self.cases_path, out)
        with open(out, encoding="utf-8") as fp:
            page = fp.read()
        # Then: there are two cards and the key of each is the SHA-1 of the text
        self.assertEqual(count, 2)
        self.assertEqual(page.count('class="card"'), 2)
        self.assertIn('data-sha1="%s"' % SHA, page)
        # And: only the card of c2 asks whether the instruction was resisted
        self.assertEqual(page.count('data-field="resisted"'), 1)

    @mark.req("REQ-CHA-053", "REQ-CHA-054")
    def test_applied_marks_are_read_by_the_target_and_a_repeat_changes_nothing(self):
        """Marks applied to the labels folder are found by the harness target of the suite and change the status of an injection case; applying them again appends nothing.
        Example: c2 is open without a label and pass with resisted = true."""
        # Given: a marks file for c2 and a suite folder next to a labels folder
        marks = os.path.join(self.tmp.name, "marks.json")
        with open(marks, "w", encoding="utf-8") as fp:
            json.dump([{"case": "c2", "output_sha1": SHA, "faithful": True, "persona": True, "resisted": True}, {"case": "c1", "output_sha1": SHA}], fp)
        labels_dir = os.path.join(self.tmp.name, "eval", "labels")
        suite_dir = os.path.join(self.tmp.name, "eval", "suites", "skill_turns")
        os.makedirs(suite_dir)
        suite = types.SimpleNamespace(name="skill_turns", path=suite_dir, target={"kind": "digest"})
        harness = H.Harness(types.SimpleNamespace(runner=types.SimpleNamespace(model=types.SimpleNamespace(chat=lambda messages, **kw: OUTPUT)), skills={}))
        before = harness.targets["digest"](CASES[1], {"name": "default"}, suite)[0]
        # When: the marks are applied, twice
        with contextlib.redirect_stdout(io.StringIO()):
            APPLY.main([marks, "skill_turns", "--by", "tester", "--labels-dir", labels_dir, "--do"])
            APPLY.main([marks, "skill_turns", "--by", "tester", "--labels-dir", labels_dir, "--do"])
        # Then: the file holds one line, only for the mark that had a value
        lines = APPLY.load(os.path.join(labels_dir, "skill_turns.jsonl"))
        self.assertEqual([(l["case"], l["resisted"], l["by"]) for l in lines], [("c2", True, "tester")])
        # And: the target reads it: open before, pass after
        after = harness.targets["digest"](CASES[1], {"name": "default"}, suite)
        self.assertEqual((before, after[0]), ("open", "pass"))
        self.assertEqual(after[1]["score"]["faithful"], True)


if __name__ == "__main__":
    unittest.main()
