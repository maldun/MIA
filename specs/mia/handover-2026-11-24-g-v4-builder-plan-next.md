# Handover: G-V4.BUILDER Explore amended (D-520); Plan waits for RUN and CONTEXT (D-521, 2026-11-24)

Branch `explore/builder-workflow` (worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/builder-workflow`, pushed) holds the TLS amendment D-520, approved by the owner 2026-11-24. BUILDER's line of work is `goal/v4.builder`. It does not exist yet.

Start a fresh session. Read `CLAUDE.md`, this file, and from `specs/mia/goals/G-V4.BUILDER/`: `top-level-spec.md` (approved D-390, amended D-520) and `goal.md`. Then read D-379 to D-391, D-473, D-520 and D-521 in `specs/mia/review-log.md`. Load `dev-workflow`, `plan-phase`, `agent-app` and `agent-app-plan`: the builder has model steps, so eval suites, model pins, the threat model and budgets apply. Also load `decomposition`, because N-6 is a new node.

## State
| Item | State | Where |
|---|---|---|
| Explore | done; TLS approved 2026-11-20 (D-390), amendment D-520 approved 2026-11-24 | `top-level-spec.md`, checkbox at the top |
| Scope | FR-41, FR-42 in; TLS items FR-98 to FR-105, FR-110, NFR-23 to NFR-25; OC-1 to OC-5 | `goal.md` |
| Realisation (D-520) | the builder is a workflow on MIA's runner, with checks and a page in the web app; N-6 is its own node without a container of its own; your confirmation is not a step of the workflow | TLS FR-110, section 3.3; HLS N-6 row and containers paragraph |
| Engine | spike C option 1: chunks at sentence borders (at most 3000 characters), one model step with a JSON schema, a quote per proposal, every name and quote checked against the whole document; LightRAG dropped (7.7 % invented against the bar of 5 %) | `explore-skill-rework/spikes.md`, interview row 21 |
| NFR-23 evidence | items and relations, light model: 113 right, 0 invented of 120 (branch `explore-n6-sample`); this meets the bar | `explore-skill-rework/n6-sample-plan.md` |
| NFR-23 open samples | runs and draws are done, **the owner's marks are not given yet**: sample A (definitions and facts, light model, 120 cards) and sample B (items and relations, full model, 128 cards) | branch `spike/builder-samples`, `specs/mia/goals/G-V4.BUILDER/nfr23-sample-plan.md` section 6; pages `explore-skill-rework/forms/nfr23-a-marking.html`, `nfr23-b-marking.html` |
| Node N-6 | not in `decomposition.yaml`, no `specs/mia/nodes/N-6-*` folder, no eval suite, nothing about the builder in `eval-spec.md` | – |
| Model | `ContextGraphBuilder` (`architecture.sysml:151`) still says "its own standalone node N-6": update it in Plan (D-520) | – |

## Dependencies: state on 2026-11-24
| Goal | Why BUILDER needs it | Phases |
|---|---|---|
| G-V4.GRAPHSTORE.CORE | context graphs in the stored form | done |
| G-V4.GRAPHAPI.RUN | runs from stored graphs: the builder runs as one (D-473, D-520) | Plan open (requirements drafted on `goal/v4.graphapi.run`) |
| G-V4.CONTEXT | editing, the rules for categories and budgets (FR-104) | Plan open |
| G-V4.VIEW | the viewer shows the builder's workflow (FR-110) and links to the builder's page | Verify done, Commit next |

**Decided at Plan step 0 (D-521, 2026-11-24):**
1. **Wait (b):** BUILDER's Plan resumes only when the plans of G-V4.GRAPHAPI.RUN and G-V4.CONTEXT are approved. Check their goal records' Phases tables first; if either is still open, stop and tell the owner.
2. **NFR-23 by equivalence check:** the workflow must give the same proposals as `option1.py` / `option_df.py` on the same documents, model and settings; then the marks carry over, otherwise a new sample. Write this as an eval criterion with its test requirements in step 4.
3. **Samples A and B are marked by the owner during Plan**, before step 4 (the owner may start now; pages on `spike/builder-samples`).
4. **Branch:** create `goal/v4.builder` off `explore/builder-workflow` when Plan resumes (worktree `.claude/worktrees/builder`).

Still to confirm with the owner at step 0: OC-1 to OC-5, and the split check (9 TLS items, GL11: recommend keeping it together).

## Plan, in order (plan-phase with agent-app-plan)
0. **Goal and scope:** confirm OC-1 to OC-5; the split check (GL11: 9 TLS items, so a split is unlikely, but say so); the dependency question above.
1. **1a HLS part for BUILDER:** N-6 as a workflow in the backend container (D-520); the page in the web app, reached from the graph viewer (D-381); dependencies; hard bounds only, e.g. the limits of FR-103 as settings.
2. **Decomposition:** add N-6 to `decomposition.yaml` (a protected file, so this needs an approved amendment). Name its interfaces to N-2.4.1 (runner), N-3.2 (context tables) and N-5 (viewer), each with a mock and a contract suite fixed before any code.
3. **1b requirements** (EARS, atomic, grouped, batches of 5 to 7), refining FR-98 to FR-105 and FR-110. The SysML agent view: each step of the builder's workflow as a `@ModelStep` with schema, tools (none), budget; documents `@Untrusted`; TB-context as `@TrustBoundary`.
4. **Eval material, before any prompt is written:**
   - a suite from the owner's marks: spike C option 1, the n6 sample, and samples A and B once they are marked;
   - a holdout split;
   - the model pins (`gemma4:12b-it-qat` default, `gemma4:26b` by choice, NFR-24);
   - the eval criteria for NFR-23 with the bar fixed: at least 120 marks per sample, at most 4 invented, at least 91 right.

   Agents never label and never open holdout cases.
5. **NFR-23 carry-over (D-521):** an equivalence check against `option1.py` / `option_df.py` (same documents, model, settings) carries the marks over; specify it as an eval criterion with test requirements.
6. **Threat model and red-team cases** for NFR-25: instruction-like text in a document (AC-3), "confirm all items", text that asks to ignore the checks.
7. **Budgets** (tokens, time per document, VRAM at `num_ctx` 8192) checked with Z3; the item and seconds limits of FR-103.
8. **Test spec with scenarios, test requirements, red tests, `plan.md`.** Review in batches with `req_review.py`. No `plausibility.yaml` (D-421).

## Shared state
- The Ollama server is shared. Before an eval or spike run, check `ListAgents` and tell running sessions.
- `explore/builder-workflow` and `goal/v4.view` both change `review-log.md` and `high-level-spec.md`; whichever merges into `goal/v4` second has a small conflict there.
- Worktrees go to `.claude/worktrees/<topic>`; only the owner pushes (`git push -4`).

## Next free numbers
- Decisions: D-522 (BUILDER's block is D-520 to D-539).
- Top-level items: FR-111 (FR-106 to FR-109 are reserved for the parked G-V5); NFR-26.
- Amendments: A-176, but VIEW's Commit handover also names A-176 as its next. Check `specs/mia/amendments/` on every branch before taking one.
- Test-requirement and check IDs for N-6: new prefixes, chosen in Plan by `references/conventions.md`.
