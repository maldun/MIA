# A-106: task T-07, graph model on the record tables (G-V2.MODEL, findings of T-05)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a106.sh` is not yet run with `--do` in the repository.

## Findings of T-05 (commit `112b6b0`) and the owner's decisions (2026-11-08)
| Finding | Decision |
|---|---|
| 1 (REQ-WFM-040): the record checks of IF-301 v2 refuse a skill record without `context_graph_id`; `SkillRecords.store` raised `StorageError('invalid')` | **catch it and give back a refused result** (rule and detail of the Storage refusal). A follow-up commit of T-05 with its test; no plan text changes |
| 2 (TR-MODEL-001): the fake accepts that broken record | known gap of the fake, pinned by the test; no change |
| 3 (TR-MODEL-001): `GraphModel` saves into `workflow_graphs`, which the real Storage does not have (`unknown_table`); `put` and `get` of the real Storage have other shapes. The graph rules of T-01 never run on stored data | **amend: new task T-07** (this note) |

## What A-106 contains
| File | Change |
|---|---|
| `goals/G-V2.MODEL/plan.md` | **T-07 new**: `GraphModel(Storage)` itself saves a graph as `graph_nodes` and `graph_edges` records plus a `graphs` header pinning the member versions, and reads it back; the mapping that the adapter test holds today (`RealGraphTables` in `tests/test_skill_record_storage.py`) moves into `graph_model.py`; a graph refused by the Storage record checks is a refused result naming rule and detail. Counts (seven tasks) and order (T-06 and T-07 both need T-05, independent of each other) |
| `review-log.md` | row D-307 appended |
No protected test, helper, contract or requirement text changes; STORE's files stay untouched; TR-MODEL-001 keeps the A-105 wording.

## Points for the owner
1. T-07 is new work beyond the first plan (the plan assumed `GraphModel` would be wired by T-05). It is one session of the same size as the others.
2. The requirement ids in the table row of T-07 are those of the rules that T-01 implements; T-07 adds no new requirement and no new check id, it only makes their stored form real. Say if you want a requirement of its own for it.
3. The refused-result shape of finding 1 follows the command clash of REQ-WFM-042; the agent that does the follow-up reports the exact shape.
4. ID choice: A-106 follows A-105; D-307 follows D-306.

## Checked by the drafter (scratch copy; nothing installed in the repository)
`--do` twice: the second run changes nothing; the look-only run changes nothing.

## Install
```
bash tools/apply_amendment_a106.sh --report     # look only
bash tools/apply_amendment_a106.sh --do         # then commit "plan: A-106 installed"
```
