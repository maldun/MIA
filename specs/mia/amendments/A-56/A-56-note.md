# A-56: the real `stop` in the IF-201 contract suite (N-2.2 T-01)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
N-2.2 T-01 left one part open: a `stop` that comes before the worker has taken the message (REQ-CHA-004, TC-IF-201-04 golden 3) was lost, because the worker cleared the stop when it took the message. Built test-first on branch `v1-n22` (`chat_service.py`, `tests/test_chat_backend.py::test_stop_before_the_answer_starts`). The real sides of TC-IF-201-04 and TC-IF-101-06 still skip, because the adapters `_ChatTurnAdapter.stop` and `_ChatApiAdapter.stop` (without a thread) in `tests/helpers/contract.py` (protected) raise `SkipTest`. No new decision of the owner is needed: the contract, the suite and the mock are unchanged; only the adapter calls the real service.

## What changes
| Installed file | Change |
|---|---|
| `tests/helpers/contract.py` | `_ChatTurnAdapter.stop` returns `{"stopped": self._chat.stop()}` (the shape of IF-201, as `web_app.py`'s `chat_stop` does); `_ChatApiAdapter.stop` no longer skips when no worker thread runs (it returns the real answer as it does with one); the class docstring of `_ChatTurnAdapter` no longer names "`stop` of an answer that has not started: N-2.2 T-01" as not built |

The script builds the new `contract.py` from the installed one at install time (it is shared by many amendments), refuses when an anchor is not found exactly once, and reports "unchanged" when it is installed already.

Unchanged: `contracts/IF-201-*.md`, the suites `test_if_201_chat_turn.py` and `test_if_101_chat_api.py`, the mocks, `specs/mia/test-spec.md`.

## Checked on a scratch copy (not installed)
See the implementation log of N-2.2 (T-01): the suite in the image with the change, and the same change against the code before the fix (red).

Install (on goal/v1 after the merge of v1-n22): `bash tools/apply_amendment_a56.sh` (look), then `bash tools/apply_amendment_a56.sh --do`, commit as "plan: A-56 installed".
