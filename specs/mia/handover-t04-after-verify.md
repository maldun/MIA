# Hand-over after Verify of T-04 (structured memory), 2026-10-26

State: verification **postponed by the owner** until trial-run data exists. Report: `specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/verification-report.md` (branch `worktree-verify-t04`, not yet merged into master).

## Done
- Holdout run once (v6, `memory.write@5`, digest `38044be4f923`, 3 repeats): 10 of 11 right, Wilson lower bound 0.62, rule of A-12 PASS. Log `/home/maldun/verify-t04-logs/holdout1.jsonl` (outside the repo; holds holdout texts, do not copy into prompts or cases).
- The holdout is **used**: a second run is allowed only after a FAIL, so after a prompt or skill change it needs a new holdout (amendment by the owner), not a re-run.
- REQ-CHA-012 by tests and reading (single caller `chat_service.py:573`), REQ-CHA-013 by `test_items_api.py`, static checks as in the report. No code, skill, sample or test was changed.

## Open
1. Trial data with `structured_memory` on (the option is off by default): real conversations over some days, then run `tools/memory_cost.py` again (AC-24 b had 1 record) and look at wrong or duplicate records in the Memory tab.
2. Memory tab demonstration (REQ-CHA-013) by the owner.
3. Transcript review (check F) of the holdout log by a person: MEM-S27, MEM-S09 and about 10 more.
4. Measure latency and VRAM with the light memory call and the full chat model on the 16 GB card (D-4).
5. Owner decisions: kind label of MEM-S27 or the matcher (D-2, by amendment), retrieval of "my height" style questions (D-3), the empty red-team draft file (D-6).

## Next steps
1. Merge the verify branch: `cd /home/maldun/prog/Python/MIA && git merge worktree-verify-t04`.
2. Turn `structured_memory` on in `setup_cfg.json` for the trial period and use MIA normally.
3. After the trial: a fresh verifier session closes the report (new `memory_cost.py` run, transcripts, Memory tab), without opening the holdout again; verdict "verified" or "with accepted deviations".
4. Then Commit phase (`commit-phase` + `agent-app-commit`).
5. In parallel, if wanted: Plan session for D-2, D-3 and the RT-009 cases.
