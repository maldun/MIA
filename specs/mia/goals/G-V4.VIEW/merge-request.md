# Merge request: G-V4.VIEW, graph viewer and the IF-104 v2 backend

**Goal:** G-V4.VIEW (subgoal of G-V4, supervised)   **Branch:** `goal/v4.view` → `goal/v4` (no version, no tag: a subgoal merge)
**Accepted by:** Stefan Reiterer (owner)   **Merged by:** the owner (agents hold no integration rights)
**TLS:** `specs/mia/goals/G-V4.VIEW/top-level-spec.md` (FR-48 to FR-55, NFR-10 to NFR-14) with the backend side of `../G-V4.EDIT/top-level-spec.md` and `../G-V4.REPLAY/top-level-spec.md` (D-430 (7))   **HLS:** `specs/mia/goals/G-V4.VIEW/high-level-spec.md` (HR-001 to HR-009)
**Goal record:** `specs/mia/goals/G-V4.VIEW/goal.md`   **Plan:** `specs/mia/goals/G-V4.VIEW/plan.md`
**Verification report:** `specs/mia/goals/G-V4.VIEW/verification-report.md` (verified with accepted deviations; both boxes ticked by the owner 2026-11-24, `56a122f7`)
**Implementation log:** `specs/mia/goals/G-V4.VIEW/implementation-log.md`
**Interfaces:** IF-104 v2 (`contracts/`, A-171, A-174), IF-302 v15 (A-172)
**Drafted:** 2026-11-25 by the agent (Commit phase); Merge: [ ] the owner

## What VIEW delivers
- **Track A (interface and backend):** every IF-104 v2 route in MIA's web application (`graph_api_v2.py`, N-2.1): list, read, versions, store, check, save as a new version, conflict and owner refusals, restore, arrangement, and the write-once record of changes. The store is the file store or PostgreSQL, chosen by the `store` setting. Both give the same answers in all 11 contract cases (33/33 on mock, files and PostgreSQL 16). New record tables `arrangements` and `graph_changes` (`record_tables.py`, IF-302 v15). The release image installs the database driver (REQ-OPR-011).
- **Track B (page):** the Graph app at `/graph/` (N-5, `graph_app/`, vendored vis-network 10.1.2, no build step). It has the owner's whole frame, with the areas of EDIT, REPLAY and RUN present but empty. It lists and filters graphs, draws every step and connection, names what can't be drawn, shows kinds by shape and words with one-word marks, and keeps stored text as text. The left column shows the selection read-only. It uses the saved arrangement, a fixed seed and a layered reset, keeps settings on the device, shows history and earlier versions, and works by keyboard in light and dark with the main app's tokens. It requests nothing from outside and writes nothing.

## Commits per task
| Task / item | Commit(s) | Requirements |
|---|---|---|
| A-171 (IF-104 v2 contract, mocks, suites), A-172 (IF-302 v15), A-174 (cases renumbered 17 to 27) | `23552a90`, `75d84491`, `de563198` (installed by the owner) | IF-104 v2, IF-302 v15 |
| Red tests, tag `plan-baseline-g-v4-view` | `82327296` | – |
| RULES brought in (`goal/v4` merged) | `b961c573` | – |
| T-01 Record tables | `3b7b8fb3` | REQ-RTB-010, 011 |
| T-02 Store setting, v2 provider, access, image | `15ad28fc` | REQ-API-018 to 022, 030, 045 to 047, REQ-OPR-011 |
| T-03 Read routes | `55f2d122` | REQ-API-023 to 029 |
| T-04 Save as a new version, refusals | `b276b250`, fix `7b945c1e` (V-5) | REQ-API-032 to 037, 048 |
| T-05 Check, restore, arrangement save | `c66550fb` | REQ-API-031, 041, 043, 044 |
| T-06 Record of changes | `dfd1dd94`, fix `e86ce702` (V-4) | REQ-API-038 to 040, 042, 051 |
| T-07 Tokens, frame, status | `87e47482`, fix `4fccc9c8` (V-10) | REQ-GA-012 to 018 |
| T-08 List and opening | `e1c82471`, fix `80c43641` (V-1, V-8) | REQ-GA-019 to 023 |
| T-09 The picture | `edac887e` | REQ-GA-024 to 029 |
| A-175 (TC-GA-025: another kind drawn with workflow shapes) | `6ca6206f` (staged), `fe03ab23` (installed) | – |
| T-10 Arrangement and settings | `d9e9aa1f`, fix `af76fb51` (V-2, V-9) | REQ-GA-030 to 035 |
| T-11 Left column and history | `a5ee04e5` | REQ-GA-036 to 040, 044 |
| T-12 The page in Firefox | `afe7861e`, layout after the owner's look `3f8463e8` (D-459), fix `976348e4` (V-13) | REQ-GA-041 to 043 and the browser checks |
| Commit phase: `goal/v4` merged in (docs only, D-471 to D-474) | `9fc48b7d` | – |
| Commit phase: requirements and checks moved into the node files; D-502 | `97524456` | all 70, REQ-GA-045 |
| Commit phase: test requirements and TD-91 to TD-95 staged, owner script | `7a07e15b` | TR-VIEW-001 to 021 |

The fix commits after Verify stay separate `fix: T-nn V-n` commits with their `Task:` and `Requirements:` lines, as RULES did (`f478e040`). Folding them in would rewrite history across `b961c573` and need a force push of the pushed branch. Nothing is squashed or rebased. The other commits are plan, verify and docs records.

## Requirements implemented
70 requirements (37 in Track A, 33 in Track B), all Verified. From this merge on, the node files are the source:
- `specs/mia/nodes/N-2-backend/nodes/N-2.1-api-and-accounts/requirements.md`: REQ-API-018 to 051 (groups SA, RD, WR, RC, AR, AF)
- `specs/mia/nodes/N-3-database/nodes/N-3.3-memories-history-feedback/requirements.md`: REQ-RTB-010, 011 (AR)
- `specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.2-operation/requirements.md`: REQ-OPR-011 (SA)
- `specs/mia/nodes/N-5-graph-app/requirements.md`: REQ-GA-012 to 044 (FL, LS, PI, AS, LC, QA), plus REQ-GA-045 (new at the merge, Deferred, TD-91)

The checks, contract cases, edge inputs, smoke rows and scenarios are in the node test specs of the same nodes. The witnesses of AC-009 to AC-016 and AC-035 are filled in `specs/mia/goals/G-V4/accepted-cases.md`. AC-014 is witnessed up to its save step, which is EDIT's (D-425 B). VAL-VIEW-01 stays in the goal's `test-spec.md`.

## Plan amendments
A-171, A-172, A-174, A-175 (installed by the owner). A-173 was dropped (D-436). No frozen requirement was changed by a joint amendment.

## Frozen requirements unchanged
`goal_check.py --spec-dir specs/mia --parent-ref goal/v4` finds no changed frozen requirement. The run without `--parent-ref` gives 98 errors: the 82 of the plan gate plus 16 GL2 errors in G-V4. These are moved requirements whose Parent is a goal-local HR item (for example REQ-API-018 → HR-004). The goal check reads HR parents only from the root `high-level-spec.md`. RULES left 27 of the same kind (D-420); the model generator already resolves them.

## Verification result and deviations (D-501, D-502)
- Fixed and re-verified: V-1, V-2, V-4, V-5 (narrowed), V-8, V-9, V-10, V-13. V-15 was closed by the owner's networked image build (keep the image tag `mia-view-check` until the merge).
- **V-3 handed to G-V4.GRAPHSTORE.TRANSFER:** a PostgreSQL store never reconnects, and MIA doesn't start while the database is down. MIA runs on files until TRANSFER's gate (D-460). The TRANSFER session writes the line in its record (D-501 (2)).
- Accepted: V-6 (the stale-version check is not atomic with the write; only the owner writes), V-12 (evidence gaps).
- Written into the specification at the merge (D-502):
  - V-7 and V-5: REQ-API-048 follows the code.
  - V-11: new REQ-GA-045, deferred as TD-91.
  - V-14: items 1, 10, 11 and 12a deferred (TD-92 to TD-95); the rest written as `Detail` lines.

## Checks on the merged branch (2026-11-25, venv `mia312`, one at a time)
| Check | Result |
|---|---|
| Update with the target | `goal/v4` (`f3e6243c`, 8 docs-only commits) merged in at `9fc48b7d`, no conflict |
| `test_view_backend.py` / `test_graph_view_files.py` | 9/9 / 2/2 |
| IF-104 v2 contract (Python) | 33/33: mock, files, PostgreSQL 16 under podman; none skipped |
| IF-104 v2 contract (JS) / IF-302 suite | 11 pass, 11 `[real]` skipped as planned / 28/28 |
| `graph_view_page.test.mjs` | 15/15 |
| `test_graph_view_browser.py` (Firefox) | 7/7 in each of three runs (13 s each) |
| `tests/js/*.test.mjs` | 230/230 |
| Unit suite | Ran 2590 in 490 s, OK (5 skipped, 2 expected failures; `test_delivery_on_stack` skipped, no model server) |
| Every acceptance script, one at a time | 76 scripts, 74 exit 0. The 2 reds are the known `test_decide_guard.py` and `test_judge_calibration.py` (G-V3.REPORT F-3) |
| Model | after the move: 668 node requirements; `check_sysml_model.py` OK; `check_sysml.sh` 4 files, 0 errors, 0 warnings |
| Traceability, before the move | 549, the same count as at the plan gate |
| Traceability, after the move | 637 now. After the owner's script it should be **585** (shown on a scratch copy), which is 549 − 3 + 38 + 1 |

What the 585 is made of:
- **−3, +38:** the three node test specs N-2.1, N-4.2 and N-5 had older checks and no `## Scenarios` section, which counted as one error per file. VIEW's scenarios add that section, so the same old gap now counts once per old check (TC-API-001 to 017, TC-GA-001 to 011, TC-OPR-001 to 010). No VIEW check is among them.
- **+1:** `SMOKE-VIEW-002 → NFR-11`. NFR-11 exists only in the goal's top-level spec, which the trace check doesn't read for node rows. The row is kept as approved.
- **The 52 between 637 and 585:** 47 VIEW checks still wait for their test requirements, and 5 `Relaxed: TD-nn` lines wait for the TD records. The owner's script installs both.

## What the owner runs
In this worktree (`/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-view`, branch `goal/v4.view`):
1. `bash tools/apply_merge_g_v4_view.sh` to look at the diff (`--report` for the readable form), then `bash tools/apply_merge_g_v4_view.sh --do`. It prints the number of trace errors about VIEW checks; expected: 1 (SMOKE-VIEW-002 → NFR-11).
2. Tick or change the five `Sign-off: [ ]` boxes of TD-91 to TD-95 in `specs/mia/deferred.md`.
3. `git add specs/mia/test-requirements.md specs/mia/deferred.md && git commit -m "plan: VIEW test requirements and deferrals TD-91 to TD-95 installed"`
4. `git push -4` (the branch tracks `origin/goal/v4.view`).

In the parent's worktree (`/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4`, branch `goal/v4`):

5. `git status` (clean), then `git merge --no-ff goal/v4.view`, then `git push -4`
6. Record the merge commit in VIEW's `goal.md` Phases row Commit (`done`, merge commit). The agent can do this on request.

## Checks after the merge (on `goal/v4`)
- `python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests`: 585
- `python3 -I tools/check_sysml_model.py .` and `bash tools/check_sysml.sh`
- VIEW's acceptance files, the IF-104 v2 contract (PostgreSQL), the Firefox checks
- whoever merges second among VIEW, TRANSFER and BUILDER: the unit suite and every acceptance script one at a time

## Notes for other subgoals
- **TRANSFER:** V-3 (reconnect, or open the PostgreSQL backend lazily, with a check on a real stopped container). Also F-1 of VIEW's Deploy (`migrate files-to-db` stops with a traceback on the `presets` files of the live volume): `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/note-f1-migrate-presets.md`. It also carries `arrangements` and `graph_changes`, and makes the store route's live and copy fields real (REQ-API-022).
- **EDIT:** the page side of the write routes and the arrangement save button. TD-91 (the notice for other errors), TD-92 (untrusted vs missing step), TD-93 (trust fields of a transform without trust), TD-94 (out-of-order answers). It may tighten REQ-API-048 (D-502 (1)).
- **CODE:** `changed_since_trusted` made real (REQ-API-028); TD-95 (the made-up toolbox reason).
- **BUILDER** (`explore/builder-workflow`): `git merge-tree` against this branch shows no conflict today. If both add rows at the end of `review-log.md`, keep both, ordered by decision number.

## Known issues / accepted deviations
- V-3, V-6, V-12; TD-91 to TD-95 (above).
- The owner's close look at the page in Firefox (the list in the report's "Notes for Commit, Deploy and Validate") moves to Deploy, with `store: database` (owner, 2026-11-25).
- SMOKE-VIEW-001 and SMOKE-VIEW-002 run in Deploy; VAL-VIEW-01 runs in Validate (G-V5, parked, D-386).
