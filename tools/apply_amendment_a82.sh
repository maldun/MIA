#!/usr/bin/env bash
# Amendment A-82 (root test table, 2026-11-01): the first cell of the 29 rows TC-MIA-001 to -029 of specs/mia/test-spec.md reads "TC-MIA-001 (AC-1)". trace_check
# reads a test-spec row only when the first cell is the id alone, so these 29 checks were unknown to it and 44 requirement lines reported "Verified by TC-MIA-nnn,
# which is in no test-spec table". The "(AC-n)" suffix goes (the acceptance criterion stays in requirements.md, "Acceptance criterion: AC-n"; the status
# table specs/mia/tc-mia-status.md names both). Nothing else changes. Note: specs/mia/amendments/A-82/A-82-note.md
# Made from the INSTALLED file at run time; refused when the rows are not found in the known form (29, or none left):
#   specs/mia/test-spec.md   "| TC-MIA-nnn (AC-n) |"  ->  "| TC-MIA-nnn |"
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a82.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a82.sh --do      install and run the trace check; commit afterwards as "plan: A-82 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - specs/mia/test-spec.md "$WORK/test-spec.md" <<'PY'
import re
import sys
installed, out = sys.argv[1:3]
text = open(installed, encoding="utf-8").read()
rows = re.findall(r"^\| TC-MIA-\d+ \(AC-\d+\) \|", text, re.M)
if rows and len(rows) != 29:
    sys.exit("%s: %d rows with an (AC-n) suffix, expected 29; install A-82 by hand" % (installed, len(rows)))
open(out, "w", encoding="utf-8").write(re.sub(r"^(\| TC-MIA-\d+) \(AC-\d+\) \|", r"\1 |", text, flags=re.M))
PY
copy "$WORK/test-spec.md" specs/mia/test-spec.md
finish
echo
echo "== trace_check: lines 'Verified by TC-MIA' that are in no table (none expected)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -c "TC-MIA.*no test-spec" || true
