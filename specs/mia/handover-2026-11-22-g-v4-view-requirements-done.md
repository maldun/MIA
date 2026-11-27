# Handover: G-V4.VIEW Plan, requirements approved; next the architecture entries (2026-11-22)

For the next session in the worktree `/home/maldun/prog/Python/MIA-goal-v4-view` (branch `goal/v4.view`, cut from `goal/v4`, not pushed). Read this file, `CLAUDE.md`, and load `dev-workflow`, `plan-phase` and `agent-app` (VIEW has no model step: FR-96 is out, so `agent-app-plan` adds nothing beyond the base). The owner (Stefan Reiterer, maldun) decides every gate. VIEW is one of the points where he is asked again (D-423). Decisions go as a questionnaire, recommended option first, review by group, never sign for him, full absolute paths, no plausibility records (D-421). He reads files in Emacs: open them with `emacsclient -n <file>` and leave them alone while he reads.

## 1. Where VIEW stands
| Item | State | Where |
|---|---|---|
| Design review (D-425, D-426, survey) and the owner's layout | committed | `specs/mia/goals/G-V4.VIEW/design-review.md`, `specs/mia/goals/G-V4/layout.drawio` |
| Goal update (statement, OC-1 to OC-8, scope incl. the backend side of EDIT and REPLAY items) | agreed (D-430, D-431) | `specs/mia/goals/G-V4.VIEW/goal.md` |
| High-level spec (HR-001 to HR-009, DEP-1 to DEP-9) | approved (D-432) | `specs/mia/goals/G-V4.VIEW/high-level-spec.md` |
| A-171 IF-104 v2 (11 routes under `/api/v2`, v1 unchanged), Python and JS mocks, contract suites | **installed** (D-433, D-434; store route fields of D-460) | `contracts/IF-104-graph-api.md`, `tests/helpers/mocks/if_104_v2_graph_api.{py,mjs}`, `tests/acceptance/contract/test_if_104_v2_graph_api.{py,test.mjs}`; drafts and `tools/apply_amendment_a171.sh` |
| A-172 IF-302 v15 (`arrangements`, `graph_changes`) | **installed** (D-435) | `contracts/IF-302-record-tables.md`, its mock and suite; `tools/apply_amendment_a172.sh` |
| A-173 | dropped (D-436); number unused | – |
| Requirements: Track A 37 (REQ-API-018 to 051, REQ-RTB-010, 011, REQ-OPR-011), Track B 33 (REQ-GA-012 to 044) | **all 70 approved** by group (D-437, D-438) | `specs/mia/goals/G-V4.VIEW/requirements.md`, `review-log.md` of the goal (70 reviewed) |
| Architecture entries, test spec with scenarios, test requirements, red tests, `plan.md`, binding map | **open** | – |

Red state at hand-over: the IF-104 v2 suite has 11 mock cases green and 22 real cases red ("graph_api_v2.create_app not built yet"; the PostgreSQL variant starts its own throw-away postgres:16). The JS suite has 11 pass and 11 skipped (the real side is the Python suite over HTTP). The IF-302 suite runs 28 cases with 2 errors: the real side of TC-IF-302-13 and -14, red until `record_tables.py` has the tables. The v1 suites are green.

## 2. Decisions of this session (full text in `specs/mia/review-log.md`)
- **D-430** goal update agreed; one goal with two tracks; v1 beside v2; Playwright for Python with Firefox (new dev dependency, own `requirements-browser.txt`, not in the image); empty labelled areas; store by configuration, shown read-only; **all IF-104 v2 routes real in VIEW** (asked twice); a blueprint in the MIA backend; `requirements-db.txt` in the image.
- **D-431** the main app's look: `templates/static/chat/tokens.css` copied unchanged into the graph page and kept identical by a check.
- **D-432** high-level spec approved; the effort is split within the goal into Track A (interface and backend) and Track B (page).
- **D-433** v2 holds only the routes of D-425 A plus `me` and `store` (toolbox, copy-step, run, sync come later from their subgoals); `GET /api/v2/store`; the check route is for the owner only.
- **D-434** A-171 text approved. D-460 (the owner, recorded on the RULES branch) crossed it and added `shown`, `live_reachable` and `lag` to the store route, with fixed values until TRANSFER.
- **D-435** the record of changes is written once, checked by the graph API (as for `snapshots`); no IF-102 change.
- **D-436** A-173 dropped: REQ-GA-001 never said "physics off" (only `tests/js/graph-view.test.mjs:69`); the fixed seed and solver are REQ-GA-031.
- **D-437, D-438** Track A and Track B requirements approved.

## 3. Next steps (the rest of Plan)
1. **Architecture entries** in `specs/mia/architecture.sysml`: the v2 provider in N-2.1 (satisfy the REQ-API items), the two tables in N-3.3 (REQ-RTB-010, 011), the page in N-5 (REQ-GA-012 to 044), the flows of IF-104 v2 between N-5 and N-2.1, REQ-OPR-011 in N-4.2, and the HR parents. Pattern: RULES' D-420 (`git show goal/v4.graphapi.rules:specs/mia/architecture.sysml`, its commit `df5ece13`). After every change run `bash tools/check_sysml.sh` (about 15 s) and `python3 -I tools/check_sysml_model.py .`.
2. **Test spec** `specs/mia/goals/G-V4.VIEW/test-spec.md`: one Given/When/Then scenario per check.
   - The installed contract cases are TC-IF-104-06 to 16 and TC-IF-302-13, 14.
   - New Track A checks:
     - store setting (REQ-API-019, 020);
     - refused record check (036);
     - written once (039);
     - lost record (040);
     - foreign origin on the real side (047);
     - the image smoke check (REQ-OPR-011, a SMOKE-VIEW id).
   - New Track B checks:
     - node tests of the page modules against the JS mock;
     - Playwright in Firefox: the frame and the empty areas, tokens identity and the style scan, light and dark, the same picture twice (REQ-GA-031), keyboard, nothing from outside, only GET requests;
     - the measured opening time of a graph of about fifty steps (a smoke number, no bound).
   - Pattern: `goals/G-V4.GRAPHAPI.RULES/test-spec.md` on `goal/v4.graphapi.rules`.
3. **Test requirements** `test-requirements.md` (TR-VIEW-nnn, setup kind with numbers: the stores, the fake fidelity of the mocks, the Firefox build and screen size, the fixture data of R11 plus `cp2.multi`, the "shown able to fail" step per check). Review them one check at a time.
4. **Red tests**, staged under `specs/mia/amendments/<A-174…>/` for an install script, as RULES did (its `red-tests/` folder). Before the Playwright tests: install the dependency (the owner approved it in D-430). Pin a Playwright release at least two weeks old in `requirements-browser.txt`, run `<venv>/bin/pip install -r requirements-browser.txt` into `mia312`, then `<venv>/bin/python -m playwright install firefox`. Track B fixtures: the prototype's `proto_checks/make_sample_store.py` (R11) into `tests/fixtures/`.
5. **`plan.md`**: the A-171 text and mocks are done; Track A tasks first (record tables, store setting and config, read routes, write routes after RULES' merge for check and rule refusal, record of changes, image), then Track B (tokens and frame, list, picture, arrangement and settings, left column and history, browser checks). Then the binding map with the accepted cases AC-009 to AC-016 and AC-035 (Witness column), and the plan gate.

## 4. Things to know
- **Dependencies on RULES:** REQ-API-031 (check route) and REQ-API-035 (`rules_broken`) need IF-301 v4. RULES is in Implement in `/home/maldun/prog/Python/MIA-goal-v4-rules` (branch `goal/v4.graphapi.rules`). Until it merges, the save path refuses with CORE's rules (`refused`).
- **TRANSFER** (planned on the RULES line, D-460) carries `arrangements` and `graph_changes` in move and sync. It also makes the store route's live/copy fields real. The one-graph move after a keep (FR-95, FR-81) gets its function signature agreed when TRANSFER is planned. VIEW owns the store setting and `requirements-db.txt` in the image.
- **The real provider's entry point** is fixed by the suite: `graph_api_v2.create_app(backend, accounts_store, store, allowed_origins)` (REQ-API-030). Accounts in the suites: `anna` is made first and is the owner, `ben` is the second account. With the real accounts, two accounts made in the same second go to the smaller name.
- **Mock fidelity:** the mocks know three rules only (`step_identity`, `connection_endpoints`, `cycle`), run no record checks, use a fixed toolbox and a counter for time. The JS mock rounds a half up, Python rounds half to even, so no case uses a half.
- **Checks of a goal folder:** `trace_check.py`, `goal_check.py` and `spec_check.py` read the product spec only. They report FR-48 and the other items of this goal's own top-level spec as unknown (GL3, GL10, HS1), as for CORE and RULES. Run the checks on a scratch folder with symlinks (CORE handover, section 5). `req_review.py --spec-dir specs/mia/goals/G-V4.VIEW` works and does not know HR items. The lint's L1-SUBJECT warning ("the API and accounts" under Subject WebApplication) is house style.
- **Staged suites** are run in a scratch overlay of the repository (symlinks to the top-level `*.py`, `library/`, `deploy/`, a copy of `tests/helpers`), because they find the repository root by their own path. Use `$CLAUDE_JOB_DIR/tmp`.
- A `! command` the owner types in a message is not run by the shell in this setup. He runs scripts himself (`bash tools/apply_amendment_aNNN.sh --do`), or he says "approved" and the agent runs his script on that explicit request.

## 5. Numbers (VIEW's blocks by D-460: D-430 to D-459, A-171 to A-184; check again before use)
Next free: **D-439, A-174, REQ-API-052, REQ-GA-045, REQ-RTB-012, REQ-OPR-012, TC-IF-104-17, TC-IF-302-15, TC-GA-017, TC-API-018, TC-OPR-011, SMOKE-VIEW-001, TR-VIEW-001**. These were counted on `goal/v4.view`, `goal/v4.graphapi.rules`, `master` and `prototype/g-v4`.

## 6. Open items for the owner
1. Older items from the CORE handover stay open: the date next to the CORE verdict tick, the round 03 sign-off in the prototype worktree, CORE V-4 and V-6, and the requirement-mode brief.
2. The stray `layout.drawio` in the main checkout (`/home/maldun/prog/Python/MIA/specs/mia/goals/G-V4/layout.drawio`) can go: the copy is on this branch.

## Start prompt for the next session
> Continue G-V4.VIEW Plan. Read `CLAUDE.md` and `specs/mia/handover-2026-11-22-g-v4-view-requirements-done.md`, load `dev-workflow` and `plan-phase`, work in `/home/maldun/prog/Python/MIA-goal-v4-view` (branch `goal/v4.view`). Start with the architecture entries, then the test spec with scenarios.
