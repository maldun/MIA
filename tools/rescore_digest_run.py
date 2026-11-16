"""Scores the stored outputs of a run of a digest suite (EV-skill_turns, G-V3.CHAT) again with the labels that exist now.

A run is scored while it runs, with the labels of that moment (harness._digest reads eval/labels/<suite>.jsonl). A holdout run is made before the owner has labelled its outputs, so every record
is stored as `open` with no `faithful` and no `persona`, and eval_decide.py finds no case. This tool reads the stored run, scores the SAME outputs again with digest_score.score_digest and the
labels of the owner, and writes a new run file next to it (RUN.rescored.jsonl). It calls no model, makes no new run and never changes the run file or the labels: the outputs are the evidence.

usage: python3 -I tools/rescore_digest_run.py RUN.jsonl SUITE [--root DIR]      (SUITE is the name of the suite of the run, for example skill_turns.holdout)
Reads DIR/eval/suites/SUITE/cases.jsonl and DIR/eval/labels/SUITE.jsonl (DIR defaults to the repository). The owner runs it on a holdout suite: an agent never opens a holdout.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import digest_score  # noqa: E402


def _jsonl(path):
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if line.strip()]


def rescore(lines, cases, labels):
    """(the lines of the new run, {"records", "labelled", "unlabelled"}); a line that is no scored output (the header, an error record, a case that is not in the suite) is kept as it is"""
    out, stats = [], {"records": 0, "labelled": 0, "unlabelled": 0}
    for line in lines:
        if not line.strip():
            continue
        record = json.loads(line)
        if "case" not in record:                                                  # the header of the run
            record["rescored"] = True
            out.append(json.dumps(record, ensure_ascii=False))
            continue
        detail = record.get("output")
        if isinstance(detail, dict) and isinstance(detail.get("output"), str) and record["case"] in cases:
            score = digest_score.score_digest(cases[record["case"]], detail["output"], labels)
            record["output"] = dict(detail, score=score)
            if "score" in record:
                record["score"] = dict(score)                                     # the harness stores the score twice; eval_decide reads this copy for faithful and persona
            record["status"] = score["status"]
            stats["records"] += 1
            stats["labelled" if any(score.get(key) is not None for key in ("persona", "resisted")) else "unlabelled"] += 1
        out.append(json.dumps(record, ensure_ascii=False))
    return out, stats


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    root = ROOT
    if "--root" in args:
        i = args.index("--root")
        root = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2:
        sys.exit(__doc__)
    run, suite = args
    cases = {case["id"]: case for case in _jsonl(os.path.join(root, "eval", "suites", suite, "cases.jsonl"))}
    labels = _jsonl(os.path.join(root, "eval", "labels", suite + ".jsonl"))
    if not cases:
        sys.exit("no cases of the suite %s under %s" % (suite, root))
    with open(run, encoding="utf-8") as fp:
        out, stats = rescore(fp.read().split("\n"), cases, labels)
    path = (run[:-len(".jsonl")] if run.endswith(".jsonl") else run) + ".rescored.jsonl"
    with open(path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(out) + "\n")
    print("rescored %d records: %d with a label, %d without (their outputs have no label yet)" % (stats["records"], stats["labelled"], stats["unlabelled"]))
    print("labels: %d lines of eval/labels/%s.jsonl" % (len(labels), suite))
    print("written: %s" % path)
    return path


if __name__ == "__main__":
    main()
