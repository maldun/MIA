# High-Level Specification: G-V4.GRAPHAPI.RULES – one rule set for graphs

**Status:** Draft (2026-11-22); open decisions taken by the owner (D-416); HR-001 to HR-006 wait for the review by group
**Top-level spec:** `../G-V4.GRAPHAPI/top-level-spec.md` (items FR-63, FR-64 are this subgoal's; FR-7 of the product spec)   **Owner:** Stefan Reiterer   **Date:** 2026-11-22
**Basis:** the validated prototype round 04 (`../G-V4/prototype/rounds/04/`, branch `prototype/g-v4`, carry-over decided all as proposed), the reuse map row R3, the owner's decisions D-375, D-404 and D-415 (Q-1 to Q-7), the accepted cases AC-017 and AC-018 (`../G-V4/accepted-cases.md`), CORE as verified (D-414).

## 1. Big parts and technology
RULES changes three existing parts and adds no module or interface. The rules of a graph are written **once**, per kind of graph, in a registry of kinds; every place that checks a graph asks that registry and gets **every** broken rule, in one fixed order, each with the steps or connections it concerns. A run asks the same registry, plus the inputs nobody supplies and whether the kind can run, before the first step.

| Part (node) | Purpose | Technology | New / existing | Decided in |
|---|---|---|---|---|
| N-3.2 Workflows and context graphs | the registry of kinds with the rule set of each kind; the rule report of a graph; the refusal of a run | the registry and its rule functions in `graph_rules.py` (Python 3.12, pure functions, no storage), adapted from `graph_rules_proto.py`, next to the document form's `violation`, which stays as it is (Q-6) | existing module, extended; internal to N-3.2, no interface (D-416) | D-404, D-415, D-416, prototype R3 |
| N-2.3 Workflow management (graph model) | the save path refuses a graph that breaks a rule of its kind, naming every broken rule | `GraphModel.save_graph` asks the rule set instead of `check_graph`/`context_problems`; `check_graph` stays as the flat list of named IDs | existing, changed | CORE, prototype CP17 |
| N-2.4.1 Pipeline runner | refuses a run before any step: kind, broken rules, inputs nobody supplies | `GraphRunner.run` asks the refusal first | existing, changed | D-375, prototype CP4, CP19 |
| N-2.1 / N-5 check route | the editor's check of a working copy | the check route of IF-104 v2 (written at G-V4 level, D-368); here tested against a mock that returns the rule report, real when IF-104 v2 is written or in EDIT | stand-in | goal.md (Parts), D-416 |

### Key decisions and alternatives
| Decision | Alternatives considered | Rationale | Record |
|---|---|---|---|
| One registry of kinds: per kind its rules in order and whether it can run; `workflow` = eight rules, `context` = rules 1, 3, 4 of the same definitions, cannot run | a rule set per caller; a separate context module | FR-63 "written in one place, chosen by the kind"; one definition per rule keeps the context set from drifting | D-404, Q-3 |
| The eight workflow rules in this order: step identity, kind of step, connection ends, duplicate connection, adjacency, one writer, session setting and stop limit, cycle | the five older rules; the cycle anywhere | D-375: local facts first, the cycle last; rule 7 as ASM-3 (Q-1); no ninth rule (Q-2) | D-375, D-415 |
| Every broken rule is reported, each with its parts; the cycle is asked only when every step name and connection end is known | the first broken rule only (today's save path and document form) | OC-1 needs the full list; an order needs known steps (Q-5) | D-415 |
| A rule never raises: any input gives a report | exceptions for malformed input | the same contract as IF-301 (A-60); the prototype found two crashes (finding 4) | prototype CP17 |
| A slash in a step name is allowed | refuse it (round 02) | CORE allows it: the graph ID ends at the first slash (REQ-GTB-029) | Q-4 |
| `check_graph` stays, as the IDs the report names, in rule order | remove it | three protected acceptance tests call `check_graph(graph) == []` (`test_pipeline_graph.py`, `test_skill_binding.py`, `test_graph_order.py`); they keep passing unchanged | this spec |
| The document form (`workflows` table, IF-301 `validate`, IF-102, IF-104 v1, IF-203) keeps the five older rules | move it to the eight now | the document form is retired by G-V4.MIGRATION; no contract changes in RULES | Q-6 |
| An unknown kind: the check and the run say `unknown_kind`; the save keeps CORE's `schema_break`/`kind` | one name everywhere | CORE is verified (REQ-WFM-154, V-2); such a graph cannot be stored today | Q-7 |
| The run is refused in this order: kind, broken rules, inputs nobody supplies; the trust check (REQ-RUN-017) comes after | trust first | a graph that breaks the rules is refused whatever its trust; trust per step is G-V4.GRAPHAPI.CODE | D-416 |
| The rule report is internal to N-3.2: the model (N-2.3) and the runner (N-2.4.1) call `graph_rules.py` directly; frozen at G-V4 as requirements, not as an interface | an amendment of IF-301 to v4 with a contract suite | the owner's choice: no interface work in RULES; the runner already calls `graph_model` directly today | D-416 |
| The registry lives in `graph_rules.py`, next to the document form's `violation` | a new module `graph_rule_set.py` | one file for the rules of graphs; `violation` leaves with the document form (G-V4.MIGRATION) | D-416 |

## 2. Dependencies
| ID | Kind | What | Pin / version | Why we need it | If it fails or changes | Used by | Update policy | Contract tests (what we rely on) |
|---|---|---|---|---|---|---|---|---|
| DEP-1 | tool | Python | 3.12 (venv `/home/maldun/prog/Python/venvs/mia312`) | runs the rule set, the model and the runner | as CORE | HR-001 to HR-006 | compatible range 3.12 to < 3.15 | the whole test suite on 3.12 |
| DEP-2 | data | the 15 converted skill graphs and the prototype's sample graphs | commit of the prototype fixtures | the golden examples of the measures | re-made from the skills | HR-004, HR-006 | exact, changed only with its tests | `proto_checks/cp1_check.converted` becomes a fixture |
| DEP-3 | data | the cases and the generator of TC-GTB-002 and TC-GTB-003 | `tests/test_graph_rules.py` at `goal/v4` | the old verdicts the eight rules must keep | none: the file is part of the repository | HR-005 | exact | the mapping of `cp17_check.py` |

No new dependency is added.

## 3. High-level requirements
Hard bounds: **none** (owner, D-416), and no time budget in the low-level spec either. The eight rules check a 500-step graph in 1.4 ms (prototype, CP17); IF-301's 200 ms for 500 steps stays a bound of the document form's `validate` only.

The kinds `rule` and `measure` follow CORE's approved high-level spec; `spec_check.py` (HS2) knows only technology, dependency, bound and constraint and reports them, as it does for CORE (owner, D-416: keep CORE's kinds).

### HR-001 – One rule set per kind
- Kind: rule
- Parent: FR-63
- Text: The system shall keep the rules of every kind of graph, their order and whether a graph of the kind can run in one registry, and every check of a stored-form graph shall take its rules from it by the kind of the graph.
- Rationale: FR-63 "written in one place, chosen by the kind"; the prototype found three implementations today and a page that lost the kind (findings 1, 9).
- Depends on: DEP-1
- Status: Draft

### HR-002 – The rule report
- Kind: rule
- Parent: FR-63
- Text: A check shall report every broken rule of the graph's kind in the registry's order, each with its name, the IDs of the steps or connections it concerns and a sentence for people, and shall report an empty list for a graph that keeps every rule.
- Rationale: OC-1 lists the same broken rules in the same order "each with its steps or connections"; the sentence is what the editor and the run show.
- Depends on: DEP-1
- Status: Draft

### HR-003 – Refusal before a run
- Kind: rule
- Parent: FR-64
- Text: Before the first step runs, the Pipeline runner shall refuse a graph whose kind is unknown or cannot run, that breaks a rule, or that has a step input with no writer, no start value and no value given with the run, naming each.
- Rationale: FR-64 and OC-2; today the runner refuses only a missing end and a cycle (REQ-RUN-016).
- Depends on: DEP-1
- Status: Draft

### HR-004 – Measure: the same list everywhere (OC-1)
- Kind: measure
- Parent: FR-63
- Text: A graph that breaks several rules shall give the same rule report, item by item (rule, parts, order), when saved, when checked through the check route, when kept and before a run, five times in a row.
- Method: two graphs that each break three rules (one with a cycle, one with a connection to a missing step), the case AC-017, on the files backend.
- Metric: 0 differences between the four entry points and between repeated checks.
- Rationale: the owner's outcome OC-1, decided on the entry points people use.
- Reference: Fedora host, Python 3.12.
- Detail in: the test requirements of this subgoal.
- Status: Draft

### HR-005 – Measure: no old refusal is lost (FR-63)
- Kind: measure
- Parent: FR-63
- Text: Every workflow graph that the five older rules refuse shall be refused by the eight rules, except a stop limit that REQ-WFM-048 accepts.
- Method: the cases of TC-GTB-002 and the generator of TC-GTB-003 (seeds 1 to 1000), each document turned into the stored form.
- Metric: 0 graphs refused by the five and accepted by the eight; the newly refused graphs are counted by rule and reported.
- Rationale: the eight rules replace the five in the save path; a graph that was refused must not become storable (prototype: 0 of 1000 lost, 57 newly refused).
- Reference: as HR-004.
- Detail in: the test requirements of this subgoal.
- Status: Draft

### HR-006 – Measure: refused before any step, ready when sound (OC-2)
- Kind: measure
- Parent: FR-64
- Text: A run of a graph with a cycle, two writers, a connection to a missing step, two identical connections, an unsupplied input, a context graph or an unknown kind shall end refused with no step run, and each of the 15 converted skill graphs shall be ready once its inputs are given.
- Method: the case AC-018, one graph per refusal reason, the 15 converted skill graphs.
- Metric: 0 steps run in a refused run; every broken part named; 15 of 15 skills ready.
- Rationale: OC-2, plus the regression that the stricter rules do not stop today's skills.
- Reference: as HR-004.
- Detail in: the test requirements of this subgoal.
- Status: Draft

## 4. Split proposal
### Nodes (decomposition)
No new node and no new interface version. N-3.2's `graph_rules.py` gets the registry; N-2.3 and N-2.4.1 call it directly (D-416). The rule report is used by EDIT, CONTEXT and the run, so its requirements are a shared item frozen at G-V4 (consistency review, section 4).

### Goals and subgoals
| Proposed goal / subgoal | Outcome it delivers | Top-level items | Why this cut | How it is checked |
|---|---|---|---|---|
| RULES (this) | one rule set by kind, the same list everywhere, refusal before a run | FR-63, FR-64 | the goal record keeps it together (D-392); the new work is a few requirements | HR-004 to HR-006 |
Keep together: the expected cut into tasks is four (rule set module; save path; runner; check route against the mock), within one plan.

## 5. Integration with the existing system
- Changed: `graph_rules.py` (the registry and the rule functions, about 150 lines from `graph_rules_proto.py`, beside `violation`), `graph_model.py` (`save_graph`, `check_graph` as a view, `context_problems` removed or kept as a view), `graph_run.py` (`GraphRunner.run` asks the refusal first). Unchanged: `violation` in `graph_rules.py`, `graph_tables.py`, `storage.py`, the contracts IF-102, IF-104 v1, IF-203, IF-301.
- Protected tests: TC-WFM-164 and TC-WFM-168 pass unchanged (prototype CP17); `test_pipeline_graph.py`, `test_skill_binding.py`, `test_graph_order.py` keep `check_graph`. To check in step 1b: the protected run tests of REQ-RUN-016 (a refusal now names every broken rule, not only the cycle or the missing end).
- Requirement amendments expected: REQ-WFM-146/150 (a refused save names every broken rule, in order; carries V-2 and V-3 of CORE), REQ-WFM-155/156 (the context rule set from the registry, rule 4 in full, Q-3), REQ-RUN-016 (the refusal of HR-003).
- Notes for other subgoals: CODE takes the known-tool check (Q-2); TRANSFER or MIGRATION the read-only listing of an unknown kind (Q-7); MIGRATION retires the document form (Q-6).

## 6. Risks and open questions
| Risk / question | Impact | Mitigation / owner |
|---|---|---|
Decided by the owner in the HLS questionnaire of 2026-11-22 (D-416): the rule report stays internal to N-3.2, the check route is tested against a mock, the run is refused in the order kind, rules, inputs, trust, no time bound, the registry goes into `graph_rules.py`, CORE's kinds of HR items.

| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| The rule report is not an interface: N-2.3 and N-2.4.1 (and later EDIT, CONTEXT) call N-3.2's `graph_rules.py` directly | a change of the report form has no contract suite to catch it in the callers; the decomposition rule "every cross-part flow has an interface requirement" is met only by the frozen requirements | **decided** (D-416); the requirements of the report are frozen at G-V4, and the tests of each caller assert the report form; revisited if a caller outside the backend needs it |
| IF-104 v2 (with the check route) is written at G-V4 level and not yet there | RULES cannot test a real route | **decided:** a mock that returns the rule report; real when IF-104 v2 is written or in EDIT |
| Order of the refusal of a run: kind, rules, inputs, then trust | a broken untrusted graph names its rules, not its trust | **decided** (D-416) |
| A time limit for the check | none needed so far (1.4 ms for 500 steps) | **decided:** none |
| `graph_rules.py` holds two rule sets until MIGRATION (the five of the document form, the registry) | a reader may take the wrong one | the module text says which one serves which form; `violation` leaves with MIGRATION |
| Run tests of REQ-RUN-016 expect only the cycle or the missing end named | a protected test may need an amendment | checked in step 1b; amendment if needed |

## Approval
Reviewed item by item with the owner (review log: `review-log.md`). The approval of the whole document is the owner's: tick the box (in Emacs `C-c C-c` on the line) or say so in the chat; the agent then sets the status to Approved and never before.

- [ ] Approved by Stefan Reiterer (owner). Date:
