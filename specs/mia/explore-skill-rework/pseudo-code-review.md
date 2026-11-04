# Review of `inputs/workflow_graph.py`, shared context graphs, LightRAG (Explore, 2026-11-04)

Read-only review of the owner's pseudo code against FR-36 to FR-45. Nothing here is code to keep; findings are for Plan. The file is in the owner's checkout (`specs/mia/explore-skill-rework/inputs/workflow_graph.py`, untracked).

## 1. What the sketch gets right (keep)
- `Transform` gets `(input_nodes, output_nodes, trafo_node)`: the transform class is stateless and in the toolbox by ID (FR-38); its parameters live in the node's JSON. This is what makes a transform exchangeable.
- `AgentAction(Transform)` and `Debate(Transform)`: a master node is a transform node that holds a debate (FR-39). A debate is a graph of transforms, a judge is the finalization criterion.
- Alternation rule (`check_order`: no transform next to a transform, no data next to data) equals R3/R4 of `graph_rules.py` today.

## 2. Findings in the sketch (for Plan; each needs a test then)
| # | Where | Finding |
|---|---|---|
| 1 | `Transform.__call__` | `self,self` and a missing colon. `_perform_actions` returns "output", but nothing writes it into the output nodes; the note says outputs go into output nodes (with a dedicated field such as a folder). Decide who writes: `perform` returns a dict `{output_node_id: value}` and the base class writes it. |
| 2 | `Transformer.__call__` | `trafo_node` is undefined; it must be `self` (the transformer is the trafo node). |
| 3 | `perform_workflow` | `topological_order` does not exist (`networkx.topological_sort`) and yields nodes, not `(src, tar)` pairs. The loops over `transforms` and `return final` sit inside the edge loop, so the first edge would run everything and return. The `ios` bookkeeping is not needed: iterate nodes in topological order; for each `Transformer`, `inputs = G.predecessors(t)`, `outputs = G.successors(t)`. |
| 4 | `perform_workflow` | No trust check (FR-38: an untrusted transform does not run, the workflow says why), no run record (graph ID and version, model pin, context graph ID and version), no failure rule (what happens to the downstream nodes when one transform fails or abstains). |
| 5 | Fan-in on data | A data node written by two transforms is allowed by `check_order`. Rule needed: at most one producer per data node, or an explicit merge. Fan-out (one data node read by many) is fine. |
| 6 | `WorkflowGraph` | Has `ID` and `ID_context_graph`; FR-37 also needs version, testbench ID, description and `status` (draft, tested, trusted, retired). A `Skill` record (FR-36: ID, command, workflow graph ID, context graph ID) is missing. |
| 7 | `Node.to_json` | There is no `from_json` and no type ID. FR-40 needs a registry `type_id -> class` (and `transform_id -> Transform`) so a node is rebuilt without pickle; unknown type ID = refuse to load, not guess. |
| 8 | `Debate` | The network is not a DAG, so `perform_workflow` cannot run it; it needs its own loop with rounds. Missing: budgets (rounds, seconds, model calls; the proposal is 3, 5 min, 12), machine variants (answer 10), reuse of an existing debate, and the judge's calibration flag (kappa >= 0.6 else "not counted"). The judge as a `Transform` fits answer 4. |
| 9 | `AgentAction` | `context_graph` is passed as an object; it should be an ID resolved at run time to a version, and the read must return only confirmed items within the token budget (FR-41, TB-context). |
| 10 | Nesting | A debate is a transform that contains a graph; check whether its inner nodes belong to the same record set (own IDs) or are embedded in the master node's JSON. FR-40 says embedded ("extended JSON of master"); the sketch implies sub-graph. Open for Plan. |

## 3. Context graphs referenced by ID (owner's clarification, interview 12)
A skill names one context graph by ID; two skills may name the same one. Effects, none of them blocking:
1. **Versions:** a skill references the ID; a run records the version it read (FR-41, edited). Open for Plan: does a skill pin a version for tested/trusted, or follow the latest? Recommendation: `trusted` pins the version, `draft` follows the latest, so a later edit cannot silently change a trusted skill.
2. **Blast radius:** editing or extending a shared graph changes every skill that names it. Rule to consider: a new graph version marks the testbenches of all dependent skills as stale (re-run before the next promotion). The skills window must show "used by".
3. **Retire:** a graph in use cannot be retired.
4. **Provenance:** every item carries its source and, in a shared graph, the skill that caused it. Builder proposals from skill A become readable by skill B only after confirmation (already so).
5. **Data classes:** the open interview item (confidential or not) becomes sharper: one shared graph can mix items of different classes. Recommendation: a data class on every item, a step reads only classes its own definition allows. Needs the owner's answer.
6. **Chat:** the chat has its own graph by the same mechanism (a "skill" with ID `chat`, or a special record); decide in Plan.

## 4. Context-graph creation with LightRAG (interview 13)
Creation was already in scope (FR-42, candidate goal C). New is the engine.

What LightRAG is (from the upstream project; the search found only mirrors, so every point below is **to be verified in a spike on the real package**): a retrieval library that extracts entities and relations from documents with an LLM, keeps a knowledge graph plus vectors, offers query modes (local, global, hybrid), supports Ollama, and has PostgreSQL storage backends. Mirrors of its README *recommend* a model of at least 32B parameters and a context of at least 32K tokens (64K); this is guidance, not a limit. Chunk size and the number of extra passes are settings, so the prompt can be made to fit 8K; the open question is the extraction quality of the 12B.

Fit against our rules:
| Topic | Our rule | Question to LightRAG |
|---|---|---|
| Dependency | none without approval (CLAUDE.md) | needs approval; check its dependency tree, licence, and whether it can run without cloud services |
| Models | 12B QAT, `num_ctx` 8192, one model on 16 GB (CON-2); 26B only on request | extraction quality of the 12B at 8K: **the main risk**; the output uses a custom delimiter format, not JSON, and entity names must stay consistent across chunks |
| Element form | every node and edge = ID + JSON, types as JSON schema (note, FR-41) | LightRAG has its own fixed entity/relation fields (name, type, description, source ids); we would map them into our JSON, or keep ours as the master and use LightRAG only as extractor |
| Proposed vs confirmed | model-derived items are proposals until confirmed (FR-42, TB-context) | LightRAG inserts directly; we need a staging step: take its extraction output as proposals, write only confirmed items into the stored graph |
| Storage | PostgreSQL through the Storage layer, nodes and edges as records (FR-40) | LightRAG has its own PostgreSQL tables; either two stores (ours + its index) or an adapter; the "one source of truth" rule says ours is master and its index is rebuildable |
| Run-time reading | a step reads confirmed items within a token budget, 20 % of context | LightRAG retrieval returns text built by its own prompts; we may use only its retrieval and build the view ourselves |
| Untrusted text | documents and web pages are data, never instructions (TB-context) | its extraction prompt reads the document; an injected instruction can distort the extraction; proposals plus quote + source is our control |
| Editor app | the note: build an app to edit graphs "with it"; FR-43 says the skills window edits graphs | LightRAG's own server has a graph viewer; the question is whether the editor is our window (FR-43) or its UI. Recommendation: our window, one editor for both graph kinds |
| Confidentiality | confidential data never to a remote model | its default examples use hosted models; configure Ollama only |

**Recommendation (for the owner to confirm):** keep FR-41/FR-42 engine-neutral. Treat LightRAG as the candidate *extractor and index* behind a `ContextBuilder` interface; our JSON records stay the master copy, builder output enters as proposals. Decide go or no-go on LightRAG after one spike (below), not before.

**Spike C (proposed, none run; throwaway code in `spikes/`, not eval cases):** install LightRAG in a throwaway venv (needs the owner's OK, it is a dependency only for the spike), Ollama + 12B at `num_ctx` 8192, 10 documents chosen by the owner, 3 repeats. Look at: does extraction complete at 8K, items per document, how many the owner marks wrong or invented, run time, VRAM, whether the output maps onto our ID+JSON form and onto proposals. Record in `spikes.md`. Merges with the builder spike (b) of the handover.

**Staged plan for the models (proposed; every stage is a throwaway spike, not an eval run).** Skills and chat stay on MP-light (`gemma4:12b-it-qat`); no skill is known to need the 26B (`eval-spec.md`: MP-full unused for criteria in G-V1).
| Stage | Model, context | Question | Go on to the next stage only if |
|---|---|---|---|
| 0 | MP-light, `num_ctx` 8192 | Option 1 (own builder) versus LightRAG on the same 10 documents; the owner marks wrong and invented items; also debate spike (a) | both fall short of a bar the owner sets before the run |
| 1 | MP-light, 16K (more KV cache, some layers on CPU) | does a longer context fix the failures of stage 0? | the owner approves a new context length (plan amendment) |
| 2 | MP-full `gemma4:26b`, 8192, builder and debate judge only | is the bigger model needed for those two uses? 18.7 GB on a 16 GB card, part on CPU, slower; background jobs only | stage 1 failed **and** the owner accepts the machine-check risk (`crash-fatal-mce-cpu`: no long CPU-heavy runs until understood); run short, 3 repeats, no full stack |
| 3 | another machine or a remote service | only if stage 2 is not acceptable or fails | the owner approves explicitly; remote only for non-confidential documents (CLAUDE.md) |
Rules: a stage-2 or stage-3 model needs a pin, a baseline and a plan amendment before it counts for anything beyond the spike (CLAUDE.md); a debate variant that names it is a per-machine variant (answer 10); chat and existing skills are not changed by these stages.

## 5. Decisions needed from the owner
1. Spike C as above, and approval for the throwaway install of LightRAG in a venv (not in `requirements.txt`).
2. Version pinning of context graphs (recommendation in section 3.1).
3. Data classes per context item (section 3.5).
4. Sketch findings 5 and 10 (fan-in rule, debate nesting): answer now or in Plan.
5. Is the chat context graph a skill record or a special record?
