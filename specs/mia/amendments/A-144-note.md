# A-144: REQ-WFM-135, what "history deleted" deletes (finding F-08, owner G-V3.PANEL)

Status: **approved** (2026-11-13, maldun, D-331). The owner decided the direction by questionnaire on 2026-11-13: deleting one history record deletes only the run of that record. The wording below waits for the owner's approval; protected tests change only as a payload with `install.py` after that.

## Why
REQ-WFM-135 says "when the history records of an account are deleted". The recorder reads the notice `{table, id, version: None, author}` of IF-102 and deletes all run records of `author`, which is the account that deleted, not the owner of the record, and it does so for a single record (probe P9: two runs gone after one delete). Today nothing in production deletes history records, so only the acceptance test shows it.

## Change of the requirement (text, Draft)
Old: "When the history records of an account are deleted in the storage, the Workflow management shall delete that account's run records and keep the files of the files volume."
New: "When a history record is deleted in the storage, the Workflow management shall delete the run record whose run id equals the id of that history record, and no other run record, and keep the files of the files volume."

## Assumption the owner must confirm
The id of the history record that belongs to a run is the run id (the message id of the answer that started the run, `skill_run` of the `chat_start` event). Nothing writes the table `history` yet, so this mapping is not tested anywhere; it becomes the interface between the chat log and the recorder. If the owner prefers another link (a field `run` in the history record), the text changes to "whose field run names it".

## Tests
- TC-WFM-135 (protected `tests/acceptance/test_skill_runs.py`, test-spec N-2.3): Given changes to two runs of one account and one of another; When one history record is deleted; Then only that run is gone, the other two stay, `skill_run_changed` names the deleted id (not null), files stay. Payload with `install.py`.
- Code (T-11, after approval): `_history_changed` deletes the run named by `notice["id"]` and sends `skill_run_changed {id}`. The view must handle a changed id that is not the shown one (check TC-CLV-038 path).

## Affected
`architecture.sysml` REQ-WFM-135 (doc text), N-2.3 `requirements.md` and `test-spec.md`, `run-recorder-interface.md` (deletion paragraph), `review-log.md` (fingerprints).

## Added when the payload was built (2026-11-13)
The contract level breaks too: TC-IF-101-39 and the test adapter `delete_history(account)` (real adapter in `tests/helpers/contract.py`, mock `tests/helpers/mocks/if_101_chat_api.py`) delete the history of a whole account. They become `delete_history(account, run_id)` and TC-IF-101-39 checks one run deleted, the other kept (payload `goals/G-V3/contract-change-5/`, together with A-145).
