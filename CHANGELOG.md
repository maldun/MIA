# Changelog

## [0.1.0] – 2026-11-01, G-V1 first version of MIA (not yet validated)

### Added
- Multi-user chat with sender, streaming, stop, queue, shared history; accounts and login; the 3D character with expressions, gestures and mouth; the local voice with the anime effect; workflows as library data with versions; the pipeline runner with budgets, tools and sandbox, the run log; the evaluation harness behind IF-105; a storage layer with a PostgreSQL service and backup and restore (the app's state stays in files, TD-21); the compose stack.

### Changed
- The chat runs on the pipeline runner (skill `chat` v2).

### Known limitations
- NFR-8/CON-7 (state in PostgreSQL, TD-21) and the red-team half of TC-MIA-006 (TD-22) are deferred; nine stage 4 checks are deferred (TD-12 to TD-20); the Graph app is a mockup and moves to the next iteration (D-177); the contract suites of IF-103, IF-404 and IF-405 run only their mock side (TD-23); the script check is off in the deployed stack (`sandbox_backend: none`, TD-24); the smoke tests of `tests/smoke/` are run in Deploy, not in the merge gate (TD-25); open deferrals TD-01 to TD-04, TD-06 to TD-11; see `specs/mia/deferred.md` and `specs/mia/goals/G-V1/release-notes.md`.

### Release record
- Verified with accepted deviations (verification report approved 2026-11-01, D-183). Merged into master by fast-forward, commit `67818fb`, tag `v0.1.0`. The merge gate ran locally (stages 0 to 3 green, no CI); the field validation (VAL-001, VAL-003 to VAL-006) and the stage 4 checks are open.
