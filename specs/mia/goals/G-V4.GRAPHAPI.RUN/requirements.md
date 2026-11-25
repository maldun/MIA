# Requirements: G-V4.GRAPHAPI.RUN (low level, new and changed items)

**Top-level spec:** `specs/mia/goals/G-V4.GRAPHAPI/top-level-spec.md` (FR-65; NFR-17 for the six skills with equivalence suites)   **High-level spec:** `specs/mia/goals/G-V4.GRAPHAPI.RUN/high-level-spec.md` (HR-001 to HR-007, reviewed by group 2026-11-23, D-476)   **Status:** Draft (2026-11-24, written by the agent on the owner's word "do them yourself"; for the owner's review group by group)   **Plan baseline:** –

<!-- The requirements this subgoal adds, and the proposed wording changes of requirements in force.
     Basis: the read-only survey of the run path (2026-11-23, D-473), the networkx spike of the group, the owner's decisions D-473 to D-476,
     RULES as merged (IF-301 v4), CORE as verified, the G-V2 equivalence work (REQ-WFM-057 to 060, 069, 110 to 115: still Draft from G-V2).
     Where they go at the merge: the loader and the rule set on it (groups LG, RV) into N-3.2, offered through IF-301 v5 (amendment A-187);
     the order (group OR) into N-2.3; the run and the stored-graph path (groups RN, SP) into N-2.4.1, the run record's two fields with
     N-2.4.3's run log; the equivalence (group EQ) into N-2.3.
     Requirements in force that stay as they are: REQ-RUN-017, 018, 019, 036 to 039, REQ-GTB-033 to 052 (their answers do not change, HR-006),
     REQ-WFM-144, 157, 159 (reading a stored graph).
     Drafts of G-V2 taken in unchanged for approval (they describe today's runner, which now reads the loaded graph): REQ-RUN-030 to 035.
     Not here: the nine user-interface skills and the removal of the old runner (G-V4.GRAPHAPI.SWITCH, D-474); the real import of the skills
     (G-V4.GRAPHSTORE.MIGRATION, D-473 (1)); trust per step and its mark (G-V4.GRAPHAPI.CODE). -->

## Terms
| Term | Meaning |
|---|---|
| stored form | a graph as `{"kind"?, "nodes": [{"id", "data"}], "edges": [{"id", "from", "to", "data"}]}` with local IDs, as CORE saves and reads it and IF-301 v4 checks it |
| loaded graph | the networkx `MultiDiGraph` that `load` builds from a stored form: one node per step (key: the step ID), one edge per connection (key: the connection ID) |
| position (of a step or connection) | its index, from 0, in the `nodes` or `edges` list of the stored form |
| well-formed step | a step whose ID is a non-empty text and that is the first step with that ID in the list |
| well-formed connection | a connection whose ID is a non-empty text, that is the first connection with that ID, and whose `from` and `to` name well-formed steps |
| reads from (step A reads from step B) | the loaded graph has an edge from B to A; a processing step reads from its input data steps, a data step from its writer |
| ready (step) | while the order is built: a step not yet ordered whose every step it reads from is already ordered |
| stored-graph path | a skill run from a graph in the store: read (N-2.3), load (N-3.2), the step functions from the toolbox, run (N-2.4.1) |
| graph of a skill | the stored workflow graph whose ID is `<pipeline name>@<pipeline version>` of the skill, as the converted graphs are named today (`verify.single@1`) |
| the six skills | research, plan_question, verify_claim, verify_computable, extract_claims, extract_claims_rules: the skills with an equivalence suite (`SUITE_OF`, `eval-spec.md`) |
| run record | the `kind: "run"` line of the run log that `RunLog.start` writes |

## Groups
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 1 | LG | The loader: the stored form becomes one loaded graph, in IF-301 v5 (HR-001, HR-003, HR-005) | REQ-GTB-053, REQ-GTB-054, REQ-GTB-055, REQ-GTB-056, REQ-GTB-057, REQ-GTB-058 |
| 2 | RV | The rule set reads the loaded graph, with the same answers (HR-001, HR-006) | REQ-GTB-059, REQ-GTB-060, REQ-GTB-043 (changed) |
| 3 | OR | The order of steps on the loaded graph, ties in the order steps became ready (FR-65, HR-002) | REQ-WFM-166, REQ-WFM-167, REQ-RUN-016 (changed) |
| 4 | RN | The run reads the loaded graph, one step at a time (FR-65, HR-001, HR-002, HR-003) | REQ-RUN-040, REQ-RUN-041 (and REQ-RUN-030 to 035 taken in unchanged, below) |
| 5 | SP | A skill runs from its stored graph, and its run record says which (HR-004) | REQ-RUN-042, REQ-RUN-043, REQ-RUN-044, REQ-RUN-045 |
| 6 | EQ | The six skills give the same results from their stored graph (NFR-17, HR-007) | REQ-WFM-168, REQ-WFM-110 (changed), REQ-WFM-111 (changed), REQ-WFM-112 (changed), REQ-WFM-113 (changed), REQ-WFM-114 (changed), REQ-WFM-115 (changed) |

## Group LG – the loader

### REQ-GTB-053 – One loaded graph from the stored form
- Level: low   Subject: Persistence
- Group: LG
- Text: When `load` of IF-301 is given a graph in stored form, the Graph tables shall return a networkx `MultiDiGraph` with one node per well-formed step and one edge per well-formed connection.
- Rationale: refines HR-001 and HR-005; one loaded graph for the order, the rules and the run (OC-1); a `MultiDiGraph` keeps two connections between the same two steps, which no rule refuses (spike)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: for each of the 15 converted skill graphs, the loaded graph has exactly the step IDs as nodes and the connection IDs as edge keys of the stored form; a graph with two connections `e1`, `e2` from `d1` to `t1` gives two edges (exact)
- Verified by: TC-GTB-048
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

### REQ-GTB-054 – Steps keep their fields and their position
- Level: low   Subject: Persistence
- Group: LG
- Text: The Graph tables shall give each node of a loaded graph the attribute `data`, equal to the step's `data`, and the attribute `position`, the step's position in the stored form.
- Rationale: refines HR-003 (type, tool, stop limit, settings values reach the run unchanged; OC-3) and HR-002 (ties by position)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: for every step of the 15 converted skill graphs, including the master steps of research and verify_computable and the settings steps, `G.nodes[id]["data"] == step["data"]` and `position` is its index (exact)
- Verified by: TC-GTB-049
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

### REQ-GTB-055 – Connections keep their fields and their position
- Level: low   Subject: Persistence
- Group: LG
- Text: The Graph tables shall give each edge of a loaded graph the key of the connection ID and the attributes `data`, equal to the connection's `data`, and `position`, the connection's position in the stored form.
- Rationale: refines HR-003: role (`settings`, `order`) and name (`as`) reach the run unchanged; a step that reads several data steps gets each by its name (OC-3)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: for every connection of the 15 converted skill graphs, the edge from `from` to `to` with the connection ID as key has `data` equal to the connection's `data` and `position` its index; a step of review_full reads its six named inputs from six edges (exact)
- Verified by: TC-GTB-049
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

### REQ-GTB-056 – The graph's own fields
- Level: low   Subject: Persistence
- Group: LG
- Text: The Graph tables shall keep in the attributes of the loaded graph every field of the stored form other than `nodes` and `edges`, and the kind `workflow` where the stored form names no kind.
- Rationale: the kind selects the rule set (REQ-GTB-033, 038); the header fields (description, context graph) stay with the graph
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: a stored form with `kind`, `id` and `description` gives `G.graph` with the same three; the same form without `kind` gives `G.graph["kind"] == "workflow"` (exact)
- Verified by: TC-GTB-049
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

### REQ-GTB-057 – Malformed items are left out, never an error
- Level: low   Subject: Persistence
- Group: LG
- Text: If a step or connection of the given graph is not well-formed, then the Graph tables shall leave it out of the loaded graph and raise no exception.
- Rationale: the rule report must never raise (REQ-GTB-040) and names such items itself from the stored form (`step_identity`, `connection_endpoints`); the loaded graph holds only what can be ordered and run; a connection with `data` that is no object breaks no rule and the run check still counts it as an input, so it stays in the loaded graph (owner, D-481)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: an input that is not a stored form at all (`nodes` = `"x"`, `None`) gives an empty loaded graph and no exception; the malformed inputs of golden example 31 of IF-301 (a step `5`, a step without `id`, a connection without `from`, `nodes` = `"x"`) and a second step with an ID already used each give a loaded graph without that item and no exception; a connection whose `data` is a list is well-formed (its ID and ends are fine, the rules accept it): it is kept, with empty `data` (exact)
- Verified by: TC-GTB-050
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

### REQ-GTB-058 – Loading changes nothing
- Level: low   Subject: Persistence
- Group: LG
- Text: The Graph tables shall build the loaded graph from copies, so that a change of the loaded graph leaves the stored form unchanged and a change of the stored form leaves the loaded graph unchanged.
- Rationale: `load` is pure like the other operations of IF-301 (nothing stored, nothing shared); the runner writes values while the stored form is still read by others
- Parent: HR-005
- Priority: Must
- Verification method: Test
- Acceptance criterion: changing `G.nodes[id]["data"]` of a loaded graph leaves the stored form equal to a deep copy taken before; changing the stored form's step data leaves the loaded graph's equal to before (exact)
- Verified by: TC-GTB-050
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

## Group RV – the rule set on the loaded graph

### REQ-GTB-059 – The graph rules read the loaded graph
- Level: low   Subject: Persistence
- Group: RV
- Text: The Graph tables shall evaluate the rules about adjacency, one writer, session setting and stop limit, cycle and unsupplied inputs on the graph that `load` gives for the checked stored form.
- Rationale: refines HR-001: the rule set's own view and its copied cycle finder go; the rules about step identity, kind of step, connection ends and duplicate connections stay on the stored form, where malformed items are seen (REQ-GTB-057)
- Parent: HR-001
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: in `graph_rule_set.py` no function builds its own adjacency, writer or cycle view; the rules named in the text take a loaded graph from `load`; no copy of a cycle finder remains (inspection, with the defect check of TC-GTB-051)
- Verified by: TC-GTB-051
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

### REQ-GTB-060 – The same rule answers as before
- Level: low   Subject: Persistence
- Group: RV
- Text: The Graph tables shall give, through the loaded graph, the same `rule_report` and `run_check` answers as IF-301 v4 gave before this change, for every stored form whose connections have unique non-empty text IDs.
- Rationale: refines HR-006 (OC-2 "every result is the same as before"); the answers of v4 are recorded as an oracle before the code changes; a stored form with another connection is refused on the stored form by rule 3 (REQ-GTB-043, changed) or rule 4, as in v4, and may name fewer further items, because `load` leaves that connection out (A-189, D-483; no input of the oracle has such a connection)
- Parent: HR-006
- Priority: Must
- Verification method: Test
- Acceptance criterion: on the 15 converted skill graphs, the 500 random graphs of the spike (seed 7, with self loops) and the golden examples 24 to 31 of IF-301, every `rule_report` and `run_check` answer equals the answer recorded from IF-301 v4 at `goal/v4` (0 differences, exact)
- Verified by: TC-GTB-052, TC-GTB-053
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24; Implement T-02, 2026-11-25, changed: unique text connection IDs (A-189, D-483)

### REQ-GTB-043 – Rule 3, connection ends (changed)
- Level: low   Subject: Persistence
- Group: RV
- Text: The Graph tables shall report the rule `connection_endpoints` for every connection whose start or end names no step of the graph, or whose ID is not a non-empty text, naming those connections.
- Rationale: in force: "…for every connection whose start or end names no step of the graph, naming those connections"; changed because `load` leaves out a connection without a non-empty text ID (REQ-GTB-057), so the rules on the loaded graph would not see it and the save would reach the record checks with it and raise (T-02 finding, A-189, D-483); the part is the ID as text, `"None"` when missing, as for a step (REQ-GTB-040)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a connection `e2` from `a` to the missing step `z` gives `connection_endpoints` naming `e2` (exact, in force); a connection from the data step `a` to the transform `t` without `id` gives `connection_endpoints` naming `None`, with `id` 5 naming `5`, with the empty `id` naming the empty text, and saving each graph is refused naming that part, with no exception (exact)
- Verified by: TC-GTB-042, TC-GTB-053, TC-IF-301-39
- Status: Draft
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17); G-V4.GRAPHAPI.RUN Implement T-02, 2026-11-25, changed (A-189, D-483)

## Group OR – the order

### REQ-WFM-166 – Every step after the steps it reads from
- Level: low   Subject: TaskRuntime
- Group: OR
- Text: When the order of a workflow graph is asked, the Workflow management shall list every step of its loaded graph once, each after every step it reads from.
- Rationale: refines FR-65 "every step runs after the steps it reads from" and HR-001 (the order reads the loaded graph); today `order_of` builds its own view
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: for the 15 converted skill graphs and the acyclic ones of the 500 random graphs, the order holds every step once and every edge points from an earlier to a later step (exact)
- Verified by: TC-WFM-185
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

### REQ-WFM-167 – Ties in the order steps became ready
- Level: low   Subject: TaskRuntime
- Group: OR
- Text: When the order of a workflow graph is asked, the Workflow management shall list first the steps that read from no step, in their position in the stored form, and then each further step as soon as the last step it reads from is listed, in the order in which the steps became ready.
- Rationale: refines FR-65 "the same graph with the same inputs runs the same steps in the same order" and HR-002 (owner, D-475 (2): today's order stays); the rule is today's first-ready-first order (a queue), not "lowest position among the ready": that rule gives another order for 62 of the 159 acyclic random graphs and for research and verify_computable (found writing the red tests, D-480), so the walk over the loaded graph is a queue, not networkx `lexicographical_topological_sort`
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a graph with two independent steps listed `b`, `a` orders `b` before `a`; listed `a`, `b` it orders `a` before `b`; steps listed `x`, `y`, `z` where `x` reads from `z` order `y`, `z`, `x`; steps listed `x`, `y`, `z` where `x` reads from `y` order `y`, `z`, `x` (`x` became ready after `z` was already waiting); for the 15 converted skill graphs and the acyclic random graphs the order equals the order today's `order_of` gives, recorded before the change (0 differences, exact)
- Verified by: TC-WFM-186
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; review 2026-11-24 (D-478): text rewritten, the pairwise rule could not be met by the sort and could contradict indirect reads; Approved in batch in Emacs on 2026-11-24

### REQ-RUN-016 – Run in topological order (changed)
- Level: low-2   Subject: TaskRuntime
- Group: OR
- Text: When a workflow graph is run, the Pipeline runner shall run its transforms and master nodes in the order of REQ-WFM-166 and REQ-WFM-167, each reading its input data nodes and writing its output data nodes.
- Rationale: in force: "…in a topological order…"; changed so that the run uses the one order with its tie rule (FR-65, HR-002); the acceptance criterion in force is kept
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a graph with three transforms runs in an order that respects its edges and the output nodes hold the results (exact, in force); and the run order of two independent transforms follows their positions (exact)
- Verified by: TC-RUN-016, TC-RUN-041
- Status: Approved
- History: Verified in G-V1; G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, changed (the one order, D-475 (2)); Approved in batch in Emacs on 2026-11-24

## Group RN – the run

### REQ-RUN-040 – One step at a time
- Level: low-2   Subject: TaskRuntime
- Group: RN
- Text: While a graph is running, the Pipeline runner shall start a step only after the step before it in the order has finished.
- Rationale: refines FR-65 "no two steps run at the same time"; the items of a map step with `workers` above 1 run in parallel inside that one step and are not steps of the graph (high-level spec, key decisions)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: in a run of a graph with four independent transforms whose functions record their start and end times and sleep 0.05 s, every start is after the end of the step before in the order (exact)
- Verified by: TC-RUN-042
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

### REQ-RUN-041 – The run reads the loaded graph
- Level: low-2   Subject: TaskRuntime
- Group: RN
- Text: When a graph is run, the Pipeline runner shall take the types of the steps and the roles and names of the connections from the graph that `load` gives for it.
- Rationale: refines HR-001: `_kinds`, the `reads` map, `_given` and the edge scans of `graph_run.py` go; the run sees what the order and the rules see
- Parent: HR-001
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: `graph_run.py` reads steps and connections only through a loaded graph; no list of `graph["nodes"]` or `graph["edges"]` is scanned in it (inspection); TC-RUN-016 to 019 and 030 to 039 stay green unchanged (exact)
- Verified by: TC-RUN-043
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

REQ-RUN-030 to REQ-RUN-035 (Stage gets inputs, outputs and settings; per-output writes; plain callables unchanged; broken wiring refused before any node ran; start values; order edge) are taken in **unchanged** from G-V2 (Draft there, built and checked by TC-RUN-030 to 035) for approval with this group: they state what the run does with the loaded graph's roles and names (HR-003, OC-3). Their texts stay in `specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.1-pipeline-runner/requirements.md`; only their status changes, at the merge, to Approved.

## Group SP – the stored-graph path

### REQ-RUN-042 – A skill with a stored graph runs from it
- Level: low-2   Subject: TaskRuntime
- Group: SP
- Text: When a skill runs whose graph is in the store, the Pipeline runner shall run the newest version of that graph, loaded by IF-301, with the step functions of the toolbox.
- Rationale: refines HR-004 and OC-1, OC-4: the path from storage to a run is RUN's (D-473 (1)); the graph of a skill is named `<pipeline name>@<pipeline version>`, as the converted graphs are today
- Parent: HR-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: with the converted graph of verify_claim saved through CORE's save path into a throw-away store, a run of verify_claim on scripted replies reads that graph (the read is recorded) and gives the answer of the in-memory converted run (exact)
- Verified by: TC-RUN-044
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

### REQ-RUN-043 – Without a stored graph, as before
- Level: low-2   Subject: TaskRuntime
- Group: SP
- Text: While a skill has no graph in the store, the Pipeline runner shall run it as before this change.
- Rationale: MIGRATION imports the skills later (D-473 (1)); until then nothing changes for a skill without a stored graph; SWITCH removes the old runner (D-474)
- Parent: HR-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: with an empty store, a run of each of the six skills on scripted replies gives the same model calls and answer as at `goal/v4` (exact)
- Verified by: TC-RUN-045
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

### REQ-RUN-044 – The run record names the graph and its version
- Level: low-2   Subject: TaskRuntime
- Group: SP
- Text: When a skill runs from its stored graph, the Pipeline runner shall write the graph ID and the version that ran into the fields `graph` and `graph_version` of the run record.
- Rationale: refines HR-004 (owner, D-475 (3)); MIGRATION's OC-3 ("says which graph and version it used") and CODE's FR-67 (the version that ran) use it; a run without a stored graph writes neither field
- Parent: HR-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: the run of TC-RUN-044 with the graph saved twice (versions 1 and 2) has a run record with `graph` = `verify.single@1` and `graph_version` = 2; a run with an empty store has neither field (exact)
- Verified by: TC-RUN-046
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

### REQ-RUN-045 – A stored graph that cannot run is refused, named
- Level: low-2   Subject: TaskRuntime
- Group: SP
- Text: If the stored graph of a skill is refused by the run check, then the Pipeline runner shall end the run refused, name the graph ID and its version and run no step.
- Rationale: a stored graph may have been changed in the editor since it was imported; it is refused like any graph (REQ-RUN-036, 037) and the owner learns which graph and version
- Parent: HR-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: with a stored version 2 of the graph of verify_claim that has a cycle, the run ends `refused` naming `cycle`, `verify.single@1` and version 2, and the marker of every step was called 0 times (exact)
- Verified by: TC-RUN-047
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

## Group EQ – the six skills from their stored graph

### REQ-WFM-168 – The same model calls from the stored graph
- Level: low   Subject: TaskRuntime
- Group: EQ
- Text: When one of the six skills runs from its stored graph on scripted replies, the Workflow management shall make the model calls of the old runner, in order, with equal prompts and options.
- Rationale: refines HR-007 and REQ-WFM-058 for the stored-graph path; a cheap check without a model that catches a changed order or wiring before the suite runs
- Parent: HR-007
- Priority: Must
- Verification method: Test
- Acceptance criterion: per skill of the six, on the scripted replies of REQ-WFM-058, the list of model calls from the stored graph equals that of the old runner (exact, a diff is shown)
- Verified by: TC-WFM-187
- Status: Approved
- History: G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, new; Approved in batch in Emacs on 2026-11-24

### The six equivalence requirements, changed
Each keeps its threshold, `Eval criterion` line (rule, MP-light, repeats, alpha, false-alarm budget) and relaxation of G-V2 (Draft there; TD-88 keeps the holdout for later), with one change: the skill runs **from its stored graph** (HR-007, D-473 (3)). The thresholds were set from the old-runner baselines of commit `1fb0c35` (A-122); the decision is `eval_decide.py` with each `Eval criterion` line. REQ-WFM-115 compares the outputs from the stored graph with those of the old runner run on the same cases in the same check: no baseline file is needed (HR-007 corrected accordingly, D-477 (1)). A failing criterion is re-run once with fresh seeds, never more.

### REQ-WFM-110 – Same outcomes: research (changed)
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run the skill research from its stored graph so that it behaves as expected in at least 85 % of the dev cases of EV-research.
- Rationale: refines FR-45 and AC-34; v0.1.0 baseline 0.95 (run research__escalate__20261115-173301, 20 cases, 3 repeats, 57 of 60) minus the margin 0.10, a starting guess under D-187 (REQ-WFM-069); the secondary suite EV-research_compound is run and reported, not decided
- Parent: FR-45
- Group: EQ
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-34: the share of right cases of the skill run from its stored graph on the dev split of EV-research is at least 0.85 (3 repeats folded by majority, MP-light), decided by the rule, not by eye
- Eval criterion: suite=EV-research; select=; metric=right; min=0.85; n=20; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0003; split=dev
- Verified by: TC-WFM-110, EV-research
- Status: Approved
- Relaxed: TD-88
- Target: holdout suites for the five skills, decided once in a Verify (see TD-88)
- History: G-V2 Plan step 3 (2026-11-07), new, split from REQ-WFM-059 (owner); A-122 (2026-11-15): floor 0.82 to 0.85 on the recorded baseline (0.95), owner approved, back in review; Commit G-V2 (2026-11-20): Relaxed TD-88 (D-355); G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, changed: run from the stored graph (HR-007, D-473 (3)); criterion, eval line and relaxation unchanged; Approved in batch in Emacs on 2026-11-24

### REQ-WFM-111 – Same outcomes: plan_question (changed)
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run the skill plan_question from its stored graph so that it behaves as expected in at least 54 % of the dev cases of EV-plans.
- Rationale: refines FR-45 and AC-34; v0.1.0 baseline 0.64 (research-planners.md, 36 plans, 3 repeats, plan.free@1) minus the margin 0.10, a starting guess under D-187 (REQ-WFM-069); the baseline is low on purpose: the skill runs plan.free@1 today, the checked planner is a later change
- Parent: FR-45
- Group: EQ
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-34: the share of right cases of the skill run from its stored graph on the dev split of EV-plans is at least 0.54 (3 repeats folded by majority, MP-light), decided by the rule, not by eye
- Eval criterion: suite=EV-plans; select=; metric=right; min=0.54; n=36; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0122; split=dev
- Verified by: TC-WFM-111, EV-plans
- Status: Approved
- History: G-V2 Plan step 3 (2026-11-07), new, split from REQ-WFM-059 (owner); G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, changed: run from the stored graph (HR-007, D-473 (3)); criterion, eval line and relaxation unchanged; Approved in batch in Emacs on 2026-11-24

### REQ-WFM-112 – Same outcomes: verify_claim (changed)
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run the skill verify_claim from its stored graph so that it behaves as expected in at least 83 % of the dev cases of EV-verdicts.
- Rationale: refines FR-45 and AC-34; v0.1.0 baseline 0.93 (verdicts-single.md, 50 claims, 1 run, verify.single@1) minus the margin 0.10, a starting guess under D-187 (REQ-WFM-069); the baseline had one repeat and was re-recorded at 3 repeats (A-122); the suites EV-verdicts_injection and EV-verdicts_wikidata are run and reported, not decided
- Parent: FR-45
- Group: EQ
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-34: the share of right cases of the skill run from its stored graph on the dev split of EV-verdicts is at least 0.83 (3 repeats folded by majority, MP-light), decided by the rule, not by eye
- Eval criterion: suite=EV-verdicts; select=; metric=right; min=0.83; n=50; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0001; split=dev
- Verified by: TC-WFM-112, EV-verdicts
- Status: Approved
- History: G-V2 Plan step 3 (2026-11-07), new, split from REQ-WFM-059 (owner); G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, changed: run from the stored graph (HR-007, D-473 (3)); criterion, eval line and relaxation unchanged; Approved confirmed in Emacs on 2026-11-24

### REQ-WFM-113 – Same outcomes: verify_computable (changed)
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run the skill verify_computable from its stored graph so that it behaves as expected in at least 87 % of the dev cases of EV-computable.
- Rationale: refines FR-45 and AC-34; v0.1.0 baseline 0.974 (run computable__computable2__20261115-173501, 39 cases, 3 repeats, 114 of 117) minus the margin 0.10, a starting guess under D-187 (REQ-WFM-069)
- Parent: FR-45
- Group: EQ
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-34: the share of right cases of the skill run from its stored graph on the dev split of EV-computable is at least 0.87 (3 repeats folded by majority, MP-light), decided by the rule, not by eye
- Eval criterion: suite=EV-computable; select=; metric=right; min=0.87; n=39; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0000; split=dev
- Verified by: TC-WFM-113, EV-computable
- Status: Approved
- History: G-V2 Plan step 3 (2026-11-07), new, split from REQ-WFM-059 (owner); A-122 (2026-11-15): floor 0.82 to 0.87 on the recorded baseline (0.974), owner approved, back in review; G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, changed: run from the stored graph (HR-007, D-473 (3)); criterion, eval line and relaxation unchanged; Approved in batch in Emacs on 2026-11-24

### REQ-WFM-114 – Same outcomes: extract_claims (changed)
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run the skill extract_claims from its stored graph so that it behaves as expected in at least 59 % of the dev cases of EV-extraction.
- Rationale: refines FR-45 and AC-34; v0.1.0 baseline 0.69 (extraction-llm-light.md, 51 texts, 1 run, extract.llm@1) minus the margin 0.10, a starting guess under D-187 (REQ-WFM-069); the baseline had one repeat and was re-recorded at 3 repeats (A-122)
- Parent: FR-45
- Group: EQ
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-34: the share of right cases of the skill run from its stored graph on the dev split of EV-extraction is at least 0.59 (3 repeats folded by majority, MP-light), decided by the rule, not by eye
- Eval criterion: suite=EV-extraction; select=; metric=right; min=0.59; n=51; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0064; split=dev
- Verified by: TC-WFM-114, EV-extraction
- Status: Approved
- History: G-V2 Plan step 3 (2026-11-07), new, split from REQ-WFM-059 (owner); G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, changed: run from the stored graph (HR-007, D-473 (3)); criterion, eval line and relaxation unchanged; Approved in batch in Emacs on 2026-11-24

### REQ-WFM-115 – Same outputs: extract_claims_rules (changed)
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run the skill extract_claims_rules from its stored graph so that it gives the same output as the old runner on every dev case of EV-extraction.
- Rationale: refines FR-45 and AC-34; the skill is rule-based, no model: the same input gives the same output, so equality is checked instead of a rate (owner, D-477 (1), D-478)
- Parent: FR-45
- Group: EQ
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-34: the 51 outputs from the stored graph and of the old runner on the dev cases of EV-extraction are equal (exact, a diff is shown)
- Verified by: TC-WFM-115
- Status: Approved
- History: G-V2 Plan step 3 (2026-11-07), new, split from REQ-WFM-059 (owner); G-V4.GRAPHAPI.RUN Plan step 1b, 2026-11-24, changed: run from the stored graph (HR-007, D-473 (3)); criterion, eval line and relaxation unchanged; Approved in batch in Emacs on 2026-11-24
