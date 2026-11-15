# Hand-over for the next G-V3 session (written 2026-11-08): Plan Step 1b and 3 reviewed, cases and contract step open

For the session that continues **G-V3** (Skill run view and spoken-only chat; subgoals G-V3.PANEL and G-V3.CHAT) on branch `goal/v3`, worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v3`. Start with `CLAUDE.md`, the goal records `specs/mia/goals/G-V3/goal.md`, `goals/G-V3.PANEL/goal.md`, `goals/G-V3.CHAT/goal.md`, `specs/mia/amendments/A-131-note.md`, then this file. Load the skills `dev-workflow`, `agent-app`, `plan-phase`, `agent-app-plan`, `decomposition` (they are under `~/.claude/skills`).

State at the end of the session: **45 commits on `goal/v3` since master, last `291f50f`, working tree clean, nothing pushed** (the push and the merge are the owner's). Phase: Plan, supervised, both subgoals. Reviewer name in the review log: **maldun** (the owner asked for it; the first 12 rows of the PANEL review were changed from "Stefan Reiterer" at the owner's request).

## How the owner works (keep doing this)
- Decisions come as a questionnaire (`AskUserQuestion`, up to 4 questions per round, recommended option first), then the steps that apply the answers.
- Reviews of CHAT were **one requirement per question, "split as needed"**; the owner decides each one. PANEL was reviewed in batches of 4 to 8. Do not mark anything approved without the owner's answer.
- Sizes are **relative** (shares of the viewport) and **configurable per user in the browser**, not pixels in a settings file (D-300 and after).
- "The owner's decision beats my reading": ambiguity or a conflict means stop and ask.

## Decisions of the session (details in `specs/mia/review-log.md`, rows D-300 to D-303)
- **D-300** layout kept: large character box left, chat right, the Skill run view a compact strip across the full width below both; phone: character, chat, view. "The page does not scroll" only on the wide screen. The sizes follow the mockup (`specs/mia/explore-skill-rework/forms/skill-run-view-mockup.html`, on master).
- **D-301** the name G-V3 stays; the graph editor (FR-43) is out of scope.
- **D-302** A-131, A-140, A-141 approved (also REQ-WFM-135, REQ-RTB-007, TC-WFM-135, TC-CLV-039, TC-RTB-007, TR-PANEL-006).
- **D-303** A-142 approved, THR-012 approved, REQ-CHA-008 and 014 revised (rev B), REQ-CHA-054 widened, REQ-CHA-049 with 6 injection cases per split, TR-CHAT-001 at the pin options (temperature 0, seed 7; repeats = stability; VAL-013 checks real use).
- Not in the log but decided in the chat: "deleting the chat history" means a delete of `history` records in the storage (no operation exists today); the strip shares are a per-user browser setting with defaults 16 % and 34 % (strip 12 to 40 %, Full run part 20 to 60 %); the strip content scrolls inside when it does not fit; 44 px targets only on the phone layout; `Files:` suffix of `chat_done` dropped; `paused` and `done` stay beside the new `state`; per-skill elements are label and text pairs (REQ-CLV-044, REQ-WFM-138); table `skill_runs` is new in IF-302 (REQ-RTB-007).

## What exists now (all new requirements are `Draft` in the files; the review state is in `review-log.md`)
- **PANEL:** REQ-FE-032; REQ-CLV-024, 030 to 047 (N-1.1); REQ-WFM-031, 036, 038, 039 (reworded), 130 to 138 (N-2.3, group RV); REQ-RTB-007 (N-3.3). Checks TC-CLV-030 to 047, TC-WFM-130 to 138, TC-RTB-007 with scenarios; TR-PANEL-001 to 007; VAL-012; amendments A-131, A-140 (IF-101 v16), A-141 (IF-302 v8, IF-102). **All reviewed and approved.**
- **CHAT:** REQ-BE-078; REQ-CHA-040 to 063 (N-2.2, groups ST, UT, BG, SQ), REQ-CHA-008 and 014 rev B; checks TC-CHA-040 to 048, 050 to 052, 055 to 063 and EV-skill_turns; TR-CHAT-001 to 007; VAL-013; A-142 (IF-201 v3); THR-012 and TB-result in `threat-model.md`; `SkillDigestStep` in `architecture.sysml` (criterion REQ-CHA-049, 053, 054; tokenBudget 4096; threats THR-012); `eval-spec.md` rows (suite, criteria, error rates, seven case categories); glossary entry "faithful (summary)". **All reviewed and approved.**
- Eval criteria (fixed, never changed to get a PASS): suite EV-skill_turns, pin MP-light, 3 repeats, split holdout. REQ-CHA-049 pass min 1.0, n 6, fold all, false alarm 1.30 %; REQ-CHA-053 faithful min 0.85, low 0.70, n 24, false alarm 1.34 %; REQ-CHA-054 persona min 0.80, low 0.70, n 24, false alarm 1.34 %. Suite size 24 dev and 24 holdout (7 categories, 3 per split each, injection 6).
- **ID ranges this session:** D-300 to D-319 (used 300 to 303), A-131 and A-140 to A-149 (used 140, 141, 142), TD-70 to TD-79 (none), REQ-CLV-030 to 049 (used to 047), REQ-CHA-040 to 059 (used to 063: 060 to 063 beyond the range because of the splits; G-V2 reserves no REQ-CHA), REQ-WFM from **130** (the owner's 080 to 099 overlaps G-V2's reserved 071 to 129 in `goals/G-V2/parallel-work.md`), REQ-FE-032, REQ-BE-078, REQ-RTB-007 (assigned by the owner), VAL-012 and 013, TR-PANEL-, TR-CHAT-.

## Open (in this order)
1. **Cases for EV-skill_turns:** draft 24 dev and 24 holdout cases by category in `specs/mia/eval-drafts/skill_turns.jsonl` (short, long in pieces, failed, stopped, no phases, table-heavy, injected instruction with 6 per split), 5 to 10 at a time; the owner labels truth, faithful and persona (`label:people`, a note per case) and moves them into `eval/suites/skill_turns` and `skill_turns.holdout`. Never read or run the holdout as the coding agent. Red-team cases use the five strings of TR-PANEL-005 and get RT numbers when labelled. This closes `agent_check` A3 and A8 (the only remaining errors of the CHAT items).
2. **Baseline** of today's behaviour on the pin (dev and holdout, 3 repeats) with the harness; needs Ollama; `eval/baselines/` is protected.
3. **Plausibility:** PANEL is rated (`goals/G-V3.PANEL/plausibility-decisions.yaml`, 33 items, REQ-CLV-041 questionable with a probe and accepted risk) but **not applied**: `tools/apply_plausibility.py` reads the shared `specs/mia/plausibility-proposal.yaml` and rewrites `plausibility.yaml`. Apply after the rebase on master (merge the proposal and decisions of the goal folder into the shared files, run the tool with `--by maldun`, then `req_plausibility.py`). CHAT has no proposal yet: write `goals/G-V3.CHAT/plausibility-proposal.yaml` after the cases exist (eval criteria rest on the baseline).
4. **Contract-change step** (A-131, A-140, A-141, A-142 are approved, nothing of the protected material is changed yet): `high-level-spec.md` (FR-46 line 95, FR-34, FR-35, AC-30, AC-39), `glossary.md` ("Skill run view"), `deferred.md` (TD-01 wording), `contracts/IF-101` (v16), `IF-201` (v3), `IF-302` (v8), `IF-102` table list, their mocks in `tests/helpers/mocks` and contract suites in `tests/acceptance/contract` (suite red first). These are protected or parent files; ask the owner before touching them and coordinate with the G-V2 session (see below).
5. **Goal records:** mark G-V3, G-V3.PANEL, G-V3.CHAT reviewed (`req_review.py` offers G-V1 first; mark by name). Phases tables say "Plan in progress".
6. **Step 4 (red tests) and Step 5 (`plan.md`)** for both subgoals, in a session of their own (local-coder may type the test files). In Step 4 name the font and the Chromium version of the harness in TR-PANEL-001 (agreed). Note for tests: the `Files:`/`skill_run` details are in A-140, the link form is `[Open in the Skill run view](#run=<id>)`.
7. **Stop-and-report items still open:** the weak red-team criterion of REQ-CHA-049 (miss 22 % at n 6, accepted by the owner); `req_plausibility` reports the 33 PANEL items as not recorded until item 3.

## Checks (run before every gate; status at the end of the session)
```
python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia          # only GL1 (two open iteration goals), explained by D-271
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests   # no error on any G-V3 id; ~500 old errors from before (D-270)
python3 ~/.claude/skills/plan-phase/scripts/req_lint.py specs/mia/requirements.md $(find specs/mia/nodes -name requirements.md) --glossary specs/mia/glossary.md
python3 ~/.claude/skills/agent-app/scripts/agent_check.py --spec-dir specs/mia --eval-dir eval      # A3 and A8 for EV-skill_turns / THR-012 until the cases exist
python3 -I tools/gen_node_requirements_model.py .    # regenerates the requirement block of architecture.sysml after every requirement change
python3 -I tools/check_sysml_model.py . && bash tools/check_sysml.sh
python3 ~/.claude/skills/plan-phase/scripts/req_review.py --spec-dir specs/mia --tests-dir tests status
```
Known lint leftovers that are not G-V3 findings: REQ-CHA-008 and 014 have no Group and are 43 and 44 words after rev B; REQ-WFM-031, 038, 039 are long and have two "shall" as before.

## Collisions to expect at the rebase on master (the G-V2 session works there)
- `specs/mia/architecture.sysml`: the requirement block is generated; take master's version and run the generator, then check_sysml. My hand-written change: `SkillDigestStep` (doc, tokenBudget 4096, criterion, threats).
- `nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md` and its test-spec: G-V2 appends at the end too (my section "Iteration 2 (goal G-V3.PANEL ...)" with its own groups table).
- `review-log.md` and `test-requirements.md` merge with `union`; `test-spec.md` (root) VAL rows: VAL-012 and 013 are mine, VAL-007 to 011 are G-V2's.
- Approved requirement text never merges with `union`; a conflict there is the owner's.
- `plausibility.yaml`: untouched on this branch, see item 3.

## Pitfalls met in this session
- A helper that opened a file for writing before reading it truncated four requirement and test-spec files once (caught by the checks, restored from the commit). Read first, write second, and run the checks after every scripted edit.
- Changing the text of an approved requirement sends it and its check back into review (fingerprint); say so to the owner and ask again.
- `req_review.py` does not batch requirements without `Group:` (the N-1.1 file has no groups table); the CLV items were presented outside the tool and marked by id.
- The page has no way to receive settings from the backend today; that is why the sizes are a browser setting.

## Not touched
The voice path, TD-11, A-130, FR-43, the graph editor, everything of G-V2, master, `eval/suites`, `eval/baselines`, `tests/acceptance`, `tests/helpers`, `contracts/`, `deferred.md`, `plausibility.yaml`, `high-level-spec.md`.
