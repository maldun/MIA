## G-V2.TOOLBOX: transforms kept by ID with trust status and lifecycle (no version, subgoal)

**Goal:** G-V2.TOOLBOX (subgoal of G-V2; supervised)   **Branch:** goal/v2.toolbox → master (there is no `goal/v2`; STORE and MODEL went into master the same way)
**Accepted by:** Stefan Reiterer (owner); verdict and deviations accepted by maldun, 2026-11-14
**Goal record:** specs/mia/goals/G-V2.TOOLBOX/goal.md
**Plan:** specs/mia/goals/G-V2.TOOLBOX/plan.md
**Verification report:** specs/mia/goals/G-V2.TOOLBOX/verification-report.md (verdict: Verified with accepted deviations F6, F7, F8 rest; six rounds, last on `ff44e2d`)
**Implementation log:** specs/mia/goals/G-V2.TOOLBOX/implementation-log.md

### What changes
- `toolbox.py` (new): transforms by ID with trust and lifecycle; an import from outside is stored untrusted and never runs; only the owner marks trusted; retired entries are not offered but can be a comparison reference.
- `workflow_library.py`: kind `transforms` (IF-203 v1).
- `record_tables.py`: tables `transform_meta` and `transforms`.
- Contracts: IF-203 v1 transforms, IF-302 v10 and v11, IF-102 v5 and v6 (A-110, A-111, A-112, installed by the owner).

### Requirements implemented
REQ-WFM-050 to 056, 067, 068, 070, 090 to 095; REQ-RTB-008, REQ-RTB-009.

### Plan amendments
A-110, A-111, A-112 (installed by the owner: `18218e0`, D-222, D-223, D-224). Not frozen requirements.

### Frozen requirements unchanged (goal_check.py --parent-ref)
`goal_check.py` on the merged tree: GL1 (two open iteration goals G-V2, G-V3) and GL3 (IF-302 in scope here, not in G-V2's scope); both known and outside this goal, GL3 needs a fix in `goals/G-V2/goal.md` by the parent. `--parent-ref` not run: there is no `goal/v2` branch.

### Resolved feedback items
none.

### Known issues / accepted deviations
- F6, F7 (`decomposition` stage red, same on master), F8 rest: accepted at the gate.
- Master's red G-V3.CHAT tests, identical on master: acceptance `test_chat_skill_turns.py` and `test_digest_score.py`, contract-real IF-201 `SkillTurnContract` (4 errors). They make the ladder's `acceptance` step fail and skip `contract-real`; run by hand, `contract-real` has the same 4 errors as master and 7 more tests (ours) that pass.
- REQ-RTB-001 (and its copy in `architecture.sysml`) still says "15 tables of IF-302 v8"; there are 17 tables at v11. A requirement text change, not made here: needs an owner decision (amendment).
- TC-RTB-008 and -009 have no `@pytest.mark.req` marker (WARN of `trace_check`).
- Historic install scripts and amendment notes (`tools/apply_*`, `amendments/A-11*-note.md`) still say IF-302 v8/v9 for the transform tables: left as they were written.

### Conflict resolutions after merge of master (`6050b84`)
Six files, all version numbers and table lists (G-V3 took IF-302 v8/v9 and IF-102 v4 first); owner decision: ours renumbered on top.
- `contracts/IF-302-record-tables.md`: ours v10 `transform_meta` (A-110), v11 `transforms` (A-112); master's v8, v9 (`skill_runs`) kept.
- `contracts/IF-102-storage-interface.md`: ours v5, v6; master's v4 kept.
- `record_tables.py`, `tests/test_record_tables.py`: all three tables listed.
- `tests/helpers/mocks/if_302_record_tables.py`, `tests/acceptance/contract/test_if_302_record_tables.py`: both sides' entries and tests kept (protected files; resolved by the owner's script, comments renumbered).
Checks on the merge: toolbox, record-table, workflow-library and IF-203/IF-302 contract tests pass; contract-postgres 12 tests OK; `toolbox.py`, `workflow_library.py`, the toolbox tests and the goal folder are identical to `1d811c2`; `trace_check`: 1200 findings against master's 1219, no new ERROR.
