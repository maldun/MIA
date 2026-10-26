# Hand-over after Verify of T-04 (structured memory), 2026-10-26

State: verification **postponed by the owner** until trial-run data exists. Report: `specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/verification-report.md` (branch `worktree-verify-t04`, not yet merged into master).

## Done
- Holdout run once (v6, `memory.write@5`, digest `38044be4f923`, 3 repeats): 10 of 11 right, Wilson lower bound 0.62, rule of A-12 PASS. Log `/home/maldun/verify-t04-logs/holdout1.jsonl` (outside the repo; holds holdout texts, do not copy into prompts or cases).
- The holdout is **used**: a second run is allowed only after a FAIL, so after a prompt or skill change it needs a new holdout (amendment by the owner), not a re-run.
- REQ-CHA-012 by tests and reading (single caller `chat_service.py:573`), REQ-CHA-013 by `test_items_api.py`, static checks as in the report. No code, skill, sample or test was changed.

## Owner decision 2026-10-26 (after the run)
- MEM-S27 relabelled `preference` to `fact` in `specs/mia/eval-drafts/memory_sample.jsonl` (the stored "is vegetarian" fact is correct). This is **post-hoc**: the recorded run was scored with the old label (10 of 11); with the new label the same log would score 11 of 11. The run is not repeated and the original score stays in the report. D-2 is closed by this.
- Measurements (AC-24 b with more records, latency and VRAM with light and full model, D-4) move to the field test.
- The security work (red-team cases RT-009) comes last.

## Open
1. Field test with `structured_memory` on (the option is off by default): real conversations over some days; then `tools/memory_cost.py` again, latency and VRAM, and wrong or duplicate records in the Memory tab.
2. Memory tab demonstration (REQ-CHA-013) by the owner.
3. Transcript review (check F) of the holdout log by a person: MEM-S09 and about 10 more.
4. Retrieval of "my height" style questions (D-3), owner decision.
5. Last: the empty red-team draft file, the four THR-006 (RT-009) cases (D-6).

## Next steps
1. Merge the verify branch: `cd /home/maldun/prog/Python/MIA && git merge worktree-verify-t04`.
2. Turn `structured_memory` on in `setup_cfg.json` for the field test and use MIA normally.
3. After the field test: a fresh verifier session closes the report (measurements, transcripts, Memory tab), without opening the holdout again; verdict "verified" or "with accepted deviations".
4. Then Commit phase (`commit-phase` + `agent-app-commit`).
5. Last, Plan session for D-3 and the RT-009 cases.

## Start prompt for the fresh session (after the field test)
> Close the verification of T-04 of MIA (structured memory). Read `CLAUDE.md`, `specs/mia/handover-t04-after-verify.md` and the verification report in `specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/`, load `verify-phase` and `agent-app-verify`, work in a worktree that branched from current local master (not origin/master). You are an independent verifier: do not open or re-run the holdout (it is used; MEM-S27 was relabelled to `fact` after the run), never tune anything. Using the field-test data of `structured_memory`: re-run `tools/memory_cost.py` (counts only, on a copy of the data), measure latency and VRAM with the light memory call and the full chat model, check wrong and duplicate records in the stored memory, and update the report. The transcript review and the Memory tab demonstration are done by the owner: list what is still missing. Propose the verdict; the red-team cases (RT-009) are the last step and not part of this session.
