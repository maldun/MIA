#!/usr/bin/env bash
# Amendment A-102 (G-V2.STORE, F-22 of the sixth look at T-11, owner's decision of 2026-11-08): a limit on the number of values of a document.
#   F-22: a Python-built document that shares sub-objects (31 levels, the same child twice per level: 2**30 paths, no cycle) makes graph_tables.check_record run
#   for minutes, and the backend would have to serialise the expanded document. Decided: refuse a document with more than 100,000 values, counting a value once for
#   every path that reaches it; the walk stops at 100,001, so such a document is refused at once. 100,000 is about 190 times the largest stored document in the
#   repository (529 values, a pipeline of library/pipelines; probe of 202 files, 2026-11-08).
#   REQ-GTB-028 (Graph tables, schema_break naming data) and REQ-SLY-015 (Storage layer, invalid), both Draft until the owner has reviewed and rated them;
#   TC-GTB-029 (new test file, staged in specs/mia/amendments/A-102/), TC-IF-301-24 (contract suite, mock and real), TC-SLY-014 (in tests/test_storage.py, T-12);
#   IF-301 v2 (v2 is not merged, so it stays v2); task T-12.
# Note: specs/mia/amendments/A-102-note.md
# Files that change (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found
# exactly once, so a second --do changes nothing):
#   N-3.2 requirements.md, test-spec.md, test-requirements.md (TR-GTB-001 applies to TC-GTB-029)   N-3.1 requirements.md, test-spec.md
#   goals/G-V2.STORE/goal.md (scope row)   goals/G-V2.STORE/plan.md (T-12)
#   contracts/IF-301-graph-tables.md                                  the size rule, golden 21, decision 16, version history
#   tests/helpers/mocks/if_301_graph_tables_v2.py                     MAX_VALUES, the walk also counts values
#   tests/acceptance/contract/test_if_301_v2_graph_tables.py          case TC-IF-301-24
#   tests/acceptance/test_graph_document_size.py                      new, TC-GTB-029
# After --do: the generated requirement block of architecture.sysml is regenerated and checked.
# THE OWNER REVIEWS REQ-GTB-028 AND REQ-SLY-015 AND RATES THEM (amendment A-103 after the ratings), then installs. Install it only when T-12 is next:
# the real side of TC-IF-301-24 and TC-GTB-029 are red until T-12.
#   bash tools/apply_amendment_a102.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a102.sh --do      install, regenerate the model, run the checks; commit afterwards as "plan: A-102 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
N32=specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs
N31=specs/mia/nodes/N-3-database/nodes/N-3.1-storage-layer
GOAL=specs/mia/goals/G-V2.STORE/goal.md
PLAN=specs/mia/goals/G-V2.STORE/plan.md
CONTRACT=contracts/IF-301-graph-tables.md
MOCK=tests/helpers/mocks/if_301_graph_tables_v2.py
SUITE=tests/acceptance/contract/test_if_301_v2_graph_tables.py
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$N32" "$N31" "$GOAL" "$PLAN" "$CONTRACT" "$MOCK" "$SUITE" "$WORK" <<'PY'
import os
import re
import sys
n32, n31, goal, plan, contract, mock, suite, work = sys.argv[1:9]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def once(text, old, new, where):
    """Replace `old` by `new` when `old` occurs exactly once. The edit counts as done when `new` is in the text already (checked FIRST)."""
    if new in text:
        return text
    if text.count(old) == 1:
        return text.replace(old, new, 1)
    sys.exit("%s: anchor not found exactly once (%s); install A-102 by hand" % (where, old[:70]))


def after_line(text, pattern, addition, where):
    if addition in text:
        return text
    found = list(re.finditer(pattern, text, re.M))
    if len(found) != 1:
        sys.exit("%s: the line %r is not found exactly once; install A-102 by hand" % (where, pattern[:60]))
    end = found[0].end()
    return text[:end] + addition + text[end:]


# --- N-3.2 requirements.md: REQ-GTB-028 after REQ-GTB-027, and in the group TY
path = os.path.join(n32, "requirements.md")
text = read(path)
if "### REQ-GTB-028 " not in text:
    if text.count("### REQ-GTB-027 ") != 1 or not text.rstrip().endswith("(A-98, proposed)"):
        sys.exit("%s: REQ-GTB-027 is not the last block; install A-102 by hand" % path)
    text = text.rstrip("\n") + """

### REQ-GTB-028 – Size of a record
- Level: low   Subject: Persistence
- Text: If a record has more than 100,000 values, counting a value once for every path that reaches it, then the Graph tables shall refuse it as `schema_break` naming `data`.
- Rationale: refines FR-40 and REQ-GTB-027; a record that shares sub-objects can have an exponential number of paths and made the check run for minutes (F-22 of the Verify of G-V2.STORE, A-102); 100,000 is about 190 times the largest stored document in the repository (529 values)
- Parent: FR-40
- Group: TY
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a data node whose value is a list of 99,995 numbers (100,000 values with the record, its id, its data object, its type and the list) is accepted, one of 99,996 is refused naming `data`; a record that names the same child twice on 30 levels (2**30 paths) is refused naming `data` within 5 s; nothing raises (exact)
- Verified by: TC-GTB-029
- Status: Draft
- History: G-V2.STORE Verify F-22, 2026-11-08, new (A-102, proposed)
"""
text = once(text, "REQ-GTB-022, REQ-GTB-027 |", "REQ-GTB-022, REQ-GTB-027, REQ-GTB-028 |", path)
out("n32_requirements.md", text)

# --- N-3.2 test-spec.md: row after TC-GTB-028, scenario before TC-GTB-015
path = os.path.join(n32, "test-spec.md")
text = read(path)
row = ("| TC-GTB-029 | REQ-GTB-028 | Unit | 1 | a data node whose value is a list of 99,995 and one of 99,996 numbers; a record that names the same child twice on 30 levels | the first is stored; "
       "the others are refused naming `data`, the last within 5 s | exact |\n")
text = after_line(text, r"^\| TC-GTB-028 \|[^\n]*\n", row, path)
scenario = """### TC-GTB-029 – A record with too many values is refused
- Verifies: REQ-GTB-028
- Given: a data node whose value is a list of 99,995 numbers (100,000 values with the record, its id, its data object, its type and the list), one with 99,996 numbers, and a record that names the same child twice on 30 levels (2**30 paths, 31 levels deep)
- When: each is written, with a time limit of 5 s
- Then: the first is stored as version 1; the second is refused as `schema_break` naming `data`
- And: the third is refused the same way within the limit; the refusals store nothing

"""
text = once(text, "### TC-GTB-015 – The document form still works\n", scenario + "### TC-GTB-015 – The document form still works\n", path)
out("n32_test-spec.md", text)

# --- test-requirements.md: TR-GTB-001 applies to TC-GTB-029
path = os.path.join(n32, "test-requirements.md")
text = read(path)
m = re.search(r"^### TR-GTB-001 [^\n]*\n(?:(?!^### ).*\n)*", text, re.M)
if not m:
    sys.exit("%s: TR-GTB-001 is not found; install A-102 by hand" % path)
block = m.group(0)
if "TC-GTB-029" not in block:
    new = re.sub(r"^(- Applies to: [^\n]*TC-GTB-028)\n", r"\1, TC-GTB-029\n", block, count=1, flags=re.M)
    if new == block:
        sys.exit("%s: the Applies-to line of TR-GTB-001 does not end with TC-GTB-028; install A-102 by hand" % path)
    text = text.replace(block, new, 1)
out("n32_test-requirements.md", text)

# --- N-3.1 requirements.md: REQ-SLY-015 after REQ-SLY-014
path = os.path.join(n31, "requirements.md")
text = read(path)
if "### REQ-SLY-015 " not in text:
    if text.count("### REQ-SLY-014 ") != 1 or not text.rstrip().endswith("(A-100, proposed)"):
        sys.exit("%s: REQ-SLY-014 is not the last block; install A-102 by hand" % path)
    text = text.rstrip("\n") + """

### REQ-SLY-015 – Size of a document
- Level: low   Subject: Persistence
- Text: If a document that is put has more than 100,000 values, counting a value once for every path that reaches it, then the Storage layer shall refuse it as invalid.
- Rationale: refines REQ-SLY-004 and REQ-GTB-028; a document that shares sub-objects can have an exponential number of paths and the backend would have to serialise all of them (F-22 of the Verify of G-V2.STORE, A-102); 100,000 is about 190 times the largest stored document in the repository (529 values)
- Parent: REQ-SLY-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16: a document with 100,000 values is stored, one with 100,001 is refused as StorageError `invalid` and nothing is stored, for a graph table (rule `schema_break`, detail `data`) and for another table (rule `schema`, detail `too large`); a document that names the same child twice on 30 levels is refused within one second, on the file backend and on PostgreSQL (exact, time limit 1 s)
- Verified by: TC-SLY-014
- Status: Draft
- History: G-V2.STORE Verify F-22, 2026-11-08, new (A-102, proposed)
"""
out("n31_requirements.md", text)

# --- N-3.1 test-spec.md: row after TC-SLY-013, scenario before the assumptions
path = os.path.join(n31, "test-spec.md")
text = read(path)
row = ("| TC-SLY-014 | REQ-SLY-015 | Component | 1 | a task document {"text": "t", "numbers": [...]} with 99,997 and with 99,998 numbers (100,000 and 100,001 values: the document, the text and the list count 3), the same as the value of a graph node (99,995 and 99,996 numbers); "
       "a document that names the same child twice on 30 levels | the 100,000-value document is stored; the others are refused as invalid and nothing is stored, the last within one second | exact, 1 s |\n")
text = after_line(text, r"^\| TC-SLY-013 \|[^\n]*\n", row, path)
scenario = """### TC-SLY-014 – size of a document
- Verifies: REQ-SLY-015
- Given: a task document `{"text": "t", "numbers": [...]}` with 99,997 numbers and one with 99,998 numbers (100,000 and 100,001 values: the document, the text and the list count 3; documents of the tables other than graph tables are mappings), a data node whose value is a list of 99,995 and one of 99,996 numbers as records of a graph table, and a document that names the same child twice on 30 levels
- When: each is put, with a time limit of one second
- Then: the documents with 100,000 values are stored as version 1; the ones with 100,001 values are refused as invalid
- And: the 2**30-path document is refused within the limit; the refusals store nothing; graph tables name `schema_break` and `data`, other tables `schema` and `too large`; the same on the file backend and on PostgreSQL

"""
text = once(text, "## Assumptions (checked in validation)\n", scenario + "## Assumptions (checked in validation)\n", path)
out("n31_test-spec.md", text)

# --- goal.md: scope row after the row of REQ-GTB-027
text = read(goal)
text = after_line(text, r"^\| REQ-GTB-027 \| in \| A-98 \|\n", "| REQ-GTB-028 | in | A-102 |\n", goal)
out("goal.md", text)

# --- plan.md
text = read(plan)
text = once(text, "Eleven small tasks (T-06 added with A-92, T-07 with A-93, T-08 and T-09 with A-98, T-10 after the fourth Verify run, T-11 with A-100)",
            "Twelve small tasks (T-06 added with A-92, T-07 with A-93, T-08 and T-09 with A-98, T-10 after the fourth Verify run, T-11 with A-100, T-12 with A-102)", plan)
text = after_line(text, r"^\| T-11 Findings of the fifth Verify run[^\n]*\n",
                  "| T-12 Size of a document (F-22) | REQ-GTB-028, REQ-SLY-015 | TC-GTB-029; real side of TC-IF-301-24; TC-SLY-014 (in `tests/test_storage.py`) | T-11; amendment A-102 (installed) |\n", plan)
task = """### T-12: Size of a document (F-22)
- Implements: REQ-GTB-028 (Graph tables) and REQ-SLY-015 (Storage layer): more than 100,000 values, counting a value once for every path that reaches it, is refused
- Tests to turn green: TC-GTB-029 (`tests/acceptance/test_graph_document_size.py`); the real side of TC-IF-301-24 (`test_a_record_with_too_many_values_is_a_schema_break_real`); new tests in `tests/test_storage.py` that fail first (unprotected; TC-SLY-014): a task document `{"text": "t", "numbers": [...]}` with 99,997 numbers and one with 99,998 numbers (100,000 and 100,001 values: the document, the text and the list count 3; documents of the tables other than graph tables are mappings) (the first is stored, the second refused as `StorageError` `invalid`, rule `schema`, detail `too large`), a data node whose value is a list of 99,995 and of 99,996 numbers for `graph_nodes` (stored / refused `schema_break`, `data`), and a document that names the same child twice on 30 levels is refused within one second for both kinds of table (the test runs `put` in a thread, so a hang cannot stall the suite); on the file backend, and on PostgreSQL through the shared `StorageBehaviour`. The T-11 test that calls `refuse_unstorable` on the 2**30-path document must now expect the refusal `too large` and still finish within a second
- Touches: `storage.py` (`_unstorable` counts the values with every path counted, memoising the count of each shared container and stopping at 100,001, so a shared structure is refused at once; the size check runs for every table, also for the graph tables whose depth check stays with `check_record`, so `check_record` never sees an expanded structure through `Storage.put`); `graph_tables.py` (`_too_deep` also counts the values and stops at 100,001, so `check_record` called directly, as the Workflow management does, refuses such a record as `schema_break` naming `data` at once; the order of the depth and size checks does not change the answer); `tests/test_storage.py`
- Must not touch: protected material, `contracts/` (A-102 changed IF-301 already), `storage_postgres.py`, `storage_files.py`, `storage_copy.py`
- Depends on: T-11; A-102 installed
- Done when: the listed tests are green and all other tests unchanged (the contract suites with no skip, the acceptance tests of the goal, TC-GTB-014 with N = 1000, `test_storage.py`, `test_storage_postgres.py` on a throwaway postgres:16, 500 node and 500 edge records within 500 ms, `test_doc_check` clean on the goal's test files)
- Notes: 100,000 values is about 190 times the largest stored document in the repository (529 values); the count includes the record or document itself, every object and list, and every scalar. A document nested deeper than 200 levels or containing itself is refused as before. F-18, F-13(a), F-07 and F-08 stay accepted. No new part, interface or dependency.

"""
text = once(text, "## Order and checks\n", task + "## Order and checks\n", plan)
text = once(text, "T-11 after T-10 and the install of A-100.", "T-11 after T-10 and the install of A-100; T-12 after T-11 and the install of A-102.", plan)
text = once(text, "eleven tasks of one session each, two nodes (N-3.2 in T-01 to T-03 and T-05 to T-10, N-3.1 in T-04, T-06, T-08, T-10 and T-11)",
            "twelve tasks of one session each, two nodes (N-3.2 in T-01 to T-03 and T-05 to T-10 and T-12, N-3.1 in T-04, T-06, T-08, T-10, T-11 and T-12)", plan)
text = after_line(text, r"^9\. After the fifth Verify run[^\n]*\n",
                  "10. After T-11 (2026-11-08): the owner decided to add a size limit of 100,000 values for every table (REQ-SLY-015) and for the record checks (REQ-GTB-028), A-102 and T-12 (F-22); "
                  "the plausibility ratings of the two requirements follow in A-103.\n", plan)
out("plan.md", text)

# --- contract
text = read(contract)
text = after_line(text, r"^- Input that cannot be checked \(REQ-GTB-027, F-09\)[^\n]*\n",
                  "- Size (REQ-GTB-028, F-22): a record with more than 100,000 values is `{\"rule\": \"schema_break\", \"detail\": \"data\"}`. A value is counted once for every path that reaches it "
                  "(a value reached twice counts twice); the record itself, every object, every list and every scalar count. The count stops at 100,001, so a record that shares sub-objects "
                  "(2**30 paths) is refused at once. Nothing raises, in `check_record` and in `to_object`.\n", contract)
text = after_line(text, r"^20\. Input that cannot be checked \(v2\)[^\n]*\n",
                  "21. Size (v2): a data node whose `value` is a list of 99,995 numbers (100,000 values with the record, its `id`, its `data` object, its `type` and the list) gives `None`; a list of 99,996 numbers gives "
                  "`{\"rule\": \"schema_break\", \"detail\": \"data\"}`; a record that names the same child twice on 30 levels gives the same refusal at once.\n", contract)
text = after_line(text, r"^15\. \*\*A-98 \(Verify finding F-09[^\n]*\n",
                  "16. **A-102 (Verify finding F-22, owner's decision of 2026-11-08):** a record with more than 100,000 values, counting a value once for every path, is `schema_break` naming `data`. "
                  "A record that shares sub-objects can have an exponential number of paths; the check made `check_record` run for minutes. 100,000 is about 190 times the largest stored document in the repository "
                  "(529 values). v2 is not merged yet, so this is part of v2.\n", contract)
text = once(text, "tables `context_nodes` and `context_edges`, input that cannot be checked | A-90 (D-188, D-262 to D-266), A-92, A-93, A-98 |",
            "tables `context_nodes` and `context_edges`, input that cannot be checked, a size limit of 100,000 values | A-90 (D-188, D-262 to D-266), A-92, A-93, A-98, A-102 |", contract)
text = once(text, "golden 5 to 20, `record_id`", "golden 5 to 21, `record_id`", contract)
out("contract.md", text)

# --- mock
text = read(mock)
text = once(text, "MAX_DEPTH = 200      # a record nested deeper than this is schema_break `data` (REQ-GTB-027)",
            "MAX_DEPTH = 200      # a record nested deeper than this is schema_break `data` (REQ-GTB-027)\nMAX_VALUES = 100000  # a record with more values (every path counted) is schema_break `data` (REQ-GTB-028)", mock)
old = '''def _too_deep(value):
    """True when the value is nested deeper than MAX_DEPTH levels (the record is level 1); iterative, so the check itself cannot hit the recursion limit."""
    stack = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        if depth > MAX_DEPTH:
            return True
'''
new = '''def _too_deep(value):
    """True when the value is nested deeper than MAX_DEPTH levels (the record is level 1) or has more than MAX_VALUES values (a value reached by two paths counts twice);
    iterative, so the check itself cannot hit the recursion limit, and it stops at MAX_VALUES + 1 values, so a record that shares sub-objects cannot make it exponential."""
    stack, seen = [(value, 1)], 0
    while stack:
        item, depth = stack.pop()
        seen += 1
        if depth > MAX_DEPTH or seen > MAX_VALUES:
            return True
'''
text = once(text, old, new, mock)
out("mock.py", text)

# --- contract suite: the case TC-IF-301-24 before the case of TC-IF-301-23, and the import
text = read(suite)
text = once(text, "import sys\nimport time\nimport unittest\n", "import sys\nimport threading\nimport time\nimport unittest\n", suite)
case = '''    @mark.req("IF-301", "REQ-GTB-028")
    @each_provider(IF, make=subject)
    def test_a_record_with_too_many_values_is_a_schema_break(self, tables):
        """TC-IF-301-24 golden 21: a record with more than 100 000 values (every path counted) is schema_break naming data, also a record that shares sub-objects (2**30 paths), at once.

        Example: a data node whose value is a list of 99 996 numbers -> {"rule": "schema_break", "detail": "data"}; 99 995 numbers -> None.
        """
        # Given: data nodes whose value is a list of 99 995 and of 99 996 numbers (the record, its id, its data object, its type and the list add 5 values: 100 000 and 100 001),
        # and a record that names the same child twice on 30 levels (31 levels deep, 2**30 paths)
        shared = 1
        for _ in range(30):
            shared = [shared, shared]
        answers = {}

        def check(name, record):
            """The answer of check_record, or a text when it did not finish in 5 s (a daemon thread, so a hang fails this test and does not stall the suite)."""
            thread = threading.Thread(target=lambda: answers.__setitem__(name, tables.check_record("graph_nodes", record)), daemon=True)
            thread.start()
            thread.join(5)
            return answers.get(name, "no answer within 5 s")
        # When/Then: the record at the limit is accepted, the one over it is refused naming data
        self.assertIsNone(check("at", node("d1", "data", value=[1] * 99995)))
        self.assertEqual(check("over", node("d1", "data", value=[1] * 99996)), {"rule": "schema_break", "detail": "data"})
        # And: the record with 2**30 paths is refused the same way within the time limit
        self.assertEqual(check("shared", node("d1", "data", value=shared)), {"rule": "schema_break", "detail": "data"})

'''
anchor = '''    @mark.req("IF-301", "REQ-GTB-027")
    @each_provider(IF, make=subject)
    def test_input_that_cannot_be_checked_is_a_schema_break(self, tables):
'''
text = once(text, anchor, case + anchor, suite)
out("suite.py", text)
PY
copy "$WORK/n32_requirements.md"      "$N32/requirements.md"
copy "$WORK/n32_test-spec.md"         "$N32/test-spec.md"
copy "$WORK/n32_test-requirements.md" "$N32/test-requirements.md"
copy "$WORK/n31_requirements.md"      "$N31/requirements.md"
copy "$WORK/n31_test-spec.md"         "$N31/test-spec.md"
copy "$WORK/goal.md"                  "$GOAL"
copy "$WORK/plan.md"                  "$PLAN"
copy "$WORK/contract.md"              "$CONTRACT"
copy "$WORK/mock.py"                  "$MOCK"
copy "$WORK/suite.py"                 "$SUITE"
copy specs/mia/amendments/A-102/test_graph_document_size.py tests/acceptance/test_graph_document_size.py
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== regenerate the requirement block of the model and check it"
    python3 -I tools/gen_node_requirements_model.py .
    bash tools/check_sysml.sh specs/mia/architecture.sysml | tail -3
    echo "== trace_check: errors about the new ids, and the total (the known baseline is 519: 517 and the two TC-SLY checks of A-100; TC-SLY-014 adds one of the same kind)"
    python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests > "$WORK/trace.txt" 2>&1 || true
    grep -E "GTB-02[89]|SLY-01[45]|IF-301-24" "$WORK/trace.txt" || echo none
    echo "total errors: $(grep -c '| ERROR |' "$WORK/trace.txt")"
    python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia 2>&1 | tail -2
    echo "== the checks (the _mock side and all old checks must pass; the real side of TC-IF-301-24 and TC-GTB-029 are red until T-12)"
    python tests/acceptance/contract/test_if_301_v2_graph_tables.py -k _mock 2>&1 | tail -1
    python tests/acceptance/test_graph_records.py 2>&1 | tail -1
    python tests/acceptance/test_graph_document_size.py 2>&1 | tail -1 || true
fi
