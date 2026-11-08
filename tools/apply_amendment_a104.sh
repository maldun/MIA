#!/usr/bin/env bash
# Amendment A-104 (G-V2.STORE, F-23 of the sixth Verify run, owner's decision of 2026-11-08): what a level is, and task T-13 (F-23, F-24, F-25).
#   F-23: the protected mock counts a scalar as a level (since A-98) and the real graph code does too, but the Storage layer counted containers only, so a
#   scalar in the 200th object was stored for `workflows` and refused for graph tables. Decided: a scalar counts as a level, everywhere. The wording of REQ-GTB-027
#   and REQ-SLY-013 (acceptance criteria) and of IF-301 says it; no requirement text changes, no protected test or mock changes.
#   T-13 (code, in plan.md): F-23 the Storage walk counts a scalar as a level; F-24 the Graph tables treat tuples like lists; F-25 put and get no longer depend
#   on the depth of the caller's stack (decided: fix now).
# Note: specs/mia/amendments/A-104-note.md
# Files that change (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found
# exactly once, so a second --do changes nothing):
#   N-3.2 requirements.md (acceptance criterion of REQ-GTB-027)   N-3.1 requirements.md (acceptance criterion of REQ-SLY-013)
#   contracts/IF-301-graph-tables.md (what a level is)             goals/G-V2.STORE/plan.md (T-13)
# No protected test, mock or helper changes. After --do: the generated requirement block of architecture.sysml is regenerated and checked.
# THE OWNER REVIEWS THE TWO CHANGED ACCEPTANCE CRITERIA (REQ-GTB-027, REQ-SLY-013 come back in req_review), then installs.
#   bash tools/apply_amendment_a104.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a104.sh --do      install, regenerate the model, run the checks; commit afterwards as "plan: A-104 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
N32=specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs
N31=specs/mia/nodes/N-3-database/nodes/N-3.1-storage-layer
PLAN=specs/mia/goals/G-V2.STORE/plan.md
CONTRACT=contracts/IF-301-graph-tables.md
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$N32" "$N31" "$PLAN" "$CONTRACT" "$WORK" <<'PY'
import os
import re
import sys
n32, n31, plan, contract, work = sys.argv[1:6]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def once(text, old, new, where):
    """Replace `old` by `new` when `old` occurs exactly once. The edit counts as done when `new` is in the text already (checked FIRST)."""
    if new in text:
        return text
    if text.count(old) == 1:
        return text.replace(old, new, 1)
    sys.exit("%s: anchor not found exactly once (%s); install A-104 by hand" % (where, old[:70]))


def after_line(text, pattern, addition, where):
    if addition in text:
        return text
    found = list(re.finditer(pattern, text, re.M))
    if len(found) != 1:
        sys.exit("%s: the line %r is not found exactly once; install A-104 by hand" % (where, pattern[:60]))
    end = found[0].end()
    return text[:end] + addition + text[end:]


# --- REQ-GTB-027: the acceptance criterion says what a level is
path = os.path.join(n32, "requirements.md")
text = read(path)
text = once(text, "a data node whose value is nested 300 levels is refused naming `data`, one nested 150 levels is accepted;",
            "a data node whose deepest value is at level 300 is refused naming `data`, one at level 150 or exactly at level 200 is accepted, one at level 201 is refused (a level is the record, an object, a list or a scalar: "
            "the record is level 1 and every value below it is one level deeper than its parent, so a scalar in the 200th object is level 201);", path)
text = once(text, "- History: G-V2.STORE Verify F-02/F-09, 2026-11-08, new (A-98, proposed)\n\n### REQ-GTB-028",
            "- History: G-V2.STORE Verify F-02/F-09, 2026-11-08, new (A-98, proposed); 2026-11-08 the acceptance criterion says what a level is (F-23, A-104)\n\n### REQ-GTB-028", path) \
    if "### REQ-GTB-028" in text and text.count("- History: G-V2.STORE Verify F-02/F-09, 2026-11-08, new (A-98, proposed)\n\n### REQ-GTB-028") == 1 else text
out("n32_requirements.md", text)

# --- REQ-SLY-013: the same
path = os.path.join(n31, "requirements.md")
text = read(path)
text = once(text, "a document nested 200 levels (the document is level 1) is stored, one nested 201, 600 and 990 levels is refused as",
            "a document whose deepest value (an object, a list or a scalar; the document is level 1 and every value below it is one level deeper than its parent) is at level 200 is stored, "
            "one whose deepest value is at level 201, 600 or 990 is refused as", path)
out("n31_requirements.md", text)

# --- contract: what a level is
text = read(contract)
text = after_line(text, r"^- Input that cannot be checked \(REQ-GTB-027, F-09\)[^\n]*\n",
                  "- What a level is (F-23, A-104): levels are counted down the path from the record. The record is level 1 and every value below it, an object, a list or a scalar, is one level deeper than its parent, "
                  "so a scalar inside the 200th object is level 201 and refused, an empty object at level 200 is accepted. The Storage layer counts a document the same way (REQ-SLY-013). "
                  "A tuple is counted like a list (F-24).\n", contract)
out("contract.md", text)

# --- plan.md: task T-13
text = read(plan)
text = once(text, "Twelve small tasks (T-06 added with A-92, T-07 with A-93, T-08 and T-09 with A-98, T-10 after the fourth Verify run, T-11 with A-100, T-12 with A-102)",
            "Thirteen small tasks (T-06 added with A-92, T-07 with A-93, T-08 and T-09 with A-98, T-10 after the fourth Verify run, T-11 with A-100, T-12 with A-102, T-13 with A-104)", plan)
text = after_line(text, r"^\| T-12 Size of a document[^\n]*\n",
                  "| T-13 Findings of the sixth Verify run (F-23, F-24, F-25) | REQ-GTB-027 and REQ-SLY-013 (what a level is); robustness of the Graph tables against tuples; put and get independent of the caller's stack depth | new unit tests that fail first | T-12; amendment A-104 (installed) |\n", plan)
task = """### T-13: Findings of the sixth Verify run (F-23, F-24, F-25)
- Implements: F-23 the acceptance criteria of REQ-GTB-027 and REQ-SLY-013 (a scalar is a level, in the Storage layer too); F-24 tuples in the Graph tables; F-25 `put` and `get` of a legal document do not depend on how deep the caller is in the call stack
- Tests to turn green: new unit tests that fail first (unprotected). F-23, in `tests/test_storage.py` and `tests/test_graph_record_checks.py`: a document or record whose deepest value is at level 200 is stored or accepted, whether that value is an empty object, an empty list or a scalar, and one whose deepest value is at level 201 is refused, for a document table (rule `schema`, detail `nested too deep`), for `graph_nodes` through `Storage.put` (`schema_break`, `data`) and for `check_record` directly (this kills the surviving mutant G6 of the sixth run). F-24, in `tests/test_graph_record_checks.py`: a record that contains itself through a tuple, a DAG of tuples 60 levels deep (the same child twice per level) and a tuple nested 5000 deep are refused as `schema_break` naming `data` by `check_record` and by `to_object`, each within one second (a daemon thread with a time limit, so a hang fails the test); a tuple holding a NaN is named like a list holding one. F-25, in `tests/test_storage.py`: a document whose deepest value is at level 200 is stored and read back when `put` and `get` are called from a call stack 700 frames deep (build the stack with a recursive helper), on the file backend, and on PostgreSQL through the shared `StorageBehaviour`; `put` never raises anything but `StorageError`
- Touches: `storage.py` (`_unstorable` counts a scalar as a level; the copy that `put` and `get` make of a document does not use the recursive `copy.deepcopy`, or the work is arranged so that the number of Python frames per level is small and fixed, so a 200-level document needs far fewer than 300 frames; find with a small experiment which calls dominate: deepcopy, the JSON encoder, the validators); `graph_tables.py` (`_too_deep`, `_non_finite_path` and the copy in `to_object` treat a tuple like a list); the three test files named above
- Must not touch: protected material, `contracts/`, `storage_postgres.py`, `storage_files.py`, `storage_copy.py`; if the experiment shows that the backends' own serialisation is what limits the depth, stop and report instead of editing them
- Depends on: T-12; amendment A-104 installed
- Done when: the listed tests are green and all other tests unchanged (the contract suites with no skip, the acceptance tests of the goal, TC-GTB-014 with N = 1000, `test_storage.py`, `test_storage_postgres.py` on a throwaway postgres:16, 500 node and 500 edge records within 500 ms, the 2**30-path and 100,001-value refusals still within 0.1 s), `test_doc_check` clean on the new tests
- Notes: a tuple cannot come from JSON, so F-24 concerns Python callers only; F-18 (non-string keys), F-13(a), F-07 and F-08 stay accepted. No new part, interface or dependency.

"""
text = once(text, "## Order and checks\n", task + "## Order and checks\n", plan)
text = once(text, "T-12 after T-11 and the install of A-102.", "T-12 after T-11 and the install of A-102; T-13 after T-12 and the install of A-104.", plan)
text = once(text, "twelve tasks of one session each, two nodes (N-3.2 in T-01 to T-03 and T-05 to T-10 and T-12, N-3.1 in T-04, T-06, T-08, T-10, T-11 and T-12)",
            "thirteen tasks of one session each, two nodes (N-3.2 in T-01 to T-03, T-05 to T-10, T-12 and T-13, N-3.1 in T-04, T-06, T-08, T-10 to T-13)", plan)
text = after_line(text, r"^10\. After T-11 \(2026-11-08\)[^\n]*\n",
                  "11. After the sixth Verify run (2026-11-08): the owner decided that a scalar counts as a level everywhere (F-23, wording in A-104, code in T-13), and to fix F-24 (tuples) and F-25 "
                  "(independence from the caller's stack depth) now in T-13.\n", plan)
out("plan.md", text)
PY
copy "$WORK/n32_requirements.md" "$N32/requirements.md"
copy "$WORK/n31_requirements.md" "$N31/requirements.md"
copy "$WORK/contract.md"         "$CONTRACT"
copy "$WORK/plan.md"             "$PLAN"
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== regenerate the requirement block of the model and check it"
    python3 -I tools/gen_node_requirements_model.py .
    bash tools/check_sysml.sh specs/mia/architecture.sysml | tail -3
    echo "== trace_check total (the known baseline is 520) and goal_check"
    python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests > "$WORK/trace.txt" 2>&1 || true
    echo "total errors: $(grep -c '| ERROR |' "$WORK/trace.txt")"
    python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia 2>&1 | tail -2
fi
