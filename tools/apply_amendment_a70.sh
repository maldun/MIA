#!/usr/bin/env bash
# Amendment A-70 (N-4.1 re-verification 2, S3 and S4; decisions D-166 and D-172 already taken, repair of their form, D-174): REQ-EVL-011 carries `Relaxed: TD-08` and
# its `Target`; the target check of TD-07 and TD-08 is `specified only` (no test can carry a deferral marker while the target is not built); TD-07 gets a dated trigger.
# Note: specs/mia/amendments/A-70/A-70-note.md
# Protected files that change (made from the INSTALLED files at run time, each edit refused when its anchor is not found exactly once):
#   specs/mia/deferred.md                                                    TD-07 trigger with a date, TD-07 and TD-08 `Target check: specified only`
#   specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation/requirements.md   REQ-EVL-011: `Relaxed: TD-08`, `Target`, History
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a70.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a70.sh --do      install and run the trace check for TD-07 and TD-08; commit afterwards as "plan: A-70 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
REQ=specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation/requirements.md
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - specs/mia/deferred.md "$REQ" "$WORK" <<'PY'
import os
import re
import sys
deferred, req, work = sys.argv[1:4]
read = lambda path: open(path, encoding="utf-8").read()


def write(name, text):
    open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def block_of(text, heading, where):
    match = re.search(r"%s.*?(?=\n## |\n### |\Z)" % re.escape(heading), text, re.S)
    if not match:
        sys.exit("%s: %s is missing" % (where, heading))
    return match.group(0)


def once(block, old, new, where, what):
    """old -> new exactly once; a block that has the new part already is left as it is (the copy then reports unchanged)"""
    if new in block:
        return block
    if block.count(old) != 1:
        sys.exit("%s: %s is not found exactly once; install A-70 by hand" % (where, what))
    return block.replace(old, new)


text = read(deferred)
for td in ("TD-07", "TD-08"):
    block = block_of(text, "## %s " % td, deferred)
    if "- Target check: specified only\n" not in block:
        changed, count = re.subn(r"- Target check: TC-EVL-0\d\d\n", "- Target check: specified only\n", block)
        if count != 1:
            sys.exit("%s: the Target check line of %s is not found exactly once; install A-70 by hand" % (deferred, td))
        text = text.replace(block, changed)
block = block_of(text, "## TD-07 ", deferred)
text = text.replace(block, once(block, "- Trigger: the first eval target with a judge\n", "- Trigger: the first eval target with a judge, or 2026-12-31, whichever first\n", deferred, "the Trigger line of TD-07"))
write("deferred.md", text)

body = read(req)
block = block_of(body, "### REQ-EVL-011 ", req)
if "- Relaxed: TD-08\n" not in block:
    old = "- Status: Approved\n- History: –\n"
    if block.count(old) != 1:
        sys.exit("%s: the Status/History lines of REQ-EVL-011 are not found exactly once" % req)
    block = block.replace(old, "- Status: Approved\n- Relaxed: TD-08\n- Target: every suite kind runs through IF-105\n- History: A-70 (2026-11-01): Relaxed TD-08 (D-172, D-174)\n")
    body = body.replace(block_of(body, "### REQ-EVL-011 ", req), block)
write("requirements.md", body)
PY
copy "$WORK/deferred.md" specs/mia/deferred.md
copy "$WORK/requirements.md" "$REQ"
finish
echo
echo "== trace_check, errors naming TD-07, TD-08 or REQ-EVL-011 (none expected)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E 'ERROR.*(TD-07|TD-08|EVL-011)' || echo "none"
