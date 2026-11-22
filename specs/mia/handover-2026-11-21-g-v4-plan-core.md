# Handover: G-V4, Plan in progress, CORE test spec written (2026-11-21)

Written for the next session. Read this first, then `CLAUDE.md` of the repository and the skills `dev-workflow`, `plan-phase`, `agent-app` (the MIA product contains an app agent; this goal touches the graph storage and the viewer). The owner is Stefan Reiterer (maldun). He decides every gate; never treat an agent report or silence as approval.

## 1. Where we are
Goal **G-V4** (graph rework, graph app, context-graph builder) is in **Plan**, run **subgoal by subgoal** (D-401). Order: **CORE, RULES, TRANSFER, RUN, VIEW, EDIT, REPLAY, CODE, MIGRATION, CONTEXT, BUILDER**. The living prototype (branch `prototype/g-v4`) is expanded per subgoal in rounds; the **reuse map stays unsigned** until the last subgoal so that rounds stay possible.

| Item | State |
|---|---|
| Explore | done (gate 2026-11-20) |
| Prototype round 01 (viewer data path), round 02 (graph path slice, 12 checkpoints), round 03 (CORE: context graphs, PostgreSQL, fault injection) | built, validated by the owner: round 02 41 outcomes met, FR-95 partly (the unreachable-live-store step was not tried, FB-2); round 03 FR-57, FR-60, NFR-16 met |
| Reuse map | drafted, decisions D-400, **unsigned** (the owner signed it by accident in Emacs and asked to restore it) |
| Accepted cases | 36 approved by the owner at once; the Witnesses column is empty and is filled from the CORE requirements (and later subgoals) |
| **CORE** high-level spec | **approved** 2026-11-21 (HR-001 to HR-005) |
| **CORE** requirements | **approved**, 21 requirements and 2 assumptions, reviewed one by one, lint clean |
| **CORE** test spec and test requirements | **written, not reviewed**: 22 scenarios, 9 test requirements, 31 items pending in the review log |
| CORE architecture entries, protected-test amendment, plan, binding pass | not done |
| RULES, TRANSFER, RUN, VIEW, EDIT, REPLAY, CODE, MIGRATION, CONTEXT, BUILDER | Plan not started (their TLS is approved and amended, see section 3) |

## 2. Where everything is
Two worktrees (never edit one session's files from another; name paths in every `git add`):
- `/home/maldun/prog/Python/MIA-goal-v4`, branch `goal/v4`, last commit `79d2e2e7`, clean: the specs and decisions (`specs/mia/review-log.md`, D-360 to D-406).
- `/home/maldun/prog/Python/MIA-prototype-g-v4`, branch `prototype/g-v4`, last commit `493aff3e`, clean: prototype code and its records (`specs/mia/goals/G-V4/prototype/`: `status.md`, `rounds/01..03/{run.md, prototype-report.md, validation.md}`). `goal/v4` is merged into it regularly (the last time after D-405 and the round 03 files).
- The main checkout `/home/maldun/prog/Python/MIA` (branch master) has unrelated untracked files; do not touch it.

Key files of this goal (all below `/home/maldun/prog/Python/MIA-goal-v4/specs/mia/goals/`):
- `G-V4/top-level-spec.md` (aggregate of the subgoal specs, generated, fingerprint `604223c1fd0f`), `G-V4/goal.md`, `G-V4/accepted-cases.md`, `G-V4/prototype/reuse-map.md`.
- `G-V4.GRAPHSTORE.CORE/{goal.md, high-level-spec.md, requirements.md, test-spec.md, test-requirements.md, review-log.md}`.
- `G-V4.EDIT/generality-review.md` (the editor generality and kind flag decisions, D-403 to D-405).
- `specs/mia/briefs/requirement-mode-sign-off.md`: brief for another agent (sign-off commands in the Emacs `requirement-mode`, `/home/maldun/prog/Lisp/requirement-mode`); not started, the owner decides when to hand it over.

## 3. Decisions of this session (full text in `specs/mia/review-log.md`)
- **D-400** reuse map: keep+tests R1 storage, R4 edit log, R6 page logic, R10 stand-ins; keep R11 fixtures; adapt R2 transfer, R3 rules, R5 backend, R8 editing panel, R9 checks; rewrite R7 page shell; none dropped.
- **D-401** Plan per subgoal with prototype rounds (03, 04, ...), each authorized by the owner in a `run.md` first; map unsigned until the end.
- **D-402** CORE HLS: first `/` separates graph and local ID; unused step versions after an interrupted save are accepted, no clean-up; a context graph is stored in round 03; no hard bound.
- **D-403** editor: one core, a **profile per graph kind**, workflow first, context later; context node types from a fixed list for now, builder categories later; copy a step only within the same kind; EDIT, RULES and VIEW plans follow the profile design.
- **D-404** the header field `kind` is the flag; one registry of kinds (rule set, profile, can it run, copy within kind); an unknown kind is listed and shown read-only, change, copy, restore and run refused.
- **D-405** the wording amendments applied: VIEW FR-48, FR-50; GRAPHAPI FR-63, FR-64; EDIT FR-72, FR-73, FR-92, FR-94 and scope; CONTEXT scope note and the open question which workflow rules are structural for a context graph (ASM-4 of round 03: identity and ends only).
- **D-406** NFR-16: after an interrupted move or sync a graph may be at an earlier complete version of the live history.

## 4. The prototype (how to run it)
- Python for every test: `/home/maldun/prog/Python/venvs/mia312/bin/python` (never create a venv in a repo or worktree). In the worktree `./proto.sh <script>` runs it.
- Backend checks: `./proto.sh proto_checks/cpN_check.py` for N = 1 to 12, 13 (`files` or `postgres`), 15 (`files` or `postgres`): all passed at the last run (cp1 10, cp2 10, cp3 20, cp4 25, cp5 21, cp6 7, cp7 14, cp8 24, cp9 19, cp10 20, cp11 21, cp12 6, cp13 10 on both, cp15 9 on both). Page tests: `node --test proto_checks/*.test.mjs` (59 at the last count). A stand-in browser harness: `proto_checks/e2e_page.mjs <base url> playback`.
- The viewer: `./proto.sh graph_proto_app.py --store files:<dir> [--live files:<dir>] --accounts <dir> [--aside <dir>] [--auto-sync] --port <n>`; sample store: `./proto.sh proto_checks/make_sample_store.py <new dir> [--broken] [--code]`; login `owner` / `secret` (the first account made is the owner).
- Sync and move: `./proto.sh graph_store_sync.py <live> <copy> [--lag] [--aside dir]`, `./proto.sh graph_store_move.py <source> <target>` with `files:<dir>` or `postgres:<url>`.
- PostgreSQL: only the throw-away container the tests start by name (`postgres:16`, never pulled). **Never** run commands that remove all containers: the owner's `mia_*`, `ollama` and `mia-searxng` containers run on this host.
- Known prototype gaps (all in the round reports): the arrangement table is not part of move and sync; a version is stored before its record of changes; editing of context graphs is out (editor check route applies workflow rules); the run uses stand-in steps and a trust check that trusts everything.

## 5. Open items for the owner and for the next steps
1. **Review of the CORE checks** (22 scenarios, 9 test requirements): `python ~/.claude/skills/plan-phase/scripts/req_review.py --spec-dir specs/mia/goals/G-V4.GRAPHSTORE.CORE next` serves them; record only what the owner answers (`mark ... --by "Stefan Reiterer" --result approved|"changes requested"|skimmed`).
2. **CORE architecture**: the requirements must appear in `specs/mia/architecture.sysml` and the node models (`trace_check` reports each new requirement as missing: Plan step 2); then the amendment of the three protected test files that fail with `unscoped_id` (`tests/test_graph_record_checks.py`, `tests/acceptance/contract/test_if_301_v2_graph_tables.py`, `tests/acceptance/test_graph_records.py`) as an amendment A-nn with the REQ-GTB-021 / A-92 text, the plan (`plan.md`, tasks T-01 .. for the reuse map rows R1, R4 and others), and the binding pass (`binding_check.py --presort`, then probes, then the owner decides; fill the Witnesses of the accepted cases).
3. **Round 03 sign-off:** `Validated by:` in `rounds/03/validation.md` and `Decided by:` in the carry-over table of `rounds/03/prototype-report.md` are the owner's signatures (round 02 is signed).
4. **Reuse map signature** only after the last subgoal's round (D-401); a signed date is the cut-off for prototype runs (PT12, PT13).
5. **Next subgoal: RULES** (HLS with the rule set per kind, FR-63, the refusal of a run by kind; prototype round 04 with its `run.md` authorized first). Then TRANSFER, RUN (the biggest unknown: networkx runner, equivalence), and so on in the order above. VIEW, EDIT and RULES follow the profile design (D-403, D-404).
6. FR-95 "live store not reachable" (FB-2) is a scenario for the test spec of EDIT; the owner may try it by hand.
7. The brief for the `requirement-mode` sign-off commands waits for the owner.

## 6. Working rules learned in this session (the owner's preferences)
- Decisions as a questionnaire, **one item per question**, the recommended option first; steps and results in the chat when asked ("give me the steps here").
- **Never sign for the owner.** Approval boxes (`[ ]`) and `Validated by`, `Decided by`, `Reviewed by` stay empty until the owner ticks or says so in the chat; then record it with the date and the way it was said. Prefer one approval box for a list.
- Test venv `mia312`; absolute paths when naming files; privacy is not a concern for now (personal use), untrusted web text still matters.
- Every finding gets a check; the prototype's own checks are never protected tests; the TLS changes only by proposal and the owner's decision (then regenerate the aggregate and add a fingerprint row to the current `run.md`).
- Commits end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; name the paths in every `git add`; never commit another session's changes.
- Leave the Emacs-edited sign-off files alone while the owner may have them open.
