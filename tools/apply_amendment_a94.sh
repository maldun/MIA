#!/usr/bin/env bash
# Amendment A-94 (G-V2.STORE, Verify finding F-04, 2026-11-07): remove what a second run of tools/apply_amendment_a92.sh --do duplicated in four places.
#   No requirement, check or interface changes; the content of REQ-GTB-021, TC-GTB-022 and TC-IF-301-20 is as A-92 meant it. Only the doubles go.
# Note: specs/mia/amendments/A-94-note.md
# Files that change (made from the INSTALLED files at run time; with no double in the file the edit does nothing, so a second --do changes nothing):
#   N-3.2 test-spec.md                                      the scenario TC-GTB-022 stood twice (trace_check error "scenario defined 2 times")
#   goals/G-V2.STORE/goal.md                                the scope row REQ-GTB-021 stood twice
#   tests/acceptance/contract/test_if_301_v2_graph_tables.py   the case test_a_record_under_another_id_is_refused stood twice (Python keeps the second: 16 cases ran, not 17)
#   tests/helpers/mocks/if_301_graph_tables_v2.py           the `if record_id ...` block of _check stood twice
#   N-3.2 requirements.md                                   REQ-GTB-021 is listed in the group HD (the table of groups forgot it)
# The cause is fixed in tools/apply_amendment_a92.sh (the "done" test came after the anchor test); A-93 has the done test first.
# Independent of A-93: either order works.
#   bash tools/apply_amendment_a94.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a94.sh --do      remove the doubles, run the checks; commit afterwards as "plan: A-94 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
NODE=specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs
GOAL=specs/mia/goals/G-V2.STORE/goal.md
MOCK=tests/helpers/mocks/if_301_graph_tables_v2.py
SUITE=tests/acceptance/contract/test_if_301_v2_graph_tables.py
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$NODE" "$GOAL" "$MOCK" "$SUITE" "$WORK" <<'PY'
import os
import sys
node, goal, mock, suite, work = sys.argv[1:6]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def dedupe(text, block, where, lead=""):
    """Keep the first copy of `block` and remove every further copy together with the `lead` before it (a blank line between two cases).
    The block must be there at least once (else the anchor is gone: refuse)."""
    if block not in text:
        sys.exit("%s: the block is not there (%s); install A-94 by hand" % (where, block[:70].strip()))
    first = text.index(block) + len(block)
    return text[:first] + text[first:].replace(lead + block, "")


path = os.path.join(node, "test-spec.md")
scenario = """### TC-GTB-022 – A record under another ID is refused
- Verifies: REQ-GTB-021
- Given: a node whose own ID is `n1`
- When: it is written under the record ID `x`, and then under the record ID `n1`
- Then: the write under `x` is refused and names `id`
- And: nothing is stored under `x`; the write under `n1` is accepted (the twin differs only in the broken rule)

"""
text = dedupe(read(path), scenario, path)
if text.count("### TC-GTB-022 – ") != 1:
    sys.exit("%s: the scenario of TC-GTB-022 is not there exactly once after the cleanup; check by hand" % path)
out("test-spec.md", text)

out("goal.md", dedupe(read(goal), "| REQ-GTB-021 | in | A-92 |\n", goal))

text = read(suite)
start = text.index('    @mark.req("IF-301", "REQ-GTB-021")\n    @each_provider(IF, make=subject)\n    def test_a_record_under_another_id_is_refused(')
end = text.index("\n    @mark", start + 10) if "\n    @mark" in text[start + 10:] else len(text)
case = text[start:end]
case_block = case if case.endswith("\n") else case + "\n"
text = dedupe(text, case_block, suite, lead="\n")
if text.count("def test_a_record_under_another_id_is_refused(") != 1:
    sys.exit("%s: the case is not there exactly once after the cleanup; check by hand" % suite)
out("suite.py", text)

block = """    if record_id is not None and record_id != record["id"]:      # the record is stored under the ID it carries (REQ-GTB-021)
        return {"rule": "record_identity", "detail": "id"}
"""
out("mock.py", dedupe(read(mock), block, mock))

path = os.path.join(node, "requirements.md")
text = read(path)
old, new = "| REQ-GTB-017, REQ-GTB-018, REQ-GTB-019, REQ-GTB-020 |", "| REQ-GTB-017, REQ-GTB-018, REQ-GTB-019, REQ-GTB-020, REQ-GTB-021 |"
if new not in text:
    if text.count(old) != 1:
        sys.exit("%s: the row of the group HD is not found; install A-94 by hand" % path)
    text = text.replace(old, new, 1)
out("requirements.md", text)
PY
copy "$WORK/requirements.md" "$NODE/requirements.md"
copy "$WORK/test-spec.md"    "$NODE/test-spec.md"
copy "$WORK/goal.md"         "$GOAL"
copy "$WORK/suite.py"        "$SUITE"
copy "$WORK/mock.py"         "$MOCK"
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== no test method is defined twice in the files of the amendments (the check F-04 asked for)"
    python3 -I - "$SUITE" tests/acceptance/test_graph_record_identity.py tests/acceptance/test_graph_records.py <<'PY2'
import ast
import collections
import sys
bad = 0
for path in sys.argv[1:]:
    for cls in [n for n in ast.walk(ast.parse(open(path, encoding="utf-8").read())) if isinstance(n, ast.ClassDef)]:
        for name, count in collections.Counter(n.name for n in cls.body if isinstance(n, ast.FunctionDef)).items():
            if count > 1:
                print("DOUBLE: %s %s.%s x%d" % (path, cls.name, name, count)); bad += 1
print("none" if not bad else "%d double(s)" % bad)
PY2
    echo "== trace_check: 'scenario defined 2 times' must be gone (none expected); the total is the known baseline of 517 errors (TC-GTB-001..005 and others are part of it)"
    python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests > "$WORK/trace.txt" 2>&1 || true
    grep "defined 2 times" "$WORK/trace.txt" || echo none
    echo "total errors: $(grep -c '| ERROR |' "$WORK/trace.txt")"
    echo "== the checks of the cleaned files"
    python tests/acceptance/contract/test_if_301_v2_graph_tables.py -k _mock 2>&1 | tail -1
    python tests/acceptance/test_graph_record_identity.py 2>&1 | tail -1
    python tests/acceptance/test_graph_records.py 2>&1 | tail -1
fi
