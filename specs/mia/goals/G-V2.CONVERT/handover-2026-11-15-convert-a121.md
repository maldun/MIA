# Hand-over G-V2.CONVERT (written 2026-11-15): A-121 approved, contract text waits for the parent session, owner list P3 to P6 open

Read `CLAUDE.md`, then this file, then `handover-2026-11-07-convert-step4.md` (still valid for the test material), `goals/G-V2/parallel-work.md` and `plan.md`. Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-convert`, branch `goal/v2.convert`, not pushed (push and merge are the owner's). One session at a time here.

## Done this session (commits, oldest first)
- `2f1e715` master merged into the branch (STORE, MODEL, TOOLBOX, G-V3 material). Conflicts by the rules of `parallel-work.md`: `architecture.sysml` from master and regenerated, `eval-spec.md`, both plausibility files and the N-2.3 `requirements.md` keep both sides. `check_sysml` 0 errors.
- `6584c94` to `25e40e1`, `9b7267d`: `specs/mia/amendments/A-121-draft-IF-203-v2.md`, the IF-203 v2 text (snapshots) with the owner's decisions (D-241): pointer in a table `current_versions` (open JSON document, only `version` required), `restore` keeps its v0 meaning and the pointer move is `set_current_version`, the library signals `forbidden`, `save` after a pointer move writes max+1 and moves the pointer, snapshot records are open documents.
- `973e216` red tests follow A-121 (D-242; `A-121-test-amendment.md`): lab `set_current_version`, `restore` back to v0 meaning, `evidence` on `set_lifecycle`, two new tests for TC-WFM-063 (O3 name rules, O4 roll back). Snapshots 8 tests red on the stub; a throwaway reference turned all 8 green. The deny rules of `tests/acceptance/**` and `tests/helpers/**` were lifted for that step and restored.
- `6b448cd` A-121 approved as a whole by the owner, items 1 to 11 one by one (D-243).

## For the parent session (contracts and parent files; not this session)
1. `contracts/IF-203-workflow-library.md` to **v2**: insert the text of `A-121-draft-IF-203-v2.md` (header sentence, operations rows, snapshot record paragraph, error rows, bounds line, golden examples 8 to 12, version row). Golden example 1 and `restore` stay unchanged.
2. `contracts/IF-302-record-tables.md` to v12: table `current_versions` as specified at the end of the draft (record id `<kind>/<id>`, open document, only `version` required, versioned, not deletable, an item without a record reads as its newest version). Check the `definitions()` row and the field list of IF-302 for how other tables are written.
3. `contracts/IF-102-storage-interface.md` to v7: table list names `current_versions`; no new operation. PostgreSQL schema: one more generic versioned table.
4. IF-301 v2 (MODEL's draft, `A-90-draft-IF-301-v2.md`): confirm its state on master; the `skills` kind of IF-203 v2 depends on it.
5. Then, with the owner's go and the deny rules lifted: the IF-203 v2 contract suite in `tests/acceptance/contract/` and the extension of the mock `tests/helpers/mocks/if_203_workflow_library.py` (kinds `skills` and `snapshots`, the four snapshot operations, `set_current_version`, `pins`, `forbidden`). The existing suite and mock stay valid for v0 and v1 behaviour.
6. The test-spec row of TC-WFM-063 should name the two added scenarios (check whether it is protected).

## Owner list (still blocks Implement of CONVERT; P3 to P6 of `plan.md`)
- P3 A-120: `split:dev` on the cases of EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction (protected eval material). Without it TC-WFM-115 uses all 51 cases.
- P4 baseline run files (dev split, 3 repeats, MP-light, per skill and variant). Today only `.md` summaries exist; verify_claim, verify_computable and extract_claims were recorded with 1 repeat and must be re-recorded at 3.
- P5 rate the ten proposed plausibility items; judge the margin 0.10 of REQ-WFM-110 to 114 against the baselines.
- P6 approve REQ-WFM-057 to 066, 069, 110 to 115 with their final text (062, 063, 066 and 059 were back in review). The two new TC-WFM-063 scenarios may need a wording change in REQ-WFM-063's criterion.
- P1 is met (STORE, MODEL, TOOLBOX in master). P2 is met with the amendment above.

## Checks after the merge
`goal_check`: GL1 (G-V2 and G-V3 open, known) and GL3 (TOOLBOX, IF-302 in scope but not in G-V2's, not compared with before). `req_graph` 5 errors, `trace_check` 553 error lines (538 on master; the 15 more not examined), `req_plausibility` warns about `REQ-WFX-…` (known). Run the commands of `handover-2026-11-07-convert-step4.md` ("Checks") after every change.

## Traps
- Never `git add -A`; name the paths; commit messages end with the Co-Authored-By line.
- Do not set baselines, `split:dev` tags or plausibility ratings; they are the owner's. Never run or open the holdout.
- The stubs `skill_converter.py` and `snapshot_store.py` are in the repo root; the implementer replaces their bodies. `snapshot_store.Conflict` and `Refused` are the exceptions the tests expect.
- Review style of this owner: one item per question, relative sizes, reviewer name maldun.
