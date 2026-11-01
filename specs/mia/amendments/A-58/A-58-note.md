# A-58: IF-111 v3, the page waits up to 30 s for the character's `ready` (N-1.2 Verify finding F5)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
IF-111 v2 bounds the time from iframe load to `ready` at 15 s; the page has waited 30 s since b077cfe (`LOAD_TIMEOUT_MS = 30000` in `templates/static/chat/character.js`). The owner decided the contract follows the page (D-155, F5). Text only: no code and no test changes.

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `contracts/IF-111-character-bridge.md` | `specs/mia/amendments/A-58/IF-111-character-bridge.md` | title v3; the bound "time from iframe load to `ready`": at most 30 s (was 15 s); version line v3 |

`tools/apply_amendment_a58.sh` builds the new contract from the installed one at install time (three lines, each found exactly once), stops if the result differs from the draft, and reports "unchanged" when v3 is installed already.

Unchanged: the mock `tests/helpers/mocks/if_111_character_bridge.mjs` and the suite `tests/acceptance/contract/test_if_111_character_bridge.test.mjs` (neither checks the 15 s), `specs/mia/test-spec.md` (no case names the bound), the golden examples (they name no time). So nothing goes to `specs/mia/contract-drafts/`.

Not in A-58 (noted for the next IF-111 change, D-155 F9): the bridge accepts a `gesture` message that IF-111 does not list (`ui/godot/host_bridge.gd`; the page never sends it), and the IF-111 bound "60 fps on desktop" differs from REQ-CHV-010 and AC-19 (30 fps on both).

## Checked on a scratch copy (not installed)
See the node log (`specs/mia/nodes/N-1-web-frontend/nodes/N-1.2-character-view/implementation-log.md`, F5).

Install (on goal/v1): `bash tools/apply_amendment_a58.sh` (look), then `bash tools/apply_amendment_a58.sh --do`, commit as "plan: A-58 installed".
