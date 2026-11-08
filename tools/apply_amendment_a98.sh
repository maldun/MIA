#!/usr/bin/env bash
# Amendment A-98 (G-V2.STORE Verify, F-02 and F-09, owner's decisions of 2026-11-08): context graph tables, and the rule for input that cannot be checked.
#   F-02: a context-graph node cannot be stored through the real Storage layer (put has no `categories`). Decided: separate tables `context_nodes` and
#   `context_edges` (six record tables); edges and headers of a context graph resolve inside the context tables; the Storage layer checks the shape only,
#   the caller checks the categories before it writes; IF-102 does not change.
#   F-09: a record nested deeper than 200 levels, and a category whose schema is not valid, are `schema_break` (detail `data`, detail `type`), not `record_identity`.
#   REQ-GTB-023 to REQ-GTB-027 (new, Draft until the owner has reviewed them), TC-GTB-024 to TC-GTB-028, TC-IF-301-22 and -23, IF-301 v2 (v2 is not merged,
#   so it stays v2), tasks T-08 (context tables) and T-09 (small fixes F-03, F-06, F-09, F-11, F-13b).
# Note: specs/mia/amendments/A-98-note.md
# Files that change (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found
# exactly once, so a second --do changes nothing, F-04):
#   N-3.2 requirements.md, test-spec.md, test-requirements.md (TR-GTB-001 applies to TC-GTB-024..028)   goal.md of G-V2.STORE (scope rows)   plan.md (T-08, T-09)
#   contracts/IF-301-graph-tables.md                                  section "Context graph tables", golden 17 to 20, decisions 14 and 15, version history
#   tests/helpers/mocks/if_301_graph_tables_v2.py                     six tables, context checks, depth cap, invalid category schema
#   tests/helpers/graph_store_standin.py                              six tables, `stored` also holds the context records
#   tests/acceptance/contract/test_if_301_v2_graph_tables.py          six tables in TC-IF-301-05; cases TC-IF-301-22 and -23
#   tests/acceptance/test_graph_records.py, test_graph_record_identity.py   the list of record tables has six names
#   tests/acceptance/test_graph_context_tables.py                     new, TC-GTB-024 to 028 (staged in specs/mia/amendments/A-98/)
# After --do: the generated requirement block of architecture.sysml is regenerated and checked.
# Independent of A-96, A-97 (other files) and of the order with A-93, A-94: the anchors work in the installed state of A-93.
# THE OWNER REVIEWS REQ-GTB-023..027 FIRST (req_review.py, rating in plausibility.yaml), then installs.
#   bash tools/apply_amendment_a98.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a98.sh --do      install, regenerate the model, run the checks; commit afterwards as "plan: A-98 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
NODE=specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs
GOAL=specs/mia/goals/G-V2.STORE/goal.md
PLAN=specs/mia/goals/G-V2.STORE/plan.md
CONTRACT=contracts/IF-301-graph-tables.md
MOCK=tests/helpers/mocks/if_301_graph_tables_v2.py
STANDIN=tests/helpers/graph_store_standin.py
SUITE=tests/acceptance/contract/test_if_301_v2_graph_tables.py
RECORDS=tests/acceptance/test_graph_records.py
IDENTITY=tests/acceptance/test_graph_record_identity.py
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$NODE" "$GOAL" "$PLAN" "$CONTRACT" "$MOCK" "$STANDIN" "$SUITE" "$RECORDS" "$IDENTITY" "$WORK" <<'PY'
import os
import re
import sys
node, goal, plan, contract, mock, standin, suite, records, identity, work = sys.argv[1:11]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def once(text, old, new, where):
    """Replace `old` by `new` when `old` occurs exactly once. The edit counts as done when `new` is in the text already (checked FIRST: `new`
    often still contains `old`); anything else is refused."""
    if new in text:
        return text
    if text.count(old) == 1:
        return text.replace(old, new, 1)
    sys.exit("%s: anchor not found exactly once (%s); install A-98 by hand" % (where, old[:70]))


def after_line(text, pattern, addition, where, last=False):
    """Insert `addition` (full lines) after the line that matches `pattern`; done when `addition` is in the text; `last` takes the last match."""
    if addition in text:
        return text
    found = list(re.finditer(pattern, text, re.M))
    if (len(found) != 1 and not last) or not found:
        sys.exit("%s: the line %r is not found exactly once; install A-98 by hand" % (where, pattern[:60]))
    end = found[-1].end()
    return text[:end] + addition + text[end:]


# --- requirements.md: REQ-GTB-023 to 027 after REQ-GTB-022, a group CX, REQ-GTB-027 in the group TY
path = os.path.join(node, "requirements.md")
text = read(path)
BLOCKS = [
    ("REQ-GTB-023", "Context graph tables", "CX",
     "The Graph tables shall list `context_nodes` and `context_edges` as versioned tables whose records are never deleted.",
     "refines FR-40 and FR-41; a context graph is stored in tables of its own because its node types come from the context graph itself, which the Storage layer cannot know (F-02, decided 2026-11-07/08, A-98)",
     "AC-31: the definitions of the Graph tables list six record tables; a context node written twice has the versions 1 and 2; a delete of a context node or edge is refused as immutable (exact)",
     "TC-GTB-024"),
    ("REQ-GTB-024", "Context record shape", "CX",
     "If a context node lacks a text ID, a JSON object or a text type, or a context edge lacks a text end, then the Graph tables shall refuse the record naming that field.",
     "refines FR-40; the Storage layer checks the shape only, the caller checks the categories before it writes (decision 14 of IF-301) (A-98)",
     "AC-31: a context node with data {} is refused naming `type`, one without data naming `data`, an edge without `to` naming `to`; the same records with the field are accepted (exact)",
     "TC-GTB-025"),
    ("REQ-GTB-025", "Context edge ends", "CX",
     "If a context edge names an end that is not a stored context node, then the Graph tables shall refuse the edge as `unknown_endpoint` naming that end.",
     "refines FR-40 and REQ-GTB-020; the ends of a context edge are looked up in `context_nodes` only (A-98)",
     "AC-31: an edge from c1 to c9 with only c1 stored is refused naming `c9`, also when a workflow node has the ID c9; an edge between stored context nodes is accepted (exact)",
     "TC-GTB-026"),
    ("REQ-GTB-026", "Context header members", "CX",
     "If a graph header of kind context names a member that is not stored in `context_nodes` or `context_edges` at that version, then the Graph tables shall refuse the header as `unknown_member` naming the member.",
     "refines FR-40 and REQ-GTB-019; a header of kind workflow still looks in `graph_nodes` and `graph_edges` (A-98)",
     "AC-31: a context header naming c9 with only c1 stored is refused naming `c9`; a workflow header naming the context node c1 is refused naming `c1`; a context header naming c1 is accepted (exact)",
     "TC-GTB-027"),
    ("REQ-GTB-027", "Input that cannot be checked", "TY",
     "If a record is nested deeper than 200 levels or its category schema is not valid, then the Graph tables shall refuse it as `schema_break` naming the field.",
     "refines FR-40 and REQ-GTB-011; before, such input gave `record_identity` with the detail `record`, which names the wrong rule (F-09, A-98); 200 levels is a fixed limit so that mock and real code agree",
     "AC-31: a data node whose value is nested 300 levels is refused naming `data`, one nested 150 levels is accepted; a category whose schema is {\"type\": 5} is refused naming `type`; nothing raises (exact)",
     "TC-GTB-028"),
]
if "### REQ-GTB-023 " not in text:
    if text.count("### REQ-GTB-022 ") != 1 or not text.rstrip().endswith("(A-93, proposed)"):
        sys.exit("%s: REQ-GTB-022 is not the last block; install A-98 by hand" % path)
    for rid, title, group, req_text, why, ac, check in BLOCKS:
        text = text.rstrip("\n") + """

### %s – %s
- Level: low   Subject: Persistence
- Text: %s
- Rationale: %s
- Parent: FR-40
- Group: %s
- Priority: Must
- Verification method: Test
- Acceptance criterion: %s
- Verified by: %s
- Status: Draft
- History: G-V2.STORE Verify F-02/F-09, 2026-11-08, new (A-98, proposed)
""" % (rid, title, req_text, why, group, ac, check)
text = after_line(text, r"^\| 5 \| HD \|[^\n]*\n",
                  "| 6 | CX | Context graph tables: where the nodes and edges of a context graph are kept and what is checked (FR-40, FR-41) | REQ-GTB-023, REQ-GTB-024, REQ-GTB-025, REQ-GTB-026 |\n", path)
text = once(text, "REQ-GTB-012, REQ-GTB-022 |", "REQ-GTB-012, REQ-GTB-022, REQ-GTB-027 |", path)
out("requirements.md", text)

# --- test-spec.md: five rows after TC-GTB-023, five scenarios before TC-GTB-015
path = os.path.join(node, "test-spec.md")
text = read(path)
rows = """| TC-GTB-024 | REQ-GTB-023 | Unit | 1 | the definitions of the Graph tables; a context node written twice; a delete of a context node and of a context edge | six record tables are listed; the versions are 1 and 2; both deletes are refused as immutable | exact |
| TC-GTB-025 | REQ-GTB-024 | Unit | 1 | a context node without type, without a JSON object, without ID; a context edge without an end; the same records complete | each broken record is refused naming the field; the complete ones are accepted | exact |
| TC-GTB-026 | REQ-GTB-025 | Unit | 1 | a context edge to a stored context node, to one that is not stored, and to the ID of a stored workflow node | the first is accepted; the others are refused naming the end | exact |
| TC-GTB-027 | REQ-GTB-026 | Unit | 1 | a header of kind context naming a stored and a missing context node; a workflow header naming a context node | the first is accepted; the others are refused as unknown_member naming the member | exact |
| TC-GTB-028 | REQ-GTB-027 | Unit | 1 | a data node nested 300 and 150 levels deep; a category whose schema is not valid | the deep one is refused naming `data`, the other accepted; the category is refused naming `type`; no exception | exact |
"""
text = after_line(text, r"^\| TC-GTB-023 \|[^\n]*\n", rows, path)
scenarios = """### TC-GTB-024 – The context tables are versioned and never deleted
- Verifies: REQ-GTB-023
- Given: the definitions of the Graph tables and an empty store
- When: a context node is written twice, a context edge once, and a delete of each is tried
- Then: six record tables are listed, the context node has the versions 1 and 2, the edge version 1
- And: both deletes are refused as immutable and the records stay

### TC-GTB-025 – A context record of a bad shape is refused
- Verifies: REQ-GTB-024
- Given: a context node with data `{}`, one with a number as type, one without data, one with an empty ID, and a context edge without `to` and one without data
- When: each is written without categories
- Then: each write is refused naming the broken field (`type`, `type`, `data`, `id`, `to`, `data`) and stores nothing
- And: the same records complete are accepted (the twins differ only in the broken rule)

### TC-GTB-026 – A context edge names stored context nodes
- Verifies: REQ-GTB-025
- Given: a stored context node `c1` and a stored workflow node `n9`
- When: a context edge from `c1` to `c9`, one from `c1` to `n9`, and one from `c1` to `c1` are written
- Then: the first two are refused as `unknown_endpoint` naming `c9` and `n9`
- And: the third is accepted

### TC-GTB-027 – A context header names stored context members
- Verifies: REQ-GTB-026
- Given: a stored context node `c1`
- When: a header of kind context naming `c9`, a header of kind workflow naming `c1`, and a header of kind context naming `c1` are written
- Then: the first two are refused as `unknown_member` naming `c9` and `c1`
- And: the third is accepted

### TC-GTB-028 – Input that cannot be checked is a schema break
- Verifies: REQ-GTB-027
- Given: a data node whose value is nested 300 levels, one nested 150 levels, and a category whose schema is `{"type": 5}`
- When: each is checked, and the deep node is also rebuilt with `to_object`
- Then: the 300-level node is refused as `schema_break` naming `data`, in the check and in the rebuild, without an exception; the category is refused as `schema_break` naming `type`
- And: the 150-level node is accepted

"""
text = once(text, "### TC-GTB-015 – The document form still works\n", scenarios + "### TC-GTB-015 – The document form still works\n", path)
out("test-spec.md", text)

# --- test-requirements.md: TR-GTB-001 applies to TC-GTB-024..028
path = os.path.join(node, "test-requirements.md")
text = read(path)
m = re.search(r"^### TR-GTB-001 [^\n]*\n(?:(?!^### ).*\n)*", text, re.M)
if not m:
    sys.exit("%s: TR-GTB-001 is not found; install A-98 by hand" % path)
block = m.group(0)
if "TC-GTB-028" not in block:
    new = re.sub(r"^(- Applies to: [^\n]*TC-GTB-023)\n", r"\1, TC-GTB-024, TC-GTB-025, TC-GTB-026, TC-GTB-027, TC-GTB-028\n", block, count=1, flags=re.M)
    if new == block:
        sys.exit("%s: the Applies-to line of TR-GTB-001 does not end with TC-GTB-023; install A-98 by hand" % path)
    text = text.replace(block, new, 1)
out("test-requirements.md", text)

# --- goal.md: scope rows after the last row of REQ-GTB-022
text = read(goal)
text = after_line(text, r"^\| REQ-GTB-022 \| in \| A-93 \|\n",
                  "".join("| REQ-GTB-0%d | in | A-98 |\n" % n for n in range(23, 28)), goal, last=True)
out("goal.md", text)

# --- plan.md
text = read(plan)
text = once(text, "Seven small tasks (T-06 added with A-92, T-07 with A-93)", "Nine small tasks (T-06 added with A-92, T-07 with A-93, T-08 and T-09 with A-98)", plan)
text = after_line(text, r"^\| T-07 Fixed fields of a node[^\n]*\n",
                  "| T-08 Context graph tables | REQ-GTB-023, 024, 025, 026 | TC-GTB-024, 025, 026, 027; real side of TC-IF-301-05 (six tables) and TC-IF-301-22; new unit tests of the Storage layer; the six-table assertions of `test_graph_records.py` and `test_graph_record_identity.py` | T-07; amendment A-98 (installed) |\n"
                  "| T-09 Small fixes of the record checks | REQ-GTB-027 (F-09); robustness of REQ-GTB-011 and REQ-GTB-022 (F-03, F-11); tests F-06, F-13b | TC-GTB-028; real side of TC-IF-301-23; new unit tests | T-08; amendment A-98 (installed) |\n", plan)
tasks = """### T-08: Context graph tables
- Implements: REQ-GTB-023, REQ-GTB-024, REQ-GTB-025, REQ-GTB-026 (A-98, F-02)
- Tests to turn green: TC-GTB-024 to TC-GTB-027 (`tests/acceptance/test_graph_context_tables.py`); the real side of TC-IF-301-05 (six record tables) and of TC-IF-301-22; new unit tests in `tests/test_storage.py` that repeat TC-GTB-024 to 027 on `Storage`, on the file backend and, where `tests/test_storage_postgres.py` runs, on PostgreSQL (red first)
- Touches: `graph_tables.py` (`RECORD_TABLES` gets `context_nodes` and `context_edges`; `_check` has a branch for them: shape, with `categories` the type and schema of a node, the ends of an edge against `stored["context_nodes"]`; a header of kind context looks its members up in `stored["context_nodes"]` and `stored["context_edges"]`); `storage.py` (the list of record tables follows `graph_tables.RECORD_TABLES`; the `stored` it builds for a write holds the versions of the context records that an edge or header names); `tests/test_storage.py`, `tests/test_storage_postgres.py`
- Must not touch: protected material, `contracts/`, `storage_postgres.py`, `storage_files.py`, `storage_copy.py` (F-07 is routed to CONVERT), IF-102 (put has no `categories`: decision 14 of IF-301)
- Depends on: T-07; A-98 installed
- Done when: the listed tests are green, all other tests unchanged except the two that stay red on purpose: TC-GTB-028 and the real side of TC-IF-301-23 (T-09); until this task the six-table assertions of `test_graph_records.py`, `test_graph_record_identity.py` and TC-IF-301-05 are red because the real code lists four tables (the three contract suites, `test_graph_records.py`, `test_graph_record_identity.py`, `test_graph_node_fields.py`, `test_storage.py`, `test_storage_postgres.py`, TC-GTB-014 with N = 1000, 500 node and 500 edge records within 500 ms)
- Notes: the Storage layer calls `check_record` without `categories` for the context tables, so it checks the shape only; the context-graph owner or the Workflow management calls `check_record` with the categories before it writes. `check_record("graph_nodes", ..., categories=...)` keeps working as before (golden 13). No new part or dependency; the interface change is the one of IF-301 v2 decided in A-98.

### T-09: Small fixes of the record checks (F-03, F-06, F-09, F-11, F-13b)
- Implements: REQ-GTB-027 (F-09, A-98); robustness of REQ-GTB-011 and REQ-GTB-022 (F-03, F-11); the test additions F-06 and F-13(b) have no requirement of their own
- Tests to turn green: TC-GTB-028 (`tests/acceptance/test_graph_context_tables.py`, the test of REQ-GTB-027); the real side of TC-IF-301-23 (`test_input_that_cannot_be_checked_is_a_schema_break_real`); new unit tests that fail first, in `tests/test_graph_record_checks.py`: F-03 (after 10 000 `check_record` calls with fresh equal `categories` dicts the validator cache stays below 256 entries), F-11 (`{"type": "entity", "xa": 1, "zz": 2}` with `patternProperties {"^x": {}}` and `additionalProperties: false` names `zz`), F-06(a) (a header whose second member names a version that is not stored gives `unknown_member` naming that member, also on `Storage`), F-06(b) (`validate("graph_nodes", {"id": "n", "data": {"type": "zz"}})` raises `invalid`/`unknown_type`); in `tests/test_storage_postgres.py`: F-13(b) (a node with an extra field is refused as `invalid`, `schema_break`, nothing stored)
- Touches: `graph_tables.py` (the validator cache keeps only the schemas of the fixed list, or is keyed by the schema's JSON; `_error_path` names an extra field as a key that neither `properties` nor `patternProperties` matches; a record nested deeper than 200 levels is `schema_break` naming `data`, a category whose schema fails `Draft202012Validator.check_schema` is `schema_break` naming `type`; the catch-all stays for anything else); `tests/test_graph_record_checks.py`, `tests/test_storage.py`, `tests/test_storage_postgres.py`
- Must not touch: protected material, `contracts/` (A-98 changed IF-301 already), `storage.py`
- Depends on: T-08; A-98 installed
- Done when: the listed tests are green and `test_graph_context_tables.py` is green; all other tests green (the three contract suites with no skip, `test_graph_records.py`, `test_storage.py`, `test_storage_postgres.py` on a throwaway postgres:16, TC-GTB-014 with N = 1000)
- Notes: the 200 levels count the record itself as level 1; checked iteratively, so the check itself does not hit the recursion limit. F-13(a) (two extra fields in a protected case) is accepted by the owner and waits for the next amendment of IF-301; F-07 and F-08 are routed to CONVERT. No new part, interface or dependency.

"""
text = once(text, "## Order and checks\n", tasks + "## Order and checks\n", plan)
text = once(text, "T-07 after T-06 and the install of A-93.", "T-07 after T-06 and the install of A-93; T-08 (context tables) after T-07 and T-09 (small fixes) after T-08, both after the install of A-98. Between the install of A-98 and T-08 the six-table assertions of three protected checks are red on purpose.", plan)
text = once(text, "18 requirements and one interface, seven tasks of one session each, two nodes (N-3.2 in T-01 to T-03 and T-05 to T-07, N-3.1 in T-04 and T-06)",
            "23 requirements and one interface, nine tasks of one session each, two nodes (N-3.2 in T-01 to T-03 and T-05 to T-09, N-3.1 in T-04, T-06 and T-09); "
            "this is over the guideline of about 8 tasks; a split into a follow-on goal for the context tables was offered and the owner decided on 2026-11-08 to keep all in G-V2.STORE", plan)
text = after_line(text, r"^6\. A-93 [^\n]*\n",
                  "7. A-98 (context graph tables `context_nodes` and `context_edges`, the rule for input that cannot be checked, REQ-GTB-023 to 027, TC-GTB-024 to 028, TC-IF-301-22 and -23, IF-301 v2) "
                  "follows the owner's decisions of 2026-11-08 on F-02 and F-09: separate tables, symmetric (`context_edges` too), the caller checks the categories, `schema_break` for input that cannot be checked; "
                  "F-03, F-11, F-06 and F-13(b) are fixed now (T-09), F-13(a) is accepted, F-07 and F-08 are routed to CONVERT.\n", plan)
out("plan.md", text)

# --- contract
text = read(contract)
section = """
## Context graph tables (A-98, F-02)
- `record_definitions()` lists six tables: the four above and `context_nodes` and `context_edges` (versioned, not deletable). `definitions()` stays the two tables of v1. The nodes and the edges of a context graph are kept in these tables, the graph header in `graphs` with `kind` `context` (REQ-GTB-023).
- `check_record("context_nodes", record, categories=None, stored=None, record_id=None)`: a record `{"id", "data"}` with a non-empty text `id`, a JSON field that is an object and a non-empty text `type` in it; otherwise `record_identity` (detail `id`) or `schema_break` (detail `data`, `type`). Without `categories` nothing more is checked: the Storage layer calls it this way and checks the shape only. With `categories` (the caller passes them, as in golden 13) the type must be one of them (`unknown_type`) and the field must fit its schema (`schema_break`) (REQ-GTB-024).
- `check_record("context_edges", record, ...)`: a record `{"id", "from", "to", "data"}` as `graph_edges`, with `data` an object; with `stored` the two ends must be stored context nodes, `stored["context_nodes"]` being `{id: [versions]}`, else `unknown_endpoint` naming the end. A workflow node does not count (REQ-GTB-025).
- `check_record("graphs", header, stored=...)`: for `kind` `context` the members are looked up in `stored["context_nodes"]` and `stored["context_edges"]`, for `kind` `workflow` in `stored["nodes"]` and `stored["edges"]` as before; a missing member is `unknown_member` (REQ-GTB-026). A missing key of `stored` counts as no records.
- Input that cannot be checked (REQ-GTB-027, F-09): a record nested deeper than 200 levels (the record itself is level 1) is `{"rule": "schema_break", "detail": "data"}`; a category whose schema is not a valid JSON schema is `{"rule": "schema_break", "detail": "type"}`, for a record of `graph_nodes` and of `context_nodes` alike. Nothing raises, in `check_record` and in `to_object`.
- `check_record("graph_nodes", ..., categories=...)` and golden 13 stay as they are.
"""
text = after_line(text, r"^The list is closed for the fields of a type too \(A-93[^\n]*\n", section, contract)
text = once(text, "the same form for `graph_nodes`, `graph_edges`, `graphs` and `skills`:", "the same form for `graph_nodes`, `graph_edges`, `graphs`, `skills`, `context_nodes` and `context_edges`:", contract)
goldens = """17. Context node (v2): `{"id": "c1", "data": {"type": "entity"}}` checked as `context_nodes` without `categories` gives `None`; `{"id": "c1", "data": {}}` gives `{"rule": "schema_break", "detail": "type"}`; with `categories = {"entity": <schema>}` and a field that breaks the schema it names that field.
18. Context edge (v2): an edge `e1` from `c1` to `c9` checked as `context_edges` with `stored["context_nodes"] == {"c1": [1]}` gives `{"rule": "unknown_endpoint", "detail": "c9"}`; with `stored["nodes"] == {"c9": [1]}` besides it still does; from `c1` to `c1` gives `None`.
19. Context header (v2): a `graphs` record of kind `context` naming `c9` with `stored["context_nodes"] == {"c1": [1]}` gives `{"rule": "unknown_member", "detail": "c9"}`; naming `c1` gives `None`; a record of kind `workflow` naming `c1` gives `{"rule": "unknown_member", "detail": "c1"}`.
20. Input that cannot be checked (v2): a data node whose `value` is nested 300 levels gives `{"rule": "schema_break", "detail": "data"}` (150 levels give `None`); a category `{"type": 5}` gives `{"rule": "schema_break", "detail": "type"}`.
"""
text = after_line(text, r"^16\. Extra field \(v2\)[^\n]*\n", goldens, contract)
decisions = """14. **A-98 (Verify finding F-02, owner's decisions of 2026-11-08):** the nodes and edges of a context graph are kept in their own tables `context_nodes` and `context_edges`, because the Storage layer cannot know the categories of a context graph (IF-102 `put` has no such argument). Symmetric tables, so ends and members of a context graph are looked up inside the context tables. The Storage layer checks the shape only (it calls `check_record` without `categories`); the context-graph owner or the Workflow management calls it with the categories before it writes. IF-102 does not change. v2 is not merged yet, so this is part of v2.
15. **A-98 (Verify finding F-09, owner's decision of 2026-11-08):** input that cannot be checked is `schema_break`, not `record_identity`: a record nested deeper than 200 levels names `data`, a category with an invalid schema names `type`. The limit is fixed so that mock and real code agree.
"""
text = after_line(text, r"^13\. \*\*A-93 [^\n]*\n", decisions, contract)
text = once(text, "golden 5 to 16, `record_id` of `check_record`, the fixed types forbid additional fields | A-90 (D-188, D-262 to D-266), A-92, A-93 |",
            "golden 5 to 20, `record_id` of `check_record`, the fixed types forbid additional fields, tables `context_nodes` and `context_edges`, input that cannot be checked | A-90 (D-188, D-262 to D-266), A-92, A-93, A-98 |", contract)
out("contract.md", text)

# --- mock
text = read(mock)
text = once(text, 'NEW_TABLES = ("graph_nodes", "graph_edges", "graphs", "skills")', 'NEW_TABLES = ("graph_nodes", "graph_edges", "graphs", "skills", "context_nodes", "context_edges")\nMAX_DEPTH = 200      # a record nested deeper than this is schema_break `data` (REQ-GTB-027)', mock)
helpers = '''def _too_deep(value):
    """True when the value is nested deeper than MAX_DEPTH levels (the record is level 1); iterative, so the check itself cannot hit the recursion limit."""
    stack = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        if depth > MAX_DEPTH:
            return True
        children = item.values() if isinstance(item, dict) else item if isinstance(item, list) else ()
        stack.extend((child, depth + 1) for child in children)
    return False


def _bad_schema(schema):
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError:
        return True
    return False


def _check_context(table, record, data, categories, stored):
    """context_nodes and context_edges (A-98): the shape; with categories the type and schema of a node; the ends of an edge in the stored context nodes."""
    if table == "context_nodes":
        type_id = data.get("type")
        if not isinstance(type_id, str) or not type_id:
            return {"rule": "schema_break", "detail": "type"}
        if categories is None:
            return None
        if type_id not in categories:
            return {"rule": "unknown_type", "detail": type_id}
        if _bad_schema(categories[type_id]):
            return {"rule": "schema_break", "detail": "type"}
        broken = _broken_path(categories[type_id], data)
        return {"rule": "schema_break", "detail": broken} if broken else None
    if stored is not None:
        for end in (record["from"], record["to"]):
            if end not in stored.get("context_nodes", {}):
                return {"rule": "unknown_endpoint", "detail": end}
    return None


'''
text = once(text, "def _check(table, record, categories, stored, record_id=None):", helpers + "def _check(table, record, categories, stored, record_id=None):", mock)
text = once(text, '    if table == "graph_edges":\n        for end in ("from", "to"):',
            '    if _too_deep(record):                                        # cannot be checked (REQ-GTB-027)\n        return {"rule": "schema_break", "detail": "data"}\n'
            '    if table in ("graph_edges", "context_edges"):\n        for end in ("from", "to"):', mock)
text = once(text, '''    data = record.get("data")
    if not isinstance(data, dict):
        return {"rule": "schema_break", "detail": "data"}
    if table in ("graph_nodes", "graph_edges"):''', '''    data = record.get("data")
    if not isinstance(data, dict):
        return {"rule": "schema_break", "detail": "data"}
    if table in ("context_nodes", "context_edges"):
        return _check_context(table, record, data, categories, stored)
    if table in ("graph_nodes", "graph_edges"):''', mock)
text = once(text, "                schema = categories[type_id]\n", "                if _bad_schema(categories[type_id]):\n                    return {\"rule\": \"schema_break\", \"detail\": \"type\"}\n                schema = categories[type_id]\n", mock)
text = once(text, '''                for member in data[key]:
                    if member["version"] not in stored.get(key, {}).get(member["id"], []):''', '''                where = ("context_" + key) if data["kind"] == "context" else key        # a context header looks in the context tables (REQ-GTB-026)
                for member in data[key]:
                    if member["version"] not in stored.get(where, {}).get(member["id"], []):''', mock)
text = after_line(text, r"^- a field of a node's JSON field that the schema of its type does not list is schema_break[^\n]*\n  detail is[^\n]*\n",
                  "- context_nodes and context_edges (A-98): the Storage layer checks the shape only; with categories a node is checked as before; edge ends and header members of a context\n"
                  "  graph are looked up in stored[\"context_nodes\"] and stored[\"context_edges\"]; a record nested deeper than 200 levels and a category with an invalid schema are schema_break.\n", mock)
out("mock.py", text)

# --- stand-in
text = read(standin)
text = once(text, 'RECORD_TABLES = ("graph_nodes", "graph_edges", "graphs", "skills")', 'RECORD_TABLES = ("graph_nodes", "graph_edges", "graphs", "skills", "context_nodes", "context_edges")', standin)
text = once(text, '''                "edges": {i: [v["version"] for v in vs] for i, vs in self._rows["graph_edges"].items()}}''',
            '''                "edges": {i: [v["version"] for v in vs] for i, vs in self._rows["graph_edges"].items()},
                "context_nodes": {i: [v["version"] for v in vs] for i, vs in self._rows["context_nodes"].items()},
                "context_edges": {i: [v["version"] for v in vs] for i, vs in self._rows["context_edges"].items()}}''', standin)
out("standin.py", text)

# --- contract suite: six tables, the two new cases
text = read(suite)
text = once(text, 'NODE_RECORD_TABLES = {t: {"versioned": True, "deletable": False} for t in ("graph_nodes", "graph_edges", "graphs", "skills")}',
            'NODE_RECORD_TABLES = {t: {"versioned": True, "deletable": False}\n                      for t in ("graph_nodes", "graph_edges", "graphs", "skills", "context_nodes", "context_edges")}', suite)
text = once(text, "record_definitions() lists the four record tables, versioned, not deletable.", "record_definitions() lists the six record tables, versioned, not deletable.", suite)
text = once(text, 'Example: record_definitions() -> graph_nodes, graph_edges, graphs, skills, each {"versioned": True, "deletable": False}.',
            'Example: record_definitions() -> graph_nodes, graph_edges, graphs, skills, context_nodes, context_edges, each {"versioned": True, "deletable": False}.', suite)
text = once(text, "v1 is unchanged and the four tables are added in their own operation", "v1 is unchanged and the six tables are added in their own operation", suite)
cases = '''    @mark.req("IF-301", "REQ-GTB-023", "REQ-GTB-024", "REQ-GTB-025", "REQ-GTB-026")
    @each_provider(IF, make=subject)
    def test_the_context_tables_are_checked(self, tables):
        """TC-IF-301-22 golden 17 to 19: context_nodes and context_edges check the shape, the ends of an edge and the members of a context header in the context tables.

        Example: {"id": "c1", "data": {}} as context_nodes -> schema_break "type"; an edge to c9 with only c1 stored -> unknown_endpoint "c9".
        """
        # Given: a stored context node c1, and the shapes of the context records
        stored = {"context_nodes": {"c1": [1]}}
        entity = {"entity": {"type": "object", "properties": {"type": {}, "name": {"type": "string"}}}}

        def header(kind, member):
            return {"id": "h1", "data": {"kind": kind, "context_graph_id": "ctx", "testbench_id": "", "description": "d",
                                         "nodes": [{"id": member, "version": 1}], "edges": []}}
        # When/Then: the six tables are listed, versioned and not deletable
        for table in ("context_nodes", "context_edges"):
            self.assertEqual(tables.record_definitions()[table], {"versioned": True, "deletable": False})
        # And: the shape of a node is checked without categories, the type and schema with them
        self.assertIsNone(tables.check_record("context_nodes", node("c1", "entity")))
        self.assertEqual(tables.check_record("context_nodes", {"id": "c1", "data": {}}), {"rule": "schema_break", "detail": "type"})
        self.assertEqual(tables.check_record("context_nodes", {"id": "c1"}), {"rule": "schema_break", "detail": "data"})
        self.assertEqual(tables.check_record("context_nodes", node("c1", "entity", name=5), categories=entity), {"rule": "schema_break", "detail": "name"})
        self.assertEqual(tables.check_record("context_nodes", node("c1", "other"), categories=entity), {"rule": "unknown_type", "detail": "other"})
        self.assertIsNone(tables.check_record("context_nodes", node("c1", "entity", name="x"), categories=entity))
        # And: an edge needs a text end and stored context nodes as ends; a workflow node does not count
        self.assertEqual(tables.check_record("context_edges", {"id": "e1", "from": "c1", "data": {}}), {"rule": "record_identity", "detail": "to"})
        self.assertEqual(tables.check_record("context_edges", edge("e1", "c1", "c9"), stored=stored), {"rule": "unknown_endpoint", "detail": "c9"})
        self.assertEqual(tables.check_record("context_edges", edge("e1", "c1", "c9"), stored={"nodes": {"c9": [1]}, "context_nodes": {"c1": [1]}}),
                         {"rule": "unknown_endpoint", "detail": "c9"})
        self.assertIsNone(tables.check_record("context_edges", edge("e1", "c1", "c1"), stored=stored))
        # And: a header of kind context looks in the context tables, a header of kind workflow does not
        self.assertEqual(tables.check_record("graphs", header("context", "c9"), stored=stored), {"rule": "unknown_member", "detail": "c9"})
        self.assertEqual(tables.check_record("graphs", header("workflow", "c1"), stored=stored), {"rule": "unknown_member", "detail": "c1"})
        self.assertIsNone(tables.check_record("graphs", header("context", "c1"), stored=stored))

    @mark.req("IF-301", "REQ-GTB-027")
    @each_provider(IF, make=subject)
    def test_input_that_cannot_be_checked_is_a_schema_break(self, tables):
        """TC-IF-301-23 golden 20: a record nested deeper than 200 levels is schema_break naming data, a category with an invalid schema is schema_break naming type.

        Example: a data node whose value is a list nested 300 times -> {"rule": "schema_break", "detail": "data"}; categories {"entity": {"type": 5}} -> detail "type".
        """
        # Given: a data node whose value is nested 300 levels, one nested 150 levels, and a category with an invalid schema
        deep, shallow = 1, 1
        for _ in range(300):
            deep = [deep]
        for _ in range(150):
            shallow = [shallow]
        # When/Then: the deep record is refused as schema_break naming data, in the check and in the rebuild, and nothing raises
        refused = {"rule": "schema_break", "detail": "data"}
        self.assertEqual(tables.check_record("graph_nodes", node("d1", "data", value=deep)), refused)
        self.assertEqual(tables.to_object(node("d1", "data", value=deep)), {"refused": refused})
        # And: the twin nested 150 levels is accepted
        self.assertIsNone(tables.check_record("graph_nodes", node("d1", "data", value=shallow)))
        # And: a category whose schema is not valid is refused naming type, for both node tables
        broken = {"rule": "schema_break", "detail": "type"}
        self.assertEqual(tables.check_record("graph_nodes", node("c1", "entity"), categories={"entity": {"type": 5}}), broken)
        self.assertEqual(tables.check_record("context_nodes", node("c1", "entity"), categories={"entity": {"type": 5}}), broken)

'''
anchor = '''    @mark.req("IF-301", "REQ-GTB-022")
    @each_provider(IF, make=subject)
    def test_a_node_with_an_extra_field_is_refused_naming_it(self, tables):
'''
text = once(text, anchor, cases + anchor, suite)
out("suite.py", text)

# --- the two acceptance tests that name the record tables
for name, path_ in (("records.py", records), ("identity.py", identity)):
    text = read(path_)
    text = once(text, 'RECORD_TABLES = {t: {"versioned": True, "deletable": False} for t in ("graph_nodes", "graph_edges", "graphs", "skills")}',
                'RECORD_TABLES = {t: {"versioned": True, "deletable": False}\n                 for t in ("graph_nodes", "graph_edges", "graphs", "skills", "context_nodes", "context_edges")}', path_)
    out(name, text)
PY
copy "$WORK/requirements.md"      "$NODE/requirements.md"
copy "$WORK/test-spec.md"         "$NODE/test-spec.md"
copy "$WORK/test-requirements.md" "$NODE/test-requirements.md"
copy "$WORK/goal.md"              "$GOAL"
copy "$WORK/plan.md"              "$PLAN"
copy "$WORK/contract.md"          "$CONTRACT"
copy "$WORK/mock.py"              "$MOCK"
copy "$WORK/standin.py"           "$STANDIN"
copy "$WORK/suite.py"             "$SUITE"
copy "$WORK/records.py"           "$RECORDS"
copy "$WORK/identity.py"          "$IDENTITY"
copy specs/mia/amendments/A-98/test_graph_context_tables.py tests/acceptance/test_graph_context_tables.py
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== regenerate the requirement block of the model and check it"
    python3 -I tools/gen_node_requirements_model.py .
    bash tools/check_sysml.sh specs/mia/architecture.sysml | tail -3
    echo "== trace_check: errors about the new ids (none expected), and the total (the known baseline is 517)"
    python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests > "$WORK/trace.txt" 2>&1 || true
    grep -E "GTB-02[3-8]|IF-301-2[23]" "$WORK/trace.txt" || echo none
    echo "total errors: $(grep -c '| ERROR |' "$WORK/trace.txt")"
    echo "== the checks (the _mock side and all old checks must pass; the real side of TC-IF-301-05, 22, 23 and TC-GTB-024 to 028 are red until T-08 and T-09)"
    python tests/acceptance/contract/test_if_301_v2_graph_tables.py -k _mock 2>&1 | tail -1
    python tests/acceptance/test_graph_records.py 2>&1 | tail -1
    python tests/acceptance/test_graph_record_identity.py 2>&1 | tail -1
    python tests/acceptance/test_graph_node_fields.py 2>&1 | tail -1
    python tests/acceptance/test_graph_context_tables.py 2>&1 | tail -1 || true
fi
