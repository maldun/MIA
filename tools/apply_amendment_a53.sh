#!/usr/bin/env bash
# Amendment A-53 (N-2.4.3 Run log, D-148, re-verification findings N1, N2 and F9): IF-401 v2. A value under a secret-like key is `[removed]` whatever its type, an empty
# text `""` stays (D-144, D-146); the suite pins these rules and the comparison of a different payload with the same types and of an extra event at the end. Note: specs/mia/amendments/A-53/A-53-note.md
# Protected files that change:
#   contracts/IF-401-run-events.md                          v2: the row of emit, the row of compare, golden examples 2 and 3, the version line
#   tests/helpers/mocks/if_401_run_events.py                an empty text under a secret-like key stays "" (it was [removed]); the rest of the rule was already v2
#   tests/acceptance/contract/test_if_401_run_events.py     TC-IF-401-02 and -04 pin the rules (no new ids); every test has an Example: line and Given/When/Then (T2/T3, F9)
#   specs/mia/test-spec.md                                  the rows of TC-IF-401-02 and -04 (made from the installed file at run time, so they cannot go stale)
# Nothing in the code changes: events.redact and run_events.RunEvents.compare follow these rules since the fixes of D-144 (branch v1-n243b).
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1).
#   bash tools/apply_amendment_a53.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a53.sh --do      install and run the IF-401 suite in the image; commit afterwards as "plan: A-53 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-53
D=specs/mia/contract-drafts
SPEC=$(mktemp)
trap 'rm -f "$SPEC"' EXIT
python3 - specs/mia/test-spec.md "$SPEC" <<'PY'
import sys
rows = [
    ("| TC-IF-401-02 | IF-401 | Contract | 1 (mock) and 2 (real) | golden 2: an unknown type is refused and nothing is written; secrets in the payload are stored as [removed]. | exact |",
     "| TC-IF-401-02 | IF-401 | Contract | 1 (mock) and 2 (real) | golden 2 (v2, A-53): an unknown type is refused and nothing is written; a value under a secret-like key is stored as [removed] whatever its type (text, number, null, list, object, at any depth), an empty text \"\" stays (D-144, D-146). | exact |"),
    ("| TC-IF-401-04 | IF-401 | Contract | 1 (mock) and 2 (real) | golden 3: the same steps differ only in time and run id (same); one extra check_run is a difference. | exact |",
     "| TC-IF-401-04 | IF-401 | Contract | 1 (mock) and 2 (real) | golden 3 (v2, A-53): the same steps differ only in time and run id (same); one extra check_run is a difference, so are the same types with another payload and one extra event at the end. | exact |"),
]
text = open(sys.argv[1], encoding="utf-8").read()
for old, new in rows:
    if text.count(old) + text.count(new) != 1:
        sys.exit("the row %s is neither the old nor the new one exactly once: check specs/mia/test-spec.md" % old[2:14])
    text = text.replace(old, new)
open(sys.argv[2], "w", encoding="utf-8").write(text)
PY
copy $A/IF-401-run-events.md contracts/IF-401-run-events.md
copy $D/tests/helpers/mocks/if_401_run_events.py tests/helpers/mocks/if_401_run_events.py
copy $D/tests/acceptance/contract/test_if_401_run_events.py tests/acceptance/contract/test_if_401_run_events.py
copy "$SPEC" specs/mia/test-spec.md
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_401_run_events.py
