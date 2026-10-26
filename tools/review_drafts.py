#!/usr/bin/env python3
"""
Review draft eval cases one by one (the person labels, not the coding agent).

  python3 tools/review_drafts.py specs/mia/eval-drafts/redteam_mia.jsonl            ask for every draft case
  python3 tools/review_drafts.py specs/mia/eval-drafts/redteam_mia.jsonl --list     only list them

For every case with the tag `source:draft` it shows the id, the input and what "resisted" means, and asks:
  k   keep: the tag `label:people` is added and `source:draft` is removed (you have checked that the case and its expected outcome are right)
  d   drop: the case is removed from the file
  s   skip: nothing changes, ask again next time (also the answer to an empty line)
  q   quit; what was decided so far is saved
Cases that are already labelled are not asked. The file is rewritten only when something changed (a copy stays next to it as <file>.bak).
Moving the labelled cases into eval/suites/<suite>/ and eval/suites/<suite>.holdout/ by their `split:` tag is the next step (tools/promote_drafts.py does that for
the verdict suites). Standard library only.
"""
import json
import shutil
import sys

DRAFT, LABEL = "source:draft", "label:people"


def review(path, ask=input, show=print, list_only=False):
    with open(path, encoding="utf-8") as fp:
        cases = [json.loads(line) for line in fp if line.strip()]
    todo = [c for c in cases if DRAFT in c.get("tags", [])]
    show("%d cases, %d drafts to review" % (len(cases), len(todo)))
    kept = dropped = 0
    out, quit_now = [], False
    for case in cases:
        if quit_now or DRAFT not in case.get("tags", []) or list_only:
            out.append(case)
            if list_only and DRAFT in case.get("tags", []):
                show("%s  %s  %s" % (case["id"], ",".join(t for t in case["tags"] if t.startswith(("rt:", "split:"))), case.get("note", "")[:90]))
            continue
        show("\n== %s   %s" % (case["id"], " ".join(case["tags"])))
        show("input : " + json.dumps(case["input"], ensure_ascii=False))
        show("expect: %s   (%s)" % (case.get("expect"), case.get("note", "")))
        answer = ask("keep / drop / skip / quit [k/d/s/q]: ").strip().lower()
        if answer == "k":
            case["tags"] = sorted((set(case["tags"]) - {DRAFT}) | {LABEL})
            kept += 1
            out.append(case)
        elif answer == "d":
            dropped += 1
        else:
            quit_now = answer == "q"
            out.append(case)
    if kept or dropped:
        shutil.copyfile(path, path + ".bak")
        with open(path, "w", encoding="utf-8") as fp:
            for case in out:
                fp.write(json.dumps(case, ensure_ascii=False) + "\n")
    show("\nkept %d, dropped %d, still drafts %d" % (kept, dropped, sum(1 for c in out if DRAFT in c.get("tags", []))))
    return kept, dropped


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    review(sys.argv[1], list_only="--list" in sys.argv[2:])
