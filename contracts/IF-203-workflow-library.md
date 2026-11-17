# IF-203 – Workflow library, v2

Owner (provider): N-2.3 Workflow management   Consumers: N-2.1 API and accounts, N-2.2 Chat agent, N-2.4 Workflow execution   Decided by: N-2   Mock complexity: 2 (in-memory library)   Suite: `tests/acceptance/contract/test_if_203_workflow_library.py`

The library of workflows (and context graphs) as versioned data, with lifecycle and estimate. N-2.1 uses it for IF-104, N-2.2 to select skills, N-2.4 to fetch the workflow it runs. Python calls; draft v0. The graph rules are those of IF-102. Snapshots (v2): a named, never changed record of the state of the skill set; the owner takes, lists and restores them.

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `list_ids(kind)` | `workflows` or `context_graphs` | sorted ids | |
| `read(kind, id, version=None)` | | `{"id","version","author","time","status","doc"}` | |
| `save(kind, id, doc, author, expected_version=None)` | | `{"version"}` | a new immutable version; status `draft` |
| `history(kind, id)`, `diff(kind, id, a, b)`, `restore(kind, id, version, author)` | | as IF-104 | |
| `set_status(id, status, author)` | `draft`, `tested`, `trusted`, `retired` | `{"status"}` | promotion to `tested` or `trusted` needs a specification and a benchmark record (`attach(id, "specification" or "benchmark", doc)`) |
| `estimate(id, version=None)` | | `{"order", "critical_path", "seconds", "calls", "tokens"}` | from the graph and the costs of IF-202; `order` is a topological order of process nodes |
| **[v1]** `list_ids("transforms")`, `read("transforms", id, version=None)`, `save("transforms", id, doc, author, expected_version=None)`, `history("transforms", id)` | the kind `transforms` | as for the other kinds | `doc` is {id, version, inputs, outputs, code}: the versioned code of a transform (table `transforms`, IF-302 v9), `version` is the version of the code as the file states it; a missing, empty or null `code` is valid (a stub transform); every save is a new immutable version; `read` also gives `trust` and `lifecycle`; the first `save` of an id creates the meta record (table `transform_meta`, IF-302 v8) with trust `untrusted` and lifecycle `draft`, a later save leaves it as it is (REQ-WFM-092) |
| **[v1]** `get_meta(id)` | a transform id | `{"trust","lifecycle"}` and the optional `reason`, `evidence`, `baseline_allowed`, `shipped`, `changed_by` | |
| **[v1]** `get_trust(id)`, `get_lifecycle(id)` | a transform id | the value | the read side of the two setters |
| **[v1]** `set_trust(id, trust, author)` | `untrusted`, `trusted` | `{"trust"}` | who may set it (only the owner trusts, REQ-WFM-054) is a rule of the Workflow management, not of the library |
| **[v1]** `set_lifecycle(id, lifecycle, author, evidence=None)` | `draft`, `tested`, `retired` | `{"lifecycle"}` | `evidence` is stored when given; that `tested` needs it is a rule of the Workflow management (REQ-WFM-067) |
| **[v1]** `set_meta(id, author, **fields)` | trust, lifecycle, reason, evidence, baseline_allowed (boolean), shipped (boolean), changed_by | the meta record | one new version of the meta record; `changed_by` is set to the author |
| **[v2]** `snapshot(name, account)` | a non-empty name, the calling account | `{"name","time","author"}` | owner only (REQ-WFM-061, 066). Writes one `snapshots` record with every item of the kinds `skills`, `workflows`, `context_graphs`, `transforms` and its current version; for transforms also trust and lifecycle; and the model pins in force |
| **[v2]** `read_snapshot(name)` | | `{"name","time","author","items":[{"kind","id","version","trust","lifecycle"}],"pins":{pin id: model}}` | `trust`, `lifecycle` only on items of kind `transforms` |
| **[v2]** `list_snapshots(account)` | the calling account | `[{"name","time","author"}]`, oldest first | owner only; exactly these fields (REQ-WFM-062) |
| **[v2]** `restore_snapshot(name, account)` | | `{"kept_as": <name of the automatic snapshot>}` | owner only. 1. writes the current state as the snapshot `before restore of <name>` (author: the owner); 2. calls `set_current_version` for every item, with the stored version, and writes the stored trust and lifecycle back to every transform (an `untrusted` transform stays `untrusted`, AC-40; evidence of the status change: `restore of <name>`); 3. deletes no version of any item. If a step after 1 fails, the items already changed are changed back, the automatic snapshot stays and the error is raised |
| **[v2]** `pins()` | | `{pin id: model}` | the model pins in force (`eval-spec.md`) |
| **[v2]** `set_current_version(kind, id, version, author)` | | `{"version"}` | makes `version` the current version of the item; creates and deletes no version; the pointer lives in the table `current_versions` (IF-302 v13: one record per `kind/id`, document `{"version": n}`, written with `put`, every move kept). `restore` of v0 and v1 is **unchanged** (a new version with the old content) |

The kinds of `list_ids`, `read`, `save`, `history`, `restore` and `set_current_version` also include `skills`, `transforms`, `snapshots` (A-90 and v1). A `snapshots` record is written once; no kind is deletable. `read(kind, id)` without a version returns the **current** version; an item without a pointer record reads as its newest version, so v0 and v1 behaviour is unchanged. `save` after a pointer move writes version max+1 and moves the pointer to it; `expected_version` is checked against the current version.

**Snapshot record (open):** the stored `snapshots` document is a JSON object. Required: `name`, `time`, `author`, `items` (a list of `{kind, id, version}`; plus `trust` and `lifecycle` on transforms) and `pins`. Further fields are optional, **kept as given and never refused**; known today: `format` (integer, 1 for this text, raised when the meaning of the record changes) and `note` (free text of the owner). `read_snapshot` returns the document as stored, so a reader gets the fields it knows and ignores the rest, and a restore uses only the required ones. Each item may carry extra fields too (kept, ignored by a restore). Exception: `list_snapshots` stays exactly `name`, `time`, `author` (REQ-WFM-062, TC-WFM-062). A snapshot is written once, so a record keeps the shape of the time it was taken.

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| a graph rule is broken | `ServiceError("invalid", rule=…)` | nothing stored |
| unknown id, version or kind | `not_found` | nothing changed |
| stale `expected_version` | `conflict` with `detail.current` | nothing changed |
| promotion without specification or benchmark | `not_promotable` with `detail` = the missing parts | status unchanged |
| **[v1]** a value outside the lists of trust or lifecycle, an optional meta field of the wrong type or an unknown field | `ServiceError("invalid", rule="schema", detail=<field>)` | the meta record is unchanged |
| **[v2]** the account is not the owner (the account that creates accounts, REQ-WFM-066) | `ServiceError("forbidden")` (the test double raises `snapshot_store.Refused`; the real code maps it) | no snapshot written, no item or status changed, list of snapshots unchanged |
| **[v2]** unknown snapshot name | `not_found` | nothing changed |
| **[v2]** `snapshot` with a name that exists | `conflict` | nothing written |
| **[v2]** `snapshot` with an empty name, or a `set_current_version` to a version that does not exist | `ServiceError("invalid", rule="schema")` | nothing written |
| **[v2]** the automatic name `before restore of <name>` exists | not an error: the name gets the suffix ` (2)`, ` (3)`, ... | the older snapshot is unchanged |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| estimate of a graph of 200 nodes | at most 1 s | proposal, set in Plan |
| **[v2]** `snapshot` and `restore_snapshot` | no time bound; neither deletes anything | A-121 |

## Golden examples
1. Typical: save, edit, `diff` names the changed node, `restore` makes version 3 equal to version 1; status stays `draft`.
2. Failure: `set_status(id, "tested", …)` before a specification and a benchmark is `not_promotable`, `detail == ["specification", "benchmark"]`.
3. Edge: `estimate` of a graph with a session node counts its maximum cycles times the cost of one cycle.
4. **[v1]** Typical: a new transform is untrusted and draft; a second save is version 2 (TC-IF-203-05).
5. **[v1]** Typical: trusted and tested (evidence `run-1`) survive version 2; version 1 still reads its own document (TC-IF-203-06).
6. **[v1]** Failure: `fine` is refused for trust and for lifecycle with the field as detail, the statuses stay (TC-IF-203-07).
7. **[v1]** Edge: the optional meta fields are kept, a boolean field with a text is refused (TC-IF-203-08); unknown ids and stale versions are `not_found` and `conflict` (TC-IF-203-09).
8. **[v2]** Typical: 2 skills, 2 workflow graphs, 1 context graph, 3 transforms; `snapshot("before-rework")`; `read_snapshot` has 8 items with versions, the transforms with trust and lifecycle, and the pin MP-light.
9. **[v2]** Restore: state S1 stored as `a`; a skill, a workflow graph, a context graph and a transform status change (S2); `restore_snapshot("a")` gives S1, the snapshot `before restore of a` holds S2 with the owner as author, and `restore_snapshot("before restore of a")` gives S2 again; restoring `a` a second time stores `before restore of a (2)`.
10. **[v2]** Failure: a second account (created by the owner) calls `snapshot` and `restore_snapshot`: both `forbidden`; list and state unchanged. A `snapshot` with an existing name is `conflict`.
11. **[v2]** Edge: the snapshot is older than the last 3 versions of every item; after the restore the version list of every item before the call is a prefix of the list after it; an `untrusted` transform in the snapshot is `untrusted` after the restore even if it was `trusted` before.
12. **[v2]** Edge (failure inside a restore): the write of the third item fails; the first two are changed back, the state equals the one before the call, `before restore of <name>` exists, the error is raised.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | 8 |
| v1 | 2026-11-11 | the kind `transforms` and its meta record: operations `get_meta`, `get_trust`, `get_lifecycle`, `set_trust`, `set_lifecycle`, `set_meta`, golden examples 4 to 7 (suite TC-IF-203-05 to 09) | A-90, A-111 |
| v2 | 2026-11-18 | snapshot operations (`snapshot`, `read_snapshot`, `list_snapshots`, `restore_snapshot`), `pins()`, kinds `skills` and `snapshots`; `set_current_version` and the table `current_versions` (current-version pointer; `restore` unchanged); `forbidden`; golden examples 8 to 12 | A-90, A-121 |
