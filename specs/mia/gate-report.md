# Plan gate report: MIA (specs/mia)

**Status:** prepared for the team review, 2026-10-26. The gate is **not passed**: it needs the team's approval of the plan package including the test code, and a person's rating of every requirement and assumption (L2b). Everything a script can check is green.

## Automated checks

| Check | Result |
|---|---|
| Decomposition (`decomp_check.py`) | 0 errors; 4 warnings = the recorded leaf exceptions (N-2.1, N-2.2, N-2.4.1, N-2.4.2) |
| Requirement lint (L0/L1) over 22 requirement files | 0 errors; warnings only in the approved HLS items (FR-2, FR-9 two `shall`; NFR ids keep their HLS form) and the REQ-API-011 phrasing; INFO notes on pronouns and compounds |
| Requirement graph (L2), 415 requirements | 0 errors, 34 warnings (the step parts of the agent view have no function or requirement of their own) |
| Quality (M32) | all nine characteristics covered |
| SysML pilot parser | 4 files, 0 errors, 0 warnings (356 node requirements generated into the model, T-14) |
| Model check | OK |
| Stage file | 13 steps; `integration` now runs `tools/run_integration_steps.py` (unittest discover does not enter the step folders) |
| Integration steps in a scratch copy | 23 Python steps and 4 JavaScript steps: step 0 of every node green, later steps skip until their node is integrated |
| Contract suites in a scratch copy | green on the mocks (stage 1), real side skipped |
| Trace check (`trace_check.py`) | 27 errors, all markers of the number-gate tests (decision 2: the `trace` step joins `stages.yaml` when those tests are in this tree) |

## What the team has to do

1. **Install the protected tests** (owner, the coding agent may not write there):
   `bash tools/install_contract_drafts.sh` then `bash tools/install_integration_drafts.sh`. If the contract drafts were installed before F-5, the IF-102 mock, suite and spec differ now (three files, amendment 9: copy by hand).
2. **Review the test code:** the 17 contract suites and mocks (`specs/mia/contract-drafts/`) and the six scenarios (`specs/mia/integration-drafts/tests/integration/*/scenario.*`).
3. **Rate plausibility (L2b).** `specs/mia/plausibility-proposal.yaml` holds a proposal for every requirement (422) and assumption (14). The agent only proposes.
   - 298 items are not flagged: accept them with `python3 -I tools/apply_plausibility.py . --by "<name>" --accept-unflagged`, or read them first.
   - 138 items are flagged `attention` (52 decided by a measurement, 65 with a numeric bound, 32 depending on the model, a GPU or a phone, 17 quality targets, 14 assumptions; some carry several reasons). For each one set `decision` and `basis`, and for a questionable one a `probe` (what, who, when) or an `accepted_risk` (reason, owner, decided, follow-up). Then run the script again; the check `req_plausibility.py` must show no error.
4. **Open numbers and risks** that the review should look at first: OPEN-1 (84 of 100 dialogues; measure today's MIA first, task T-04), the 30 fps on a phone (NFR-7), the first text in 10 s on the light model, the review recall and precision, the stability limit 0.90, the judge calibration (kappa 0.6, to be optimised).
5. **Approve** the package; then the plan documents change by amendment only.

## Decisions taken in this plan cycle (details in `review-log.md`)

D-45 to D-61, among them: the cut of MIA into five nodes (D-45), the example workflows as library data (D-50), the numbers of OPEN-1 to OPEN-6 (D-52), psycopg 3 (D-54), IF-105 and the cut of N-4 (D-55), OPEN-7 (D-56), the trace decision and F-5 (D-61).

## Findings closed or open

| Id | Finding | State |
|---|---|---|
| F-1 | test of AC-11 with 10 in 1000 fails 41.7 % at a true 1 % | closed: 0.5 % implemented (OPEN-2) |
| F-2, F-3 | requirement texts of the table nodes said "store"; account creation by role | closed |
| F-4 | no interface for the evaluation harness | closed: IF-105 |
| F-5 | IF-102 mock without `runs` and `source_trust` | closed: IF-102 v1, TC-IF-102-08 |
| T-14 | node requirements in the model | closed |
| T-04, T-01 | baseline of today's MIA; install of the drafts | open (owner) |
