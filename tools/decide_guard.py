#!/usr/bin/env python3
"""
Decide a criterion only on held-out cases (REQ-EVL-002): a guard around eval_decide.py of the agent-app skill.

  python tools/decide_guard.py --run <holdout run> [--run ...] [eval_decide.py options ...]

Every run file must be a holdout run (suite name ends in `.holdout`, or every record carries the tag `split:holdout`). A dev-split run (or a mix) is
NOT DECIDED with the reason "dev split": feedback runs are not verification (CLAUDE.md). Otherwise eval_decide.py decides with `--split holdout`.
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


def decide(paths, options=()):
    """{"decision": PASS | FAIL | NOT DECIDED, "reason", "report"}; options are passed on to eval_decide.py"""
    verdict = check_runs(paths)
    if not verdict["ok"]:
        return {"decision": "NOT DECIDED", "reason": verdict["reason"], "report": None}
    command = [sys.executable, "-I", DECIDE, "--json", "--split", "holdout"]
    for path in paths:
        command += ["--run", path]
    result = subprocess.run(command + list(options), capture_output=True, text=True)
    try:
        report = json.loads(result.stdout)
    except ValueError:
        return {"decision": "NOT DECIDED", "reason": "eval_decide.py gave no result: " + (result.stderr.strip() or result.stdout.strip())[:300], "report": None}
    return {"decision": report["verdict"], "reason": "", "report": report}


def main(argv):
    paths, options, i = [], [], 0
    while i < len(argv):
        if argv[i] == "--run" and i + 1 < len(argv):
            paths.append(argv[i + 1])
            i += 2
        else:
            options.append(argv[i])
            i += 1
    result = decide(paths, options)
    if result["report"] is None:
        print("NOT DECIDED: " + result["reason"])
        return 2
    print(json.dumps(result["report"], indent=1, default=str))
    return {"PASS": 0, "FAIL": 1, "NOT DECIDED": 2}[result["decision"]]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
