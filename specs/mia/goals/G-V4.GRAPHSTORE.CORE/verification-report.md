# Verification report: G-V4.GRAPHSTORE.CORE (one stored truth for graphs)

**Goal:** G-V4.GRAPHSTORE.CORE (subgoal of G-V4.GRAPHSTORE), supervised, accepted by Stefan Reiterer (owner)
**Branch:** `goal/v4` @ 137fbaf4 (code as of b9f50875; Implement started at a16465e4)   **Plan baseline:** `plan-baseline-g-v4-core` (3e43ff1c)
**Date:** 2026-11-22   **Reviewer:** an independent AI reviewer (Opus 5.5, fresh context, never saw the implementation chat); a person has not yet read this report

## Verdict
**Proposal: verified with accepted deviations**, on condition that the owner decides V-1 (medium). Every one of the 22 requirements in scope has a green check that ran under its test requirements; protected material is unchanged except the four A-168 scripts, which are byte-identical to the approved staging copies; nothing outside `graph_tables.py`, `graph_model.py` and tests was touched. V-1 is a real gap: an **unchanged** save after an interrupted save writes a new step version and a new graph version (against REQ-WFM-149). It comes from a word in REQ-WFM-148 that can be read two ways. V-2 to V-4 are the implementer's open questions, now confirmed by probes; they are unspecified behaviour, not defects.

- [X] Verdict decided by Stefan Reiterer (owner). Date:

## Automated checks (all run by me in `/home/maldun/prog/Python/MIA-goal-v4`, Python 3.12 venv `mia312` with psycopg 3)
| Check | Result |
|---|---|
| Unit suite `unittest discover -s tests` | Ran 2526 in 482 s: 1 failure, skipped 5, expected failures 2. The failure, `test_checkout_untouched`, saw the gitignored `mia.log` change. My acceptance scripts were writing to it in the same worktree at the same time. Run alone: OK (1 test, 88 s). Not a finding of the goal |
| Acceptance scripts, each run as a script (44 + 19 contract) | All exit 0, except `test_decide_guard.py` and `test_judge_calibration.py`: `AttributeError: module 'behaviour' has no attribute 'FUNCTIONS'` on import. These are known and pre-existing (G-V3.REPORT F-3, also red on a16465e4 per the handover), not CORE |
| CORE checks | `test_core_scoped_ids.py` 6 OK, `test_core_save.py` 6 OK, `test_core_context_and_history.py` 8 OK, `test_core_both_stores.py` 6 OK; no skip in any of the four logs, so the PostgreSQL 16 halves ran |
| IF-301 suites | `test_if_301_graph_tables.py` 8 OK, `test_if_301_v2_graph_tables.py` 44 OK (TC-IF-301-25, -26 included), no skip |
| Regression set of A-168 | `test_graph_records` 20, `test_graph_model` 10, `test_graph_run` 4, `test_graph_run_stages` 5, `test_graph_order` 4, `test_pipeline_graph` 6, `test_skill_binding` 4: OK; the unit modules named in the plan are inside the unit run above; IF-102 `test_if_102_storage.py` 24 OK, and on PostgreSQL (`tools/contract_postgres.sh`) 12 OK |
| SMOKE-CORE-001 `tests/smoke/smoke_core_graphs.py --server <throw-away>` | **green**: files and PostgreSQL, workflow and context graph, 3 versions by 3 accounts each, each read as saved; temp folder removed, `mia_smoke` dropped. Server was a throw-away `postgres:16` container (tmpfs) named `mia-core-smoke-<pid>`, stopped and gone afterwards. The run on the owner's server belongs to Deploy |
| My own mutants of the save path (scratch worktrees, removed) | header written first: caught (TC-WFM-164, 165, 166, 167, 168, 169); every member rewritten: caught (TC-WFM-165, 166, 167, 169); unchanged-graph shortcut removed: caught (TC-WFM-167, 169) |
| Protected material vs. `plan-baseline-g-v4-core` | only `tests/acceptance/test_graph_context_tables.py`, `test_graph_document_size.py`, `test_graph_node_fields.py`, `test_graph_record_identity.py` changed, each byte-identical (`cmp`) to `specs/mia/amendments/A-168/tests/acceptance/` (A-168, D-412). `tests/helpers`, `tests/smoke`, `contracts`, `benchmarks`, `eval/suites`, `eval/baselines`, `test-requirements.md`: unchanged. No `skip`/`xfail` added |
| `trace_check.py` (temporary folder with the CORE `*.md` and `specs/mia/architecture.sysml`, as in the handover) | 30 errors, none names a CORE item (requirement, TC-GTB-033..036, TC-WFM-162..178, TC-IF-301-25/26); the same count the handover measured on a16465e4 |
| `goal_check.py --spec-dir specs/mia` | 11 errors, all in G-V2 / G-V3 records; CORE: only GL11 (size), decided in its split check. `--parent-ref` is meaningless here: no `goal/v4.graphstore` branch exists (see V-5) |
| `tools/check_sysml_model.py .` | OK (40 acceptance criteria); no `.sysml` file changed on the branch, so `check_sysml.sh` was not re-run |
| `test_doc_check.py` on the three new unit files | 0 errors, 0 warnings |
| Static, security, dependencies | no linter or SAST is configured (CLAUDE.md); no dependency or new import added; code read in full (below) |
| Refactoring commits, agent configuration, deployable build, usability | not applicable: no `refactor:` commit, no agent configuration changed, no user surface (Deploy runs SMOKE-CORE-001) |

## Verification matrix
| Requirement | Method | Evidence (run by me) | TR met | Result |
|---|---|---|---|---|
| REQ-GTB-029 scoped ID | Test | TC-GTB-033, TC-IF-301-25 (mock and real), TC-GTB-036 both backends | 005, 007 | Pass |
| REQ-GTB-030 header names own members | Test | TC-GTB-034, TC-IF-301-26, TC-GTB-036 | 005, 007 | Pass |
| REQ-GTB-031 first slash separates | Test | TC-GTB-035 | 005 | Pass |
| REQ-WFM-160 no slash in graph ID | Test | TC-WFM-178, TC-GTB-036 | 005, 007 | Pass |
| REQ-WFM-144 local IDs on reading | Test | TC-WFM-162 | 005, 007 | Pass |
| REQ-WFM-145 history of a step in its graph | Test | TC-WFM-163; clause "only pinned versions" only by the unit test `test_a_steps_history_lists_only_what_its_graphs_headers_pin` (V-4) | 004, 006, 007 | Pass (clause: unit witness) |
| REQ-WFM-146 checked first | Test | TC-WFM-164 (green since the red commit, D-410), my header-first mutant caught | 005, 006 | Pass |
| REQ-WFM-147 header last | Test | TC-WFM-165, every write position, files and PostgreSQL | 001, 002, 003, 006 | Pass |
| REQ-WFM-148 changed members only | Test | TC-WFM-166; mutant caught | 004, 006, 007 | Pass as tested, see **V-1** |
| REQ-WFM-149 unchanged graph, no version | Test | TC-WFM-167; mutant caught | 004, 006, 007 | **Pass as tested; fails after an interrupted save (V-1)** |
| REQ-WFM-150 refused save writes nothing | Test | TC-WFM-168 | 005, 006 | Pass |
| REQ-WFM-151 repeating finishes | Test | TC-WFM-169, every write position, both backends | 001, 002, 003, 006 | Pass |
| REQ-WFM-152 kind selects tables | Test | TC-WFM-170, SMOKE-CORE-001 | 005, 007 | Pass |
| REQ-WFM-153 no kind means workflow | Test | TC-WFM-171; explicit `None` see V-2 | 005 | Pass |
| REQ-WFM-154 unknown kind refused | Test | TC-WFM-172, TC-GTB-036 | 005 | Pass |
| REQ-WFM-155 identity and ends of a context graph | Test | TC-WFM-173, TC-GTB-036 | 005 | Pass |
| REQ-WFM-161 empty context graph | Test | TC-WFM-173 | 005 | Pass |
| REQ-WFM-156 no workflow rules for context | Test | TC-WFM-174 | 005 | Pass |
| REQ-WFM-157 kind on reading | Test | TC-WFM-175 | 005 | Pass |
| REQ-WFM-158 versions with who and when | Test | TC-WFM-176, SMOKE-CORE-001; unknown graph see V-3 | 004, 008 | Pass |
| REQ-WFM-159 a version as saved | Test | TC-WFM-177 both backends, SMOKE-CORE-001 | 003, 004, 008 | Pass |
| REQ-GTB-032 same refusals in both places | Test | TC-GTB-036 files and PostgreSQL | 003 | Pass |

22 of 22 requirements have a green check. All results are plausible: the CORE scripts take 0.03 to 6 s; the fault-injection checks show that the injector fired at each position (TR-CORE-002), and the mutants show the checks can fail.

## Test requirements (M41)
| Test requirement | Source | Applies to | How I verified | Met? |
|---|---|---|---|---|
| TR-CORE-001 every write position | product | TC-WFM-165, 169 | code: `for k in range(1, writes + 1)` plus k = writes + 1; ran | yes |
| TR-CORE-002 injector shown to fire | product | TC-WFM-165, 169 | code: `(failing.fired, failing.writes) == (True, k - 1)` and the counted uninterrupted save; ran on both backends | yes |
| TR-CORE-003 both backends, skips visible | product | TC-GTB-036, 165, 169, 177, SMOKE | no skip in the logs; smoke on a throw-away PostgreSQL 16 | yes (smoke on the owner's server: Deploy) |
| TR-CORE-004 golden examples | product | 163, 166, 167, 176, 177 | the fixtures `tests/fixtures/graphs/` unchanged since the baseline | yes |
| TR-CORE-005 exact values | product | 13 checks | `assertEqual` on rules, fields, IDs, counts | yes |
| TR-CORE-006 shown able to fail | product | 163 to 169 | red at the baseline by assertion (164: D-410 defect); implementer's mutants (log T-01b, T-03, T-04); my three save-path mutants | yes |
| TR-CORE-007 fresh IDs and stores | product | 8 checks | `fresh_backend(kind, self)` per check | yes |
| TR-CORE-008 times not compared exactly | product | 176, 177 | `all(h["time"])`, `assertLessEqual` | yes |
| TR-CORE-009 smoke never writes live data | product | SMOKE | target name fixed to `mia_smoke`, the files store is a new temp folder; run against a throw-away server only | yes |

## Goal acceptance (supervised goal: for information)
| Item | Result |
|---|---|
| Requirements in scope verified | 22 / 22 (V-1 open on REQ-WFM-148/149) |
| Frozen requirements unchanged | CORE freezes none; IF-301 v3 installed by A-167 before the baseline |
| Protected checks identical to the baseline | yes, except A-168 (identical to the approved staging copies) |
| Nothing outside the goal's parts touched | the code diff a16465e4..HEAD touches only `graph_tables.py` (N-3.2), `graph_model.py` (N-2.3), unprotected tests and `tools/apply_amendment_a168.sh` |
| Stop conditions logged | yes: A-168 and A-169 were stops with the owner's decision (D-412, D-413), not work-arounds |
| Exit criterion OC-1 to OC-3 | OC-1: TC-WFM-176/177, smoke; OC-2: TC-WFM-163; OC-3: TC-WFM-165/168/169. V-1 touches OC-1 ("every edit a new version": here a non-edit becomes a version) |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-WFM-149 | after an interrupted save, the unchanged graph gets a new version (V-1) | Phase 2 (clarify REQ-WFM-148) + Phase 3 |
| done, not specified | explicit `"kind": None` refused as `schema_break` / `kind` | V-2 | Phase 2 or accept |
| done, not specified | `graph_versions` / `step_history` of an unknown graph raise `StorageError not_found` | V-3 | Phase 2 or accept |
| done, not specified | a workflow graph saved with an explicit `"kind": "workflow"` is read back **without** `kind` | in line with AC-CORE-17 ("keeps the shape it had before"); REQ-WFM-159 says "header fields exactly as saved", and `kind` is not listed as a header field | accept (info) |
| done, not specified | a member written by a refused save at Storage level (code `invalid` after the pre-check) is returned as a refused result; other Storage errors raise | consistent with REQ-WFM-150; the pre-check makes it unreachable in the tested cases | accept |

No item is marked `Code review: needed` in the goal. I read both changed product files in full.

## Quality evidence per characteristic (M32)
Touched: functional suitability (matrix), reliability (TC-WFM-165, 169 at every write position; V-1), compatibility (same refusals on files and PostgreSQL, TC-GTB-036, smoke). Not touched by this goal: performance efficiency, interaction capability, security, maintainability, flexibility, safety (pure storage logic without a user surface or new input path). `quality_check.py` not run (no goal-level `quality.md`).

## Open deferrals (M26)
None in the goal's scope. Won't-this-time items (cleanup of unused versions, D-402; context rule set, CONTEXT; transfer, TRANSFER) are decided scope, not deferrals.

## Review findings
Severity: High / Medium / Low / Info. The probes are outside the repo in `/home/maldun/.claude-work/jobs/85fdeba4/tmp/probe/`; they are deleted with this job, so the reproduction steps are given here in full.

| ID | Severity | Where | Finding | Reproduce | Destination |
|---|---|---|---|---|---|
| V-1 | Medium | `graph_model.GraphModel._write` | The save compares each member with the **newest stored** version of its record, not with the version the graph's newest header pins. Under ASM-002, an interrupted save may leave an unused newer version. If the user then saves the graph unchanged (equal to its newest version), the step is written again (same content as the pinned version), and a new graph version follows. This breaks REQ-WFM-149: no record and the newest version in the answer. It also adds a no-change entry to the step's history, against the rationale of REQ-WFM-148 ("real changes only"). REQ-WFM-148's text says "its newest version", so the code meets its letter; the two requirements together are ambiguous. No check covers the case: TC-WFM-167 saves twice without an interruption in between, and TC-WFM-169 repeats the same save, not the old graph | files store: save `memory.write@5` (v1); change `step.write` and save it through `FailingBackend(fail_at=2)` (the step is written, the header is interrupted); save the original v1 graph again → answer `version=2`, `graph_nodes` 6 → 7 versions, `graphs` 1 → 2 | Owner decides: (a) Phase 2 amendment: REQ-WFM-148 compares with "the version the newest header of the graph pins", plus a new check (next free TC-WFM-179); then Phase 3 (regression test first, then fix in `_write`); or (b) accept as deviation (rare: needs an interrupted save and then a save of the old content) |
| V-2 | Low | `graph_model._kind` | An explicit `"kind": None` is refused (`schema_break`, `kind`); REQ-WFM-153 only says "no kind" (implementer's question 1) | `save_graph({..., "kind": None})` → `SaveResult(False, …, 'schema_break', 'kind')` | Phase 2: say whether `None` counts as "no kind"; or accept as is (it is stricter) |
| V-3 | Low | `graph_versions`, `step_history` | For an unknown graph both raise the Storage layer's `not_found`; no requirement says what the answer is (implementer's question 3) | `graph_versions("nope")` → `StorageError not_found` | Phase 2 (an empty list or a named error), or accept; the callers come in later subgoals (VIEW, REPLAY) |
| V-4 | Low | TC-WFM-163 | The clause "only the versions the headers pin" of REQ-WFM-145 is witnessed only by an unprotected unit test; the protected check does not catch a mutant that lists every stored version (implementer's log, T-03; binding map D-411 (2) left it open) | log T-03 mutant | Binding map iteration 1 / Phase 2: make the unit test the named witness, or add the case to TC-WFM-163 by amendment |
| V-5 | Low | `goal.md` of CORE | The records disagree. The Line of work says `goal/v4.graphstore.core`, but the approved plan says `goal/v4`, and the work is there; no `goal/v4.graphstore` branch exists, so it is open where this subgoal merges in Commit. The Phases table still says Plan "open", though the plan was approved on 2026-11-21 | `git branch -a`; `goal.md` lines 11, 56 | Owner decides the line of work for Commit; then the agent updates `goal.md` (Plan done, Verify state) |
| V-6 | Info | `requirements.md` ASM-001 | The rationale says the refusal of a graph ID with a slash is REQ-GTB-031; it is REQ-WFM-160 | – | fix the reference with the next amendment |

## Accepted-deviation candidates
V-1 (if the owner picks (b)), V-2, V-3, V-6.

## Decisions on the findings (owner maldun, 2026-11-22, chat questionnaire; D-414)
- V-1: **accepted deviation** (option (b)): no amendment, no code change.
- V-2, V-3: accepted as implemented; the next amendment that touches the CORE requirements states them.
- V-5: the line of work is `goal/v4`, as the plan says; `goal.md` corrected (line of work, Plan done, Verify state).
- V-4, V-6: not asked separately; they stay open for binding map iteration 1 and the next amendment.

With these decisions the proposal is **verified with accepted deviations (V-1, V-2, V-3)**; the verdict box above stays the owner's.

## Notes for Commit and Validate
- Commit: the merge steps of `plan.md` (move the 22 requirements into N-3.2 / N-2.3, regenerate the model, fill the Witnesses of AC-001..003) and the target branch of V-5.
- Deploy: SMOKE-CORE-001 on the owner's running server.
- Validate: the round 03 signatures (`Validated by`, `Decided by`) are still open; they are the owner's.
- Environment caveat: I ran the unit suite and the acceptance scripts in parallel in the same worktree; only `test_checkout_untouched` was affected (shared `mia.log`), and it passed alone.
