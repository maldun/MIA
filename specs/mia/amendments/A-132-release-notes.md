# MIA, TD-11 option B: speak again through the voice route (2026-11-08, verified, not tagged)

No version: the owner decided on 2026-11-08 that the tag comes with iteration 2 (v0.2.0) after its own Verify (D-289). This change set is on `master` (merge `781393b`, status and notes `f65bc76`). The same text is in `CHANGELOG.md` under `[Unreleased]`.

## New
- Nothing new for the user beyond the fixes below.

## Changed
- `stop()` of the chat agent returns true only when an answer was stopped; a spoken-again playback is ended anyway (IF-101 and IF-201 unchanged).
- Specification: parents of REQ-CHA-030..036 and REQ-VPB-006 one level up (A-134); REQ-CHA-033 AC-1 reworded to "one error line of the Chat agent" (A-135); the 3 s of REQ-VPB-006 recorded as an accepted risk (A-136); TD-62 linked to NFR-6 (A-143).

## Fixed
- The speaker button under a message ("Speak again") is heard. The chat agent hands the stored text sentence by sentence, in order and through the speech filter, to the voice route of live answers, one repeat at a time (REQ-CHA-030, 031, 034). Before, it only sent `audio_chunk` events that no page played (D-276).
- Stop ends a spoken-again playback, also when no answer is generated (REQ-CHA-032). The Stop button shows while a message is spoken again, also over a running answer, and the status returns afterwards (REQ-CHA-035, 036). A spoken-again line is heard within 3 s after a Stop (REQ-VPB-006).
- A voice route that is not reachable does not break the chat: one connection attempt, the rest of that repeat is dropped (REQ-CHA-033).

## Resolved feedback
- D-276: found in the hand test on the host, "Speak again" does nothing (REQ-CHA-030).

## Goal
- TD-11 has no goal record: it is a change set on master (deferral TD-11 is dropped, replaced by TD-61 and the requirements REQ-CHA-030..036, A-132 option B).
- Provisional values to be settled in validation: the 3 s of REQ-VPB-006 (VAL-006).

## Known issues and open deferrals
- F4: `/api/speak_again` has no rate limit and no cap on waiting repeats (accepted, trusted users; revisit with TD-61).
- TD-61 (trigger: the Plan of an iteration that changes the voice, or 2026-12-31): two voice paths, the sound server and `SpeechService`. The sound server's handler ends only after the client closes its connection (today's route always closes). One connection per sentence loses rendering ahead (D-280); no choppy gaps were heard in the hand check.
- A failed repeat logs two error lines in the app (A-135).
- Two guards for an answer that runs during a repeat (`not self._running`) are not pinned by a test; the status itself is (TC-CHA-037).
- Hand check TC-CHA-035 is owner-reported (Firefox, steps 1 to 4 and both extra checks passed); audio device, exact commit and per-step table not recorded (TR-VOICE-002 met with incomplete detail).
- TD-62 (trigger: the Plan of the next iteration, or 2026-12-31): `test_tailscale.ScriptTest.test_without_tailscale_it_says_how_to_install` runs the real `tailscale` on a host that has it; an expected failure there.
- The ladder (stages 0 to 3, local run on master `1732666`, no CI) is red for other work, accepted as deviations (D-289): 59 `decomposition` errors (plan backlog, none of TD-11), 2 acceptance files `test_graph_model.py` and `test_graph_run.py` (G-V2.MODEL, not implemented yet). `merge_gate.py` was not run.
- Master holds production changes since v0.1.0 that this verification did not cover, so a tag on master would release them: `deploy/preflight.sh`, `deploy/up.sh voice`, `tools/recovery_check.sh`, `tools/fetch_kokoro.sh`, `tools/fetch_benchmarks.py`, and the stubs `graph_model.py`, `graph_run.py`, `skill_record.py` of G-V2.MODEL.

## For deployment (Phase 6)
- Artifact: none, no tag and no image built for this change set.
- Target: the owner's workstation runs master from the checkout.
- Smoke tests: none new; the hand check TC-CHA-035 was run by the owner.
