# Interface note: the run recorder of N-2.3 (proposal for Plan Step 4, G-V3.PANEL)

Status: **proposed** (the owner approves or changes it before any test of TC-WFM-130 to 138 is written). Drafted 2026-11-08. Not a contract in `contracts/` (it is inside the node N-2.3, no other node calls it); it fixes the names the red tests use. A change after approval is a plan amendment.

## Why
REQ-WFM-130 to 138 and TC-WFM-130 to 138 name behaviour (one record per run, figures, reason, result, material, files, answers, the run that is shown, deletion with the history, texts as data, elements) but no part that has it. `task_monitor.py` (`TaskMonitor`, REQ-WFM-031) only sends `task_status`. A part is needed that keeps the run record next to it.

## Proposal
New module `skill_runs.py` with the class `SkillRunRecorder(storage, emit, clock=time.monotonic, now=utc_now)`:
- `storage`: the storage of IF-102 (`put`, `get`, `ids`, `delete`, `subscribe`); in the checks the fake of the table `skill_runs` of TR-PANEL-003.
- `emit(event, payload)`: the same callback as `TaskMonitor`; sends `task_status` and `skill_run_changed`.
- `clock`: monotonic seconds for the monitor; `now`: UTC time string for `started`, `ended` and the time of an answer (a fake in the checks).

| Method | Does | Requirement |
|---|---|---|
| `start(run, skill, version, account, phases=())` | writes the record (state `running`, `started`, phases all `waiting`), creates the `TaskMonitor` of the run, sends `task_status` | REQ-WFM-130, 031 |
| `phase(run, name)` | marks the phase `running` and the one before it `done`; sends `task_status` | REQ-WFM-130 |
| `report(run, budget=None, counts=None, elements=None)` | passes figures to the monitor (at most twice per second) and keeps the last figures and the `elements` (list of `{label, text}`) in the record | REQ-WFM-031, 131, 138 |
| `answer(run, text)` | appends `{text, time}` to the record in order; sends `skill_run_changed` | REQ-WFM-133 |
| `file(run, name)` | appends the file name to the record; sends `skill_run_changed` | REQ-WFM-132 |
| `end(run, state, reason=None, result="", material=())` | state `done`, `failed` or `stopped`; stores final figures, reason (only failed and stopped), result, material, `ended`; sends the last `task_status` (done true) and `skill_run_changed` | REQ-WFM-131, 132 |
| `record(run)` | the stored record as the run record of IF-101 v16 (`id, skill, version, started, ended, state, phases, budget, counts, reason, answers, result, material, files`), or `None` | REQ-WFM-130, IF-101 |
| `shown(account)` | the id of the run started most recently while runs of the account run, else the one ended last, else `None`; never an earlier one | REQ-WFM-134 |

Texts (result, material, answers, reason, elements) are stored and returned as they came, as text; the recorder never evaluates them (REQ-WFM-137).

**Deletion with the history (REQ-WFM-135):** the constructor subscribes to the table `history`; a notice with `version: None` deletes the run record whose run id is the `id` of the notice (the history record has the id of its run; A-144), no other, and sends `skill_run_changed {id: <run>}`; a notice whose id is no run changes nothing; the files are not touched. The recorder is told nothing else.

**Skills stay unchanged (REQ-WFM-136):** a skill-runner adapter (not part of the recorder) translates the events a skill sends today into these calls; TC-WFM-136 drives the adapter with a scripted skill and inspects that no skill file names the view.

## Open questions (with my proposal)
1. **Which account does a history deletion name?** The IF-102 notice carries `table`, `id`, `version: None`, `author` only. Proposal: the recorder treats `author` as the account whose records are deleted (a delete of an account's history is made in the name of that account, as the deletes of `memos` in TC-IF-102-09). The alternative is a changed notice (new IF-102 field), which is a contract change.
2. **Which events feed the adapter?** IF-202 returns `events` after the run and the chat service sends `task_status` today; no live event stream of a skill is specified. Proposal: the checks drive the recorder directly through the methods above, and the adapter is a task of Step 5 with its own check TC-WFM-136; the adapter's event list is fixed there from the code of today, not here.

## Stub for Step 4
`skill_runs.py` is created as a stub whose methods raise `NotImplementedError` after the constructor, so the checks import it and fail in their assertions or on the first call; the real class is written in Implement.
