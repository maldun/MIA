# Handover: Verify of G-V2.TOOLBOX (written 2026-11-12)

Branch `goal/v2.toolbox`, worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox`. Report: `specs/mia/goals/G-V2.TOOLBOX/verification-report.md`. Verdict so far: **Verified with open findings**. Decisions of the batched review: D-229 in `specs/mia/review-log.md`.

## Done
- Protected material vs `plan-baseline-it2-toolbox`: clean, every change maps to the installs d77858f, 756bdbc, 6f8cd02, 18218e0.
- All test files of the scope pass in the venv; the 17 skipped real-contract tests belong to other nodes (IF-103, IF-404, IF-405, IF-101).
- Matrix, test requirements TR-TOOLBOX-001..006, trace/goal/graph checks, code review of `toolbox.py` and the `transforms` block, repro of the findings (scratchpad `repro.py`, not committed).
- Review questionnaire answered (F1, F2, F3-F5, F7).

## Still open in Verify
1. **Stage ladder**: the local run was restarted and may have finished. Log: `<scratchpad>/stages-log.jsonl`, output `stages-out.txt` (scratchpad `/tmp/claude-1000/-home-maldun-prog-Python-MIA--claude-worktrees-goal-v2-toolbox/3d8793f1-83c9-4e3c-a501-91a04d410798/scratchpad`; it may be gone). If not, rerun in the background with the venv bin first in PATH, never a symlinked python (the first run was invalid for that reason):
   `V=/home/maldun/prog/Python/venvs/mia312/bin; PATH=$V:$PATH nohup $V/python ~/.claude/skills/dev-workflow/scripts/run_stages.py --stages stages.yaml --upto 2 --keep-going --log <log> > <out> 2>&1 &`
   Then enter the result in the section "Stage log" of the report. Local runs are feedback; only CI counts for `merge_gate.py`.
2. F6 and F8 were not put to the questionnaire (info/notes); ask only if wanted.
3. Tell the owner the report is ready for the gate once item 1 is in.

## Findings and routing (D-229)
| F | What | Route |
|---|---|---|
| F1 high | baseline allowance survives a replace by any account, exec of new code | clear `baseline_allowed` on replace; amend REQ-WFM-091/092; test first (Phase 2/3) |
| F2 medium | allowance settable on a live transform, never revoked | only together with `retired`; any other lifecycle change clears it; the "twin" test in `tests/test_toolbox.py::BaselineChecks` changes |
| F3 | float version 1.0 passes the schema, wrong error type | Phase 3, failing test first |
| F4 | reason after untrust stale or empty | Phase 3 |
| F5 | event failure leaves the code replaced | Phase 3 |
| F7 | `decomposition` step red on master (70) and +6 | known red, parent session |
| F6, F8 | owner rule lives in the toolbox only; unknown id raises `WorkflowLibraryError`, two-step save | notes / wiring task |

After the fixes: automated checks 1, 2, 4, 5 again in full, reviewer reads the fix commits only.

## What to push
Nothing is pushed by me. After this commit the owner pushes `goal/v2.toolbox` (the commit "verify(toolbox): ..." holds the report, this handover and the D-229 row of `review-log.md`). Do not merge yet: F1 and F2 are to be fixed first. Merge order stays STORE, MODEL, TOOLBOX, CONVERT.
