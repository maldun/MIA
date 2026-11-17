"""
Accepts a converted skill (G-V2.CONVERT, D-256, D-257; REQ-WFM-057, 059): decides the criterion of the skill's requirement on the dev run (and the re-run of a FAIL) and, only on a PASS,
writes data/conversion/<skill>.json. This is the only writer of that record; the owner runs it after reading the table of the decision and the cases wrong in all repeats.

  python tools/accept_conversion.py plan_question --run data/eval/plans__converted__<stamp>.jsonl [--rerun FILE] [--out data/conversion]
Exit 0 accepted, 1 not accepted, 2 the skill has no equivalence requirement.
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
import skill_converter as C                                  # noqa: E402
from library import Library                                  # noqa: E402

REQUIREMENTS = os.path.join(REPO, "specs", "mia", "nodes", "N-2-backend", "nodes", "N-2.3-workflow-management", "requirements.md")


def header_of(run):
    with open(run, encoding="utf-8") as fp:
        return json.loads(fp.readline())


def wrong_run(head, skill, suite):
    """why a run file cannot decide the acceptance of `skill` (F-04), or None: it must be a run of the converted path, of this skill, on this suite"""
    variant = head.get("variant") or {}
    if not variant.get("converted"):
        return "the run is not of the converted variant (header variant %r): the old runner proves nothing for the graph path" % (variant.get("name"),)
    if (variant.get("skill") or head.get("skill")) != skill:
        return "the run is of the skill %r, not %r" % (variant.get("skill") or head.get("skill"), skill)
    if head.get("suite") not in (suite, suite.replace("EV-", "", 1)):
        return "the run is on the suite %r, not %s" % (head.get("suite"), suite)
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("skill")
    parser.add_argument("--run", required=True)
    parser.add_argument("--rerun", default=None)
    parser.add_argument("--out", default=os.path.join(REPO, "data", "conversion"))
    args = parser.parse_args()
    if args.skill not in C.SUITE_OF:
        print("%s has no equivalence requirement: it stays on the old runner (%s)" % (args.skill, C.UI_REASON))
        return 2
    suite, requirement = C.SUITE_OF[args.skill]
    criterion = C.criterion_of(requirement, REQUIREMENTS)
    head = header_of(args.run)
    wrong = wrong_run(head, args.skill, suite)
    if wrong:
        print("not accepted: %s (no record written)" % wrong)
        return 1
    decision = C.decide_acceptance(args.run, criterion, rerun_path=args.rerun)
    print("%s: %s on %s (%s)\ncriterion: %s\n%s" % (args.skill, decision["verdict"], suite, requirement, criterion, decision["reason"]))
    if not decision["accepted"]:
        print("not accepted: no record written")
        return 1
    pin = head.get("pin") or {}
    check = {"suite": suite, "run": os.path.relpath(os.path.abspath(args.run), REPO), "pins": pin.get("id"), "model": pin.get("name"), "digest": pin.get("digest"),
             "verdict": "PASS", "requirement": requirement, "criterion": criterion, "skill_version": head.get("skill_version"), "pipeline": head.get("pipeline"),
             "pipeline_resolved": C.pipeline_ref(Library(os.path.join(REPO, "library")).resolve(head.get("pipeline"), "pipeline")), "commit": head.get("commit")}
    C.save_check(args.out, args.skill, check)
    print("recorded: %s" % os.path.join(args.out, args.skill + ".json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
