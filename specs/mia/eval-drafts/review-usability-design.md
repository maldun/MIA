# Design draft: usability of long tasks, first case `/review` (owner's hand review 2026-10-29)

Status: draft for the owner. Nothing is built. It changes REQ-WFM-019 (limits and questions), so it needs an amendment (A-23, requirements + IF-101 v8) before code.

## Owner's points
1. A mode without slicing: the task runs to the end, shows a monitorable status with the budget sizes, can be paused. Default for local models; the user can set it back to slicing. A commercial model gives a warning and goes back to slicing.
2. Instead of "...": numbers. Budget: time, tokens, model calls, API requests, sources screened/read. Sources: on the list, processed, still to process, include / maybe / exclude (dropped). The same monitoring for ALL future tasks; slicing/splitting stays an option for expensive models.
3. The report can be downloaded as `.md` or `.tex` from the chat.
4. The final result is attached at the END of the chat, not inside the first message of the task (that message is far up after questions and replies).

## Owner decisions (2026-10-29)
- Run mode `run` (no questions at limits): **hard safety caps only** (generous, a stop reports as it stands); pause and stop always work.
- Local or paid: **ask once per session** when the model is not clearly local; "paid" = warning + slicing for that session.
- UI: **one status card** per running task, updated in place, with Pause / Resume / Stop; the report message gets **.md and .tex buttons**.

## Proposed design
**A. Task monitor (generic, in `chat_service.py`, not in `review_*`).** A task gets `monitor(update)`: `update(dict)` merges into the card state `{task, phase, budget: {name: {used, limit}}, counts: {name: n}, paused, mode}` and emits the event `task_status` (one per task, replaced in place on the page, at most 2 per second). A task reports through `update`; the service adds `seconds` itself. `review` fills: budget `seconds, tokens, calls, api_requests, screen, read`; counts `on_list, processed, to_process, include, maybe, exclude, dropped`; phase = the stage name. Future tasks (`/lookup`, workflows of N-2.4) use the same call; the card renders any budget/counts keys, so the page needs no change per task.
**B. Pause.** `ChatService.pause()/resume()` (IF-101 `pause`, `resume`, event `task_status.paused`); a task asks `should_pause()` between steps (same places as `should_stop`) and waits; the time budget does not run while paused (pause stops the clock of `Budget`). Stop still works while paused.
**C. Run mode.** Config `task_mode`: `run` (default for a local model) or `slice`. `Budget` gets `mode="run"`: `exhausted()` only reports the hard caps (`caps` = limits x `task_cap_factor`, default 10 of the old limits, so one setting scales both); the checkpoint before the full texts stays (it is a content decision, not a budget). In `slice` the behaviour of today. The model class comes from the model pin (`local: true` for Ollama on this host); anything else -> MIA asks once per session ("is this a paid model?"), the answer "paid" prints the warning and sets `slice` for the session. Chat command `/mode slice|run` (IF-101 note).
**D. Report at the end.** For tasks with questions (`review`) `chat_start` is emitted when the report is ready (not at the start); progress lines go to the card, not to a message. `chat_done` carries `task`, `downloads: ["md", "tex"]`.
**E. Download.** New route `GET /api/report?message_id=..&format=md|tex` (session required; 404 for a message without a report): `md` is the stored text, `tex` is made by code (`report_tex.py`: headings, tables, escaping; no new dependency, no LaTeX run). The page shows two buttons on a message with `downloads`.

## Parts and tests (all new unless marked)
| Part | Test |
|---|---|
| `task_monitor.py` (state, merge, throttle) | `tests/test_task_monitor.py` |
| `Budget(mode=...)`, caps, pause clock (`review_request.py`, changed) | `tests/test_review_request.py` (changed) |
| `ChatService` pause/resume, `task_status`, `chat_start` at the end (`chat_service.py`, changed) | `tests/test_chat_review.py` (changed), `tests/test_chat_monitor.py` |
| `ReviewRun` reports counts and budget through `update`; no question at a limit in `run` mode | `tests/test_review_stages.py` (changed) |
| `report_tex.py`, route `/api/report` | `tests/test_report_tex.py`, `tests/test_report_api.py` |
| page: status card, buttons (`chat.js`) | `tests/js/*.test.mjs`, hand test |
| model class and the once-per-session question | `tests/test_task_mode.py` |

## Amendment A-23 (protected / plan files)
REQ-WFM-019 reworded (limits: run mode with hard caps, slicing as an option), new requirements for the monitor (all tasks), pause, download, report at the end; IF-101 v8: events `task_status`, operations `pause`, `resume`, `report`, command `/mode`; contract tests (drafts under `contract-drafts`); agent view: no new model step. Eval: none (no model behaviour changes).

## Open for the owner
1. Hard caps: factor 10 of today's limits (e.g. 1800 s, 4M tokens) fine as a start?
2. `.tex`: plain `article` with a table for the works, German or English headings (English proposed)?
3. Should the card stay in the chat history after the end (frozen with the final numbers) or disappear? Proposed: stays, frozen, collapsed.
