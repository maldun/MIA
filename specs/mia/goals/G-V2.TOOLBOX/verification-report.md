# Verification report: G-V2.TOOLBOX (toolbox and trust)

**Goal:** G-V2.TOOLBOX (subgoal of G-V2), supervised
**Branch:** goal/v2.toolbox @ 02f8785 (plus this report)   **Parent line of work:** goal/v2 (merge order STORE, MODEL, TOOLBOX, CONVERT)   **Plan baseline:** plan-baseline-it2-toolbox (installed state: plan-baseline-it2-toolbox-installed = d77858f)
**Date:** 2026-11-12   **Reviewers:** maldun (human, pending), Claude Sonnet 5.5 (AI, fresh session, did not see the Implement chat)

## Verdict (proposal, after the fourth round)
**Verified with open findings** (round 4, 2026-11-14, commit `bf253ce`): N4 is fixed and verified (the message of a failed `set_meta` after a first save is honest, the code is `store_failed`, nothing deleted, replace branch untouched). One new finding, N5 (info, Phase 3): the new text is not pinned by any test. Owner decision (maldun): pin the text and the reason clause. After that commit a reader checks that commit only. Deviations to accept at the gate: F6, F7, F8 rest. See "Fourth round" at the end. The verdict of the third round follows.

## Verdict (proposal, after the third round)
**Verified with open findings** (round 3, 2026-11-14, commit `ca3d8fa`): N1, N2 and N3 are fixed and verified; the protected material is unchanged; the ladder on `HEAD` is clean except F7 (known). One new small finding, N4 (low, Phase 3), goes back: the message of a failed new import says "was not stored" although the entry stays; no test covers that branch. Owner decision (maldun): fix the text and add a test. After that commit a reader checks that commit only; deviations to accept at the gate: F6, F7, F8 rest. See "Third round" at the end. The text below is the earlier rounds' verdict.

## Verdict of the first round
**Verified with open findings** (decisions of the batched review below; the findings F1, F2, F3, F4, F5 go back to Phase 3 before the merge). All checks of the scope are green, the protected material is unchanged apart from the approved installs, and no unapproved code path was found that runs untrusted text on import or lets a non-owner mark a transform trusted through the toolbox. One security finding (F1) is a gap in the owner rule and should be fixed before the merge; the others are small.

## Automated checks
| Check | Result |
|---|---|
| Acceptance and unit tests of the scope (venv `/home/maldun/prog/Python/venvs/mia312`, run as scripts) | `tests/acceptance/test_toolbox.py` 17 ok; `contract/test_if_203_v1_transforms.py` 10 ok (mock and real); `contract/test_if_203_workflow_library.py` 8 ok; `contract/test_if_302_record_tables.py` 18 ok; `tests/test_toolbox.py` 21 ok; `tests/test_record_tables.py` 17 ok; `tests/test_workflow_library.py` 13 ok |
| Skips | `-k _real` over all contract suites: 137 tests, 17 skipped. None belongs to this goal: real model server 6 (IF-103), real web client 5 (IF-404), real scholarly APIs 4 (IF-405), IF-101 2 (REQ-CHV-008, A-130). The IF-203 v1 transforms `_real` tests ran and passed (TR-TOOLBOX-001). |
| Stage ladder (`run_stages.py --upto 2 --keep-going`, local, not CI) | see "Stage log" below; a local run is feedback, only CI counts for `merge_gate.py` |
| Protected material vs baseline | clean: see section "Protected material" |
| `trace_check.py` | no error or warning names a requirement or check of this scope except 2 warnings (REQ-RTB-008, 009: "no `@pytest.mark.req` marker found"; the markers exist in `tests/acceptance/contract/test_if_302_record_tables.py` as `@mark.req("IF-302","REQ-RTB-00x")`, which the script does not read). The 536 errors are other nodes' (MODEL, CONVERT ids and old ids), known. |
| `goal_check.py` | GL1 (G-V2, G-V3) and GL3 (IF-302 not in G-V2's scope) as known; nothing else |
| `req_graph.py` | no error on a requirement of this scope |
| `req_review.py status` | the scope's items are in `review-log.md` as approved by maldun (TC-WFM-056 first "changes requested", then approved); requirements still carry `Status: Draft` in `requirements.md` (set in Commit) |
| `decomp_check.py` (step `decomposition`, stage 1) | FAILS: 76 errors on the branch, 70 on master. The 6 new ones are REQ-WFM-090..095 "no parent one level up (in N-2); Parent is 'FR-38'", the same class as the 64 old ones (F7) |
| `check_sysml.sh` (step `sysml-parse`) | pass (67 s) |
| `refactor_check.py`, `agent_config_diff.py` | 0 findings |
| Static / security | no bandit in the venv (not installed, no new dependency); manual: the one `exec` is `toolbox.py:130`; no `eval`, `compile`, `subprocess`, `pickle`, `importlib` in `toolbox.py`, `workflow_library.py`, `record_tables.py`. `jsonschema==4.23.0` was already pinned; `requirements*.txt` unchanged |
| Documentation, license/bill of materials, deployable artifact | not applicable to this goal (no user-visible surface yet, no release); Deploy is recorded `empty` by the goal |
| Usability (bad inputs) | `import_transform` refuses non-JSON, list, version 0/true, text `inputs`, empty id with `invalid_file` (unit test); the float version `1.0` is the exception (F3) |

### Stage log
Clean run on `HEAD` (`3b77fe8`, code as of `ca3d8fa`) by the third-round reviewer, 2026-11-14, `run_stages.py --stages stages.yaml --upto 2 --keep-going`, venv `bin` first in PATH, started from the session shell as a background command (the SIGINT tests passed this time). Not a CI run; only CI counts for `merge_gate.py`. It replaces the entry of the second round.

| Stage | Step | Result |
|---|---|---|
| 0 | model-ids | pass |
| 1 | contract-js, js, quality, contract-mocks | pass (contract-mocks 137 tests) |
| 1 | sysml-parse | pass (64 s) |
| 1 | decomposition | **fail**, F7 (known red, same class as master; decided D-229) |
| 1 | unit | pass: 2243 tests, 5 skipped, 2 expected failures (463 s), the shutdown tests included |
| 2 | acceptance | pass (11.6 s) |
| 2 | contract-real | pass (9.7 s), 17 skipped (none of this goal) |
| 2 | integration | pass (4.0 s) |
| 3 | contract-postgres | pass by hand, 11 tests (podman and the local `postgres:16` are there) |
| 3 | container-alone | pass by hand, 2 tests (image `localhost/mia:latest`, built 7 days ago, not rebuilt: it says nothing about `ca3d8fa`) |

`bf253ce` touches no file outside `toolbox.py`, `tests/test_toolbox.py` and `implementation-log.md`, so the ladder of `ca3d8fa` stands (checked by `git show --stat bf253ce`).

Stage 4 (eval runs on the pinned model) has no step by design (comment in `stages.yaml`). Slow stage 1: 529 s against a budget of 120 s (the unit step), a known tuning item.

## Protected material
`git diff --stat plan-baseline-it2-toolbox..HEAD -- tests/acceptance tests/helpers tests/smoke contracts eval benchmarks stages.yaml specs/mia/test-requirements.md`: 10 files. Every change maps to an approved install; against the installed state (`plan-baseline-it2-toolbox-installed`) only the A-111/A-112 installs remain:

| Commit | What | Approved by |
|---|---|---|
| d77858f | red tests, IF-203 v1 transforms suite, IF-302 transform_meta case (TC-IF-302-09), mocks, `toolbox_fakes.py` | Plan Step 4 install |
| 756bdbc | contracts IF-102 v5, IF-302 v9, `test-requirements.md` (TR-TOOLBOX-005 applies also to TC-RTB-009) | A-112 (D-224) |
| 6f8cd02 | suite case TC-IF-302-10 and the mock table `transforms` | A-112 |
| 18218e0 | `contracts/IF-203` v1 text | A-111 (D-223) |

`tests/smoke`, `eval`, `benchmarks`, `stages.yaml`: no change (they do not exist or are untouched). No `skip`/`xfail` in the new acceptance and contract files (only a docstring says the suite was skipped until T-06). No other change to protected paths (`git log` over those paths shows only the four commits). Result: **no finding**.

## Verification matrix
All checks ran green in this session. "Code" is the line in `toolbox.py` (T) or `workflow_library.py` (W) or `record_tables.py`.

| Requirement | Check (test) | Code | Test requirements | Result |
|---|---|---|---|---|
| REQ-WFM-050 one entry per ID, equal/lower version refused | TC-WFM-050 `test_toolbox.py:58` | T `import_transform` 66-82 | 001, 005 | pass |
| REQ-WFM-051 trust and lifecycle values exact | TC-WFM-051 `:73` | T `set_trust`, `set_lifecycle`; W `set_meta`; table `transform_meta` | 001, 005 | pass |
| REQ-WFM-052 import is untrusted whatever `status` says | TC-WFM-052 `:98` | T `import_transform` (field `status` dropped), W `_save_transform` | 001, 002 | pass |
| REQ-WFM-053 import runs no code | TC-WFM-053 `:109` | T `_checked` parses JSON only; `exec` only in `run` | 001, 002 | pass (inspected: no compile path on import) |
| REQ-WFM-054 only the owner trusts, any account untrusts | TC-WFM-054 `:122` | T `set_trust` | 001, 002, 003 | pass; see F1/F6 for what the owner rule does not cover |
| REQ-WFM-055 exchange form | TC-WFM-055 `:140` | T `EXCHANGE_SCHEMA`, `export_transform` | 001, 005 | pass; F3 float version |
| REQ-WFM-056 shipped, trusted, highest non-retired | TC-WFM-056 `:159`, real folder `:174` | T `seed_shipped` | 001, 004 | pass; D-226/D-227 decided |
| REQ-WFM-067 lifecycle, tested needs evidence | TC-WFM-067 `:211` | T `set_lifecycle` | 001, 005 | pass |
| REQ-WFM-068 retired runs as baseline | TC-WFM-068 `:226` | T `run` | 001, 005 | pass |
| REQ-WFM-070 retired not offered | TC-WFM-070 `:238` | T `offer` | 001, 005 | pass |
| REQ-WFM-090 reason shown | TC-WFM-090 `:252` | T `look_up`, `REASON_IMPORTED` | 001, 002, 005 | pass; F4 |
| REQ-WFM-091 baseline allowance | TC-WFM-091 `:267` | T `run`, `set_lifecycle` | 001, 002, 003 | pass; F1, F2 |
| REQ-WFM-092 newer version keeps trust and lifecycle | TC-WFM-092 `:289` | T `import_transform`; W `_save_transform` | 001, 002 | pass; F1 |
| REQ-WFM-093 event for a replaced trusted transform | TC-WFM-093 `:303` | T `import_transform` | 001, 006 | pass; F5 |
| REQ-WFM-094 shipped is not exported | TC-WFM-094 `:194` | T `export_transform` | 001, 004 | pass |
| REQ-WFM-095 only the owner allows the baseline | TC-WFM-095 `:317` | T `set_lifecycle` | 001, 003 | pass |
| REQ-RTB-008 table `transform_meta` | TC-RTB-008 = TC-IF-302-09 | `record_tables.py` | 005 | pass (mock and real) |
| REQ-RTB-009 table `transforms` (thin) | TC-RTB-009 = TC-IF-302-10 | `record_tables.py` | 005 | pass |
| IF-203 v1 kind `transforms` | TC-IF-203-05..09 | W 210-262 (`_read_transform` 213 to `_known_transform` 257) | 001 | pass on mock and real, no skip |
| REQ-WFM-068 / 070 (CONVERT's review, code here) | see above | | | pass |

Every requirement of the scope has a check, a test and a code line; no requirement is unlinked. 20 of 20 in scope verified.

## Test requirements (M41)
| TR | Kind | Applies to | Verified by | Met? |
|---|---|---|---|---|
| TR-TOOLBOX-001 mock vs contract suite | setup | 16 TC-WFM | the IF-203 v1 transforms suite runs on mock and real (10 tests, both pass); `tests/test_toolbox.py::ToolboxOnTheRealLibrary` re-runs the 17 acceptance tests on the real library over the file backend | yes |
| TR-TOOLBOX-002 marker file proves no code ran | setup | TC-WFM-052, 053, 054, 090, 091, 092 | marker file asserted absent in the acceptance tests | yes |
| TR-TOOLBOX-003 fixed account lookup | setup | TC-WFM-054, 091, 095 | `toolbox_fakes` account lookup | yes |
| TR-TOOLBOX-004 shipped nodes a fixed copy | setup | TC-WFM-056, 094 | `shipped_copy` plus the check on the real folder `library/nodes` | yes |
| TR-TOOLBOX-005 exact names, versions, statuses | unit | 9 checks | exact assertions, no fuzzy compare | yes |
| TR-TOOLBOX-006 events a list in order | setup | TC-WFM-093 | `EventRecord` list | yes |

No check ran outside its test requirements. Credibility note: the toolbox is not wired to a caller yet (only tests use `Toolbox`; `GraphRunner` of MODEL asks `look_up` after the merge), so the owner rule is verified at the toolbox, not at an HTTP door.

## Goal acceptance
| Item | Result |
|---|---|
| Requirements in scope verified | 20 / 20 (16 REQ-WFM, 2 REQ-RTB, IF-203, IF-302) |
| Frozen requirements unchanged vs parent | none frozen here; `goal_check` without a new GL error |
| Protected checks identical to the baseline | yes, except the approved installs |
| Nothing outside the goal's parts touched | `git diff --stat` outside specs/tests/contracts: `toolbox.py`, `workflow_library.py` (block `transforms`), `record_tables.py`, the A-111/A-112 install scripts |
| Every stop condition logged | yes (T-06 finding, A-112 raised) |
| Exit criterion OC-1..3 | OC-1 and OC-2 hold at the toolbox (F1 is the exception for new code); OC-3 holds. Real use is Validate. |

## Specification vs code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| done, not specified | the allowance `baseline_allowed` carries to a new version and to later states | F1, F2 | Phase 2 amendment or Phase 3 |
| done, not specified | `look_up` unknown id raises `WorkflowLibraryError(not_found)` (not `ToolboxError`) | F8 | Phase 2 note |
| specified, not done | REQ-WFM-052: "a file that fails the check is refused": a float version `1.0` passes the schema and fails later | F3 | Phase 3 |
| specified, not done | REQ-WFM-090: the reason of an untrusted transform | F4 | Phase 3 |
| specified, not done | REQ-WFM-093: one event per replace | F5 | Phase 3 |
| decided | D-225 (shipped run is a KeyError), D-226 (shipped is `tested`), D-227 (seed skips existing ids) | accepted by the owner, no finding | |

Human review: specification side via `review-log.md` (approved); code to read: `Toolbox.run` and `set_lifecycle` (`toolbox.py:107-131`), the `exec` of trusted code (SC-09, TD-24, accepted).

## Quality evidence per characteristic (M32)
| Characteristic | Evidence | Result | Gap or `not now` |
|---|---|---|---|
| Functional suitability | the checks above | pass | F3 to F5 |
| Performance efficiency | none stated for the toolbox | n/a | not now (no budget in scope) |
| Compatibility | IF-203 v1 suite on mock and real, v0 suite unchanged; IF-302 v9, IF-102 v5 | pass | |
| Interaction capability | error texts in `ToolboxError.why` | pass | wording of F4 |
| Reliability | storage writes in two steps (`_save_transform`: record then meta) | partly | a failure between them leaves a record without meta (F8) |
| Security | `exec` of trusted code only; import never runs code; owner rule at the toolbox | partly | F1, F2, F6; SC-09 accepted |
| Maintainability | module small, one `exec`, comments explain why | pass | |
| Flexibility | library part replaces the mock without a change in the toolbox | pass | |
| Safety | not applicable | n/a | not now |

## Open deferrals
TD-24 (trusted code unsandboxed, SC-09) stays open and accepted. Nothing new.

## Findings, ranked
Each has a failing test proposed (a proposal only; `tests/acceptance/` is not touched). The repro code is in the scratchpad, `repro.py` (not committed).

**F1 (high, security, Phase 2 decision + Phase 3): the owner's baseline allowance covers new code from any account.**
`toolbox.py` `import_transform` replaces the code of an untrusted retired entry whose meta record has `baseline_allowed=True`; the meta record is kept (REQ-WFM-092) and no event is written (REQ-WFM-093 only for a trusted transform). Then `run(id, as_baseline=True)` executes the new code with `exec`. Repro: anna imports v1, the owner retires it with `allow_baseline=True`, mallory (any account) imports v2 with other code, `run(as_baseline=True)` returns "v2 from mallory". So the owner's decision on one code text becomes a permission for code the owner never saw, and untrusted import by anyone reaches `exec`. Likely fixes: a replace clears `baseline_allowed` (and the status of an allowance belongs to a version), or REQ-WFM-092 says so. Proposed test (TC-WFM-091 twin): "an allowance does not survive a newer version: after a replace by another account the check is refused with `untrusted`".

**F2 (medium, Phase 2 + 3): the allowance can be set outside retirement and is never revoked.**
REQ-WFM-091 reads "when retiring an untrusted transform", REQ-WFM-095 "allow an untrusted retired transform". `set_lifecycle(id, "draft", owner, allow_baseline=True)` stores the allowance on a live transform, and any account's later retire turns it into a runnable baseline; un-retiring keeps `baseline_allowed=True`; there is no way to withdraw. `tests/test_toolbox.py::BaselineChecks` (the "twin") documents this order as intended. Proposed test: "an allowance given to a live transform is refused (or cleared) and does not run after a later retire by another account"; and "un-retire clears the allowance". Needs a decision by the owner.

**F3 (low, Phase 3): a float version `1.0` passes the exchange schema.**
jsonschema `integer` accepts `1.0`; the file passes `_checked`, then the table `transforms` refuses it, and `import_transform` raises `WorkflowLibraryError(invalid, schema)` instead of `ToolboxError("invalid_file")`. Nothing is stored, but the error type differs from REQ-WFM-052's contract and from the mock. Proposed test: add `json.dumps(dict(good, version=1.0))` to `test_malformed_files_are_refused_and_store_nothing` run against the real library.

**F4 (low, Phase 3): the reason shown after an untrust is wrong.**
`REASON_IMPORTED` is the only reason ever written. A shipped transform set back to untrusted by an account (or a trusted one the owner untrusts) shows "It came from outside MIA and was not reviewed.", or an empty text when no reason was stored (a shipped entry). REQ-WFM-090 says "the reason it is untrusted". Proposed test: seed a shipped node, `set_trust(untrusted, "anna")`, `look_up()["reason"]` is not empty and not the import text.

**F5 (low, Phase 3): the order of replace and event.**
`import_transform` saves the new version, then records the event. If `events.record` raises, the code is replaced and trusted but no event exists. Repro: an event stand-in that raises: the entry is version 2, trusted. Proposed test: with a failing event stand-in the replace is refused (or retried) and the entry stays at version 1.

**F6 (info, Phase 2 note): the owner rule lives in the toolbox, not in the library or the table.**
`WorkflowLibrary.set_trust` / `set_meta` and the table `transform_meta` accept `trust="trusted"` from any caller (A-112 says "thin on purpose", the plan says "who may set a value is the rule of the toolbox"). Safe as long as the only door is `Toolbox`; the wiring of the later API must not expose the library. Also `set_trust(.., "untrusted", account)` does not check "logged in": the caller must. Record in the wiring task.

**F7 (low, Phase 2): `decomp_check` step fails 6 errors more than master.**
REQ-WFM-090..095 have `Parent: FR-38` directly in N-2 ("no parent one level up"), the same as the old REQ-WFM-050..056. The step already fails on master (70 errors), so it is not a regression of the goal's code but the ladder step `decomposition` (stage 1, required for merge) is red.

**F8 (low, Phase 3): unknown ids and half-saved entries.**
`look_up`, `run`, `set_trust` on an unknown id raise `WorkflowLibraryError(not_found)`, not a `ToolboxError`, so a caller handling only `ToolboxError` sees a different type. `_save_transform` writes the record, then the meta record in two calls; a failure in between leaves a transform without meta and `look_up` fails with `not_found` for it. Also a concurrent import check-then-save is not atomic (`save` without `expected_version`). No test proposed beyond the unknown-id type; the rest is a note.

Also noted: D-225 (running a shipped transform with empty code is a `KeyError`) and D-226/D-227 are decided and not findings. The 2 warnings of `trace_check` on REQ-RTB-008/009 come from the marker spelling `@mark.req`.

## Batched human review (maldun, 2026-11-12, D-229)
| Finding | Decision | Destination |
|---|---|---|
| F1 | a replace by a higher version clears `baseline_allowed` | Phase 2 amendment of REQ-WFM-091/092 (text and criterion), then Phase 3: failing test first |
| F2 | the allowance is accepted only together with lifecycle `retired`; any other lifecycle change clears it; the "twin" unit test in `tests/test_toolbox.py::BaselineChecks` changes with it | Phase 2 + 3 |
| F3, F4, F5 | fix all three, a failing test each | Phase 3 |
| F7 | known red, repaired in a parent session with the 70 old errors | recorded here, no change in this goal |
| F6, F8 | not put to the review (info/notes); F6 goes into the wiring task, F8 stays a note | backlog |

After the fixes the automated checks 1, 2, 4 and 5 run again in full and a reviewer reads the fix commits only. Verdict until then: **Verified with open findings**.

## Needs a person (Code review: needed)
- `toolbox.py` `run` and `set_lifecycle`, `import_transform`: F1, F2, F5 (they decide what may reach `exec`).
- The decision on F1/F2: should an allowance belong to one version, and may it be set only at the moment of retiring?
- F7: whether the `decomposition` step is repaired in this goal or stays a known red.

## Notes for Phase 7
- The toolbox has no caller yet; real behaviour of trust and the owner rule at the API is first seen after MODEL's `GraphRunner` and the wiring.
- Shipped nodes carry no code; "running a shipped transform" is a `KeyError` until the old runner is connected (D-225).
- The reason text and the lifecycle `tested` of shipped nodes (D-226) are what a user sees first.

## Second round (2026-11-14, fresh reviewer, scope `02a4906 33ab9a2 931c53f`)
Verdict: **Verified with open findings** (N1, N2, N3 back to Phase 3; the rest is verified).

| Check | Result |
|---|---|
| 1 protected material | `git diff 84eddb6..HEAD -- tests/acceptance tests/helpers tests/smoke contracts eval benchmarks` is empty: no finding |
| 2 failing tests | `84eddb6:toolbox.py` with `HEAD`'s `tests/test_toolbox.py` (copy in the scratchpad, worktree untouched): 33 tests, 10 failures and 11 errors, covering F1, F2, F3 (mock errors, real fails with `WorkflowLibraryError`), F4, F5, F8 and the changed twin `BaselineChecks`. On `HEAD`: 33 OK. No test passes without its fix |
| 3 F1/F2 paths | A replace clears the allowance (also on a trusted retired entry); a lifecycle change away from retired clears it in the same `set_meta` call as the lifecycle; `allow_baseline` with another lifecycle is `allowance_needs_retired`. Order event, clear, save: a failing save after the clear leaves version 1 and no allowance (checked, mock and real): a permission may be lost, none is kept. `get_meta` always has a record (`_save_transform` writes it with the first save). Retire again, or retire by the owner without `allow_baseline`, keeps the allowance: same retirement, in line with the text of REQ-WFM-091. There is no withdrawal while staying retired (un-retire and retire again); not required, noted |
| 4 F3 | `1e0`, `1E0`, `2.0`, `1.5`, `1e400`, `-0.0` are `invalid_file` on mock and real; a huge integer is accepted (fine) |
| 4 F4 | owner untrust: "The owner took its trust back."; account: "An account took its trust back."; shipped entry untrusted by an account shows the account text (not empty); `look_up` of a trusted entry shows no reason. See N1 |
| 4 F5 | event recorded, then save fails: the event stays, the entry stays at version 1 (mock and real). See N2 |
| 5 requirement text | REQ-WFM-091/092 match code (`run`, `set_lifecycle`, `import_transform`) both ways. Two clauses (allowance refused with another lifecycle, cleared on un-retire and on replace) are checked by the unit tests only; TC-WFM-091 in `test-spec.md` says so. TC-WFM-091, 092, 095 (protected) are unchanged and read the same behaviour; the allowance set by the owner on a retired entry stays valid in them |
| 6 re-run | scope test files: `tests/acceptance/test_toolbox.py` 17, `contract/test_if_203_v1_transforms.py` 10, `test_if_203_workflow_library.py` 8, `test_if_302_record_tables.py` 18, `tests/test_toolbox.py` 33, `test_record_tables.py` 17, `test_workflow_library.py` 13: all OK. Ladder: see Stage log. `check_sysml.sh` pass |

### New findings (owner decisions of 2026-11-14, maldun)
**N1 (low, Phase 3): an untrust of an already untrusted entry overwrites the reason.** `set_trust(id, "untrusted", account)` always writes `REASON_UNTRUSTED_BY_*`. A fresh import untrusted again by `guest` changes "It came from outside MIA and was not reviewed." to "An account took its trust back.", which is false (never trusted); REQ-WFM-090. Decision: fix, write a new reason only on the change trusted to untrusted. Proposed test: import, `set_trust(untrusted, "guest")`, `look_up()["reason"] == REASON_IMPORTED`, mock and real.

**N2 (low, Phase 3): failures of the event store or the save are not `ToolboxError`, and the event can stand without a replace.** Decision: wrap in a `ToolboxError` (for example `store_failed`); the orphan event is accepted as it is (the fix chose it on purpose). Proposed tests: (a) event stand-in raises `RuntimeError`: `import_transform` raises `ToolboxError`, version stays 1; (b) `library.save` raises after the event: `ToolboxError`, version stays 1, no allowance kept. Update the F5 test, which expects `RuntimeError`.

**N3 (info, Phase 3): test gaps in the new tests.** Decision: add. (a) F4: untrust by an account (text differs from the owner's and from `REASON_IMPORTED`) and of a shipped entry (not empty); (b) F3: `1e0`, `2.0` and `1e400` are `invalid_file`; (c) F1: a failing `library.save` after the clear leaves version 1 and the allowance cleared. The code already passes them.

Not findings: the event-before-replace order (accepted by the owner's choice of N2), no withdrawal of an allowance while retired, the red `unit` step in the shutdown tests (environment, see Stage log), F7 (decided).

After the fixes of N1 to N3 a reviewer reads those commits only and re-runs `tests/test_toolbox.py` and the acceptance tests; the full ladder is then run in a normal terminal (not `nohup`), so that the shutdown tests can pass.

## Third round (ca3d8fa)
Scope: `ca3d8fa` only (`toolbox.py`, `tests/test_toolbox.py`). Verdict: **Verified with open findings** (N4 back to Phase 3; N1 to N3 verified). Not in scope and decided: F6, F7, F8 rest, the order event, allowance clear, save.

| Check | Result |
|---|---|
| 1 protected material | `git diff 84eddb6..HEAD -- tests/acceptance tests/helpers tests/smoke contracts eval benchmarks` is empty: no finding |
| 2 red before green | `HEAD`'s `tests/test_toolbox.py` (41 tests) against `5c0f2b0:toolbox.py` (copy in the scratchpad): 2 failures and 4 errors. Red: `test_n1_an_untrust_of_an_untrusted_entry_keeps_its_reason` and `test_f5_a_failed_event_refuses_the_replace` (now expects `store_failed`), `test_n2_a_failed_save_is_a_toolbox_error_and_the_old_version_stays`, each on mock and real. On `HEAD`: 41 OK |
| 2 N3 tests (pass on old code, as expected) | `test_n3a` (reason texts), `test_n3b` (`1e0`, `2.0`, `1e400`); N3c is covered by the N2 save test above. Mutations on a copy of `HEAD`: drop the float check: `test_n3b` and F3 fail; accept only `2.0`: `test_n3b` fails; account text equal to owner text: `test_n3a` fails; no allowance clear before the save: F1 and the N2 save test fail; untrust always overwrites: N1 test fails. All killed |
| 2 survivor | replace the wrap of the new-import branch by a bare `raise`: all 41 tests pass. That branch has no test: N4 |
| 3 N1 `set_trust` | mock and real, same result: trusted, owner untrusts: owner text; again by an account: owner text kept; trust given back, account untrusts: account text; owner untrusts the untrusted entry: account text kept; fresh import untrusted by `guest`: import text kept; shipped entry (trusted) untrusted by an account: non-empty account text. `_latest(tid)` is a second read before the write: with one user it only matters if trust changes between the read and the write, and then only the reason text could differ from the state; no finding |
| 4 N2 `import_transform` | `KeyboardInterrupt` and `SystemExit` are not `Exception`: confirmed, a `KeyboardInterrupt` from the event store passes through and the version stays 1. A `ToolboxError` raised inside the `try` (stand-in `save`) becomes `store_failed`; no real library or event call raises one, so nothing is lost today (info). New import with `save` ok and `set_meta` failing: `store_failed`, but the entry stays (version 1, untrusted, empty reason), a retry gives `duplicate_id`: the text "was not stored" is not honest: **N4**. `why` carries the text of the library's error as it is (a path in a stand-in's text appeared in it): the owner ranks privacy-only findings low, info only. The module docstring lists `store_failed` |
| 5 re-run | `tests/test_toolbox.py` 41, `tests/acceptance/test_toolbox.py` 17, `tests/test_workflow_library.py` 13, `contract/test_if_203_v1_transforms.py` 10: all OK. Ladder: see Stage log (only `decomposition` fails, F7; 17 skips in contract-real). Stage 3 steps run by hand: pass |

### New finding
**N4 (low, Phase 3): a failed `set_meta` after the first save of a new import is reported as "was not stored".** In `import_transform` the new-id branch wraps `save` and `set_meta` in one `try`; when `set_meta` fails the entry is already in the library (version 1, untrusted, no reason), but the message says it was not stored and a retry is `duplicate_id`. REQ-WFM-090 shows a reason for an untrusted entry; here it is empty. Decision (maldun, 2026-11-14): fix the text and add a test; the orphan stays, as decided for N2 and F8. Proposed test (mock and real): `library.set_meta` raises after a new import's `save`: `ToolboxError` with code `store_failed`, `look_up(id)["version"] == 1`, and the message does not say "was not stored" (it says the entry was stored without its meta record).

Info, no action: a `ToolboxError` inside the `try` would be re-wrapped (cannot happen today); the error text of the library goes into `why` unchanged.

After the N4 commit a reader checks that commit only and re-runs `tests/test_toolbox.py` and the acceptance tests; the full ladder ran clean on `ca3d8fa`, so it is repeated only if other files change.

## Fourth round (bf253ce)
Scope: `bf253ce` only (`toolbox.py`, `tests/test_toolbox.py`, `implementation-log.md`). Verdict: **Verified with open findings** (N4 verified; N5 back to Phase 3). Not in scope and decided: F6, F7, F8 rest, the order event, allowance clear, save, N1 to N3.

| Check | Result |
|---|---|
| 1 protected material | `git diff 84eddb6..HEAD -- tests/acceptance tests/helpers tests/smoke contracts eval benchmarks` is empty. `git show --stat bf253ce`: exactly the three files. `git diff ca3d8fa..HEAD --stat` adds only docs (two start prompts, this report) and the same three files: no finding |
| 2 red before green | `HEAD`'s `tests/test_toolbox.py` (45 tests) against `ca3d8fa`'s code (`git archive` copy in the scratchpad): 2 failures, `test_n4_a_failed_set_meta_after_a_first_save_says_the_entry_was_stored` on mock and on real. `test_n4_a_failed_first_save_still_says_not_stored` passes on the old code, as expected: it guards the unchanged save text. It fails if that text, the code `store_failed` or the empty library breaks (mutations c, d1); it does not fail if the old single `try` came back, the set_meta test covers that |
| 3 mutations on a copy of `HEAD` | (a) bare `raise` in the `set_meta` branch: set_meta test errors (mock, real). (b) old text "was not stored" there: set_meta test fails. (c) the "stored without its meta record" text in the `save` branch: save test fails. (d) code changed in the save branch: save test fails; in the `set_meta` branch: set_meta test fails. (e) replace branch: the diff of `bf253ce` has one hunk, inside the new-id branch, the replace branch is untouched. All killed. Extra mutations (not asked): drop "(its reason is empty)", or shorten the text to "was stored": **survive**, see N5 |
| 4 new-id branch | Two `try` blocks, `save` then `set_meta`. A `KeyboardInterrupt` and a `SystemExit` pass through in both (ids: none after a save, `t.one` after a `set_meta`, as decided); a `ToolboxError` inside is re-wrapped as before (info, cannot happen today); nothing is deleted, no library method added. Real and mock, `set_meta` raising before it writes: `look_up` = version 1, untrusted, reason `""`, retry `duplicate_id`; the text "(its reason is empty)" is true. Contrived: a `set_meta` that writes and then raises leaves the reason set, and the text would be false; no real library or event call does that (info). Module docstring: still true (`store_failed` while importing); it does not name the two texts or that the entry stays (info) |
| 5 behaviour only in the code | No new default, output, retry or cleanup. The text "(its reason is empty)" is an addition to the wording proposed in N4; it states what `look_up` shows, but no test and no requirement pins it: N5 |
| 6 re-run (mia312 venv) | `tests/test_toolbox.py` 45 OK, `tests/acceptance/test_toolbox.py` 17 OK, `tests/test_workflow_library.py` 13 OK, `contract/test_if_203_v1_transforms.py` 10 OK. Ladder not repeated: no code file outside the three changed |

### New finding
**N5 (info, Phase 3): the text of a failed `set_meta` after a first save is not pinned.** `test_n4_a_failed_set_meta_after_a_first_save_says_the_entry_was_stored` asserts only `assertNotIn("was not stored", why)`, so the wording "was stored without its meta record (its reason is empty)" can be dropped or shortened to "was stored" and all 45 tests pass. Decision (maldun, 2026-11-14): pin the text and the reason clause. Proposed test: in that test add, after the `assertNotIn`, `self.assertIn("stored without its meta record", caught.exception.why)`, `self.assertIn("its reason is empty", caught.exception.why)` and `self.assertEqual(self.box.look_up("t.one")["reason"], "")` (mock and real), so the claim is checked against `look_up`. No code change is needed.

After the N5 commit a reader checks that commit only and re-runs `tests/test_toolbox.py`; no other file changes, so the ladder is not repeated. Then the report is ready for the gate with the deviations F6, F7, F8 rest.
