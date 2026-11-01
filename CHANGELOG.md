# Changelog

## [Unreleased] – v0.1.0 (proposed), G-V1 first version of MIA

### Added
- Multi-user chat with sender, streaming, stop, queue, shared history; accounts and login; the 3D character with expressions, gestures and mouth; the local voice with the anime effect; workflows as library data with versions; the pipeline runner with budgets, tools and sandbox, the run log; the evaluation harness behind IF-105; a storage layer with a PostgreSQL service and backup and restore (the app's state stays in files, TD-21); the compose stack.

### Changed
- The chat runs on the pipeline runner (skill `chat` v2).

### Known limitations
- NFR-8/CON-7 (state in PostgreSQL, TD-21) and the red-team half of TC-MIA-006 (TD-22) are deferred; nine stage 4 checks are deferred (TD-12 to TD-20); the Graph app is a mockup and moves to the next iteration (D-177); open deferrals TD-01 to TD-04, TD-06 to TD-11; see `specs/mia/deferred.md` and `specs/mia/goals/G-V1/release-notes.md`.
