# A-124: the three-argument call of the graph runner (T-CV-03a, G-V2.CONVERT, proposal for the owner's review)

Status: **proposed, not applied, not reviewed**. Written 2026-11-15 after D-248 (the owner's revision of the transform interface). Reserved range of CONVERT: A-120 to A-129, REQ-RUN-030 to 039, TC-RUN-030 to 039, TR-CONVERT-. Nothing of the verified REQ-RUN-016 to 019, `graph_run.py` behaviour or `tests/acceptance/test_graph_run.py` changes: the new call is additive.

## Why additive
D-248 C agreed that the runner calls `nodes[id](inputs, outputs, node)`, old one-argument functions wrapped. The simplest wrapper is explicit: a function that wants the new call is handed to the runner as `Stage(function)`; every other callable is called as today (`function({input data node id: value})`, one value written to every output node). So the tested behaviour of REQ-RUN-016 to 019 stays exactly as verified, no protected test is amended, and old callers need no change.

## The conventions (one place for all configuration: the `value` of a data node)
- **inputs:** `{name: value}` of the input data nodes of the transform. The name is the `as` field of the edge from the data node to the transform; without `as`, the data node's ID (D-248 E).
- **outputs:** `{name: value}` of the output data nodes at the start of the run (an artifact store or a model descriptor is such a node; an ordinary result node has value `None`). The name is the `as` field of the edge from the transform to the data node, else the node's ID.
- **node:** the settings of the transform: the `value` (an object) of the one input data node whose edge carries `role: "settings"`; `{}` when there is none; more than one is refused as a broken graph before any node runs. Edges are open JSON objects (`graph_tables.py`), so `as` and `role` need no change of IF-301.
- **Tools and models** are descriptors in `value`: `{"tool": "<name>", "settings": {...}}` and `{"model": "<profile>", "options": {...}}`. The runner passes them like any value; the common module resolves them (D-248 D).
- **result of a Stage:** an object with the key `outputs` holding `{output name: value}`; each value is written to the output node of that name (an unknown name fails the node). Any other return value is written to every output node, as today. (An object that has other keys as well as `outputs` is an ordinary value.)

## Requirements (new, EARS, for REQ-RUN-030 to 033 in the Pipeline runner node)
| ID | Text | Acceptance criterion |
|---|---|---|
| REQ-RUN-030 | When a transform or master node is run as a Stage, the Pipeline runner shall hand it the values of its input data nodes by name, the values of its output data nodes by name and the settings object of its settings node. | AC-31: a Stage with two inputs (one renamed by the edge field `as`), one output and a settings node receives exactly those three objects (exact) |
| REQ-RUN-031 | When a Stage returns an object with an `outputs` entry, the Pipeline runner shall write each value to the output data node of that name; otherwise it shall write the one result to every output data node. | AC-31: a Stage with two outputs gets two different values written; a Stage returning a plain value writes it to both; an unknown output name fails the node and the run result names it (exact) |
| REQ-RUN-032 | While a callable is not a Stage, the Pipeline runner shall call it as before with the values of its input data nodes by data node ID. | AC-31: the checks TC-RUN-016 to 019 give the same results with the new code (exact; they stay as they are) |
| REQ-RUN-033 | If a graph has more than one settings edge into one transform, or a Stage's output name appears twice, then the Pipeline runner shall refuse the run before any node ran, naming the node. | AC-32: nothing ran, the refusal names the node (exact), with the accepted twin that runs |
The refusal of an unregistered tool or model (D-248 D) is a rule of the common module, checked when a Stage resolves a descriptor, and before any node runs: see TC-WFM-119 and 120 (revised) and a new check there; the runner itself does not know tools.

## Checks (new file `tests/acceptance/test_graph_run_stages.py`, red first, protected folder: the owner's go)
TC-RUN-030 (inputs, renamed input, outputs, settings), TC-RUN-031 (per-output writes, plain value to all, unknown name), TC-RUN-032 (old callables and the four old checks unchanged: the new file also runs a plain function next to a Stage), TC-RUN-033 (two settings edges, double output name, accepted twin). Stage stub in `graph_run.py` (not protected): `Stage` class, `GraphRunner.run` unchanged until T-CV-03a.

## Open points for the owner (one at a time)
- **R1** additive `Stage` wrapper instead of an amendment of the old call (this note's premise).
- **R2** the conventions above: `as` names inputs and outputs, `role: "settings"` marks the settings edge, all configuration in `value`.
- **R3** the result form `{"outputs": {...}}` and the rule that anything else goes to every output node.
- **R4** the four new requirements and the refusals of REQ-RUN-033; the tool and model whitelist stays in the common module.
- **R5** the new checks TC-RUN-030 to 033 in a new test file.
