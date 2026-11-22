# Requirements: G-V4.GRAPHAPI.RULES (low level, new and changed items)

**Top-level spec:** `specs/mia/goals/G-V4.GRAPHAPI/top-level-spec.md` (FR-63, FR-64)   **High-level spec:** `specs/mia/goals/G-V4.GRAPHAPI.RULES/high-level-spec.md` (HR-001 to HR-006, approved 2026-11-22)   **Status:** Draft (Plan step 1b, 2026-11-22), for review group by group   **Plan baseline:** –

<!-- The requirements this subgoal adds, and the proposed wording changes of requirements in force.
     Basis: the validated prototype round 04 (`specs/mia/goals/G-V4/prototype/rounds/04/` on `prototype/g-v4`, findings 1 to 13, carry-over all as proposed),
     the owner's decisions D-375, D-404, D-414 (V-2, V-3), D-415 (Q-1 to Q-7), D-416 (2) to (4), D-417 and D-418.
     Where the requirements go at the merge: the rule set (groups RS, RD, RF, DF) into N-3.2
     (`specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md`), offered through IF-301 v4 (amendment A-170);
     the save path (group SV) into N-2.3; the run (group RR) into N-2.4.1.
     Requirements in force that stay as they are: REQ-WFM-043, 045 to 048 (the rules of a workflow graph; the eight rules below include them, with names),
     REQ-WFM-146 (whole graph checked first), REQ-WFM-153, REQ-WFM-156 (no workflow rules for a context graph: the context set below has none of them),
     REQ-GTB-002 (the document form keeps its five rules, Q-6), REQ-RUN-016, 017, 033.
     Accepted cases: AC-017 (FR-63) and AC-018 (FR-64), `specs/mia/goals/G-V4/accepted-cases.md`; their Witness column is filled when the checks exist.
     27 new requirements and 3 changed ones: more than the 25 of the split hint; kept together by the owner (D-418 (3), goal.md split check). -->

## Terms
| Term | Meaning |
|---|---|
| kind (of a graph) | the header field `kind`: `workflow` or `context` today (D-404); a graph that names no kind is a workflow graph (REQ-WFM-153) |
| registry of kinds | the one table that names, per kind, its rules in their fixed order and its run flag (D-404, HR-001) |
| run flag | yes when a graph of the kind may be run, no when it may not (FR-64 "a kind that cannot run") |
| rule report | the answer of a check: a list with one item per broken rule, in the registry's order, each `{"rule", "parts", "text"}`; an empty list when every rule is kept (HR-002) |
| parts (of a broken rule) | the local IDs of the steps or connections the rule concerns, in the order the rule finds them |
| refusal (of a run) | the answer of the run check: `{"status": "refused" or "ready", "broken": [...]}`, each item of `broken` a broken rule, an unsupplied input or the kind (HR-003) |
| unsupplied input | an input connection of a processing or loop-controlling step from a data step that has no writer, no start value in the graph and no value given with the run; settings and order connections are not inputs here |
| session setting | the `stop` or `session` field of a step, and the settings connection (`role: "settings"`) into a step (ASM-3, Q-1) |
| stored form | a graph as `{"kind"?, "nodes": [{"id", "data"}], "edges": [{"id", "from", "to", "data"}]}` with local IDs, as the Workflow management saves and reads it (CORE) |

## Groups
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 1 | RS | The rule set by kind: one registry, the rules of each kind in order, the rule report (FR-63, HR-001, HR-002) | REQ-GTB-033, REQ-GTB-034, REQ-GTB-035, REQ-GTB-036, REQ-GTB-037, REQ-GTB-038, REQ-GTB-039, REQ-GTB-040 |
| 2 | RD | The eight rules: what each one finds and which parts it names (FR-63, D-375, Q-1, Q-4, Q-5) | REQ-GTB-041, REQ-GTB-042, REQ-GTB-043, REQ-GTB-044, REQ-GTB-045, REQ-GTB-046, REQ-GTB-047, REQ-GTB-048 |
| 3 | RF | The refusal of a run as a report: kind, broken rules, unsupplied inputs (FR-64, HR-003) | REQ-GTB-049, REQ-GTB-050, REQ-GTB-051 |
| 4 | SV | Saving with the rule set: the save path of the Workflow management, and V-2, V-3 of CORE (FR-63, HR-004) | REQ-WFM-162, REQ-WFM-163, REQ-WFM-164, REQ-WFM-165, REQ-WFM-150 (changed), REQ-WFM-154 (changed), REQ-WFM-155 (changed) |
| 5 | RR | The run: refused before the first step, every part named, trust after (FR-64, HR-003, HR-006) | REQ-RUN-036, REQ-RUN-037, REQ-RUN-038, REQ-RUN-039 |
| 6 | DF | The document form stays as it is until MIGRATION (Q-6) | REQ-GTB-052 |

## Requirements

### REQ-GTB-033 – One registry of kinds
- Level: low   Subject: Persistence
- Group: RS
- Text: The Graph tables shall offer through IF-301 one registry of kinds that names, for each kind of graph, its rules in their fixed order and its run flag.
- Rationale: refines HR-001 and FR-63 "written in one place, chosen by the kind" (D-404, D-417); the prototype found three rule implementations today (finding 1)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: the registry read through IF-301 lists exactly the kinds `workflow` and `context`, each with a list of rule names and a yes/no for running (exact)
- Verified by: TC-GTB-037
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17)

### REQ-GTB-034 – The eight workflow rules in order
- Level: low   Subject: Persistence
- Group: RS
- Text: The Graph tables shall list in the registry of kinds for the kind `workflow` the rules `step_identity`, `step_kind`, `connection_endpoints`, `duplicate_connection`, `adjacency`, `single_writer`, `stop_limit` and `cycle`, in this order.
- Rationale: refines HR-001; D-375: local facts first, the cycle last; no ninth rule (Q-2: the known-tool check goes to G-V4.GRAPHAPI.CODE)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: the rules of `workflow` are exactly these eight names in this order (exact)
- Verified by: TC-GTB-037
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17)

### REQ-GTB-035 – The rules of a context graph
- Level: low   Subject: Persistence
- Group: RS
- Text: The Graph tables shall list in the registry of kinds for the kind `context` the rules `step_identity`, `connection_endpoints` and `duplicate_connection`, in this order, with the definitions used for `workflow`.
- Rationale: refines HR-001; one definition per rule keeps the context set from drifting (D-404); rule 4 in full, so two identical connections with different IDs are refused (Q-3); CONTEXT may add rules by amendment (FR-75, ASM-4)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: the rules of `context` are exactly these three names in this order; a context graph with two identical connections under different IDs is reported with `duplicate_connection` naming the second ID (exact)
- Verified by: TC-GTB-037, TC-GTB-038
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, finding 7)

### REQ-GTB-036 – Which kinds can run
- Level: low   Subject: Persistence
- Group: RS
- Text: The Graph tables shall set the run flag of the kind `workflow` to yes and the run flag of the kind `context` to no.
- Rationale: refines HR-001 and FR-64 "a kind that cannot run"; context steps are categories, not data and processing steps (D-404)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: `workflow` can run, `context` cannot (exact)
- Verified by: TC-GTB-037
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17)

### REQ-GTB-037 – The rule report
- Level: low   Subject: Persistence
- Group: RS
- Text: When a graph in stored form is checked, the Graph tables shall return one item per broken rule of the graph's kind, in registry order, each with rule name, parts and sentence.
- Rationale: refines HR-002 and OC-1 "the same broken rules in the same order, each with its steps or connections"; the sentence is what the editor and a refused run show; a graph that keeps every rule gives an empty list
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a workflow graph with a missing connection end and two writers of one data step gives exactly two items, `connection_endpoints` before `single_writer`, each with its parts and a non-empty sentence; a sound graph gives `[]` (exact)
- Verified by: TC-GTB-039
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, CP19)

### REQ-GTB-038 – No kind means workflow, for the check
- Level: low   Subject: Persistence
- Group: RS
- Text: Where a graph in stored form names no kind, the Graph tables shall check it with the rules of the kind `workflow`.
- Rationale: refines HR-001; the same default as the save path (REQ-WFM-153), so a check and a save of the same graph agree
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: a graph without the field `kind` and the same graph with `"kind": "workflow"` give the same rule report (exact)
- Verified by: TC-GTB-039
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17)

### REQ-GTB-039 – Unknown kind in a check
- Level: low   Subject: Persistence
- Group: RS
- Text: If the kind of a checked graph is not in the registry of kinds, then the Graph tables shall return a rule report with the single item `unknown_kind`, naming the kind as its part.
- Rationale: refines HR-001 and D-404 (the reason `unknown kind`); the rules of an unknown kind are not known, so nothing else can be said (Q-7); the save keeps CORE's `schema_break` / `kind` (REQ-WFM-154)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: a graph of kind `swarm` with a cycle gives exactly `[{"rule": "unknown_kind", "parts": ["swarm"], ...}]` (exact)
- Verified by: TC-GTB-040
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, finding 10)

### REQ-GTB-040 – A check never raises
- Level: low   Subject: Persistence
- Group: RS
- Text: If a checked graph is malformed, then the Graph tables shall return a rule report instead of raising an exception.
- Rationale: refines HR-002; the same contract as the record checks of IF-301 (A-60); the prototype raised on connection data that is not an object and on steps without IDs (finding 4). Malformed: a step or connection that is not an object, data that is not an object, a missing or non-text ID or end
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: each of five malformed graphs (a step that is a number, connection data that is a list, a step without `id`, a connection without `from`, `nodes` that is not a list) returns a list; no exception escapes (exact)
- Verified by: TC-GTB-041
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, finding 4)

### REQ-GTB-041 – Rule 1, step identity
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `step_identity` for every step whose ID is not a non-empty text or repeats the ID of an earlier step, naming those IDs.
- Rationale: refines HR-002 and D-375 (whitespace and repeated IDs); a slash inside a step ID is allowed, as in CORE (Q-4, REQ-GTB-029: the graph ID ends at the first slash)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: steps `a`, `a` and `` give `step_identity` naming `a` and `` ; a step `x/y` breaks no rule by its ID (exact)
- Verified by: TC-GTB-042
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, finding 5)

### REQ-GTB-042 – Rule 2, kind of step
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `step_kind` for every step whose type is none of `data`, `transform` and `master`, naming those steps.
- Rationale: refines HR-002; the rule of REQ-WFM-043 under its name in the registry
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a step of type `loop` gives `step_kind` naming it; steps of the three types give no item (exact)
- Verified by: TC-GTB-042
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17)

### REQ-GTB-043 – Rule 3, connection ends
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `connection_endpoints` for every connection whose start or end names no step of the graph, naming those connections.
- Rationale: refines HR-002; today's runner refuses the same before a run (REQ-RUN-016, `graph_run.py`)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a connection `e2` from `a` to the missing step `z` gives `connection_endpoints` naming `e2` (exact)
- Verified by: TC-GTB-042
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17)

### REQ-GTB-044 – Rule 4, duplicate connection
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `duplicate_connection` for every connection that repeats the ID, or the start, end, role and name, of an earlier connection, naming those connections.
- Rationale: refines HR-002 and D-375 (duplicate connections, new against the five older rules); role is the field `role`, name the field `as` of the connection's data; two connections that differ only in `as` hand over two names and are not duplicates
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: `e1` and `e2` both from `a` to `t` without role and name give `duplicate_connection` naming `e2`; two connections with the ID `e1` name `e1`; the same pair with `as` `x` and `y` gives no item (exact)
- Verified by: TC-GTB-042
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, finding 6)

### REQ-GTB-045 – Rule 5, adjacency
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `adjacency` for every connection between two existing steps that are both data steps or both not data steps, naming those connections.
- Rationale: refines HR-002; the rule of REQ-WFM-045 under its name; a connection with a missing end is rule 3, not rule 5; a transform connected to itself breaks this rule and the cycle (seen on the scratch run of 2026-11-22: `T1>T1` is named by both)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a connection from data `d1` to data `d2` and one from transform `t1` to master `m1` give `adjacency` naming both; a connection from `d1` to the missing `z` gives no `adjacency` item (exact)
- Verified by: TC-GTB-042
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17)

### REQ-GTB-046 – Rule 6, one writer
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `single_writer` for every data step that connections from more than one existing step lead into, naming those data steps.
- Rationale: refines HR-002; the rule of REQ-WFM-046 under its name
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: transforms `t1` and `t2` both connected into data `d` give `single_writer` naming `d`; two connections from `t1` into `d` give no `single_writer` item (they are rule 4) (exact)
- Verified by: TC-GTB-042
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, finding 6)

### REQ-GTB-047 – Rule 7, session setting and stop limit
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `stop_limit` for every loop-controlling step without a valid stop limit, data step holding `stop` or `session`, and step with more than one settings connection, naming those steps.
- Rationale: refines HR-002; Q-1 confirms ASM-3; a valid stop limit is that of REQ-WFM-048 (a positive maximum number of repetitions or a positive maximum time), so `max_seconds: 1.0` stays valid (finding 6); none of the 17 graphs the prototype stores breaks it (finding 11)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a master without `stop`, a data step with `session`, and a transform with two settings connections each give `stop_limit` naming that step; a master with `{"max_seconds": 1.0}` gives no item (exact)
- Verified by: TC-GTB-042
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, CP18)

### REQ-GTB-048 – Rule 8, cycle
- Level: low   Subject: Persistence
- Group: RD
- Text: While `step_identity` and `connection_endpoints` are kept, the Graph tables shall report `cycle` for a graph whose steps cannot be ordered, naming the cycle with its first step repeated at the end.
- Rationale: refines HR-002 and REQ-WFM-047 (the cycle is named, its first step repeated at the end; finding 3); an order needs known, unique steps (Q-5), so the owner sees the cycle once identity and ends are fixed
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: `d1 → t1 → d1` gives `cycle` with the parts `d1, t1, d1`; the same graph plus a connection to a missing step gives `connection_endpoints` and no `cycle` (exact)
- Verified by: TC-GTB-042
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, findings 3 and 8)

### REQ-GTB-049 – Refusal of a run: the kind first and alone
- Level: low   Subject: Persistence
- Group: RF
- Text: If a graph's kind is not in the registry or has the run flag no, then the run check of the Graph tables shall answer refused with one item naming the kind: `unknown_kind` or `kind_cannot_run`.
- Rationale: refines HR-003 and FR-64 "of a kind that cannot run"; the rules of such a kind say nothing about a run (ASM-7); refusal order kind, rules, inputs (D-416 (3))
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: a context graph gives refused with exactly one item `kind_cannot_run` naming `context`; a graph of kind `swarm` with a cycle gives exactly one item `unknown_kind` naming `swarm` (exact)
- Verified by: TC-GTB-043
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP19)

### REQ-GTB-050 – Refusal of a run: rules, then inputs
- Level: low   Subject: Persistence
- Group: RF
- Text: When a graph whose kind has the run flag yes is checked for a run, the Graph tables shall answer refused, listing every broken rule in registry order, then every unsupplied input, else ready.
- Rationale: refines HR-003 and D-416 (3); the trust check follows in the runner (REQ-RUN-038); the given values of the run are part of the question, so the same graph can be refused without values and ready with them (AC-018)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: a workflow graph with two writers and an unsupplied input gives refused with `single_writer` first and the input second; the converted `chat` skill gives ready with `{"input.text": "hello"}` (exact)
- Verified by: TC-GTB-043
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP19)

### REQ-GTB-051 – Unsupplied input
- Level: low   Subject: Persistence
- Group: RF
- Text: The run check of the Graph tables shall report every unsupplied input as one item naming the processing or loop-controlling step and the data step it reads.
- Rationale: refines HR-003 and D-375 (a step input nobody supplies); the term is defined above: no writer, no start value in the graph, no value given with the run; settings and order connections are not inputs here (a step gets `{}` without settings, REQ-RUN-030, an order connection hands over nothing, REQ-RUN-035); the inputs of a Stage with a prepare function count as given (REQ-RUN-039, D-418 (1))
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: the converted `chat` skill without values names the step `step.converse` and the data step `input.text`; a data step with a graph value, or one written by another step, is not named (exact)
- Verified by: TC-GTB-044
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP19)

### REQ-WFM-162 – Save with the rule set of the graph's kind
- Level: low   Subject: TaskRuntime
- Group: SV
- Text: When a graph is saved, the Workflow management shall check it with the rule report of IF-301 for the graph's kind.
- Rationale: refines HR-001 and HR-004; replaces CORE's `check_graph` (five rules, first broken group) and `context_problems` in the save path (prototype CP17: TC-WFM-164 and TC-WFM-168 stay green, finding 2)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: a workflow graph with two identical connections (a rule the five older rules lack) is refused on save naming `duplicate_connection`; the same graph checked through IF-301 gives the same items (exact)
- Verified by: TC-WFM-179
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17)

### REQ-WFM-163 – A refused save carries the rule report
- Level: low   Subject: TaskRuntime
- Group: SV
- Text: If a save is refused for broken rules, then the Workflow management shall return the rule report with the refusal.
- Rationale: refines HR-002 and HR-004; the editor shows rules with their sentences, the IDs alone lose the rule names (ASM-8, `SaveResult.rules`)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: the graph of AC-017 (a cycle and a second writer) saved gives a refusal whose rule report equals the report of IF-301 for the same graph, item by item (exact)
- Verified by: TC-WFM-180
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, ASM-8)

### REQ-WFM-164 – The flat list of named IDs
- Level: low   Subject: TaskRuntime
- Group: SV
- Text: The Workflow management shall offer the check of a workflow graph as a flat list of the parts of every broken rule, in the registry's order, keeping repeated IDs.
- Rationale: refines HR-002; `check_graph` stays (HLS section 1): three protected acceptance tests call `check_graph(graph) == []`; repeats are kept so a cycle keeps its first step at the end (finding 3)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a sound graph gives `[]`; `d1 → t1 → d1` gives `["d1", "t1", "d1"]`; the AC-017 graph gives the parts of `single_writer` before those of `cycle` (exact)
- Verified by: TC-WFM-181
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, finding 3)

### REQ-WFM-165 – History of a graph that was never stored
- Level: low   Subject: TaskRuntime
- Group: SV
- Text: If the versions of a graph or the history of one of its steps are asked for a graph ID that was never stored, then the Workflow management shall answer `not_found`.
- Rationale: states CORE's V-3 as implemented and accepted (D-414: "to be stated by the next amendment that touches the CORE requirements")
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: `graph_versions("never")` and `step_history("never", "a")` each fail with the reason `not_found` and store nothing (exact)
- Verified by: TC-WFM-182
- Status: Approved
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: CORE verification report V-3, D-414)

### REQ-RUN-036 – Run check before the first step
- Level: low-2   Subject: TaskRuntime
- Group: RR
- Text: When a graph is run, the Pipeline runner shall ask the run check of IF-301 with the given values before the first step runs, and run no step when it answers refused.
- Rationale: refines HR-003 and FR-64 "before any step has run"; today the runner refuses only a missing end and a cycle (REQ-RUN-016, `graph_run.py`)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: for each refusal reason of HR-006 (cycle, two writers, missing step, two identical connections, unsupplied input, context graph, unknown kind) the run ends `refused` and the marker function of every step was called 0 times (exact)
- Verified by: TC-RUN-036
- Status: Draft
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP19)

### REQ-RUN-037 – A refused run names every part
- Level: low-2   Subject: TaskRuntime
- Group: RR
- Text: If the run check answers refused, then the Pipeline runner shall end the run refused, naming the parts of every item in the check's order and keeping repeated IDs.
- Rationale: refines HR-003 and OC-2 "each broken part is named"; repeats are kept so a cycle keeps its first step at the end, as today (the scratch run of 2026-11-22 lost it when repeats were removed: three unit checks of `tests/test_graph_run_findings.py` failed)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: the graph `wf-cycle` is refused naming `D1, T1, D2, T2, D1`; the graph with the missing end `X8` names the connection `X8>T1`; the converted `chat` skill without values names `input.text` (exact)
- Verified by: TC-RUN-037
- Status: Draft
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP19; scratch run 2026-11-22)

### REQ-RUN-038 – Trust after the run check
- Level: low-2   Subject: TaskRuntime
- Group: RR
- Text: While the run check answers ready, the Pipeline runner shall check the trust of the steps as REQ-RUN-017 says.
- Rationale: refines HR-003; D-416 (3): a graph that breaks the rules is refused whatever its trust; trust per step is G-V4.GRAPHAPI.CODE
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: a graph with a cycle and an untrusted transform is refused naming the cycle, without the trust status; the same graph without the cycle is refused naming the untrusted transform and its status (exact)
- Verified by: TC-RUN-038
- Status: Draft
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: D-416 (3))

### REQ-RUN-039 – Inputs a prepare function may give
- Level: low-2   Subject: TaskRuntime
- Group: RR
- Text: When the Pipeline runner asks the run check, it shall count every input of a step whose function has a prepare function as a given value.
- Rationale: refines HR-003 and keeps REQ-RUN-034 (D-250) as it is: a prepare function may give a default input, which the run check cannot see in the graph, and "else nothing" stays for such an input. Without this the protected TC-RUN-034 is refused in two cases (scratch run 2026-11-22); with it every protected run test passes unchanged. It narrows FR-64 a little (a prepare function that gives nothing leaves the input empty instead of refused); chosen by the owner (D-418 (1))
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: the TC-RUN-034 graph (`DB` read by a Stage `T` with a prepare function, no value anywhere) runs; the same graph with a plain function for `T` is refused naming `DB` and `T` is not called (exact)
- Verified by: TC-RUN-039
- Status: Draft
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: scratch run 2026-11-22 of the protected run tests with the run check in front; owner's choice D-418 (1))

### REQ-GTB-052 – The document form keeps its five rules
- Level: low   Subject: Persistence
- Group: DF
- Text: The Graph tables shall keep the check of the document form (IF-301 `validate`) and its five rules unchanged in IF-301 v4.
- Rationale: Q-6: the document form (IF-301 `validate`, IF-102, IF-104 v1, IF-203) keeps REQ-GTB-002 until G-V4.MIGRATION retires it; RULES covers every check of the stored form; the v1 to v3 contract suites stay unchanged
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: the contract suites of IF-301 v1, v2 and v3 and the suites of IF-102, IF-104 v1 and IF-203 pass unchanged against the v4 code (exact)
- Verified by: TC-GTB-045
- Status: Draft
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: Q-6, prototype round 04, finding 1)

## Changed requirements (proposed; the approved text in `In force:` stays in force until the owner approves the change, M8)

### REQ-WFM-150 – Refused save writes nothing
- Level: low   Subject: TaskRuntime
- Group: SV
- In force (Verified, CORE): "If a save is refused, then the Workflow management shall write no record, count no version and name the broken rule or the IDs."
- Text: If a save is refused, then the Workflow management shall write no record, count no version and name every broken rule in registry order with its parts.
- Rationale: refines NFR-16 and HR-004; finding 2: with the rule set a refused save names every broken rule, not the first group; the CORE text ("names") already allows it, the change makes it checkable (OC-1). TC-WFM-168 stays as it is (prototype CP17); the new case goes to TC-WFM-180
- Parent: NFR-16
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-10 (accepted case AC-003) unchanged, plus: the AC-017 graph (a cycle and a second writer) names `single_writer` and then `cycle`, each with its parts, and no table grew (exact)
- Verified by: TC-WFM-168, TC-WFM-180
- Status: Approved
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new; verified 2026-11-22 (D-414); G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, change proposed (basis: prototype round 04, finding 2)

### REQ-WFM-154 – Unknown kind refused
- Level: low   Subject: TaskRuntime
- Group: SV
- In force (Verified, CORE): "If the kind of a graph is neither `workflow` nor `context`, then the Workflow management shall refuse the save and name the field `kind`."
- Text: If a graph names a kind that is neither `workflow` nor `context`, including an empty kind (`null`), then the Workflow management shall refuse the save and name the field `kind`.
- Rationale: refines FR-57; states CORE's V-2 as implemented and accepted (D-414); REQ-WFM-153 ("no kind means workflow") then covers only a graph without the field `kind`
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-14 unchanged (kind `swarm` refused naming `kind`, nothing stored), plus: `"kind": None` is refused naming `kind` and nothing is stored (exact)
- Verified by: TC-WFM-172, TC-WFM-183
- Status: Approved
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new; verified 2026-11-22 (D-414); G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, change proposed (basis: CORE verification report V-2, D-414)

### REQ-WFM-155 – Rules of a context graph on save
- Level: low   Subject: TaskRuntime
- Group: SV
- In force (Verified, CORE): "When a context graph is saved, the Workflow management shall refuse a repeated step ID, a repeated connection ID or a connection to a missing step, and name the IDs."
- Text: When a context graph is saved, the Workflow management shall refuse it if it breaks a rule of the kind `context`, naming the broken rules with their parts.
- Rationale: refines FR-57 and HR-001; Q-3 (rule 4 in full) and finding 7: the same definitions refuse an empty step ID and two identical connections, which CORE's `context_problems` accepts; the rules come from the registry (D-404), CONTEXT may add rules by amendment (FR-75, ASM-4)
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-15 unchanged (each of the three faults refused naming the ID, nothing written), plus: two identical connections with different IDs and an empty step ID are each refused naming the rule (exact)
- Verified by: TC-WFM-173, TC-WFM-184
- Status: Approved
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new; verified 2026-11-22 (D-414); G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, change proposed (basis: prototype round 04, finding 7, Q-3)

## Notes for other subgoals (not requirements of RULES)
- EDIT and the check route (IF-104 v2, G-V4 level): every entry point checks a working copy with the kind stored for the graph; the prototype's page lost it (finding 9). RULES tests the check route against a mock returning the rule report (D-416 (2)).
- CODE: the known-tool check (Q-2). TRANSFER or MIGRATION: the read-only listing of an unknown kind (Q-7). MIGRATION: retires the document form and REQ-GTB-052 with it (Q-6).
- HLS section 5 names REQ-RUN-016 for the refusal change; REQ-RUN-016 (order) keeps its text, the refusal is the new group RR. Its protected TC-RUN-016 passes with the run check in front (scratch run 2026-11-22).
- REQ-RUN-034 keeps its text (D-418 (1)): "else nothing" stays reachable for outputs and for the inputs of a Stage with a prepare function; TC-RUN-034 passes unchanged.
- The unit check `tests/test_graph_run_findings.py` (self-loop) expects only the cycle; a transform connected to itself now also names `adjacency` (REQ-GTB-045). Unit checks are changed in Implement, with this requirement as the reason.
- REQ-RUN-033 (more than one settings connection) overlaps rule 7: the run check refuses such a graph first and names the same step; TC-RUN-033 passes (scratch run 2026-11-22).
