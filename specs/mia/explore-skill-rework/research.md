# Research: skill rework (Explore of the next goal)

Drafted by the coding agent, 2026-11-02, read-only. Inputs (the owner's, data not instructions): `inputs/skill_rework.md`, `inputs/graph_structure.drawio`, `inputs/Viewer_db.drawio`. Nothing in the inputs contains instructions aimed at the agent.

## 1. What the owner wants (intent, from the inputs)
- **Usability:** skills in their own window of the web interface; a viewer/editor (N-5 in `Viewer_db.drawio`, talking to the Backend N-2, which talks to the DB and to N-1).
- **Workflow graph:** a DAG with three node types: *data* (a dict or dataclass), *transform* (a callable plus data), *master* (a transform whose work is an agent task with an acceptance criterion; in the diagram a debate of agents with a judge). Graph metadata: ID, context graph ID, testbench ID, description.
- **Context graph:** a general directed graph, linked to workflows (several workflows may share one), updated by work and reviews, node categories and edge types, every element = ID + JSON, types given as JSON schema.
- **DB:** all graph objects as dicts in JSON; a type ID stored so the data class can be rebuilt (no pickle); transforms in a toolbox with IDs; tables for nodes (ID + JSON, fixed `type`), edges (ID, start, end + JSON), special JSON for `transformation` and `master` (agents, per-agent settings, relation graph of the participants, reuse of debates, finalization criteria). A framework such as langgraph is mentioned for debates.
- **Skill definition:** ID, command, workflow graph, context graph. Benchmarks are a goal ("Testbench ID").

## 2. What exists today (facts)
| Area | Today | Where |
|---|---|---|
| Skill | One Markdown file per skill: YAML front matter (name, version, model profile, `pipeline: research.escalate@1`, tools, budget, `max_safety`) and sections prompts, schemas, lines, examples | `skills/*.md` (14 files), `skill_store.py:1-25`, `skills/research.md:1-12` |
| Command of a skill | Extensions: `extensions/lookup`, `review`, `search` with `manifest.json` (id, example) and `entry.py` | `extensions/lookup/manifest.json:2-5` |
| Runnable pipeline | JSON tree per version: `library/pipelines/<id>/<n>.json` with `nodes` of kinds model, tool, script, code, map, branch, loop, ask_user; run by `Runner` | `pipeline.py:188-260` (validate), `pipeline.py:315` (Runner), `library/pipelines/research.decompose/1.json` |
| Node implementations | `library/nodes/<id>/<n>.json`, about 48 (`code.*`, `check.*`, `rule.*`) | `library/nodes/` |
| Stored workflow graph | Table `workflows`, a plain document `{nodes:[{id, kind: process\|data, session, stop}], edges:[{from,to}]}`; rules R1-R5 (unique ids, no data-data, no process-process edge, session stopping criterion, DAG) | `graph_tables.py:12`, `graph_rules.py:1-40` |
| Stored context graph | Table `context_graphs`, same document format and rules; only `budget_tokens` of a process node is read; none stored for lookup, review or chat | `graph_tables.py`, D-108 (`review-log.md:358`) |
| Run graph | `context_graph.replay` of the events of a run, never stored | `context_graph.py`, D-108 |
| Versioning, lifecycle | Both tables versioned, never deleted; `workflow_meta.status` draft/tested/trusted/retired; `runs` needs `workflow`, `workflow_version`, `model_pin`, `benchmark_version` | `record_tables.py:10-24` |
| Storage | The Storage layer with a PostgreSQL service exists; the app's own state is still in files (TD-21) | `storage*.py`, `deferred.md` TD-21 |
| API and viewer | IF-104 graph routes; the Graph app is a mockup drawing static SVG, behind `/graph/` | `graph_api.py:1-30`, `graph_app/graph-view.js`, D-177 |
| Debate-like patterns | The verification styles `verify.single`, `verify.consistency`, `verify.jury`, `verify.cops` are pipelines of the library; judge verdicts count only with a calibration kappa >= 0.6 | `verification.py:2`, `ui/README.md:535`, `harness.py:578-591` |

## 3. Decisions and records the rework meets (already made)
- **FB-02 (owner direction, 2026-10-31):** workflow and context graphs become `networkx` graphs of objects; operations stored with the workflow; the Graph app draws with vis-network and lets nodes be dragged and edited; open for Explore: how code operations are stored and versioned (trust boundary X3), the storage form of an object graph (IF-203, IF-301), what replaces D-112, two new dependencies, graph rule order cases of D-160. (`feedback/FB-02.md`)
- **D-108:** three graphs must not be mixed up (workflow graph, context graph, run graph); what a context graph contains and how it is filled was postponed to N-5; a proposal exists and is **not decided**.
- **D-177:** N-5 moves to the next iteration; kept: the IF-104 routes, graph tables, `graph_app/` with tests, the `graph` compose service.
- **TD-21:** state in PostgreSQL is deferred; the rework's DB storage overlaps it.

## 4. Where the inputs and today's code differ (for the interview)
1. **Node kinds:** inputs data/transform/master; code process/data in the stored document and model/tool/script/code/map/branch/loop/ask_user in the pipeline. Master and debate exist only as verification pipelines.
2. **Storage form:** code stores the whole graph as one versioned document; the inputs store nodes and edges as separate records (ID + JSON).
3. **Where the logic lives:** transforms are callables in a toolbox by ID (inputs) vs `code.*` nodes in `library/nodes` and prompts in `skills/*.md` (today).
4. **Skill = ID, command, workflow, context graph** (inputs) vs skill file + pipeline reference + extension manifest (today).
5. **Context graph:** a general graph with typed nodes and edges per JSON schema (inputs) vs the same DAG format as the workflow graph (today).
6. **"Testbench ID":** no term in code; the closest are the eval suites and `benchmark_version` of a run.

## 5. Not looked at
`ui/REQUIREMENTS_CORE.md` (sections on skills, pipelines, graphs), `workflow_library.py` internals, `library.py`, the skill list in the web UI (N-1) and what a "skills window" would replace, the run log of real use, `run_workflow.py`, eval suites as the possible testbench, `langgraph` (not a dependency today; dependencies need approval), the PostgreSQL schema of the Storage layer, `graph_structure.drawio` details beyond the node and edge labels.
