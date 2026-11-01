#!/usr/bin/env bash
# Amendment A-84 (2026-11-01, at the owner's request): the sign-off of the owner on TD-15 (adaptation to negative feedback, FR-29). The text of FR-29 contains the
# word "safety", so trace_check demands a `Sign-off: <responsible person, date>` line. The owner asked for it in the session of 2026-11-01. Note: specs/mia/amendments/A-84/A-84-note.md
# Made from the INSTALLED file at run time, refused when the anchor is not found exactly once:
#   specs/mia/deferred.md   TD-15 gets the line `- Sign-off: Stefan Reiterer, 2026-11-01` before its Decision line
# INSTALL IT ON THE LINE OF WORK goal/v1 (A-83 must be installed).
#   bash tools/apply_amendment_a84.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a84.sh --do      install and run the trace check; commit afterwards as "plan: A-84 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - specs/mia/deferred.md "$WORK/deferred.md" <<'PY'
import re
import sys
installed, out = sys.argv[1:3]
text = open(installed, encoding="utf-8").read()
m = re.search(r"^## TD-15 [^\n]*\n(?:(?!^## ).*\n)*", text, re.M)
if not m:
    sys.exit("%s: TD-15 is not found; install A-84 by hand (A-83 must be installed first)" % installed)
block = m.group(0)
if "- Sign-off:" in block:
    new = block
else:
    if block.count("\n- Decision: D-178") != 1:
        sys.exit("%s: the Decision line of TD-15 is not found exactly once; install A-84 by hand" % installed)
    new = block.replace("\n- Decision: D-178", "\n- Sign-off: Stefan Reiterer, 2026-11-01\n- Decision: D-178", 1)
open(out, "w", encoding="utf-8").write(text.replace(block, new, 1))
PY
copy "$WORK/deferred.md" specs/mia/deferred.md
finish
echo
echo "== trace_check, errors about TD-15 (none expected)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E "ERROR.*TD-15" || echo none
