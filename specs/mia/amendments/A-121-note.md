# A-121: IF-203 v1, snapshot section (proposal for the owner's review, G-V2.CONVERT)

Status: **proposed, not applied, not reviewed**. This is text for the owner to read (D-188: the contract text is reviewed before any contract suite is written). It fills in the snapshot part of A-90 ("new kinds `skills`, `transforms`, `snapshots`; operations `snapshot`, `list_snapshots`, `restore_snapshot`, owner only"), which names the operations and nothing else. It does not change `contracts/` (parent session) and it does not replace A-90. The signatures below are the ones the red tests of `plan-baseline-it2` assume (`snapshot_store.py`, `tests/helpers/snapshot_lab.py`); where the text differs from the tests, the line is marked **[differs from the tests]**.

Open points for the owner are numbered O1 to O5 at the end. O1 changes tests.

## Kinds (addition to the operations table)
`list_ids`, `read`, `save`, `history` and `restore` also accept `skills`, `transforms` and `snapshots` (A-90). Every kind is versioned and nothing is deletable. A `snapshots` record is written once and never changed.

## Operations (addition)
| Name | Input | Output | Notes |
|---|---|---|---|
| `snapshot(name, account)` | a non-empty name, the calling account | `{"name", "time", "author"}` | owner only. Stores one `snapshots` record that holds every item of the kinds `skills`, `workflows`, `context_graphs` and `transforms` with its current version, the transforms also with trust and lifecycle, and the model pins |
| `read_snapshot(name)` | | `{"name", "time", "author", "items": [{"kind", "id", "version", "trust", "lifecycle"}], "pins": {pin id: model}}` | `trust` and `lifecycle` only on items of kind `transforms` |
| `list_snapshots(account)` | the calling account | `[{"name", "time", "author"}]`, oldest first | owner only; exactly these three fields |
| `restore_snapshot(name, account)` | | `{"kept_as": "before restore of <name>"}` | owner only. 1. stores the current state as the snapshot "before restore of <name>" with the owner as author; 2. gives every item of the snapshot its version, and every transform its trust and lifecycle; 3. deletes no version of any item |
| `get_trust(id)`, `get_lifecycle(id)` | a transform id | the value | **[not in A-90, assumed by the tests]** read side of `set_trust` and `set_lifecycle` |
| `pins()` | | `{pin id: model}` | **[not in A-90, assumed by the tests]** the model pins in force, as in `eval-spec.md` |
| `set_trust(id, trust, author)` | `untrusted`, `trusted` | | owner only (A-90) |
| `set_lifecycle(id, lifecycle, author, evidence)` | `draft`, `tested`, `retired` | | A-90 asks for named evidence **[differs from the tests: the lab has no `evidence` argument; a restore would pass the evidence "restore of <name>"]** |

`restore(kind, id, version, author)` (existing): see O1.

## Errors (addition)
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| the account is not the owner (the account that creates accounts, REQ-WFM-066) | `ServiceError("forbidden")` **[the tests expect `snapshot_store.Refused`; the real code maps it to this signal]** | no snapshot written, no item and no status changed, the list of snapshots unchanged |
| unknown snapshot name | `not_found` | nothing changed |
| `snapshot` with a name that exists | `conflict` **[not covered by the tests, see O3]** | nothing written |

## Golden examples (addition)
1. Typical: a state of 2 skills, 2 workflow graphs, 1 context graph and 3 transforms; the owner calls `snapshot("before-rework")`; `read_snapshot` holds 8 items, each with its version, the three transforms with trust and lifecycle, and the pin MP-light.
2. Restore: state S1 is stored as "a"; a skill, a workflow graph, a context graph and one transform status change (S2); the owner calls `restore_snapshot("a")`; the snapshot "before restore of a" exists with S2 and the owner as author, the state equals S1, and `restore_snapshot("before restore of a")` gives S2 again.
3. Failure: a second account, created by the owner, calls `snapshot` and `restore_snapshot`; both give `forbidden`, the list of snapshots and the state are unchanged.
4. Edge: the snapshot is older than the last 3 versions of every item; after the restore the list of versions of every item before the restore is a prefix of the list after it (nothing deleted).

## Version history (addition)
| Version | Date | Change | Amendment |
|---|---|---|---|
| v1 | proposed | kinds `skills`, `transforms`, `snapshots`; trust and lifecycle of transforms; `snapshot`, `read_snapshot`, `list_snapshots`, `restore_snapshot` | A-90, A-121 |

## Open points
- **O1, what a restore does to an item. Decided: A (owner, answer in the session of 2026-11-07); the tests of `plan-baseline-it2` stay as they are. The text of B is kept for the record.** The requirement says every item gets "the version … it had in the snapshot" (REQ-WFM-064).
  - *A, current-version pointer* (the red tests assume this): `restore(kind, id, version, author)` makes `version` the current one and creates and deletes nothing. It needs a "current version" concept in the storage interface, which v0 and IF-102 do not have.
  - *B, new version with the old content* (v0 behaviour, golden example 1 of v0: "`restore` makes version 3 equal to version 1"): the item then has version n+1 with the document of version k. "Equal in version" can then only mean "same content", and the snapshot records which version it came from. Nothing new is needed in storage. If B is chosen, TC-WFM-063 to 065 and `LibraryLab.restore` change, and the wording of REQ-WFM-064's criterion should say "content" instead of "version".
- **O2, the transform trust on restore.** `set_trust` is owner only; a restore is done by the owner, so it may call it. A restore of a transform that is `untrusted` in the snapshot must leave it untrusted (AC-40); the text above does that by writing the stored trust back.
- **O3, name rules.** Duplicate names give `conflict` here (snapshots are never overwritten). The automatic names "before restore of <name>" can themselves be restored and may repeat when the same snapshot is restored twice; the proposal is a numeric suffix " (2)". Neither is in the requirements or the tests.
- **O4, failure in the middle of a restore.** Proposal: the automatic snapshot is written first and always stays; if a later step fails, the items already changed are changed back, so the state equals the one before the call. Not in the requirements or the tests.
- **O5, bounds.** No time bound is proposed for `snapshot` and `restore_snapshot`; a bound would be set in Plan like the 1 s of `estimate`.
