# Hand-over for 2026-10-27: T-04 closing state and start of N-2.5 (Voice synthesis)

## Term decided by the owner (2026-10-26): "postponed to field test"
Checked during the **first validation run** (Phase 7, after everything is implemented) and **fully tested in the second implementation iteration**. The requirement stays open and is not forgotten, but it is not treated before the first validation has finished and the second implementation run has started. Only the owner applies the label; when a requirement is unclear, **ask** whether it carries it. (Memory: `postponed-to-field-test`.)

Items carrying it now (from the T-04 verification report):
- AC-24 (b) token cost with a filled store (only 1 record so far).
- D-3 retrieval of "my height" style questions (word overlap only), owner decision then.
- D-4 latency and VRAM with the real chat model, repeats and median (preliminary snapshot is in the report).
- D-5 duplicate and wrong records in the Memory tab over real use.
- AC-8 (persona) and AC-25 (detector precision and recall): earlier "postponed to the first iteration after the field test" (`HANDOVER.md`). Confirmed by the owner 2026-10-26: the same label.

## T-04 verification: state
Report `specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/verification-report.md`, branch `worktree-verify-t04-close` (commit `8cc777c`, from master `f007fd3`). Proposed verdict: **verified with accepted deviations**, once the owner has done:
1. Transcript review of the holdout log (`/home/maldun/verify-t04-logs/holdout1.jsonl`): MEM-S09, MEM-S27 and about 10 more.
2. Memory tab demonstration (REQ-CHA-013).
Last, separate session: red-team cases RT-009 (D-6). The holdout is used; never re-run it.
Merge: `cd /home/maldun/prog/Python/MIA && git merge worktree-verify-t04-close`.

## Open in N-2.2 (not blocking N-2.5)
- T-01 (chat turn, queue, stop) is not listed as done in `HANDOVER.md`; the IF-201 contract case "stop of a waiting answer" is still skipped. Check whether T-01 is complete before N-2.2 is called finished.

## Next: N-2.5 Voice synthesis (owner decision 2026-10-26)
Files: `specs/mia/nodes/N-2-backend/nodes/N-2.5-voice-synthesis/` (`requirements.md` REQ-VOI-001 to -004, `plan.md` T-01 to T-03, `test-spec.md`). Interface: IF-204 (contract suite in `tests/acceptance/contract/`, protected).
- T-01 speech per sentence and markup filtering (REQ-VOI-001, -002, IF-204); touches `speak.py`, `speech_stream.py`, `speech_text.py`, `voice_effects.py`. Voice effects stay as they are (decision: anime effect, RVC off).
- T-02 voice lines (REQ-VOI-003), T-03 default voice lines generated (REQ-VOI-004, no third-party recording).
- Existing code to test first (rule: reuse): `speech_stream.py`, `speech_text.py`, `voice_effects.py`, `voice_lines.py`, `audio_router.py`; tests `test_speech_text.py`, `test_voice_effects.py`, `test_voice_lines.py`, `test_speech_repair.py`.
- Known: only the voice line `annoyed` has a clip, the others are `silent`, and nothing plays them yet. Skipped contract cases that N-2.5 should resolve: IF-101 expression and `audio_chunk`, IF-201 (A-07).
- Order after N-2.5 (decomposition.yaml, N-2): N-2.3, N-2.4, N-2.2 integration, N-2.1.

## Start prompt for tomorrow
> Implement N-2.5 Voice synthesis of MIA, one task at a time starting with T-01. Read `CLAUDE.md`, `specs/mia/handover-n-2-5-start.md`, `specs/mia/HANDOVER.md` and the N-2.5 folder; load `dev-workflow`, `implement-phase`, `agent-app` and `agent-app-implement`. Work in a worktree from current local master (not origin/master; check `git log --oneline -1`). Test the existing code first and change only what fails. Do not touch protected material; stop and report on any contradiction. Items labelled "postponed to field test" are not treated; ask when unsure. End with exact merge commands.
