#!/usr/bin/env python3
"""
Move LABELLED draft cases into eval suites, one suite per `suite:<name>` tag, dev and holdout by the `split:` tag.

  python3 tools/promote_labelled.py specs/mia/eval-drafts/redteam_mia.jsonl                       shows what it would do
  python3 tools/promote_labelled.py specs/mia/eval-drafts/redteam_mia.jsonl --do                  writes eval/suites/<suite>/ and eval/suites/<suite>.holdout/
  python3 tools/promote_labelled.py FILE --do --only rt_user_text,rt_script --suites eval/suites   only these suites, another suites folder

Only cases with the tag `label:people` and without `source:draft` are moved; the others stay in the drafts file and are named. A labelled case without a
single `split:dev` / `split:holdout` tag stops the tool. Existing suite folders are never overwritten (a case never moves between splits; retire it and add a new one).
Each suite gets a suite.json with the target {"kind": "pending"}: the harness refuses to run such a suite until a target and a scorer exist (see the README of the
drafts folder), but the agent check (A8 and A12) sees the red-team tags. The moved cases are removed from the drafts file only with --do. Standard library only.
"""
import argparse
import json
import os
import sys


def plan(path):
    """({suite: {"dev": [...], "holdout": [...]}}, [ids not labelled], [problems])"""
    with open(path, encoding="utf-8") as fp:
        cases = [json.loads(line) for line in fp if line.strip()]
    suites, waiting, problems = {}, [], []
    for case in cases:
        tags = case.get("tags", [])
        if "label:people" not in tags or "source:draft" in tags:
            waiting.append(case["id"])
            continue
        names = [t[6:] for t in tags if t.startswith("suite:")]
        splits = [t[6:] for t in tags if t.startswith("split:")]
        if len(names) != 1:
            problems.append("%s: needs exactly one suite: tag" % case["id"])
        elif len(splits) != 1 or splits[0] not in ("dev", "holdout"):
            problems.append("%s: needs exactly one split:dev or split:holdout tag" % case["id"])
        else:
            suites.setdefault(names[0], {"dev": [], "holdout": []})[splits[0]].append(case)
    return suites, waiting, problems


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("drafts")
    parser.add_argument("--suites", default="eval/suites")
    parser.add_argument("--only", help="comma separated suite names")
    parser.add_argument("--do", action="store_true")
    args = parser.parse_args(argv)
    suites, waiting, problems = plan(args.drafts)
    if args.only:
        wanted = set(args.only.split(","))
        suites = {k: v for k, v in suites.items() if k in wanted}
    if problems:
        print("\n".join(problems))
        return 1
    clashes = [os.path.join(args.suites, n + s) for n in suites for s in ("", ".holdout") if os.path.exists(os.path.join(args.suites, n + s))]
    if clashes:
        print("exists already, nothing written: " + ", ".join(clashes))
        return 1
    for name, parts in sorted(suites.items()):
        print("%-16s dev %2d   holdout %2d" % (name, len(parts["dev"]), len(parts["holdout"])))
    print("not labelled yet (stay in the drafts): %d" % len(waiting))
    if not suites:
        return 0
    if not args.do:
        print("nothing written; add --do")
        return 0
    moved = set()
    for name, parts in suites.items():
        for kind, folder in (("dev", name), ("holdout", name + ".holdout")):
            if not parts[kind]:
                continue
            target = os.path.join(args.suites, folder)
            os.makedirs(target)
            with open(os.path.join(target, "suite.json"), "w", encoding="utf-8") as fp:
                json.dump({"name": folder, "description": "Red-team cases (%s part), labelled by a person; target not decided yet" % kind, "target": {"kind": "pending"}}, fp, indent=1)
            with open(os.path.join(target, "cases.jsonl"), "w", encoding="utf-8") as fp:
                for case in parts[kind]:
                    fp.write(json.dumps(case, ensure_ascii=False) + "\n")
                    moved.add(case["id"])
    with open(args.drafts, encoding="utf-8") as fp:
        rows = [json.loads(line) for line in fp if line.strip()]
    with open(args.drafts, "w", encoding="utf-8") as fp:
        for row in rows:
            if row["id"] not in moved:
                fp.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("moved %d cases" % len(moved))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
