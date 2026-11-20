# Review: how general is the graph editor? (owner's remark of 2026-11-21)

**Remark of the owner:** the editor should ultimately edit both context graphs and workflow graphs, with little difference by design. A context graph may have more kinds of nodes, but the basic functions (add a node, edit the entries of a node, make connections) stay the same. The generality of the editor is reviewed before more is planned on it.

Written by the agent from the prototype (branch `prototype/g-v4`, round 03) and the specs of EDIT, CONTEXT, VIEW, RULES and REPLAY. Status: for the owner's decision; nothing here changes an approved spec.

## 1. What is already general
| Part | Why it is general |
|---|---|
| Working copy, undo and redo, keep as a new version, restore, conflicts (`undo-stack.js`, keep and restore routes) | they work on `{nodes, edges}` and never look at what a node is |
| Edit log, playback and comparison (`graph_changes.py`, `change-log.js`, `replay.js`, `compare.js`) | entries are add, remove or change of a step or connection with the content before and after; no kind appears in them |
| Storage and versions (CORE, round 03) | a context graph is stored through the same save path, by `kind` of the graph |
| Add and remove a connection, copy of a step (as content) | they only need the IDs and the content |

## 2. Where the prototype assumes a workflow graph
| Place | The assumption | What a general editor does instead |
|---|---|---|
| `edit-model.js` `START`, `KNOWN`, `formFor`, `applyForm` | the node types are data, processing and loop-controlling, each with hard-coded fields (`value`, `parameters`, `toolbox_id`, `stop`) | node types and their fields come from a **description of the graph kind**; the form and its checks are built from it |
| `edit-panel.js` `toolPicker` | a node has a tool from the toolbox | a field can be of the kind "choose from a list" (tools for processing steps, categories or other lists for context nodes); the list is part of the description |
| `step-marks.js` `groupOf`, `KIND_NAMES`, trust marks | three shapes and the trust and lifecycle marks | shape, words and marks per node type come from the description; trust marks only where the type has a tool |
| `graph_rules_proto.py` (the check route and the keep route) | the eight workflow rules, including "no two data steps adjacent" and the kinds of step | one **rule set per graph kind**: the workflow set of eight; for a context graph its own (identity, ends, category schema, budgets; FR-7 extended, D-369) |
| `graph_proto_app.py` `full_graph`, `keep_graph`, `check_graph` | a graph is a workflow graph: the header fields are those of a workflow, `kind` is dropped | the route follows the `kind` of the stored graph and asks its rule set |
| `graph_proto_app.py` `steps_info`, `/api/v2/toolbox` | trust and lifecycle from the toolbox for processing and loop-controlling steps | information about a node comes from its type's description (a tool, a category, nothing) |
| the connection form (`role`: settings, order, code) | roles of workflow connections | the description of the kind lists the connection fields (workflow: role and name; context: the relation) |
| Run, stand-in steps, missing inputs | workflow only | stays workflow-only by nature (a context graph is not run) |

## 3. Proposed design: one editor, a description per graph kind
The editor core knows nodes, connections, entries, the working copy and the record of changes. Everything that differs between kinds is data in a **graph profile**:
- the **node types**: ID, name, shape, marks, and a list of **fields** (name, label, kind of input: text, number, JSON, choice from a list; limits; start value);
- the **connection fields** (workflow: `role`, `as`; context: for example `relation`);
- the **rule set** of the kind (an ordered list, every broken rule named, as FR-63);
- **lists** a choice field draws from (the toolbox for a processing step; the categories for a context node).

Two profiles to begin with: **workflow** (the fixed list of IF-301: data, processing, loop-controlling) and **context** (the node types are categories with their schemas; where these come from is the builder's subject, goal C). A new kind of graph later is a new profile, not a new editor.

## 4. What this changes in the plan
| Spec | Change proposed (for the owner to decide; nothing is edited without that) |
|---|---|
| EDIT, FR-92 ("a form for the known fields of each kind of step: data, processing, loop-controlling") | wording: "each type of node of the graph's kind"; the three workflow types stay as the first profile |
| EDIT scope | EDIT is the general editor with the **workflow profile and a minimal context profile** (so generality is proven early); the prototype round for EDIT shows both kinds in one editor |
| CONTEXT (OC-1, REQ-GA-006) | shrinks to the context profile in full (categories, their schemas, budgets), the run's context graph view (FR-97) and the context rule set; the editing functions are EDIT's |
| RULES, FR-63 ("one set of eight rules") | "one rule set **per graph kind**, in one fixed order"; the eight are the workflow set; the context set extends the one rule set (D-369) |
| VIEW, FR-50 (kinds, trust and lifecycle at a glance) | "the type of each node by shape and words, and for nodes with a tool its trust and lifecycle"; the three shapes are the workflow profile |
| REPLAY | none: already general |
| CORE | none beyond round 03 (both kinds are stored) |

## 5. Decided by the owner (2026-11-21, D-403)
1. **Principle:** one editor, a profile per graph kind, **workflow first, context later**: the design is general from the start; the context profile is built when CONTEXT is planned. (This replaces the proposal in section 4 that EDIT's prototype round shows both kinds.)
2. **Context node types:** a fixed list in the context profile for now, the builder's categories later (goal C).
3. **Copy of a step (FR-94):** only within the same kind of graph.
4. **Gate:** the plans of EDIT, RULES and VIEW follow the profile design and wait for the amendments below; CORE goes on.

## 6. Proposed amendments of the top-level specs (not applied; the owner approves each)
| Spec | Now | Proposed |
|---|---|---|
| EDIT FR-92 | "…the known fields of each kind of step as a form with checks…" Outcome: "Given a step of each kind (data, processing, loop-controlling)…" | "…the known fields of each type of node of the graph's kind as a form with checks, and any other field as editable text." Outcome: "Given a node of each type of a workflow graph (data, processing, loop-controlling), when the owner opens it for change, then…" (rest unchanged); the profile of a further kind adds its types later |
| RULES FR-63 | "…one set of eight graph rules to a graph wherever it is checked…" | "…one set of graph rules **for the kind of the graph** wherever it is checked, in the same fixed order…"; the outcome keeps the eight rules of workflow graphs and says that the rule set of a context graph is written in the same place (its content is CONTEXT's, FR-75) |
| VIEW FR-50 | "…the kind of each step, and the trust and lifecycle state of each processing step…" | "…the type of each node, and for a node that uses a tool its trust and lifecycle state…"; the outcome keeps the three workflow types as the example |
| CONTEXT FR-75 | "…with the structural rules of workflow graphs and the rules for categories and budgets" | unchanged; **note:** which of the workflow rules are structural for a context graph (identity, ends and duplicates are; order and the data/processing alternation probably are not) is decided in CONTEXT's plan; the prototype round 03 assumed identity and ends only (ASM-4) |
| EDIT scope and CONTEXT scope | EDIT: workflow editor; CONTEXT: edit context graphs and view a run's graph | EDIT: the general editor (core and workflow profile); CONTEXT: the context profile, its rule set, the run view; no change of the requirements' text |

## 7. Still open
The wording of the amendments in section 6 (approve, change or leave).

1. Is the principle right: one editor, a profile per kind, workflow and context as the first two?
2. Where do the node types and field schemas of a context graph come from: the categories of the builder (goal C), or a fixed list in the profile until then?
3. May a step be copied between graphs of different kinds (FR-94)?
4. What does the review gate: the plan of EDIT only, the plans of RULES, VIEW and CORE as well, or only the EDIT prototype round?

## 8. The kind flag (owner's addition, 2026-11-21)
**Remark of the owner:** like the copy rule, the structural checks differ between context graphs and workflow graphs (and later other kinds); there should be a flag for the kind. The editor stays mostly generic, but the flag steers the things that must stay consistent: the checks, whether a copy is allowed, and so on.

**What exists:** the stored header of every graph already has a field `kind` (`workflow` or `context`; the schema is an enumeration of these two, IF-301 v2). The prototype stores and reads it (round 03) and reads the table set from it. Nothing else uses it yet: the check route, the keep route and the copy route treat every graph as a workflow graph.

**Proposal:** the `kind` of the header is the flag. A **kind** is a named entry (a registry, one place in the code and the spec) that says, for graphs of that kind:
| What depends on the flag | Today (prototype) | With the flag |
|---|---|---|
| the structural rule set (check while editing, keep, save, run) | the eight workflow rules for every graph | the rule set of the kind: workflow = the eight; context = its own (CONTEXT, FR-75); a further kind brings its own |
| the member tables of the store | by kind (round 03) | unchanged |
| the editor profile (node types, fields, connection fields, choice lists) | hard-coded workflow | the profile of the kind |
| the copy of a step (FR-94) | not checked | refused when the kinds differ, naming both kinds |
| marks and shapes in the viewer and the list | workflow shapes only | from the profile of the kind; the list shows the kind |
| running | any graph | only a kind that says it can run (workflow); a run of another kind is refused before any step |
| comparison and playback | kind-free | unchanged (compare only graphs of the same kind: a comparison across kinds is refused) |
| the stored enumeration of kinds (IF-301 v2) | two fixed values | the registry is the list; a new kind is an amendment of IF-301 with its tables |

**Open:** what happens to a graph whose kind is not in the registry (an older program opening a newer store).
