#!/usr/bin/env bash
# Amendment A-85 (2026-11-01): correction of the reasons of TD-12 to TD-20. A-83 wrote that the eval specs and pins were "not fixed (no eval-spec.md for MIA)". That is wrong:
# specs/mia/eval-spec.md and specs/number-gate/eval-spec.md exist as drafts with the pins MP-light and MP-full; what is missing is the owner's approval, the holdout baselines
# (eval/baselines has no .jsonl), holdouts for the lookup, review and behaviour suites, and the run of stage 4 itself, which the goal Verify did not make (D-178). Reasons that
# I could not back with a file are replaced by what the repository shows. Decision D-179. Note: specs/mia/amendments/A-85/A-85-note.md
# Made from the INSTALLED file at run time (A-83 installed), each Reason line replaced only when it is still the old text:
#   specs/mia/deferred.md   the Reason line of TD-12 to TD-20
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a85.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a85.sh --do      install and run the trace check; commit afterwards as "plan: A-85 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - specs/mia/deferred.md "$WORK/deferred.md" <<'PY'
import re
import sys
installed, out = sys.argv[1:3]
text = open(installed, encoding="utf-8").read()
COMMON = ("the eval specs are drafts the owner has not approved (`specs/mia/eval-spec.md`, `specs/number-gate/eval-spec.md`), no baseline run is recorded as a .jsonl in "
          "`eval/baselines`, and the goal Verify did not run stage 4 (D-178)")
REASONS = {
    "TD-12": COMMON + "; the verdicts suites have holdouts, the lookup suites (`research`, `research_compound`) have none (12 + 8 cases are for the owner to label)",
    "TD-13": COMMON + "; the review entry is out of G-V1 (REQ-RUN-013 partly, D-128, D-130), the suite `review_toy` has no holdout and the recall threshold is the owner's (open question 3 of the draft)",
    "TD-14": "the review is the next goal's (VAL-002 moved, D-134), so the second workflow of the skill path does not exist yet; " + COMMON,
    "TD-15": COMMON + "; the seeds, repeats and the rate (0.5 % implemented, 1 % in the text, finding F-1 of the test table) are not decided",
    "TD-16": COMMON + "; the benchmark REQ-RUN-007 is a proposal of the draft that needs an amendment to live under `benchmarks/` (open question 4), the 10 s part is out of G-V1 (REQ-RUN-009 partly, D-128) and the frame rate on the phones is a field measurement (D-62)",
    "TD-17": COMMON + "; the AC-22 measurement is out of G-V1 (REQ-RUN-005 partly, D-128), the criterion for REQ-RUN-006 is only a proposal in the draft, and the learning layer is not built (REQ-RUN-004 out, D-119)",
    "TD-18": COMMON + "; the check is marked later and Should in the root table, and no criterion for the memory test set is in either draft",
    "TD-19": COMMON + "; the suite `behaviour` exists without a recorded baseline and without a holdout, and no criterion for the detectors is in either draft",
    "TD-20": COMMON + "; no criterion for the estimate is in either draft, and no set of recorded lookup runs is named as its reference",
}
SUFFIX = "; the stage 4 rows of the root table were deferred at the goal Verify of G-V1"
for td, reason in REASONS.items():
    m = re.search(r"^## %s [^\n]*\n(?:(?!^## ).*\n)*" % td, text, re.M)
    if not m:
        sys.exit("%s: %s is not found; install A-85 by hand (A-83 must be installed first)" % (installed, td))
    block = m.group(0)
    lines = re.findall(r"^- Reason: .*$", block, re.M)
    if len(lines) != 1:
        sys.exit("%s: %s has no single Reason line; install A-85 by hand" % (installed, td))
    new_line = "- Reason: " + reason + (SUFFIX if td not in ("TD-14",) else SUFFIX)
    text = text.replace(block, block.replace(lines[0], new_line, 1), 1)
open(out, "w", encoding="utf-8").write(text)
PY
copy "$WORK/deferred.md" specs/mia/deferred.md
finish
echo
echo "== trace_check errors (47 or 48 expected, none new about TD-12 to TD-20)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E "ERROR.*TD-(1[2-9]|20)" || echo none
