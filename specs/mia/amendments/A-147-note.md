# A-147: the architecture model after G-V3.PANEL (finding F-07, owner G-V3.PANEL)

Status: **approved** (2026-11-13, maldun, by the answer "approve" to the five drafts as written; D-number and review-log row follow). `tools/check_sysml_model.py` fails today ("files not found: task-card-model.js, task-card.js"); it passed at the tag.

## Changes in `architecture.sysml` (model change, payload with `install.py`, then `bash tools/check_sysml.sh`)
| Item | Change |
|---|---|
| module list of the chat views part (line about 232) | remove `task-card.js`, `task-card-model.js` (removed in T-10); add `skill-run.js`, `skill-run-model.js`, `skill-run-shares.js` |
| N-2.3 part for the recorder | add `SkillRunRecorder` (`skill_runs.py`) and `SkillRunObserver` (`skill_run_observer.py`) with their modules, tables (`skill_runs`) and the subscription to `history` |
| part `skillRuns : SkillRunSource` | describes CHAT's relay today; keep it for CHAT and name the recorder as a different part, so that the two are not mixed |
| `extension_loader.py` | modules list unchanged; manifest `phases` now checked (T-11, F-09) |

## Not changed
Requirements, interfaces, the generated block of the CHAT line. Both lines edit the same file: the order of the merge decides who resolves it (handover, "Open for the owner" 6).

## Done (2026-11-13)
Applied directly in `architecture.sysml` (the file is not a protected test file): the chat views part lists `skill-run.js`, `skill-run-model.js`, `skill-run-shares.js` instead of the two `task-card` files; the existing part `taskRuntime.skillRunStore` (it was "proposed", target of FB-01) is now `built` with the modules `skill_runs.py` and `skill_run_observer.py` and a doc that says what the code does, so no second part was needed. `SkillRunSource` stays CHAT's relay. Checks: `tools/check_sysml_model.py` has no problems (it failed before), `bash tools/check_sysml.sh specs/mia/architecture.sysml` is ok. Not done: the manifest check of `extension_loader.py` is not listed (no part of it carries modules today). Both lines edit this file; the CHAT line will meet these hunks at the merge.
