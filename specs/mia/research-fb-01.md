# Research: FB-01, skills panel beside the chat (2026-10-30)

Read-only, master `8c564f3`. Scope: where a running skill shows up today (card, result, questions), what a "session" is, how speech and the model history are fed. Nothing was run; no model was used.

## Questions
1. Where are the status card, the progress and the result of a skill drawn, and what carries them?
2. How does a skill ask a question mid-run, and where do the question and the answer end up?
3. What does a skill return to the core; is there a summary?
4. What "session" exists (login, chat, conversation) and what could list the skills of one after a reload?
5. Can task text be spoken, with repair, and is it in the history the chat model sees?
6. How are the tabs (Files) built, on desktop and phone?

## Summary
- The card is one `<section class="task-card">` per task, **inside the chat list** `#messages` (`templates/static/chat/app.js:203`, `task-card.js:62-74`), fed by `task_status` from `TaskMonitor` (at most every 0.5 s, `task_monitor.py:44`). It is not stored: after a reload it is gone (TD-01).
- A skill returns **one plain string** (`run(argument, on_delta, on_emotion, should_stop, **needs)`, `extensions/review/entry.py:19`); no summary field, no structured result. The review has a `summary` key internally (`extensions/review/review_chat.py:144,152`) but only the formatted markdown reaches the core (`:291`).
- For a skill that `needs` `ask` the result is posted late as the newest message (`chat_service.py:611`, `:689-703`), as `role: assistant` with `task: <id>` in the log record (`:695-702`); `chat_done` does not carry `task`, and the page does not draw task messages differently. Files are appended as `Files: [n](/api/files/n)` (`:687`). A failure becomes `/<task> could not finish: <reason>` with `status: error` (`:672-679`).
- Questions go through `ChatService.ask` (`chat_service.py:542-567`) as ordinary assistant messages without a `task` marker; the answer is the user's next `chat_send`. Both are in the chat log; neither is in the model history.
- **No chat-session or conversation id exists.** The login session is an in-memory token (`api_sessions.py:36,50`), lost on restart. The chat log is one global, shared JSONL file (`chat_log.py`, `constants.py:57`) read page by page with `GET /api/chat/history` (`chat_api.py:46`); it survives reload and restart and can be deleted by a user (FR-1).
- The `reports` table holds only the review's record (`record_tables.py:11`: task, skill, skill_version, question, account, model_pin, report), keyed by the message id of the result; storage has `ids/get/history` only, no query by user or time (`storage.py:84-98`). No endpoint lists running or finished tasks; `run_log.py` writes runs but nothing reads them over HTTP.
- The model history (`Communicator.chat`, `communicator.py:203-211`) is `[persona_message] + _history` from `memories.json`, separate from the chat log; tasks run outside it.
- Speech: chat answers use `SpeechStreamer(repair=behaviour.apply_rules, settle=...)` (`web_app.py:364`); tasks get `speak_answer` **without** repair (`web_app.py:603-610`), gated by `workflow_speak` / `workflow_speak_tasks`. The review speaks its questions through `say()` (`review_chat.py:227-233`).
- Personality text without a model exists: `moods.json` has phrase lists per emotion and activity, picked by `moods.py` for the mood chip; plain strings, no placeholders. `voice_lines.py` maps moods to `.wav` files, not text.
- The tabs (tasks, memos, memory, files, trust, persona, score, `workspace.js:6`) live in a **modal dialog** `#workspace` (`index.html:199-205`), the same on every layout; the phone layout is a bottom sheet with the chat (`layout.css:176-197`). "A tab like Files" today means a tab of that dialog, which cannot sit *beside* the chat.

## Relevant files
- `task_monitor.py:9-69` – monitor, payload `{id, task, phase, mode, paused, done, budget, counts}` (contract `contracts/IF-101-chat-api.md:57`)
- `chat_service.py:542-567` (`ask`), `:607-711` (`_do_chat`: card, late result, files, failure), `:278-284` (report saver), `:293-310` (pause/resume)
- `templates/static/chat/task-card.js`, `task-card-model.js`, `app.js:203`, `workspace.js:131,139,201`, `layout.js`, `layout.css`
- `extension_loader.py:5-8,51-72` – manifest fields `id, text, argument, example, entry, aliases, needs (ask, options, monitor, files, reports), options, version`
- `extensions/{lookup,review,search}/` – the three skills; only the review needs `ask`
- `communicator.py:191-211`, `speech_stream.py:38-45`, `web_app.py:364,603-610`, `moods.py`, `moods.json`
- `tests/test_core_names_no_skill.py` – core files name no skill id; the extensions folder holds exactly lookup, review, search

## Existing patterns to reuse
- `TaskMonitor` and `task_status` already carry everything the panel card needs; only the place of the card changes.
- The `task` field of a log record already marks skill output; the panel can be built from it plus a list of runs.
- `moods.json` phrase lists are the model for a status-line template file (data, editable, FR-5).
- `files_changed` / `drawFiles` are the model for a live-updated list.

## Constraints and risks found
- The panel must sit beside the chat: the workspace dialog is modal, so the panel is a new part of the chat page, not a new tab of the dialog (decision for the HLS, see section 8).
- A history "after a reload" needs a stored list of runs (today only the review's record and the chat log); a card after a reload needs the final figures stored (TD-01 resolved by this).
- Putting questions, answers and summary into the model history adds tokens to every later chat call (`num_ctx` 8192, NFR-2 "inside 50 %"): 1200 characters is about 300 tokens per summary.
- Speaking task text today skips the repair of answers; FB-01 asks for the repair.
- `test_core_names_no_skill.py` stays: the core must not name `review`, `lookup` or `search` in status-line templates either.

## Not investigated
- The inside of the lookup and search entries (whether they call `comm`), `task_registry.py`'s `tasks` field, `panels-model.js`, the i18n texts, how `speak_answer` relates to the page's `audio_claim`, and the Godot side (the panel only touches the chat page).
