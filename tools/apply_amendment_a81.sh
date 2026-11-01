#!/usr/bin/env bash
# Amendment A-81 (N-0 integration steps 02 to 04, 2026-11-01): the Web Frontend N-1 is listed as integrated in the Python READY (its three children were integrated
# in the JavaScript READY by A-72, A-73 and A-74; the root steps are Python). N-3, N-4 and N-2 are listed already, so this one entry wakes N-0 step_02 (N-1 real),
# step_03 (N-4 real) and step_04 (N-2 real): they all need only N-1 more. Step_05 still needs N-5. Note: specs/mia/amendments/A-81/A-81-note.md
# Made from the INSTALLED file at run time (shared by every integration), refused when its anchor is not found exactly once:
#   tests/helpers/integration.py   the READY line gets N-1
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a81.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a81.sh --do      install and run N-0 steps 02 to 04; commit afterwards as "plan: A-81 installed"
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
    sys.exit("tests/helpers/integration.py: the READY line is not found exactly once; install A-81 by hand")
line = lines[0]
match = re.match(r'READY = \{([^}]*)\}(\s*#.*)?\n$', line)
if not match:
    sys.exit("tests/helpers/integration.py: the READY line has an unexpected form; install A-81 by hand")
nodes = [n.strip().strip('"') for n in match.group(1).split(",") if n.strip()]
new_nodes = nodes + [n for n in ("N-1",) if n not in nodes]
comment = (match.group(2) or "").rstrip()
if "A-81" not in comment:
    comment = (comment[:-1] + "; A-81: the Web Frontend)") if comment.endswith(")") else (comment + " (A-81: the Web Frontend)")
open(out, "w", encoding="utf-8").write(text.replace(line, "READY = {%s}%s\n" % (", ".join('"%s"' % n for n in new_nodes), comment)))
PY
copy "$HELPER" tests/helpers/integration.py
finish
echo
bash tools/run_in_image.sh tests/integration/N-0/step_00/test_step.py tests/integration/N-0/step_01/test_step.py tests/integration/N-0/step_02/test_step.py tests/integration/N-0/step_03/test_step.py tests/integration/N-0/step_04/test_step.py tests/integration/N-0/step_05/test_step.py
