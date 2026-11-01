#!/usr/bin/env bash
# Amendment A-78 (N-2 integration step 2, 2026-11-01): the Workflow management N-2.3 is integrated. Its real provider of IF-203 (WorkflowLibrary on the real
# Storage in a fresh folder) is in tests/helpers/contract.py since A-14, so only the list of integrated nodes changes: READY gets N-2.3. The holdouts of N-2.3
# (REQ-WFM-014/015/016/024) are the owner's and are not touched. Note: specs/mia/amendments/A-78/A-78-note.md
# Made from the INSTALLED file at run time (shared by every integration), refused when its anchor is not found exactly once:
#   tests/helpers/integration.py   the READY line gets N-2.3
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a78.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a78.sh --do      install and run N-2 step_02; commit afterwards as "plan: A-78 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
HELPER=$(mktemp)
trap 'rm -f "$HELPER"' EXIT
python3 - tests/helpers/integration.py "$HELPER" <<'PY'
import re
import sys
installed, out = sys.argv[1:3]
text = open(installed, encoding="utf-8").read()
lines = [line for line in text.splitlines(keepends=True) if line.startswith("READY = {")]
if len(lines) != 1:
    sys.exit("tests/helpers/integration.py: the READY line is not found exactly once; install A-78 by hand")
line = lines[0]
match = re.match(r'READY = \{([^}]*)\}(\s*#.*)?\n$', line)
if not match:
    sys.exit("tests/helpers/integration.py: the READY line has an unexpected form; install A-78 by hand")
nodes = [n.strip().strip('"') for n in match.group(1).split(",") if n.strip()]
new_nodes = nodes + [n for n in ("N-2.3",) if n not in nodes]
comment = (match.group(2) or "").rstrip()
if "A-78" not in comment:
    comment = (comment[:-1] + "; A-78: the Workflow management)") if comment.endswith(")") else (comment + " (A-78: the Workflow management)")
open(out, "w", encoding="utf-8").write(text.replace(line, "READY = {%s}%s\n" % (", ".join('"%s"' % n for n in new_nodes), comment)))
PY
copy "$HELPER" tests/helpers/integration.py
finish
echo
bash tools/run_in_image.sh tests/integration/N-2/step_00/test_step.py tests/integration/N-2/step_01/test_step.py tests/integration/N-2/step_02/test_step.py
