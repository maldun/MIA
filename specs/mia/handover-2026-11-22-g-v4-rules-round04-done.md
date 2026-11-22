# Handover: G-V4.GRAPHAPI.RULES, prototype round 04 built; next the owner's validation, then the high-level spec (2026-11-22)

Read first: this file, `CLAUDE.md`, the previous handover `handover-2026-11-22-g-v4-rules-plan-next.md` (sections 5 and 7 still hold), skills `dev-workflow`, `plan-phase`, `agent-app`. The owner (Stefan Reiterer, maldun) decides every gate.

## 1. Where we are
| Item | State |
|---|---|
| Line of work | **`goal/v4.graphapi.rules`**, cut from `goal/v4` @ `e7847ba5` (D-415 (1)), worktree `/home/maldun/prog/Python/MIA-goal-v4-rules`; merges into `goal/v4` at Commit. Not pushed |
| Prototype round 04 | authorized (D-415 (2)), built (CP17 to CP19), report and validation sheet written; **the owner's validation of the outcome rows is open** (`Validated by` empty); decisions Q-1 to Q-7 taken (D-415) |
| Plan of RULES | not started beyond `goal.md` |

## 2. Round 04 in short (`/home/maldun/prog/Python/MIA-prototype-g-v4/specs/mia/goals/G-V4/prototype/rounds/04/`)
- Branch `prototype/g-v4` @ `cc0a91d1`; `goal/v4` merged in first (`3faa9404`, `graph_model.py` and `graph_tables.py` from `goal/v4`).
- `graph_rules_proto.KINDS` is the one place: `workflow` = eight rules in order, runs; `context` = rules 1, 3, 4, cannot run; unknown kind = `unknown_kind`. CORE's save path (prototype copy) asks `check`; `SaveResult.rules`. Checks: `cp17_check.py` 11, `cp18_check.py` 3, `cp19_check.py` 14 pass; rounds 01 to 03 and the 32 rule-related test files stay green (incl. protected TC-WFM-164/168: **no protected-test amendment is needed for the save path**).
- Findings to carry into the requirements (report, "Findings"): three rule implementations today (doc form stays, Q-6); a rule never raises; a cycle keeps its first step at the end; `named` lists every broken rule's parts (wording amendment of REQ-WFM-146/150, carry V-2/V-3 with it); every entry point checks with the stored kind (the page lost it); old-to-new mapping (no old refusal lost except `max_seconds: 1.0`, 57/1000 newly refused); 500 steps in 1.4 ms.

## 3. Next steps
1. The owner validates round 04 (`validation.md` rows FR-63, FR-64, AC-017, AC-018) and fills `Validated by`; the carry-over rows of `prototype-report.md` are his (`Decided by` style, never pre-filled).
2. High-level spec `specs/mia/goals/G-V4.GRAPHAPI.RULES/high-level-spec.md`: the registry of kinds in N-3.2 (replaces `check_graph`/`context_problems` of `graph_model.py`; `graph_rules.py` stays for the document form, Q-6), the check at the save path, the check route of IF-104 v2 (stand-in against the mock) and the runner of N-2.4.1 before the first step; the hard bound is IF-301's 200 ms for 500 steps (if it is restated at all).
3. Requirements (EARS, grouped, batches of 5 to 7), architecture entries, test spec with scenarios, test requirements, red tests, `plan.md`, binding map; witnesses for AC-017, AC-018.
4. Notes for other subgoals: CODE takes the known-tool check (Q-2); TRANSFER or MIGRATION the read-only listing of an unknown kind (Q-7); MIGRATION retires the document form and its five rule names (Q-6).

## 4. Numbers and rules
- Next free numbers (check again before use): **D-416**, A-170, REQ-WFM-162, REQ-GTB-033, REQ-RUN-036, TC-WFM-179, TC-GTB-037, TC-RUN-036, TC-IF-301-27, AC-41; prototype checkpoints from CP21, assumptions from ASM-9.
- A session isolated in this worktree cannot `cd` into the prototype worktree; plain `git -C /home/maldun/prog/Python/MIA-prototype-g-v4 <cmd>` (one command per call) and the file tools work.
- Untracked `specs/mia/amendments/A-167/A-167.diff` in `../MIA-goal-v4` is a view file: never commit it.

## Start prompt for the next session
> Continue G-V4.GRAPHAPI.RULES. Read `CLAUDE.md` and `specs/mia/handover-2026-11-22-g-v4-rules-round04-done.md`, load `dev-workflow`, `plan-phase` and `agent-app`, work in `/home/maldun/prog/Python/MIA-goal-v4-rules` (branch `goal/v4.graphapi.rules`). If my validation of round 04 is in, start the high-level spec of RULES.
