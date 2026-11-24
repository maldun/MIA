# Handover: G-V4.BUILDER Plan waits for RUN and CONTEXT (D-521, 2026-11-24)

Replaces `handover-2026-11-24-g-v4-builder-plan-next.md`, which is kept as history.

Branch `explore/builder-workflow` (worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/builder-workflow`) holds the TLS amendment D-520 and the step 0 decisions D-521 (commit `c474b299`). **Not pushed yet:** the owner runs `git push -4` there. BUILDER's line of work `goal/v4.builder` does not exist yet.

## First thing to do
BUILDER's Plan resumes **only when the plans of G-V4.GRAPHAPI.RUN and G-V4.CONTEXT are approved** (D-521 (1)).
1. Look at the Plan row in the Phases tables of `specs/mia/goals/G-V4.GRAPHAPI.RUN/goal.md` (on `goal/v4.graphapi.run`) and `specs/mia/goals/G-V4.CONTEXT/goal.md` (on the newest branch that holds CONTEXT's plan).
2. If either plan is not approved, stop and tell the owner. Do not plan around the gap.
3. If both are approved: create the line of work off `explore/builder-workflow`, not off `goal/v4` (D-521 (4)):
   `git worktree add .claude/worktrees/builder -b goal/v4.builder explore/builder-workflow`
   Then merge in what BUILDER needs from RUN and CONTEXT only through git, after asking the owner which branches are final.

Read `CLAUDE.md`, this file, `specs/mia/goals/G-V4.BUILDER/top-level-spec.md` (approved D-390, amended D-520) and `goal.md`, and D-379 to D-391, D-473, D-520 and D-521 in `specs/mia/review-log.md`. Load `dev-workflow`, `plan-phase`, `agent-app`, `agent-app-plan` and `decomposition` (N-6 is a new node).

## Decisions of this session (D-521, owner, 2026-11-24)
| # | Question | Answer |
|---|---|---|
| 1 | Dependency order with RUN and CONTEXT | (b) wait until both plans are approved, then plan against their approved interfaces |
| 2 | NFR-23 for the workflow | equivalence check: the workflow gives the same proposals as `option1.py` / `option_df.py` on the same documents, model and settings, so the owner's marks carry over; if it does not, a new sample is marked |
| 3 | When samples A and B are marked | by the owner during Plan, before step 4 (eval material); the owner may start now |
| 4 | Where the branch starts | `goal/v4.builder` off `explore/builder-workflow` |

Still open for step 0 when Plan resumes: the owner confirms OC-1 to OC-5, and the split check (9 TLS items; recommend keeping it together, record it in `goal.md` `Split check`).

## State
| Item | State | Where |
|---|---|---|
| Explore | done; TLS approved 2026-11-20 (D-390), amendment D-520 approved 2026-11-24 | `top-level-spec.md` |
| Plan | open, waiting (D-521) | `goal.md` Phases table |
| Scope | FR-41, FR-42 in; TLS items FR-98 to FR-105, FR-110, NFR-23 to NFR-25; OC-1 to OC-5 | `goal.md` |
| Realisation (D-520) | the builder is a workflow on MIA's runner, with checks and a page in the web app; N-6 is its own node with no container of its own; the owner's confirmation is not a step of the workflow | TLS FR-110, 3.3; HLS N-6 row |
| Engine | spike C option 1: chunks at sentence borders (at most 3000 characters), one model step with a JSON schema, a quote per proposal, every name and quote checked against the whole document; LightRAG dropped (7.7 % invented, bar 5 %) | `explore-skill-rework/spikes.md` |
| NFR-23 evidence | items and relations, light model: 113 right, 0 invented of 120 (branch `explore-n6-sample`) | `explore-skill-rework/n6-sample-plan.md` |
| Samples A and B | drawn, **not marked**: A definitions and facts, light model, 120 cards (gates D-382); B items and relations, full model, 128 cards (gates D-384) | branch `spike/builder-samples`: `specs/mia/goals/G-V4.BUILDER/nfr23-sample-plan.md` section 6, pages `explore-skill-rework/forms/nfr23-a-marking.html`, `nfr23-b-marking.html` |
| Node N-6 | not in `decomposition.yaml`, no `specs/mia/nodes/N-6-*` folder, no eval suite, nothing in `eval-spec.md` | – |
| Model | `ContextGraphBuilder` (`architecture.sysml:151`) still says "its own standalone node N-6": fix it in Plan (D-520) | – |

## Dependencies on 2026-11-24
| Goal | Why BUILDER needs it | Phases |
|---|---|---|
| G-V4.GRAPHSTORE.CORE | context graphs in the stored form | done |
| G-V4.GRAPHAPI.RUN | the run of a stored graph: the builder runs as one (D-473, D-520) | Plan open (requirements drafted on `goal/v4.graphapi.run`) |
| G-V4.CONTEXT | editing; the rules for categories and budgets (FR-104) | Plan open |
| G-V4.VIEW | the viewer shows the builder's workflow (FR-110) and links to its page | Verify done, Commit next |

## Plan, in order (plan-phase with agent-app-plan), once it resumes
0. **Goal and scope:** OC-1 to OC-5 confirmed, split check recorded, `Depends on` checked against the approved RUN and CONTEXT plans.
1. **1a HLS part:** N-6 as a workflow in the backend container (D-520); the page in the web app, reached from the graph viewer (D-381); dependencies; hard bounds only (e.g. the limits of FR-103 as settings).
2. **Decomposition:** add N-6 to `decomposition.yaml` (protected: needs an approved amendment). Interfaces to N-2.4.1 (runner), N-3.2 (context tables) and N-5 (viewer), each with a mock and a contract suite before any code, taken from RUN's and CONTEXT's approved interfaces.
3. **1b requirements** (EARS, atomic, grouped, batches of 5 to 7) refining FR-98 to FR-105 and FR-110. SysML agent view: each step of the builder's workflow as `@ModelStep` (schema, tools none, budget); documents `@Untrusted`; TB-context as `@TrustBoundary`.
4. **Eval material before any prompt:** a suite from the owner's marks (spike C option 1, the n6 sample, samples A and B); a holdout split; model pins (`gemma4:12b-it-qat` default, `gemma4:26b` by choice, NFR-24); NFR-23 criteria with the bar fixed (at least 120 marks per sample, at most 4 invented, at least 91 right); **the equivalence check of D-521 (2)** as a criterion with its test requirements (same documents, model, settings as `option1.py` / `option_df.py`). Agents never label and never open holdout cases.
5. **Threat model and red-team cases** for NFR-25: instruction-like text (AC-3), "confirm all items", text that asks to ignore the checks.
6. **Budgets** (tokens, time per document, VRAM at `num_ctx` 8192) checked with Z3; the item and seconds limits of FR-103.
7. **Test spec** with scenarios, test requirements, red tests, `plan.md`; review in batches with `req_review.py`. No `plausibility.yaml` (D-421).

## Shared state
- The Ollama server is shared: before an eval or spike run, check `ListAgents` and tell running sessions.
- `explore/builder-workflow` and `goal/v4.view` both change `review-log.md` and `high-level-spec.md`; whichever merges into `goal/v4` second has a small conflict there.
- Worktrees go to `.claude/worktrees/<topic>`; only the owner pushes (`git push -4`).

## Next free numbers
- Decisions: D-522 (BUILDER's block is D-520 to D-539).
- Top-level items: FR-111 (FR-106 to FR-109 reserved for the parked G-V5); NFR-26.
- Amendments: A-176, but VIEW's Commit handover also names A-176. Check `specs/mia/amendments/` on every branch before taking one.
- Test-requirement and check IDs for N-6: new prefixes, chosen in Plan by `references/conventions.md`.
