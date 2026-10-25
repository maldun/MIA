# IF-104 – Workflow and graph API (REST with the backend's session), v0

Owner (provider): N-2 Backend (child N-2.1, workflow logic in N-2.3)   Consumers: N-5 Graph app   Decided by: N-0   Mock complexity: 2 (fake REST server on the storage mock)   Suite: `tests/acceptance/contract/test_if_104_graph_api.py`

Added by amendment 7 (D-47): the graph app has no database access and no login of its own. The adapter methods below stand for HTTP routes (`POST /api/login`, `GET /api/{kind}`, `GET/PUT /api/{kind}/{id}`, `GET /api/{kind}/{id}/history`, `GET /api/{kind}/{id}/diff?a&b`, `POST /api/{kind}/{id}/restore`); `kind` is `workflows` or `context_graphs`. Draft v0.

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `login(user, password)` | account, password | session token | the same accounts and throttle as IF-101 |
| `list_ids(session, kind)` | | sorted ids | |
| `read(session, kind, id, version=None)` | | `{"id","version","author","time","doc"}` | |
| `save(session, kind, id, doc, expected_version=None)` | document | `{"version": n}` | a new immutable version, author = the session's account |
| `history(session, kind, id)` | | list of `{"version","author","time"}` | |
| `diff(session, kind, id, a, b)` | two versions | `{"nodes_added","nodes_removed","nodes_changed","edges_added","edges_removed"}` | edges as `from->to` |
| `restore(session, kind, id, version)` | | `{"version": n}` | saves the former content as a new version; the former version stays |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| no or unknown session | 401 `unauthenticated` | nothing changed |
| wrong credentials | 401 `bad_credentials` | no session |
| unknown id, version or kind | 404 `not_found` / `unknown_kind` | nothing changed |
| `expected_version` differs from the current version | 409 `conflict` with `detail.current` | nothing changed |
| a graph rule is broken | 422 `invalid` with `rule` (`node_identity`, `adjacent_data_nodes`, `adjacent_process_nodes`, `session_stopping_criterion`, `cycle`) | no version consumed |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| read of one graph | at most 200 ms for a graph of 200 nodes | proposal, set in Plan |
| graph size | at most 500 nodes | proposal, set in Plan |

## Golden examples
1. Typical: anna logs in, saves the lookup workflow (version 1), edits one node (version 2), `diff(…,1,2)` lists the changed node, `restore(…,1)` gives version 3 equal to version 1.
2. Failure: saving a graph with a cycle `a->b->a` gives 422 `cycle`; `list_ids` shows no new id.
3. Edge: a request with a made-up session token is 401; saving with `expected_version=1` when the record is at version 2 is 409.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | 7 |
