# A-166 draft: deferred entry TD-90 (the real half of the IF-103 contract suite never runs)

Owner decision of 2026-11-20 (D-357): TR-CONVERT-006 is accepted "in spirit". `specs/mia/deferred.md` is protected: the owner appends the block below after TD-89 with `bash tools/apply_deferred_td90.sh --do`. The Sign-off line is yours to tick: nothing is signed here.

---

## TD-90 – The fake model server of TC-WFM-058 is not shown to be as faithful as the real one: the real half of the IF-103 contract suite is skipped (DRAFT)
- Kind: defer
- Requirement: REQ-WFM-058 (TR-CONVERT-006: "the fake model server passes the contract suite of the model server interface"; finding F-09(a) of the Verify of G-V2.CONVERT)
- Interim criterion: the check TC-WFM-058 compares the model calls of the old runner and of the graph path on the same scripted replies, so both sides send through the same fake; the fake never decides an eval criterion (the rates of TC-WFM-110 to 114 are decided on the real pinned model); the mock side of the IF-103 suite passes (6 of 6), the real side is skipped by the table of reasons in `tests/helpers/contract.py` ("the real model server is only used in stage 2") because a real Ollama cannot be scripted to give bad output, a timeout or an unreachable server
- Target: a scripted proxy in front of Ollama (or another real adapter, a `real_subject` for IF-103) so that the real half of the suite runs; the same part would serve the real halves of IF-404 and IF-405; then TR-CONVERT-006 holds as written, or is reworded to what the check really compares (prompt and options as the real client sends them)
- Reason: the owner decided on 2026-11-20 (D-357) to accept TR-CONVERT-006 in spirit; the proxy is a new part, which needs a plan step and the owner's approval
- Effort: about a day (the proxy, its contract adapter, the removal of the skip reasons of IF-103, and the check of TC-WFM-058 against it)
- Risk of the gap: the fake can differ from the real client in the shape of the options or the prompt sent, so that TC-WFM-058 passes on calls the real server would see differently; a difference would show as a worse rate in TC-WFM-110 to 114, not as a failure of TC-WFM-058
- Owner: Stefan Reiterer
- Trigger: the first change of the model client (`model_client`, the options sent to Ollama) or of the runner's calls, the first provider other than Ollama, or the start of the stage 2 integration of IF-404 and IF-405, whichever first
- Target check: specified only
- Decision: D-357, 2026-11-20
- Sign-off: pending
- Status: open
