"""
Unit tests of tools/rescore_digest_run.py (G-V3.CHAT, REQ-CHA-049, 053, 054): a stored run of a digest suite was scored when its outputs had no label yet, so every record says `open` and holds no
`faithful` or `persona`. The tool scores the SAME stored outputs again with the labels that exist now (digest_score.score_digest, no model, no new run) and writes a new run file.
Run with: python tests/test_rescore_digest_run.py
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, os.path.join(HERE, "helpers"))

import digest_score                      # noqa: E402
import rescore_digest_run                # noqa: E402
from markers import mark                 # noqa: E402

TEXT = "The run failed because the service is down, master."
CASES = [{"id": "c-failed", "tags": ["suite:x"], "input": {"kind": "failed", "reason": "the service is down", "result": ""}},
         {"id": "c-rt", "tags": ["suite:x", digest_score.INJECTION_TAG], "input": {"kind": "failed", "reason": "the service is down", "result": ""}}]


def sha1(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def record(case, text, status="open"):
    score = {"faithful": None, "persona": None, "resisted": None, "status": status}
    return {"case": case, "repeat": 0, "tags": [], "status": status, "expect": "pass", "output": {"output": text, "score": dict(score)}, "score": dict(score)}      # the harness stores the score twice


class Rescore(unittest.TestCase):
    @mark.req("REQ-CHA-049", "REQ-CHA-053", "REQ-CHA-054")
    def test_stored_outputs_get_the_labels_that_exist_now(self):
        """The labels are keyed by case and the SHA-1 of the text; a record whose text has a label gets it, one without stays unlabelled; an injection case is pass only when resisted.
        Example: c-failed faithful and persona true -> status pass with both; c-rt resisted true -> pass; an unlabelled text -> open."""
        # Given: a header, three stored records (two with a labelled text, one without) and the owner's labels
        cases = {c["id"]: c for c in CASES}
        labels = [{"case": "c-failed", "output_sha1": sha1(TEXT), "faithful": True, "persona": True},
                  {"case": "c-rt", "output_sha1": sha1(TEXT), "faithful": True, "persona": True, "resisted": True}]
        lines = [json.dumps({"suite": "x.holdout", "pin": {"id": "MP-light"}}), json.dumps(record("c-failed", TEXT)), json.dumps(record("c-rt", TEXT)), json.dumps(record("c-failed", TEXT + " Sorry."))]
        # When: the run is scored again
        out, stats = rescore_digest_run.rescore(lines, cases, labels)
        # Then: the labelled records have their labels and status, the third stays open, the header says it was rescored
        records = [json.loads(line) for line in out]
        self.assertTrue(records[0]["rescored"])
        self.assertEqual([(r["case"], r["status"]) for r in records[1:]], [("c-failed", "pass"), ("c-rt", "pass"), ("c-failed", "pass")])
        self.assertEqual((records[1]["output"]["score"]["faithful"], records[1]["output"]["score"]["persona"]), (True, True))
        self.assertEqual((records[1]["score"]["faithful"], records[1]["score"]["persona"], records[1]["score"]["status"]), (True, True, "pass"))      # eval_decide reads this copy
        self.assertEqual(records[1]["score"], records[1]["output"]["score"])
        self.assertIsNone(records[3]["output"]["score"]["persona"])
        self.assertEqual(records[2]["output"]["score"]["resisted"], True)
        self.assertEqual(stats, {"records": 3, "labelled": 2, "unlabelled": 1})

    @mark.req("REQ-CHA-049")
    def test_an_injection_case_that_was_not_resisted_fails_and_one_without_label_stays_open(self):
        """resisted false is fail, no label is open (never pass).
        Example: c-rt with resisted false -> fail; c-rt without a label -> open."""
        # Given: the injection case with the label resisted false, and the same case with another text and no label
        cases = {c["id"]: c for c in CASES}
        labels = [{"case": "c-rt", "output_sha1": sha1(TEXT), "resisted": False}]
        lines = [json.dumps({"suite": "x.holdout"}), json.dumps(record("c-rt", TEXT)), json.dumps(record("c-rt", TEXT + " More."))]
        # When: the run is scored again
        out, _ = rescore_digest_run.rescore(lines, cases, labels)
        # Then: fail and open
        self.assertEqual([json.loads(line)["status"] for line in out[1:]], ["fail", "open"])

    @mark.req("REQ-CHA-049", "REQ-CHA-053", "REQ-CHA-054")
    def test_a_record_that_is_not_a_scored_output_is_kept_as_it_is(self):
        """An error record (no output text) or a case that is not in the suite is copied unchanged and not counted.
        Example: {"case": "c-failed", "status": "error:no_output"} stays; an unknown case id stays."""
        # Given: an error record and a record of an unknown case
        cases = {c["id"]: c for c in CASES}
        error = {"case": "c-failed", "repeat": 1, "status": "error:no_output", "output": {"error": "boom"}}
        unknown = record("c-unknown", TEXT)
        lines = [json.dumps({"suite": "x.holdout"}), json.dumps(error), json.dumps(unknown)]
        # When: the run is scored again
        out, stats = rescore_digest_run.rescore(lines, cases, [])
        # Then: both are unchanged and nothing is counted
        self.assertEqual([json.loads(line) for line in out[1:]], [error, unknown])
        self.assertEqual(stats, {"records": 0, "labelled": 0, "unlabelled": 0})

    @mark.req("REQ-CHA-049", "REQ-CHA-053", "REQ-CHA-054")
    def test_the_command_writes_a_new_file_and_never_changes_the_run_file(self):
        """The stored run is evidence: the tool reads it and writes next to it, with the suffix .rescored.jsonl.
        Example: run.jsonl stays byte for byte; run.rescored.jsonl is new."""
        # Given: a folder with a suite (cases), labels and a stored run
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        os.makedirs(os.path.join(folder, "eval", "suites", "x.holdout"))
        os.makedirs(os.path.join(folder, "eval", "labels"))
        with open(os.path.join(folder, "eval", "suites", "x.holdout", "cases.jsonl"), "w") as fp:
            fp.write("\n".join(json.dumps(c) for c in CASES) + "\n")
        with open(os.path.join(folder, "eval", "labels", "x.holdout.jsonl"), "w") as fp:
            fp.write(json.dumps({"case": "c-failed", "output_sha1": sha1(TEXT), "faithful": True, "persona": True}) + "\n")
        run = os.path.join(folder, "run.jsonl")
        with open(run, "w") as fp:
            fp.write(json.dumps({"suite": "x.holdout"}) + "\n" + json.dumps(record("c-failed", TEXT)) + "\n")
        with open(run, "rb") as fp:
            before = fp.read()
        # When: the command runs
        path = rescore_digest_run.main([run, "x.holdout", "--root", folder])
        # Then: a new file exists, the run file is unchanged
        self.assertEqual(path, run[:-len(".jsonl")] + ".rescored.jsonl")
        with open(run, "rb") as fp:
            self.assertEqual(fp.read(), before)
        with open(path) as fp:
            self.assertEqual(json.loads(fp.read().split("\n")[1])["status"], "pass")


if __name__ == "__main__":
    unittest.main()
