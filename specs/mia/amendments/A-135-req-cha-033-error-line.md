# A-135: wording of the error line in REQ-CHA-033 AC-1 (owner decision 2026-11-08, D-287)

Status: **decided by the owner 2026-11-08 (D-287): "Accept two, reword AC-1".** Applied by the Verify session; the owner may correct the wording.

## Why
After the fix of finding F1 (`speak_answer` raises when the sound server is not reachable) one failed spoken-again request logs two error lines in the app: the line of the sound server streamer ("Sound server not reachable", shared with live answers, unchanged) and the line of the Chat agent ("Speak again: the voice route failed"). AC-1 said "one error line is logged". With the fake route of TC-CHA-033 it is one line; with the real route it is two (`tests/test_speech_route_failure.py` asserts exactly 2 and one connection attempt for five sentences).

## Change (no behaviour, no code)
- `requirements.md` of N-2.2, REQ-CHA-033 AC-1: "one error line of the Chat agent is logged (a failing route may log its own line too: the sound server streamer does, A-135)"; the rest of the AC, including the remark "(A-133: the status is busy while the repeat runs)", is unchanged.
- `test-spec.md` of N-2.2: the table row and the scenario of TC-CHA-033 carry the same wording.
- The checks do not change: TC-CHA-033 already counts the log records of the Chat agent only (one, with the fake route); the real-route test says two in total.

## Checks after the change
Text only: `git diff` shows three changed lines; `check_sysml.sh` and `check_sysml_model.py` are unaffected (the AC is not in the model).
