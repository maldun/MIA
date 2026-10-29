# Design draft: usability of long tasks, first case `/review` (owner's hand review 2026-10-29)

Status: draft for the owner. Nothing is built. It changes REQ-WFM-019 (limits and questions), so it needs an amendment (A-23, requirements + IF-101 v8) before code.

## Owner's points
1. A mode without slicing: the task runs to the end, shows a monitorable status with the budget sizes, can be paused. Default for local models; the user can set it back to slicing. A commercial model gives a warning and goes back to slicing.
2. Instead of "...": numbers. Budget: time, tokens, model calls, API requests, sources screened/read. Sources: on the list, processed, still to process, include / maybe / exclude (dropped). The same monitoring for ALL future tasks; slicing/splitting stays an option for expensive models.
3. The report can be downloaded as `.md` or `.tex` from the chat (revised below: no buttons, a files area).
4. The final result is attached at the END of the chat, not inside the first message of the task (that message is far up after questions and replies).

## Owner decisions (2026-10-29)
- Run mode `run` (no questions at limits): **hard safety caps only** (generous, a stop reports as it stands); pause and stop always work.
- Local or paid: asked **only when a model is new** (never seen before); the answer is remembered per model and not asked again. A change is made by telling MIA (below). "Paid" = warning + slicing.
- UI: **one status card** per running task, updated in place, with Pause / Resume / Stop.
- **Revised after the first reading (same day):** (a) options are given per skill as `/review options slice ...`, not as a global `/mode`; the pattern is for all skills; (b) every skill has an id that is also the name of its command; (c) **no download buttons**: generated files are put into a files area of the page, where the user downloads them; this serves every future skill.

## Proposed design
**A. Task monitor (generic, in `chat_service.py`, not in `review_*`).** A task gets `monitor(update)`: `update(dict)` merges into the card state `{task, phase, budget: {name: {used, limit}}, counts: {name: n}, paused, mode}` and emits the event `task_status` (one per task, replaced in place on the page, at most 2 per second). A task reports through `update`; the service adds `seconds` itself. `review` fills: budget `seconds, tokens, calls, api_requests, screen, read`; counts `on_list, processed, to_process, include, maybe, exclude, dropped`; phase = the stage name. Future tasks (`/lookup`, workflows of N-2.4) use the same call; the card renders any budget/counts keys, so the page needs no change per task.
**B. Pause.** `ChatService.pause()/resume()` (IF-101 `pause`, `resume`, event `task_status.paused`); a task asks `should_pause()` between steps (same places as `should_stop`) and waits; the time budget does not run while paused (pause stops the clock of `Budget`). Stop still works while paused.
**C. Run mode and skill options.** `Budget` gets `mode="run"`: `exhausted()` only reports the hard caps (`caps` = limits x `cap_factor`, default 10, so one setting scales both); the checkpoint before the full texts stays (a content decision, not a budget). `slice` is the behaviour of today. The mode is an **option of the skill**, set per call: `/review options slice -- your question [until DATE]` (syntax to confirm: words after `options` up to `--` are options, `name=value` for those with a value, e.g. `slice slice_seconds=120 cap_factor=5`; `/review options` alone lists the options of the skill with their defaults). A default for all calls goes into the config `skill_options` (`{"review": {"slice": true}}`). The skill declares its options in its file (name, type, default, text), so `/<id> options` and the check of unknown options are generic code (`skill_options.py`); a future skill adds options by declaring them.
**C2. Skill id = command.** Every skill has one id; it is the command (`/review`), the name of the skill file and of the library entry. The id is unique; a second skill with the same id is refused when the library is loaded (new REQ-WFM-029, amendment A-23; the current code has the ids only by habit in `TASK_COMMAND` and `COMMANDS`). `TASK_COMMAND` and the command list are then built from the library instead of being written in `chat_service.py`.
**C3. Local or paid.** The model class (`local` | `paid`) is kept per model name in `data/model_classes.json`. A model the file does not know and that is not clearly local (Ollama on this host) is asked once ("Is `<name>` a paid model? yes / no"); the answer is stored, and a known model is never asked again. `paid` gives the warning at the start of a task and sets the default options to `slice`. The user changes it by telling MIA: the command `/model paid <name>` or `/model local <name>` (natural language later, it needs the intent step of the chat agent).
**D. Report at the end.** For tasks with questions (`review`) `chat_start` is emitted when the report is ready (not at the start); progress lines go to the card, not to a message. `chat_done` carries `task`, `downloads: ["md", "tex"]`.
**E. Files area and reports in the database (revised 2026-10-29 after the owner's answer).**
- **Two places, two jobs.** (1) The **report as a record in the database** (new table `reports`, IF-302 v4: id, task, skill id and version, question, account, created, the structured report = flow figures, works with decisions, grades and notes, keywords, limits, ended_by, and the model pin). It is the source for further reference and for benchmarks (a later review can be compared with an earlier one; labelled cases can be drawn from real runs), it lives on the dedicated volume of the database, and it is not removed by anything the user does with files. (2) The **rendered files** (`review-<date>-<slug>.md` and `.tex`, made by code from the record, so they can be made again) in a **dedicated volume for files**: the folder `files_dir`, by default on the disk MIA runs on (`data/files`), movable to another volume by config; podman mounts it as a volume in the deployment.
- **Limits are config, not policy.** `files_max_bytes` (per file) and `files_max_total_bytes` (the whole volume); assumed space is several 10 GB, so the defaults are generous (1 GB a file, 50 GB the volume). **Nothing is deleted automatically** (no retention): when a limit would be crossed the file is not written and the final message says so, the report stays in the database and can be rendered again.
- **No delete in the app.** The user deletes a file in the volume (file manager or shell); the Files tab lists what is in the folder, so a deleted file is gone from the list at the next refresh. Metadata is read from the folder (name, size, time) plus a small sidecar `<name>.json` (task, message id, account, record id) written with the file. The record in the database is deleted in the database (a later tool, not part of this amendment).
- **Service and routes.** `file_store.py`: `put(name, data, task, message_id, account, record_id)` (name sanitised, no path, type whitelist md, tex, txt, json, csv, pdf, atomic write, limits above) and `list()`. Routes, session required, every user sees all files like the other records: `GET /api/files`, `GET /api/files/<name>` (the bytes, `Content-Disposition: attachment`); event `files_changed`. No `DELETE` route. The page gets a **Files tab** (like Tasks and Memos): name, size, time, task, a download link. The final message of `/review` names the files ("Files: ...").
- **`.tex`** is made by code (`report_tex.py`: article, headings, a table of the works, escaping; no new dependency, no LaTeX run).

## Parts and tests (all new unless marked)
| Part | Test |
|---|---|
| `task_monitor.py` (state, merge, throttle) | `tests/test_task_monitor.py` |
| `Budget(mode=...)`, caps, pause clock (`review_request.py`, changed) | `tests/test_review_request.py` (changed) |
| `ChatService` pause/resume, `task_status`, `chat_start` at the end (`chat_service.py`, changed) | `tests/test_chat_review.py` (changed), `tests/test_chat_monitor.py` |
| `ReviewRun` reports counts and budget through `update`; no question at a limit in `run` mode | `tests/test_review_stages.py` (changed) |
| `report_tex.py` | `tests/test_report_tex.py` |
| `file_store.py` (volume folder, sidecar, name and type rules, size limits, nothing deleted), routes `/api/files` | `tests/test_file_store.py`, `tests/test_files_api.py` |
| table `reports` (record of a finished review, read back, same figures as the report) | `tests/test_report_record.py`, contract suite IF-302 (amendment) |
| `skill_options.py` (declare, parse `/id options ... --`, list, unknown option refused), ids from the library | `tests/test_skill_options.py`, `tests/test_chat_commands.py` (changed) |
| model class file, the question for a new model, `/model paid|local <name>` | `tests/test_model_class.py` |
| page: status card, Files tab (`chat.js`, `files.js`) | `tests/js/*.test.mjs`, hand test |

## Amendment A-23 (protected / plan files)
REQ-WFM-019 reworded (limits: run mode with hard caps, slicing as an option of the skill), new requirements: monitor (all tasks), pause, skill options (`/id options`), skill id = command (REQ-WFM-029), files area, report at the end, model class; IF-101 v8: events `task_status`, `files_changed`, operations `pause`, `resume`, `files`, `file`, `delete_file`, commands `/model`, `/<id> options`; IF-302 v4: table `reports`; contract tests (drafts under `contract-drafts`); agent view: no new model step. Eval: none (no model behaviour changes).

## Open for the owner
1. Hard caps: factor 10 of today's limits (e.g. 1800 s, 4M tokens) fine as a start?
2. `.tex`: plain `article` with a table for the works, German or English headings (English proposed)?
3. Should the card stay in the chat history after the end (frozen with the final numbers) or disappear? Proposed: stays, frozen, collapsed.
4. Syntax of the options: `/review options slice -- question` as proposed, or another separator?
5. ~~Retention and delete~~ decided: dedicated volume, size limits in config, no automatic deletion, the user deletes in the volume (the database record in the database).
6. Is a user's own phrase ("MIA, this model is paid") needed from the start, or is the command `/model paid <name>` enough for now?
