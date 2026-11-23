# Implementation log: G-V4.GRAPHSTORE.TRANSFER

Goal: G-V4.GRAPHSTORE.TRANSFER   Line of work: goal/v4.graphstore.transfer   Supervision: supervised (agent's own recommendations delegated by the owner for RULES and TRANSFER, D-423)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Move integrity and order | done | see `git log` ("feat: T-01 move integrity and order") | TC-SLY-016 to 020, TC-SLY-009 (`tests/acceptance/test_transfer_move.py` 6 of 7); the move half of TC-SLY-021; `tests/test_graph_store_transfer.py` (9 unit tests); `tests/test_storage_copy.py`, `tests/test_migrate.py` kept | TC-SLY-021 stays red at its sync half (line 156, `sync_store` is still the stub) until T-03 |
| T-02 Durable files, cut back, the same answers | done | see `git log` ("feat: T-02 durable files, cut back") | TC-SLY-023; TC-SLY-022 kept (`tests/acceptance/test_transfer_sync.py` class SameBehaviour 2 of 2); `tests/test_storage_files.py` (6 new unit tests); `tests/test_storage_postgres.py` 44 (1 new) | the format marker is left to T-05 (decision below) |
| T-03 Lag, sync, aside, lock, commands | done | see `git log` ("feat: T-03 lag, sync, aside, lock, commands") | TC-SLY-024 to 028, TC-SLY-038, TC-SLY-039, TC-SLY-021 whole; `tests/test_graph_store_transfer.py` 14 (5 new) | TC-SLY-033 and 037 (T-05) green early through the sync |
| T-04 Side records, one-graph move, interruptions | done | see `git log` ("feat: T-04 side records, one-graph move, interruptions") | TC-SLY-031, TC-SLY-029, TC-SLY-036 (all cases); `tests/test_graph_store_transfer.py` 19 (5 new) | TC-SLY-030 skipped until VIEW is merged; must be green before Verify |

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

## T-02: Durable files, cut back, the same answers

**What was done**
- `storage_files.py`: one private writer `_replace(path, text)` for every file the backend writes: temporary file in the target folder, flush and `os.fsync` of the file, `os.replace`, then `os.fsync` of the folder (REQ-SLY-023); a failure before the rename removes the temporary file and leaves the old one. `append` writes through it (same JSON text as before, so REQ-SLY-007's identical files hold). `cut(table, id, n)` keeps the versions 1 to n and rewrites the file through `_replace`; nothing is written when the record has no version above n; `n == 0` removes the record. `put_file(path, text)` writes a plain file at `path` relative to the root through `_replace`, making its folders.
- `storage_postgres.py`: `cut(table, id, n)` is one `DELETE ... WHERE tbl, id AND version > n`.
- `storage.py`, IF-102 and `graph_store_transfer.py` untouched (the sync calls `cut` and `put_file` in T-03).
- `specs/mia/architecture.sysml`: the storageLayer doc says what T-02 built. `check_sysml_model.py` OK; `check_sysml.sh specs/mia/architecture.sysml` 0 errors, 0 warnings.
- Unit tests written first and seen red (files 6 of 6, PostgreSQL cut 1 of 1 with `AttributeError: cut`): durable append (exactly fsync file, replace, fsync folder), a failed flush keeps the old file and leaves no temporary file, cut to 2 lists 1 and 2 (the demonstrator, on files and on the database), cut at or above the last version and on a missing record writes nothing, cut to 0 leaves no record, `put_file` below the root is durable.

**Tests green (my runs, feedback only):** `tests/acceptance/test_transfer_sync.py` SameBehaviour 2/2 (TC-SLY-022 on a throw-away postgres:16, TC-SLY-023); `tests/test_storage_files.py` 6/6; `tests/test_storage_postgres.py` 44/44; `tests/test_storage.py` OK.

**Regression set (2026-11-23, sequential, runner `/home/maldun/.claude-work/jobs/85fdeba4/tmp/regress02.sh`):** unit suite `discover -s tests` 2570 tests OK (skipped 5, expected failures 2). Acceptance scripts one by one, compared with a clean `git archive HEAD` export (`/home/maldun/.claude-work/jobs/85fdeba4/tmp/acc02_new.txt`, `acc02_base.txt`): the only difference is `test_transfer_sync.py` 8 failures + 1 skipped (was 9: TC-SLY-023 now green). `test_rules_rule_set.py` is red only in the export (it asks git). Unchanged reds: `test_decide_guard.py`, `test_judge_calibration.py` (known), `test_transfer_move.py` 1, `test_transfer_interrupt.py` 6, `test_transfer_sets.py` 6 (T-03 to T-05). No new red.

**Deliberate-defect check (TR-TRANSFER-008),** runner `/home/maldun/.claude-work/jobs/85fdeba4/tmp/mutate_t02.py` (replaces `FileBackend._replace` in the test process by a rename without fsync, as before T-02; code on disk unchanged):

| Defect | Check | Result |
|---|---|---|
| no flush (rename only) | TC-SLY-023 | fails |

**Traceability:** `trace_check.py --spec-dir specs/mia --tests-dir tests` gives the same 549 ERROR lines as the HEAD export (compared line by line); none new.

## T-03: Lag, sync, aside, lock, commands

**What was done**
- `graph_store_transfer.py`: `copy_lock(root)` takes `fcntl.flock` (exclusive, non-blocking) on `<root>/sync.lock`; a held lock is `StorageError("locked", detail={"lock": "sync.lock"})`; the system drops it with the process (REQ-SLY-028). `lag(live, copy)` lists every graph of either store that is not current: `refused` when the live graph has problems (`graph_problems`, reason the rules joined by ", "), `copy_only`, `differs` when the header or any member named by a header version in either store holds copy versions the live store does not (entries compared with author and time), `behind` when the copy lacks live versions; reason `None` except for `refused` (REQ-SLY-024). `sync_store(live, copy)`: under the lock, `check_graphs` on the live store first (REQ-SLY-021, the same refusal as the move); a record of the graph group outside every not-current graph whose copy history is not the start of the live one is `conflict` before any write; then per differing or copy-only graph the aside file through `put_file` (`aside/<graph>__<UTC stamp>.json`, a suffix `_n` when the name is taken; content `{"graph", "set_aside_at", "reason", "header", "members"}` with only the copy's versions beyond the shared ones), then the cut back of every record of the graph to its shared versions, header first (REQ-SLY-026, 038); then `copy_records` over the graph group tables (members first, headers last, REQ-SLY-019). Answer: `graphs` = graphs not current, `records` = versions appended, `set_aside` per graph `{"versions", "file", "reason"}` with the file relative to the copy (REQ-SLY-027).
- A copy-only graph goes through the same cut back (to 0, which removes), header first, after its aside file; the prototype's `_remove_from` and `_clear_orphans` are not needed: a rerun after any stop finds the remaining copy-only member versions as `differs` and cuts them back after a new aside file.
- `migrate.py`: `lag` and `sync` with `--copy DIR` and the live store from `--data DIR` or `--database-url URL` (REQ-SLY-039). `lag` prints `"%-40s live %-3d copy %-3d %s %s"` per graph, sorted, nothing when the copy is current; `sync` prints `synced N records, set aside M graphs` and one line per set-aside graph with its versions, its aside file and the reason; a refusal is one line, exit 1 (`refused: another sync or move holds the copy's lock sync.lock (nothing was written)` for the lock). `--data` is no longer required by argparse; the other commands still stop with a usage error without it.
- `specs/mia/architecture.sysml`: the storageLayer doc says what T-03 built. `check_sysml_model.py` OK; `check_sysml.sh specs/mia/architecture.sysml` 0 errors, 0 warnings.
- Unit tests in `tests/test_graph_store_transfer.py`, class Sync (5): a copy-only graph set aside and removed header first, a differing record outside every graph refused before any write, the lock held in the same process, the `sync` command naming the aside file, `sync` without `--copy` a usage error. **Written after the code and not seen red** (deviation from test-first; the acceptance checks were red before).

**Tests green (my runs, feedback only):** `tests/acceptance/test_transfer_sync.py` 8 of 9 + 1 skipped (TC-SLY-031 is T-04; TC-SLY-030 skipped until VIEW); `test_transfer_move.py` 7/7 (TC-SLY-021 whole); `test_transfer_interrupt.py`: TC-SLY-038 green, TC-SLY-029/036 red only at `run='one-graph move'` (files, postgres; T-04), the sync cases green; `test_transfer_sets.py` 3 of 6 (TC-SLY-039 and, early, TC-SLY-033, 037; TC-SLY-032, 034, 035 are T-05); `tests/test_graph_store_transfer.py` 14/14; `tests/test_migrate.py` 10/10.

**Regression set (2026-11-23, sequential, runner `/home/maldun/.claude-work/jobs/85fdeba4/tmp/regress03.sh`):** unit suite `discover -s tests` 2575 tests OK (skipped 5, expected failures 2). Acceptance scripts one by one compared with a clean `git archive` export of the T-02 commit (`/home/maldun/.claude-work/jobs/85fdeba4/tmp/acc03_new.txt`, `/home/maldun/.claude-work/jobs/85fdeba4/tmp/acc03_base.txt`): changes only in the transfer files above, plus `test_skill_run_view_browser.py` 1 failure on the branch (OK in the export); re-run alone twice on the branch: OK both times, so taken as a flaky browser check unrelated to storage (noted under Findings). `test_rules_rule_set.py` red only in the export (it asks git). Unchanged reds: `test_decide_guard.py`, `test_judge_calibration.py` (known). No new red.

**Deliberate-defect check (TR-TRANSFER-008),** runner `/home/maldun/.claude-work/jobs/85fdeba4/tmp/mutate_t03.py` (patches the module in the test process; code on disk unchanged):

| Defect | Check | Result |
|---|---|---|
| removal before the aside file (cut back, then the aside file) | TC-SLY-026 | fails at line 181: after the fault the copy no longer holds its version 2 |
| header removed first (the prototype's whole-graph removal, header first) | TC-SLY-038 | fails: `sample.code` missing from the copy after write 3 |

**Traceability:** `trace_check.py --spec-dir specs/mia --tests-dir tests` gives the same 549 ERROR lines as the export (compared line by line); none new.

## T-04: Side records, one-graph move, interruptions

**What was done**
- `graph_store_transfer.py`: `move_graph(source, target, graph_id)` under the copy's lock when the target is a files folder (`_lock_of`; a database target has no copy lock): the graph checked first (`check_graphs`, REQ-SLY-021); every record of the graph (`_graph_records`: members named by any header version in either store, side records, header last) compared with the target: a target holding versions of its own of any of them is `StorageError("conflict", detail={"graph": id})`, and each record's source versions pass `storage_copy._check_entries` (what put would refuse), both before any write; then the lacking versions are appended record by record, header last. Answer `{"graphs": 1, "records": versions appended}`.
- Side records (REQ-SLY-030): `_side_records` adds, only where VIEW's tables are defined, one `graph_changes` record per header version (`<graph>/<version>`; a version kept without one has no record and none is made) and the `arrangements` record of the graph, before the header. Through `_graph_records` they also belong to the lag, the aside file, the cut back and the conflict check of the sync, so the T-03 question about differing records outside every graph now concerns only records no graph names (members of no header, `skills`).
- Unit tests in `tests/test_graph_store_transfer.py`, class OneGraph (5), **written first and seen red** (5 of 5 against the stub): lacking versions with the headers last and another graph untouched, a member of the copy's own is a conflict, an unknown kind is refused, a locked copy refuses the move, the side records listed only where their tables exist (table list patched in the test).

**Tests green (my runs, feedback only):** `test_transfer_sync.py` OK (1 skipped: TC-SLY-030, TR-TRANSFER-010); `test_transfer_interrupt.py` OK (every write position of the move, the one-graph move and the sync, files and postgres); `test_transfer_move.py` OK; `tests/test_graph_store_transfer.py` 19/19.

**Regression set (2026-11-23, sequential, runner `/home/maldun/.claude-work/jobs/85fdeba4/tmp/regress04.sh`):** unit suite 2580 tests OK (skipped 5, expected failures 2). Acceptance scripts compared with a `git archive` export of the T-03 state (`/home/maldun/.claude-work/jobs/85fdeba4/tmp/acc04_new.txt`, `acc04_base.txt`): only `test_transfer_interrupt.py` and `test_transfer_sync.py` turned OK; `test_rules_rule_set.py` red only in the export (it asks git); `test_skill_run_view_browser.py` OK this time. Unchanged reds: `test_decide_guard.py`, `test_judge_calibration.py` (known), `test_transfer_sets.py` 3 (T-05). No new red.

**Deliberate-defect check (TR-TRANSFER-008),** runner `/home/maldun/.claude-work/jobs/85fdeba4/tmp/mutate_t04.py`:

| Defect | Check | Result |
|---|---|---|
| one-graph move overwrites (the copy's own versions cut back and replaced, no conflict) | TC-SLY-031 | fails at its conflict assertion ("StorageError not raised") |

**Traceability:** 549 ERROR lines, the same as the export (compared line by line); none new.

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| `tests/acceptance/test_skill_run_view_browser.py` failed once in the full acceptance run and passed twice alone (not storage; not changed by T-03) | T-03 | none new: a protected check, reported for Verify; no change made |

## Plan amendments
None.

## Stop conditions hit
| Date | Task | Condition | Escalated to | Outcome |
|---|---|---|---|---|

## Unspecified behavior (decisions no requirement covers)
| Decision | Where in code | Proposed requirement or amendment |
|---|---|---|
| The command line text of a refused move: `refused: <graph>: <rule> <detail> (nothing was written)`, all graphs on one line separated by `; ` | `migrate._explain` | none proposed: same form as the existing `refused:` line of REQ-SLY-007 (finding F1 of G-V1); Verify may ask for an item under REQ-SLY-039's command texts |
| `cut(table, id, 0)` removes the record on both backends; a cut at or above the last version writes nothing | `FileBackend.cut`, `PostgresBackend.cut` | none: REQ-SLY-038 cuts a differing graph to its shared version; T-03 also removes a copy-only graph (and members without a shared version) by a cut to 0, so a removal counts as one write like any cut; the case is defined so both backends answer alike (REQ-SLY-022) |
| `put_file` takes a path relative to the store's root | `FileBackend.put_file` | none: follows REQ-SLY-027 (aside paths relative to the copy); the only caller is the sync (T-03) with paths it builds itself |

| The sync answer's `graphs` counts the graphs that were not current before the sync | `sync_store` | none: the plan fixes the field, not its meaning; Verify may ask for it in REQ-SLY-025's answer |
| `sync` prints one more line per set-aside graph (`  <graph>: versions [..] set aside in <copy>/<file> (<reason>)`); `lag` prints nothing when the copy is current | `migrate._copy_command` | proposed for REQ-SLY-039's command texts at the next amendment: the plan names only the summary line; the extra line names the aside file to the owner as FR-93 asks |
| `--data` is required per command, not by argparse, so `lag`/`sync` can take the live store from `--database-url` alone | `migrate.main` | none: follows the plan's `--data DIR` or `--database-url URL` |
| A differing record of the graph group that no graph names is refused (`conflict`) by the sync, not overwritten | `_refuse_other_conflicts` | open for Phase 4: REQ-SLY-025 says the copy equals the live store for every record of the group; since T-04 the side records belong to their graph, so this concerns only steps or connections no header names and `skills` records |
| `move_graph` takes the copy's lock only when the target is a files folder | `_lock_of` | none: REQ-SLY-028 locks the copy, which is always a files folder; a database has no lock file |

## Decisions
- T-01: `library-seed` does not run the per-graph check of the move; it keeps `copy_records`' checks and the write order (members first). REQ-SLY-009 asks for identical entries and the order, not for the graph check; a damaged library folder is refused by `copy_records` only where a record breaks put's rules.

- T-02: the format marker (`mia-store.json`, `{"format": 1}`) is **not** written in T-02 but in T-05. The plan names REQ-SLY-032 under T-05 and REQ-SLY-023 asks only for the flush; TC-SLY-023 allows either. If the marker were written now, it would have no reading side: an older set or a newer one (REQ-SLY-034, 035) would not be told apart, and every files store and library export would change its tree one task early. T-05 adds both sides together, through `put_file`.

## Open questions for Phase 4
- T-03: should the sync also overwrite (with an aside file) a differing graph-group record that no graph names, instead of refusing it? See Unspecified behavior.
- T-01: should `library-seed` also refuse a folder whose headers name missing members (the check of REQ-SLY-017)? Not asked by REQ-SLY-009; noted above.
