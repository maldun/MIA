#!/usr/bin/env bash
# Amendment A-108 (G-V2.MODEL, wording only, owner's decision (c) of 2026-11-08): the plan text of task T-06 (written by A-107) says that a record-only skill is
# "listed by its command" and that `TaskRegistry.commands` shows the record's command. The code and the tests (T-06, `tests/test_skill_catalog_loader.py`) do something
# smaller, as decided: a record-only skill (a record, but no manifest folder or entry module) is NOT a Task: it is not in `TaskRegistry.commands()`, not runnable,
# and it is listed through `SkillCatalog.list()` only, until G-V2.CONVERT moves the skills one by one. This amendment corrects the two sentences. No code, test,
# protected file, contract or requirement text changes.
# Note: specs/mia/amendments/A-108-note.md
# Files that change (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found
# exactly once, so a second --do changes nothing):
#   specs/mia/goals/G-V2.MODEL/plan.md (test (3) and the notes of T-06)     specs/mia/review-log.md (row D-310, appended)
#   bash tools/apply_amendment_a108.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a108.sh --do      install and run the checks; commit afterwards as "plan: A-108 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
PLAN=specs/mia/goals/G-V2.MODEL/plan.md
LOG=specs/mia/review-log.md
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$PLAN" "$LOG" "$WORK" <<'PY'
import os
import sys
plan, log, work = sys.argv[1:4]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def once(text, old, new, where):
    """Replace `old` by `new` when `old` occurs exactly once; the edit counts as done when `new` is in the text already (checked FIRST)."""
    if new in text:
        return text
    if text.count(old) == 1:
        return text.replace(old, new)
    sys.exit("anchor not found exactly once (%d) in %s: %r" % (text.count(old), where, old[:70]))


p = read(plan)
p = once(p,
         "(3) a record-only skill (no manifest folder) is not invented as a runnable task; the listing of commands (`TaskRegistry.commands`) shows the record's command;",
         "(3) a record-only skill (a record, no manifest folder or entry module) is not a `Task`: it is not in `TaskRegistry.commands()`, not runnable, no problem is reported, and `parse` does not find its command; it is listed through `SkillCatalog.list()` only;",
         plan)
p = once(p,
         "such a skill is listed by its command but is not made runnable by T-06 (report as a note, G-V2.CONVERT moves the skills one by one).",
         "such a skill is listed through `SkillCatalog.list()` only and is not made runnable by T-06 (owner decision (c) of 2026-11-08, worded by A-108; G-V2.CONVERT moves the skills one by one).",
         plan)
out("plan", p)

row = ("| D-310 | **G-V2.MODEL, wording of T-06, owner maldun, 2026-11-08 (A-108).** Decision (c) of 2026-11-08: a record-only skill (a record, but no manifest folder or entry module) "
       "is listed through `SkillCatalog.list()` only: not a `Task`, not in `TaskRegistry.commands()`, not runnable, until G-V2.CONVERT. A-108 corrects the two sentences of the T-06 text in "
       "`plan.md` and supersedes point 1 of `A-107-note.md` (\"listed by its command\"); no code or test changes. |\n")
l = read(log)
if "| D-310 |" not in l:
    l = l + ("" if l.endswith("\n") else "\n") + row
out("log", l)
PY
copy "$WORK/plan" "$PLAN"
copy "$WORK/log" "$LOG"
finish
if [ "$do_it" = 1 ]; then
    echo "checks after --do:"
    python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia 2>&1 | tail -3 || true
    python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E '^\*\*' || true
fi
