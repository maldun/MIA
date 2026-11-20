# Research: how graphs are stored today (G-V4.GRAPHSTORE, Explore)

Read-only, 2026-11-20, on `goal/v4` (= master `18d80348`). Scope: who writes and reads which graph form, and what data exists. Not examined: the web frontend, `graph_app/`, PostgreSQL contents (only code), the old runner `pipeline.py`, `skill_store.py` internals.

## Facts
| # | Fact | Evidence |
|---|---|---|
| F1 | The Storage layer (IF-102) has two backends, files and PostgreSQL, that behave the same; copy and migration between them exist (`copy_records`, library export/seed, `migrate.py`) and have tests (`test_storage_copy*.py`, `test_migrate.py`) | `storage.py:1-12`, `storage_copy.py:1-18`, `migrate.py:42,67` |
| F2 | The **record form** (`graph_nodes`, `graph_edges`, `graphs`, `context_nodes`, `context_edges`) is written only by `GraphModel.save_graph` and read by `GraphModel.read_graph`. No production module calls `GraphModel`; only tests do | `graph_model.py:140-170`; grep of non-test code finds no caller |
| F3 | The **document form** (tables `workflows`, `context_graphs`, one `{nodes, edges}` document per version) is what production uses: `WorkflowLibrary`, `run_workflow`, the review extension, snapshots, the graph API, the library export/seed | `workflow_library.py:19,105,260`, `run_workflow.py:74-202`, `extensions/review/review_entry.py:37`, `snapshot_store.py:16`, `storage_copy.py:18` |
| F4 | Stored data of the running app: one workflow, `data/db/workflows/review.json` (1 record, versions list). No `graph_*`, `context_*` or `graphs` records exist | `data/db` listing |
| F5 | **A converted skill's graph is not stored at all.** `run_converted` builds the graph from the pipeline JSON of `library/pipelines/` (25 files) and the nodes of `library/nodes/` at every call and runs it; the run uses a throw-away `Storage(FileBackend(tmpdir))` only for the toolbox | `skill_converter.py:85-122` |
| F6 | `run_workflow.workflow_of_skill` derives a document-form workflow from a skill's graph (D-112 "reference + sync"); the document is a view of the pipeline, not the source of the run | `run_workflow.py:172-202` |
| F7 | Context graphs: `context_graph.py` and `WorkflowLibrary` read the document form (`context_graphs`) as a template | `workflow_library.py:260` |
| F8 | `to_document` / `from_document` convert between the forms; a graph with a master node is `not_representable` in the document form | `graph_tables.py:347-364` |
| F9 | Conversion evidence for 5 skills sits in `data/conversion/*.json` (eval verdicts, not graphs) | `data/conversion/` |

## What this means for the goal
1. The draft's premise ("two forms in the same backend, no migration") is right for the schema but **the record form has no production data**: migration of existing graphs is one document (`review`) plus whatever the owner keeps elsewhere. The real work is to decide what the stored truth of a *skill's* graph is: the pipeline JSON (F5) or a stored graph.
2. If the stored graph becomes the truth for execution, the pipeline JSON in `library/pipelines/` and the converter become an import path (pipeline to graph, once) instead of a per-run step. That is a change to FR-6 behaviour (versions, trust, snapshots, F6/D-112) and touches GRAPHAPI.
3. Files and database are already interchangeable at the record level (F1); what has to be shown is the same for graph versions and the pinned node versions of a `graphs` header (a graph is spread over three tables and must move together).

## Open questions for the owner
See the questionnaire in the session; answers go to `review-log.md` (D-361 and following).
