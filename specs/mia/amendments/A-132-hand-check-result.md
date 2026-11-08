# Result of the hand check TC-CHA-035 (TD-11 option B), for the verification report

Check: TC-CHA-035 (REQ-CHA-030, REQ-CHA-032, REQ-CHA-035), `specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/test-spec.md`; test requirement TR-VOICE-002 (done by the owner on the host with the real sound server, the real engine and the real page; result goes into the verification report). Decisions: D-282 to D-284.

| Date | Code state | Result |
|---|---|---|
| 2026-11-08 | master before `62a32d0` (A-132 implemented) | Failed at step 3: no stop button while a message is spoken again. Finding recorded as D-282, amendment A-133. |
| 2026-11-08 | master at `62a32d0` (A-133 fix) | Passed, reported by the owner in the chat: "it works now". The result per step (1 to 4), the browser and the audio device were not written down; Verify may ask for them. |
| 2026-11-08 | master after the merge of `verify-a132` (merge commit `a2bc052`: fixes F1, F2, F3, A-134), the code the owner ran | **Passed**, reported by the owner in the Verify session: TC-CHA-035 steps 1 to 4 and both extra checks (a repeat requested while an answer is generated, with Stop offered over the overlap; a long answer spoken again without choppy gaps). Browser: Firefox (version not given). **Not recorded:** the audio device, the exact commit the host ran (the owner said it was the merged `verify-a132`), the result per step as a table. |

Also confirmed by the owner on 2026-11-08 (D-284): the clarified wording of REQ-CHA-033 AC-1 and TC-CHA-033.
