# High-Level Specification: G-V4.GRAPHAPI.RUN – one loaded graph for the order, the rules and the run

**Status:** Reviewed by group 2026-11-23 (D-476: parts and key decisions, dependencies, HR-001 to HR-007 accepted); the approval of the whole document with the goal update (D-473, D-474) is the owner's box below; decisions D-475, D-476
**Top-level spec:** `../G-V4.GRAPHAPI/top-level-spec.md` (items FR-65 and, for the six skills with equivalence suites, NFR-17 are this subgoal's; FR-37 of the product spec)   **Owner:** Stefan Reiterer   **Date:** 2026-11-23
**Basis:** the read-only survey of the run path (2026-11-23, in D-473), the networkx spike of the group (`../G-V4.GRAPHAPI/spikes.md`), RULES as merged (IF-301 v4, `graph_rule_set.py`), CORE as verified (the stored form, `GraphModel.read_graph`), the equivalence work of G-V2 (REQ-WFM-057 to 060, 069, 110 to 115; A-122, D-244; `eval-spec.md`).

## 1. Big parts and technology
Today no production code reads a stored graph for a run: a converted skill is converted in memory on every run and handed to `GraphRunner`, the others run on the old runner. About seven places build their own view of a graph (`graph_run` internals, `graph_model.order_of`, `graph_rule_set._view` with a copied cycle finder, `graph_order`, the converter, `stages_from_toolbox`, the document form). RUN puts **one loader** in N-3.2: the stored form becomes one networkx `MultiDiGraph`, and the order, the rules and the run all read it. A skill with a stored graph runs from it, and its run record names the graph and the version.

| Part (node) | Purpose | Technology | New / existing | Decided in |
|---|---|---|---|---|
| N-3.2 Workflows and context graphs | the loader: stored form to one loaded graph; the rule set reads the loaded graph | a new function `load(stored_form)` in a new module of N-3.2, returning a networkx `MultiDiGraph` (steps with their `data`, connections keyed by their ID with `from`, `to`, `data`); offered as **IF-301 v5** (amendment A-187); IF-301 v4's operations keep their signatures and build their view through `load` | new module, new interface version | D-473 (2), D-475 (1) |
| N-2.3 Workflow management (graph model) | the order of steps on the loaded graph; reading a stored graph for a run | `order_of` and `topological_order` on the loaded graph: networkx `lexicographical_topological_sort` keyed by the position of the step in the stored graph's list | existing, changed | D-475 (2) |
| N-2.4.1 Pipeline runner | runs a loaded graph one step after the other; a skill with a stored graph runs from it; the run record names graph and version | `GraphRunner.run` reads types, connections, roles and names from the loaded graph; the stored-graph path: read (N-2.3), load (N-3.2), stages from the toolbox, run | existing, changed | D-473 (1), D-475 (3) |
| N-4.1 Evaluation (suites, harness) | the equivalence runs of the six skills on the stored-graph path | `tools/eval.py run <suite> --pin MP-light --repeats 3` on the stored-graph path, `eval_decide.py` against the old-runner baselines | existing, a path added | D-473 (3) |
| N-3.1 Storage layer | serves the stored graphs | a fake storage in the checks (goal record, Parts) | stand-in | goal.md |

### Key decisions and alternatives
| Decision | Alternatives considered | Rationale | Record |
|---|---|---|---|
| The loaded graph is a networkx `MultiDiGraph`, connections keyed by their ID | an own small module; a `DiGraph` | owner's choice (D-473 (2)); the spike: 15 of 15 graphs keep every attribute, order and cycle check agree with today's code on 500 random graphs; a `DiGraph` would merge two connections between the same two steps, which no rule refuses | D-473, spike |
| The loader lives in N-3.2 and is part of IF-301 v5; the rule set, the order and the runner use it | inside the runner, with the rule set keeping its own view | OC-1 "built in one place"; the rule set is N-3.2's and its consumers test against IF-301 | D-475 (1) |
| IF-301 v5 only adds `load`; v4's `kinds`, `rule_report`, `run_check` keep their signatures (stored form in) | the rule set takes the loaded graph as input | VIEW, EDIT and CONTEXT consume v4 with the stored form; adding is a compatible change (the joint amendment at G-V4 stays small) | this spec |
| Ties of the order follow the stored order of the steps | sorted by step ID | today's order of every current graph stays as it is, so no converted skill changes its order | D-475 (2) |
| One step after the other; the items of a map step with `workers` above 1 stay parallel inside that one step | no parallelism at all | FR-65 speaks of steps; no shipped pipeline sets `workers` above 1; the map is one step | this spec |
| A run from a stored graph names the graph ID and the version in its run record | left to CODE with FR-67 | RUN builds the path; MIGRATION (OC-3) and CODE (FR-67) use the record | D-475 (3) |
| NFR-17 for the six skills: G-V2's criteria (REQ-WFM-110 to 115) on the stored-graph path, against the old-runner baselines of commit `1fb0c35`; extract.rules first gets its missing baseline run | a new rule | the rule is fixed and was passed by five skills on the in-memory path (2026-11-16) | D-473 (3) |
| The duplicated graph views go once their checks are green (the copied cycle finder, `find_cycle`, the edge scans of `graph_run`); the old runner and the in-memory converter stay | remove everything now | the old runner leaves with G-V4.GRAPHAPI.SWITCH; the converter is MIGRATION's import | D-473 (4), D-474 |

## 2. Dependencies
| ID | Kind | What | Pin / version | Why we need it | If it fails or changes | Used by | Update policy | Contract tests (what we rely on) |
|---|---|---|---|---|---|---|---|---|
| DEP-1 | tool | Python | 3.12 (venv `/home/maldun/prog/Python/venvs/mia312`) | runs the loader, the order, the runner | as CORE | HR-001 to HR-007 | compatible range 3.12 to < 3.15 | the whole test suite on 3.12 |
| DEP-2 | library | networkx | `networkx==3.7` (pure Python, BSD-3-Clause; new in `requirements.txt`, owner D-473 (2)) | the loaded graph, the order, the cycle | the order or the cycle could change: the characterization checks of HR-006 fail | HR-001, HR-002, HR-006 | exact pin; an update is a plan amendment with HR-006 re-run | `MultiDiGraph` keeps node and edge attributes and keyed parallel edges; `lexicographical_topological_sort(key=…)`; `find_cycle` / `is_directed_acyclic_graph` |
| DEP-3 | model | MP-light `gemma4:12b-it-qat` with its digest (`eval-spec.md`) | as pinned in `eval-spec.md` | the equivalence runs of HR-007 | a different digest: the runs do not count | HR-007 | never changed by RUN | `deploy/preflight_agent.py` checks the digest |
| DEP-4 | data | the old-runner baselines of commit `1fb0c35` (`eval/baselines/*__baseline.jsonl`, A-122, D-244) and the dev suites of the six skills | as in the repository | the reference of HR-007 | none: part of the repository, protected | HR-007 | never changed by an agent | `eval_decide.py` reads them |
| DEP-5 | data | the 15 converted skill graphs (`tests/helpers/rules_graphs.converted_skills`) and the 500 random graphs of the spike (seed 7) | as in the repository | the characterization of the order and the cycle | re-made from the skills | HR-006 | exact | TR-RULES-004 |

## 3. High-level requirements
Hard bounds: **none** (owner, D-475 (4)); a smoke number for loading and ordering is measured in the low-level spec, no bound. The kinds `rule` and `measure` follow CORE's and RULES' approved high-level specs (`spec_check.py` HS2 reports them, as for CORE and RULES).

### HR-001 – One loaded graph
- Kind: rule
- Parent: FR-65
- Text: The order of steps, the rule set and the Pipeline runner shall read a graph only through one loaded graph that the loader of N-3.2 builds from the stored form.
- Rationale: OC-1 "built in one place"; today about seven places build their own view (D-473).
- Depends on: DEP-2
- Status: Approved

### HR-002 – One step after the other in a fixed order
- Kind: rule
- Parent: FR-65
- Text: The Pipeline runner shall run the steps of a loaded graph one at a time, each after every step it reads from, in the order that breaks ties by the position of the step in the stored graph.
- Rationale: FR-65 and its outcome (no two steps at the same time, the same order for the same graph and inputs); the tie rule keeps today's order (D-475 (2)).
- Depends on: DEP-2
- Status: Approved

### HR-003 – Everything the run needs is on the loaded graph
- Kind: rule
- Parent: FR-65
- Text: The loaded graph shall carry every field of the stored steps and connections, including type, tool, stop limit, settings values, role and name, unchanged.
- Rationale: OC-3; the run needs them for loop-controlling steps, session settings and a step that reads several data steps; the converted graphs of research and verify_computable have master steps and three skills have settings connections (survey, D-473).
- Depends on: DEP-2
- Status: Approved

### HR-004 – A skill runs from its stored graph
- Kind: rule
- Parent: FR-65
- Text: When a skill with a stored graph runs, the Pipeline runner shall run the loaded stored graph of that skill and name its graph ID and version in the run record.
- Rationale: OC-1, OC-4; the path from storage to a run is RUN's (D-473 (1)); the record serves MIGRATION's OC-3 and CODE's FR-67 (D-475 (3)).
- Depends on: DEP-1
- Status: Approved

### HR-005 – The loader is part of IF-301
- Kind: technology
- Parent: FR-65
- Text: The loader shall be offered by N-3.2 as an operation of IF-301 v5, beside the unchanged operations of IF-301 v4, with a contract suite and a mock.
- Rationale: the rule set is N-3.2's and its consumers test against IF-301; IF-301 is frozen at G-V4, so v5 is a joint amendment (A-187) agreed by its consumers (D-475 (1)).
- Depends on: DEP-2
- Status: Approved

### HR-006 – Measure: the same results as before (OC-2)
- Kind: measure
- Parent: NFR-17
- Text: On the current graphs, the order, the rule report, the cycle verdict and the run result shall be the same through the loaded graph as through today's code.
- Method: the 15 converted skill graphs and the 500 random graphs of the spike (seed 7, with self loops); today's `order_of`, `rule_report`, `find_cycle` and `GraphRunner.run` with scripted stages as the oracle, recorded before the change; the existing graph, rule and run tests unchanged.
- Metric: 0 differences in order, report and verdict; 0 changed results; every existing test green.
- Rationale: OC-2 "every result is the same as before"; the oracle is recorded before today's code is changed.
- Reference: Fedora host, Python 3.12, networkx 3.7.
- Detail in: the test requirements of this subgoal.
- Status: Approved

### HR-007 – Measure: the six skills give the same results from their stored graph (OC-4)
- Kind: measure
- Parent: NFR-17
- Text: Each of the six skills with an equivalence suite, run from its stored graph, shall meet its equivalence criterion of G-V2 against its old-runner baseline.
- Method: `tools/eval.py run <suite> --pin MP-light --repeats 3` on the stored-graph path for research, plan_question, verify_claim, verify_computable, extract_claims, extract_claims_rules; `eval_decide.py` with the criteria of REQ-WFM-110 to 115 against the baselines of commit `1fb0c35`; extract.rules first gets its baseline run on the old runner (the file is missing); a failing criterion is re-run once with fresh seeds, never more.
- Metric: the decision of each criterion (PASS required for all six).
- Rationale: NFR-17 for the six (D-473 (3)); the same rule as G-V2, now on the stored path.
- Reference: the owner's host, MP-light with its digest, Ollama as pinned in `eval-spec.md`.
- Detail in: `eval-spec.md` and the test requirements of this subgoal.
- Status: Approved

## 4. Split proposal
### Nodes (decomposition)
No new node. The interface that changes is **IF-301 v5** (amendment A-187): the loader beside v4's registry, rule report and run check. N-3.2 provides it; N-2.3 (order) and N-2.4.1 (run) consume it, and later EDIT, CONTEXT and SWITCH. IF-301 is frozen at G-V4, so A-187 is a joint amendment: its consumers agree (VIEW consumes v4 through the check route; v5 is compatible).

### Goals and subgoals
| Proposed goal / subgoal | Outcome it delivers | Top-level items | Why this cut | How it is checked |
|---|---|---|---|---|
| RUN (this) | one loaded graph for order, rules and run; the six suite skills from their stored graph | FR-65; NFR-17 for six skills | split from SWITCH (D-474): RUN finishes and is checked before the user-interface skills move | HR-006, HR-007 |
| G-V4.GRAPHAPI.SWITCH (after RUN) | the nine user-interface skills on the graph path, the old runner removed | NFR-17 for nine skills | D-474 | its own plan |
Keep RUN together: the expected cut into tasks is five (oracle recorded first; loader and IF-301 v5; order and rule set on the loaded graph; runner and the stored-graph path with the run record; the equivalence runs), within one plan.

## 5. Integration with the existing system
- New: the loader module in N-3.2 (`load`, a few lines after the spike); `networkx==3.7` in `requirements.txt`. Changed: `graph_rule_set.py` (its view through `load`; the copied `_find_cycle` goes), `graph_model.py` (`order_of`, `topological_order` on the loaded graph; `find_cycle` goes once no production code uses it), `graph_run.py` (reads the loaded graph; the stored-graph path; the run record names graph and version), `core.py` / `skill_converter.py` (a skill with a stored graph runs from it), `tools/eval.py` (the stored-graph path for the equivalence runs), `contracts/IF-301-graph-tables.md` to v5 with its contract suite and mock (protected: the owner's amendment A-187). Unchanged: the old runner `pipeline.py`, the converter `pipeline_graph.py` (used by MIGRATION's import and the in-memory path), `graph_rules.py` (document form, leaves with MIGRATION), `storage.py`.
- Protected tests: the run tests of REQ-RUN-016 to 019 and 036 to 039, the rule tests of RULES and the IF-301 v4 contract suite stay green unchanged; to check in step 1b which of them pin internals that move (the order of ties, the copied cycle finder).
- Requirement amendments expected (step 1b): REQ-RUN-016 (topological order: the tie rule), the Draft REQ-RUN-030 to 035 (Stage inputs, outputs, settings, order edge: settled on the loaded graph), REQ-WFM-110 to 115 (the stored-graph path), IF-301 v5 (A-187).
- Notes for other subgoals: MIGRATION stores the converted skills and switches each skill to its stored graph through `load` (D-473 (1)); SWITCH moves the nine user-interface skills and removes the old runner (D-474); CODE uses the run record's graph and version (FR-67).

## 6. Risks and open questions
Decided by the owner in the HLS questionnaire of 2026-11-23 (D-475): the loader in N-3.2 as IF-301 v5; ties by the stored order; the run record names graph and version; no hard bound.

| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| IF-301 is frozen at G-V4: v5 is a joint amendment (A-187) | VIEW, EDIT, CONTEXT must agree; contract text, suite and mock change through the owner's script | v5 only adds `load`; written in step 1b with the requirements; agreement in G-V4's Joint amendments table |
| networkx's own order differs from today's Kahn order | a converted skill could run its steps in another order | `lexicographical_topological_sort` keyed by the stored position; HR-006 compares the order on 15 + 500 graphs against the oracle recorded before the change |
| extract.rules has no baseline run file | HR-007 cannot be decided for it | a baseline run on the old runner first (a real model run, logged), before the stored-graph run |
| The equivalence runs need the shared GPU for some hours | other sessions' model work | announced to the running sessions first (CLAUDE.md) |
| The six skills must be stored before they can run from their stored graph, and storing them is MIGRATION's | RUN's OC-4 would wait for MIGRATION | **decided (D-476):** RUN's checks and equivalence runs store the six converted graphs through CORE's save path into a throw-away store (a check fixture, not the import) and run from there; MIGRATION does the real import |
| Protected run tests may pin internals that move (tie order, `find_cycle`) | an amendment of a protected test | checked in step 1b; amendment if needed |

## Approval
Reviewed item by item with the owner (review log: `review-log.md`). The approval of the whole document is the owner's: tick the box (in Emacs `C-c C-c` on the line) or say so in the chat; the agent then sets the status to Approved and never before.

- [ ] Approved by maldun (owner). Date:
