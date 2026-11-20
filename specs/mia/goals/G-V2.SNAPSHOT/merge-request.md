## G-V2.SNAPSHOT: snapshots of the skill set, real provider, owner and pins (DRAFT, not for merge before the reports are signed)

**Goal:** G-V2.SNAPSHOT (subgoal of G-V2; supervised)   **Branch:** goal/v2.snapshot-prod → master (G-V2 has no `goal/v2` branch; its subgoals went into master, as STORE, MODEL, TOOLBOX and CONVERT did)
**Accepted by:** [X] maldun (owner: mark with an X; also the Agreement row in `goals/G-V2.SNAPSHOT/goal.md`)
**TLS:** specs/mia/top-level-spec.md (FR-47)   **HLS:** specs/mia/high-level-spec.md
**Goal record:** specs/mia/goals/G-V2.SNAPSHOT/goal.md
**Plan:** specs/mia/goals/G-V2.SNAPSHOT/plan.md (T-SN-01)
**Verification report:** specs/mia/goals/G-V2.SNAPSHOT/verification-report.md, on this branch (merged from `verify/g-v2-snapshot`, `dc739b24`). Round 1: Verified with accepted deviations (`b660b282`). Round 2 (`11e5ef5b`, `4fdcc896`, `64e956f4`, `693a5c48`): Verified with accepted deviations once F-08 is closed. Round 3 (`32fc1873`, `42043f16`, `eeef2346`; F-01, F-08, F-09): **Verified**, one info note N-1. **Signed by the owner (maldun, 2026-11-19)**, commit `281f1be8`.
**Implementation log:** specs/mia/goals/G-V2.SNAPSHOT/implementation-log.md

### Commits on the branch (oldest first)
`b660b282` production fork, `11e5ef5b` F-03 test and F-04, `4fdcc896` and `64e956f4` owner of the snapshots, `693a5c48` pins from the config, `32fc1873` F-08 example config and F-09 tests, `42043f16` F-08 config of the stack, `eeef2346` F-01 snapshot written once. Eight commits, 15 files, +486 -13 against master, then the merge request draft `36c27eca`, the merge of master `54f50e81`, the merge of the report branch `dc739b24` and the signature `281f1be8`.

### What changes
- Table `snapshots` in the record tables (IF-302 v14): versioned, not deletable; name, time, author, items (list) and pins (mapping) required, other fields kept (`record_tables.py`).
- `WorkflowLibrary` offers `snapshot`, `read_snapshot`, `list_snapshots`, `restore_snapshot` (IF-203 v2) on top of `SnapshotStore`; error codes `conflict`, `forbidden`, `not_found`, `invalid/schema` (name, snapshot). `pins()` and the test seam `fail_set_current_version_at`. `snapshots` is an internal kind: not in `KINDS`, so the graph API does not offer it.
- A stored snapshot is checked before the first write of a restore (nothing changes and no "before restore" snapshot is kept for a broken one); a failing way back is logged and the original error is raised (F-04).
- The owner of the snapshots in the running app is the account named by `owner_account` of the config, else the first account made (`accounts.owner_check`, `accounts.first_account`; owner decisions 2026-11-19). Before this every snapshot call in the app was `forbidden`.
- A snapshot is written once, atomically (F-01): a second write of the same name is `conflict`, also when two writers pass the name check together.
- A snapshot records the model pins of the config: light model as `MP-light`, full model as `MP-full` (`pins_from_config`; no digests, no model server needed).
- Earlier, already on master: `snapshot_store.py`, the pointer table `current_versions` (IF-302 v13) and the pointer in the library (`2c4b0915` and before).

### Requirements implemented
REQ-WFM-061 to 066 (take, list, restore without deleting a version, automatic "before restore of <name>" snapshot with suffix, trust and lifecycle written back with evidence, owner only). Checks: TC-WFM-061 to 066 (8 of 8), TC-IF-203-10 to 17 (16 of 16, the real rollback variant TC-IF-203-17 runs, no skip), TC-IF-302-11 and 12 (24 of 24). New tests: `tests/test_library_snapshots.py` (8), `tests/test_snapshot_store.py` (7), `tests/test_owner_account.py` (7), `tests/test_model_pins.py` (5); `tests/test_record_tables.py` updated (set of tables).

### Plan amendments
None in this branch. The protected tests and contracts it relies on came with A-121 and A-161 (`c939cc51`, `2b65f4dc`, `ac89f1f3`) and are already on master; this branch does not touch `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `benchmarks/`, `contracts/` or `eval/` (round 1 checked it against the merge base; round 2 to confirm).

### Frozen requirements unchanged (goal_check.py --parent-ref master)
No frozen-requirement finding. `goal_check.py --spec-dir specs/mia --parent-ref master` reports other errors that are not caused by this branch, see "Known issues".

### Resolved feedback items
None (no FB items).

### Agent changes (agent-app-commit)
No prompt, skill file, pipeline, tool, budget or model pin changed; no suite, baseline or red-team case touched; no eval run is needed for this merge. The "pins" of a snapshot are a record of the configured models, not a change of the pins in `eval-spec.md`.

### Known issues / accepted deviations
Accepted by the owner (maldun, 2026-11-19, recorded in the signed report): F-02, F-05, F-06, F-07, F-10, F-11. Fixed: F-01, F-03, F-04, F-08, F-09 (F-01, F-08, F-09 re-checked in round 3).
- N-1 (info, round 3): the file backend has no cross-process lock; two processes on one data folder could write the same snapshot name, the second overwriting the first. Accepted as a note by the owner.
- F-01 (medium): fixed in `eeef2346` (`expected_version=0` for the kind `snapshots`).
- F-02 (low): after a failed restore the transform meta fields `evidence` and `changed_by` are not changed back (version, trust and lifecycle are).
- F-05 (low): the failure seam keeps instance state, is not thread safe; the contract requires it.
- F-06 (info): `read`, `save`, `list_ids` accept the internal kind `snapshots` without an owner check; only `graph_api` blocks it.
- F-07 (info): TC-WFM-061 to 066 run on the in-memory lab; the real library is covered by the real variants of TC-IF-203-10 to 17 and `tests/test_library_snapshots.py`.
- **F-10 (info), accepted by the owner (maldun, 2026-11-19):** "first account" is not literally "the account that creates accounts" of REQ-WFM-066; only the CLI creates accounts today, so it is the same person; the requirement text is not changed.
- F-11 (info): an item that does not exist is refused only after the "before restore" snapshot is written; allowed by REQ-WFM-064.
- Fixed after round 1: F-03 (test), F-04. Fixed after round 2: F-08 (`owner_account` in `setup_cfg.example.json`, `deploy/setup_cfg.compose.json`, `deploy/README.md`), F-09 (tests for malformed stored snapshots).
Not done and not in this branch:
- No HTTP route calls the snapshot operations: the owner cannot yet take a snapshot from the app (a route is a new interface; decide whether it belongs to G-V2 or later).
- The owner changes by editing `owner_account` in `setup_cfg.json` and restarting; the model pins change with the config after a restart.
- Two accounts made in the same second are ordered by name (resolution of `utc_now` is one second).
- The failing tests `test_task_files_browser` (2) fail on master too and are unrelated.
- `goal_check.py` errors present on master and not from this branch: GL1 (two open iteration goals, G-V2 and G-V3: resolved when G-V2 is closed), GL3 (the scope items of G-V2.SNAPSHOT such as "REQ-WFM-061 to 066" and "IF-203 v2" are not parsed as ids; same for CONVERT and TOOLBOX), GL6 (G-V2.SNAPSHOT has no Phases table), GL4 warning (no agreement row of the subgoal in G-V2). Owner or goal-file fixes; none is a code issue.
- Owner items from the hand-over that this merge does not close: review-log rows (A-159 split, `c939cc51`), `deferred.md` TD-86, REQ-WFM-143, the five missing baseline files, the `verify_computable` record.

### Conflict resolutions
Not rebased: master was merged into the branch (`54f50e81`), no conflict, so the hashes the reports cite stay valid. `git range-diff ab8e8f4f..36c27eca master..54f50e81` marks all 9 commits `=` (same patch, only the base changed). The report branch was merged too (`dc739b24`, one new file). On the merged tip: `tests/test_storage_postgres.py` 43 of 43 OK; the whole suite has only the 2 known `test_task_files_browser` failures (also on master); `test_checkout_untouched` failed once only because the report was edited during the run and passes alone. Still to do by the owner before the merge: `bash tools/run_merge_gate.sh` (the tracked tree must be clean; stage 3 starts podman containers, `MIA_GATE_UPTO=3` only on an idle machine and after a backup).

### Merge
A person merges, after `merge_gate.py` shows the required checks green for the exact commit and the verification report is signed. The agent does not merge, tag or push.
