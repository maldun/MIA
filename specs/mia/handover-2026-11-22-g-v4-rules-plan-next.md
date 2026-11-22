# Handover: G-V4, CORE through Deploy; next Plan of RULES (2026-11-22)

Written for the next session. Read this first, then `CLAUDE.md` of the repository and the skills `dev-workflow`, `plan-phase` and `agent-app` (the MIA product contains an app agent; RULES itself has no model step, prompt or eval suite, so `agent-app-plan` adds little beyond the base). The owner is Stefan Reiterer (maldun). He decides every gate; never treat an agent report or silence as approval. Previous handovers: `handover-2026-11-22-g-v4-core-implement-done.md` (CORE Implement), `handover-2026-11-21-g-v4-plan-core.md` (the Plan pattern per subgoal, still valid in its sections 4 and 6).

## 1. Where we are
Goal **G-V4** (graph rework, graph app, context-graph builder) is planned and built **subgoal by subgoal** (D-401). Order: CORE, **RULES**, TRANSFER, RUN, VIEW, EDIT, REPLAY, CODE, MIGRATION, CONTEXT, BUILDER.

| Item | State |
|---|---|
| **G-V4.GRAPHSTORE.CORE** | Explore to Deploy **done**; Validate open (first test run of G-V5, parked, D-386). Verified with accepted deviations V-1, V-2, V-3 (D-414); requirements moved into the node files N-3.2 and N-2.3 (status Verified), TR-CORE-001..009 in `specs/mia/test-requirements.md`; SMOKE-CORE-001 green on the owner's PostgreSQL server |
| **G-V4.GRAPHAPI.RULES** | **next: Plan**. `goal.md` agreed (2026-11-20), nothing else in its folder yet |
| TRANSFER, RUN, VIEW, EDIT, REPLAY, CODE, MIGRATION, CONTEXT, BUILDER | Plan not started |
| Prototype | rounds 01 to 03 built and validated; round 04 (RULES) not started |
| Reuse map | unsigned on purpose until the last subgoal (D-401) |
| Accepted cases | 36 approved; Witnesses filled for AC-001..003 (CORE); the RULES cases get theirs when its requirements exist |

## 2. Where everything is
- Worktree `/home/maldun/prog/Python/MIA-goal-v4`, branch `goal/v4` (not pushed, no upstream), last commit: this handover. CORE's line of work is `goal/v4` (D-414). Untracked `specs/mia/amendments/A-167/A-167.diff` is a view file: never commit it.
- Prototype worktree `/home/maldun/prog/Python/MIA-prototype-g-v4`, branch `prototype/g-v4` @ `493aff3e` (round 03 validated), clean. Merge `goal/v4` into it before round 04, as before.
- Main checkout `/home/maldun/prog/Python/MIA` (master): unrelated untracked files; do not edit. The owner's stack `deploy/` lives there.
- RULES material (below `specs/mia/goals/`): `G-V4.GRAPHAPI.RULES/goal.md`; the group's `G-V4.GRAPHAPI/{goal.md, top-level-spec.md, research.md (F3: the two rule sets today), spikes.md}`; `G-V4/prototype/reuse-map.md` row **R3** (adapt: `graph_rules_proto.py` of the prototype replaces the older `graph_rules.py` with five rules and takes over its tests; fix the definition of "session setting", ASM-3; `cp4_check.py` 25 pass); `G-V4/accepted-cases.md` (the cases with Outcome FR-63, FR-64); `G-V4.EDIT/generality-review.md` (D-403, D-404: one registry of kinds, the rule set per kind).
- CORE records for reference: `G-V4.GRAPHSTORE.CORE/{plan.md, verification-report.md, deployment-record.md, implementation-log.md}`.

## 3. Decisions since the last handover (full text in `specs/mia/review-log.md`)
- **D-414** CORE Verify: V-1 (an unchanged save after an interrupted save writes a new version, against REQ-WFM-149) is an accepted deviation; V-2 (explicit `"kind": None` refused) and V-3 (versions of an unknown graph raise `not_found`) are accepted as implemented and are to be stated by the next amendment that touches the CORE requirements; CORE's line of work is `goal/v4`.
- The owner ticked the verification verdict of CORE (the date field next to the tick is still empty: his).

## 4. Next: Plan of RULES
What RULES is (goal record): one set of **eight graph rules** in **one fixed order** wherever a graph is checked (saving, editing, before a run), every broken rule named with its steps or connections; a graph with a broken rule or a step input nobody supplies is refused before any step runs. Top-level items: FR-7 via the group spec's **FR-63, FR-64** (D-375: ids, kind of step, missing and duplicate connections, adjacency, one writer, session setting and stop limit, cycle last; plus a step input nobody supplies). Parts: N-3.2 (rules module and table checks, real), N-2.4.1 pipeline runner (check before a run, real), N-5 graph app (check route, stand-in against the mock).

Steps, in the pattern of CORE (handover of 2026-11-21, sections 1 and 5):
1. **Line of work first** (one question to the owner): `goal.md` says `goal/v4.graphapi.rules`; CORE worked on `goal/v4` (D-414). Recommend `goal/v4` again, or cut the branch.
2. **Prototype round 04** (D-401): write `specs/mia/goals/G-V4/prototype/rounds/04/run.md` **in the prototype worktree** (`/home/maldun/prog/Python/MIA-prototype-g-v4`; the round files live on `prototype/g-v4`, the folder on `goal/v4` is empty) (checkpoints of R3: the eight rules in order, the session-setting definition of ASM-3, the refusal before a run, the rule set by kind of D-404), and have the owner **authorize it before any prototype code**. Then build, run `cp4_check.py` and the new checks, validation sheet, report.
3. **High-level spec** of RULES (`G-V4.GRAPHAPI.RULES/high-level-spec.md`): the rule set per kind (registry of kinds, D-404), where the check sits (save path in `graph_model.py`, editor check route, runner), hard bounds only if there are any.
4. **Requirements** (`requirements.md`, EARS, grouped, reviewed one by one in batches), then architecture entries, test spec with scenarios, test requirements, red tests, protected-test amendments where today's tests assume five rules, `plan.md`, binding map; batched review with `req_review.py`.

Things CORE leaves for RULES:
- `graph_model.py` now picks the rules by kind: `check_graph` (today's workflow rules, `graph_rules.py`) for `workflow`, `context_problems` (identity and ends only, REQ-WFM-155/156) for `context`; `MEMBER_TABLES` and `_kind` are the seed of the registry of kinds. RULES replaces the workflow rule set; the context rule set stays CONTEXT's (FR-75, ASM-4).
- TC-WFM-168 (refused saves) and TC-WFM-164 (checked before the first write) use today's rule names (cycle, two writers, unknown kind of step): if RULES renames or reorders them, those protected checks need an amendment, and the CORE requirements REQ-WFM-146/150 may need a wording amendment (and can carry V-2/V-3 with it).

## 5. Lessons from CORE (do it right the first time)
- **Merge move (Commit of a subgoal):** requirements, test-case rows, **smoke rows** and scenarios go into the node files; test requirements go into the protected `specs/mia/test-requirements.md` through an owner-run script (`tools/apply_merge_g_v4_core.sh` is the pattern), and their **groups must be rows of the one `## Groups` table at the top** of that file, not a table of their own (`trace_check.py` reads only that one). Before the owner runs `--do`, check the staging copy with `trace_check.py` on a scratch copy.
- **Checks of a goal folder:** `trace_check.py` and `binding_check.py` do not read `goals/*/`; run them on a temporary folder with symlinks (the goal's `*.md` + `specs/mia/architecture.sysml`, + `G-V4/accepted-cases.md` and the group's `top-level-spec.md` for the binding check). Over the whole `specs/mia` the count is **549 errors** after CORE (none about CORE; old goals, number gate, eval harness).
- **Regression runs:** the full unit suite takes about 8 minutes and the acceptance scripts (one by one, `tests/acceptance/` has no `__init__.py`) about as long; do not run them in parallel in the same worktree (`test_checkout_untouched` then trips over the shared, gitignored `mia.log`). Known reds: `test_decide_guard.py`, `test_judge_calibration.py` (import of `behaviour.FUNCTIONS`, G-V3.REPORT F-3).
- **Mutants catch what the red state does not show:** in Verify, three save-path mutants were each caught by their own check; plan an explicit "shown able to fail" step per check (TR like TR-CORE-006).
- **The owner's database:** it publishes no port (by design). A check against it runs in a throw-away container on `mia_default` with the worktree mounted read-only; the release image `mia:v0.2.1` has no psycopg, so mount `psycopg`, `psycopg_binary`, `psycopg_binary.libs` read-only from the `mia312` venv (same Python 3.12). Start it with `deploy/up.sh db-only` only with the owner's yes, and stop just `mia_db_1` afterwards (`db down` would remove the other stopped stack containers). Finding for TRANSFER's Deploy: the image needs `requirements-db.txt`, and no code reads `MIA_DATABASE_URL` yet.

## 6. Open items for the owner
1. The date next to the verdict tick in `G-V4.GRAPHSTORE.CORE/verification-report.md`.
2. Round 03 sign-off, in the prototype worktree: `Validated by:` in `/home/maldun/prog/Python/MIA-prototype-g-v4/specs/mia/goals/G-V4/prototype/rounds/03/validation.md`, `Decided by:` in `.../rounds/03/prototype-report.md`.
3. CORE V-4 (REQ-WFM-145's "only pinned versions" witnessed by a unit test only) and V-6 (ASM-001 cites REQ-GTB-031 instead of REQ-WFM-160): binding map iteration 1 / next amendment.
4. The brief `specs/mia/briefs/requirement-mode-sign-off.md` still waits for the owner.

## 7. Tools, numbers, working rules
- Test venv `/home/maldun/prog/Python/venvs/mia312/bin/python` (psycopg 3); never a venv in a repo or worktree. PostgreSQL tests start their own throw-away `postgres:16` (never pulled). **Never** remove other containers: the owner's `mia_*`, `ollama`, `mia-searxng` live on this host.
- Next free numbers (counted on `goal/v4`, `master`, `prototype/g-v4`; check again before use): **D-415, A-170, REQ-WFM-162, REQ-GTB-033, REQ-RUN-036, TC-WFM-179, TC-GTB-037, TC-RUN-036, TC-IF-301-27, AC-41**.
- Owner's preferences: decisions as a questionnaire (AskUserQuestion), one item per question, recommended option first, then the steps that apply each answer; never sign for him (`[ ]`, `Validated by`, `Decided by`, `Reviewed by`, `Verified by` stay empty until he ticks or says so; record how he said it); full absolute paths for files; privacy is no concern (personal use), untrusted web text still is; leave files alone while he may have them open in Emacs.
- Git: commits end with the Co-Authored-By line of the session; name paths in every `git add`; never commit another session's changes; protected files change only through the owner's scripts (writing their staging copies needs his yes when prompted); never push (denied anyway).

## Start prompt for the next session
> Continue G-V4 with the Plan of RULES. Read `CLAUDE.md` and `specs/mia/handover-2026-11-22-g-v4-rules-plan-next.md`, load `dev-workflow`, `plan-phase` and `agent-app`, work in `/home/maldun/prog/Python/MIA-goal-v4`. Ask me the line of work first, then draft the run.md of prototype round 04 for my authorization.
