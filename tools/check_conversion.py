"""
Checks one converted skill on its dev suite (G-V2.CONVERT T-CV-09; TC-WFM-110 to 114, a step of stage 4): runs the suite on the graph path with the pin and repeats of the Eval criterion of the
skill's requirement, decides it with eval_decide.py and prints the verdict. A dev run is feedback; the decision to switch a skill is the owner's (accept_conversion.py writes the record, this never does).

  python tools/check_conversion.py plan_question                       run, then decide
  python tools/check_conversion.py plan_question --run FILE            decide a run that exists, no model
  python tools/check_conversion.py plan_question --rerun FILE          the one re-run of a FAIL (made with fresh seeds, which needs another pin: an amendment) is passed in with --rerun
Exit 0 PASS, 1 FAIL, 2 NOT DECIDED, 3 the skill has no check with a model.
"""
import argparse
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
import skill_converter as C                                  # noqa: E402

REQUIREMENTS = os.path.join(REPO, "specs", "mia", "nodes", "N-2-backend", "nodes", "N-2.3-workflow-management", "requirements.md")


class CheckError(Exception):
    pass


def _fields(criterion):
    return dict(part.strip().split("=", 1) for part in criterion.split(";") if "=" in part)


def criterion_of_skill(skill, requirements=REQUIREMENTS):
    if skill not in C.SUITE_OF or skill == "extract_claims_rules":
        raise CheckError("%s has no dev run with a model (TC-WFM-115 compares outputs in stage 2)" % skill)
    return C.criterion_of(C.SUITE_OF[skill][1], requirements)


def eval_command(skill, requirements=REQUIREMENTS, results=None):
    """the command of the dev run: suite folder = the suite of the criterion without EV-, pin and repeats of the criterion, the converted variant"""
    fields = _fields(criterion_of_skill(skill, requirements))
    command = [sys.executable, os.path.join(REPO, "tools", "eval.py"), "run", fields["suite"].replace("EV-", "", 1), "--pin", fields["pin"], "--repeats", fields["repeats"],
               "--skill", skill, "--variant", "converted", "--converted", "--quiet"]
    return command + (["--results", results] if results else [])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("skill")
    parser.add_argument("--run", default=None, help="decide this run file instead of making a run")
    parser.add_argument("--rerun", default=None, help="the run file of the one re-run of a FAIL")
    parser.add_argument("--out", default=None, help="folder of the saved run (default data/eval)")
    args = parser.parse_args(argv)
    try:
        criterion = criterion_of_skill(args.skill)
    except CheckError as error:
        print(error)
        return 3
    run = args.run
    if run is None:
        done = subprocess.run(eval_command(args.skill, results=args.out), capture_output=True, text=True)
        print(done.stdout[-1500:])
        found = re.search(r"^saved: (.+)$", done.stdout, re.M)
        if done.returncode != 0 or not found:
            print("the run did not finish: %s" % (done.stderr.strip()[-300:] or "no saved file"))
            return 2
        run = found.group(1).strip()
    decision = C.decide_acceptance(run, criterion, rerun_path=args.rerun)
    print("%s: %s (%s)\ncriterion: %s\n%s" % (args.skill, decision["verdict"], run, criterion, decision["reason"]))
    if decision["verdict"] == "FAIL" and not args.rerun:
        print("one re-run with fresh seeds is allowed, never more; pass its file with --rerun")
    return {"PASS": 0, "FAIL": 1}.get(decision["verdict"], 2)


if __name__ == "__main__":
    sys.exit(main())
