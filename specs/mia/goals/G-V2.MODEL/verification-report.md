# Verification report: G-V2.MODEL (skill record and graph model), first run

**Goal:** G-V2.MODEL (subgoal of G-V2), supervised
**Branch:** goal/v2.model @ `b36b053` (code unchanged since `5382d28`)   **Parent line of work:** master (`b250450`, STORE merged)   **Plan baseline:** `plan-baseline-it2-model-installed` (`97146b4`)
**Date:** 2026-11-08   **Reviewers:** (human review pending), Claude Sonnet 5.5 (AI, fresh Verify session, no part in the implementation)

## Verdict
**Not verified.** Reasons that remain (all in the table of findings):
1. F-01: the "maximum time" half of REQ-WFM-048 does not work with the field the owner confirmed (`max_seconds`); the code looks for `max_time`.
2. F-02 and F-03: REQ-WFM-042 compares raw command strings only (case, slash, old-form skills), and a record command the task registry cannot handle breaks chat parsing (`KeyError`) or takes over a command.
3. F-05: `GraphRunner.run` reports "done" for a graph with a cycle and skips the nodes of the cycle (`IndexError` when one of them is untrusted).
4. Open decisions for a person: F-04 (context graph ID not taken from the record), TC-WFM-047 and TR-MODEL-003 changed after approval and to be re-approved, together with TR-MODEL-001 (A-105).
Everything else is green: all 14 checks, the adapter test on the file backend and PostgreSQL, the full unit suite, the contract suites, the protected-material diff, the model checks. No accepted deviation exists for this goal.

## Automated checks (local run, clean `git archive HEAD` in the scratchpad; no CI run)
| Check | Result |
|---|---|
| Stage log | not available (no CI); the steps of `stages.yaml` stage 1 to 3 run by hand below |
| `test_graph_model.py` (10), `test_graph_run.py` (4) | OK, both |
| `tests/test_skill_record_storage.py` | 20 tests OK: file backend 10, PostgreSQL 10, not skipped (verbose run) |
| `tests/test_skill_catalog_loader.py`, `test_extension_loader.py`, `test_task_registry.py`, `test_chat_tasks.py` | 5, 8, 8, 12 tests OK |
| `tests/test_storage_postgres.py` | 43 tests OK, not skipped |
| Full unit suite `python -m unittest discover -s tests -q` (clean checkout, alone) | 2169 tests OK, skipped 4, expected failures 2 (the tailscale test of A-143 is among them; I did not identify the other); 497 s |
| All acceptance files, one process each | all OK |
| Contract suites, mocks / real | 130 / 130 OK; real: 17 skipped, all for external services (model server, web client, scholarly APIs, one express variant of IF-101), none for IF-102/IF-301 |
| `MIA_DB_PYTHON=... bash tools/contract_postgres.sh` | 11 tests OK |
| JavaScript tests | 163 of 163 OK |
| Statistical check TC-WFM-047 (seeds 1 to 200, 100 with, 100 without a cycle) | run once as part of the acceptance file and of the unit suite: 0 failures; no re-run needed; seeds and n unchanged |
| Protected material vs `b250450` (`tests/acceptance`, `tests/helpers`, `tests/smoke`, `contracts`, `benchmarks`, `eval/suites`, `eval/baselines`, `stages.yaml`, `plausibility.yaml`, `deferred.md`, STORE's `storage.py`, `graph_tables.py`, `storage_copy.py`, also `graph_rules.py`, `pipeline.py`, `library.py`, `requirements.txt`) | empty diff |
| Three red-test files vs `plan-baseline-it2-model-installed` | empty diff |
| Changes of `test-requirements.md`, `plan.md`, `review-log.md` since the tag | `test-requirements.md`: only TR-MODEL-001 (A-105); `plan.md`: `5f13e3e` (plan approval of 2026-11-07, no amendment id), A-105, A-106, A-107; `review-log.md`: D-306, D-307, D-308 appended. See F-10 for TC-WFM-047 / TR-MODEL-003 |
| `plausibility.yaml` vs master | no change (0 removed, 0 rating changed); all 14 MODEL requirements have a record, rater `maldun`, rating plausible. `req_plausibility.py` 9 errors, all REQ-WFM-130..138 (PANEL, not ours) |
| `trace_check.py` | 547 errors; the sorted error list is **identical** to a `git archive` run of master `b250450` (it also has 547, including TC-SLY-012..014; the brief's "544 + 3" is the same set). None for REQ-WFM-040..049, REQ-RUN-016..019, TC-WFM-040..049, TC-RUN-016..019, TR-MODEL-001..005. No new error |
| `goal_check.py` and `--parent-ref master` | one error GL1 "G-V2, G-V3: more than one open iteration goal" (old, D-271), nothing for MODEL |
| `req_graph.py` | 28 errors as baseline, none for MODEL ids |
| `req_lint.py` | MODEL requirements: only INFO lines (L1-COMPOUND, L1-PRONOUN); the 55 errors are L0-GROUP of old requirements |
| `req_review.py status` | changed since review: TR-MODEL-001, TC-WFM-047, TR-MODEL-003 (cause: F-10); nothing marked by me |
| `test_doc_check.py` | 0 errors for `test_graph_model.py`, `test_graph_run.py`, `test_skill_record_storage.py`, `test_skill_catalog_loader.py` |
| `check_sysml_model.py`, `check_sysml.sh` | OK; 4 files, 0 errors, 0 warnings |
| Static / security (`bandit`, `vulture`, `ruff`) | not run: not installed in the venv. By hand: no subprocess, file deletion, environment, network or secret in the new code (grep over the diff); see F-05, F-06 for robustness |
| Documentation, deployable artifact | not run (no user-visible documentation changed; no image build in scope) |

## Verification matrix
| Requirement | Method | Evidence | Result | Result plausible? (vs plausibility.yaml) |
|---|---|---|---|---|
| REQ-WFM-040 skill record | Test | TC-WFM-040 on fake, file backend, PostgreSQL; read back equal, edit = version 2, version 1 stays | Met; author never tested (F-08) | yes, "no number depends on it" |
| REQ-WFM-041 skill taken from its record | Test | TC-WFM-041 (catalog), 4 loader tests, `ast` test of `web_app.py` | Partly: command and workflow graph yes, context graph ID taken by nothing (F-04); real start of `web_app` not hand-checked | yes |
| REQ-WFM-042 command used once | Test | TC-WFM-042 on all three sides; probes | Met for the tested case; weaker than the text for case, slash and old forms (F-02, F-03) | yes |
| REQ-WFM-043 three node types | Test | TC-WFM-043; probes (unknown type, no `data`) | Met; malformed nodes raise (F-06) | yes |
| REQ-WFM-044 graph description | Test | TC-WFM-044 on three sides; version-pinned read | Met; missing key raises (F-06) | yes |
| REQ-WFM-045 alternate | Test | TC-WFM-045; self-loops, unknown endpoint, probes | Met | yes |
| REQ-WFM-046 one writer | Test | TC-WFM-046; probes | Met | yes |
| REQ-WFM-047 no cycle | Test, property | 200 seeds, 5-node cycle, three hand-drawn graphs (2, 4 and 4 nodes, tails): cycles named correctly | Met; recursion limit at about 1000 chained nodes (F-06) | yes |
| REQ-WFM-048 master stops | Test | TC-WFM-048 (`max_repetitions` only) | **Not met for the maximum time** (F-01) | yes |
| REQ-WFM-049 parameters | Test | TC-WFM-049 on three sides | Met | yes |
| REQ-RUN-016 order | Test | TC-RUN-016; mutants (order reversed, edge swapped) killed | Met for graphs without a cycle; F-05 | yes |
| REQ-RUN-017 untrusted | Test | TC-RUN-017 incl. twin; trust called for every non-data node before any node; unreachable untrusted node refuses | Met; test gaps F-09; first status only (open question 2) | yes |
| REQ-RUN-018 master like transform | Test | TC-RUN-018; "master run twice" mutant killed | Met | yes |
| REQ-RUN-019 failed node stops | Test | TC-RUN-019; "does not stop" and "wrong node" mutants killed | Met | yes |

## Test requirements (M41)
| Test requirement | Source | Kind | Applies to | Credibility aspect | Verified by | Met? (evidence) |
|---|---|---|---|---|---|---|
| TR-MODEL-001 fake with known gap, same scenarios on the real Storage | product-specific (A-105) | setup | TC-WFM-040, 041, 042, 044, 049 | stand-in fidelity | adapter test | Met: `tests/test_skill_record_storage.py` runs the five scenarios on fake, file backend and PostgreSQL, compares IDs, flags, versions; the differences found (fake takes records the record checks refuse; duplicate IDs; empty IDs; `max_time`) are pinned or listed in F-01, F-07. Text changed by A-105: back in review |
| TR-MODEL-002 every refusal has an accepted twin | product-specific | setup | TC-WFM-042, 043, 045, 046, 048 | power and false-alarm rate | mutation | Met: twins present; mutants "refuse everything" (T-01, T-02, T-04) killed |
| TR-MODEL-003 cycle check on generated graphs | product-specific | setup | TC-WFM-047 | repetitions and seeds | known answer and mutation | Met: 100/100 graphs, fixed 5-node cycle, order checked as "every edge points forward" in the test, not by the function. Known answer: no test in the repository, I ran three hand-drawn graphs (probe) and mutants (cycle check removed, first id not repeated, order reversed) are killed. Text changed after approval: F-10 |
| TR-MODEL-004 scripted nodes, observable effects | product-specific | setup | TC-RUN-016..019 | stand-in fidelity | review | Met: scripted nodes, order list, marker file in a fresh folder, no model |
| TR-MODEL-005 IDs and versions exact, wording not | product-specific | unit | TC-WFM-040, 042, 043, 045, 046, 048, TC-RUN-017, 019 | reference accuracy | review | Met: tests compare IDs, flags, versions; the rule and detail of a Storage refusal are compared with the Storage's own, never a sentence |

## Goal acceptance (M34, M36)
| Item | Result |
|---|---|
| Requirements in scope verified (count / total) | 11 / 14 fully; REQ-WFM-041 partly (F-04), REQ-WFM-048 not for the maximum time (F-01), REQ-WFM-042 per text only with F-02 |
| Frozen requirements unchanged vs. parent's line of work | Yes: no frozen requirement in this goal; IF-301 and IF-203 (frozen at G-V2): `contracts/` empty diff, requirement files, `architecture.sysml` unchanged vs `b250450` |
| Protected checks identical to the parent's baseline | Yes (empty diffs above) |
| Nothing outside the goal's parts touched | Yes: code diff vs `b250450` is `graph_model.py`, `skill_record.py`, `graph_run.py`, `extension_loader.py`, `task_registry.py`, `web_app.py` (2 lines), the two new test files, three amendment scripts and notes. `requirements.txt` untouched (see F-11) |
| Every stop condition logged (not worked around) | Yes: T-05 and T-06 stops are A-105 and A-107; the T-05 finding 3 is A-106. No implementation-log.md exists for the goal; the hand-over file and the amendment notes serve (see F-11) |
| Exit criterion met (or: checked in Validate) | OC-1 to OC-3 per requirement above; VAL-009 is checked in the Validate of G-V2 |
| Accepted by (unsupervised goal; at the merge) | not applicable, supervised |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-WFM-048 | maximum time with `max_seconds` | Implement fix (F-01) |
| specified, not done | REQ-WFM-041 | context graph ID not taken from the record | Plan amendment (F-04) |
| specified, not done | REQ-WFM-042 | "a skill with another ID" includes skills of the old forms; case and slash | Plan amendment, then Implement (F-02) |
| specified, not done | REQ-RUN-016 | a graph with a cycle is not run in an order and is reported as done | Implement fix (F-05) |
| done, not specified | form of a command | any string is a command; the loader strips a leading slash, the registry lowercases | Plan amendment (F-03) |
| done, not specified | `GraphModel` / `SkillRecords` | `author` optional, default None; empty graph, empty node list and a transform with no input accepted; duplicate node IDs collapsed before the type check; unchanged re-save writes new versions of every member | Plan amendment or backlog (F-07, F-08) |
| done, not specified | `GraphRunner` | any status other than "trusted" counts as untrusted (fail closed); trust callback exceptions propagate; a node failure drops the error text; data node `value` of the stored graph is not used as start value; a missing input is silently left out | keep fail-closed; state it in Plan; rest backlog (open question 1) |
| done, not specified | `extension_loader` | `lstrip("/")` of the record's command becomes the task ID; a failing catalog disables every extension | F-03, F-06 |

Human review: specification side via `review-log.md` (not done by me). Code read for marked items: none are marked (`Code review: needed` appears on no MODEL requirement).

## Quality evidence per characteristic (M32)
| Characteristic | Requirement(s) | Evidence | Result | Gap or `not now` |
|---|---|---|---|---|
| Functional suitability | all 14 | tests above, probes, 53 mutants | see findings | F-01, F-02, F-04, F-05 |
| Performance efficiency | none | none stated | not applicable | not now |
| Compatibility | IF-301 v2, IF-102 (records, `ids`, `put` with author) | adapter test on both backends | met; `max_time` vs `max_seconds` contradicts IF-301 (F-01) | |
| Interaction capability | none | refusals name IDs; messages not compared | not applicable | |
| Reliability | REQ-RUN-019 | tests, probes | failed node stops; F-05, F-06 for malformed input | |
| Security | REQ-RUN-017 | marker file test; fail-closed status; untrusted text from records is data | met; no new tool, network or write access given by a record | `Quality:` lines for REQ-WFM-040 and REQ-RUN-017 left out by the owner's decision of 2026-11-08: a known gap |
| Maintainability | -- | small modules (157, 84, 53 lines), `test_doc_check` clean | met | |
| Flexibility | -- | node field names confirmed by the owner | met | |
| Safety | -- | -- | not applicable | |

## Open deferrals (M26)
None for this goal (`deferred.md` unchanged).

## Review findings
Direction: SnD = specified, not done; DnS = done, not specified. Severity high / medium / low. A proposed failing test follows each row.

| # | Finding | Severity | Resolution / destination |
|---|---|---|---|
| F-01 | **Commit `0fefbe3`, `graph_model.py:91-92` (and docstring line 9); REQ-WFM-048; SnD.** `check_graph` accepts a master node only with `max_repetitions` or `max_time`. IF-301 v2 (`graph_tables.py:42`) and the owner-confirmed names say `max_seconds`. Probe on fake and real: stop `{"max_seconds": 5}` (valid for the record check) is refused naming the master node; stop `{"max_time": 5}` passes the graph rules, is accepted by the fake and refused by the real Storage with `schema_break` / `stop`. The tests only use `max_repetitions`, so all mutants of this rule are killed but this defect is invisible. *Test:* in the adapter test, a graph with a master node and stop `{"max_seconds": 5}` is saved on the fake and on both real backends and is accepted (version 1), and a twin with `{"max_time": 5}` is refused naming `M1`. | high | Implement fix (reopen T-01) |
| F-02 | **Commit `23bbfe5`, `skill_record.py:41`; REQ-WFM-042; SnD.** The clash check compares the raw `command` strings of records only. (a) `/Lookup` after `/lookup`, and `lookup` after `/lookup`, are accepted, although the registry parses case-insensitively and the loader strips the slash, so these are one command. (b) A skill that exists only as extension manifest (old form, e.g. `beta`) counts as "a skill with another ID" in the text but is not compared: a record of `alpha` with command `/beta` is stored and, loaded, registers `alpha`'s code under `beta`; the real `beta` fails with "task id already in use" and is gone. *Test:* store `lookup` with `/lookup`, then `review` with `/Lookup` and with `lookup`: both refused naming `lookup`; with a legacy manifest `beta`, a record `/beta` for another ID is refused naming `beta`. | medium | Plan amendment (which skills count, how commands are normalised), then Implement |
| F-03 | **Commit `5382d28`, `extension_loader.py:67`, `task_registry.py:76-80`; REQ-WFM-040/041/042; DnS.** The form of a command is not specified, the record accepts any text (also empty). Probes: `/Lookup` or `/ALPHA2` makes `TaskRegistry.parse("/lookup x")` raise `KeyError` (names are stored with case, looked up lowercased); `""` and `/` register a task with the empty ID that then answers `/` and `/ text`; `/a b` becomes an unreachable task; a clash with an alias or another task ID raises in `register`, the skill is dropped (problem list only) although its manifest form was fine. Records are untrusted data and now decide task IDs. *Test:* load an extension whose record has command `/Lookup`: `parse("/lookup x")` must not raise; empty and `/` commands must be refused at `store` or not registered. | medium | Plan amendment (command rule), then Implement |
| F-04 | **Commit `5382d28`, `extension_loader.py:67`, `task_registry.py`; REQ-WFM-041; SnD.** The text says command, workflow graph and context graph come from the record. `SkillCatalog.list()` returns ID and command, `start()` the workflow graph ID, `Task` gets `workflow_graph_id`; nothing delivers the context graph ID. No check demands it (AC-31 is only about listing and running). *Test:* `SkillCatalog.start` (or a new `read`) returns the context graph ID of the record, or the Plan states that the context graph is read by CONVERT. | low | Plan amendment (decide, or reword to what is built) |
| F-05 | **Commit `e282e65` / `5d5405f`, `graph_run.py:26-44` with `graph_model.order_of`; REQ-RUN-016, 017; SnD.** `order_of` silently leaves out the nodes of a cycle. `GraphRunner.run` of a graph with a cycle returns status `done` and runs only the other nodes (probe: `D1 -> T1 -> D1`: `done`, T1 not run); with an untrusted node inside the cycle `named` is empty and `named[0]` raises `IndexError` (line 36); an edge to an unknown node raises `KeyError` (line 29). Graphs saved through `GraphModel` cannot have a cycle, but the runner takes any dict and IF-102 writers (graph API) do not run the rules of T-01 (D-262). *Test:* `run` of a cyclic graph, with and without an untrusted node in the cycle, returns status `failed` or `refused` (decision by Plan) and never `done`; no node of the other part runs on partial data. | medium | Implement fix (reopen T-03) |
| F-06 | **Commits `0fefbe3`, `b648a3e`, `112b6b0`; REQ-WFM-043, 044, 047, 040; DnS (robustness).** Malformed input raises instead of a refusal: node `data` of None (`AttributeError`), edge without `from`, graph without `nodes` or on the real Storage without `testbench_id` (`KeyError`), skill without `command` (`KeyError`); `_find_cycle` is recursive and raises `RecursionError` for a chain of about 1100 nodes; if the catalog raises (storage down), `load_extensions` skips every extension, also those without a record. *Test:* each malformed graph/record gives `saved=False` with a named item; a 3000-node chain is accepted; with a failing catalog, skills without a record are still registered. | low | Implement fix or backlog |
| F-07 | **Commits `24afde1`, `0fefbe3`; REQ-WFM-040, 043..049; DnS.** (a) An unchanged re-save writes new versions of all nodes and edges (two saves give node version 2, the graph version 3 after a third). (b) A refusal after the node pre-check (edge or header) leaves the written members as unused versions (probe: D1 history length 4). (c) Duplicate node or edge IDs are collapsed by the rule check (a bad type hidden behind a duplicate is not seen); the fake saves them, the real Storage refuses with `record_identity` after writing the members. (d) Node and edge records are global by ID: two graphs with a node `D1` share one record history. (e) The empty graph and a graph of one node are accepted. Known and noted by the Implement session (hand-over), D-264 designs (d). | low | Backlog; Plan amendment if (c) or (e) must be refused |
| F-08 | **Commits `23bbfe5`, `112b6b0`, `24afde1`, `5382d28` (`web_app.py:679`); IF-102 `put(..., author)`; DnS.** `SkillRecords` and `GraphModel` take `author=None` by default and write with it; the Storage accepts None. No test checks the stored author: mutants "author not passed" (skills, nodes/edges, header) survive. *Test:* after `store` and `save_graph` on the real Storage, `get(...)["author"]` and `history` name the caller's account; a write without author is refused. | low | Implement fix (tests, optional required author) |
| F-09 | **Tests (T-04, T-07, T-05); REQ-RUN-017, REQ-WFM-043.** Mutants that survive, 9 of 53 (see below): `named` order and `named_status` with more than one untrusted node (3 mutants); `!= "trusted"` replaced by `== "untrusted"` (equivalent for the two defined statuses; a gap only if fail-closed is wanted); the `except StorageError` branch of `save_graph` (an edge or header refusal) is untested: "refusal swallowed" and "refusal raised" survive; "node pre-check removed" survives because the test checks only that no header exists, not that no node record was written. *Tests:* two untrusted nodes (`named` in topological order); status `"revoked"` refuses; a graph with an edge record the Storage refuses is `saved=False` with rule and detail; after a refused bad node `ids("graph_nodes") == []`. | low | Implement (tests only) |
| F-10 | **Review log; TC-WFM-047, TR-MODEL-003, TR-MODEL-001.** Approved in `913bd34` (2026-11-07 20:12); their text changed in `2b5acd8` (20:36, "owner: odd cycles break REQ-WFM-045") without an amendment id; TR-MODEL-001 changed by A-105. The three come back in `req_review` as changed. Not a code defect. | low | Owner re-approves in review (I marked nothing) |
| F-11 | **Plan and architecture text.** (a) `plan.md` T-01 and `goal.md` (Dependencies: networkx "real") say `networkx` is added; the code uses its own search and `requirements.txt` is unchanged (no new dependency: good, the text is stale). (b) `architecture.sysml` lists none of `graph_model.py`, `skill_record.py`, `graph_run.py` as modules of a part (`pipelineRunner`, `skillStore`, `workflowGraph`); the model checks pass because they do not look for them. (c) The goal has no `implementation-log.md`; the hand-over holds the log. | low | Plan amendment (text and model) |

### Mutants (scratch copy of `git archive HEAD`, goal's tests incl. file backend of the adapter test)
53 mutants, 44 killed, 9 survived. Killed: T-01 each rule removed or inverted (type, alternation, writers, master stop, cycle, cycle not closed, order reversed, edge direction swapped, "refuse everything"); T-02 clash removed, clash with itself, version always 1, record loses to old forms, read ignores version, `start` always None / for unknown, "refuse everything"; T-03 order reversed, master run twice, failed node does not stop, wrong node named; T-04 only transforms checked, "refuse everything"; T-05/T-07 `ids` not used, members not pinned, read ignores graph version, rules not checked before write, header kind, edges not pinned, skill refusal raised; T-06 catalog ignored, command not used, graph ID not set, slash kept, skill without a record changed, default graph ID changed, `web_app` catalog not passed or over another store.
Survivors: (1) `== "untrusted"` instead of `!= "trusted"`: equivalent for the defined statuses, F-09. (2) `named` in reverse order and (3) wrong `named_status` for several untrusted nodes: gap, F-09. (4) to (6) author not passed in skills, nodes/edges, header: gap, F-08. (7) refusal swallowed and (8) raised in the `except` branch of `save_graph`: gap, F-09. (9) node pre-check removed: gap (only the header absence is asserted), F-09. The T-01 order oracle "sorted ids" is killed only by the adapter test, not by the acceptance test (generated graphs have ID order equal to a valid order): not a defect, TR-MODEL-003 as written.

## Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| none | | |

## Notes for Phase 7 (validation) and open questions
- Facts, not findings: `goal.md` still shows Implement `open` and Plan `in progress` (the owner updates it). The "listed by its command" wording of A-107 note point 1 and of the T-06 test (3) text in `plan.md` is too strong: decision (c) lists a record-only skill through `SkillCatalog.list()` only, the tests pin that; a plan amendment should correct the wording, no code change.
- The owner's decisions held: node field names (but see F-01 for the stop field), a refused skill or graph record is a `StoreResult` / `SaveResult` with rule and detail and not an exception (tested on both backends), no `Quality:` lines for REQ-WFM-040 and REQ-RUN-017 (a known gap), record-only skills stay in the catalog until CONVERT, "untrusted" means any status other than "trusted" in REQ-RUN-017.
- Question 1 for the owner: the glossary and REQ-WFM-051 know two statuses only (untrusted, trusted). The runner refuses everything else (also None and "Trusted"), which is fail-closed and sound; the requirement text says "whose status is untrusted". Keep and state it in Plan, or restrict?
- Question 2: `named_status` holds only the status of the first refused node (topological order). The requirement says "naming the node and its status". With two untrusted nodes of different status the second status is lost. Does it need a per-node answer?
- Not run or not decidable here: the real start of `web_app.py` with the catalog (only an `ast` test shows the wiring; hand-check at Deploy); `ruff`/`bandit`/`vulture` (not installed); documentation and clean-machine walkthrough; the human review of the specification side; CI stage log.
- For users to judge: command names with capitals or spaces in a skill record; what a record-only skill should do when started (nothing today).
- The stored graph is not re-checked on read; the Graph app (IF-104/IF-203) writes through IF-102 and bypasses the rules of T-01 by design (D-262). Validate should ask whether the runner must be the second guard (F-05).
