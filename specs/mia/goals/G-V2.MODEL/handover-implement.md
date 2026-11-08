# Hand-over after Plan Step 4 of G-V2.MODEL (written 2026-11-07): what is left

Read `CLAUDE.md` first. Line of work `goal/v2.model`, worktree `.claude/worktrees/goal-v2-model`. Commit there, never `git add -A`, name the paths. The owner merges.

## State
- Plan Steps 0 to 5 are done. `plan.md` header says "Approved by the owner, 2026-11-07 (Plan Step 5)" (the older `handover-step4.md` still calls it Draft; the plan.md header is newer).
- Red tests are installed (commit `97146b4`): `tests/acceptance/test_graph_model.py` (10 tests, TC-WFM-040..049), `tests/acceptance/test_graph_run.py` (4 tests, TC-RUN-016..019), `tests/helpers/graph_model_fakes.py`. All 14 fail by assertion on the stubs `graph_model.py`, `skill_record.py`, `graph_run.py` in the repo root; no ImportError.
- Checks: `test_doc_check` has no finding in the new files; `trace_check` has no line for the 14 IDs; `goal_check` has none; `req_graph` has none for them. The 517 trace errors, the 2640 doc-check errors and the baseline red of the old suite (1831 tests: 4 failures, 61 errors, e.g. `test_accounts_api`, `test_api_events`, `test_audio_router`, `test_chat_backend`) are old and not ours.
- Tags (local, not pushed): `plan-baseline-it2-model` at `e169361` (red tests only staged in `red-tests/`), `plan-baseline-it2-model-installed` at `97146b4` (installed). The bare `plan-baseline-it2` is the owner's, set on master after every subgoal has its tests installed (`goals/G-V2/parallel-work.md`).
- The fake graph tables (`FakeGraphTables`) take the simplest shape: a dict keyed by (table, ID), a list of documents per key, versions 1..n, no rule enforced. Nodes are built only through `make_node`, `data_node` and the other builders in `graph_model_fakes.py`, so a field-name change is one place.

## Left to do
1. **Owner, now:** review the 14 red tests against their scenarios (batched, see `plan-phase` hand-over), then tell the agent whether the protected folders get the deny rules in `.claude/settings.json` (plan gate; agents cannot write `tests/acceptance` or `tests/helpers`, which is why the install was a script).
2. **Owner:** answer the open points below. Until then the tests do not depend on them.
3. **Owner, at the end of G-V2:** set `plan-baseline-it2` on master after STORE, TOOLBOX and CONVERT have their red tests installed. Nobody else sets it.
4. **Implement (new session, skills `dev-workflow`, `implement-phase`; `agent-app` only to know it does not apply):** tasks of `plan.md`, one per session, test-first, in this order:
   - T-01 graph rules (REQ-WFM-043..049, `graph_model.py`), T-02 skill record (REQ-WFM-040..042, `skill_record.py`; may run parallel to T-01),
   - T-03 run in topological order (REQ-RUN-016, 018, 019, `graph_run.py`, needs T-01), T-04 untrusted node refuses the run (REQ-RUN-017, needs T-03),
   - T-05 swap the fake for the contract-checked storage (TC-WFM-040, 041, 042, 044, 049 against the IF-301 v2 suite, no skip); blocked until G-V2.STORE is merged.
   Tests are protected: a wrong test or scenario means stop and report, never edit it.
5. Later phases (Verify to Validate) as `goal.md` records them; VAL-009 is written.

## Open points (owner has not answered; do not guess)
1. Field names of the node types (`data`: `value`, `parameters`; `transform`: `toolbox_id`; `master`: `stop`, `task`, maybe `toolbox_id`) are a proposal (answer to STORE, last section of `goal.md`). A change is a change in `graph_model_fakes.py` plus the stubs' docstrings.
2. Where the graph header, the membership of nodes in a graph version and the skill record live in the record form (five points, same section of `goal.md`).
3. `plan.md` module names, and whether STORE's write validation shares the rules of T-01.
4. `Quality:` lines for REQ-WFM-040 and REQ-RUN-017 (Q-5): not added, they would bring the approved requirements back into review.

## Rules that bite
- TR-MODEL-001..005 (`specs/mia/test-requirements.md`): fake gets the contract suite in T-05; every refusal has an accepted twin; TC-WFM-047 seeds 1 to 200, at least 60 graphs with and 60 without a cycle (now 100 and 100), order checked as "every edge points forward"; compare IDs and version numbers exactly, never message wording.
- Do not touch `contracts/`, `tests/smoke/`, `benchmarks/`, `eval/`, existing files in `tests/acceptance/` and `tests/helpers/`. IF-301 and IF-203 are Frozen at G-V2 (A-90).
- Reserved IDs for MODEL: D-200..219, A-100..109, TD-30..39, SC-20..29, REQ-WFM-071..089, REQ-RUN-020..029 (019 taken), VAL-009. `git merge master` first; on a conflict in `architecture.sysml` take master's and regenerate (`python3 -I tools/gen_node_requirements_model.py .`, `bash tools/check_sysml.sh specs/mia/architecture.sysml`).

## Commands
- One file: `python tests/acceptance/test_graph_model.py`; `python tests/acceptance/test_graph_run.py`.
- All acceptance files as stage 2: `rc=0; for f in tests/acceptance/test_*.py; do python "$f" || rc=1; done; exit $rc`.
- Checks: `python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests`, `goal_check.py --spec-dir specs/mia`, `python3 ~/.claude/skills/plan-phase/scripts/req_graph.py --spec-dir specs/mia --tests-dir tests`, `python3 ~/.claude/skills/dev-workflow/scripts/test_doc_check.py --tests-dir tests`.

## Update 2026-11-08 (after T-01 to T-04, STORE merged): owner's answers and the T-05 finding
- State: T-01 to T-04 done (`0fefbe3`, `23bbfe5`, `e282e65`, `5d5405f`); master with G-V2.STORE merged into `goal/v2.model` (`c95a30a`); `test_graph_model.py` 10 OK, `test_graph_run.py` 4 OK on the merged tree.
- **T-05 stopped (finding for TR-MODEL-001):** `FakeGraphTables` is a versioned key-value store (`put`, `get`, `versions`); the IF-301 v2 suite tests record checks and conversion (`check_record`, `to_object`, ...), so 0 of its 20 cases pass on the fake. The five TC tests hardcode `FakeGraphTables`, so they cannot run on the real `Storage` without a protected change. Nothing was changed. Probe: `fake_vs_suite.py` (scratchpad of the session).
- **Owner's answers (2026-11-08, asked in a questionnaire; to be written into `review-log.md` by the amendment):**
  1. T-05 path: plan amendment plus a new adapter test outside `tests/acceptance`. TR-MODEL-001 and T-05 are amended: the fake is checked against IF-102 plus the record rules (as `GraphStoreStandIn` does), and a new test file runs the five TC tests on the real Storage. No protected file changes. `skill_record.py` stops using the `skill_index` pseudo-table (`Storage.ids("skills")` replaces it) and needs an `author`.
  2. Node field names are confirmed as proposed (`data`: value, parameters; `transform`: toolbox_id; `master`: stop, toolbox_id, task optional).
  3. REQ-WFM-041 (skill listing and start from the record in `library.py`, `extension_loader.py`) becomes an own task T-06 after T-05, test first.
  4. No `Quality:` lines for REQ-WFM-040 and REQ-RUN-017; note the gap as known at Verify.
- Open points 2 (graph header, membership, skill record table) are answered by IF-301 v2: tables `graphs` and `skills` (D-264). Open point 3 was decided on 2026-11-07 (`plan.md`, "Decided by the owner").
- Next: draft the plan amendment (TR-MODEL-001, T-05 text, new T-06, adapter test file name) for the owner's review; then T-05, then T-06.
