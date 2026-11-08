# Spike note: what a skill sends today, and how a test starts the real backend (G-V3.PANEL T-03)

Status: **approved** (owner maldun, 2026-11-08, all five decisions as proposed: exact phase-name match, an optional `elements` argument of `TaskMonitor.update`, a new stub with a data folder for TC-CLV-038, the observer `SkillRunObserver`, material empty; D-309). Read-only spike; no code and no test written. Next: TC-WFM-136 and TC-CLV-038 are written (Step 4b); then T-04 (the adapter) can start. Read: `chat_service.py`, `task_registry.py`, `task_monitor.py`, `extension_loader.py`, `extensions/{lookup,search,review}`, `web_app.py`, `tools/start_testing.sh`, `tools/testing_stages.d`.

## 1. What a task is today
A skill that runs as a task is an extension folder (`extensions/<id>/manifest.json` + `entry.py`): the manifest has `id`, `text`, `argument`, `example`, `aliases`, `needs`, `options`, `version`, `entry`; **no `phases` field yet** (REQ-WFM-039 adds it). `extension_loader` builds a `Task(id, run, ..., needs, version)` and registers it. `ChatService._do_chat` runs it: `entry.run(text, on_delta, on_emotion, should_stop, **handed)`, where `handed` holds only what the manifest `needs`: `ask`, `options`, `monitor` (a `TaskMonitor`), `files` (`_file_putter`), `reports`. The core, not the skill, sends `chat_start`, `chat_delta`, `chat_done`.

## 2. What each skill sends today
| | lookup | search | review |
|---|---|---|---|
| `needs` | none | none | ask, options, monitor, files, reports |
| progress | pipeline events through `services.pipeline_event` (kind `run_start`, steps with a `plain` text); the core keeps them in the status block of the answer | none: one call of the search tool (`research_chat.run_search`), no model and no pipeline events (read in `extensions/search/entry.py`) | `monitor.update(phase=<plain text>, budget=..., counts=...)`; questions through `ask(text)` |
| `task_status` | the core makes a `TaskMonitor` for every task: one card with phase `starting`, then the final one at the end (the monitor's `update` is only fed by `pipeline_event` when the task asks questions, `_late`) | the same | many, from `monitor.update` (at most every 0.5 s and once more at the end) |
| questions and answers | none | none | `ask(text)` posts the question as a message of MIA (`post_assistant`), waits for the next message of the same account (`send()` hands it over); `None` when stopped or after `review_timeout` |
| files | none | none | `files(name, data)` stores in the files volume, emits `files_changed`, adds the name to `_task_files` (shown as `Files:` links) |
| end | text returned; `chat_done` {id, text, emotion, status, files?} | the same | the same; the result is the newest message (`_late`) |
| failure and stop | exception: `chat_error` and the text `/<task> could not finish: <reason>`; stop: status `stopped` | the same | the same |

## 3. Where the recorder calls would hook in (names of the approved interface)
| Recorder call | Hook today | Source of the value |
|---|---|---|
| `start(run, skill, version, account, phases)` | in `_do_chat` right after `TaskMonitor(...)` is made | run = `message_id`; skill = `entry.id`; version = `entry.version`; account = `self._author`; phases = the manifest field (REQ-WFM-039, not there yet) |
| `phase(run, name)` | `monitor.update(phase=...)` | **a free text today** (e.g. "searching for x"), not a declared phase name: see decision 1 |
| `report(run, budget, counts, elements)` | `monitor.update(budget=..., counts=...)` | budget and counts exist; **elements do not** (`update` has no such argument): see decision 2 |
| `answer(run, text)` | the place where `send()` hands a reply to `_waiter["replies"]` | the text of the user's message |
| `file(run, name)` | `_file_putter.put` | the stored name |
| `end(run, state, reason, result, material)` | the end of `_do_chat` (`status` done, stopped, error; exception text; the result text) | `state` = done, stopped, failed (from `error`); reason = the exception text or `stopped by the user`; result = `state["text"]` before the `Files:` suffix; **material: nothing today** (a skill returns one text) |
The adapter would be one small observer object that `_do_chat` creates and calls at these places; the skills are not changed (REQ-WFM-136), and no skill file or manifest names the view.

## 4. Findings
1. **Phases:** today's phase strings are free texts for a card; declared phase names (REQ-WFM-039) cannot be matched to them.
2. **Elements:** no skill reports label and text pairs and the monitor has no argument for them, so REQ-WFM-138 ("pass on the elements a skill reports") has nothing to pass on yet.
3. **Material:** a skill returns one text; the run record's `material` stays empty for today's skills.
4. **Lookup and search** need no hook beyond start and end: they have no phases, answers, files or figures.
5. **Restart check (TC-CLV-038):** the real backend keeps its data in `web_app._db_dir` (`data/db` of the checkout, `Storage(FileBackend(_db_dir))`, the accounts in the same folder). Existing browser checks use the mock server in a container (`--network none`, the checkout mounted `:O`, writes are lost); the full app stage (`tools/testing_stages.d/20-full-app.sh`, `deploy/up.sh`) needs a GPU or the compose stack. A test that restarts the real backend needs a **data folder mounted read-write** into a container of the MIA image, a seeded run record in it (written with `Storage(FileBackend(folder)).put("skill_runs", ...)`, valid after PANEL T-01) and a seeded account; whether `web_app` starts without Ollama (`ui/tools/chat_stub_server.py` imports `web_app` and replaces the model, so it does) and how an account is created for the test are **not yet tried**.

## 5. Decisions for the owner (with my proposal)
1. **Phase names:** (a) a phase change is recorded only when the text of `monitor.update(phase=...)` equals a declared phase name; the review's manifest then declares the names its stages use and the review sends them (a small change of the review's phase strings, not of its interface) | (b) a mapping table in the manifest from free texts to phase names | (c) no phases in the run record until a skill sends names. Proposal: **(a)**, because the review is ours and the rule is simple to test; lookup and search declare none.
2. **Elements:** (a) add an optional `elements` argument to `TaskMonitor.update` (skills that do not use it are unchanged; the review may use it later) | (b) none today, REQ-WFM-138 is met by the recorder and `task_status` and checked with a scripted skill only. Proposal: **(a)**.
3. **TC-CLV-038:** (a) a new stub `ui/tools/real_backend_stub.py` (the chat stub server with a data folder from the environment and a seeded account), started twice in a container with the folder mounted read-write | (b) the real backend without a stub, with a model that is down. Proposal: **(a)**, tried first in the spike of its test (Step 4b): if it does not start, I report before writing the test.
4. **Adapter shape:** one observer object created in `_do_chat`, named `SkillRunObserver` in a new module next to `chat_service.py`, calling the recorder; `chat_service.py` gets only the calls at the six places. Proposal: yes.
5. **Material:** stays empty for today's skills (no change of skills); the recorder keeps the field. Proposal: yes.
