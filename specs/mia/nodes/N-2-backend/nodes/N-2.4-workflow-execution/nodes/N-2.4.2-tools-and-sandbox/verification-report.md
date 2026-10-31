# Verification report: Tools and sandbox (N-2.4.2)

**Goal:** G-V1 (iteration), supervised; this report covers node N-2.4.2 only (node cycle, verified as a black box against the mocks of its neighbours)
**Branch:** goal/v1 @ bfc9424   **Parent line of work:** master (53c6766)   **Plan baseline:** 53c6766 (`plan-baseline-it1` + amendments up to A-34)
**Date:** 2026-10-31   **Reviewers:** – (human, open), Claude Opus 5.5 (AI, independent; never saw the implementation chat)

Commits reviewed: 3f7d5c8 (T-01), 9a7de6f (T-02), 543983a (eval case), f48572c (T-03), 8b0e82a (T-04), 5bac182 (T-05), 686de47 (T-06), 821b2d3 (T-07 deferred), and the `tool_calls.py` / `web_app.py` part of 356f90b (N-2.4.1 T-07, provider side of A-34).

## Verdict
**Proposed: Verified with findings.** The door (`tool_calls.py`) meets REQ-TLS-001, -003, -004, -005, -007, -008 and IF-402 v2 in its own tests and the contract suites; the sandbox refuses rather than weakens; the URL rules refuse private addresses and odd ports. It is not *Verified* because of F-1 (a stage-1 regression test is red since 543983a, through an eval case that seems malformed), F-2 (the app wires the door without the trust and retraction sources, so REQ-TLS-003 holds only in tests) and three findings that need the owner (F-3 trust label of `run_script`, F-4 the sandbox tier of a script on web text, F-5 what REQ-TLS-007 allows to leave the host). The team decides.

## Automated checks
No CI here; all runs are local, in the project image `localhost/mia:latest` (Python 3.12) unless stated.

| Check | Result |
|---|---|
| Node tests: `bash tools/run_in_image.sh tests/test_tool_calls*.py` | 6 files, 41 tests, OK (11 + 6 + 5 + 6 + 8 + 5) |
| Contract suites: IF-402, IF-404, IF-405 | IF-402 12 OK (6 mock, 6 real through the A-32 adapter); IF-404 10 OK, 5 real skipped; IF-405 8 OK, 4 real skipped (stage 2: real web and APIs) |
| Full suite, goal/v1 vs master (all `tests/test_*.py` and `tests/integration/**`, one container each side) | goal/v1: 3 files fail: `test_amendment_report` (1 error), `test_config` (1 failure), `test_harness` (**2** failures). master: the same three files, but `test_harness` with **1** failure. Same failing test names for `test_config` and `test_amendment_report`. `test_shutdown` passed on both sides in this run (the claim that it fails on master was not reproduced). The extra `test_harness` failure is F-1. |
| Integration N-2.4 | step_00 OK; step_01..03 skipped (`need(REAL_NODES)`: N-2.4.2 not marked integrated); REQ-TLS-001/-008 integration evidence not yet run |
| Sandbox wall on the host (bubblewrap, Python 3.14): `python3 -m unittest test_sandbox.{Policy,Seccomp,Run,Wall,Router}Tests` | 42 OK, none skipped. `PodmanTests` not run (no containers besides the test image, by instruction). In the image `test_sandbox.py` skips 52 (no bubblewrap there). |
| Protected material vs 53c6766 (`tests/acceptance tests/helpers tests/smoke tests/integration benchmarks contracts eval/suites eval/baselines stages.yaml decomposition.yaml threat-model.md`) | Changes: `contracts/IF-402` (v1 A-32, v2 A-34), `contracts/IF-404` (v1 A-33), `test_if_402_tool_calls.py` (A-32 golden 5, A-34 TC-IF-402-06), `test_if_404_web.py` (A-33 port 22), `helpers/contract.py` (A-32 adapter), mocks IF-402 (A-34 `fetch_page`) and IF-404 (A-33 ports): every change maps to A-32/A-33/A-34 (D-115, D-116, D-123, D-125). `eval/suites/hard_checks/cases.jsonl` +1 case (543983a, owner label in the commit trailer; no A-nn and no D-entry): see F-1, F-10. No `skip`/`xfail` added. |
| Traceability `trace_check.py` | 94 errors in all, mostly older. For this node: `REQ-TO-005` unknown marker (`tests/test_tool_calls_sandbox.py:60`, F-7); the node's `test-spec.md` has no `## Scenarios` section (22 test specs share this, plan level); no `test-requirements.md` exists for MIA (plan level, older). |
| Goals `goal_check.py` | 0 errors, 0 warnings |
| Agent checks `agent_check.py` | 2 errors, both `SkillDigestStep` (not this node); A7 warnings on wikidata cases (not this node) |
| Model consistency `tools/check_sysml_model.py` | OK; but `tool_calls.py` is in no `@Implementation` of the model (F-9) |
| Test docs `test_doc_check.py` on each `tests/test_tool_calls*.py` | 0 errors, 0 warnings each |
| Refactoring commits, agent configuration | no `refactor:` commit and no change of agent configuration in the node's commits |
| Static / SAST / lint | none configured (CLAUDE.md); inspected by hand (below) |
| Usability with bad inputs | probes below: wrong tool names are refused; wrong arguments crash with a raw `TypeError` after being counted (F-8) |
| Deployable artifact | not built (not part of a node cycle) |

Independent probes of the door (scratch script run read-only in the image; no network): `sandbox_backend: none` and `auto` without bubblewrap give `{"status": "unavailable", "stdout": ""}`; limit 0 gives `budget` naming the tool, nothing counted; `_need`, `__class__`, `call`, `used` as tool names are `unknown_tool`; `check_url` refuses 127.0.0.1, `::ffff:127.0.0.1`, `::1`, 0.0.0.0, 169.254.169.254, 100.64.0.1, fe80::1, 2002:7f00:1:: (6to4 of loopback), `2130706433`, port 22, ftp, user:password; allows port 8080 (A-33). A backend that is available when asked but gone when run gives `status: ok` with nothing run (F-6); a script that prints web text from its `inputs` comes back with trust `code` (F-3).

## Verification matrix
| Requirement | Method | Evidence | Result | Plausible? |
|---|---|---|---|---|
| REQ-TLS-001 code checks first | Test | `test_tool_calls.py` (4 tests): the three checks are offered with trust `code`; IF-402 TC-01, -02, -05 on the real door | **Partly**: the checks are offered (Text met). AC-2 ("in the run log the code checks precede the first model call of each claim") is not tested at this node; the door cannot order a run. N-2.4 step_02 carries the marker but is skipped and checks only that the mock model has no calls. | yes (fixed behaviour) |
| REQ-TLS-002 lookup with sources | Test, Measurement | `test_tool_calls_lookup.py` (5): findings with url, title, short text; passages verbatim, best first, `ref` kept; `anchor_answer` demotes a paraphrase to unknown | **Test part met. Measurement part open** (AC-2 on the lookup suite, eval on the pinned model; no eval criterion, no `eval-spec.md`, no pins) → gap G-1 | yes; test fixture was strengthened by the implementer so 2 tests are red on the old code (log) |
| REQ-TLS-003 source records, cut-off | Test | `test_tool_calls_scholar.py` (8): strict cut-off over a 10-date grid, codes `no_date`/`after_cutoff`, retracted/withdrawn dropped and listed, notices after the cut-off ignored, `source_record` by DOI; IF-405 contract (mock side) | **Met at the door; not in the app** (F-2: `web_app.py:591` passes no `work_trust`, `retractions`, `work_lookup`: trust is `None`, retraction only as reported by the sources, `source_record("doi:…")` is `source_error`) | yes |
| REQ-TLS-004 untrusted text is data | Test | `test_tool_calls_untrusted.py` (6): an instruction in evidence, source or value changes no verdict of the code checks; a page that orders a tool starts none; `untrusted()` neutralises delimiters | **Met for the door** (component part of AC-6). The red-team part (RT-001..003 on the model steps) is eval, not run here → gap G-2. Residual: planted figure (F-1, F-11). | yes |
| REQ-TLS-005 sandbox or refuse | Test | `test_tool_calls_sandbox.py` (5): no router, all backends removed, `force=none` → `unavailable` and no backend asked; with a backend the script runs there; PDF not converted without bubblewrap, `Popen` not called. Host wall tests 42 OK. Probes above. | **Met** (refuses, never weakens; the door asks `available_for` before the check). Notes: F-4 (tier), F-6 (status after a race). | yes; removing the door's check would turn the tests red (the check's own `inconclusive` maps to `ok`) |
| REQ-TLS-006 no invented source | Measurement | – | **Out of scope of G-V1** (D-117, goal scope row); T-07 deferred; not verified | – |
| REQ-TLS-007 only queries leave the host | Test, Inspection | `test_tool_calls_web_log.py` (6): search sends only `q` (+format, safesearch, User-Agent); search, fetch, refused address and failing backend are logged; every redirect address logged (fix of 8b0e82a, regression test red first). Inspection of `scholar.ApiHttp`: every scholarly request is logged (`kind: scholar`). | **Met for the web; open for scholarly requests** (no test) and **the Text is narrower than the code** (F-5: API keys, User-Agent, date filters, DOIs and fetched addresses also leave the host) | yes |
| REQ-TLS-008 budget and trust label per call | Test | `test_tool_calls.py` (7): over the limit → `budget` naming the tool, nothing run or counted; per run and per tool; unknown tool not counted; failing source counted; trust on every output incl. `fetch_page`; IF-402 TC-03, -05, -06 | **Met at the door.** Notes: F-3 (label of `run_script`), F-12 (check-then-count not atomic). In the app not every tool call passes the door (web checks and the broker get the web functions directly, `web_app.py` `functions=`/`broker_factory`), and the runner drops the label after emitting it (`pipeline.py:513`): N-2.4.1 / N-2.4 integration, reported there. | yes |
| IF-402 v2 | Test | contract suite 12/12 (mock and real adapter) | **Met**; beyond the contract: `run_script` adds `result`; `scholar_search` records add `trust` and `unconfirmed` in `retraction`; dropped entries add `title`, `detail` and reasons `retracted`, `withdrawn`, `before_since` (F-13) | yes |
| IF-404 v1 | Test | contract suite mock side 5/5; real side skipped (no provider class for the real web client; log, open item) | **Mock side met; real side not run** (stage 2, gap G-3) | – |
| IF-405 | Test | contract suite mock side 4/4; real side skipped | **Mock side met; real side not run** (stage 2, gap G-3) | – |

## Test requirements (M41)
MIA has no `test-requirements.md` (trace_check: "no test requirements"); no TR-… applies to this node's checks. Plan-level gap, older than this node: not counted against the code.

## Goal acceptance (node part)
| Item | Result |
|---|---|
| Requirements in scope verified | 8 of 8 in scope (REQ-TLS-006 out): 5 fully at the node (TLS-004 component part, -005, -008 door, IF-402, -007 web), 3 partly (TLS-001 AC-2, TLS-002 measurement, TLS-003 app wiring); IF-404/405 mock side only |
| Frozen requirements | none in G-V1 (goal_check 0) |
| Protected checks vs baseline | only A-32, A-33, A-34; plus one eval case without amendment (F-1, F-10) |
| Nothing outside the node's parts touched | `scholar.py` (+`cutoff_code`), `web_tools.py` (redirect log) are modules of ResearchSuite parts the plan names; `tool_calls.py` is new and not in the plan's Touches nor the model (F-9) |
| Every stop logged | yes: D-115 (A-32), D-116 (A-33), D-117 (T-07); the planted-figure finding logged and turned into a case |
| Exit criterion | checked in Validate (VAL-001..006) |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-TLS-003 trust class and retraction state in the running app | F-2 | Phase 3 (wiring) |
| specified, not done | REQ-TLS-001 AC-2 order in the run log | not tested anywhere active | decision (G-4) |
| specified, not done | REQ-TLS-007 test for scholarly requests | F-5 | Phase 3 test |
| done, not specified | `run_script` `result` key; IF-405 extra reasons and fields; `fetch_passages` selection by word overlap (at most 2 of ~900 chars) | F-13 | Phase 2 (next IF-402/IF-405 version) |
| done, not specified | API key, User-Agent, date filters leave the host | F-5 | Phase 2 (REQ-TLS-007 text) |
| done, not specified | `quote_in_source`: a near match is `fail` (contract says verbatim: consistent); `number_check` `not_applicable` → `inconclusive` | consistent with IF-402 v2 | – |

Human review: no item of this node is marked `Code review: needed`. Mismatches above are for the owner.

## Quality evidence per characteristic (M32, this node)
| Characteristic | Requirement(s) | Evidence | Result | Gap |
|---|---|---|---|---|
| Functional suitability | TLS-001..005, -007, -008 | tests above | partly | F-2, G-1, G-4 |
| Performance efficiency | – | – | not now | no budget requirement on the door |
| Compatibility | IF-402/404/405 | contract suites | mock side met | G-3 real sides |
| Interaction capability | – | – | not now | no user-facing part |
| Reliability | TLS-008 | counted failing source | met | F-8, F-12 |
| Security | TLS-004, -005, -007, -008; THR-001, -005, -007, -008 | sandbox and URL probes, wall tests on host, web log tests | met with findings | F-3, F-4, F-5, F-6 |
| Maintainability | – | test doc check clean; small module | met | F-7, F-9 |
| Flexibility | – | – | not now | – |
| Safety | – | – | not now | – |

## Open deferrals (M26)
None for this node (REQ-TLS-006 is out of scope by D-117, not a TD record). TD-01..TD-04 belong to other nodes.

## Agent verification (agent-app-verify, node part)
| Check | Result |
|---|---|
| eval/suites, eval/baselines vs 53c6766 | +1 case `n-planted-figure` in `hard_checks` (dev), owner label in the commit trailer only (F-1, F-10) |
| threat-model.md, eval-spec.md | threat model unchanged; no `eval-spec.md` exists |
| Pins on the host | not checked: no model needed, no eval run (by instruction) |
| Sandbox backends | host: bubblewrap present, wall tests green; podman present, not exercised. Image: none, the door refuses (`unavailable`). |
| Eval criteria | none decided at this node; REQ-TLS-002 measurement and REQ-TLS-004 red-team part need eval runs → G-1, G-2. No holdout touched. |
| Red-team cases | RT-001..003 (THR-001) and RT-008, RT-010 (THR-005, THR-007; still drafts) name this node's boundary; none run (no model) |

Threat conformance (door): untrusted text enters as data with trust `web`; the door never starts a tool from an output (T-02 test); model-written code runs only through the router, refused without a backend; web access only through the handed-in `web_tools` functions, whose `check_url` refuses private and reserved addresses, odd ports, other schemes and credentials, re-checks every redirect and checks the peer address after connecting. Residual: `_check_peer` (`web_tools.py:181`) fails open when the socket is not reachable (older code, not changed by this node; noted, no finding). THR-001's residual risk does not name the planted-figure case (F-11).

## Review findings
| # | Finding | Severity | Needs | Resolution / destination |
|---|---|---|---|---|
| F-1 | Since 543983a `tests/test_harness.py::ShippedSuites.test_the_hard_checks_suite_matches_every_time` is red on goal/v1 (green on master): `[('n-planted-figure', 'not_applicable', 'fail')]`. The case (`eval/suites/hard_checks/cases.jsonl:119`) gives `claim.data = {claim, evidence}`, but the hard-checks numeric route reads `{expression, value}`, so the check answers `not_applicable`: the case does not exercise the planted-figure behaviour it was written for (the log says `pass` is the bad output). The log's "fails only as on master" is true per file, not per test. | High | decision of the owner (eval case seems wrong: not fixed here) | Owner: correct the case's input shape (or route it to `number_check` with claim and evidence) by an amendment, and decide how a known-red case lives in a stage-1 regression suite (e.g. tag `known_limit` as other limits are, or keep it out of `hard_checks` until the rule changes). |
| F-2 | `web_app.py:591` builds `ToolCalls` without `work_trust`, `retractions`, `work_lookup`, though `_source_trust.for_work`, `_scholar.verify_retraction` and the Crossref lookup exist. In the app every `scholar_search` record has `trust: None`, retraction only as the sources report it, and `source_record("doi:…")` is `source_error`. REQ-TLS-003 holds only in the tests. (Wiring came with N-2.4.1 T-07, 356f90b.) | High | test + fix (Phase 3) | A test that the app's door returns a trust class and the Crossref retraction state for a scripted work (and a DOI record), then pass the three sources in `web_app.py`. Owner decides whether this is N-2.4.1 T-07 or the N-2.4 integration step. |
| F-3 | `run_script` output is labelled `code` (`tool_calls.py:30`) although the script is model-written and may print its `inputs`: a probe script printing web text from `inputs` returned it with trust `code`. The label launders web text into "computed by code". IF-402 v2 and the mock say `code`, so the code follows the contract. | Medium | decision of the owner + amendment | Proposal: IF-402 v3 labels `run_script` as `model` (written by a model), or the door labels `stdout` `web` when any input came from a `web` output and keeps `code` only for the check's verdict; test with an input that carries web text. |
| F-4 | The door always asks for `Operation("compute", "model")` untainted (`tool_calls.py:95`), the standard tier (bubblewrap). A script on web text should be `tainted` → strong tier (podman, or refused without it) per `sandbox.required_tier`; IF-402 `run_script` has no way to say so (logged by the implementer). THR-005/THR-007. | Medium | decision of the owner + amendment | IF-402 v3: `run_script` takes `tainted` (or the runner passes the trust of the inputs) and the door asks for the strong tier; test that a tainted script with only bubblewrap is `unavailable` (unless `sandbox_degrade`). |
| F-5 | REQ-TLS-007 allows only the query text and an e-mail address to leave the host. The code also sends API keys (`scholar.py:658` NCBI `api_key`, `:701` `x-api-key`), a User-Agent, date filters (`publicationDateOrYear`), DOIs for retraction lookups and the addresses of fetched pages. TC-TLS-007 covers web search and fetch only; no test for scholarly requests in the web log. | Medium | amendment (requirement text) + test | Owner: widen REQ-TLS-007 to "the query, the addresses and identifiers asked for, and configured credentials and e-mail", or forbid keys; add a test that every scholarly request is in the web log with only those fields. |
| F-6 | When the backend is available at the door's check but gone at run time (race, or a router that fails), the check returns `inconclusive` and the door reports `status: "ok"` (`tool_calls.py:97-99`); also a policy-rejected, crashed or timed-out script is `ok`. Nothing runs unprotected, but the status misreports. | Low | test + fix | Map the check's run status: `unavailable` when the evidence says the sandbox was missing; regression test with a backend that disappears between the two calls. |
| F-7 | `tests/test_tool_calls_sandbox.py:60` marks `REQ-TO-005` (unknown id; trace_check error). | Low | fix in the test (not protected) | Change to `REQ-TLS-005` (Phase 3, one-line). |
| F-8 | Wrong or missing arguments raise a raw `TypeError` after the call was counted (`tool_calls.py:66-73`; probe: `number_check` without `evidence`, args as a list). IF-402 has no error for it; a workflow edit with a typo crashes the step instead of a contract error. | Low | decision of the owner + amendment | IF-402: an error `bad_arguments` (not counted), test for it. |
| F-9 | `tool_calls.py` (the door of IF-402) is in no `@Implementation` of `architecture.sysml`, and its imports `research.collect_passages` (ResearchSuite.lookup) and `schema_check` (pipelineRunner) have no flow in the model; the plan's Touches list omits the module. | Low | amendment (model) | Add a part (e.g. `VerificationSuite.toolCalls`, modules `tool_calls.py`) and the two flows, or move the passage selection behind web_tools. |
| F-10 | The eval case entered `eval/suites/` with the owner's label only in a commit trailer (`Labelled-by:`); no A-nn and no D-entry in `review-log.md`. | Low | decision record | Record the label decision (D-nn) in the review log, with F-1's correction. |
| F-11 | THR-001's residual risk names "biased text without any instruction" but not a page that plants the claimed figure, which passes `number_check` (log T-02). | Low | amendment (threat model) | Add it to THR-001 (residual risk, case `n-planted-figure` once F-1 is fixed); the rule change itself stays the owner's (handover item). |
| F-12 | `ToolCalls.call` checks the limit and counts without a lock (`tool_calls.py:61-66`); the runner calls tools from a thread pool (`pipeline.py:553`), so parallel calls of one run can pass a limit. The runner's own count under its lock likely catches it first. | Low | test | Concurrency test with workers > limit; a lock in the door if it fails. |
| F-13 | Outputs beyond the contracts: `run_script.result`; IF-405 reasons `retracted`, `withdrawn`, `before_since`; dropped `title`, `detail`; `retraction.unconfirmed`; `fetch_passages` returns at most 2 passages of ~900 characters chosen by word overlap. Logged as proposals by the implementer. | Low | amendment | Next IF-402 / IF-405 versions name them (or the code drops them). |

Gaps that need an eval run or a decision (not findings of the code):
- **G-1** REQ-TLS-002 measurement (AC-2 on the lookup suite): no eval criterion, no `eval-spec.md`, no pins. Same situation as REQ-TLS-006 (D-117); owner decides: fix the criterion, or take the measurement part out of G-V1.
- **G-2** REQ-TLS-004 AC-6 red-team part (RT-001..003): eval on the model steps; not run here.
- **G-3** Real sides of IF-404 and IF-405 never run: no provider class for the real web client and the real APIs (log T-04); an amendment for a stage-2 provider is open.
- **G-4** REQ-TLS-001 AC-2 (order in the run log): owner decides whether the N-2.4 scenario gets a run-log order check (amendment of the protected scenario) or AC-2 is moved to N-2.4.1.

## Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| REQ-TLS-006 not verified | out of the scope of G-V1 | Stefan Reiterer, D-117 |

## Could not check
- Podman wall tests and any real web / scholarly / SearXNG request (no containers besides the test image, no network, by instruction).
- Eval runs, red-team runs, model pins, budgets (no model server, no evals, by instruction).
- CI stage log and `merge_gate.py` (no CI here).

## Notes for Phase 7 (validation)
- Whether users notice that scholarly records carry no trust class (F-2) in the review.
- Whether `fetch_passages`' two passages are enough for workflows other than the lookup.

## Re-verification (2026-10-31)

**Reviewer:** Claude Opus 5.5 (AI, independent; never saw the implementation chat). **Checked state:** goal/v1 @ 2e1d588 (frozen in a scratch worktree; includes 70a6f35, 191a8f3, 408ee77, 4892783, 0f5050d, 6fa07ff, a32ce04, and the A-40 draft 7b1a95e). Master for comparison: 53c6766. `git log 5078cfa..HEAD -- tool_calls.py checks.py scholar.py sandbox.py web_tools.py` finds only 191a8f3 besides 70a6f35 (which is before 5078cfa), 38e72de and bfeffa9 (`web_app.py` only, N-2.4.1, nothing of the door). `sandbox.py`, `scholar.py`, `web_tools.py` unchanged since the first report.

**Numbering note.** The fix commits and A-42 use the owner's list of D-132: their "#10" is this report's **F-12** (lock) and their "#11" is **F-13** (dropped works). This report's F-10 (label record) and F-11 (THR-001 residual) were not addressed under those numbers; see the table.

### Per finding
| # | State | Evidence / where |
|---|---|---|
| F-1 planted figure | **Decided, not built** | D-132 (1) retire the case, (2) rule `open` for conflicting values, with an **open conflict** (with `open` the planted figure is inconclusive, but the expected outcome stays `fail`). A-40 drafted (7b1a95e; draft differs from the suite only in the case's line: tag `retired`), not installed. Unit test of `checks.number_check` and the IF-402 contract case not built. `tests/test_harness.py::ShippedSuites.test_the_hard_checks_suite_matches_every_time` is **still red** on goal/v1 (`[('n-planted-figure', 'not_applicable', 'fail')]`) and green on master. |
| F-2 app door without trust sources | **Fixed** (70a6f35) | `tool_calls.build_tool_calls` hands in `for_work`, `verify_retraction`, `crossref.lookup`; `web_app.py:591` uses it (inspected; `Scholar.crossref`, `verify_retraction(work, errors)`, `TrustTable.for_work(work, as_of)` exist with these signatures). Test `AppDoorTests.test_the_door_of_the_app_has_every_source` is red before the fix only by `ImportError` (run on 160bef6); it covers the DOI record and the wiring of the retraction check; that `web_app` calls `build_tool_calls` rests on inspection (no test imports the app). |
| F-3 trust label of `run_script` | **Deferred** to the next iteration with FB-03 | D-128 (F6: "the IF-402 trust and tier gaps go to the next iteration with FB-03"); handover-2026-10-31-pm row of N-2.4.2. Not yet in the accepted-deviation table of this report. |
| F-4 sandbox tier of a script on web text | **Deferred** with FB-03 | as F-3 (D-128). Still: the door asks the standard tier untainted (`tool_calls.py:113`). |
| F-5 what leaves the host | **Decided and applied (text)**; test part open, low (D-131) | A-41 (6fa07ff): REQ-TLS-007 names filters, DOI, API key, e-mail, User-Agent. Not done: a REQ-TLS-007 test for scholarly requests (`tests/test_scholar.py:282` logs them but carries no marker and does not check the fields); IF-402 v3 Bounds still says "only the text of a web or scholarly query" (N-4 below). The text does not name the address of a fetched page. |
| F-6 `run_script` status | **Fixed** (191a8f3, A-42) | `test_a_script_that_did_not_run_to_the_end_is_not_ok` red on 6fa07ff (`'ok' != 'failed'`), green on HEAD. Host probe with real bubblewrap: a finishing script `ok`, raise / endless loop / `import os` `failed`. |
| F-7 marker `REQ-TO-005` | **Fixed** (191a8f3) | trace_check no longer reports it. |
| F-8 wrong arguments | **Fixed for missing, unknown and non-mapping arguments**; residual for wrong types (N-2) | `test_wrong_arguments_are_refused_before_they_count` and TC-IF-402-07 (real side) red on 6fa07ff (raw `TypeError`), green on HEAD; probes: `args` None or a list → `bad_arguments`, nothing counted. |
| F-9 door not in the model | **Partly fixed** | 408ee77: part `verifier.toolDoor` (`tool_calls.py`); `check_sysml_model.py` OK (note: "toolDoor carries no requirement"), `check_sysml.sh` 0 errors. The two flows of the first report (`research.collect_passages`, `schema_check`) are not in the model. |
| F-10 label record of the case | **Decided** (superseded) | D-132 (1) records the owner's decision on the case (retire, A-40). |
| F-11 THR-001 residual | **Open** | `threat-model.md` unchanged since A-19; THR-001's residual risk still does not name the planted figure. D-132 (4) planned it as an amendment draft with #9, but the drafts took "#11" as the dropped works. |
| F-12 lock | **Fixed** (191a8f3), test cannot fail before the fix | Lock checked by inspection (`tool_calls.py:78-84`); `test_concurrent_calls_keep_the_limit` passed on 6fa07ff too (stated in the commit). |
| F-13 outputs beyond the contracts | **Partly fixed** (A-42) | IF-402 v3 names `run_script.result`, the dropped works and the reasons `retracted`, `withdrawn`. Still beyond the contracts: `trust` and `retraction.unconfirmed` in `scholar_search` records (IF-405 unchanged), `fetch_passages` at most 2 passages chosen by word overlap. |
| G-1 REQ-TLS-002 measurement | **Open** | no scope row in `goals/G-V1/goal.md`, no criterion in the `eval-spec.md` draft (726dae1 names REQ-TLS-006, not -002). |
| G-2 RT-001..003 | **Open** | no eval or red-team run (by instruction). |
| G-3 real sides IF-404, IF-405 | **Open** | still skipped (`tests/helpers/contract.py:21-22`). |
| G-4 REQ-TLS-001 AC-2 order | **Open** | no decision found in `review-log.md`. |

### New findings
| # | Finding | Severity | Needs | Proposal |
|---|---|---|---|---|
| N-1 | `number_check` with `evidence` as one string instead of a list passes the new argument check and gives a confident wrong verdict labelled `code`: `"\n".join(evidence)` splits the string into characters (`tool_calls.py:98`). Probe: claim "It is 1,200 m", evidence `"It is 1,200 m"` → `fail` ("the evidence gives another value"). A template argument of a workflow can easily resolve to a string. Older than this round (T-01), not seen in the first report. | Medium | test + fix; amendment if refused | Test first; then either refuse a non-list `evidence` as `bad_arguments` (IF-402 v3 names only missing/unknown arguments → widen by amendment) or take one string as a list of one. |
| N-2 | Arguments of a wrong type still crash with a raw exception **after** being counted: `number_check` with `evidence: None` → `TypeError`, `schema_check` with a string schema → `AttributeError` (`tool_calls.py:85-91`: non-external tools re-raise). Residual of F-8. | Low | amendment + test | With N-1: `bad_arguments` for wrong types of the checks' arguments, before counting. |
| N-3 | IF-402 v3 says `run_script` returns `{status, stdout, result}`, `failed` included, but the protected mock returns neither `result` nor `failed` (`tests/helpers/mocks/if_402_tool_calls.py:60-63`), the contract suite has no case for `failed`, and the door's `unavailable` output has no `result` (`tool_calls.py:114`). The mock and the door agree only on what the suite tests. | Low | amendment (mock, suite) | Next IF-402 amendment: `result` only when a script ran (say so), mock `failed` for a scripted failing script, a TC for it. |
| N-4 | IF-402 v3 Bounds (`contracts/IF-402-tool-calls.md:35`) "only the text of a web or scholarly query" contradicts REQ-TLS-007 after A-41 (filters, DOI, API key, User-Agent). | Low (D-131) | amendment (contract text) | Align the bound with REQ-TLS-007 at the next IF-402 version. |
| N-5 | The node's `implementation-log.md` has no entry for this round (70a6f35 is logged under N-2.4.1; 191a8f3, A-41, A-42 nowhere in the node log): which test reproduces which finding, and that the lock test cannot fail, stand only in commit messages. | Low | log | Add a section "Verify findings" to the node log with the mapping (incl. the numbering of D-132 vs this report). |
| N-6 | (Info, N-2.4.1 / N-2.4 integration) The runner counts a door tool against its own budget before it calls the door (`pipeline.py:489-497`), so a call the door refuses as `bad_arguments` is counted by the runner anyway. Not a defect of the door (IF-402 "nothing counted" is the door's count). | Info | – | Note for the N-2.4 integration step. |

The new contract test TC-IF-402-07 has no `Example:` line and no Given/When/Then comments (2 more `test_doc_check` errors, 13 in the file, 9 on master); it follows the style of the rest of that protected file. No action proposed.

### Check results
| Check | Result |
|---|---|
| Before/after of the new tests | on 6fa07ff (parent of 191a8f3) with the tests of 191a8f3/0f5050d: `test_tool_calls.py` 1 error (bad arguments), `test_tool_calls_sandbox.py` 1 failure (F-6), IF-402 contract 1 error (TC-IF-402-07 real); the concurrency test passes there. On 160bef6 (parent of 70a6f35): `test_tool_calls.py` ImportError. All green on HEAD. |
| All Python tests in the image (`--init --network none`, one container per side, `python <file> -v`) | goal/v1: 185 files, 2037 tests, 137 skipped; fail: `test_amendment_report` (FromGit, no git in the image), `test_harness` 2 (`test_every_shipped_suite_is_valid`, `test_the_hard_checks_suite_matches_every_time` = F-1). master: 171 files, 1938 tests; fail: `test_amendment_report` (same test), `test_harness` 1 (`test_every_shipped_suite_is_valid`), `test_config` 1, `test_chat_review` 1 (`test_stop_ends_the_wait_with_no_answer`; green on goal/v1). **Per test, goal/v1 adds only F-1's failure.** |
| Node tests | `test_tool_calls*.py` 14 + 6 + 8 + 5 + 6 + 6 = 45 OK; IF-402 14 OK (7 mock, 7 real); IF-404 10 OK, 5 skipped; IF-405 8 OK, 4 skipped; N-2.4 step_00 OK, step_01..03 skipped (`REAL_NODES`) |
| JavaScript (`node --test "tests/js/*.test.mjs" tests/acceptance/contract/*.mjs`) | goal/v1 155 tests, 0 fail, 16 skipped; master 125, 0 fail, 11 skipped |
| Bubblewrap wall on the host (Python 3.14, `test_sandbox.{Policy,Seccomp,Run,Wall,Router}Tests`) | 42 OK |
| trace_check | 93 errors in all; for this node only the older one: its `test-spec.md` has no `## Scenarios` section. `REQ-TO-005` gone. Warnings TD-02, TD-03 "not listed in this report" (deferrals of other nodes: Files tab, token estimate). |
| test_doc_check | `tests/test_tool_calls*.py` 0 errors each; IF-402 contract suite 13 (9 on master, see above) |
| SysML | `check_sysml_model.py` OK; `check_sysml.sh specs/mia/architecture.sysml` 0 errors |
| Protected folders vs master | changes only in `contracts/IF-104`, `IF-402`, `IF-404`, the IF-104 JS suite and mock, `tests/helpers/contract.{py,mjs}`, mocks IF-402 and IF-404, suites IF-402 and IF-404, and one line of `eval/suites/hard_checks/cases.jsonl` (`n-planted-figure`). Installed files equal their drafts: all eight test/helper files equal `specs/mia/contract-drafts/…`; `contracts/IF-402` = `amendments/A-42`, `IF-404` = `A-33`, `IF-104` = `A-36`; `specs/mia/test-spec.md` = `A-42/test-spec.md`. The A-42 install diff adds only TC-IF-402-07, the v3 rows and the mock's argument check. `eval/baselines`, `threat-model.md`, `stages.yaml` unchanged. |

### Proposed status
**Verified with findings** (unchanged), not *Verified*. Everything this round built is green, the new tests fail on the old code where they can, and the protected material changed only by installed amendments. What still blocks *Verified*:
1. F-1: the stage-1 test `test_harness` hard-checks is red on goal/v1; A-40 waits for installation, and D-132's conflict (`open` vs expected `fail`) needs the owner before the replacement test is built.
2. N-1 (Medium): a confident wrong `code` verdict from a string `evidence`.
3. F-11 (THR-001 residual) and F-9's flows: amendments not drafted.
4. F-3, F-4 (FB-03) and G-1..G-4: the owner's deferrals should be listed as accepted deviations with their decision (D-128 for F-3/F-4); G-1 and G-4 have no decision yet.

### Could not check (this round)
Podman wall tests, real web and scholarly requests, the app started with `build_tool_calls` (no network, no services), eval and red-team runs, CI and `merge_gate.py`.
