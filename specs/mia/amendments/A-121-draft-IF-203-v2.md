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
| **[v2]** `restore_snapshot(name, account)` | | `{"kept_as": <name of the automatic snapshot>}` | owner only. 1. writes the current state as the snapshot `before restore of <name>` (author: the owner); 2. calls `set_current_version` for every item, with the stored version,, and writes the stored trust and lifecycle back to every transform (an `untrusted` transform stays `untrusted`, AC-40; evidence of the status change: `restore of <name>`); 3. deletes no version of any item. If a step after 1 fails, the items already changed are changed back, the automatic snapshot stays and the error is raised (O4) |
| **[v2]** `pins()` | | `{pin id: model}` | the model pins in force (`eval-spec.md`) |
| **[v2]** `set_current_version(kind, id, version, author)` | | `{"version"}` | makes `version` the current version of the item; creates and deletes no version; the pointer lives in the table `current_versions` (one record per `kind/id`, document `{"version": n}`, written with `put`, every move kept). `restore` of v0 and v1 is **unchanged** (a new version with the old content) |

The kinds of `list_ids`, `read`, `save`, `history`, `restore` and `set_current_version` also include `skills`, `transforms`, `snapshots` (A-90 and v1). A `snapshots` record is written once; no kind is deletable. `read(kind, id)` without a version returns the **current** version.

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
| v2 | proposed | snapshot operations (`snapshot`, `read_snapshot`, `list_snapshots`, `restore_snapshot`), `pins()`, kinds `skills` and `snapshots`; `set_current_version` and the table `current_versions` (current-version pointer; `restore` unchanged); golden examples 8 to 12 | A-90, A-121 |

## Owner decisions on this draft (2026-11-15, session of the G-V2.CONVERT prep)
- **D-a** pointer as a table `current_versions`, written with `put` by the library. IF-102 gets v7 (table list only, no new operation); IF-302 or IF-301 must define the table (document rules, never deletable): a task for the contract owner.
- **D-b** `restore` keeps its v0 meaning (new version with the old content); golden example 1 of IF-203 and IF-104, TC-IF-203-01 and the mock stay as they are. The pointer move has its own name, `set_current_version`.
- **D-c** the library signals `forbidden` for the owner-only operations; `forbidden` joins the library's errors.

## What D-b changes elsewhere (not done, owner's go needed)
1. The red tests of `plan-baseline-it2-convert` call `restore(kind, id, version, author)` on the lab and assume the pointer meaning (TC-WFM-063 to 065; `tests/helpers/snapshot_lab.py`, `LibraryLab.restore`, `snapshot_store.py`). They must call `set_current_version` instead: an amendment of protected tests and helpers.
2. REQ-WFM-064 says every item gets "the version it had in the snapshot"; with a pointer this stays true (the current version is that version), so the text can stay; its rationale line should name `set_current_version`.
3. `read(kind, id)` without a version returns the **current** version: for items never restored this is the newest version, so v0/v1 behaviour is unchanged; after a restore of a snapshot it is the older one, and the next `save` must continue from the highest version (stale `expected_version` is checked against the current one; to be fixed in the text with the owner: proposal, `save` after a pointer move writes version max+1 and moves the pointer to it).
4. IF-301 v2 (A-90 draft of MODEL) adds the `skills` table; the `skills` kind depends on its approval.
5. The `forbidden` signal of the library needs a place in the error table of IF-203 (the draft has it); the real code maps `snapshot_store.Refused`.
