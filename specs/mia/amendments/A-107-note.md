# A-107: task T-06 reworded, the extension loader (G-V2.MODEL, stop of T-06)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a107.sh` is not yet run with `--do` in the repository.

## What happened
The T-06 agent stopped before writing code. The plan said `library.py` and `extension_loader.py` list and start skills. `library.py` is the pipeline and node library (`entries`, `search`, `resolve`, `expand`): it has no commands, skill IDs or graph IDs. The only place that registers commands is `extension_loader.load_extensions(package, folder, registry, services)` (manifests become `Task` objects in `TaskRegistry`; `web_app.py` line ~678 calls it). It has no access to the records, and a `Task` has no graph ID.

## Owner's decisions (2026-11-08, questionnaire)
- Where: **option A**, the extension loader: a new optional parameter `catalog` on `load_extensions`; a skill with a record registers under the record's command; its task carries `workflow_graph_id` from `SkillCatalog.start`.
- Bounds: **yes, amend**: `task_registry.py` (one new attribute `workflow_graph_id` on `Task`, default None) and `web_app.py` (create the `SkillCatalog` over `SkillRecords`, pass it) come into T-06.

## What A-107 contains
| File | Change |
|---|---|
| `goals/G-V2.MODEL/plan.md` | T-06 row and section rewritten: tests (1) record skill registers under the record's command with `workflow_graph_id`, (2) a skill without a record unchanged, (3) a record-only skill is listed by its command but not made runnable, (4) the wiring in `web_app.py`; touches `extension_loader.py`, `task_registry.py`, `web_app.py`; `library.py` is not touched |
| `review-log.md` | row D-308 appended |
No protected test, helper, contract or requirement text changes; STORE's files stay untouched.

## Points for the owner
1. **Record-only skills (my reading, for you to confirm):** AC-31 of REQ-WFM-041 speaks of the old files going away. T-06 does not decide what runs when a record exists but no entry module does; such a skill is listed by its command and not made runnable. G-V2.CONVERT moves the skills one by one. If you want a record-only skill to start its graph already in T-06, say so: that is a new behaviour in the runner and needs its own task.
2. The `web_app.py` test is limited to what a test without a running server can show (the catalog is created and passed); the real start is hand-checked at Verify or Deploy.
3. Findings noted from T-07 (not changed): saving the same graph again writes a new version of every node and edge; an edge or header refusal can leave orphan node versions (append-only, harmless). They go to the Verify list.
4. ID choice: A-107 follows A-106; D-308 follows D-307.

## Checked by the drafter (scratch copy; nothing installed in the repository)
`--do` three times: runs 2 and 3 change nothing; the rest of the plan (from T-07 on) is identical.

## Install
```
bash tools/apply_amendment_a107.sh --report     # look only
bash tools/apply_amendment_a107.sh --do         # then commit "plan: A-107 installed"
```
