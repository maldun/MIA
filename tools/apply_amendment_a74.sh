#!/usr/bin/env bash
# Amendment A-74 (N-1 integration step 3, 2026-11-01; owner decision D-176): the Chat and login views N-1.1 are integrated. The real page cannot take the place of
# the stand-in page in the scenario without changing the protected scenario (D-176 chose not to), so READY gets N-1.1 and step 03 runs the scenario as it is.
# The real page is evidenced by its own page tests (tests/js). Note: specs/mia/amendments/A-74/A-74-note.md
# Made from the INSTALLED file at run time (A-72 and A-73 must be installed), refused when its anchor is not found exactly once:
#   tests/helpers/integration.mjs   READY gets N-1.1
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a74.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a74.sh --do      install, run the four N-1 steps; commit afterwards as "plan: A-74 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - tests/helpers/integration.mjs "$WORK" <<'PY'
import os
import re
import sys
integration, work = sys.argv[1:3]
text = open(integration, encoding="utf-8").read()
match = re.search(r"^export const READY = new Set\((\[[^\]]*\])?\);(.*)$", text, re.M)
if not match or len(re.findall(r"^export const READY = ", text, re.M)) != 1:
    sys.exit("%s: the READY line is not found exactly once in its usual form; install A-74 by hand" % integration)
nodes = re.findall(r"'([^']+)'", match.group(1) or "")
if "N-1.1" not in nodes:
    nodes.append("N-1.1")
comment = match.group(2)
if "A-74" not in comment:
    comment = comment.rstrip()[:-1] + "; A-74: the Chat and login views)" if comment.rstrip().endswith(")") else comment.rstrip() + " (A-74: the Chat and login views)"
text = text[:match.start()] + "export const READY = new Set([%s]);%s" % (", ".join("'%s'" % n for n in nodes), comment) + text[match.end():]
open(os.path.join(work, "integration.mjs"), "w", encoding="utf-8").write(text)
PY
copy "$WORK/integration.mjs" tests/helpers/integration.mjs
finish
echo
echo "== N-1 steps"
node --test "tests/integration/N-1/step_0*/test_step.test.mjs" 2>&1 | grep -E "^not ok|^ok .*SKIP|^# (pass|fail|skipped)"
