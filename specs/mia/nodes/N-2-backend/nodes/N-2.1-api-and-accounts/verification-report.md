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
