#!/usr/bin/env python3
"""
Decide a criterion only on held-out cases (REQ-EVL-002): a guard around eval_decide.py of the agent-app skill.

  python tools/decide_guard.py --run <holdout run> [--run ...] [--rerun <holdout run> ...] [eval_decide.py options ...]

Every run file, also of --rerun, must be a holdout run (suite name ends in `.holdout`, or every record carries the tag `split:holdout`). A dev-split run
(or a mix) is NOT DECIDED with the reason "dev split": feedback runs are not verification (CLAUDE.md). Otherwise eval_decide.py decides with
`--split holdout`; an option that would change the split (`--split`, also as `--split=...` or abbreviated) is refused (Verify F5a).
Exit code as eval_decide.py: 0 PASS, 1 FAIL, 2 NOT DECIDED. Standard library only.
"""
import json
import os
import subprocess
import sys

DECIDE = os.environ.get("EVAL_DECIDE", os.path.expanduser("~/.claude/skills/agent-app/scripts/eval_decide.py"))
HOLDOUT_TAG = "split:holdout"


def _is_holdout(path):
    """True for a holdout run; False for anything else, also for a file that cannot be read"""
    suite, records = "", []
    try:
        with open(path, encoding="utf-8") as fp:
            for line in fp:
                if not line.strip():
                    continue
                item = json.loads(line)
                if item.get("kind") == "header":
                    suite = str(item.get("suite", ""))
                else:
                    records.append(item)
    except (OSError, ValueError):
        return False
    if suite.endswith(".holdout"):
        return True
    return bool(records) and all(HOLDOUT_TAG in r.get("tags", []) or r.get("split") == "holdout" for r in records)


def check_runs(paths):
    """{"ok", "reason"}: ok only if there is at least one run and every one is a holdout run"""
    if not paths:
        return {"ok": False, "reason": "no run given"}
    dev = [p for p in paths if not _is_holdout(p)]
    if dev:
        return {"ok": False, "reason": "dev split: %s is not a holdout run; a verdict is decided on held-out cases only" % ", ".join(dev)}
    return {"ok": True, "reason": ""}


def decide(paths, options=(), reruns=()):
    """{"decision": PASS | FAIL | NOT DECIDED, "reason", "report"}; reruns are checked like paths; options are passed on to eval_decide.py"""
    verdict = check_runs(list(paths) + list(reruns))
    if not verdict["ok"]:
        return {"decision": "NOT DECIDED", "reason": verdict["reason"], "report": None}
    command = [sys.executable, "-I", DECIDE, "--json", "--split", "holdout"]
    for path in paths:
        command += ["--run", path]
    for path in reruns:
        command += ["--rerun", path]
    result = subprocess.run(command + list(options), capture_output=True, text=True)
    try:
        report = json.loads(result.stdout)
    except ValueError:
        return {"decision": "NOT DECIDED", "reason": "eval_decide.py gave no result: " + (result.stderr.strip() or result.stdout.strip())[:300], "report": None}
    return {"decision": report["verdict"], "reason": "", "report": report}


def _option(token):
    """the option of eval_decide.py a token stands for, as argparse reads it (exact, `--name=value`, or an unambiguous abbreviation): run, rerun,
    split or None for anything else"""
    name = token.split("=", 1)[0]
    if name == "--run":
        return "run"
    if len(name) >= 5 and "--rerun".startswith(name):            # --rer ... --rerun
        return "rerun"
    if len(name) >= 4 and "--split".startswith(name):            # --sp ... --split
        return "split"
    return None


def parse(argv):
    """(runs, reruns, options, refusal): the run files are taken out of the options so that they are checked; a split option is a refusal"""
    files, options, i = {"run": [], "rerun": []}, [], 0
    while i < len(argv):
        token, kind = argv[i], _option(argv[i])
        if kind == "split":
            spelled = token if token.startswith("--split") else "%s (= --split)" % token
            return [], [], [], "the option %s would change the split; a verdict is decided on the holdout split only" % spelled
        if kind and "=" in token:
            files[kind].append(token.split("=", 1)[1])
            i += 1
        elif kind and i + 1 < len(argv):
            files[kind].append(argv[i + 1])
            i += 2
        else:
            options.append(token)
            i += 1
    return files["run"], files["rerun"], options, None


def main(argv):
    paths, reruns, options, refusal = parse(argv)
    result = {"decision": "NOT DECIDED", "reason": refusal, "report": None} if refusal else decide(paths, options, reruns)
    if result["report"] is None:
        print("NOT DECIDED: " + result["reason"])
        return 2
    print(json.dumps(result["report"], indent=1, default=str))
    return {"PASS": 0, "FAIL": 1, "NOT DECIDED": 2}[result["decision"]]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
