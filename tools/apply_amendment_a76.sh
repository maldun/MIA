#!/usr/bin/env bash
# Amendment A-76 (N-4 integration step 2, 2026-11-01): the Operation layer N-4.2 is integrated, and with it the node N-4 (both children done). N-4.2 provides
# no interface, so only the list of integrated nodes changes: READY gets N-4.2 and N-4. The scenario of N-4 never starts the compose stack (TC-N4-001 to -003
# run in stage 3), so the step adds no coverage; the layer is evidenced by its own tests. N-4 does not wake any N-0 step: they all need N-1 as well.
# Note: specs/mia/amendments/A-76/A-76-note.md
# Made from the INSTALLED file at run time (shared by every integration), refused when its anchor is not found exactly once:
#   tests/helpers/integration.py   the READY line gets N-4.2 and N-4
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a76.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a76.sh --do      install and run the N-4 steps; commit afterwards as "plan: A-76 installed"
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
    sys.exit("tests/helpers/integration.py: the READY line is not found exactly once; install A-76 by hand")
line = lines[0]
match = re.match(r'READY = \{([^}]*)\}(\s*#.*)?\n$', line)
if not match:
    sys.exit("tests/helpers/integration.py: the READY line has an unexpected form; install A-76 by hand")
nodes = [n.strip().strip('"') for n in match.group(1).split(",") if n.strip()]
new_nodes = nodes + [n for n in ("N-4.2", "N-4") if n not in nodes]
comment = (match.group(2) or "").rstrip()
if "A-76" not in comment:
    comment = (comment[:-1] + "; A-76: the Operation layer)") if comment.endswith(")") else (comment + " (A-76: the Operation layer)")
open(out, "w", encoding="utf-8").write(text.replace(line, "READY = {%s}%s\n" % (", ".join('"%s"' % n for n in new_nodes), comment)))
PY
copy "$HELPER" tests/helpers/integration.py
finish
echo
bash tools/run_in_image.sh tests/integration/N-4/step_00/test_step.py tests/integration/N-4/step_01/test_step.py tests/integration/N-4/step_02/test_step.py
