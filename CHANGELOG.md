# Changelog

## [Unreleased]

### Added (G-V2, skill rework foundation)
- Skills are records: one description gives command, steps and knowledge; a wrong one is refused with the reason. Graphs and skill sets are stored as node and edge records (IF-302).
- Toolbox with trust status: a step from outside does not run until the owner allows it (IF-402 door).
- Snapshots of the skill set with restore; the state before restoring is kept (IF-102 v7, IF-203 v2, IF-302 v13 and v14).
- The five skills with a suite (research, plan_question, verify_claim, extract_claims, verify_computable) run from records on the workflow graph when an acceptance record exists (`conversion_dir`, default `data/conversion`, written with `tools/accept_conversion.py`); dev decisions PASS on MP-light.

### Known limitations (G-V2)
- TD-86 live trust and lifecycle on the converted path; TD-87 budgets and stop there; TD-88 AC-34 decided on dev only (no holdout); TD-89 `research.escalate@3` in the check, `@1` in the skill; TD-90 real half of the IF-103 contract suite skipped (all DRAFT until signed). No red-team case for THR-011 (V2-6). `test_decide_guard.py` and `test_judge_calibration.py` fail (`behaviour.FUNCTIONS`).

### For deployment
- The stack starts from a fresh copy (SMOKE-MIA-001 green 2026-11-20). `deploy/build.sh` does not exist yet (gap for Phase 6).

### Added (G-V3)
- G-V3.PANEL: the Skill run view, one strip across the full width below the character box and the chat. It shows the skill that runs (or the last run): header, phases, Time and Searches meters, counts, pause, resume and stop, the reason of a failed or stopped run and the elements a skill reports; a collapsed Full run part holds the result, your answers, the material, the files and the counts. The chat links to it (`#run=<id>`), it survives a reload and a restart, and its heights are two shares of the window that are set in the settings of the browser (strip 12 to 40 %, default 16; Full run part 20 to 60 %, default 34). On the phone character, chat and view are stacked.
- IF-101 v16/v17: `task_status` carries skill, start, phases, state, elements and reason; `GET /api/skill-runs/shown` and `GET /api/skill-runs/<id>`; the event `skill_run_changed`; the marker `skill_run` on the messages of a run. The table `skill_runs` (IF-302 v8). The review declares its five stages in its manifest.
- G-V3.CHAT: during a skill run the chat holds only spoken text: the skill's questions, a short status message per declared phase and a short end summary in MIA's persona with a link to the Skill run view (digest step, version 8); a live status line shows the run; the model text is cleaned of tags, scripts and run links.
- G-V3.REPORT (FB-08): every skill run ends with a report file (`# Done`, `# Stopped: ...`, `# Failed: ...`), shown in the Report part of the Full run and downloadable; http and https addresses are links that open in a new tab, nothing else is active (REQ-WFM-139 to 141, REQ-CLV-048 to 052; IF-101 v18). `lookup`, `review` and `search` are at version 2.
- Evaluation: the eval target `digest` runs the step as the app does and reads an input text by checked reference (REQ-EVL-012 to 015).

### Changed
- The result of a skill ends with a link to the Skill run view instead of a `Files:` list; a failed run says `The /<skill> run failed: <reason>`.

### Removed
- The status card in the chat (REQ-CLV-023 is superseded by REQ-CLV-030 to 039).

## [Unreleased] – 2026-11-08, TD-11 option B: speak again through the voice route (verified, not released)

### Fixed
- The speaker button under a message ("Speak again") is heard: the chat agent hands the stored text sentence by sentence, in order and through the speech filter, to the voice route of live answers, one repeat at a time (REQ-CHA-030, REQ-CHA-031, REQ-CHA-034). Before, it only sent audio_chunk events that no page played (D-276).
- Stop ends a spoken-again playback, also when no answer is generated (REQ-CHA-032); the Stop button is shown while a message is spoken again, also over a running answer, and the status returns afterwards (REQ-CHA-035, REQ-CHA-036); a spoken-again line is heard within 3 s after a Stop (REQ-VPB-006).
- A voice route that is not reachable does not break the chat: one connection attempt, the rest of that repeat is dropped (REQ-CHA-033).

### Changed
- `stop()` returns true only when an answer was stopped (IF-101 and IF-201 unchanged).
- Specification: parents of REQ-CHA-030..036 and REQ-VPB-006 one level up (A-134); REQ-CHA-033 AC-1 reworded (A-135); the 3 s of REQ-VPB-006 recorded as an accepted risk (A-136).

### Known limitations
- `/api/speak_again` has no rate limit and no cap on waiting repeats (F4, accepted; revisit with TD-61). TD-61 is open: two voice paths. A failed repeat logs two error lines (A-135). Hand check TC-CHA-035 is owner-reported, device and commit not recorded. The 3 s of REQ-VPB-006 is an accepted risk (VAL-006). Open deviations of the ladder: TD-62 (tailscale unit test), the plan backlog of `decomposition` and the red G-V2.MODEL acceptance tests (other goals). Production changes on master since v0.1.0 that this verification did not cover: `deploy/preflight.sh`, `deploy/up.sh voice`, `tools/recovery_check.sh`, `tools/fetch_kokoro.sh`, `tools/fetch_benchmarks.py`, the G-V2.MODEL stubs.

### Release record
- Verified (verification report approved 2026-11-08, `specs/mia/amendments/A-132-verification-report.md`), on master since the merges of 2026-11-08; no tag (the owner, 2026-11-08: the tag comes with iteration 2). The ladder ran locally on master `1732666`, stages 0 to 3, no CI.

## [0.1.0] – 2026-11-01, G-V1 first version of MIA (not yet validated)

### Added
- Multi-user chat with sender, streaming, stop, queue, shared history; accounts and login; the 3D character with expressions, gestures and mouth; the local voice with the anime effect; workflows as library data with versions; the pipeline runner with budgets, tools and sandbox, the run log; the evaluation harness behind IF-105; a storage layer with a PostgreSQL service and backup and restore (the app's state stays in files, TD-21); the compose stack.

### Changed
- The chat runs on the pipeline runner (skill `chat` v2).

### Known limitations
- NFR-8/CON-7 (state in PostgreSQL, TD-21) and the red-team half of TC-MIA-006 (TD-22) are deferred; nine stage 4 checks are deferred (TD-12 to TD-20); the Graph app is a mockup and moves to the next iteration (D-177); the contract suites of IF-103, IF-404 and IF-405 run only their mock side (TD-23); the script check is off in the deployed stack (`sandbox_backend: none`, TD-24); the smoke tests of `tests/smoke/` are run in Deploy, not in the merge gate (TD-25); open deferrals TD-01 to TD-04, TD-06 to TD-11; see `specs/mia/deferred.md` and `specs/mia/goals/G-V1/release-notes.md`.

### Release record
- Verified with accepted deviations (verification report approved 2026-11-01, D-183). Merged into master by fast-forward, commit `67818fb`, tag `v0.1.0`. The merge gate ran locally (stages 0 to 3 green, no CI); the field validation (VAL-001, VAL-003 to VAL-006) and the stage 4 checks are open.
