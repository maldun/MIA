# Handover: start of G-V4.GRAPHSTORE.TRANSFER (Plan) (2026-11-22)

For a new session in the worktree `/home/maldun/prog/Python/MIA-goal-v4-transfer` (branch `goal/v4.graphstore.transfer`, created by the owner, cut from `goal/v4` **before** the RULES merge). Read this file, `CLAUDE.md`, the skills `dev-workflow`, `plan-phase`, `agent-app`. TRANSFER is planned **on the agent's own recommendations** (D-423): record each choice as taken by delegation; ask the owner only where noted below or where a choice changes an approved top-level item, needs a new dependency, touches the owner's live data or crosses a trust boundary. Approval boxes and sign-offs stay the owner's (`[ ]`). Decisions as a questionnaire, recommended option first; full absolute paths; no plausibility records (D-421).

This file is on `goal/v4.graphapi.rules`; after step 1 below it is on your branch too.

## 1. First step: bring in RULES
RULES is merged into `goal/v4` (`ae34260a`, 2026-11-22). Your branch was cut before it, so: `git merge goal/v4` (normal merge). TRANSFER needs RULES' registry of kinds (`graph_rule_set.kinds()`, IF-301 v4) for the unknown-kind refusal. If the RULES closing records (`goal/v4.graphapi.rules` after `ae34260a`) are not yet in `goal/v4`, read them with `git show goal/v4.graphapi.rules:<path>`.

## 2. Decisions already taken for TRANSFER
- **D-460 (owner):** (1) TRANSFER's Deploy runs only a smoke on a throw-away database `mia_smoke`; switching MIA to "live database + files copy" and moving the owner's data (volume `mia-data`) is a **separate later owner gate** after `tools/backup.sh`; until then MIA runs on files. (2) VIEW put the TRANSFER fields into IF-104 v2 (A-171, commit `97c7010e` on `goal/v4.view`): route `GET /api/v2/store` answers `{"store": "files"|"database", "reachable", "shown": "live"|"copy", "live_reachable", "lag": {"graphs": n, "since": time|null}}`, fixed values until TRANSFER (shown=live, live_reachable=reachable, lag 0/null); TRANSFER makes them real without a new interface version. (3) **Numbers:** this line uses **D-460 and up, A-185 and up**; used so far D-460 to D-462, A-185 → next **D-463, A-186**. VIEW has D-430 to D-459, A-171 to A-184.
- **D-460, taken by delegation when planning** (from the read-only survey of 2026-11-22):
  - move: fix the two current defects test-first (`migrate.py:77` copies `graphs` before `context_nodes`/`context_edges`; `storage_copy.copy_records` checks each record alone, so a header naming a missing step version is not refused, AC-005); the integrity check stays structural (`check_record` with stored versions), never the eight rules;
  - scope: move = all tables (as `migrate` does), sync = the graph group (`graphs`, `graph_nodes`, `graph_edges`, `context_nodes`, `context_edges`, `skills`, plus side tables); name the FR-58 reading in the plan review;
  - set-aside versions in an `aside/` folder in the copy's root (durable: fsync then rename), named in the sync's answer, a `lag`/`aside` command;
  - carry VIEW's side tables `arrangements` and `graph_changes` (A-172) by an explicit list in the transfer module (no contract change); tests run once VIEW is merged, skip while the tables are missing;
  - remove on the copy only after its aside file is durable, as an N-3.1 backend operation (no IF-102 change);
  - older sets: a format marker in the copy's root; a set without one is format 0: read when it holds only scoped record-form graphs, else refused naming MIGRATION's conversion step;
  - unknown kind: TRANSFER (not MIGRATION) refuses the whole move or sync naming the graph `unknown_kind`; `lag` lists it with its kind and `refused`;
  - the copy setting on top of VIEW's store setting (live = `MIA_DATABASE_URL`, copy = a folder), AutoSync at start and at an orderly stop, **off by default**; an unreachable live store is a report, not a failure; one sync at a time (lock file in the copy's root);
  - no prototype round 05 (rounds 02 and 03 suffice; record the deviation from D-401);
  - REQ-GA-008 ("export and seed") re-parented to FR-59 as a storage command (show it in the plan review).
- **To agree with VIEW/EDIT when planning:** the signature of the one-graph move after a keep (FR-95 / FR-81, VIEW took their backend side). Message the VIEW session (ListAgents) once your plan names it.

## 3. Facts and risks (from the survey; check again before relying on them)
- Top-level items (group spec `specs/mia/goals/G-V4.GRAPHSTORE/top-level-spec.md`): FR-58, FR-59, FR-93, NFR-15, NFR-16 (D-389, D-406 wording); also NFR-8 and REQ-GA-008. Accepted cases AC-004 to AC-008; AC-027 (FR-95) and AC-033 (FR-81) touch TRANSFER's mechanisms.
- Prototype: rounds 02 (CP2, CP3, CP9) and 03 (CP15) on `prototype/g-v4`; not covered: PostgreSQL as the live side of a sync, the side tables, older sets, the start/stop hook.
- CORE's Deploy lessons (handover `handover-2026-11-22-g-v4-rules-plan-next.md` §5): the owner's PostgreSQL publishes no port: a check against it runs in a throw-away container on `mia_default` with the worktree mounted read-only; start the database only with the owner's yes (`deploy/up.sh db-only`) and stop only `mia_db_1`; **never** remove containers (`mia_*`, `ollama`, `mia-searxng`); tests and smoke name `mia_smoke` and refuse any other target (a TR like TR-CORE-009).
- Stale text to correct in TRANSFER's records: `goal.md` Depends on (add RULES and VIEW), Parts (add N-2.1 for the start hook, N-3.3 for side tables), Scope rows; group TLS "Prototype decisions" (overtaken by rounds 02/03); G-V4 `goal.md:117` (no IF-102 amendment needed); IF-102 v8 table list (no graph tables named).
- Likely task cut (keep together, about 15 to 20 requirements): T-01 move integrity; T-02 the same answers on files and PostgreSQL; T-03 lag, one-way sync, aside, orphans, rerun after an interruption; T-04 side records and the one-graph move; T-05 portability and the format marker; T-06 copy setting, AutoSync, lock, unknown kind, SMOKE-TRANSFER-001.

## 4. Next steps (Plan of TRANSFER)
1. `git merge goal/v4` (section 1).
2. Step 0: update `G-V4.GRAPHSTORE.TRANSFER/goal.md` (scope rows, depends on, parts, outcome criteria), owner's agreement.
3. Step 1a: high-level spec (technology, dependencies, hard bounds only), decisions by delegation recorded, owner's approval box.
4. Then requirements by group, architecture (`tools/gen_node_requirements_model.py` resolves goal HR parents, D-420), test spec, test requirements, red tests, plan — the pattern is `specs/mia/goals/G-V4.GRAPHAPI.RULES/`.
5. Deferred from RULES (D-462): SMOKE-RULES-001 can run on the owner's host together with TRANSFER's Deploy.

## Start prompt for the new session
> Start G-V4.GRAPHSTORE.TRANSFER. Work in `/home/maldun/prog/Python/MIA-goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). First `git merge goal/v4`, then read `CLAUDE.md` and `specs/mia/handover-2026-11-22-g-v4-transfer-start.md` (if it is not there yet: `git show goal/v4.graphapi.rules:specs/mia/handover-2026-11-22-g-v4-transfer-start.md`), load `dev-workflow`, `plan-phase` and `agent-app`, and start the Plan on your recommendations (D-423).
