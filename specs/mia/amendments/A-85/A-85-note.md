# A-85: correction of the reasons of TD-12 to TD-20

Status: **proposed** (draft for the owner to read and install). Decision: D-179. A-83 must be installed (and A-84, which this branch carries).

## What was wrong
A-83 and D-178 gave as the reason for the nine deferrals that the criteria, suites and pins "are not fixed (no `eval-spec.md` for MIA)". `specs/mia/eval-spec.md` and `specs/number-gate/eval-spec.md` exist (drafts, with the pins MP-light and MP-full), and `eval/suites` has holdouts for the verdicts suites. Several reasons I wrote for single rows were not backed by a file either. The agent found this while preparing the Deploy documents.

## What changes (built from the installed file)
| File | Change |
|---|---|
| `specs/mia/deferred.md` | the Reason line of TD-12 to TD-20: the drafts are not approved by the owner, no baseline run is recorded as a .jsonl in `eval/baselines`, the goal Verify did not run stage 4 (D-178); plus, per record, what the repository shows (no holdout for the lookup, review or behaviour suites; the criterion missing in both drafts for TC-MIA-011, -024, -025, -028; the review and the 10 s part out of G-V1) |

Nothing else changes: the deferral (D-178), the owner and trigger, the interim criteria, the target and the target check stay. Refused when a record or its single Reason line is not found; a second run says "nothing to do". `merge-request.md`, `release-notes.md` and `tc-mia-status.md` on this branch carry the corrected wording; the older text of A-83 and D-178 stays as written and D-179 corrects it.

## Checked on a scratch copy (not installed)
A-84 and A-85 installed in order on a `git archive` of this branch: trace_check no error about TD-12 to TD-20, second run "nothing to do".
