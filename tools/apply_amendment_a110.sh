#!/usr/bin/env bash
# Amendment A-110 (G-V2.TOOLBOX, owner decisions of 2026-11-08 and 2026-11-11, D-221): the table transform_meta of IF-302 (trust and lifecycle of a transform, one record per
# transform ID, REQ-RTB-008) and its entry in the table list of IF-102. Note: specs/mia/amendments/A-110-note.md
# Files that change (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found exactly once, so a second
# --do changes nothing):
#   contracts/IF-302-record-tables.md   definitions(), required fields, version history; the version number becomes the next free one (v7 -> v8 today, v9 when A-141 is installed first)
#   contracts/IF-102-storage-interface.md   the table list, version history; the version number goes up by one
#   specs/mia/review-log.md   row D-222 (installed), appended
# NOT changed here (separate steps, suite red first, the owner's go): the mock in tests/helpers/mocks, the contract suites in tests/acceptance/contract, REQ-RTB-001 (its
# "Proposed" line is the place to name the count), the Phases text of the goal record.
#   bash tools/apply_amendment_a110.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a110.sh --do      install and run the checks; commit afterwards as "contracts: A-110 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
C302=${A110_IF302:-contracts/IF-302-record-tables.md}
C102=${A110_IF102:-contracts/IF-102-storage-interface.md}
LOG=${A110_LOG:-specs/mia/review-log.md}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$C302" "$C102" "$LOG" "$WORK" <<'PY'
import os
import re
import sys
c302, c102, log, work = sys.argv[1:5]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def once(text, old, new, where):
    if new in text:
        return text
    if text.count(old) == 1:
        return text.replace(old, new)
    sys.exit("anchor not found exactly once (%d) in %s: %r" % (text.count(old), where, old[:70]))


def bump(text, where):
    """Title `, vN` -> `, vN+1` unless the amendment is installed already; returns (text, new version)."""
    m = re.match(r"(# IF-\d+ – [^\n]*, v)(\d+)\n", text)
    if not m:
        sys.exit("no version in the title of " + where)
    if "transform_meta" in text:
        return text, int(m.group(2))
    return m.group(1) + str(int(m.group(2)) + 1) + "\n" + text[m.end():], int(m.group(2)) + 1


def history_row(text, row, where):
    """Append `row` after the last version-history row (a line `| vN | ...`)."""
    if "A-110" in text.split("\n## Version history")[-1]:
        return text
    lines = text.split("\n")
    last = max(i for i, l in enumerate(lines) if re.match(r"\| v\d+ \|", l))
    lines.insert(last + 1, row)
    return "\n".join(lines)


t = read(c302)
t, v302 = bump(t, c302)
V = "**[v%d]**" % v302
t = once(t,
         "(a user deletes any record, FR-14); every other table",
         "(a user deletes any record, FR-14); " + V + " `transform_meta` (trust and lifecycle of a transform, REQ-RTB-008) is versioned and not deletable; every other table",
         c302) if "transform_meta" not in t else t
t = once(t,
         "the record id is the workflow id.",
         "the record id is the workflow id; " + V + " `transform_meta` {trust, lifecycle} with `trust` one of `untrusted`, `trusted` and `lifecycle` one of `draft`, `tested`, `retired` "
         "(else rule `schema`, detail the field; a missing field is rule `schema` with that field as detail), and the optional fields `reason` (why untrusted), `evidence` (the check or run named "
         "for `tested`), `baseline_allowed` (boolean, the owner's allowance for an untrusted retired transform), `shipped` (boolean) and `changed_by` (an account); the record id is the transform id.",
         c302)
t = history_row(t, "| v%d | 2026-11-11 | the table `transform_meta`: trust and lifecycle of a transform, one record per transform id, a new version per change, not deletable (owner 2026-11-08 and 2026-11-11: trust and lifecycle survive a new version of the code, REQ-WFM-092) | A-110 |" % v302, c302)
out("if302", t)

u = read(c102)
u, v102 = bump(u, c102)
u = once(u, "`workflow_meta`, `reports`);", "`workflow_meta`, `reports`, `transform_meta`);", c102)
u = history_row(u, "| v%d | 2026-11-11 | the table list names `transform_meta` (IF-302 v%d); no new operation | A-110 |" % (v102, v302), c102)
out("if102", u)

l = read(log)
if "| D-222 |" not in l:
    l = l + ("" if l.endswith("\n") else "\n") + (
        "| D-222 | **A-110 installed, G-V2.TOOLBOX, 2026-11-11.** `contracts/IF-302-record-tables.md` v%d and `contracts/IF-102-storage-interface.md` v%d name the table `transform_meta` "
        "(REQ-RTB-008). The mock, the contract suites, REQ-RTB-001's count and the goal record are separate steps. |\n" % (v302, v102))
out("log", l)
PY
copy "$WORK/if302" "$C302"
copy "$WORK/if102" "$C102"
copy "$WORK/log" "$LOG"
finish
if [ "$do_it" = 1 ]; then
    echo "checks after --do:"
    python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia 2>&1 | tail -3 || true
    python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E '^\*\*' || true
fi
