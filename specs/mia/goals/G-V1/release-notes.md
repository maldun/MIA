# MIA v0.1.0 (<<date of the tag>>): release notes (DRAFT, version proposed)

## New
- MIA as a multi-user chat with a 3D character and a local voice: one shared MIA for a handful of trusted people, answers streamed sentence by sentence with the sender shown, stop, queue position, shared history, regenerate and speak again, on desktop and phone.
- Accounts: the owner creates them, login with a rate limit, salted slow password hashes, HTTPS in the home network or the tailnet.
- The character: expressions, gestures and mouth follow the mood and the voice; the chat works without the character.
- The voice: answers synthesised on the host with the anime effect and played sentence by sentence in the browser; voice lines per mood; mute and stop per device.
- Workflows as library data with specifications and versions, the pipeline runner with budgets, tools behind one door with a sandbox, a run log that can be replayed and explained, the evaluation harness behind IF-105.
- A storage layer behind one interface (files, and PostgreSQL in the code), a PostgreSQL service in the compose stack, backup and restore of the data folder and the database, a compose stack with one configuration file. **The app itself still keeps its state in files**; moving it to PostgreSQL is deferred (NFR-8, CON-7, TD-21).

## Changed
- The chat runs on the pipeline runner (skill `chat` v2); memory writing is a skill (`memory_write` v7).

## Fixed
- Findings of the node verifications are closed with tests that fail on the old code; the list is in the verification report of each node.

## Resolved feedback
- None. FB-01 to FB-06 are triaged for the next iteration.

## Goal
- G-V1: MIA runs as the decomposed multi-user system of the approved HLS; exit criterion VAL-001 and VAL-003 to VAL-006 (field validation, still to be done); out of scope: N-5 Graph app and FR-22 (D-177), FR-34, FR-35, the review entry (VAL-002 moved to the next goal), the items in `specs/mia/goals/G-V1/goal.md`.
- Provisional values to be settled in validation: none (no `Provisional:` line in the requirements of the goal, verification report and `validation-plan.md`).

## Known issues and open deferrals
- Failing test files and skips by design: see the merge request.
- Not met or not held: NFR-8/CON-7 (state in PostgreSQL, TD-21); the red-team half of TC-MIA-006 (TD-22); no `test-requirements.md` yet; the 36 eval-suite files added without an amendment are to be confirmed by the owner (D-180).
- Stage 4 checks not decided: TC-MIA-002, -003, -009, -011, -019, -022, -024, -025, -028 (TD-12 to TD-20, D-178). No claim about answer quality, speed on the phones or memory quality is made by this release.
- Open deferrals:

| Record | Subject | Requirement | Trigger |
|---|---|---|---|
| TD-01 | The status card is not tested in a browser and is gone after a reload | REQ-CLV-023 | the chat mock server sends `task_status` and files events, or the Plan of FB-01, or 2026-12-31, whichever first (the browser harness exists since D-141; D-172) |
| TD-02 | The Files tab is not tested in a browser | REQ-CLV-024 | the chat mock server sends `task_status` and files events, or the Plan of FB-01, or 2026-12-31, whichever first (the browser harness exists since D-141; D-172) |
| TD-03 | Tokens on the card are an estimate | REQ-WFM-032 | the first review run that ends at the cap of tokens, or 2026-12-31, whichever first |
| TD-04 | The glue of lookup and search stays in the core | REQ-WFM-039 | the fourth skill is added, or 2026-12-31, whichever first |
| TD-06 | The workflow library folder is not there yet | REQ-GTB-004 | root task T-10, or 2026-12-31, whichever first |
| TD-07 | Judge calibrations are not loaded yet | REQ-EVL-003 | the first eval target with a judge, or 2026-12-31, whichever first |
| TD-08 | Older eval suite kinds run the in-process Core | REQ-EVL-011 | the Plan of FB-03, or 2026-12-31, whichever first |
| TD-09 | Deleting the chat history after a confirmation | REQ-CHA-005 | the first request to delete a history, or 2026-12-31, whichever first |
| TD-10 | Persona check dialogues (AC-8) | REQ-CHA-008 | the first iteration after the field test |
| TD-11 | The voice goes through IF-204 | REQ-VOI-001 | the Plan of the next iteration, or 2026-12-31, whichever first |
| TD-12 | Verify before asserting; lookup (TC-MIA-002) | FR-9, FR-10 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-13 | Literature review quality (TC-MIA-003) | FR-11, FR-12, NFR-4 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-14 | The skill path (TC-MIA-009) | FR-20 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-15 | Adaptation to negative feedback (TC-MIA-011) | FR-29 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-16 | Speed and frame rate (TC-MIA-019) | NFR-7 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-17 | Cost of the first try; comparing variants; learned choices (TC-MIA-022) | NFR-2, FR-17, FR-18 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-18 | Memory that improves (TC-MIA-024) | FR-14 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-19 | Speech rules (TC-MIA-025) | FR-15 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-20 | Estimate before a run (TC-MIA-028) | FR-33 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-21 | The state is in PostgreSQL | NFR-8, CON-7 | the Plan of the next iteration, or 2026-12-31, whichever first |
| TD-22 | Red-team cases of the untrusted inputs | NFR-3 | the Plan of the next iteration, or 2026-12-31, whichever first |

## Agent changes
See the merge request ("Agent changes"): MP-light unchanged, skills and pipelines as listed there, no eval result, no new baseline.

## For deployment (Phase 6)
- Artifact: the mia image, built from the tag in CI (<<CI run link>>); `deploy/build.sh` is missing, the build is `deploy/Containerfile`.
- Target: the owner's host (Fedora, RX 7800 XT 16 GB, podman) and the phones in the tailnet.
- Smoke tests: `tests/smoke/` (SMOKE-GATE-001, -002, SMOKE-MIA-nnn per the verification report).
- Rollback: the previous image and, with it, the previous skill versions and model digests (preflight records them).
