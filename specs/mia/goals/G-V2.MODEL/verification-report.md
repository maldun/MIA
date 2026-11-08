# Verification report: G-V2.MODEL (skill record and graph model), first run

**Goal:** G-V2.MODEL (subgoal of G-V2), supervised
**Branch:** goal/v2.model @ `b36b053` (code unchanged since `5382d28`)   **Parent line of work:** master (`b250450`, STORE merged)   **Plan baseline:** `plan-baseline-it2-model-installed` (`97146b4`)
**Date:** 2026-11-08   **Reviewers:** (human review pending), Claude Sonnet 5.5 (AI, fresh Verify session, no part in the implementation)

> The verdict of the first run below is superseded by the sections **Second run** (after T-08, `49c18b4`) and **Third run** (after T-09, `e42de62`, merge `735c983`) at the end of this file. Finding IDs are kept; the current verdict and the status of every finding are in the Third run.

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

---

## Second run (after T-08)
**Branch:** goal/v2.model @ `5152013` (code unchanged since `49c18b4`; `git diff 775ec90..HEAD` touches `extension_loader.py`, `graph_model.py`, `graph_run.py`, `skill_record.py`, three test files, `plan.md` and the brief only)   **Date:** 2026-11-08   **Reviewer:** Claude Sonnet 5.5 (AI, fresh Verify session, no part in the implementation); human review pending.
Owner decisions of 2026-11-08 used as given: fix F-01, F-02, F-03, F-05; an unknown trust status stays refused (fail safe); `named_status` stays one value; the re-save and orphan versions of F-07 are a known property; F-04, F-06, F-08 to F-11 are not part of T-08.

### Verdict (second run)
**Not verified.** Reasons that remain:
1. F-13 (medium, new, regression of T-08): a failing catalog (storage down) now makes `load_extensions` raise out of `web_app.py` at import; before T-08 every skill was skipped with a problem line and the app started.
2. F-14 (medium, new, residual of F-02 b): a record command that is an alias of a manifest-only skill is accepted by the store and by the loader; with the record skill sorted first, the real manifest skill (`lookup`, alias `research`) is dropped and its alias belongs to the record skill.
3. F-10: TC-WFM-047, TR-MODEL-003 and TR-MODEL-001 still wait for the owner's re-approval (`req_review.py status`: changed since review).
F-01, F-02 (a), F-03 and F-05 are closed by my own probes. The remaining open items are all low except F-13 and F-14 (table below). **If F-13 and F-14 are fixed, the other open findings (F-04, F-06, F-07 c to e, F-08, F-09, F-11, F-12, F-15, F-16) are low and could be accepted by the owner, giving 'Verified with accepted deviations'; F-10 is an owner approval, not a deviation.** No deviation is accepted yet (the owner's decisions above are scope decisions, not acceptances of open findings).

### Automated checks (clean `git archive HEAD` in the scratchpad `vm2/head`)
| Check | Result |
|---|---|
| `trace_check.py` | 547 errors, sorted list **identical** to a `git archive` run of master `b250450`; none for REQ-WFM-040..049, REQ-RUN-016..019, TC-WFM-040..049, TC-RUN-016..019, TR-MODEL-001..005 (the new test file adds no error) |
| `goal_check.py` and `--parent-ref master` (in the worktree) | only GL1 "G-V2, G-V3 open" (old); nothing for MODEL |
| `req_graph.py` | 28 errors as baseline, none for MODEL ids |
| `req_review.py status` | changed since review: TR-MODEL-001, TC-WFM-047, TR-MODEL-003 (F-10); nothing marked by me |
| `test_doc_check.py` on `test_graph_run_findings.py`, `test_skill_record_storage.py`, `test_skill_catalog_loader.py`, `test_graph_model.py`, `test_graph_run.py` | 0 errors, 0 warnings |
| Goal tests, one process each | `test_graph_model` 10, `test_graph_run` 4, `test_graph_run_findings` 5, `test_skill_catalog_loader` 7, `test_extension_loader` 8, `test_task_registry` 8, `test_chat_tasks` 12: all OK |
| `test_skill_record_storage.py` verbose | 26 tests OK: 13 scenarios on the file backend and 13 on PostgreSQL, none skipped |
| `test_storage_postgres.py`, `contract_postgres.sh` | 43 OK; 11 OK |
| Contract suites mock / real | 130 / 130 OK (17 skipped for external services, as before); `run_integration_steps.py`: 23 python + 4 javascript steps, 0 failed |
| All acceptance files, one process each | all OK (`test_benchmarks.py`: one expected failure, as before) |
| JavaScript tests | 163 of 163 OK |
| Full unit suite alone | 2182 tests OK, skipped 4, expected failures 2; 494 s (first run 2169: the 13 new tests) |
| TC-WFM-047 statistical check (seeds 1 to 200, 100 + 100 graphs) | run once (acceptance file and unit suite): OK, no re-run needed; seeds and n unchanged |
| Protected material vs `b250450` (list as in the first run, also `graph_rules.py`, `pipeline.py`, `library.py`, `requirements.txt`) | empty diff |
| Three red-test files vs `plan-baseline-it2-model-installed` | empty diff |
| `plausibility.yaml`, `architecture.sysml` vs `b250450` | no change; `test-requirements.md` only the A-105 change |
| `check_sysml_model.py`, `check_sysml.sh` | OK; 4 files, 0 errors, 0 warnings |
| `ruff`, `bandit`, `vulture`, `req_lint.py`, `req_plausibility.py` | not run again (not installed / no spec or plausibility file changed since the first run); by hand: the diff adds no subprocess, file deletion, environment, network or secret |

### Status of the findings
| # | Status | Evidence of this run |
|---|---|---|
| F-01 | **Closed** | Probe `p_f01.py`, forms `max_repetitions`, `max_seconds`, `both`, `max_time`, `{}`, `None`, missing: the rule and the saves agree on the fake, the file backend and PostgreSQL (`p_pg.py`): the first three and "both" are saved, `max_time`, `{}`, `None`, missing and `max_seconds: 0` are refused naming `M1`. A refused graph leaves no node record. Remaining difference: F-16 |
| F-02 | **(a) closed, (b) partly: F-14** | Store on fake, file backend and PostgreSQL: `/Lookup`, `LOOKUP`, `lookup`, `//lookup` refused naming `lookup`; clash is checked before the form check; a skill with several records is compared by its latest version only (`review` takes the old command `/lookup` of `lookup` after `lookup` moved to `/two`: accepted, by design). Loader: record command equal to a manifest-only folder name is skipped with a problem, the manifest skill stays. Alias of a manifest: F-14 |
| F-03 | **Closed** (code); F-15 low residue | Store refuses `""`, `/`, `/a b`, `//a`, `/Alpha`, tab, NBSP, NUL with rule `schema` on both sides; every command the store accepted was registered by the loader under `normal_command` and found by `parse` (40 commands, `p_f02.py`); records written around the store (`""`, `/`, `/a b`, `//a`, `/Alpha`) register nothing and give one problem line each, the other skills load. The rule is in `plan.md` T-08 only; REQ-WFM-040/041 do not state the command form (note for Plan) |
| F-04 | **Open**, low | unchanged: nothing delivers the context graph ID (`SkillCatalog.start` returns the workflow graph ID only) |
| F-05 | **Closed**; F-12 low regression | `p_f05.py`: cycle of 2 and 4 nodes, self-loop on a transform and on a data node, a cycle in a disconnected part next to a good part, untrusted node inside a cycle, unknown edge end (both directions): status `refused`, named = edge IDs for unknown ends, the cycle with the first ID repeated otherwise, `named_status` None, no node ran, the trust callback was not called (also when it raises). Empty graph, one data node, isolated nodes, a duplicate node ID: unchanged behaviour (`done`). A trust callback that raises on an acyclic graph still propagates before any node ran (unchanged) |
| F-06 | **Open**, low; T-08 widened it (F-12, F-13) | `_find_cycle` still raises `RecursionError` at about 1000 chained nodes (`check_graph` 1100: raises); malformed input still raises (edge without `id` and an unknown end: `KeyError`; graph without `nodes`: `KeyError`) |
| F-07 | **(a), (b) decided by the owner (known property); (c), (d), (e) open**, low | code unchanged |
| F-08 | **Open**, low | mutants "author not passed" (skills, graph nodes and edges, header) survive again |
| F-09 | **Partly closed**, low | killed now: `named` order, `named_status` of the first node, `!= "trusted"` replaced by `== "untrusted"` (test with status `revoked`). Still surviving: the `except StorageError` branch of `save_graph` (swallowed, raised), node pre-check removed; new gaps in the T-08 tests: `named` of a cycle is only compared as a set (the repeated first ID is not pinned), `named_status` None for a cycle, the trust callback is not asserted to be uncalled before a cycle refusal |
| F-10 | **Open, owner's** | unchanged (`req_review.py status`) |
| F-11 | **Open**, low | `architecture.sysml` and `plan.md` text unchanged; `goal.md` still shows Implement `open`, Plan `in progress` |
| F-12 | **New**, low | below |
| F-13 | **New**, medium | below |
| F-14 | **New**, medium | below |
| F-15 | **New**, low | below |
| F-16 | **New**, low | below |

### New findings
| # | Finding | Severity | Destination |
|---|---|---|---|
| F-12 | **`graph_run.py:30` (`_find_cycle` import, commit `49c18b4`); REQ-RUN-016; regression.** The recursive `_find_cycle` is now called by every `GraphRunner.run`: a chain of 1100 nodes (and 3000) raises `RecursionError` before any node ran. At `775ec90` the same graphs ran (`done`, 550 and 1500 transforms; probe `p_old_chain.py`). The private import across modules (`_find_cycle`) is a note: acceptable inside the Workflow management, but it ties the runner to the recursive search. *Test:* `run` of a 3000-node chain of alternating data and transform nodes returns `done` (or `refused` with a named reason), never raises; the fix can use `order_of` (iterative): nodes missing from the order are the cycle. | low | Implement fix |
| F-13 | **`extension_loader.py:61-64` (`manifest_only = {... catalog.start(n) ...}` before the loop, commit `49c18b4`); REQ-WFM-041; regression of F-06.** The new loop over all folders runs outside the per-skill `try`. If the catalog raises (storage down, `records.ids()` raising, probes `p_loader_reg.py`, `p_loader_old.py`), `load_extensions` raises `ConnectionError`; `web_app.py:680` calls it at import, so the app does not start. At `775ec90` the same failure was caught per skill (`alpha: storage down`) and the app started without the extensions. A catalog that returns an odd value (`""`, `0`, `True`) gives `not_found` problems per skill in both versions (no change). *Test:* `load_extensions` with a catalog whose `start` raises returns one problem per skill and raises nothing; skills without a record still load if only `records.read` fails. | medium | Implement fix |
| F-14 | **`extension_loader.py:62-72`, `skill_record.py:56-61`; REQ-WFM-042; DnS residual of F-02 (b).** The loader refuses a record command only when it equals the folder name of a manifest-only skill. The aliases of a manifest are not compared (`lookup` has `["research"]`). Probe: record of `alpha` with `/research`, extension `lookup` manifest-only: `alpha` sorts first, registers `research`; `lookup` fails with "task id 'research' is already in use" and is gone (ids `['research']`). With a record skill sorted after the manifest skill the record skill is dropped (reported). The store cannot see aliases. *Test:* extensions `alpha` (record `/research`) and `lookup` (alias `research`, no record): `lookup` is registered, `alpha` is skipped with a problem naming `research`, in both folder orders. | medium | Implement fix (compare with the names of the already registered or manifest tasks, aliases included) |
| F-15 | **`skill_record.py:26-34` (`command_problem`); REQ-WFM-041; low.** The docstring says "a command the task registry can register and parse", but 23 lower-case characters pass the check (`µ`, `ı`, `ſ`, `ς`, `ϐ`, `ϑ`, `ϕ`, `ϖ`, `ϰ`, `ϱ`, `ϵ`, `ι` and the combining `ͅ`, Cyrillic `ᲀ`-`ᲈ`, `ẛ`) for which `TaskRegistry.parse` raises `KeyError` on user text in another case (`/ς x` registered, user types `/Σ x`; `p_uni.py` over all code points to U+2FFFF). The final sigma matters for Greek commands. Also: `/model` and similar names are accepted but shadowed by the argument commands of the chat service (skill unreachable, no error). *Test:* load a record command `/ς`; `parse("/Σ x")` must not raise (refuse such characters, or compare case-folded). | low | Implement fix or backlog |
| F-16 | **`graph_model.py:89-92` (T-01 rule); REQ-WFM-048; low.** The rule tests only truthiness. Property probe (600 random stops: `max_repetitions`, `max_seconds`, `max_time`, `max_cycles`, `x` with 0, 1, -1, 0.5, 2.5, True, False, "5", "", None, [], {}, 10**12, inf): in 123 cases the rule and the fake accept and the real Storage refuses with `schema_break` (negative, boolean, fractional or string values, a non-integer repetition count); in 0 cases the rule refuses what the Storage accepts. The real save is refused with a rule and writes nothing, so no data is lost; this is the known gap of the fake (TR-MODEL-001). *Test:* adapter test: `{"max_repetitions": -1}` and `{"max_seconds": True}` are refused on the fake as on the Storage, or pinned as a listed difference. | low | Backlog or pin in the adapter test |

### Regression review of `git diff 775ec90..HEAD`
- Done, not specified: the command form rule (`command_problem`) and the extra `catalog.start` pass exist only in `plan.md` T-08, not in the requirement texts; the loader skips a whole skill (also its manifest form) when its record is bad, as T-08 states (a note: a bad record disables a working skill). No new default or output otherwise. `normal_command` uses `str(command)`, so a non-string is refused by the form check, not raised.
- The skipped skill's `register` hook is not run; this matches the earlier behaviour of a skill whose `register()` of the task failed (checked by probe).
- Behaviour for skills without a record: none. The repository's real `extensions/` folder (`lookup`, `review`, `search`) loads to the same tasks, aliases, versions, options and names with `catalog=None`, with an empty catalog and with an unrelated record (`p_real_ext.py`: identical).
- The private import `_find_cycle`: note inside F-12.

### Mutants (second run; scratch copy of `git archive HEAD`, goal's five test files, file backend of the adapter test)
89 mutants: the 53 of the first run (49 patterns still applicable, 4 rebuilt for the changed code) and 36 new for the T-08 code. 76 killed, 13 survived.
| Group | Result |
|---|---|
| T-01 (11 rules and order), T-02 (7), T-03 (4), T-04 (5), refuse-everything (3) | all killed |
| T-05/T-07, T-06 | killed except the survivors below |
| T-08 new: normal form without `lower()`, without `lstrip`; clash on raw commands; clash after the form check; form check removed; empty / space / second slash / capital / `//` each allowed; loader: problem ignored, manifest-only clash ignored, set empty, set inverted, raw command as ID, skipped skill still registered; `max_seconds` check inverted, `max_time` again, `max_seconds` ignored; runner: cycle check removed, moved after the trust check, cycle or unknown edge not refused, one end only, nodes named instead of edges, status `failed`, refusal that still runs, unknown/cycle order inverted | all 33 killed |
Survivors (13): (1) to (3) author not passed in skills, nodes/edges, header: gap, F-08. (4), (5) refusal swallowed / raised in `save_graph`: gap, F-09. (6) node pre-check removed: gap, F-09. (7) cycle named without the repeated first ID: gap in the T-08 test (set comparison), F-09. (8) `named_status` set for a cycle refusal: gap, F-09. (9) trust callback called before a cycle refusal: gap, F-09. (10) `values` empty after a cycle refusal: not specified, equivalent for the tests. (11) loader `lstrip("/")` instead of `normal_command`: equivalent (a command that passes `command_problem` is lower case with at most one slash). (12) manifest-only check including the skill itself: equivalent (a skill with a record is never in the set). (13) a no-op control mutant: equivalent by construction. The nine survivors of the first run: `== "untrusted"`, `named` order and `named_status` are now killed by the owner's pins; the other six survive (3 author, 2 refusal branch, 1 pre-check).

### Not run
`ruff`, `bandit`, `vulture` (not installed); real start of `web_app.py` with a failing catalog (shown at the loader level only); CI stage log; documentation and clean-machine walkthrough; the human review. The mutants ran on the file backend of the adapter test only (the PostgreSQL class runs the same code and was run unmutated).

### Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| none | | |


---

## Third run (after T-09)
**Branch:** goal/v2.model @ `d88dd3b` (code unchanged since `e42de62` and the merge `735c983`; `git diff f11fa10..HEAD` on code: `extension_loader.py`, `graph_model.py`, `graph_run.py`, `skill_record.py`, `task_registry.py` and three test files)   **Baseline for diffs and trace_check:** master `66fc76a`   **Date:** 2026-11-08   **Reviewer:** Claude Sonnet 5.5 (AI, fresh Verify session, no part in the implementation); human review pending.
Owner decisions of 2026-11-08 used as given: fix F-12 to F-16 and the three T-08 test gaps in T-09; F-14: skip the record, keep the manifest skill; F-04, F-06, F-07 (c) to (e), F-08, F-11 are not fixed (the owner decides whether to accept them as deviations); F-10 is the owner's.

### Verdict (third run)
**Not verified.** Reasons that remain:
1. F-17 (medium, new, regression of T-09): a record whose command is an alias of its OWN manifest (`lookup` has the alias `research`, record command `/research`) is refused by the loader, and because the record is refused the whole skill is dropped (registered ids: none; at `f11fa10` it was registered). The brief required that a record does not clash with itself.
2. F-10: TC-WFM-047, TR-MODEL-003 and TR-MODEL-001 still wait for the owner's re-approval (`req_review.py status`: changed since review).
F-12, F-13, F-14 (as specified: skip the record, keep the manifest skill), F-15 and F-16 are closed by my own probes. The two other new findings (F-18, F-19) are low. **If F-17 is fixed, the other open findings (F-04, F-06 remainder, F-07 c to e, F-08, F-09 remainder, F-11, F-18, F-19) are all low and could be accepted by the owner, giving 'Verified with accepted deviations'; F-10 is an owner approval, not a deviation.** No deviation is accepted yet (the owner's decisions above are scope decisions).

### Automated checks (clean `git archive HEAD`, scratchpad `vm3/head`; master `66fc76a` in `vm3/master`)
| Check | Result |
|---|---|
| `trace_check.py` | 547 errors, sorted list **identical** to a `git archive` run of master `66fc76a`; none for REQ-WFM-040..049, REQ-RUN-016..019, TC-WFM-040..049, TC-RUN-016..019, TR-MODEL-001..005 |
| `goal_check.py` | only GL1 "G-V2, G-V3 open" (old) |
| `req_graph.py` | 28 errors as baseline |
| `req_review.py status` | changed since review: TR-MODEL-001, TC-WFM-047, TR-MODEL-003 (F-10); nothing marked by me |
| `test_doc_check.py` on `test_graph_run_findings.py`, `test_skill_record_storage.py`, `test_skill_catalog_loader.py`, `test_graph_model.py`, `test_graph_run.py` | 0 errors, 0 warnings |
| Goal tests, one process each | `test_graph_model` 10, `test_graph_run` 4, `test_graph_run_findings` 7, `test_skill_catalog_loader` 12, `test_extension_loader` 8, `test_task_registry` 8, `test_chat_tasks` 12: all OK |
| `test_skill_record_storage.py -v` | 30 tests OK: 15 on the file backend and 15 on PostgreSQL, none skipped |
| `test_storage_postgres.py`, `contract_postgres.sh` | 43 OK (not skipped); 11 OK |
| Contract suites mock / real | 130 / 130 OK (17 skipped for external services, as before); `run_integration_steps.py`: 23 python + 4 javascript steps, 0 failed |
| All acceptance files, one process each | all OK (`test_benchmarks.py`: one expected failure, as before) |
| JavaScript tests | 163 of 163 OK |
| Full unit suite alone | 2193 tests OK, skipped 4, expected failures 2; 491 s (second run 2182: the 11 new tests) |
| TC-WFM-047 statistical check (seeds 1 to 200, 100 + 100 graphs) | run once (acceptance file and unit suite): OK, no re-run needed; seeds and n unchanged |
| Protected material vs `66fc76a` (acceptance, helpers, smoke, contracts, benchmarks, eval suites and baselines, `stages.yaml`, `plausibility.yaml`, `deferred.md`, `storage.py`, `graph_tables.py`, `storage_copy.py`, `graph_rules.py`, `pipeline.py`, `library.py`, `requirements.txt`, `architecture.sysml`) | empty diff |
| Three red-test files vs `plan-baseline-it2-model-installed` | empty diff |
| `check_sysml_model.py`, `check_sysml.sh` | OK; 4 files, 0 errors, 0 warnings |
| `ruff`, `bandit`, `vulture` | not installed, not run; by hand: the diff adds no subprocess, file deletion, environment, network or secret |

### Status of the findings
| # | Status | Evidence of this run |
|---|---|---|
| F-01 | **Closed** | unchanged since the second run; the T-09 stop rule is covered under F-16 |
| F-02 | **Closed** | (a) as before. (b) aliases: record `/research` for `alpha` with a manifest-only `zeta` alias `research` (and the folder orders alpha/zeta both ways, `p_f14.py` cases 1a, 1b, 1c with `/Research`): the record skill is skipped with a problem, the manifest skill and its alias stay. Folder names: 5a, 5b same. Alias of a skill that has a record (case 3) is also kept. Swaps (alpha `/zeta`, zeta `/alpha`; alpha `/zeta`, zeta `/other`) load. Residue: F-17 |
| F-03 | **Closed** | see F-15 |
| F-04 | **Open**, low | unchanged |
| F-05 | **Closed** | unchanged; with F-12 the runner refuses cycles of 1101, 3001 and 20001 nodes (named = the cycle, `named_status` None, no node ran) |
| F-06 | **Open**, low (narrower) | the recursion part is gone (F-12). Remaining: malformed input still raises (code lines unchanged: edge without `id`, graph without `nodes`, `n["data"]` None); the F-13 part is closed |
| F-07 | **(a), (b) decided by the owner; (c), (d), (e) open**, low | code unchanged |
| F-08 | **Open**, low | mutants "author not passed" (skills, graph nodes and edges, header) survive again |
| F-09 | **Partly closed**, low | the three T-08 gaps are killed now (cycle named without the repeated first ID, `named_status` set for a cycle, trust callback called before a cycle refusal). Still surviving: the `except StorageError` branch of `save_graph` (swallowed, raised) and the node pre-check removed. New gaps from the T-09 mutants: see the survivor list |
| F-10 | **Open, owner's** | unchanged (`req_review.py status`) |
| F-11 | **Open**, low | `architecture.sysml` and `plan.md` text unchanged; `goal.md` still shows Implement `open`, Plan `in progress`. The command form and the stop rule exist only in `plan.md` T-08/T-09 and IF-301 v2, not in the texts of REQ-WFM-040/041/042/048 (042 names "a command that a skill with another ID already uses": nothing on case, slash, folder names or aliases; 048 says "neither ... nor": nothing on zero, negative, boolean or fractional values). **Plan note**: the requirement texts should state the command form and the stop values, or say that the rules of IF-301 v2 and the plan hold |
| F-12 | **Closed** | `p_f12.py`, `p_f12b.py`, `p_f12d.py`: chains and cycles of 1100, 3000 and 20000 nodes in `find_cycle`, `check_graph`, `GraphRunner.run` (chain: `done` with 550 / 1500 / 10000 transforms run, cycle: `refused`), `save_graph` on the fake and the file backend (chain saved, cycle refused naming the cycle); no RecursionError anywhere (the 20000-node real save takes more than 10 s because of 40000 file writes: linear cost, not a hang). `p_f12e.py`: 30000 random graphs (shuffled ID order, multi-edges, self-loops, 9814 with a cycle), seed 20261108: `find_cycle` equals the old recursive `_find_cycle` of `775ec90` in every case, the cycle list identical. No `_find_cycle` is left in the code |
| F-13 | **Closed** | `p_f13.py` (three skills, two with records): `start` raising `ConnectionError`, `ValueError`, `KeyError`, `RuntimeError`, `RecursionError`, `MemoryError`, `OSError`, `AttributeError`, `TypeError`, `StopIteration`, `UnicodeDecodeError` for one skill: the app loads, the other record skills keep their record commands (`one`), the failing skill is registered as its manifest says and one problem line names it; `start` raising for all skills and `records.ids()` raising: all three registered as manifests, three problem lines; `start` returning `""`, `0`, `True`, `"g"`, `5`, `[]`, `{}`, `b"x"`, `nan` and `read` raising for one skill: the other record skills keep theirs, one problem line for the odd one. A record without a usable command is skipped with one problem line |
| F-14 | **Closed** (as decided: record skipped, manifest skill kept) | see F-02 (b), `p_f14.py`: aliases, folder names, normal form of the alias (`/Research`), two records competing for one command written around the store (second dropped by the registry with its own message), a broken manifest of another skill (loader goes on), non-list `aliases` values (no crash). Residue F-17 |
| F-15 | **Closed** | `p_f15b.py`: `command_problem` over every code point 0 to U+10FFFF (surrogates excluded) alone and inside `/a?b`: exactly the 108 strings made of `[a-z0-9]` are accepted, none else (full-width letters, combining marks, dotless i, long s, Kelvin sign, final sigma, digits of other scripts, NBSP, NUL, newline, zero-width space, lone surrogate, `None`, numbers, bytes, lists: refused with a reason, no exception). Store: refused with rule `schema` for all of them on the file backend; written around the store they register nothing and give one problem line, no `KeyError` in `parse`. Notes: there is no length limit (a command of 2 000 000 characters is stored and registered; no defect found); `/model`-like names are shadowed by chat arguments (as in the second run) |
| F-16 | **Closed** (see F-19) | `p_f16.py`, 61681 generated stops (ints, floats, bool, None, str, nan, inf, big ints, `-0.0`, nested objects and lists, extra keys, the full cross product of both limit keys; seed 1608) against `graph_tables.check_record`: no case in which the rule refuses and the Storage accepts, and none in which the rule raises where the Storage refuses; rule accepts and Storage refuses only when a non-finite number sits in an extra key (421 cases, a document-level rule of the Storage; the rule ignores extra keys by design: note); rule raises `OverflowError` for an integer `max_seconds` beyond the float range (F-19). Single values: 0, -1, True, None, str, list, dict, nan, inf refused; `2.0`, `1e308`, `10**30` as repetitions accepted; `0.5`, `1e-300`, `5e-324` as seconds accepted; `1.5` as repetitions refused |
| F-17 | **New**, medium | below |
| F-18 | **New**, low | below |
| F-19 | **New**, low | below |

### New findings
| # | Finding | Severity | Destination |
|---|---|---|---|
| F-17 | **`extension_loader.py:77-84` (`taken` contains the aliases of ALL manifests, `e42de62`); REQ-WFM-042; regression of T-09 against `f11fa10`.** The check "command or alias of a skill without a record" compares with the aliases of every manifest, also the record skill's own. Probe `p_f14_own.py`: extension `lookup` with alias `research`, record `{"id": "lookup", "command": "/research"}` (accepted by the store): at `f11fa10` the skill is registered (id `research`); at HEAD the loader refuses the record (`'/research' is already the command or an alias of a skill without a record`, the message is also wrong: the skill has a record) and then drops the whole skill, so neither its manifest form nor the record is available (`registry.ids() == []`). A skill with a record whose command is one of its own aliases is plausible (`lookup` / `research` of the real `extensions/` folder). Same for a command that equals the folder name only through an alias. *Test:* extension `lookup` (alias `research`, no other skill), record command `/research`: `lookup` is registered under `research`, no problem line; with a second skill `alpha` (record `/research`) it is still skipped. The fix compares the aliases of the other skills only. | medium | Implement fix |
| F-18 | **`task_registry.py:77` (`re.A` on the `fullmatch`, `e42de62`, outside T-09's list of files); REQ-WFM-029; low.** The flag is correct for its purpose and enough: `/ſearch x` made `parse` raise `KeyError` at `f11fa10` for the real command `search` too (`ſ` matches `s` under `re.I`, `.lower()` keeps it), now it gives `None`; over 12771 code points in five text shapes `parse` raises no `KeyError` (the old one did for `/ſearch`); 60000 random ASCII texts (case, tabs, newlines, slashes) parse identically before and after; all commands registered by the repository (`lookup`, `research`, `review`, `search`) are ASCII, `test_task_registry` and `test_chat_tasks` pass. It changes one more thing: `re.A` also makes `\s` ASCII-only, so a command followed by a non-ASCII space is no longer a task command and falls through to normal chat: `/lookup x`, ` `, `　`, ` `, ` `, `\x85` parsed as `lookup` with the argument `x` before and give `None` now (`p_f15.py`; the Kelvin sign and other letters that fold to ASCII letters under unicode matching are also no longer accepted, which is harmless). Pasted text or an IME can produce such a space. Not covered by a test. *Test:* `parse("/lookup x y")` returns task `lookup` with argument `x y`, and `parse("/ſearch x")` does not raise. The fix applies `re.A` to the name only (scoped flag `(?a:...)` around the names, or a separator class `[\s]` written with `re.U` semantic), not to the separator. Judgement: the change is correct for the crash and does not change any ASCII command or the existing tests; it is a finding, not a note, because of the separator. | low | Implement fix (one more line in the test) |
| F-19 | **`graph_model.py:72` (`_limit`, `math.isfinite(value)` on an int), `e42de62`; REQ-WFM-048; low.** `stop_is_valid` and so `check_graph` and `save_graph` raise `OverflowError: int too large to convert to float` for an integer `max_seconds` above about `1.8e308` (e.g. `10**400`, 461 of the generated cases), where `graph_tables.check_record` accepts it (a valid positive number). Reachable through the graph API as JSON with a long integer. *Test:* `check_graph` with `{"max_seconds": 10**400}` returns a list (accepted or refused), never raises. The fix tests `value > 0` first and calls `isfinite` for floats only. | low | Implement fix |

### Regression review of `git diff f11fa10..HEAD`
- Done, not specified: the folder-name and alias comparison and the command form are only in `plan.md` T-08/T-09 (Plan note under F-11). The bad-record skill drop is as T-08 states; with F-17 it also drops a skill whose record is fine. The per-skill guard adds a problem line for every failed lookup and registers the skill as its manifest says (the owner's decision for the manifest skill is only about clashes; this reading is consistent).
- Behaviour for skills without a record: none. The repository's real `extensions/` folder (`lookup`, `review`, `search`) loads to the same tasks, aliases, versions, options and names with `catalog=None`, with an empty catalog and with an unrelated record, at `f11fa10` and at HEAD (`p_real_ext.py`: identical).
- `re.A`: see F-18. `find_cycle` public and used by `graph_run.py` only; `order_of` unchanged.
- New T-09 tests (7 + 30 + 12) all run and pass; they use fixed seeds.

### Mutants (third run; scratch copy of `git archive HEAD`, goal's tests incl. `test_task_registry.py`, `test_extension_loader.py`, file backend of the adapter test)
The 89 mutants of the second run were re-run; 17 of their patterns do not apply to the T-09 code and were rebuilt (stop rule, `find_cycle` name, `taken` set) and 52 new ones added for the T-09 code. 131 effective mutants: 106 killed, 25 survived. Killed: all T-01 rule and order mutants, T-02 (clash removed, clash with itself, version, record order, read version, `start`), T-03, T-04, all T-05/T-07 except the three groups below, T-06 catalog ignored, record command not used, graph ID not set, skill without record changed; T-08 normal form, clash on raw commands, clash after the form check, loader problem ignored, skipped skill registered; T-09: `find_cycle` roots reversed, first root skipped, done nodes counted as cycle, cycle without the repeated first ID, no `break` (stack order), only the last follower; per-skill guard removed, guard around the whole loop, problem line dropped, broken manifest aborts the loader, folder names dropped, aliases dropped, folder names inverted; stop rule `>= 0` and `>= 2` for repetitions, seconds `>= 0`, not finite, fractional repetitions, `2.0` refused, bool, string, `max_time`, null, `or` instead of `and`, flags swapped, not-dict, empty dict, extra keys refused; command: `-`, `ς`, rule removed, prefix match; `re.A` removed (and `re.I` removed); runner: unknown edge check dropped, cycle check dropped, cycle check after the trust check, trust called before a cycle refusal, cycle named without the repeated ID, `named_status` set for a cycle. The three T-08 test gaps are killed.
Survivors (25):
| Survivor | Class | Reason / proposed test |
|---|---|---|
| author not passed in skills, graph nodes and edges, header (3) | gap, F-08 | store, then `get(...)["author"]` names the account |
| `save_graph` refusal swallowed / raised in the `except StorageError` branch (2) | gap, F-09 | a graph with an edge record the Storage refuses is `saved=False` with rule and detail |
| node pre-check removed (1) | gap, F-09 | after a refused bad node `ids("graph_nodes") == []` |
| form checks for empty, space, second slash, capitals removed (4) | equivalent | the ASCII rule that follows refuses the same strings; only the wording of the reason differs |
| loader `lstrip("/")` instead of `normal_command` (1) | equivalent | a command that passes the form check is lower case with at most one slash |
| clash check including the skill itself (1) | equivalent | a skill with a record is never in `taken` by its folder name (see F-17 for aliases) |
| lookup failure leaves the entry unset (1); trust-first no-op (1); values empty after a cycle refusal (1); control no-op (1) | equivalent / not specified | no observable difference |
| folder names of skills WITH a record also taken (1) | gap, low | alpha `/zeta`, zeta moved to `/other` is accepted today (`p_f14.py` 5d): pin it |
| aliases of skills with a record not taken (alias comparison only for manifest-only skills) (1) | gap, low | `p_f14.py` case 3: alpha `/research` with `lookup` alias `research` and record `/ask`: alpha skipped |
| aliases / folder names compared without `normal_command` (2) | gap, low | alias `/Research`, folder `Alpha`: pin the normal form |
| `find_cycle` skips the last node (1) | gap, low | only cycle is a self-loop on the last ID: `find_cycle(["a","b","c"], [c->c]) == ["c","c"]` |
| `find_cycle` without the done mark (1) | gap, low (speed) | a ladder of 40 diamonds finishes within a time limit; exponential otherwise |
| `find_cycle` returns the whole path instead of the cycle (1) | gap, low | `a->b->c->b` gives `["b","c","b"]`, not `["a","b","c","b"]` (the tests start the cycle at the first node) |
| self-loop ignored by `find_cycle` (1) | gap, low | `GraphRunner.run` of a graph with an edge `T1->T1` is `refused` naming `["T1","T1"]` (the rule check never reaches `find_cycle` with a self-loop: alternation first) |
| `_` allowed in a command (1) | gap, low | `/a_b` refused |
The nine survivors of the first run: six still survive (3 author, 2 refusal branch, 1 pre-check), as expected from the owner's decision not to fix F-08 and the rest of F-09.

### Not run
`ruff`, `bandit`, `vulture` (not installed); real start of `web_app.py` with a failing catalog (shown at the loader level only); CI stage log; documentation and clean-machine walkthrough; the human review; the mutants ran on the file backend of the adapter test only (the PostgreSQL class runs the same code and was run unmutated); `save_graph` of 20000 real nodes did not finish within the 10 s probe limit (linear file writes, not a hang).

### Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| none | | |
