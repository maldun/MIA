# Hand-over for Plan Step 4 of G-V2.TOOLBOX (written 2026-11-11): contract suites and red tests

Read `CLAUDE.md`, then this file, `plan.md` of this folder, `goals/G-V2/parallel-work.md` and the Step 4 hand-over of MODEL (`goals/G-V2.MODEL/handover-step4.md`, the pattern: stubs in the repo root, fakes in `tests/helpers`, tests with `from markers import mark` and `mark.req(...)`). Line of work `goal/v2.toolbox`, worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox`, last commit before this file: `d779ab4` plus the goal review. Nothing pushed; the owner pushes and merges. Skills: `dev-workflow`, `plan-phase` (`agent-app` does not apply: no model step). Python for every test: `/home/maldun/prog/Python/venvs/mia312/bin/python`.

## State
- Plan Steps 0 to 3 and 5 are done and **reviewed by the owner (maldun, 2026-11-11)**: REQ-WFM-050..056, 067, 090..095, REQ-RTB-008, TC-WFM-050..056, 067, 090..095, TC-RTB-008, TR-TOOLBOX-001..006, the goal. Plausibility of REQ-WFM-090..095 and REQ-RTB-008 rated plausible. Master was merged into the branch (STORE, MODEL, TD-11 in master).
- Owner decisions: D-220 (REQ-WFM-092/093 whole, goal kept together), D-221 (A-110: table `transform_meta`, REQ-RTB-008, version at install time, `shipped` a field). Earlier: D1 to D5 of 2026-11-08 (see `plan.md`). Next free ids: D-222 is used by the apply script of A-110; check `tail specs/mia/review-log.md` first; TOOLBOX range D-220..239, A-110..119.
- **Not reviewed here:** REQ-WFM-068, 070 and TC-WFM-068, 070 (CV group, CONVERT's review); TR-TOOLBOX-001 lists them anyway.
- **A-110 is drafted, not installed:** `specs/mia/amendments/A-110-note.md`, `tools/apply_amendment_a110.sh` (look-only by default, tested on a scratch copy, idempotent). It changes `contracts/IF-302` (v8 today, v9 if G-V3's A-141 goes first) and `IF-102` (v4). The owner installs it (`--do`) before the table suite is written. **Open: who takes IF-302 v8, TOOLBOX or G-V3 (A-141)?** The script takes the next free number at install time, so order does not break it, but the suite text must name the right version.

## What Step 4 has to produce (all protected material: the owner's go, deny rules lifted)
1. **IF-203 v1 contract suite for the kind `transforms`** (`tests/acceptance/contract/test_if_203_workflow_library.py` is the v0 suite; add a v1 part or a new module, as MODEL did for IF-301 v2) and its draft of the contract text: A-90 names kinds `skills`, `transforms`, `snapshots`; the `transforms` part (versioned records of ID, version, schemas, code text; `set_trust`, `set_lifecycle`, `get_trust`, `get_lifecycle`) is TOOLBOX's. CONVERT's A-121 note proposes the snapshot part and assumes `get_trust`, `get_lifecycle`, `evidence` on `set_lifecycle`: keep the signatures the same (D-240 of CONVERT: `set_lifecycle(id, lifecycle, author, evidence)`).
2. **IF-302 table suite for `transform_meta`** (`tests/acceptance/contract/test_if_302_record_tables.py`, TC-RTB-008) after A-110 is installed; mock `tests/helpers/mocks/if_302_record_tables.py` gets the table (the owner's go for protected mocks).
3. **Red tests** TC-WFM-050..056, 067, 090..095 in `tests/acceptance/` (`test_toolbox.py` or by topic), with the stubs the plan names (`toolbox.py` in the repo root: `Toolbox(library)`, `import_transform`, `export_transform`, `look_up`, `offer`, `set_trust`, `set_lifecycle`, `run`, `seed_shipped`; stubs return wrong values and never raise, so every test fails on an assertion). **If a test passes before the code exists, stop and report.** TC-WFM-068, 070 are CONVERT's tests; include them only if CONVERT's session agrees (they use the same `Toolbox`).
4. **Helpers** in `tests/helpers/`: a mock of the library part for `transforms` (versions, trust and lifecycle records, refuses unknown values; TR-TOOLBOX-001), a fixed copy of three shipped nodes (one ID with versions 1 and 2, one with version 2 retired; TR-TOOLBOX-004) plus one check against the real `library/nodes` folder (every ID once), a marker folder per check and a sample transform whose code writes a marker (TR-TOOLBOX-002), a fixed account lookup with the owner and a second account of equal rights (TR-TOOLBOX-003), an event stand-in that keeps events with fields in order (TR-TOOLBOX-006).
5. Tag `plan-baseline-it2-toolbox` (local, never pushed by an agent) on the commit with the red tests; the bare `plan-baseline-it2` is the owner's, after every subgoal has its red tests.

## Facts the tests must respect
- Trust values exactly `untrusted` and `trusted`; lifecycle exactly `draft`, `tested`, `retired`; comparisons exact, every refusal with an accepted twin (TR-TOOLBOX-005).
- Import stores untrusted whatever the file's `status` says; import never compiles or runs the code text (REQ-WFM-052, 053).
- Only the owner trusts; any account may set trusted back to untrusted (REQ-WFM-054). Owner = the account that creates accounts (`accounts.is_owner`, built in Implement; the test double supplies it).
- A replace by a higher version keeps trust and lifecycle (TC-WFM-092 starts from a trusted, `tested` entry); an equal or lower version is refused (050); one event only when the replaced transform is trusted (093).
- A shipped transform has no code text: its export is refused and the answer says so (094). Shipped IDs: highest version that is not retired (056).
- The baseline allowance: set only by the owner (095); an untrusted retired transform runs as baseline only with it, never in a graph (091).
- Statuses of workflows (four values in `workflow_library.py`) are not used for transforms.

## Checks after every change
```
P=~/.claude/skills
python3 $P/dev-workflow/scripts/goal_check.py --spec-dir specs/mia          # GL1 and GL3 are known (parent session)
python3 $P/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests   # the 536 older errors; none new on the toolbox ids
python3 $P/plan-phase/scripts/req_graph.py --spec-dir specs/mia --tests-dir tests
python3 -I tools/gen_node_requirements_model.py . && python3 -I tools/check_sysml_model.py . && bash tools/check_sysml.sh
python3 $P/plan-phase/scripts/req_review.py --spec-dir specs/mia --tests-dir tests status   # nothing "changed since review" on TOOLBOX ids
```
Never `git add -A`; name the paths; commit messages end with the Co-Authored-By line. Do not edit approved requirement or check text: a change sends the item back to review (fingerprint); ask the owner.

## Still open for the owner or the parent session
1. A-110: read the diff (`bash tools/apply_amendment_a110.sh --report`), install with `--do`, commit "contracts: A-110 installed"; decide the IF-302 version order with G-V3.
2. Parent session: `goals/G-V2/goal.md` (IF-302 in scope: the GL3 error; line 115 "all three extend it"), `high-level-spec.md` (FR-38 text with lifecycle, AC-32 split into AC-32a..c; wording in the prototype's `proposed-spec-changes.md` on branch `prototype/toolbox`), root `requirements.md`.
3. `plan.md` of this folder is Draft: approve it at the Plan gate. Its T-06 depends on STORE (merged) and A-110.
4. Re-add the deny rules for `tests/acceptance/**`, `tests/helpers/**`, `tests/smoke/**` in `.claude/settings.json` after Step 4 if they were lifted.
5. REQ-WFM-054 etc. need no History change; the `A-89` mention in the rationale of 054 is fine.
