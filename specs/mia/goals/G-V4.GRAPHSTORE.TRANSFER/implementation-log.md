# Implementation log: G-V4.GRAPHSTORE.TRANSFER

Goal: G-V4.GRAPHSTORE.TRANSFER   Line of work: goal/v4.graphstore.transfer   Supervision: supervised (agent's own recommendations delegated by the owner for RULES and TRANSFER, D-423)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Move integrity and order | done | see `git log` ("feat: T-01 move integrity and order") | TC-SLY-016 to 020, TC-SLY-009 (`tests/acceptance/test_transfer_move.py` 6 of 7); the move half of TC-SLY-021; `tests/test_graph_store_transfer.py` (9 unit tests); `tests/test_storage_copy.py`, `tests/test_migrate.py` kept | TC-SLY-021 stays red at its sync half (line 156, `sync_store` is still the stub) until T-03 |

## T-01: Move integrity and order

**What was done**
- `graph_store_transfer.py`: `move_store` replaces the stub. First `check_graphs` checks every graph of the source (`graph_problems`): the kind against `graph_rule_set.kinds()` (`unknown_kind` with the kind; such a graph is not checked further, its member tables are unknown), every header version with `graph_tables.check_record(..., stored=...)` built from the member versions the source holds (`unknown_member` and the other structural refusals), every connection the header names with `check_record` against the step IDs the source holds (`unknown_endpoint`). Every graph with problems is named in one `move_refused` refusal, each problem once. Then one `copy_records` over all defined tables in write order.
- `storage_copy.py`: `GRAPH_GROUP` (write order, moved here from the stub so that `storage_copy` does not import `graph_store_transfer`; the stub's name stays as an import), `ordered_tables` (graph group members first, `graphs` last, then the other tables), `library_tables()` (graph group as far as defined, plus `workflows`, `context_graphs`); export and seed carry them (REQ-SLY-009). `copy_records` unchanged: its conflict and record checks stay, both before any write.
- `migrate.py`: `files-to-db` and `db-to-files` go through `move_store` (the dry run wraps the target as before); `library-export` and `library-seed` use `library_tables()`; a `move_refused` refusal is one line, `refused: <graph>: <rule> <detail>[, ...][; <graph>: ...] (nothing was written)`, exit 1.
- Adapted from the prototype `graph_store_move.py` (`_problems`, `move_store`): problems as `{"rule", "detail"}` items instead of text, the kind from the registry, the endpoint check added, the target conflict left to `copy_records` (one refusal path for conflicts, as before), no separate `GRAPH_TABLES`.
- `specs/mia/architecture.sysml`: `graph_store_transfer.py` added to the modules of `storageLayer`, its doc says what T-01 built. `check_sysml_model.py` OK; `check_sysml.sh specs/mia/architecture.sysml` 0 errors, 0 warnings.
- Unit tests `tests/test_graph_store_transfer.py`, written first and seen red against the stub (7 of 9 failing; the round trip and the second move pass on the stub by their nature): every table moved with members before headers, a missing member version, a connection to a missing step, an unknown kind, a cycle moved, a second move, `files-to-db` with a damaged header (the demonstrator: one line naming the graph, exit 1, nothing written), the round trip through `migrate`, the export holds the graph group.

**Tests green (my runs, feedback only):** `tests/acceptance/test_transfer_move.py` 6 of 7 with the database side on a throw-away postgres:16 (TC-SLY-021 fails only at `sync_store`, line 156); `tests/test_graph_store_transfer.py` 9/9; `tests/test_storage_copy.py` 7/7; `tests/test_migrate.py` 10/10.

**Regression set (2026-11-23, sequential):** unit suite `discover -s tests` 2563 tests, 1 failure: `test_checkout_untouched` named `goal.md` and this log, which I edited by hand during the run; re-run alone on the quiet tree: OK. Acceptance scripts one by one (52 Python files), compared with a clean `git archive HEAD` export run the same way: 46 OK; red `test_decide_guard.py`, `test_judge_calibration.py` (known, G-V3.REPORT F-3, no summary line as at HEAD), `test_transfer_move.py` 1 (TC-SLY-021 sync half, T-03; was 7), `test_transfer_interrupt.py` 6 (was 8), `test_transfer_sync.py` 9 + 1 skipped and `test_transfer_sets.py` 6 (unchanged, T-02 to T-05). The export showed `test_rules_rule_set.py` red only because its protected-file check asks git and the export is not a checkout; on the branch it is OK. No new red.
- The two interrupt cases now green are the whole-store move of TC-SLY-029/036 (`run='move'`, files and postgres): members first and the skip on a rerun give complete graphs at every stop already. Their one-graph and sync cases stay red (T-03, T-04); T-04 keeps them as its checks.

**Deliberate-defect check (TR-TRANSFER-008),** runner `/home/maldun/.claude-work/jobs/85fdeba4/tmp/mutate_t01.py` (patches the module in the test process, the code on disk unchanged):

| Defect | Check | Result |
|---|---|---|
| each record checked alone (today's `copy_records` only: `check_graphs` a no-op) | TC-SLY-017, TC-SLY-018 | both fail; TC-SLY-019 passes |
| headers written first (`graphs` first in the write order, as today's `migrate`) | TC-SLY-019 | fails; TC-SLY-017, 018 pass |

**Traceability:** `trace_check.py --spec-dir specs/mia --tests-dir tests` gives the same 549 errors on this change as on a clean export of HEAD (legacy items, compared line by line); none new.

## Findings
| Finding | Task | Covered by test |
|---|---|---|

## Plan amendments
None.

## Stop conditions hit
| Date | Task | Condition | Escalated to | Outcome |
|---|---|---|---|---|

## Unspecified behavior (decisions no requirement covers)
| Decision | Where in code | Proposed requirement or amendment |
|---|---|---|
| The command line text of a refused move: `refused: <graph>: <rule> <detail> (nothing was written)`, all graphs on one line separated by `; ` | `migrate._explain` | none proposed: same form as the existing `refused:` line of REQ-SLY-007 (finding F1 of G-V1); Verify may ask for an item under REQ-SLY-039's command texts |

## Decisions
- T-01: `library-seed` does not run the per-graph check of the move; it keeps `copy_records`' checks and the write order (members first). REQ-SLY-009 asks for identical entries and the order, not for the graph check; a damaged library folder is refused by `copy_records` only where a record breaks put's rules.

## Open questions for Phase 4
- T-01: should `library-seed` also refuse a folder whose headers name missing members (the check of REQ-SLY-017)? Not asked by REQ-SLY-009; noted above.
