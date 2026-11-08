# A-105: TR-MODEL-001 and task T-05 reworded, task T-06 new (G-V2.MODEL, finding of T-05)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a105.sh` is not yet run with `--do` in the repository.

## Finding and the owner's decisions (2026-11-08)
T-05 stopped before any change. `FakeGraphTables` (`put`, `get`, `versions`) is a versioned key-value store; the IF-301 v2 suite tests pure functions (`check_record`, `to_object`, `types`, ...), so 0 of its 20 cases pass on the fake (probe `fake_vs_suite.py`). The five checks TC-WFM-040, 041, 042, 044, 049 hardcode `FakeGraphTables` in `tests/acceptance/test_graph_model.py` (protected), so they cannot run on the real `Storage` without a protected change.

| Question | Decision |
|---|---|
| T-05 path | plan amendment plus a new adapter test outside `tests/acceptance` (this note) |
| Node field names | confirmed as proposed; no text change |
| REQ-WFM-041 (listing and start from the record) | own task T-06 after T-05 |
| `Quality:` lines for REQ-WFM-040, REQ-RUN-017 | left out; gap noted at Verify |

## What A-105 contains
| File | Change |
|---|---|
| `test-requirements.md` | **TR-MODEL-001** text, rationale, "Verified by" and history: the same scenarios also run on the real Storage layer in a test file outside the protected folders; a difference between fake and real is a finding. The text changes, so the test requirement returns to review |
| `goals/G-V2.MODEL/plan.md` | T-05 reworded (adapter test `tests/test_skill_record_storage.py`; `skill_record.py` uses `Storage.ids("skills")` instead of the `skill_index` pseudo-record and gets the `author` from the caller); **T-06 new** (REQ-WFM-041: `library.py`, `extension_loader.py`); counts and order |
| `review-log.md` | row D-306 appended (the owner's answers) |
No protected test, helper, contract or requirement text changes; STORE's files stay untouched.

## Points for the owner
1. **My reading of "checked against IF-102 plus the record rules":** the fake cannot satisfy the IF-102 contract suite either (its `put` has no `author`, it has no `ids` or `history`). I therefore wrote the check as a **differential run**: the same five scenarios on the fake and on the real Storage layer (file backend, PostgreSQL where available), answers compared by IDs and version numbers (TR-MODEL-005). Say if you meant something else.
2. TR-MODEL-001 is changed text; it comes back in review after the install. I mark it only when you say so.
3. The name of the adapter test file (`tests/test_skill_record_storage.py`) is my proposal.
4. A skill record that the real record checks refuse is a finding for REQ-WFM-040, not a reason to change STORE.
5. ID choice: A-105 is the next free number in the MODEL range after STORE used A-100 to A-104; D-306 follows D-305 on master.

## Checked by the drafter (scratch copy; nothing installed in the repository)
`--do` twice: the second run changes nothing; the look-only run changes nothing.

## Install
```
bash tools/apply_amendment_a105.sh --report     # look only
bash tools/apply_amendment_a105.sh --do         # then commit "plan: A-105 installed"
```
