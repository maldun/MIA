#!/usr/bin/env bash
# Amendment A-55 (N-2.4 integration step, 2026-10-31): the Workflow execution N-2.4 is integrated. Its three parts are verified (N-2.4.1, N-2.4.2 with
# findings, N-2.4.3 with accepted deviations) and their real providers are in tests/helpers/contract.py already (A-29 IF-401, A-31 IF-202 and IF-105,
# A-32 IF-402), so only the list of integrated nodes changes: READY gets N-2.4.3, N-2.4.2, N-2.4.1 and N-2.4, and the steps 1 to 3 of N-2.4 run on the real
# parts instead of skipping. No other step changes (N-2 step_03 and later also need N-2.5, N-2.3, N-2.2). Note: specs/mia/amendments/A-55/A-55-note.md
# Protected file that changes:
#   tests/helpers/integration.py   the READY line; made from the INSTALLED file at run time (shared by every integration, so it cannot go stale).
#                                  specs/mia/contract-drafts/tests/helpers/integration.py is the same change on the file as of 9f79dab, for reading.
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1) after the merge of v1-n24-int.
#   bash tools/apply_amendment_a55.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a55.sh --do      install and run the four N-2.4 steps in the image; commit afterwards as "plan: A-55 installed"
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
added = ("N-2.4.3", "N-2.4.2", "N-2.4.1", "N-2.4")
lines = [line for line in text.splitlines(keepends=True) if line.startswith("READY = {")]
if len(lines) != 1:
    sys.exit("tests/helpers/integration.py: the READY line is not found exactly once; install A-55 by hand")
line = lines[0]
match = re.match(r'READY = \{([^}]*)\}(\s*#.*)?\n$', line)
if not match:
    sys.exit("tests/helpers/integration.py: the READY line has an unexpected form; install A-55 by hand")
nodes = [n.strip().strip('"') for n in match.group(1).split(",") if n.strip()]
new_nodes = nodes + [n for n in added if n not in nodes]
comment = (match.group(2) or "").rstrip()
if "A-55" not in comment:
    if comment.endswith(")"):                    # "... (amendment A-02: the Database)" -> "... (amendment A-02: the Database; A-55: the Workflow execution)"
        comment = comment[:-1] + "; A-55: the Workflow execution)"
    else:
        comment = (comment + " (A-55: the Workflow execution)") if comment else "    # nodes whose integration step has been done (A-55: the Workflow execution)"
new_line = "READY = {%s}%s\n" % (", ".join('"%s"' % n for n in new_nodes), comment)
open(out, "w", encoding="utf-8").write(text.replace(line, new_line))
PY
copy "$HELPER" tests/helpers/integration.py
finish
echo
bash tools/run_in_image.sh tests/integration/N-2.4/step_00/test_step.py tests/integration/N-2.4/step_01/test_step.py \
    tests/integration/N-2.4/step_02/test_step.py tests/integration/N-2.4/step_03/test_step.py
