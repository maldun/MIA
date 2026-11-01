#!/usr/bin/env bash
# Amendment A-80 (N-2 integration step 5, 2026-11-01): the API and accounts N-2.1 are integrated, and with them the node N-2 (all five children done). The real
# providers of IF-101 (routes and accounts, A-05/A-07) and IF-104 (A-51) are in tests/helpers/contract.py, so only the list of integrated nodes changes:
# READY gets N-2.1 and N-2. The unbuilt events of an answer skip in the IF-101 suite (TD-11, D-173; one more is REQ-CHV-008, out of G-V1).
# N-2 wakes no N-0 step: they all need N-1 as well. Note: specs/mia/amendments/A-80/A-80-note.md
# Made from the INSTALLED file at run time (shared by every integration), refused when its anchor is not found exactly once:
#   tests/helpers/integration.py   the READY line gets N-2.1 and N-2
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a80.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a80.sh --do      install and run N-2 step_05; commit afterwards as "plan: A-80 installed"
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
    sys.exit("tests/helpers/integration.py: the READY line is not found exactly once; install A-80 by hand")
line = lines[0]
match = re.match(r'READY = \{([^}]*)\}(\s*#.*)?\n$', line)
if not match:
    sys.exit("tests/helpers/integration.py: the READY line has an unexpected form; install A-80 by hand")
nodes = [n.strip().strip('"') for n in match.group(1).split(",") if n.strip()]
new_nodes = nodes + [n for n in ("N-2.1", "N-2") if n not in nodes]
comment = (match.group(2) or "").rstrip()
if "A-80" not in comment:
    comment = (comment[:-1] + "; A-80: the API and accounts)") if comment.endswith(")") else (comment + " (A-80: the API and accounts)")
open(out, "w", encoding="utf-8").write(text.replace(line, "READY = {%s}%s\n" % (", ".join('"%s"' % n for n in new_nodes), comment)))
PY
copy "$HELPER" tests/helpers/integration.py
finish
echo
bash tools/run_in_image.sh tests/integration/N-2/step_00/test_step.py tests/integration/N-2/step_01/test_step.py tests/integration/N-2/step_03/test_step.py tests/integration/N-2/step_04/test_step.py tests/integration/N-2/step_05/test_step.py
