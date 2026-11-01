# A-57: IF-101 says that a minus vote is followed by the shocked expression (N-2.2 T-06, D-156)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
The owner decided (D-156, question 2 of the N-2.2 hand-over) that IF-101 records the reaction built in N-2.2 T-06 (REQ-CHV-006, D-137, D-143): after a stored minus the Backend sends `expression {name: "shocked"}` to every connected page (and the shocked line on the audio route; then the face of the current mood, D-156 (1)). The event `expression` exists since v0; only the `vote` row did not say it. The mock of IF-101 sends the same event, so N-1.2's TC-CHV-006 on the mock and the real Backend agree.

## What changes
| Installed file | Change (built from the INSTALLED file at install time) |
|---|---|
| `contracts/IF-101-chat-api.md` | the title goes one version up (v11 -> v12, or v12 -> v13 when A-54 is installed first); one sentence at the end of the `vote` row; one row in the version history |
| `tests/helpers/mocks/if_101_chat_api.py` | `vote`: after the event `score`, a minus also broadcasts `expression {name: "shocked"}` |

Unchanged: the suites, `tests/helpers/contract.py`, `specs/mia/test-spec.md`. No contract test is added (the real side of the IF-101 suite has no character; TC-CHV-006 of N-2.2, `tests/test_converse_behaviours.py`, checks the real Backend).

## Order with A-54 (branch v1-n21b, also IF-101 contract and mock)
- A-54 first, then A-57: A-57 builds on A-54's files and becomes v13.
- A-57 first, then A-54: **A-54's script copies whole files and would take A-57's change out again.** Run `bash tools/apply_amendment_a57.sh --do` once more after A-54: it then adds itself as v13 (the script is safe to run twice; when the change is there it reports "unchanged").

Install (on goal/v1 after the merge of v1-n22): `bash tools/apply_amendment_a57.sh` (look), then `--do`, commit as "plan: A-57 installed".
