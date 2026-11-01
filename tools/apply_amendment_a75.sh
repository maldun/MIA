#!/usr/bin/env bash
# Amendment A-75 (N-4 integration step 1, 2026-11-01): the Evaluation harness N-4.1 is integrated. It provides no interface (it consumes IF-105), so only the
# list of integrated nodes changes: READY gets N-4.1. The scenario of N-4 calls IF-105 directly and never the harness (noted in the N-4.1 verification), so
# the step adds no coverage; the harness is evidenced by its own tests. Note: specs/mia/amendments/A-75/A-75-note.md
# Made from the INSTALLED file at run time (shared by every integration), refused when its anchor is not found exactly once:
#   tests/helpers/integration.py   the READY line gets N-4.1
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a75.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a75.sh --do      install and run N-4 step_01 and step_02; commit afterwards as "plan: A-75 installed"
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
    sys.exit("tests/helpers/integration.py: the READY line is not found exactly once; install A-75 by hand")
line = lines[0]
match = re.match(r'READY = \{([^}]*)\}(\s*#.*)?\n$', line)
if not match:
    sys.exit("tests/helpers/integration.py: the READY line has an unexpected form; install A-75 by hand")
nodes = [n.strip().strip('"') for n in match.group(1).split(",") if n.strip()]
new_nodes = nodes + [n for n in ("N-4.1",) if n not in nodes]
comment = (match.group(2) or "").rstrip()
if "A-75" not in comment:
    comment = (comment[:-1] + "; A-75: the Evaluation harness)") if comment.endswith(")") else (comment + " (A-75: the Evaluation harness)")
open(out, "w", encoding="utf-8").write(text.replace(line, "READY = {%s}%s\n" % (", ".join('"%s"' % n for n in new_nodes), comment)))
PY
copy "$HELPER" tests/helpers/integration.py
finish
echo
bash tools/run_in_image.sh tests/integration/N-4/step_00/test_step.py tests/integration/N-4/step_01/test_step.py tests/integration/N-4/step_02/test_step.py
