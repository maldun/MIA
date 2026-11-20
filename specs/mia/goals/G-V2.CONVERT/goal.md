# Goal G-V2.CONVERT – Conversion

Drafted 2026-11-07 when the owner asked to split G-V2 into four subgoals for review and build (cut: STORE, MODEL, TRUST, CONVERT).

- Kind: subgoal
- Parent: G-V2
- Statement: Every existing skill runs from its record with the same outcomes on its suite, or stays on the old runner for a written reason.
- Exit criterion: OC-1 and OC-3 (OC-2, snapshots, moved to G-V2.SNAPSHOT by A-159), with the checks of its requirements below; validation: VAL-007 (`specs/mia/test-spec.md`)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v2.convert
- Subgoals: –
- Status: Verified

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given each skill MIA had in v0.1.0, when the owner uses it after conversion, then it gives the same results on its test cases as before, or it stays as it was and the reason is written down | FR-45, OC-1 |
| OC-2 | (moved to G-V2.SNAPSHOT, A-159) Given the skill set at a moment the owner has named, when the owner later changes things and goes back, then everything is as it was and the state before going back is kept too | FR-47, OC-4 |
| OC-3 | Given MIA is started from a fresh copy with one configuration file and one command, when it is up, then everything that worked before still works | NFR-9, OC-5 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| model server with the pins of eval-spec.md | real | equivalence runs on MP-light |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| further cut | keep together | 11 items in scope, one chain | 2026-11-07 |
| REQ-WFM-059 split per skill into REQ-WFM-110 to 115 | keep together | 17 items in scope, one chain, the six new ones share one suite family and one rule | 2026-11-07 |
| snapshots (REQ-WFM-061 to 066, T-CV-05) out of CONVERT | split: new subgoal G-V2.SNAPSHOT | Verify 2026-11-17: the conversion half is ready, the snapshots waited for the contract text (A-121); owner decision 2026-11-18 in the session, A-159 | 2026-11-18 |

## Scope
Ids REQ-WFM-110 to 115 are reserved for this subgoal. Nine skills stay on the old runner in this goal: chat, check_speech, memory_write, summarize and the five review skills; reason (owner, 2026-11-07): they are part of the user interface; they are revisited in another goal (recorded per skill by REQ-WFM-060).

Top-level items it serves: FR-45, FR-47. Requirements by ID (inside G-V2's scope):

| Item | In/Out | Reason |
|---|---|---|
| REQ-WFM-057 | in | |
| REQ-WFM-058 | in | |
| REQ-WFM-059 | in | |
| REQ-WFM-060 | in | |
| REQ-WFM-061 | out | moved to G-V2.SNAPSHOT (A-159) |
| REQ-WFM-062 | out | moved to G-V2.SNAPSHOT (A-159) |
| REQ-WFM-063 | out | moved to G-V2.SNAPSHOT (A-159) |
| REQ-WFM-064 | out | moved to G-V2.SNAPSHOT (A-159) |
| REQ-WFM-065 | out | moved to G-V2.SNAPSHOT (A-159) |
| REQ-WFM-066 | out | moved to G-V2.SNAPSHOT (A-159) |
| REQ-WFM-069 | in | |
| REQ-WFM-110 | in | split from REQ-WFM-059 (owner 2026-11-07) |
| REQ-WFM-111 | in | split from REQ-WFM-059 (owner 2026-11-07) |
| REQ-WFM-112 | in | split from REQ-WFM-059 (owner 2026-11-07) |
| REQ-WFM-113 | in | split from REQ-WFM-059 (owner 2026-11-07) |
| REQ-WFM-114 | in | split from REQ-WFM-059 (owner 2026-11-07) |
| REQ-WFM-115 | in | split from REQ-WFM-059 (owner 2026-11-07) |
| REQ-WFM-143 | in | budgets and stop on the converted path (A-159, F-05 of the Verify; the text is in `amendments/A-159-draft-split-snapshots.md` and not yet in requirements.md, owner review open) |
| IF-301 | in | frozen at G-V2 (A-90, approved 2026-11-07); used through its mock until the provider is merged |
| IF-203 | out | v2 (snapshots) belongs to G-V2.SNAPSHOT (A-159); v1 is used through its mock until the provider is merged |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.3 converter | real | the snapshot store moved to G-V2.SNAPSHOT (A-159) |
| N-2.4.1 pipeline runner | real | old runner side by side |
| G-V2.STORE, MODEL, TOOLBOX | real | merged before this subgoal starts |
| model server (Ollama) | real | equivalence on MP-light |

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|
| – | – | see parent G-V2 |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| – | – | no subgoals |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | HLS of iteration 2 approved 2026-11-05 (D-186) |
| Plan | done | the plan package, drafts of the open plan documents in `drafts/` |
| Implement | done | `implementation-log.md`; snapshots (T-CV-05) split out to G-V2.SNAPSHOT (A-159) |
| Verify | done | `verification-report.md` (2026-11-17, conversion half) and the parent Verify of G-V2 (`../G-V2/verification-report.md`, 2026-11-20): Verified with accepted deviations (TD-86 to TD-90) |
| Commit | done | merged into master by the owner as `054f1d2` (2026-11-16), fixes up to `0251723b` |
| Deploy | open | |
| Validate | open | |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|
