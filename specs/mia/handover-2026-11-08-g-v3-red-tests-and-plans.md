# Hand-over for the next G-V3 session (written 2026-11-08, night): red tests and plans drafted, decisions open

For the session that continues **G-V3** (subgoals G-V3.PANEL and G-V3.CHAT) on branch `goal/v3`, worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v3`. Start with `CLAUDE.md`, the goal records (`specs/mia/goals/G-V3/goal.md`, `G-V3.PANEL/goal.md`, `G-V3.CHAT/goal.md`, all Status `Agreed`), the two plans `goals/G-V3.PANEL/plan.md` and `goals/G-V3.CHAT/plan.md`, then this file. The earlier hand-overs `handover-2026-11-08-g-v3-plan-review.md` (how the owner works, the ID ranges) and `handover-2026-11-08-g-v3-contracts-done.md` (cases, plausibility, contract change, goal records; its "Open" list is superseded by this file) stay valid for what they describe. Load the skills `dev-workflow`, `agent-app`, `plan-phase`, `agent-app-plan` (and `agent-app-implement` once the gate is passed).

Phase: **Plan, Step 5 drafted**, supervised, both subgoals. Reviewer name in the review log: **maldun**. Nothing is pushed (the push and the merge are the owner's). **One session at a time in this worktree** (a second session edited requirements and the model once; the owner closed it).

## Commits of the last sessions (all on `goal/v3`, newest first)
| Commit | What |
|---|---|
| (next commit) | scorer tests TC-CHA-064..067, stubs `digest_score.py` and `Harness._digest`, test-spec rows and TR-CHAT-008 |
| `e9f62d3` | note on the harness target `digest` and the scorer, approved |
| `e71f4a6`, `ecb72fe` | dark-theme browser runner (driver fixed), A-143 installed (IF-302 v9, IF-101 v17) |
| `73a4962` | A-143 and payloads, D-306, starter flag, hand-over |
| `d7a75eb` | `plan.md` of G-V3.PANEL (10 tasks) and G-V3.CHAT (6 tasks), drafts |
| `e705709` | red tests batch 3: the Skill run view in a browser (12 tests), stub server, TR-PANEL-001 names the harness |
| `72bce48` | red tests batch 2: JS model `skill-run-model.js` (7 tests) |
| `f7953ca` | red tests CHAT: TC-CHA-040..048, 050..052, 055..063 (21 tests) with the stubs `skill_digest.py`, `ChatService.skill_turn`, `model_history` |
| `2f8867f` | red tests batch 1: TC-RTB-007 and TC-WFM-130..135, 137, 138 with the stub `skill_runs.py` |
| `a176085`, `9650df8`, `e2c3d69` | hand-over, goal records Agreed (D-305), REQ-BE-078 and the step budget |
| `ed17ee5`, `6218bf5`, `37d9920`, `0212037` | contract change IF-101 v16, IF-201 v3, IF-302 v8, IF-102 v4; HLS (A-131); plausibility; EV-skill_turns suites and baseline |

## State of Step 4 (red tests)
| Part | State |
|---|---|
| TC-RTB-007, TC-WFM-130..135, 137, 138 | written, installed, red (stub `skill_runs.py` raises NotImplementedError) |
| TC-CHA-040..048, 050..052, 055..063 | written, installed, red (stubs `skill_digest.py`, `ChatService.skill_turn`, `model_history`) |
| TC-CLV JS part (030, 031, 032, 033, 034, 039, 044) | written, installed, red (stub `skill-run-model.js` throws) |
| TC-CLV browser part (030, 032, 035, 036, 037, 040, 041, 042, 043, 045, 046, 047) | written, installed, red (all fail at the first missing page hook); the assertions behind the first lookup are not yet checked against a page |
| **TC-WFM-136**, **TC-CLV-038** | **not written**: after the T-03 spike of PANEL (the events of a skill today; how a test starts the real backend on file-backed storage with a seeded run record) |
| scorer and target of EV-skill_turns: TC-CHA-064..067 (`tests/acceptance/test_digest_score.py`) | written, installed, red (stubs `digest_score.py`, `Harness._digest` raise NotImplementedError); note `goals/G-V3.CHAT/eval-target-note.md` approved; new draft spec items TC-CHA-064..067 (N-2.2 test-spec) and TR-CHAT-008 for the owner's review |
| AC-39 integration check | not written (CHAT T-06) |

How the red tests were made (use the same way): the permission classifier blocks edits of `tests/acceptance/`, `tests/helpers/` and `contracts/` by the agent. Write the files in a sandbox copy in the scratchpad, run them red against the stubs, check the assertions against a throwaway reference implementation, store the files as a payload in `specs/mia/goals/G-V3/red-tests/payload/` (contract change: `.../contract-change/payload/`) and let the owner run `install.py [--do]` there. The owner installed all payloads; `install.py` lists nothing as changed now. Interface notes the owner approved: `goals/G-V3.PANEL/run-recorder-interface.md`, `skill-run-view-interface-note.md` (eight exports, not six: `applyStatus` and `controlAction` were added), `goals/G-V3.CHAT/digest-step-interface.md`.

## Decided at the end of the session (D-306) and what is still to do for it
| Decision | Result | Still to do |
|---|---|---|
| `elements` in the run record | amendment **A-143** (IF-302 v9 optional field, IF-101 v17 run record, mock and suites red first in the sandbox, all mock variants green) | the owner installs `specs/mia/goals/G-V3/contract-change-2/install.py --do` (5 files); then run the four contract suites |
| dark theme of TR-PANEL-001 | the browser driver and runner in the payload run the eight scenarios of TR-PANEL-001 in both themes and refuse a dark run that is light | the owner installs `specs/mia/goals/G-V3/red-tests/install.py --do` (2 files); then run `python3 tests/acceptance/test_skill_run_view_browser.py` (a few minutes): all 12 must fail at the first missing hook in both themes; **not yet run** (the classifier blocked the sandbox copy of `tests/helpers`, so the new driver passed a syntax check only) |
| `"starter": true` in the two `suite.json` of `skill_turns` | done by the owner; `test_harness.ShippedSuites` passes | – |
| rule `both` of REQ-CHA-053 and 054 | kept; the sign test against the empty baseline is reported NOT DECIDED in Verify and the owner decides from the bounds | note it in the verification report |

## Open (in this order)
1. Install the two payloads above and run the four contract suites and the browser tests (see the table). Then commit the installed files (message: `test: ...` for the contract amendment and the dark-theme runner).
2. **EV-skill_turns target and scorer (CHAT T-04):** the note is approved (2026-11-08) and the scorer tests are installed; the code follows in T-04; after it the owner sets `"target": {"kind": "digest"}` in the two `suite.json` (one-line command, no case text) and creates `eval/labels/`; `faithful` is false after a failed hard check even without a label (refinement of the note, TR-CHAT-004).
3. **Reviewed and marked approved on 2026-11-08 (one by one):** TR-PANEL-001 (with the harness versions), TR-CHAT-008, TC-CHA-064 to 067. Every G-V3 requirement, check and test requirement is now reviewed. Not rows in the review log: the validation criteria VAL-012 and VAL-013 (to be settled by the owner at the gate or in Validate).
4. **The two plans are reviewed and approved** (D-307 PANEL, D-308 CHAT, task by task; one plan each; the one call in `communicator.py` is allowed for CHAT T-03). Left in their open lists: TC-WFM-136 and TC-CLV-038 (after the PANEL T-03 spike), the AC-39 integration check (CHAT T-06), and after CHAT T-04 the target line in the two `suite.json` and `eval/labels/`.
5. After approval: protect the paths (deny rules in `.claude/settings.json` for `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `test-requirements.md`, `stages.yaml`, `plausibility.yaml`, `deferred.md`), tag `plan-baseline` (ask for the name of the iteration tag), run the gate checks.
6. The CHAT goal shows the `goal_check` warning GL11 (29 requirements in scope, no subgoals) after the scope rows were added; its Split check already says "keep together"; adding a row sends the approved goal back into review: the owner decides.
7. `REQ-FE-032` has no marked test (the browser tests do not carry its marker); the `.mjs` tests carry the TC id in the title only, as the old JS tests do.

## Checks (status at the end of the session)
```
python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia          # GL1 (D-271) and GL11 on CHAT
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests   # 545 errors, none of G-V3 (old, D-270)
python3 ~/.claude/skills/plan-phase/scripts/req_review.py --spec-dir specs/mia --tests-dir tests status   # changed since review: TR-PANEL-001 (ours), TC-WFM-047 and TR-MODEL-003 (not ours)
python3 ~/.claude/skills/agent-app/scripts/agent_check.py --spec-dir specs/mia --eval-dir eval   # 6 errors: REQ-WFM-059 (A2), THR-011 (A8), not G-V3
python3 -I tools/gen_node_requirements_model.py . && python3 -I tools/check_sysml_model.py . && bash tools/check_sysml.sh
/home/maldun/prog/Python/venvs/mia312/bin/python -m unittest discover -s tests      # about 8 minutes; the new red tests fail on purpose
node --test "tests/js/*.test.mjs"                                                    # the 7 new tests fail on purpose
python3 -I specs/mia/goals/G-V3/red-tests/install.py                                 # lists nothing as new or changed
```
Known failures of the last full unit run (2071 tests, before the red tests were installed): `test_tailscale` (`remote.sh up` times out after 30 s, not touched by G-V3, not checked on master) and `test_harness.ShippedSuites` (item 3, after the `expect` fix of the suites).

## Rules that bit in this session (keep)
- **The holdout:** no script of the agent opens `eval/suites/*.holdout/` (the retag dry run once printed only counts; the classifier then blocked a similar dry run). Scripts for the suites are run by the owner.
- **`tools/apply_plausibility.py` is not run** (it rewrites the whole record: 39 hand-added ratings would go, 437 dates would change); items are added by hand in the tool's format.
- Changing the text of an approved item sends it back into review (fingerprint): say so and ask (done for the goal scope rows, REQ-BE-078, TR-PANEL-001).
- Goal Status values: Proposed, Agreed, In progress, Verified, Validated, Closed, Dropped (`Approved` is invalid).
- Typed into a normal terminal, a leading `!` negates the exit status; it is for the Claude Code prompt only.
- A stub must not make a test pass: the stub of `skill_digest.py` has no `tools` and `prompt` attribute on purpose.

## Not touched
The voice path, TD-11, A-130, FR-43, the graph editor, everything of G-V2, master, `deferred.md` (TD-01 stays on REQ-CLV-023 until REQ-CLV-023 is retired in PANEL T-10), `plausibility.yaml` ratings of other goals.
