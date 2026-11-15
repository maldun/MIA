# A-121 draft: IF-203 v2, snapshot section (text for `contracts/IF-203-workflow-library.md`)

Status: **draft for the owner's review**, not applied. Parent session applies it to `contracts/` after approval (`parallel-work.md`); no contract suite is written before that (D-188). Basis: `A-121-note.md` with the owner's answers O1 (A), O2 to O5, assumptions 3, 4, 6 (D-240), A-90, and IF-203 v1 as merged from TOOLBOX (2026-11-11).

Changes against the note: IF-203 v1 already has `get_trust`, `get_lifecycle`, `set_trust` and `set_lifecycle(..., evidence=None)` (A-111), so the note's rows for them and its assumption 6 fall away; the library needs no new transform operation. The result is **v2**.

## Text to insert

### Header sentence (append)
Snapshots (v2): a named, never changed record of the state of the skill set; the owner takes, lists and restores them.

### Operations (new rows)
| Name | Input | Output | Notes |
|---|---|---|---|
| **[v2]** `snapshot(name, account)` | a non-empty name, the calling account | `{"name","time","author"}` | owner only (REQ-WFM-061, 066). Writes one `snapshots` record with every item of the kinds `skills`, `workflows`, `context_graphs`, `transforms` and its current version; for transforms also trust and lifecycle; and the model pins in force |
| **[v2]** `read_snapshot(name)` | | `{"name","time","author","items":[{"kind","id","version","trust","lifecycle"}],"pins":{pin id: model}}` | `trust`, `lifecycle` only on items of kind `transforms` |
| **[v2]** `list_snapshots(account)` | the calling account | `[{"name","time","author"}]`, oldest first | owner only; exactly these fields (REQ-WFM-062) |
| **[v2]** `restore_snapshot(name, account)` | | `{"kept_as": <name of the automatic snapshot>}` | owner only. 1. writes the current state as the snapshot `before restore of <name>` (author: the owner); 2. makes the stored version the current one of every item, and writes the stored trust and lifecycle back to every transform (an `untrusted` transform stays `untrusted`, AC-40; evidence of the status change: `restore of <name>`); 3. deletes no version of any item. If a step after 1 fails, the items already changed are changed back, the automatic snapshot stays and the error is raised (O4) |
| **[v2]** `pins()` | | `{pin id: model}` | the model pins in force (`eval-spec.md`) |
| **[v2]** `restore(kind, id, version, author)` | | `{"version"}` | **changed meaning, see O1**: makes `version` the current version of the item; creates and deletes no version. Applies to all kinds, also `workflows` and `context_graphs` |

The kinds of `list_ids`, `read`, `save`, `history` and `restore` also include `skills`, `transforms`, `snapshots` (A-90 and v1). A `snapshots` record is written once; no kind is deletable. `read(kind, id)` without a version returns the **current** version.

### Errors (new rows)
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| **[v2]** the account is not the owner (the account that creates accounts, REQ-WFM-066) | `ServiceError("forbidden")` (the test double raises `snapshot_store.Refused`; the real code maps it) | no snapshot written, no item or status changed, list of snapshots unchanged |
| **[v2]** unknown snapshot name | `not_found` | nothing changed |
| **[v2]** `snapshot` with a name that exists, or an empty name | `conflict`, or `invalid` with `rule="schema"` for the empty name | nothing written |
| **[v2]** the automatic name `before restore of <name>` exists | not an error: the name gets the suffix ` (2)`, ` (3)`, ... (O3) | the older snapshot is unchanged |

### Bounds
No time bound for `snapshot` and `restore_snapshot` (O5). Nothing is deleted by either.

### Golden examples (new)
8. **[v2]** Typical: 2 skills, 2 workflow graphs, 1 context graph, 3 transforms; `snapshot("before-rework")`; `read_snapshot` has 8 items with versions, the transforms with trust and lifecycle, and the pin MP-light.
9. **[v2]** Restore: state S1 stored as `a`; a skill, a workflow graph, a context graph and a transform status change (S2); `restore_snapshot("a")` gives S1, the snapshot `before restore of a` holds S2 with the owner as author, and `restore_snapshot("before restore of a")` gives S2 again; restoring `a` a second time stores `before restore of a (2)`.
10. **[v2]** Failure: a second account (created by the owner) calls `snapshot` and `restore_snapshot`: both `forbidden`; list and state unchanged. A `snapshot` with an existing name is `conflict`.
11. **[v2]** Edge: the snapshot is older than the last 3 versions of every item; after the restore the version list of every item before the call is a prefix of the list after it; an `untrusted` transform in the snapshot is `untrusted` after the restore even if it was `trusted` before.
12. **[v2]** Edge (failure inside a restore): the write of the third item fails; the first two are changed back, the state equals the one before the call, `before restore of <name>` exists, the error is raised.

### Version history (new row)
| v2 | proposed | snapshot operations (`snapshot`, `read_snapshot`, `list_snapshots`, `restore_snapshot`), `pins()`, kinds `skills` and `snapshots`; `restore` makes a stored version the current one (current-version pointer); golden examples 8 to 12 | A-90, A-121 |

## Consequences the owner should see before approving
1. **O1 (A) breaks golden example 1 of v0 and v1** ("`restore` makes version 3 equal to version 1", a new version with old content), and the same sentence in IF-104. Under A the restore creates no version. The line has to be replaced (example 1: "`restore` makes version 1 the current one; `history` still lists 3 versions"), and every consumer of `restore` (N-2.1 via IF-104, the editor) reads the new meaning. The existing suite `test_if_203_workflow_library.py` and the mock test the old meaning (checked: TC-IF-203-01 expects `restore("workflows", "lookup", 1, "anna") == {"version": 3}`; the mock `restore` at `tests/helpers/mocks/if_203_workflow_library.py:60` does the same): **an amendment of a protected suite and mock** (owner's go).
2. **The current-version pointer has no home yet.** IF-102 (v6) has no such operation. Two ways, both need a contract change decided by the contract owner (not by this session):
   - *(a)* a table `current_versions` (id per kind and item, document `{"version": n}`), written with `put` by the library: IF-102 changes only in its table list (v7), no new operation; every version of the pointer is kept, which is a free history of restores.
   - *(b)* a new storage operation `set_current(table, id, version, author)` and `get` without version returning it: touches every backend, the mock, the PostgreSQL contract suite.
   Recommendation: (a), the smaller change, same pattern as `transform_meta`. It makes the restore of many items not atomic (O4 handles that by the roll-back rule above).
3. **`forbidden` is not yet an error code of the library**, only `invalid`, `not_found`, `conflict`, `not_promotable`; the ServiceError set of IF-102 would need it, or the owner check stays a rule of the Workflow management (as for `set_trust` in v1) and the library signals nothing. The draft keeps the signal because the tests expect a refusal.
4. IF-301 v2 (A-90 draft of MODEL) adds the `skills` table; the `skills` kind here depends on its approval.

## Decisions needed
- D-a: pointer as table (a) or storage operation (b)?
- D-b: replace golden example 1 as proposed, and amend the existing IF-203 suite and mock for the new `restore`?
- D-c: `forbidden` in the library, or the owner rule only in the Workflow management?
