#!/usr/bin/env bash
# Amendment A-112 (G-V2.TOOLBOX, owner decisions of 2026-11-11): the table transforms of IF-302 (the versioned code of a transform, thin: id and version required, REQ-RTB-009)
# and its entry in the table list of IF-102. Note: specs/mia/amendments/A-112-note.md
# Files that change (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found exactly once, so a second
# --do changes nothing). A-110 must be installed first (this script builds on its text):
#   contracts/IF-302-record-tables.md   definitions(), required fields, version history; the version number becomes the next free one (v8 -> v9 today, v10 when A-141 is installed first)
#   contracts/IF-102-storage-interface.md   the table list, version history; the version number goes up by one
#   specs/mia/test-requirements.md   TC-RTB-009 joins the "Applies to:" line of TR-TOOLBOX-001 (next to TC-RTB-008), so the check has a test requirement (M41)
#   specs/mia/review-log.md   row D-nnn (installed), the next free id of the TOOLBOX range D-220..239, appended
# NOT changed here (separate steps): the mock and the suite case (tools/apply_red_tests_a112.sh), REQ-RTB-001's count, the Phases text of the goal record.
#   bash tools/apply_amendment_a112.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a112.sh --do      install and run the checks; commit afterwards as "contracts: A-112 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
C302=${A112_IF302:-contracts/IF-302-record-tables.md}
C102=${A112_IF102:-contracts/IF-102-storage-interface.md}
LOG=${A112_LOG:-specs/mia/review-log.md}
TR=${A112_TR:-specs/mia/test-requirements.md}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$C302" "$C102" "$LOG" "$TR" "$WORK" <<'PY'
import os
import re
import sys
c302, c102, log, tr, work = sys.argv[1:6]
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
    if "REQ-RTB-009" in text or "A-112" in text:
        return text, int(m.group(2))
    return m.group(1) + str(int(m.group(2)) + 1) + "\n" + text[m.end():], int(m.group(2)) + 1


def history_row(text, row, where):
    """Append `row` after the last version-history row (a line `| vN | ...`)."""
    if "A-112" in text.split("\n## Version history")[-1]:
        return text
    lines = text.split("\n")
    last = max(i for i, l in enumerate(lines) if re.match(r"\| v\d+ \|", l))
    lines.insert(last + 1, row)
    return "\n".join(lines)


t = read(c302)
if "transform_meta" not in t:
    sys.exit("A-110 is not installed in %s: install it first" % c302)
t, v302 = bump(t, c302)
V = "**[v%d]**" % v302
t = once(t,
         "`transform_meta` (trust and lifecycle of a transform, REQ-RTB-008) is versioned and not deletable;",
         "`transform_meta` (trust and lifecycle of a transform, REQ-RTB-008) and " + V + " `transforms` (the versioned code of a transform, REQ-RTB-009) are versioned and not deletable;",
         c302)
t = once(t,
         "and `changed_by` (an account); the record id is the transform id.",
         "and `changed_by` (an account); the record id is the transform id; " + V + " `transforms` {id, version} with `id` a text that is not empty and `version` an integer of at least 1 "
         "(a boolean, a float such as `1.0` or a text is rule `schema`, detail `version`; a missing field is rule `schema` with that field as detail), and the free fields `inputs`, `outputs` "
         "(JSON schemas) and `code` (text; missing, empty or null are all valid, a stub transform); `version` is the version of the code as the file states it, not the Storage counter; "
         "the record id is the transform id.",
         c302)
t = history_row(t, "| v%d | 2026-11-11 | the table `transforms`: the versioned code of a transform, thin (id and version required, the rest free, an empty code is valid), one record per transform id, not deletable (owner 2026-11-11) | A-112 |" % v302, c302)
out("if302", t)

u = read(c102)
u, v102 = bump(u, c102)
u = once(u, "`reports`, `transform_meta`);", "`reports`, `transform_meta`, `transforms`);", c102)
u = history_row(u, "| v%d | 2026-11-11 | the table list names `transforms` (IF-302 v%d); no new operation | A-112 |" % (v102, v302), c102)
out("if102", u)

r = read(tr)
r = once(r, "TC-WFM-090, TC-RTB-008\n", "TC-WFM-090, TC-RTB-008, TC-RTB-009\n", tr)
out("tr", r)

l = read(log)
if "A-112 installed" not in l:
    used = [int(n) for n in re.findall(r"^\| D-(2[23]\d) \|", l, re.M)]
    new_id = "D-%d" % (max(used) + 1 if used else 220)
    l = l + ("" if l.endswith("\n") else "\n") + (
        "| %s | **A-112 installed, G-V2.TOOLBOX, 2026-11-11.** `contracts/IF-302-record-tables.md` v%d and `contracts/IF-102-storage-interface.md` v%d name the table `transforms` "
        "(REQ-RTB-009; id and version required, a missing, empty or null code valid). The mock and the suite case are installed with `tools/apply_red_tests_a112.sh`. |\n" % (new_id, v302, v102))
out("log", l)
PY
copy "$WORK/if302" "$C302"
copy "$WORK/if102" "$C102"
copy "$WORK/tr" "$TR"
copy "$WORK/log" "$LOG"
finish
if [ "$do_it" = 1 ]; then
    echo "checks after --do:"
    python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia 2>&1 | tail -3 || true
    python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E '^\*\*' || true
fi
