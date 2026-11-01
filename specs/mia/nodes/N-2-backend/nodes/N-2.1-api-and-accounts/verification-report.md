# Verification report: N-2.1 API and accounts

**Goal:** G-V1 (iteration), supervised; node N-2.1 (leaf of N-2 Backend), verified as a black box against the mocks of its neighbours
**Branch:** goal/v1 @ f4da817   **Parent line of work:** master (53c6766, start of goal/v1)   **Plan baseline:** node plan of 2026-10-26 plus amendments A-04, A-05, A-07, A-21, A-25, A-36, A-51
**Date:** 2026-10-31   **Reviewers:** – (human), Claude Opus 5.5 as independent reviewer (AI; never saw the implementation chat)

Node commits reviewed: on master 24754cc (T-01), 69863dd (T-02), fb83953 (F-3, authors in records), f58d0af (T-03 first slice), 344484c, 2c7e20b, 7ad6187 (deploy and login switch); on goal/v1 (v1-n21, merged in 900ed83) 7452f85 (T-03 rest), bbe695e (T-04), 63cd505 (A-51 draft), bfa1e3e (T-05), 8d9a8ec (hand-over), and f4da817 (A-51 installed).

## Verdict
**Proposed: Not verified yet — verified with accepted deviations once the owner decides F-7 (REQ-API-013) and accepts or routes findings V-1 to V-4.**
14 of 17 requirements have passing evidence that can fail (mutation-checked where cheap). REQ-API-013 has no evidence (F-7, stopped by the implementer, correctly). REQ-API-002 is met for the events IF-101 defines but not for every kind of shared data (Q-T03-1). REQ-API-007 is met with the login switch on; the shipped default is off. No security defect that lets a request past the guard was found; the production wiring in `web_app.py` that carries the guard, the socket guard, the graph routes and the chat attribution has no automated test (V-1).

## Automated checks
| Check | Result |
|---|---|
| Stage log (CI) | No CI for this repo; all runs below are the reviewer's own, in `localhost/mia:latest` (Python 3.12.15) with `--network none`, on `git archive` copies of f4da817 and 53c6766 in the scratchpad |
| Node tests (image) | all OK: test_api_sessions 8, test_accounts_api 31, test_accounts_cli 3, test_internal_auth 3, test_author_in_records 9, test_api_events 5, test_graph_api 7, test_python_version 3 (the in-image check ran, not skipped), test_api_storage_imports 4, test_accounts 5, test_chat_backend 41 |
| Contract suites, Python (mock and real) | IF-101: 60 run, OK, 3 skipped (TC-IF-101-04 N-2.5, -06 N-2.2 T-01, -17 REQ-CHV-008 out of G-V1, D-137). IF-104: 10 OK, 0 skipped (real side via A-51 adapter). IF-203: 8 OK |
| Contract suites, JS | `node --test tests/acceptance/contract/*.mjs`: 32 tests, 16 pass, 16 skipped, 0 fail. The 5 real IF-104 cases skip ("N-2 Backend does not serve the routes of IF-104 yet" in `tests/helpers/contract.mjs`; the reason is stale, the routes exist; a running Backend is needed: integration step of N-2) |
| Full suite, per test, vs master | HEAD: 176 files, 1404 test cases ok, 90 skipped, failures only the known two: `test_amendment_report` (FromGit, no git in the image, ERROR) and `test_harness` (ShippedSuites, rt_edit 2 of 30 cases, FAIL). Master 53c6766 (148 files): the same two plus `test_config` (`test_every_option_the_code_reads_is_in_the_example`, fixed on goal/v1). Per test: no case that passes on master fails on HEAD (the 6 names seen only in the master parse are output interleaved with ResourceWarnings; their files pass on HEAD) |
| Statistical checks, benchmarks, flakiness | none in this node (no model step; IF-104 read bound of 200 ms is a proposal, see V-6) |
| Protected material vs. installed amendments | The five v1-n21 commits touch no protected path. f4da817 changes only `tests/helpers/contract.py`; a fresh `tools/apply_amendment_a51.sh --do` on a copy of f4da817^ gives a byte-identical file (diff empty) and the IF-104 suite 10 OK |
| Traceability (trace_check.py, whole repo) | 93 errors, 250 warnings for the repo; for N-2.1 only two warnings: REQ-API-013 and REQ-API-015 have no `@mark.req` marker (013: no test, F-7; 015: the contract suite marks IF-101, not REQ-API-015) |
| test_doc_check.py on node test files | v1-n21 files clean (test_api_events, test_graph_api, test_python_version, test_api_storage_imports: 0 errors). Older T-01/T-02 files from master: 70 errors (test_accounts_api 40, test_author_in_records 11, test_api_sessions 10, test_accounts_cli 5, test_internal_auth 4): missing docstrings, Example lines, Given/When/Then (V-9) |
| Model consistency | `check_sysml_model.py .` OK. No `.sysml` file changed by this node |
| Architecture rules | `accounts_api.py`, `api_sessions.py`, `graph_api.py`, `internal_auth.py` are not named in any `@Implementation modules` of `architecture.sysml` (V-8). Dependencies: graph_api → workflow_library (IF-203) only; accounts_api → api_sessions → accounts → IF-102 store; no database driver in node modules (TC-API-012 and a reviewer grep) |
| Static / security | No linter or SAST configured (CLAUDE.md). Manual review of guard, sessions, hashing, throttle, proxy trust, internal secret; bad-input probes (below) |
| Dependencies | none added by the node |
| Usability with bad inputs | login with `user` a list or object: **500** (V-3); graph routes: non-number versions → 404, bad body → 422 `node_identity`, `expected_version: "abc"` → 409, encoded `/` in an id → Flask HTML 404 (V-7), 300-character id → 500 from the file backend (storage, not N-2.1) |
| Deployable artifact | image not rebuilt (not needed for the node; existing image used) |

### Mutation runs (scratch copy, each reverted)
| # | Mutation (file:line at f4da817) | Killed by |
|---|---|---|
| M1 | guard lets `/api/workflows`, `/api/context_graphs` pass without session (accounts_api.py:185) | test_graph_api (3 fail), IF-104 suite real (2 fail) |
| M2 | throttle `>=` → `>` (api_sessions.py:45) | test_api_sessions, test_accounts_api, IF-101 suite |
| M3 | throttle only for a wrong password (api_sessions.py:46) | same three |
| M4 | fixed salt (accounts.py:21) | test_accounts (TC-SLY-005); test_api_sessions survives (fine, salting is N-3.1's test) |
| M5 | plaintext password kept in the record (accounts.py:22) | test_accounts, test_api_sessions (TC-API-005) |
| M6 | graph author always "page" (graph_api.py:30) | test_graph_api, IF-104 suite real |
| M7 | `web_app.py:252` chat message stored without author | **survives** all of test_author_in_records, test_api_events, test_accounts_api, test_chat_backend, IF-101 suite |
| M8 | `web_app.py:252` rate key per connection instead of per account | **survives** the same five |
| M9 | `web_app.py:251` no change record for `chat_send` | **survives** |
| M10 | chat_service drops `sender` (chat_service.py:254) | test_author_in_records, test_chat_backend, IF-101 suite |
| M11 | logout keeps the session (api_sessions.py:70) | test_api_sessions, test_accounts_api, IF-101 suite |
| M12 | sockets of a session not disconnected (accounts_api.py:229) | test_accounts_api (3 fail) |
| M13 | every channel counts as secure (accounts_api.py:149) | test_accounts_api (8 fail) |
| M14 | origin check off (accounts_api.py:176) | test_accounts_api |
| M15 | `web_app.py:262` socket guard removed | **survives** test_accounts_api, test_api_events, IF-101 suite |
| M16 | `X-Forwarded-Proto` trusted from anyone (accounts_api.py:159) | test_accounts_api (6 fail) |
| M17 | `web_app.py:667` graph blueprint not registered | **survives** test_graph_api, IF-104 suite, test_api_events, test_chat_page |

The surviving mutants are all in the production wiring of `web_app.py`. The reviewer checked that wiring by hand at f4da817 (scratch copy, the real `web_app` imported with `accounts_enabled: true`, no model server; script kept out of the repo): `/api/workflows` 401 without session; `/` 200; plain-HTTP login from 192.168.1.20 403; login 200; PUT a workflow → version 1, author anna; foreign Origin 403; change log `PUT /api/workflows/w` by anna and `chat_send` by anna; socket without session refused, with session accepted; ack `message.sender` = anna; 13 quick messages → rate refusal; logout 200 drops the socket; history 401 afterwards. So the wiring is right today; nothing keeps it right (V-1).

### Route shadowing by `GET /api/<kind>` (hand-over item 5)
The URL map of the real `web_app` (default config) was dumped in the image. Werkzeug ranks static segments above converters, so every existing route still wins: `/api/items`, `/api/files`, `/api/persona`, `/api/trust`, `/api/presets`, `/api/presets/version`, `/api/chat/history`, `/api/gestures/<name>`, `/api/files/<name>` answer from their own blueprints (checked by request). The kinds `workflows` and `context_graphs` collide with no existing path. The only change of behaviour: a GET (or PUT) on a path that exists only for other methods, or not at all, now gives JSON `404 unknown_kind` where Flask gave HTML 404 or 405 (e.g. `GET /api/vote`, `GET /api/expression/feedback`, `PUT /api/items/x`, `GET /api/login`). No route is shadowed; the 405 → 404 change is harmless but not in IF-104 (V-7).

## Verification matrix
| Requirement | Method | Evidence | Result | Plausible? |
|---|---|---|---|---|
| REQ-API-001 chat events | Test | test_api_events TC-API-001 on the real `web_app`: three sentences reach two pages as growing deltas in order, then `chat_done`; implementer's mutation (emit no-op) red | Pass | yes (scripted exchange; ordering exercised) |
| REQ-API-002 changes reach all devices | Test | TC-API-002 (4): memo save/delete, trust, persona reach a second account's socket within 5 s with author; real guard + real blueprints in a test app | **Partial**: workflow saves (IF-104), presets and gestures emit no event; IF-101 has none for them (Q-T03-1, V-2) | yes |
| REQ-API-003 login | Test | test_api_sessions, test_accounts_api, IF-101 TC-IF-101-01 real | Pass | yes |
| REQ-API-004 throttle | Test | TC-API-004 (service and HTTP), IF-101 real; M2, M3 killed. Code refuses the 6th attempt after 5 failures, matching AC-14 ("the sixth failed attempt … is refused"); the requirement text "more than 5 fail" would allow a 6th — wording only (V-10) | Pass | yes |
| REQ-API-005 password handling | Test, Inspection | TC-API-005 (store and logging after 10 logins), test_accounts; M4, M5 killed; inspection: scrypt n=2^14, r=8, 16-byte random salt, `hmac.compare_digest`, the change log omits login/logout/password paths, no print of the body | Pass | yes |
| REQ-API-006 owner-only accounts | Test | TC-API-006: no `create_account`, `POST /api/accounts` 404; `tools/accounts_cli.py` uses getpass; items/graph routes cannot reach the `accounts` table (kind whitelists) | Pass (by the owner decision of 2026-10-27: CLI only) | yes |
| REQ-API-007 every request authenticated, origin, rate per user | Test | TC-API-007 in test_accounts_api (guard, origin, internal secret); M1, M14 killed. Per-account rate key and socket guard only in `web_app.py`: M8, M15 survive; reviewer's wiring run passes | Pass **with the switch on**; default `accounts_enabled: false` leaves every route open (V-4). Rate value 10/60 s is a config default, not "set in Plan" (V-5) | yes |
| REQ-API-008 secure channel | Test | TC-API-008, proxy-trust tests; M13, M16 killed; wiring run: LAN plain HTTP 403 | Pass | yes |
| REQ-API-009 attribution | Test | TC-API-009 (change log), test_author_in_records (updated_by, sender), test_graph_api (version author), IF-104 real; M6, M10 killed; **M7, M9 survive** (web_app wiring) | Pass, wiring untested (V-1) | yes |
| REQ-API-010 everything visible | Test | TC-API-010 uses a dummy `/api/data` route; real evidence elsewhere: ben edits anna's workflow (test_graph_api), persona by two accounts (TC-API-002); presets across users only at store level | Pass (combined evidence); TC-API-010 itself does not exercise workflow, preset and persona as AC-20 says (V-9) | yes |
| REQ-API-011 Python 3.12 | Test | test_python_version (3, in-image interpreter 3.12.15); full suite in the image passes except the known two | Pass | yes |
| REQ-API-012 storage only via IF-102 | Inspection, Test | test_api_storage_imports (4); implementer's mutation `import sqlite3` red; reviewer grep of node modules: no driver. `library.py` (N-2.4) imports sqlite3 for a rebuildable index (owner/N-2.4 question, not N-2.1) | Pass for N-2.1 | yes |
| REQ-API-013 serve the frontend, container alone | Test (System, stage 3) | **none**: F-7, the container start blocks on the model server (`__main__.py` calibrate); no HTTP mock of IF-103 | **Open** — owner decision | – |
| REQ-API-014 workflow and graph API | Test | test_graph_api (7) on the real guard and library; probes; reviewer wiring run | Pass | yes |
| REQ-API-015 realise IF-101 | Test | IF-101 suite: 57 pass real+mock, 3 skip for other nodes / out of scope | Pass (as far as N-2.1 owns it) | yes |
| REQ-API-016 realise IF-104 routes | Test | IF-104 Python suite 10 OK incl. 5 real (A-51 adapter on the real modules, not on `web_app.py`); JS real side skipped | Pass (Python); JS real side pending at N-2 integration | yes |
| REQ-API-017 logout | Test | TC-API-017 (service, HTTP, sockets), IF-101 TC-IF-101-18 real; M11, M12 killed; wiring run | Pass | yes |

## Test requirements (M41)
No `test-requirements.md` exists in `specs/mia/`; contract-suite fidelity was checked directly: the IF-101 and IF-104 suites run against mock and real (Python). The real IF-104 provider is the adapter of A-51, which composes the real `accounts_api`, `graph_api`, `workflow_library` and storage modules in its own Flask app — real modules, not the `web_app.py` wiring (V-1).

## Goal acceptance (node level)
| Item | Result |
|---|---|
| Requirements in scope verified | 14 pass, 1 partial (002), 1 pass with switch only (007, counted in the 14 with V-4), 1 open (013) — of 17 |
| Frozen requirements unchanged | no requirement file changed by the v1-n21 commits |
| Protected checks identical to installed amendments | yes (A-51 re-install identical) |
| Nothing outside the node's parts touched | v1-n21 touched `graph_api.py` (new), `web_app.py` (2 lines), tests, README/requirements.txt (D-63), the node log, A-51 draft files. In bounds |
| Stop conditions logged | F-7 stopped and logged, not worked around; Q-T03-1, IF-104 bounds, library.py logged |
| Exit criterion | checked in Validate (VAL-…) |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-API-013 AC-29 | container alone does not serve the page (F-7) | owner decision (A-52 / requirement / accept) |
| specified, not done | REQ-API-002 "shared data" | workflow, preset and gesture changes emit no event | owner: define "shared data" or amend IF-101 with an event |
| done, not specified | message rate limit (10 per 60 s, `chat_rate_per_minute`) | value not in plan/IF-101; refusal ack has no `code` (`{"ok": false, "error": "Too many messages…", "code": null}`); IF-101 lists no rate-limit error | Phase 2 amendment (value and code, e.g. 429 `rate_limited`) |
| done, not specified | 422 rules `budget_tokens`, `variant` from the library pass through IF-104 | IF-104 lists five rules only | Phase 2: add to IF-104 or document "rules of IF-203" |
| done, not specified | 404 `unknown_kind` JSON for every unmatched GET/PUT under `/api/` | was HTML 404/405 | amendment note in IF-104, or accept |
| done, not specified | `immutable` → 409 in `graph_api.STATUS` | not in IF-104 | accept or amend |

Human review: specification side via `review-log.md`; code read for marked items: none marked.

## Quality evidence per characteristic (M32)
| Characteristic | Requirement(s) | Evidence | Result | Gap or `not now` |
|---|---|---|---|---|
| Functional suitability | REQ-API-001…017 | matrix above | 14/17 | 013 open, 002 partial |
| Performance efficiency | IF-104 bounds (proposal) | probe: 5,000-node graph saved in 0.06 s | not a requirement | bounds not set (V-6) |
| Compatibility | REQ-API-015, -016 | contract suites mock+real | pass | JS real side at N-2 integration |
| Interaction capability | – | error codes in JSON | mostly | V-3, V-7 |
| Reliability | REQ-API-017; F-4 sessions in memory (decided) | tests | pass | restart logs out (accepted) |
| Security | REQ-API-003…009, 017 | tests + 13 killed mutants + wiring run | pass with switch on | V-1, V-3, V-4; no SAST tool configured |
| Maintainability | – | test_doc_check | v1-n21 clean | V-8, V-9 |
| Flexibility | – | – | – | not now (no requirement) |
| Safety | – | – | – | not now (no requirement) |

## Open deferrals (M26)
| TD | Requirement | Interim criterion verified? | Target check state | Trigger |
|---|---|---|---|---|
| – (skip) | IF-101 TC-04, -06, -17 real | other nodes | skip with reason | N-2.5, N-2.2 T-01, next iteration |
| – (skip) | IF-104 JS real side | Python real side passes | skip, stale reason | N-2 integration |

## Review findings
| # | Finding | Severity | Resolution / destination |
|---|---|---|---|
| V-0 | REQ-API-013 has no evidence (F-7): `__main__.py:76` `comm.calibrate()` needs a model server; no HTTP mock of IF-103 | High (requirement unverified) | Owner decision. Reviewer agrees with the implementer's option (a) A-52, an HTTP stand-in of IF-103 plus a stage-3 test; (c) is acceptable only as an accepted deviation with SMOKE-MIA-003 + stack as evidence |
| V-1 | The production wiring in `web_app.py` is untested: lines 249–252 (chat author, per-account rate key, change record), 261–262 (socket guard), 667 (graph blueprint), 676–683 (guard install). Mutants M7, M8, M9, M15, M17 survive the whole suite; only `tools/check_accounts_real.sh` (needs Ollama, manual) covers it | Medium | Needs test (Phase 3, N-2.1): a component test that imports the real `web_app` with `accounts_enabled: true` and a temp config/data dir (as the reviewer's scratch run did, no model needed), asserting 401 on `/api/workflows`, refused socket, `sender` and change record of `chat_send`, per-account rate key, logout drop. The config must not be written into the checkout (copy or env override); if that needs a change of `web_app`'s config loading, that is the owner's call |
| V-2 | REQ-API-002 partial: workflow saves (IF-104), presets, gestures emit no IF-101 event (Q-T03-1) | Medium | Owner decision: narrow "shared data" in REQ-API-002 to the IF-101 kinds, or amendment adding e.g. `workflow_changed {kind,id,version,author}` to IF-101 with a contract case |
| V-3 | `api_sessions.py:43,48`: `self._failed.get(user)` with a JSON list/object `user` raises TypeError → 500 instead of 401 `bad_credentials` (IF-101). No bypass. `test_a_bad_body_is_a_401_and_not_a_crash` tries `user: 5` only | Low | Needs test (Phase 3): add `{"user": ["anna"]}` and `{"user": {}}` to that test, then check `isinstance(user, str)` before the throttle lookup |
| V-4 | REQ-API-007 holds only with `accounts_enabled: true`; the shipped default (`setup_cfg.example.json:85`, `deploy/setup_cfg.compose.json:118`) is false, so every route incl. IF-104 PUT is open to the LAN without session or origin check | Medium (security posture) | Owner decision: accept as a deviation for G-V1 (the switch and `up.sh login on` exist, D-146), or a requirement that the stack starts with the login on |
| V-5 | REQ-API-007 AC "the rate limit value is set in Plan": not set; code uses `chat_rate_per_minute` default 10 per 60 s; the refusal ack has no `code` and IF-101 has no rate-limit error | Low | Amendment (Phase 2): fix the value and an error code in IF-101 |
| V-6 | IF-104 bounds (500 nodes, 200 ms read) are "proposal, set in Plan"; not enforced (5,000 nodes accepted) | Low | Owner decision: set them in Plan (then a test) or drop them from the contract |
| V-7 | IF-104 edge behaviour not in the contract: ids with `/` (`%2F`) cannot be addressed (Flask HTML 404); unmatched `/api/...` GET/PUT now JSON 404 `unknown_kind` instead of HTML 404/405; library rules `budget_tokens`, `variant` and code `immutable` pass through | Low | Amendment note in IF-104 (id charset, rule list), or accept |
| V-8 | `accounts_api.py`, `api_sessions.py`, `graph_api.py`, `internal_auth.py` have no `@Implementation` part in `architecture.sysml` (WebApplication lists chat, presets, …) | Low | Phase 2: add the parts/modules (then `check_sysml.sh`) |
| V-9 | Test readability: 70 test_doc_check errors in the T-01/T-02 test files (master); TC-API-010 uses a dummy route rather than the workflow, preset and persona routes of AC-20 | Low | Backlog: docstrings and Given/When/Then; TC-API-010 on the real blueprints when V-1's wiring test exists |
| V-10 | REQ-API-004 text "more than 5 fail" vs AC "the sixth failed attempt is refused" and code (6th refused) | Low | Amendment: align the text to "after 5 failed logins" |
| V-11 | Stale skip reason for the JS real side of IF-104 in `tests/helpers/contract.mjs:9` ("does not serve the routes yet") | Low | Protected: change at the N-2 integration step with the real adapter |
| Note | `library.py` imports sqlite3 (index cache) vs root AC-15 | – | Owner / N-2.4, not N-2.1 |
| Note | `accounts_api.py:18,22` imports `time` twice | – | none (style) |

## Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| (candidate) V-4 login off by default | trusted home network, switch exists | – |
| (candidate) V-0 option (c) if chosen | – | – |

## Not checked
- The browser pages themselves, the HTTPS proxy and `tailscale serve` (what `remote_addr` the backend sees through rootless podman port publishing: if the publish rewrites the source to 127.0.0.1, a LAN plain-HTTP login would count as local — check in Phase 6 with the stack).
- `tools/check_accounts_real.sh` (needs Ollama; not run by rule) — replaced by the reviewer's wiring run without a model.
- The JS real side of IF-104 (needs a running Backend).
- No SAST/lint tools are configured; review was manual.

## Notes for Phase 7 (validation)
- Sessions live in memory: a restart logs everybody out (F-4, decided).
- The per-account throttle lets anyone lock an account for a minute by guessing (by design of REQ-BE-009); watch whether users notice.

---

# Re-verification (2026-10-31)

**Branch:** goal/v1 @ 3ef5af3 (bc6df53, which followed during the review, changes only docs of N-1.1/N-4.1 and the review log)   **Previous report:** goal/v1 @ f4da817 (above)
**Plan baseline:** as above plus amendments A-52 (IF-103 HTTP stand-in), A-54 (IF-101 v12), A-57 (v13), A-61 (v14), A-60 (IF-104 TC-IF-104-06, JS), A-53/55/56/58/59 (other nodes; shared helpers)
**Decisions read:** D-131, D-146, D-147, D-149, D-153 (corrects D-149 on V-10), D-158 (N-3.1 F3), D-160/D-162 (session limits through IF-104)
**Reviewer:** Claude Opus 5.5, independent (AI; never saw the implementation chat)

Commits reviewed: branch v1-n21b (merged in 131efdd): e440a24, 30a1b40, 7fb8ac9, fcbe633, 5c982a7, 8e467ee, 979d9fd, 10ca9bf, baa1234, 2a637ba; later goal/v1 commits on the node's files: d4e8fbd (N-3.1 F3, `accounts.create` with `expected_version=0`), fda514a and 0442a40 (N-3.2, new cases in `tests/test_graph_api.py`), 348175f (V-8, model); installs a262376, 424c329, 849ac36.

## Verdict
**Proposed: Verified with accepted deviations.** All 17 requirements now have evidence that can fail; every finding of the first report is closed by a test that was seen to fail under a mutation, accepted by the owner (V-4, D-149) or decided (V-2, V-6 by D-147; V-10 by D-153). What is still open: the IF-104 JS real side and the N-2 integration step 5 (both belong to the N-2 integration, V-11), and six new low findings (R-1 to R-6). None of them lets a request past the guard.

## Automated checks (re-run)
| Check | Result |
|---|---|
| Environment | No CI. Reviewer's runs on a `git archive` copy of 3ef5af3 in the scratchpad, Python tests in `localhost/mia:latest` (built 2026-10-31 22:03 local; contains the v1-n21b and d4e8fbd code, checked by grep) with `--network none`; TC-API-013 on the host with podman |
| Protected material vs. installed amendments | Only three commits since f4da817 touch protected paths: a262376, 424c329, 849ac36. Re-installing the drafts with the amendment scripts (`--do`, trailing test run cut off) on copies of the parents: a262376^ + A-52, A-53, A-54, A-57, A-55, A-56, A-58 gives the tree of a262376 byte for byte, except `tests/helpers/mocks/if_103_model_server_http.py` (installed separately by 424c329; equal to its draft). 849ac36^ + A-59, A-60, A-61 gives 849ac36 byte for byte. Installed IF-101 is **v14** (A-61), not v15 |
| Node tests (image) | all OK: test_api_sessions 8, test_accounts_api 30, test_accounts_cli 3, test_internal_auth 3, test_author_in_records 9, test_api_events 5, test_graph_api 10, test_python_version 3, test_api_storage_imports 4, test_accounts 6, test_chat_backend 43, **test_accounts_wiring 6** (new), test_runbook 9; test_container_alone skips in the image (no podman, as intended) |
| TC-API-013 on the host | `python3 tests/test_container_alone.py`: **2 OK in 12 s** (pod on 127.0.0.1, stand-in + image as it is; no pod left). Red check: MIA pointed at a port without the stand-in → error after 33 s ("stopped before the page was served"); restored |
| Contract suites, Python (mock and real) | IF-101 64 run, OK, 2 skipped (TC-IF-101-04 N-2.5, -17 REQ-CHV-008 out of G-V1); IF-104 10 OK; IF-203 8 OK; IF-102 20 OK |
| Contract suites, JS | 34 tests, 17 pass, 17 skipped, 0 fail; IF-104 real side still skipped with the stale reason (V-11) |
| N-2 integration steps | step_00 OK; steps 01-05 skip ("N-2.5, N-2.3, N-2.2, N-2.1 not integrated yet"): the N-2 integration has not started |
| Neighbouring web tests (image) | test_chat_page 11, test_presets_api 28, test_chat_mock_server 13, test_web_app_wiring 3, test_frontend_delivery 2 (1 skip), test_first_account 9, test_graph_rules 12, test_items_api 9, test_trust_persona_api 11, test_gestures_api 27, test_files_api 4: all OK |
| Full suite | not re-run (the previous full run and the implementer's run after v1-n21b had only the known two failures; the later goal/v1 changes on node files are covered by the runs above) |
| Traceability (`trace_check.py`) | repo 96 errors, 271 warnings. For N-2.1: REQ-API-013 has markers now; REQ-API-015 still no `@mark.req` (the suite marks IF-101; as before); ERROR "test-spec.md: 17 checks but no `## Scenarios` section" (M39; the same for every node test-spec in the repo, a plan-wide gap, not a node regression); WARN TD-01..TD-04, TD-06 not listed here (none concerns N-2.1, listed below) |
| test_doc_check | 0 errors for every N-2.1 test file (test_api_sessions, test_accounts_api, test_accounts_cli, test_internal_auth, test_author_in_records, test_api_events, test_graph_api, test_python_version, test_api_storage_imports, test_accounts_wiring, test_container_alone, test_runbook); was 70 (V-9 closed). `tests/test_accounts.py` (N-3.1's TC-SLY file) 9 errors, older cases, not this node |
| Model consistency | `check_sysml_model.py .` OK; `architecture.sysml:272,276,280` name `api_sessions.py`, `internal_auth.py`, `accounts.py`, `accounts_api.py`, `graph_api.py` (V-8 closed by 348175f) |

### Mutation runs on the fixes (scratch copy, each reverted)
| # | Mutation | Killed by |
|---|---|---|
| N1 | `api_sessions.py:42-43` type check of `user` removed (V-3) | test_accounts_api |
| N2 | `chat_service.py:220` refusal without `"code": "rate_limited"` (V-5) | test_chat_backend, test_accounts_wiring; **survives** the IF-101 suite (R-2) |
| N3 | `graph_api.py:78` catch-all route moved away (V-7) | test_graph_api; IF-104 suite survives (it has no slash case; fine) |
| N4 | `accounts.py:41` `expected_version=0` dropped (N-3.1 F3) | test_accounts |
| N5 | `web_app.py:290` socket guard removed (old M15) | test_accounts_wiring (3 fail, 1 error) |
| N6 | `web_app.py:696` graph blueprint not registered (old M17) | test_accounts_wiring |
| N7 | `web_app.py:280` rate key per connection (old M8) | test_accounts_wiring |
| N8 | `web_app.py:279` no change record of `chat_send` (old M9) | test_accounts_wiring |
| N9 | `web_app.py:280` message without author (old M7) | test_accounts_wiring |

## Earlier findings
| # | State | Evidence |
|---|---|---|
| V-0 (REQ-API-013) | **closed** | A-52 installed (equal to draft); TC-API-013 green on the host, red with the stand-in unreachable |
| V-1 (wiring untested) | **closed** | `tests/test_accounts_wiring.py`, imports the real `web_app` from a temp folder (writes nothing into the checkout: checked); N5-N9 killed |
| V-2 (REQ-API-002 partial) | **decided** (D-147: shared data = IF-101's events) | but the requirement's history line that D-147 asks for is missing (R-4) |
| V-3 (500 on non-string user) | **closed** | 7fb8ac9; N1 killed; probe: list, object, null, number as `user` and a list as password → 401 `bad_credentials` |
| V-4 (login off by default) | **accepted** (D-149) | README "The login", RUNBOOK line, `test_runbook` |
| V-5 (rate value, code) | **closed** | REQ-API-007 AC names 10 per 60 s, `web_app.py:687` default 10; IF-101 v12 (A-54) installed; N2 killed by unit tests |
| V-6 (IF-104 bounds) | **decided** (D-147: proposal, measured in Validate) | – |
| V-7 (`%2F` ids) | **closed** | 8e467ee; N3 killed; only `workflows`/`context_graphs` prefixes caught; restore/history/diff routes still win (test_graph_api, IF-104 suite) |
| V-8 (model) | **closed** | 348175f; model check OK |
| V-9 (test docs, TC-API-010) | **closed** | 0 doc errors; TC-API-010 on the real workflow, preset and persona routes in test_accounts_wiring (implementer's mutation red; reviewer did not repeat it) |
| V-10 (throttle wording) | **closed** (D-153) | REQ-API-004 text and AC-14 say "after 5 failures the 6th attempt is refused"; code unchanged (`api_sessions.py:47` `>=`); TC-IF-101-02 real green. The text's end "until fewer than 5 of its failed logins are younger than one minute" matches the code (the refused attempt is not counted) |
| V-11 (stale JS skip) | **open** | at the N-2 integration step (D-149) |

## Verification matrix (changes only)
| Requirement | Evidence now | Result |
|---|---|---|
| REQ-API-002 | as before; scope narrowed to IF-101's events by D-147 | Pass (by D-147); history line missing (R-4) |
| REQ-API-004 | text aligned (D-153); TC-API-004, TC-IF-101-02 real | Pass |
| REQ-API-007 | + test_accounts_wiring (socket guard, per-account rate over three sockets, 11th `rate_limited`); value fixed in the AC | Pass (with the login on; off by default is the accepted deviation V-4) |
| REQ-API-009 | + test_accounts_wiring (`sender`, change record of `chat_send`); N8, N9 killed | Pass |
| REQ-API-010 | TC-API-010 on the real routes (test_accounts_wiring) | Pass |
| REQ-API-013 | TC-API-013 on the host, 2 OK, red when the model server is unreachable | **Pass** (stage 3, host only; see R-5) |
| REQ-API-014 | + `%2F` ids → JSON 404 (V-7); N-3.2's new session-limit and malformed-stop cases in test_graph_api pass through IF-104 | Pass |
| REQ-API-016 | Python suite 10 OK; JS real side skipped | Pass (Python); JS real side at the N-2 integration |
Unchanged rows (001, 003, 005, 006, 008, 011, 012, 015, 017): Pass as in the first report; their tests pass again.

## Per-commit review
| Commit | Finding |
|---|---|
| e440a24 TC-API-013 + A-52 draft | in bounds; the test skips (never passes) without podman, image or stand-in; the stand-in is standard library, bound to 127.0.0.1 inside the pod. Stage: R-5 |
| 30a1b40 wiring test | correct; isolated from the checkout (verified: no new files after the run) |
| 7fb8ac9 V-3 | correct; a non-string user no longer counts as a failure of `""` (no account can have that name) |
| fcbe633 V-4 docs | as D-149 asks |
| 5c982a7 V-5 + A-54 draft | code correct; A-54 reused the id TC-IF-101-30 (R-1); the real side of the new case cannot fail on the code (R-2) |
| 8e467ee V-7 | correct; `POST` on the catch-all is needed for `restore` with a slash id |
| 979d9fd, baa1234, 2a637ba | log and requirement text only; REQ-API-004 matches D-153 |
| 10ca9bf V-9 | docstrings only (implementer's AST check); TC-API-010 moved to real routes |
| d4e8fbd (N-3.1) | correct for both backends: `storage.py:85` and the Postgres primary key both give `conflict` for `expected_version=0` on an existing record; mapped to the same `ValueError` as the pre-check, so `accounts_cli` and `first_account` behave as before (test_accounts_cli, test_first_account green) |
| fda514a, 0442a40 (N-3.2) | new test_graph_api cases (malformed stop, bool limits) go through `graph_api.py` unchanged; green |

## New findings
| # | Finding | Severity | Destination / proposal |
|---|---|---|---|
| R-1 | Duplicate test-case ids in the protected IF-101 suite: `TC-IF-101-30` at `tests/acceptance/contract/test_if_101_chat_api.py:518` (v8, task files) and `:563` (v12 rate limit, A-54); `TC-IF-101-09` at `:104` and `:156` (older). `specs/mia/test-spec.md:91` has only the A-54 row for -30; rows -20 to -29 are missing (noted in A-54's log entry) | Low (traceability) | Amendment: renumber A-54's case to TC-IF-101-33 (and one -09), add the missing test-spec rows |
| R-2 | The real side of the rate-limit case cannot fail on the code: `tests/helpers/contract.py:329` maps a refusal without `code` to 429 `rate_limited`; mutant N2 passes the IF-101 suite (held only by test_chat_backend and test_accounts_wiring) | Low (contract fidelity) | Amendment: the adapter maps a missing code to a distinct error (e.g. 500 `no_code`), so the real side checks the code |
| R-3 | `api_sessions.py:46` `self._failed[user] = recent` keeps an entry for every user name ever tried and never drops it; probe: 3,000 distinct wrong names → 3,000 entries. Anyone who can reach `/api/login` (local or via HTTPS/Tailscale, login on) grows the backend's memory without limit | Low (untrusted input; D-131 lowers the stakes) | Needs test (Phase 3): failures older than 60 s leave no entry (e.g. 1,000 names, clock + 61 s, one more login → `len(_failed)` ≤ 1), then drop empty lists; or the owner accepts |
| R-4 | D-147 asks for a history line in REQ-API-002 ("shared data" = IF-101's events; presets, gestures, workflows re-read when opened); `requirements.md:31` still says `History: –` | Low (spec text) | Phase 2 text fix, no test |
| R-5 | TC-API-013 is stage 3 in the node test-spec but `stages.yaml` has no step for it; it runs only inside `unit` (stage 1, `stages.yaml:21`) on a host with podman and skips in the image | Low | Amendment of `stages.yaml` (a stage-3 step `python3 tests/test_container_alone.py`), or the owner accepts host-only runs |
| R-6 | `tests/test_api_events.py` (TC-API-001/002) imports `web_app` with the checkout's config and writes into `data/` of the checkout (`editor_token.txt`, `library.sqlite`, seeded presets, `db/workflows/review.json`), as the other older `web_app` tests do; test_accounts_wiring shows how to avoid it | Low | Backlog: reuse the temp-folder fixture of test_accounts_wiring |
| Note | IF-101 is v14 (A-61), not v15 | – | – |
| Note | `trace_check` ERROR "no `## Scenarios` section" holds for every node test-spec | – | plan-wide (M39), not this node |

## Open deferrals (M26)
| TD | Concerns N-2.1? | State |
|---|---|---|
| TD-01, TD-02 (browser harness), TD-03 (token estimate), TD-04 (lookup glue), TD-06 (library folder) | no | open, owned by other nodes |
| IF-104 JS real side (skip) | yes | at the N-2 integration step (V-11) |

## Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| V-4: with `accounts_enabled` off (shipped default) every route is open | trusted users (D-131); documented with how to turn the login on | owner, D-149 |
| (candidate) R-3 if not fixed | trusted users | – |

## Not checked
- The browser pages, the HTTPS proxy, `tailscale serve`, and what `remote_addr` the backend sees through rootless podman publishing (as before; Phase 6).
- The IF-104 JS real side and the N-2 integration steps 1-5 (not started).
- `tools/check_accounts_real.sh` (needs Ollama).
- No full-suite re-run; no SAST tools configured.
