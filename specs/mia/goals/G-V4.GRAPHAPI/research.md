# Research: how the runner and the graph rules work today (G-V4.GRAPHAPI, Explore)

Read-only, 2026-11-20, `goal/v4` = master `18d80348` plus the goal records. Not examined: `pipeline.py` (the old runner), `control_flow.py`, `graph_api.py`, the web side.

## Facts
| # | Fact | Evidence |
|---|---|---|
| F1 | The runner (`GraphRunner.run`) takes a plain dict `{nodes, edges}`; it finds a cycle with its own search, orders with `order_of`, checks trust per transform before the first runs, checks wiring, then runs stages in order | `graph_run.py:36-80` |
| F2 | Node type, `stop`, edge `role` (`settings`, `order`) and `as` all sit in the `data` dicts of nodes and edges; the runner reads them from there | `graph_run.py:37,85-100` |
| F3 | **Two sets of graph rules exist**: `graph_rules.py` (document form: kinds `process`/`data`, `session`, R1 to R5, first broken rule per edge) and `graph_model.check_graph` (record form: types `data`/`transform`/`master`, stop with `max_repetitions`/`max_seconds`, rule order fixed). They differ in names and in the order they report | `graph_rules.py:1-30`, `graph_model.py:84-123` |
| F4 | The run does not run the graph rules; it checks only unknown edges and cycles itself ("the writers of IF-102 do not run the graph rules, D-262") | `graph_run.py:38-41` |
| F5 | A master node runs once like a transform; its stop criterion is stored and unused until debates (FR-39) | `graph_run.py:63-64` |
| F6 | Several edges between the same two nodes are not refused by any rule (FB-02/D-160) | `graph_model.py:84-123` |
| F7 | `networkx` is not used in production code; D-187 approved it, `requirements.txt` changes in Implement | `grep` of non-test code |
| F8 | Code in a graph has no precedent in the stored data: transform nodes carry a `toolbox_id`, the toolbox entry names the function, and trust is a property of the toolbox entry. THR-009 (an edit changes what runs) and THR-011 (an imported transform does harm) are the nearest threats; `TB-code` (generated script, sandbox, no network) is the nearest boundary | `threat-model.md:93,116`, `library/nodes/check.script/1.json:74` |

## Proposed threat entry (for Plan, not written into `threat-model.md`)
**THR-013 candidate: code text stored in a graph.** A code snippet is a data node; a transform reaches it through the toolbox reference (for example a `python-exec` tool). Risks: a snippet edited in the graph app changes what runs (THR-009); a snippet imported from outside (THR-011); a model-written snippet. Candidate mitigations for the owner to accept: the code text is data until a trusted toolbox tool runs it in the sandbox (`TB-code`); only the owner raises trust; a change of a snippet drops the transform back to untrusted; the run record names the snippet version. Red-team cases to be written by Plan with the owner.
