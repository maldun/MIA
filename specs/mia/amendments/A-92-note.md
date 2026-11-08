# A-92: a graph record is stored under its own ID (G-V2.STORE, REQ-GTB-021)

Status: **draft for the owner's review, 2026-11-07**; the script `tools/apply_amendment_a92.sh` is not yet run with `--do`.

## Finding
Found in Implement T-04 (`implementation-log.md`, Findings): `Storage.put("graph_nodes", "x", {"id": "y", ...})` is accepted. A graph header pins its members by the `id` inside the record, the storage finds a record by the record ID, so a record under another ID cannot be found again (REQ-GTB-014, REQ-GTB-017). The stand-in of the tests behaves the same, so no check covers it.

## Proposal (the usual robust way: refuse at the write boundary, one rule, one place)
- **REQ-GTB-021** (new, Draft, subject Persistence, Must): if a record of a graph table is written under a record ID that differs from the ID inside the record, the Graph tables refuse the record and name the field `id`. Check TC-GTB-022 (scenario: a node with its own ID `n1`, written under `x`, then under `n1`); TR-GTB-001 (values by hand) applies to it.
- **IF-301 v2**: `check_record(table, record, categories=None, stored=None, record_id=None)`. When `record_id` is given and differs from the `id` inside the record: `record_identity`, detail `id`. Without it nothing changes. The Storage layer passes the ID it writes under. v2 is not merged yet, so the argument is part of v2 (decision 12 in the contract text, golden example 15, the version-history row).
- **Mock, suite, stand-in**: the mock follows the contract; the suite gets TC-IF-301-20 (a node, an edge and a skill, with and without `record_id`); the storage stand-in passes `record_id`; a new acceptance test `test_graph_record_identity.py` holds TC-GTB-022.

Why this and not the alternatives: (1) the Storage layer compares the two IDs itself: the rule would live in N-3.1 while FR-40 and the other GTB requirements are Graph-tables rules, and the Workflow management (which calls `check_record` before it writes, D-264) would not get the refusal; (2) leave it: a header can then pin a member that the storage cannot find, found only on read; (3) a new function `check_write(table, record_id, record, ...)`: a second entry point for the same checks. The optional argument is the smallest change and keeps `check_record` a pure function.

## What the script changes (anchored edits of the installed files; refuses when an anchor is missing; running it twice changes nothing)
| File | Change |
|---|---|
| N-3.2 `requirements.md` | REQ-GTB-021, Status Draft |
| N-3.2 `test-spec.md` | row and scenario of TC-GTB-022 |
| N-3.2 `test-requirements.md` | TR-GTB-001 applies also to TC-GTB-022 (the approved text changes: review again) |
| `goals/G-V2.STORE/goal.md` | scope row REQ-GTB-021 |
| `contracts/IF-301-graph-tables.md` | argument, rule text, golden 15, decision 12, version-history row |
| `tests/helpers/mocks/if_301_graph_tables_v2.py`, `tests/helpers/graph_store_standin.py`, `tests/acceptance/contract/test_if_301_v2_graph_tables.py` | protected files, edited by the owner's script only |
| `tests/acceptance/test_graph_record_identity.py` | new, TC-GTB-022 (staged in `specs/mia/amendments/A-92/`) |
| `specs/mia/architecture.sysml` | the generated requirement block, regenerated after `--do` |

Already in the branch (not protected, harmless): `graph_tables.check_record` accepts `record_id` and ignores it, so the new checks fail by assertion and not by a TypeError.

## Tried on a scratch copy of the branch (2026-11-07)
`--do`: nine files installed, the model regenerates (427 node requirements, `check_sysml` 0 errors), no structural finding of `trace_check` for REQ-GTB-021 or TC-GTB-022; the mock side of the v2 suite, `test_graph_records.py` and everything old stay green; red as intended: TC-GTB-022 (StorageError not raised) and the real side of TC-IF-301-20 (None where `record_identity` is expected). With the simulated T-06 (the comparison in `graph_tables._check`, `record_id` passed by `storage.py`) both turn green, together with `test_storage.py` and the IF-102 suite.

## To decide and to do
1. **Owner:** review REQ-GTB-021, TC-GTB-022 and the changed TR-GTB-001 as in the batched review of REQ-GTB-005..020 (`req_review.py`), and rate the plausibility record. Proposed basis text: "an equality of two strings before the write; no number depends on it (proposal of the agent, 2026-11-07; to be rated by the owner)". `plausibility.yaml` is protected: the owner (or `apply_plausibility.py`) writes it.
2. **Owner:** `bash tools/apply_amendment_a92.sh` (look), then `--do`, commit as `plan: A-92 installed`.
3. **Task T-06 (proposed for `plan.md`, after the approval; not yet added):** "Record under its own ID" implements REQ-GTB-021; touches `graph_tables.py` (the comparison in `_check`), `storage.py` (`put` passes `record_id`), `tests/test_storage.py` (a unit test for the real storage on every backend); must not touch protected material; depends on A-92 installed; done when TC-GTB-022, the real side of TC-IF-301-20 and the new unit test are green and all other tests unchanged. One session, no new part or dependency.
4. A-92 is the second amendment of this goal (A-91, A-92 of the reserved A-91..A-99); REQ-GTB-021 and TC-GTB-022 are the first of the reserved REQ-GTB-021..029 and TC-GTB-022...
