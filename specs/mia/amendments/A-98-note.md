# A-98: context graph tables and input that cannot be checked (G-V2.STORE, F-02 and F-09)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a98.sh` is not yet run with `--do` in the repository.

## Owner's decisions of 2026-11-08 (acceptance questionnaire on the third Verify run)
| Finding | Decision | Where |
|---|---|---|
| F-02 context node cannot be stored through the real Storage layer | **fix now in this goal**: separate tables `context_nodes` **and** `context_edges` (six record tables); the caller checks the categories, the Storage layer checks the shape; IF-102 does not change | A-98, T-08 |
| F-09 catch-all names the wrong rule | **fix now**: `schema_break`, detail = the field (`data`, `type`) | A-98, T-09 |
| F-03 validator cache, F-11 extra-field naming with patternProperties | **fix now** | T-09 |
| F-06 two test gaps, F-13(b) postgres | add the unprotected tests now | T-09 |
| F-13(a) two extra fields in a protected case | **accepted** by the owner; waits for the next amendment of IF-301 | – |
| F-07, F-08 (`copy_records`, conversion inputs) | accepted, routed to the CONVERT goal | – |
| scope | keep everything in G-V2.STORE (the drafter had proposed a split; plan.md is now at nine tasks, over the guideline of about 8, and says so) | plan.md |

## What A-98 contains
| Part | Content |
|---|---|
| **REQ-GTB-023..027** (new, Draft; group CX for 023..026, TY for 027; Parent FR-40) | 023 the two tables, versioned, never deleted; 024 shape of a context node and edge; 025 ends of a context edge are stored context nodes; 026 members of a header of kind context are stored context records; 027 input that cannot be checked is `schema_break` |
| **IF-301 v2** | new section "Context graph tables", `record_definitions()` lists six, golden 17 to 20, decisions 14 and 15, version row (v2 is not merged: stays v2) |
| **Checks** | TC-GTB-024..028 (new `tests/acceptance/test_graph_context_tables.py`, staged in `amendments/A-98/`), TC-IF-301-22 and -23 in the contract suite (mock and real), TR-GTB-001 applies to the five |
| **Protected files changed** | mock (six tables, context checks, depth cap, `check_schema`), stand-in helper (six tables, `stored` holds the context records), contract suite (TC-IF-301-05 expects six tables), `test_graph_records.py` and `test_graph_record_identity.py` (the table list has six names) |
| **plan.md** | T-08 context tables (graph_tables.py, storage.py), T-09 small fixes (F-03, F-06, F-09, F-11, F-13b), counts, order, decision 7 |
| Generated | `architecture.sysml` requirement block regenerated after `--do` |

## Points for the owner
1. **A new bound: 200 levels.** A record nested deeper than 200 levels (the record is level 1) is refused as `schema_break` naming `data`. It is fixed so that mock and real code agree; before, such input gave `record_identity`/`record` only when it hit the recursion limit (about 1000 levels). A legal value nested 201 levels or more is now refused. Say if you want another number.
2. **Red on purpose between the install of A-98 and the end of T-08:** `test_graph_records.py`, `test_graph_record_identity.py` and TC-IF-301-05 (real side) assert six tables and the real code lists four. That is why the context tables are T-08 and the small fixes T-09 (T-09 would otherwise start with three red protected checks). Install A-98 only when T-08 is next.
3. **`check_record("graph_nodes", ..., categories=...)` and golden 13 stay.** A context node can still be checked through `graph_nodes` with categories, but the Storage layer cannot store it there; the contract names `context_nodes` for storing. If you want golden 13 removed, that is another amendment.
4. **The Storage layer checks the shape only for context nodes.** A context node with a wrong field is stored unless the caller (context-graph owner or Workflow management) calls `check_record` with the categories first. The sentence "the Storage layer calls it again as a guard" holds for the workflow tables only (decision 14).
5. **IDs are per table.** A context node and a workflow node may have the same ID; edges and headers look in their own tables (that is the symmetric design you chose).
6. REQ-GTB-023..027 need review and a plausibility rating (protected `plausibility.yaml`; the same basis as REQ-GTB-019..022 fits for 023..026; REQ-GTB-027 has one fixed number, 200).

## Checked by the drafter (scratch copies; nothing installed in the repository)
- `--do` twice: the second run changes nothing (checksums of `specs/`, `contracts/`, `tests/` identical). All anchors found on the repository state after A-93, A-94 and T-07.
- After `--do`: `check_sysml` 0 errors; `trace_check` 517 errors = baseline, none for REQ-GTB-023..027, TC-GTB-024..028, TC-IF-301-22/23; `_mock` side of the contract suite and all other mock-side checks green.
- Red as expected before T-08/T-09: the new real-side cases, `test_graph_context_tables.py` (2 failures, 9 errors), the three six-table assertions.
- Satisfiable: a throwaway implementation of T-08 and T-09 in the scratch copy (about 50 lines in `graph_tables.py` and `storage.py`) turns the contract suite (mock and real), TC-GTB-024..028, the IF-301 v1 suite and all earlier checks green (`test_graph_records.py`, `test_graph_record_identity.py`, `test_graph_node_fields.py`, `test_graph_record_checks.py`, `test_graph_tables.py`, `test_storage.py`, `test_graph_record_objects.py`, `test_graph_document_form.py`). It is not in the repository; T-08 and T-09 write the real code, test first. Not run: `test_storage_postgres.py` (needs a throwaway postgres:16).

## Install (after the look-only review; the next step is T-08 in a fresh Implement session)
```
bash tools/apply_amendment_a98.sh --report     # look only
bash tools/apply_amendment_a98.sh --do         # then commit "plan: A-98 installed"
```
