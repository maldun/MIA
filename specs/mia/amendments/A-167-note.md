# A-167: IF-301 v3, scoped IDs of steps and connections (G-V4.GRAPHSTORE.CORE, REQ-GTB-029 to 031)

Status: **draft for the owner's review, 2026-11-21**; the script `tools/apply_amendment_a167.sh` is not yet run with `--do`.

## Finding
CORE makes a step or connection belong to exactly one graph (FR-60, D-368, D-402): its record ID is `<graph id>/<local id>`, and the Graph tables refuse any other non-empty ID and any header member of another graph as `unscoped_id` (REQ-GTB-029, REQ-GTB-030, REQ-GTB-031). On the prototype code (branch `prototype/g-v4`, the rule in `graph_tables.py`) the protected v2 tests that write plain IDs fail: `tests/test_graph_record_checks.py` 34 failures, `tests/acceptance/contract/test_if_301_v2_graph_tables.py` 28 failures, `tests/acceptance/test_graph_records.py` 14 errors (reproduced 2026-11-21, numbers as in section 5 of the CORE high-level spec). The contract IF-301 v2 does not know the rule, and the v2 mock does not refuse plain IDs.

## Proposal
- **IF-301 v3** (the owner's choice, D-409: v2 is on master and scoped IDs refuse what v2 accepted): section "What changes against v2"; the rule `unscoped_id` in the row of `check_record`; golden 10, 11, 15 to 19 with scoped IDs; new golden 22 (a step or connection without its graph in the ID; the empty ID stays `record_identity`, D-409) and 23 (a header names only members of its own graph, with and without `stored`); decision 17; a version-history row.
- **Mock** `tests/helpers/mocks/if_301_graph_tables_v2.py`: `_split_scoped` and the two checks, in the order of the prototype (after the identity checks; header members member by member before `unknown_member`). The file name stays.
- **Suite** `test_if_301_v2_graph_tables.py`: the plain IDs scoped (same 20 cases, same rules and expected results); new TC-IF-301-25 (golden 22) and TC-IF-301-26 (golden 23). The file name stays.
- **Acceptance and unit tests** `tests/acceptance/test_graph_records.py` and `tests/test_graph_record_checks.py` (the latter is not protected; rewritten here so all three stay consistent): plain IDs scoped, nothing else. Where a test has a header its ID is the graph part (`wf1/n1`, `h1/c1`), elsewhere `g`; header, skill and v1 document IDs stay plain. Three places where intent had to be read: garbage records in the contract suite scoped so they still reach the data and type checks; a malformed header member `g/n1`; the document round trip and the master node, whose node IDs are now `g/...` in the v1 document too (both implementations accept a slash there).
- **N-3.2 node files**: one paragraph each in `test-spec.md` and `requirements.md`: the IDs named in the scenarios and acceptance criteria are local IDs; the tests write the scoped form. The approved texts are otherwise unchanged.

Why this and not the alternatives: (1) scope the IDs in the Workflow management only and leave the tables open: a record written by any other path (move, sync, a test, a later tool) could still belong to no graph, which FR-60 forbids; (2) a separate graph field next to a plain ID: two places that must agree, and every lookup by record ID needs both; (3) keep v2 tests and add a switch: two behaviours of one table. The scoped ID is the form the converter and the 15 skill graphs already use (prototype round 02).

## What the script changes (drafts in `specs/mia/amendments/A-167/`; the node notes are made from the installed files; running it twice changes nothing)
| File | Change |
|---|---|
| `contracts/IF-301-graph-tables.md` | v3 text (+20 -10 lines) |
| `tests/helpers/mocks/if_301_graph_tables_v2.py` | rule `unscoped_id` (+19 -6) |
| `tests/acceptance/contract/test_if_301_v2_graph_tables.py` | scoped IDs, TC-IF-301-25 and -26 (+134 -95) |
| `tests/acceptance/test_graph_records.py` | scoped IDs (+78 -78) |
| `tests/test_graph_record_checks.py` | scoped IDs (+24 -24) |
| N-3.2 `test-spec.md`, `requirements.md` | one note paragraph each |

## Tried (2026-11-21)
- Drafts against the prototype code: the three test files green (19, 40, 20 tests; before: 34 failures, 28 failures, 14 errors), the new cases green on mock and real side.
- Drafts against `goal/v4` code (no rule yet): `test_graph_records.py`, `test_graph_record_checks.py` and the v1 suite green; the v2 suite red only in the real side of TC-IF-301-25 and -26 (assertion, not an error), as intended until the CORE task that adds the rule.
- `--do` on a scratch copy of the worktree: seven files installed, the same results; a second run changes nothing. `test_doc_check.py`: no finding in the three files, before and after. The mock is used by no other test.

## To decide and to do
1. **Owner:** read the v3 text (`bash tools/apply_amendment_a167.sh --report`), above all golden 22 and 23 and decision 17, and the three places of interpretation above.
2. **Done (owner, 2026-11-21):** the text change of REQ-GTB-029 ("a **non-empty** ID not of the form ..."), which follows from D-409 (the empty ID stays `record_identity`); it is the one CORE item marked changed since review.
3. **Owner:** `bash tools/apply_amendment_a167.sh --do` on `goal/v4`, then commit as `plan: A-167 installed`.
4. **Plan of CORE (step 5, not yet written):** the first task implements REQ-GTB-029 to 031 in `graph_tables.py` (prototype lines 159 to 224 as the basis, reuse map R1) and turns the real side of TC-IF-301-25 and -26 green, with every other test unchanged.
