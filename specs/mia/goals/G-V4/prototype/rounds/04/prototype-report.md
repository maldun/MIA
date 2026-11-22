# Prototype report: G-V4, round 04 (G-V4.GRAPHAPI.RULES, MVP)

Status: Prototype (reviewable draft, no product guarantees until parts are `real`) · Location: `specs/mia/goals/G-V4/prototype/rounds/04/` · Code: worktree `../MIA-prototype-g-v4`, branch `prototype/g-v4`
Scope: the outcomes of G-V4.GRAPHAPI.RULES (run.md) · Budget: 4 checkpoints of about an hour · Status table: `specs/mia/goals/G-V4/prototype/status.md`

## Question
Can one set of graph rules, chosen by the kind of the graph and written in one place, serve every place a graph is checked (saving, the editor's check, keeping, before a run) with the same list in the same order (FR-63, OC-1), and refuse a run before any step for broken rules, unsupplied inputs and kinds that cannot run (FR-64, OC-2), on top of CORE as verified?

## Hard requirements (top-level only)
FR-63, FR-64 of `specs/mia/goals/G-V4.GRAPHAPI/top-level-spec.md`; OC-1, OC-2 of `specs/mia/goals/G-V4.GRAPHAPI.RULES/goal.md`.

## What was built
- **Merge of `goal/v4`** (CORE, verified) into `prototype/g-v4`: `graph_model.py` and `graph_tables.py` taken from `goal/v4`; every check of rounds 01 to 03 passes on it.
- **CP17: one place, chosen by kind.** `graph_rules_proto.KINDS` names per kind its rules in order and whether it can run: `workflow` = the eight rules, `context` = rules 1, 3 and 4 of the same definitions, cannot run. `check(graph)` gives every broken rule; a kind not in `KINDS` gives one item `unknown_kind`. The save path of `graph_model.py` asks `check` instead of `check_graph` and `context_problems`; a refused save carries the rules (`SaveResult.rules`). `proto_checks/cp17_check.py` maps the five older rules onto the eight.
- **CP18: counts.** `proto_checks/cp18_check.py`: rule 7 and the candidate rule "a processing step needs a tool" on the 17 graphs the prototype stores.
- **CP19: the same list everywhere.** `proto_checks/cp19_check.py` sends two graphs that each break three rules through the function, the save path, the check route, keeping and the run route; the refusal of a run for inputs, a context graph and an unknown kind; the 15 converted skills as a regression. The page's working copy now keeps the stored kind.

## Findings
1. **Three rule implementations, not two.** `graph_rules.violation` (document form; IF-301 `validate`, used through the Storage layer by IF-102, IF-104 v1, IF-203 and their contract suites, REQ-GTB-002: "the first broken rule" of five), `graph_model.check_graph` (CORE save path: five rules, the first broken group) and the prototype's rule set. Inventory of the old names (`node_identity`, `adjacent_data_nodes`, `adjacent_process_nodes`, `session_stopping_criterion`): `graph_rules.py`, `graph_tables.py`, `contracts/IF-102`, `IF-104`, `IF-301`, the contract suites of IF-102, IF-104 (Python and JS), IF-203, IF-301, `tests/acceptance/test_workflow_library.py`, the mocks `graph_rules.py`, `if_104_graph_api.mjs`, `if_301_graph_tables_v2.py`, the unit tests `test_graph_api.py`, `test_graph_document_form.py`, `test_graph_rules.py`, `test_storage.py`, `test_workflow_library.py`, the requirement REQ-GTB-002 and the test spec of N-3.2. Decision Q-6.
2. **The save path takes the new set without touching a protected test.** With `check` in the save path every test that imports `graph_model`, `graph_rules` or the rules (32 test files, incl. TC-WFM-164 and TC-WFM-168) passes once findings 3 to 5 were fixed: a graph with one broken rule names the same IDs as before. A graph with several broken rules now names all of them (before: the first group); REQ-WFM-146/150 say "names", so the wording amendment Plan writes can say "every broken rule, in the fixed order" and carry V-2/V-3 with it (handover of 2026-11-22).
3. **A cycle keeps its first step at the end** (REQ-WFM-047): removing repeated parts lost it, and three CORE checks caught it. Fixed: the parts of `cycle` are kept as found; a refused save lists the parts of every rule in order, without removing repeats.
4. **A rule must never raise** (as A-60): the CP8 module raised on connection data that is not an object and on steps or connections without IDs; CORE's record check had refused the first as `schema_break`. Fixed; checked in `cp17_check.py`.
5. **Slash in a step name:** rule 1 of CP8 refused it, CORE allows it (REQ-GTB-029). The prototype follows CORE now. Decision Q-4.
6. **Old cases on the new set:** every case of TC-GTB-002 that the five rules refuse is refused by the eight, except `max_seconds: 1.0` (a valid limit under REQ-WFM-048, already so in CORE). On the generator of TC-GTB-003 (seeds 1 to 1000) no graph refused by the five is accepted by the eight; 57 are newly refused (42 duplicate connection, 15 two writers): the two rules the old set did not have.
7. **Context graphs on the same definitions** refuse, beyond CORE's `context_problems`, an empty step name (53 of 500 generated graphs; CORE refuses it later through the record check anyway) and two identical connections with different IDs (3 of 500; CORE accepts them). Decision Q-3.
8. **The cycle is asked only on known steps:** while rule 1 or 3 is broken, the cycle is not asked (CP4). OC-1 holds (the same list everywhere); the owner may see the cycle only after the fix. Decision Q-5.
9. **The page lost the kind:** the working copy of the editor (`full_graph`) dropped the stored kind, so a context graph would have been checked and kept with the workflow rules. Fixed; checked in `cp19_check.py`. Plan needs a test that every entry point checks with the stored kind.
10. **Unknown kind:** the Storage layer refuses a header of an unknown kind (`schema_break`, `kind`), so such a graph cannot be stored today; the save path says the same (REQ-WFM-154, V-2); the check and the run say `unknown_kind` (D-404). D-404's read-only listing only arises with a store written by a newer version. Decision Q-7.
11. **Rule 7 (ASM-3)** refuses none of the 17 stored graphs (35 processing and loop-controlling steps, 4 loop-controlling, 7 steps with a settings connection, none with two). Decision Q-1.
12. **Candidate rule "a processing step needs a tool":** all 35 steps name a tool; 2 tools of the prototype samples are unknown to the toolbox. A known-tool check needs the toolbox at check time, so RULES would no longer be pure checks (goal.md: "pure checks, they need no stored graph"). Decision Q-2.
13. **Time:** the eight rules check a 500-step chain in 1.4 ms (IF-301 bound: 200 ms); a refusal of a 5-step graph takes 0.03 ms.

## Assumptions and choices the prototype made
| ID | Assumption or choice | Alternatives | Evidence |
|---|---|---|---|
| ASM-3 | rule 7 as in Q-1 (from round 02) | only the stop limit | CP18: refuses nothing stored |
| ASM-7 | a kind that cannot run, or an unknown kind, is the only item of a refusal (its rules say nothing about a run) | the kind plus the rules of the kind | FR-64 names the kind; a context graph's rules are not about running |
| ASM-8 | `SaveResult` gets a field `rules` (the broken rules); `named` lists the parts of every broken rule in order | a separate call for the rules | the editor and the run show rules with their texts; the IDs alone lose the rule names |

## Proposed TLS changes
None. FR-63 and FR-64 hold as written; Q-2 would need a TLS amendment only if a ninth rule is taken.

## Effect on the TLS
None; the fingerprint stays `cb0a21233175`.

## Carry-over (the developer decides)
| Item (requirement, spec text, decision, code, scenario) | Where | Decision: adopt / adapt / drop / stand-in | Reason |
|---|---|---|---|
| The registry of kinds with the rule set per kind and the run flag (R3 update) | `graph_rules_proto.py` (`KINDS`, `RULES`, `check`, `refusal`) | adapt | Confirmed by the owner 2026-11-22 as proposed: replaces `check_graph` and `context_problems` of `graph_model.py` in N-3.2; the decisions Q-1 to Q-7 set its content |
| The save path asks the one rule set; `SaveResult.rules` | `graph_model.py` (prototype change) | adapt | Confirmed by the owner 2026-11-22 as proposed: the CORE tests stay green; wording amendment of REQ-WFM-146/150 (finding 2) |
| The mapping of the older rules and the generator comparison | `proto_checks/cp17_check.py` | adapt | Confirmed by the owner 2026-11-22 as proposed: becomes the scenario and test requirement that the eight rules refuse whatever the five refused |
| The same list at every entry point; refusal before a run | `proto_checks/cp19_check.py` | adapt | Confirmed by the owner 2026-11-22 as proposed: becomes the acceptance test of OC-1 and OC-2 (with the runner of N-2.4.1, the check route against the IF-104 mock) |
| The kind kept by the editor's working copy | `graph_proto_app.py` (`full_graph`) | adopt | Confirmed by the owner 2026-11-22 as proposed: a scenario for EDIT and the check route |

Decided by: Stefan Reiterer (owner), 2026-11-22, by answer in the session ("All as proposed")

## Prototype tests (run once here; the developer's carry-over decision above decides what happens)
| Question (requirement or top-level item) | Command (repeatable) | Result (value, unit, uncertainty, hardware, date; pass / fail / not_run) |
|---|---|---|
| FR-63: one place, by kind; the five older rules mapped; the save path asks the same set | `./proto.sh proto_checks/cp17_check.py` | 11 pass, 2026-11-22, Fedora host |
| FR-63: rule 7 and the candidate rule counted | `./proto.sh proto_checks/cp18_check.py` | 3 pass, 2026-11-22, Fedora host |
| FR-63, FR-64 (OC-1, OC-2): the same list at every entry point; refusal before a run | `./proto.sh proto_checks/cp19_check.py` | 14 pass, 2026-11-22, Fedora host |
| No regression of rounds 01 to 03 | `cp1` to `cp15` checks, `node --test proto_checks/*.test.mjs`, the 32 test files that import the rules | all pass (216 checks over 14 scripts on files, `cp13` and `cp15` also on PostgreSQL 16 under podman, 60 page tests, 32 files), 2026-11-22, Fedora host |
