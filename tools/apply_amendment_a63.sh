#!/usr/bin/env bash
# Amendment A-63 (N-4.1, D-164 F6, 2026-10-31): the TC-EVL tests move from tests/ to the protected tests/acceptance/.
# Protected files that are created (drafts in specs/mia/amendments/A-63/tests/acceptance/, the copies of tests/<name>.py with the paths one folder deeper):
#   tests/acceptance/test_eval_platform.py      TC-EVL-001, -004, -008, -011
#   tests/acceptance/test_decide_guard.py       TC-EVL-002
#   tests/acceptance/test_judge_calibration.py  TC-EVL-003
#   tests/acceptance/test_check_baselines.py    TC-EVL-005
#   tests/acceptance/test_skill_path_doc.py     TC-EVL-006
#   tests/acceptance/test_measure_latency.py    TC-EVL-007 (the frame-rate half stays in tests/js/measure-fps.test.mjs)
# Shared files BUILT FROM THE INSTALLED FILES at run time: the node's test-spec.md (each row names its protected test file, one note line) and
# docs/skill-path.md (the name of the test that runs its examples).
# With --do the six protected tests are run (host python, as CLAUDE.md); only when all pass are the old copies tests/<name>.py removed.
# Note: specs/mia/amendments/A-63/A-63-note.md.
#   bash tools/apply_amendment_a63.sh           show what changes (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a63.sh --do      install, run the protected tests, remove the old copies; commit afterwards as "plan: A-63 installed"
# A63_DRAFT=1 bash tools/apply_amendment_a63.sh  (author only) rewrite the drafts from the current tests/<name>.py
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
NAMES="test_eval_platform test_decide_guard test_judge_calibration test_check_baselines test_skill_path_doc test_measure_latency"
SPEC=specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation/test-spec.md
DRAFTS=specs/mia/amendments/A-63/tests/acceptance
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$WORK" "$DRAFTS" "$SPEC" $NAMES <<'PY'
import os
import sys
work, drafts, spec, names = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
# the lines of the unprotected tests that know their folder, and what they become one folder deeper
MOVES = [
    ('REPO = os.path.dirname(HERE)\n', 'REPO = os.path.dirname(os.path.dirname(HERE))\n'),
    ('os.path.join(HERE, "helpers"', 'os.path.join(os.path.dirname(HERE), "helpers"'),
    ('sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))', 'sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools"))'),
]


def moved(name, text):
    run = "Run: python tests/%s.py\n" % name
    if text.count(run) != 1:
        sys.exit("tests/%s.py: the line %r is not found exactly once; install A-63 by hand" % (name, run.strip()))
    text = text.replace(run, "Protected since A-63 (D-164). Run: python tests/acceptance/%s.py\n" % name)
    for old, new in MOVES:
        text = text.replace(old, new)
    if 'os.path.join(HERE, "helpers"' in text or "REPO = os.path.dirname(HERE)\n" in text:
        sys.exit("tests/%s.py: a path is left one folder too high; install A-63 by hand" % name)
    return text


for name in names:
    source, installed, draft = "tests/%s.py" % name, "tests/acceptance/%s.py" % name, os.path.join(drafts, name + ".py")
    if os.environ.get("A63_DRAFT"):
        os.makedirs(drafts, exist_ok=True)
        open(draft, "w", encoding="utf-8").write(moved(name, open(source, encoding="utf-8").read()))
        continue
    if os.path.exists(source):
        built = moved(name, open(source, encoding="utf-8").read())
        if built != open(draft, encoding="utf-8").read():
            sys.exit("%s changed since the draft of A-63: the protected copy would not be what was reviewed. Redraft (A63_DRAFT=1) and review again" % source)
    elif os.path.exists(installed):
        built = open(installed, encoding="utf-8").read()          # moved already: nothing to do for this file
    else:
        sys.exit("neither %s nor %s exists; install A-63 by hand" % (source, installed))
    open(os.path.join(work, name + ".py"), "w", encoding="utf-8").write(built)
if os.environ.get("A63_DRAFT"):
    sys.exit(0)

FILES = {"TC-EVL-001": "test_eval_platform", "TC-EVL-002": "test_decide_guard", "TC-EVL-003": "test_judge_calibration", "TC-EVL-004": "test_eval_platform",
         "TC-EVL-005": "test_check_baselines", "TC-EVL-006": "test_skill_path_doc", "TC-EVL-007": "test_measure_latency", "TC-EVL-008": "test_eval_platform",
         "TC-EVL-011": "test_eval_platform"}
NOTE = ("Since A-63 (D-164 F6) the tests of TC-EVL-001 to TC-EVL-008 and TC-EVL-011 are protected in `tests/acceptance/` (the frame-rate half of "
        "TC-EVL-007 stays in `tests/js/measure-fps.test.mjs`); each row names its file.\n\n")
text = open(spec, encoding="utf-8").read()
if "A-63" not in text:
    if text.count("## Test cases\n") != 1:
        sys.exit("%s: the heading '## Test cases' is not found exactly once; install A-63 by hand" % spec)
    text = text.replace("## Test cases\n", "## Test cases\n\n" + NOTE.rstrip("\n") + "\n", 1)
    lines = text.split("\n")
    for tc, name in FILES.items():
        rows = [i for i, line in enumerate(lines) if line.startswith("| %s | " % tc)]
        if len(rows) != 1:
            sys.exit("%s: the row of %s is not found exactly once; install A-63 by hand" % (spec, tc))
        cells = lines[rows[0]].split(" | ")
        cells[4] += "; test: `tests/acceptance/%s.py`" % name           # the column Setup / inputs
        lines[rows[0]] = " | ".join(cells)
    text = "\n".join(lines)
open(os.path.join(work, "test-spec.md"), "w", encoding="utf-8").write(text)

doc = open("docs/skill-path.md", encoding="utf-8").read().replace("`tests/test_skill_path_doc.py`", "`tests/acceptance/test_skill_path_doc.py`")
open(os.path.join(work, "skill-path.md"), "w", encoding="utf-8").write(doc)
PY
if [ -n "${A63_DRAFT:-}" ]; then echo "drafts written to $DRAFTS"; exit 0; fi
for name in $NAMES; do copy "$WORK/$name.py" "tests/acceptance/$name.py"; done
copy "$WORK/test-spec.md" "$SPEC"
copy "$WORK/skill-path.md" docs/skill-path.md
finish
[ "$do_it" = 1 ] || exit 0
echo
failed=0
for name in $NAMES; do
    printf '== tests/acceptance/%s.py: ' "$name"
    if out=$(python3 "tests/acceptance/$name.py" 2>&1); then echo "$out" | tail -n 1; else echo "FAILED"; echo "$out" | tail -n 15 | sed 's/^/   /'; failed=1; fi
done
if [ "$failed" = 1 ]; then echo "a protected test fails: the old copies in tests/ are kept; fix or undo before committing"; exit 1; fi
for name in $NAMES; do
    if [ -e "tests/$name.py" ]; then rm "tests/$name.py"; echo "removed the old copy tests/$name.py"; fi
done
echo "A-63 installed: commit as \"plan: A-63 installed\""
