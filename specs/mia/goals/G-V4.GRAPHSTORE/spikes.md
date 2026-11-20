# Spike: do converted skill graphs survive the record form and both backends? (G-V4.GRAPHSTORE)

Throwaway, 2026-11-20. Code in the session scratchpad, not in the repo (nothing to bin). Cases are the 15 skills of `skills/` with a pipeline, converted as `run_converted` does (`pipeline_graph.convert` + `bind_skill`). Not eval cases; no model used. Code state: `goal/v4` = master `18d80348`.

| Question | Setup | Result |
|---|---|---|
| Does a converted graph save and read back identical through `GraphModel` on the file backend? | 15 graphs, 3 to 54 nodes | 15 of 15 identical |
| Same on PostgreSQL 16 (podman, tmpfs), then copied database to files with `copy_records`? | same 15 graphs | identical on the database, identical after the copy, version lists equal |
| Does a copy files to files keep them identical? | `copy_records` on `graph_nodes`, `graph_edges`, `graphs` | 15 of 15 identical |
| Do the graphs hold master nodes? | node data of all 154 nodes | none (the 15 converted skills have no master node; the document form could hold them all) |
| Are node record IDs unique across graphs? | the 107 distinct node ids | **13 ids occur in more than one graph, 4 with different content** (`descriptor.model`, `step.write`, `step.rules`, ...) |

## What it means
- Storing, reading and moving graphs between files and database works on real data. No loss found.
- **Finding S1:** the converter names records by their role (`step.write`, `descriptor.model`), and a node record is stored under its own ID (A-92, REQ-GTB-021). Two graphs with `step.write` of different content write versions of the same record. Reads stay correct because each graph header pins the version it uses, but the history of a node mixes graphs and an edit in the app would look like a change to another graph's node. Fix options: record IDs prefixed with the graph ID (`<graph>/step.write`), or content-identical nodes stay shared and different ones get their own ID. It needs a decision in Plan (IF-301 / A-92 touch).
- Not covered: master nodes (none exist in the converted skills), the context-graph tables, snapshots, graphs of the document form, a spike of the migration tool.
