# A-195 – The copy setting: what the requirement texts did not say (G-V4.GRAPHSTORE.TRANSFER, REQ-API-064, 065, 066)

**Decided:** D-543 (owner, 2026-11-27), D-544 and D-545 (agent on the owner's delegation, D-423/D-468), D-546 (this amendment). **Installs:** `bash tools/apply_amendment_a195.sh --do` (the owner runs it), then commit as "plan: A-195 installed". TRANSFER's amendment numbers: A-195 to A-199 (RUN goes on at A-190).

**Why.** T-06 built behaviour that users see and no requirement text states (implementation log, "Unspecified behavior"): a copy of a newer format, the writes while a copy is set, the store answer while the live store does not answer. Each is now a requirement with an acceptance check; the code of T-06 already behaves so (the new checks are green on the branch, and each fails on its planted defect).

**Changed, not protected (in the commit of this amendment's drafts):**
- `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md`: REQ-API-064 moved to "Changed requirements" with its approved text as `In force:`: the lag is no graphs since null while the live store does not answer; `since` counted from header versions (D-540, D-545); verified also by TC-API-067. New, Draft: REQ-API-065 (a copy MIA cannot read: the live store is read, `shown` live, one log line; D-543), REQ-API-066 (writes go to the live store, the copy unchanged; D-544). Group AS updated.
- `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/test-spec.md`: TC-API-065, 066, 067 (table and scenarios).

**Changed (protected, installed by the script):**
- `tests/acceptance/test_transfer_backend.py`: TC-API-065 (marker format 2: live version read, `shown` live, one log line naming the copy and "format 2"), TC-API-066 (a save on live version 6 gives 7 in the live store, the copy's graph group unchanged), TC-API-067 (live database at a closed port: `shown` copy, `reachable` true, `live_reachable` false, lag no graphs). TC-API-060 to 064 unchanged.
- `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/test-requirements.md`: TC-API-065, 066, 067 added to the "Applies to" lines of TR-TRANSFER-001 (exact values), TR-TRANSFER-007 (throw-away stores only) and TR-TRANSFER-009 (start and stop through `__main__`).

**Not changed:** REQ-API-060 (its rationale already says writes go to the live store; REQ-API-066 states it); REQ-SLY-039 (the extra `sync` line per set-aside graph adds to "reports the records added", it does not contradict it); IF-104 v2 (no field or route changes: the shape of the store answer stays).

**For the owner after install:** REQ-API-064's Status line still says Approved: set it to Draft in Emacs, review, approve again; approve REQ-API-065 and REQ-API-066.

**Expected after install:** `<venv python> tests/acceptance/test_transfer_backend.py` 8/8 on the branch. Defects that must make the new cases fail (run on the drafts, 2026-11-27, all failed as expected): a newer-format copy stops the start (TC-API-065); writes go to the copy (TC-API-066); `live_reachable` fixed true (TC-API-067).
