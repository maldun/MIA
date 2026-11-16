# Draft: scenarios for the checks without one (G-V2.CONVERT, for the owner's review; nothing here is applied)

Where they go: part 1 at the end of `## Scenarios` of `specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/test-spec.md`, part 2 at the end of `## Scenarios` of `.../N-2.4.1-pipeline-runner/test-spec.md`. The wording follows the table rows of the same files (Given, When and Then are what the row says, written out), and the tests that carry them are the acceptance and unit modules named in each line (all green on `goal/v2.convert`).

## Decision needed first: five ids are used twice
`TC-WFM-130` to `TC-WFM-134` are in the workflow-management test spec twice: for G-V3.PANEL (REQ-WFM-130 to 134, table lines 60 to 68, with `Verified by` in the requirements) and for G-V2.CONVERT (A-125, table lines 61 to 64 and 120). `trace_check` does not say it, but a scenario `### TC-WFM-131` cannot belong to both. Proposal: keep the PANEL ids (they are verified by requirements) and renumber the five CONVERT checks to **TC-WFM-139 to TC-WFM-143** (138 is the highest in use). Needed: the table rows of the CONVERT five, the markers in the acceptance modules that name them, and this draft. The old ids are used in the drafts below in brackets.

## Part 1: workflow management (TC-WFM-116 to 129 and the five renumbered)

### TC-WFM-116 – Every function of a shipped node is in the common module
- Verifies: REQ-WFM-058 (A-123)
- Given: the shipped library nodes (`library/nodes`) and the old registries of research, extraction and verification
- When: the function each shipped code node names is looked up in `common_operations.FUNCTIONS`
- Then: every one is there and callable; a function of the old registries is the same object there, not a copy
- Carried by: `tests/acceptance/test_common_operations.py`

### TC-WFM-117 – The toolbox gives the value of the old function
- Verifies: REQ-WFM-058 (A-123)
- Given: the toolbox seeded from `library/nodes`; the inputs of `top_urls`, `tally` and `tidy_claims`
- When: `Toolbox.run(<node id>, args)` is called for each
- Then: the value equals exactly what the old function returns for the same input
- Carried by: `tests/acceptance/test_toolbox.py`

### TC-WFM-118 – Entries are thin
- Verifies: REQ-WFM-058 (A-123)
- Given: the seeded toolbox
- When: the code text of every shipped entry of kind code, model, tool or script is read
- Then: each has `run(args)` or `stage(inputs, outputs, node)`; an entry of a common function has at most 12 lines

### TC-WFM-119 – A model step is one call like the old runner's
- Verifies: REQ-WFM-058 (A-123, D-248)
- Given: `view.verdict` run as a stage with the model as an input descriptor and a scripted registered model
- When: the stage runs
- Then: exactly one model call, with the messages, schema, profile and options of the old runner, and the parsed reply is returned

### TC-WFM-120 – A tool step calls the registered function
- Verifies: REQ-WFM-058 (A-123, D-248)
- Given: `tool.web_search` run as a stage with a tool descriptor and a registered function
- When: the stage runs, then once without a descriptor
- Then: the function is called with the other inputs as keywords and the declared settings; without a descriptor `ToolMissing` is raised

### TC-WFM-121 – Descriptors are resolved only against what MIA registered
- Verifies: REQ-WFM-058 (D-248 D)
- Given: descriptors of an unknown tool, of an undeclared setting and of an unknown model profile, and their registered twins
- When: each is resolved
- Then: the refusals are `ToolMissing`, `DescriptorRefused` and `ModelMissing`, raised before anything is called; the twins resolve

### TC-WFM-122 – Independent steps keep the listed order
- Verifies: REQ-WFM-058 (A-123 P4)
- Given: all 12 listings of four steps in which S1 precedes S3 and S2 reads nothing
- When: `order_steps` builds the graph for each
- Then: the transforms come in `order_of` exactly as listed, and the graph keeps the graph rules

### TC-WFM-123 – The graph holds the given reads and writes and a few order edges
- Verifies: REQ-WFM-058 (A-123 P4)
- Given: the built graph of one listing
- When: its edges are read
- Then: the given reads and writes are edges with their `as` names; the added edges are order edges through extra data nodes with one writer each, at most steps minus one

### TC-WFM-124 – Run order, names and order inputs
- Verifies: REQ-WFM-058 (A-123 P4)
- Given: the graph of the listing S2, S1, S4, S3 run with recording stages
- When: it runs
- Then: the calls come in that order, S3 reads S1's result under its name, and no stage sees an order input

### TC-WFM-125 – The three plain pipelines convert
- Verifies: REQ-WFM-058 (A-123 P2, P3)
- Given: `plan.free@1`, `verify.single@1`, `extract.llm@1` from `library/pipelines` and the library nodes
- When: each is converted
- Then: no refusal and a valid graph; one transform per call with its node ID as toolbox ID, in pipeline order; data nodes for inputs, variables and the result, named

### TC-WFM-126 – Literals and field references
- Verifies: REQ-WFM-058 (A-123, D-252)
- Given: `verify.single@1` and `extract.llm@1`
- When: they are converted
- Then: a literal in a wire is a data node with that value, read under the parameter name; a field reference goes through a pick transform `code.pick_field` with a settings node holding the path

### TC-WFM-127 – The repair branch is one master node
- Verifies: REQ-WFM-058 (A-123 P2, P3)
- Given: `verify.computable@2`
- When: it is converted
- Then: the repair branch with its loop is one master node `control.branch` with stop `max_repetitions` 2 and the budget seconds, a settings node holding the branch JSON, the reads and writes of its variables, and the last version of `verdict` as the result

### TC-WFM-128 – Maps, branches and loops of research
- Verifies: REQ-WFM-058 (A-123 P2, P3)
- Given: `research.escalate@3`
- When: it is converted
- Then: calls are transforms in pipeline order; the map `read` is a master node `control.map` with `max_seconds` only (noted); the branch that holds maps and a loop is a master node `control.branch`; two master nodes in all

### TC-WFM-129 – What cannot be placed is refused with a reason
- Verifies: REQ-WFM-058 (A-123 P2)
- Given: a pipeline with an unknown library node, one with an unknown node kind, one with neither, and one with a plain branch
- When: each is converted
- Then: the refusals name the node and a reason and give no graph; the plain branch is a transform `control.branch` with a settings node

### TC-WFM-139 – Same ids are kept apart (was TC-WFM-130 of A-123)
- Verifies: REQ-WFM-058 (A-123)
- Given: a step and a variable of the same name, and a variable named like an order node
- When: the pipeline is converted
- Then: node ids are unique, the graph is valid and every data node has one writer, or the pipeline is refused

### TC-WFM-140 – Defaults of a node apply, a given value wins (was TC-WFM-131 of A-125 Q3)
- Verifies: REQ-WFM-058 (A-125 Q3)
- Given: `view.extract_claims` (default `guide`) and `rule.speech.no_bold` (default `rules`) run through the toolbox, with and without the parameter
- When: each runs both ways
- Then: the default of the node applies when nothing is given and a given value wins; the rule default removes only bold markup

### TC-WFM-141 – Binding a skill to a graph (was TC-WFM-132 of A-125 Q2)
- Verifies: REQ-WFM-058 (A-125 Q2)
- Given: `verify.single@1` and a pipeline with a tool step, bound to a skill with and without changes
- When: `bind_skill` is called
- Then: data nodes `descriptor.model` and `descriptor.tool.<name>` with edges `as` model and tool into the steps that need them; changes replace the options; the input graph is unchanged; rules and order are kept

### TC-WFM-142 – A converted plan runs on scripted replies (was TC-WFM-133 of A-125 Q4)
- Verifies: REQ-WFM-058 (A-125 Q4)
- Given: `plan.free@1` of `plan_question`, converted, bound and run with `stages_from_toolbox` and a scripted registered model
- When: it runs
- Then: status done, one model call with the rendered template, and the result node holds what `normalize_plan` gives

### TC-WFM-143 – An untrusted entry stops the run before the model is asked (was TC-WFM-134 of A-125 Q4)
- Verifies: REQ-WFM-058 (A-125 Q4)
- Given: the same graph with the entry `code.normalize_plan` untrusted, then trusted
- When: it is run each way
- Then: refused naming `step.norm` before the model was asked; trusted again it runs to done

## Part 2: pipeline runner (TC-RUN-030 to 035)

### TC-RUN-030 – A Stage gets inputs, outputs and settings
- Verifies: REQ-RUN-030
- Given: a Stage on a transform with two input data nodes (one renamed by `as`), one output data node and a settings node
- When: the graph is run
- Then: the Stage receives exactly three objects: the two inputs by name (the renamed one under its `as`), the output by name, and the settings value

### TC-RUN-031 – Outputs are written one by one
- Verifies: REQ-RUN-031
- Given: a Stage with two outputs, in three runs: it returns `{"outputs": {a: 1, b: 2}}`, it returns a plain value, it names an unknown output
- When: each graph is run
- Then: two different values are written; the plain value is written to both nodes; the unknown name fails the node and the result names it

### TC-RUN-032 – Plain functions run as before
- Verifies: REQ-RUN-032
- Given: a plain function and a Stage in one graph
- When: the graph is run
- Then: the plain function is called with the contents of its input data nodes as before; `TC-RUN-016` to `TC-RUN-019` are unchanged

### TC-RUN-033 – Broken wiring is refused before anything runs
- Verifies: REQ-RUN-033
- Given: a graph with two settings edges into one transform, one with two outputs of one name, and the same graph corrected
- When: each is run
- Then: for the broken ones nothing ran and the refusal names the transform; the corrected graph runs

### TC-RUN-034 – Start values come in a fixed order
- Verifies: REQ-RUN-034
- Given: a Stage with `prepare` and a data node that has a graph value, in three runs (graph value only; with prepare; with a value given to the run)
- When: each is run
- Then: the Stage gets the run value, else the prepare value, else the graph value, else nothing; `prepare` ran once before the Stage

### TC-RUN-035 – An order edge orders and gives no input
- Verifies: REQ-RUN-035
- Given: a transform with an order edge from a data node written by another transform
- When: the graph is run
- Then: the writer runs first and the Stage's inputs hold no entry for the order node
