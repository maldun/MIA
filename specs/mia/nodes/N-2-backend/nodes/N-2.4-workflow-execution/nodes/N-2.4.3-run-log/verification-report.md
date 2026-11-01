# Verification report: Run log (N-2.4.3)

**Goal:** G-V1 (iteration), supervised; node N-2.4.3 (leaf, low-2) of `decomposition.yaml`
**Branch:** goal/v1 @ 0568820 (node merged in d3735b2; node commits on master before 53c6766)   **Parent line of work:** master   **Plan baseline:** master 53c6766 plus installed amendments A-28, A-29, A-30, A-49
**Date:** 2026-10-31   **Reviewers:** – (human), Claude Opus 5.5 (AI, independent reviewer; did not see the implementation chat)

## Verdict (proposed)
**Verified with findings.** All five requirements and IF-401 have a test that passes and can fail, and nothing regressed against master. Two medium findings: the result of a task that asks questions keeps no steps for its account (F1), and no test notices if the replay stops comparing the result (F2). Neither blocks the merge if the owner accepts them as deviations; F1 should be fixed in G-V1.

## Automated checks
All runs in `localhost/mia:latest` (image 22619de57b4b) with `--network none`, on scratch checkouts of 0568820 and 53c6766. No model server and no eval runs (none in scope).

| Check | Result |
|---|---|
| Tests of the node: `test_run_events.py` (12), `test_run_log_files.py` (2), `test_run_log_node.py` (4), `test_events.py` (23), `test_run_explain.py` (16) | all OK |
| Contract suite IF-401 `tests/acceptance/contract/test_if_401_run_events.py` | 10 OK: 5 against the mock and 5 against the real `RunEvents` (A-29 adapter), none skipped |
| Neighbours: `test_runner_interfaces.py` (8), `test_pipeline.py` (26), `test_run_workflow.py` (12), `test_chat_backend.py` (41), IF-101 suite (60, 3 skipped as on master) | all OK |
| Full Python suite, failures per test, goal/v1 against master 53c6766 (171 modules each) | goal/v1: `test_benchmarks` (gate-time baseline not measured until T-06), `test_amendment_report` (no git in the image), `test_harness` (rt_edit 2 of 30 cases). These are the same on master, which also fails `test_config` (fixed on goal/v1). **No new failure.** |
| Protected material of the node vs master/amendments | IF-401 contract, mock and suite are byte-identical to the A-30 drafts; the `_RunEventsAdapter` in `tests/helpers/contract.py` is unchanged since A-29 (later changes there are A-32, IF-402); `contracts/IF-101-chat-api.md` is byte-identical to `amendments/A-49`. Nothing else changed. |
| Scope of the merge (`git diff d3735b2^1...d3735b2^2`) | `chat_service.py`, `tests/test_chat_backend.py` (D-138), `tests/test_run_events.py`, `tests/test_run_log_files.py`, the node's plan and log. Nothing outside the bounds that were agreed. |
| trace_check (node lines only) | 1 error: the node's `test-spec.md` has no `## Scenarios` section (M39). The same error is reported for 22 nodes. Every REQ-LOG and TC-LOG has markers in the tests. |
| test_doc_check (node tests) | node tests 0 findings; the IF-401 suite has 4×T2 and 4×T3 findings (known, D-138 (4)). |
| Model consistency `tools/check_sysml_model.py` | OK |
| Static / lint / types | none configured (CLAUDE.md) |
| Statistical checks, benchmarks, eval | none in the node's scope |

## Verification matrix
| Requirement | Method | Evidence | Result | Can the test fail? (mutation on a scratch copy) |
|---|---|---|---|---|
| REQ-LOG-001 account from event data, no model part | Test | `test_run_events.py` (TC-LOG-001, account = plain texts of events); IF-401 TC-01; chat: `test_chat_backend.py::test_a_chat_answer_keeps_its_steps_for_the_account` (A-49/D-138) | Pass, with **F1** | yes: account over all events → 3 + 1 fail; chat account read from `pipeline` only → chat test fails (the IF-101 suite stays green, F7) |
| REQ-LOG-002 typed events, run id, user, secrets removed, order checked | Test | `test_run_events.py` (incl. the real runner written through `RunEvents`), IF-401 TC-02, -03, -05; `test_events.py` | Pass, with **F3** | yes: no `redact` → unit + contract fail; no `clean_text` → unit fails; no check of `run_start` first → both fail |
| REQ-LOG-003 replay identical offline, comparison | Test | `test_run_log_node.py` (TC-LOG-003, baseline and decomposed lookup replay with no differences or divergences), `test_run_explain.py`; comparison `test_run_events.py`, IF-401 TC-04 | Pass, with **F2, F4** | partly: removing the result comparison of the replay (`reproduce.py:157`, `differences = []`) **survives**; compare with types only **survives**; a length difference that is ignored **survives**; removing divergences → `test_run_explain` fails |
| REQ-LOG-004 statements traceable to a query | Test | `test_run_log_node.py` (TC-LOG-004: 100 % on the recorded lookups; without `query_issued` events none links) | Pass | yes (the negative case is part of the test) |
| REQ-LOG-005 append-only files, no driver | Inspection, Test | `test_run_log_files.py` (AST import check of 5 files; the RunLog file only grows), `test_run_events.py` (file per run, a restart continues the seq); my inspection of `run_events.py` (`"ab+"`, no seek-and-rewrite) | Pass | yes: `"wb+"` → 7 + 3 fail in unit + contract; seq not resumed → unit fails |
| IF-401 v1 | Test | contract suite on mock and real, 10/10 | Pass | see above |

Plausibility: all results are exact checks on files or recorded runs; nothing is faster or better than it could be.

## Test requirements (M41)
The node has no `test-requirements.md` entries of its own. Contract suite against mock and real: met (10 tests, none skipped). Fake model: `test_run_log_node.py` uses the scripted `Lab` of `test_run_explain.py`, no network (met, ASM-N2-001).

## Goal acceptance (supervised goal; for information)
| Item | Result |
|---|---|
| Requirements in scope verified | 5 / 5 plus IF-401 (with findings F1–F4) |
| Protected checks identical to baseline or installed amendments | yes (A-28, A-29, A-30, A-49) |
| Nothing outside the node's parts touched | yes. `chat_service.py` (N-2.1) was changed by the owner's decision D-138 |
| Stops logged | yes: four questions in the hand-over, answered in D-138 |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | IF-101 v11 / D-138: "the steps of every answer" | The result of a task that asks questions (`needs` contains `ask`, e.g. `/review`) keeps no steps (F1) | Phase 3 |
| specified, not done | IF-401: keys like `password` "stored as `[removed]`" | Numbers, booleans and `None` under such keys are kept (F3) | owner decision, then Phase 3 or Phase 2 |
| done, not specified | `events.redact` exempts numeric values | not in IF-401, not in REQ-LOG-002 (F3) | as above |
| done, not specified | `events(run_id)` returns the events in file order; the contract says "in order of seq" | The two orders are the same under the single-writer rule (module doc). No action: a note | – |
| model | `architecture.sysml:518` part `runLog` lists `events.py`, `run_log.py`, `evidence.py`, not `run_events.py` (the IF-401 provider) | F5 | Phase 2 (model update) |

Human review: specification side through `review-log.md`; no item marked `Code review: needed`.

## Agent additions (agent-app-verify)
- A (protected eval material): no change to eval suites or baselines by this node. No skill or pipeline prompt changed, so no version bump was due.
- B, C, E, F (pins, suites, budgets, transcripts): not applicable. The node has no eval criterion, and the task excluded model runs.
- D (trust): `RunEvents` writes only to its own folder; the run id is checked against a plain-name pattern with no `..` (TC-IF-401-05), so no path traversal is possible. Untrusted text reaches the log only as data, after `redact`.
- E (replay): replay was exercised offline by `test_run_log_node.py` (recorded lookups, scripted model). See F2 for its weakness.

## Quality evidence per characteristic (M32)
| Characteristic | Evidence | Gap |
|---|---|---|
| Functional suitability | matrix above | F1, F2 |
| Reliability | a half-written last line is skipped and the next line is repaired (test, mutation M7 caught); a restart continues the seq | – |
| Security | secrets removed in the payload and plain text (tests, mutations caught); run id as a plain name | F3 (numeric secrets) |
| Maintainability | readable node tests (test_doc_check 0) | IF-401 suite T2/T3 (D-138 (4)); two docstrings do not match their code (F6) |
| Performance, compatibility, interaction, flexibility, safety | not now: no requirement of this node | – |

## Open deferrals (M26)
None in this node. Recorded debt: D-120 (replay and the task account read `RunLog`, the comparison reads IF-401; two formats side by side), D-138 (4) (a counter per run id for the life of the process; the IF-401 suite's test documentation), D-138 (1) (account from IF-401 by run id in the next iteration).

## Review findings
| # | Finding | Severity | Resolution / destination |
|---|---|---|---|
| F1 | `chat_service.py:527` `if event.get("plain") and not self._late:` drops every step of a task that asks questions (`late`, REQ-WFM-036, e.g. `/review`). Its result's account is "No steps were kept for this answer." This contradicts IF-101 v11 ("for every answer"), D-138 (1) and REQ-LOG-001 ("an answer produced by a task"). Reproduced with a probe test built on `tests/test_chat_tasks.py`: a task with `needs=("ask",)` → `[{'seq': 1, 'plain': 'No steps were kept for this answer.'}]`; the same task without `ask` → its two steps. | Medium | Needs a test, then Phase 3: a failing test in `test_chat_tasks.py` or `test_chat_backend.py`, then keep the steps of a late task too (the monitor update can stay). |
| F2 | The replay's result comparison is untested. With `reproduce.py:157` mutated to `differences = []`, `test_run_log_node.py` and `test_run_explain.py` stay green. `test_run_log_node.py:86-96` says "the difference is named" but asserts only `reproduced is False`, which divergences already cause. REQ-LOG-003 AC-4 ("replay equals the original") therefore rests on divergences only. | Medium | Needs a test (Phase 3, node test): assert `result["differences"]` is non-empty for a changed run, or a replay whose model calls match but whose result differs. |
| F3 | `events.py:48` keeps the value of a secret-named key when it is a number, boolean or `None`: `{"password": 123456}` is stored as `123456` by `RunEvents.emit` (probe). IF-401 says such keys are "stored as `[removed]`", and REQ-LOG-002 AC-4 says a secret does not appear in the log. Related: a bare `key` and `passphrase` are not matched, and `password=…` inside a plain text stays (the plain texts are code-made). | Low–medium (D-131 ranks privacy low; secrets are security) | Owner decision: (a) redact numbers too and keep counts under non-secret names (recommended; a failing test first); or (b) an IF-401 amendment that exempts non-string values. |
| F4 | `RunEvents.compare` (`run_events.py:108-114`): no test has two runs with the same types but different payloads (the "types only" mutation survives the unit and contract tests), and none has an extra event at the end (ignoring the length check survives). | Low | Needs a test: two cases in `test_run_events.py` (node test, free). |
| F5 | `specs/mia/architecture.sysml:518` part `runLog` does not list `run_events.py`, the provider of IF-401. | Low | Phase 2: model update. |
| F6 | Docstrings that do not match their code: `tests/test_chat_backend.py:380` gives the Example account as `[{"seq": 1, "plain": "thinking about it"}]`, but the test asserts `talk` first; `tests/test_run_log_node.py:87` "the difference is named" (see F2). | Low | Phase 3 docs fix with F1 and F2. |
| F7 | The IF-101 suite does not check v11: mutating `account` to read only `pipeline` keeps `test_if_101_chat_api.py` green (only the node test catches it). | Low | Amendment: a TC in the IF-101 suite for the account of an answer without a status block. |
| F8 | The node's `test-spec.md` has no `## Scenarios` section (trace_check M39). This is systemic: 22 nodes. | Low | Phase 2, together with the other nodes. |
| F9 | The IF-401 suite fails test-doc rules T2 and T3 (known, D-138 (4)). | Low | recorded; amendment later |

## Accepted deviations
To be decided by the owner (candidates: F3 if option b, F8, F9).

## Not checked
- Stage logs or CI (`run_stages.py`, `merge_gate.py`): local runs only.
- The live app writing `<runs>/events` with a real model: no model server, by the rules of this task.
- `refactor_check.py` and `agent_config_diff.py`: there are no refactor commits in the node, and the node changed no agent configuration.
- Mutation testing by hand only (16 mutants; 7 survived: F2, F4; three replay mutants that drop one of the conditions of `reproduced` are covered by the others, and the `kind != "event"` filter of `account` is redundant because `pipeline_event` already drops those events).

## Notes for Phase 7
- Whether users find the account of a task (coarse steps) helpful, and whether the late task's missing account (F1) is noticed.

## Re-verification (2026-10-31)
**Branch:** goal/v1 @ f4da817 (fixes: branch v1-n243b, merged in 4be4367; commits 9b71f69, e4d678d, a633b60, 73037cb, 073ceab)   **Decisions:** D-138, D-144, D-146
**Reviewer:** Claude Opus 5.5 (AI, independent; did not see the implementation chat). Runs in `localhost/mia:latest` (22619de57b4b), `--network none`; mutants on a scratch `git archive` copy of f4da817 (removed afterwards). No model server, no eval.

### Per finding
| # | State | Evidence |
|---|---|---|
| F1 late task keeps no steps | **Fixed** | `chat_service.py:527` now `if event.get("plain"):`. Test `test_chat_tasks.py::test_a_task_that_asks_keeps_its_steps_for_the_account`: mutant "re-add `and not self._late`" fails it (1 failure); green on the real code. Steps before and after the question both survive (the answer of the user does not reset `_steps`). `test_chat_backend.py` and the IF-101 suite stay green under the mutant (see F7). |
| F2 replay result comparison untested | **Fixed** (test only) | `test_run_log_node.py::test_a_changed_run_is_reported_as_a_difference_and_not_as_a_replay` asserts status, the divergence and the lost `claim` / `draft`. Mutant `reproduce.py:156` `differences = []` fails it; green on the real code. |
| F3 numeric secrets kept | **Fixed, decided (D-144) and applied; D-146 applied** | `events.py:49` drops the type exemption; only `""` stays. Mutant "old type exemption" fails `test_events.py` and `test_run_events.py`; mutants "remove `\"\"` too" (D-146), "keep lists/dicts", "keep `None`" each fail `test_events.py`. Matches D-146 exactly: `""` stays, every other value (0, False, None, " ", list, dict) becomes `[removed]`. No production event payload carries a number under a secret-like key (grep). The "related" items (bare `key`, `passphrase`, `password=` in plain text) stay recorded, not part of D-144. |
| F4 compare: payloads, length | **Fixed** (test only) | Two tests in `test_run_events.py`; mutant "types only" and mutant "length ignored" each fail one; green on the real code. The IF-401 suite stays green under both (N1). |
| F5 model part `runLog` | **Fixed** | `architecture.sysml:518` lists `run_events.py`; `test_run_log_files.py::test_the_model_part_of_the_run_log_names_the_provider_of_if_401` fails when it is removed. |
| F6 docstrings | **Fixed** | `test_chat_backend.py:380` Example now matches the asserted account; `test_run_log_node.py` docstring names what it asserts. |
| F7 IF-101 suite does not check v11 | **Open** (recorded) | Protected suite; needs an amendment. Confirmed again: the F1 mutant keeps `test_if_101_chat_api.py` green. |
| F8 no `## Scenarios` in test-spec.md | **Open** (recorded, systemic) | trace_check still reports it (Phase 2, with the other nodes). |
| F9 IF-401 suite T2/T3 | **Open** (recorded, D-138 (4)) | test_doc_check: 4×T2, 4×T3, unchanged. |

### New findings
| # | Finding | Severity | Needs | Proposal |
|---|---|---|---|---|
| N1 | The IF-401 contract suite does not pin the D-144 rules: `tests/acceptance/contract/test_if_401_run_events.py:42` checks only a string secret, `:64` only an extra middle event. The F3 mutant and both F4 mutants keep the suite green on mock and real; only node tests catch them (same kind as F7). | Low | amendment (protected suite) | With the F9 amendment: a numeric secret and `""` in TC-IF-401-02, a same-types/other-payload case in TC-IF-401-04. |
| N2 | `contracts/IF-401-run-events.md:10` says secret-named keys "are stored as `[removed]`" with no exception; the code keeps `""` (D-146). Not a leak (an empty text holds no secret, REQ-LOG-002 AC-4 is met), but the contract text and the code differ. | Low | amendment (contract wording) or accepted deviation | Add "(an empty text stays `""`, D-146)" to the IF-401 row at the next IF-401 amendment. |

No correctness, interface or security problem in the five fix commits. Scope: only `chat_service.py` (N-2.1, allowed by D-144), `events.py`, `architecture.sysml`, node tests and the node log; no protected file changed.

### Check results
| Check | Result |
|---|---|
| Node tests: `test_run_events.py` (15), `test_run_log_files.py` (3), `test_run_log_node.py` (4), `test_events.py` (23), `test_run_explain.py` (16), `test_chat_tasks.py` (12), `test_chat_backend.py` (41) | all OK |
| IF-401 suite `test_if_401_run_events.py` | 10 OK (mock and real) |
| IF-101 suite `test_if_101_chat_api.py` | 60 OK, 3 skipped (as before) |
| Neighbours: `test_pipeline.py` (26), `test_runner_interfaces.py` (8), `test_run_workflow.py` (12), `test_content_store.py` (12) | all OK |
| Mutants (9 on the scratch copy) | all 9 killed by node tests (F1, F2, F3, F4a, F4b, F5, three D-146 variants) |
| trace_check (node lines) | 1 error: no `## Scenarios` (F8); WARN TD-01..TD-04 not listed (system-wide deferrals of other nodes, same warning on every node report) |
| test_doc_check | node tests 0 findings; the new tests in `test_events.py`, `test_chat_tasks.py`, `test_chat_backend.py` have no finding (older tests in those files have, not this node's); IF-401 suite 4×T2, 4×T3 (F9) |
| `bash tools/check_sysml.sh specs/mia/architecture.sysml` | ok, 0 errors, 0 warnings |
| `python3 -I tools/check_sysml_model.py .` | OK |
| Full suite | not rerun by me; the implementation log reports only the known failures (`test_amendment_report`, `test_harness` rt_edit) |

### Proposed status
**Verified with accepted deviations (proposed).** F1 to F6 are fixed, each with a test that fails against the mutant of the first report and passes on the code; D-144 and D-146 are applied as decided. Open items are all low and on protected or plan material (F7, F8, F9, N1, N2): they need amendments, not code, and none affects REQ-LOG-001..005 or the IF-401 / IF-101 behaviour. Candidates for accepted deviations: F7, F8, F9, N1, N2 (or N1 and N2 joined to the F9 amendment).
