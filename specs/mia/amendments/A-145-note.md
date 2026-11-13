# A-145: another account's run is a 404 (finding F-04, owner G-V3.PANEL)

Status: **proposed** (Draft, 2026-11-13). Security property of IF-101 v16, `GET /api/skill-runs/<id>`.

## Why
No protected check makes the run of another account a 404. Mutant M10 (`record` ignores the account) survives all tests of the goal. The code is correct today (`chat_ops_api.py` passes `g.account`, `ChatService.skill_run` passes it to `record`).

## Change
No requirement or contract text changes; REQ-API-015 and IF-101 v16 already say the run record of the asking account is returned. One new check:
- TC-IF-101-40 (protected `tests/acceptance/contract/test_if_101_chat_api.py`, all variants incl. the real adapter): Given two accounts A and B, A has a finished run; When B asks `/api/skill-runs/<A's run>` and A asks the same; Then B gets 404 `not_found` and A gets 200 with the record; also `shown` for B never names A's run.
The mock of IF-101 gets the same rule (404 for another account) so the mock and the real variant agree.

## Delivery
Payload with `install.py` under `goals/G-V3/contract-change-5/` (suite red first on a mock that ignores the account, as the earlier payloads). Number TC-IF-101-40: to be checked against the highest existing number before the payload is built.
