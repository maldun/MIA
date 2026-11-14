#!/usr/bin/env bash
# Amendment A-100 (G-V2.STORE Verify, F-19 and F-20 of the fifth run, owner's decision of 2026-11-08): the Storage layer refuses a document that is nested
# too deep or contains itself, for every table.
#   F-19: after T-10 `Storage.put` of an object that contains itself never returns (it was a RecursionError before); F-20: for tables that are not graph
#   tables the depth limit is the recursion limit of the interpreter (about 496 levels, less on a deep stack). Decided: one limit of 200 levels for all tables.
#   REQ-SLY-013 and REQ-SLY-014 (new in N-3.1, Draft until the owner has reviewed and rated them), TC-SLY-012 and TC-SLY-013 (in tests/test_storage.py,
#   unprotected, written in T-11), task T-11 (these two fixes and F-21, the missing Given/When/Then comment).
# Note: specs/mia/amendments/A-100-note.md
# Files that change (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found
# exactly once, so a second --do changes nothing):
#   N-3.1 requirements.md, test-spec.md                        goals/G-V2.STORE/plan.md (T-11)
# No protected file changes. After --do: the generated requirement block of architecture.sysml is regenerated and checked.
# THE OWNER REVIEWS REQ-SLY-013 AND REQ-SLY-014 AND RATES THEM (plausibility.yaml: amendment A-101 after the ratings), then installs.
#   bash tools/apply_amendment_a100.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a100.sh --do      install, regenerate the model, run the checks; commit afterwards as "plan: A-100 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
NODE=specs/mia/nodes/N-3-database/nodes/N-3.1-storage-layer
PLAN=specs/mia/goals/G-V2.STORE/plan.md
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$NODE" "$PLAN" "$WORK" <<'PY'
import os
import re
import sys
node, plan, work = sys.argv[1:4]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def once(text, old, new, where):
    """Replace `old` by `new` when `old` occurs exactly once. The edit counts as done when `new` is in the text already (checked FIRST)."""
    if new in text:
        return text
    if text.count(old) == 1:
        return text.replace(old, new, 1)
    sys.exit("%s: anchor not found exactly once (%s); install A-100 by hand" % (where, old[:70]))


def after_line(text, pattern, addition, where):
    if addition in text:
        return text
    found = list(re.finditer(pattern, text, re.M))
    if len(found) != 1:
        sys.exit("%s: the line %r is not found exactly once; install A-100 by hand" % (where, pattern[:60]))
    end = found[0].end()
    return text[:end] + addition + text[end:]


# --- N-3.1 requirements.md
path = os.path.join(node, "requirements.md")
text = read(path)
if "### REQ-SLY-013 " not in text:
    if text.count("### REQ-SLY-012 ") != 1 or not text.rstrip().endswith("- History: –"):
        sys.exit("%s: REQ-SLY-012 is not the last block; install A-100 by hand" % path)
    text = text.rstrip("\n") + """

### REQ-SLY-013 – Depth of a document
- Level: low   Subject: Persistence
- Text: If a document that is put is nested deeper than 200 levels, then the Storage layer shall refuse it as invalid.
- Rationale: refines REQ-SLY-004 and REQ-GTB-027; one limit for every table, so that the refusal does not depend on the recursion limit of the interpreter or on how deep the caller is in the call stack (F-20 of the fifth Verify run of G-V2.STORE, A-100); the deepest real document in library, skills and eval has 19 levels
- Parent: REQ-SLY-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16: a document nested 200 levels (the document is level 1) is stored, one nested 201, 600 and 990 levels is refused as StorageError `invalid` and nothing is stored, for a graph table (rule `schema_break`, detail `data`) and for another table (rule `schema`, detail `nested too deep`), on the file backend and on PostgreSQL (exact)
- Verified by: TC-SLY-012
- Status: Draft
- History: G-V2.STORE Verify F-20, 2026-11-08, new (A-100, proposed)

### REQ-SLY-014 – A document that contains itself
- Level: low   Subject: Persistence
- Text: If a document that is put contains itself, then the Storage layer shall refuse it as invalid within one second.
- Rationale: refines REQ-SLY-004; a hang is worse than the RecursionError it replaced (F-19 of the fifth Verify run of G-V2.STORE, A-100); only Python callers can build such a document, JSON has no cycles
- Parent: REQ-SLY-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16: a list or dict that contains itself, also twice in one dict, is refused as StorageError `invalid` within one second for a graph table and for another table, on the file backend and on PostgreSQL, and nothing is stored (exact, time limit 1 s)
- Verified by: TC-SLY-013
- Status: Draft
- History: G-V2.STORE Verify F-19, 2026-11-08, new (A-100, proposed)
"""
out("requirements.md", text)

# --- N-3.1 test-spec.md: two rows after TC-SLY-011, two scenarios before the assumptions
path = os.path.join(node, "test-spec.md")
text = read(path)
rows = """| TC-SLY-012 | REQ-SLY-013 | Component | 1 | a document nested 200, 201, 600 and 990 levels, for `graph_nodes` and for another table | the 200-level one is stored as version 1; the others are refused as invalid and nothing is stored | exact |
| TC-SLY-013 | REQ-SLY-014 | Component | 1 | a list that contains itself, a dict that contains itself twice, as the value of a graph node and as a document of another table | each is refused as invalid within one second and nothing is stored | exact, 1 s |
"""
text = after_line(text, r"^\| TC-SLY-011 \|[^\n]*\n", rows, path)
scenarios = """### TC-SLY-012 – depth of a document
- Verifies: REQ-SLY-013
- Given: a document nested 200 levels (the document is level 1) and others nested 201, 600 and 990 levels, once as the value of a graph node and once as a document of a table that is not a graph table
- When: each is put
- Then: the 200-level document is stored as version 1; the others are refused as invalid
- And: the refusals store nothing; graph tables name `schema_break` and `data`, other tables `schema` and `nested too deep`; the same on the file backend and on PostgreSQL

### TC-SLY-013 – a document that contains itself
- Verifies: REQ-SLY-014
- Given: a list that contains itself and a dict that contains itself twice, once as the value of a graph node and once as a document of another table
- When: each is put, with a time limit of one second
- Then: each is refused as invalid within the limit
- And: nothing is stored; the same on the file backend and on PostgreSQL

"""
text = once(text, "## Assumptions (checked in validation)\n", scenarios + "## Assumptions (checked in validation)\n", path)
out("test-spec.md", text)

# --- plan.md
text = read(plan)
text = once(text, "Ten small tasks (T-06 added with A-92, T-07 with A-93, T-08 and T-09 with A-98, T-10 after the fourth Verify run)",
            "Eleven small tasks (T-06 added with A-92, T-07 with A-93, T-08 and T-09 with A-98, T-10 after the fourth Verify run, T-11 with A-100)", plan)
text = after_line(text, r"^\| T-10 Findings of the fourth Verify run[^\n]*\n",
                  "| T-11 Findings of the fifth Verify run (F-19, F-20, F-21) | REQ-SLY-013, REQ-SLY-014; F-21 | TC-SLY-012, TC-SLY-013 (in `tests/test_storage.py`); `test_doc_check` clean | T-10; amendment A-100 (installed) |\n", plan)
task = """### T-11: Findings of the fifth Verify run (F-19, F-20, F-21)
- Implements: REQ-SLY-013 (one depth limit of 200 levels for every table, F-20) and REQ-SLY-014 (a document that contains itself is refused within one second, F-19); F-21 is a missing comment line
- Tests to turn green: new tests in `tests/test_storage.py` that fail first (unprotected; TC-SLY-012 and TC-SLY-013): a document nested 200 levels is stored as version 1, nested 201, 600 and 990 levels is refused as `StorageError` `invalid` and nothing is stored, for `graph_nodes` (rule `schema_break`, detail `data`) and for a table that is not a graph table (rule `schema`, detail `nested too deep`); a list that contains itself, a dict that contains itself twice (`d["a"] = d; d["b"] = d`) and the same as the value of a graph node are refused as `StorageError` within one second (the test runs `put` in a thread and fails when it does not finish in time, so a hang cannot stall the suite); on the file backend, and on PostgreSQL in `tests/test_storage_postgres.py` through the shared `StorageBehaviour`. F-21: the Given/When/Then comments of `test_a_local_reference_still_works` in `tests/test_graph_record_checks.py`, so `test_doc_check` is clean
- Touches: `storage.py` (`_unstorable` counts the depth with the document as level 1 and refuses more than 200 levels for every table; it keeps the containers on the current path and refuses a container that contains itself, walking each shared container once so that a document that names the same object many times cannot make the check exponential; the existing `RecursionError` catches in `validate` and `put` can stay as a last guard); `tests/test_storage.py`, `tests/test_storage_postgres.py`, `tests/test_graph_record_checks.py`
- Must not touch: protected material, `graph_tables.py` (its 200-level rule is REQ-GTB-027 and stays), `contracts/`, `storage_postgres.py`, `storage_files.py`, `storage_copy.py`
- Depends on: T-10; A-100 installed
- Done when: the listed tests are green and all other tests unchanged (the contract suites with no skip, the acceptance tests of the goal, TC-GTB-014 with N = 1000, `test_storage.py`, `test_storage_postgres.py` on a throwaway postgres:16, 500 node and 500 edge records within 500 ms), `test_doc_check` clean on the goal's test files
- Notes: the read side (`Storage.get` of a stored document nested about 480 levels on a deep call stack) is older behaviour and not part of this task; F-13(a), F-18, F-07 and F-08 stay accepted. No new part, interface or dependency.

"""
text = once(text, "## Order and checks\n", task + "## Order and checks\n", plan)
text = once(text, "; T-10 after T-09.", "; T-10 after T-09; T-11 after T-10 and the install of A-100.", plan)
text = once(text, "ten tasks of one session each, two nodes (N-3.2 in T-01 to T-03 and T-05 to T-10, N-3.1 in T-04, T-06, T-08 and T-10)",
            "eleven tasks of one session each, two nodes (N-3.2 in T-01 to T-03 and T-05 to T-10, N-3.1 in T-04, T-06, T-08, T-10 and T-11)", plan)
text = after_line(text, r"^8\. After the fourth Verify run[^\n]*\n",
                  "9. After the fifth Verify run (2026-11-08): the owner decided to add one Storage requirement for all tables (REQ-SLY-013, depth 200) and one for a document that contains itself (REQ-SLY-014, F-19), "
                  "A-100 and T-11; the plausibility ratings of the two requirements follow in A-101.\n", plan)
out("plan.md", text)
PY
copy "$WORK/requirements.md" "$NODE/requirements.md"
copy "$WORK/test-spec.md"    "$NODE/test-spec.md"
copy "$WORK/plan.md"         "$PLAN"
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== regenerate the requirement block of the model and check it"
    python3 -I tools/gen_node_requirements_model.py .
    bash tools/check_sysml.sh specs/mia/architecture.sysml | tail -3
    echo "== trace_check: errors about the new ids (the tests of TC-SLY-012 and 013 are written in T-11), and the total (the known baseline is 517)"
    python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests > "$WORK/trace.txt" 2>&1 || true
    grep -E "SLY-01[234]" "$WORK/trace.txt" || echo none
    echo "total errors: $(grep -c '| ERROR |' "$WORK/trace.txt")"
    python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia 2>&1 | tail -2
fi
