#!/usr/bin/env bash
# Amendment A-95 (G-V2.STORE Verify, F-05 and the open rating of REQ-GTB-022, owner's ratings of 2026-11-08): five plausibility records.
#   REQ-GTB-022 (new with A-93) and four requirements that lost their record in the rewrite of specs/mia/plausibility.yaml since the tag
#   plan-baseline-it2-store: REQ-API-004, REQ-API-007, REQ-VPB-002, REQ-CLV-011. All four changed after their first rating of 2026-10-26
#   (D-149, D-153, D-157, D-163, D-165), so they are rated again on the current text, not restored.
# Note: specs/mia/amendments/A-95-note.md
# File that changes (made from the INSTALLED file at run time; a record that is there already is skipped, so a second --do changes nothing):
#   specs/mia/plausibility.yaml   five records inserted in sorted place; nothing else in the file is touched
#   bash tools/apply_amendment_a95.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a95.sh --do      install and run the plausibility check; commit afterwards as "plan: A-95 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
FILE=specs/mia/plausibility.yaml
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$FILE" "$WORK" <<'PY'
import os
import sys
path, work = sys.argv[1:3]
text = open(path, encoding="utf-8").read()

HEAD = "      hardware: HW-target\n      rated: '2026-11-08'\n      rated_by: Stefan Reiterer\n      rating: plausible\n"


def record(key, basis):
    lines = "".join("      - %s\n" % line for line in basis)
    return "    %s:\n      basis:\n%s%s" % (key, lines, HEAD)


# (key, the key of the record it goes before, basis)
NEW = [
    ("REQ-API-004", "REQ-API-005",
     ["limits are exact counts (5 failed logins, a 60 s window) judged on the host clock, no measurement uncertainty; the text of D-153 matches the code, IF-101 and TC-IF-101-02; realised and Verified in v0.1.0 (owner rating 2026-11-08)"]),
    ("REQ-API-007", "REQ-API-008",
     ["the limit is an exact count (10 messages per 60 s, the setting chat_rate_per_minute, default 10) and the refusal is rate_limited; fixed by D-149 and A-54 (IF-101 v12); realised and Verified in v0.1.0; whether 10 suits real use is for Validate (owner rating 2026-11-08)"]),
    ("REQ-CLV-011", "REQ-CLV-012",
     ["no number, measurement or model quality depends on it; the behaviour (list, change, delete, due time of a task) is fixed by an acceptance criterion and a mock; realised and Verified in v0.1.0 (D-163, D-165; owner rating 2026-11-08)"]),
    ("REQ-GTB-022", "REQ-LOG-001",
     ["no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion, a contract mock and golden 16; realised in T-07 (27cba26) with the contract suite, TC-GTB-023 and the old suites green (owner rating 2026-11-08)"]),
    ("REQ-VPB-002", "REQ-VPB-003",
     ["the window is 3 s after the Stop or until the next answer begins, checked by the browser check TC-VPB-007 on the reference browser; the 3 s are a product guess because lines carry no answer id (D-157, D-165); realised and Verified in v0.1.0; whether 3 s suits real use is for Validate (owner rating 2026-11-08)"]),
]
for key, before, basis in NEW:
    if "\n    %s:\n" % key in text:
        continue
    anchor = "\n    %s:\n" % before
    if text.count(anchor) != 1:
        sys.exit("%s: the record %s is not found exactly once; install A-95 by hand" % (path, before))
    at = text.index(anchor) + 1
    text = text[:at] + record(key, basis) + text[at:]
open(os.path.join(work, "plausibility.yaml"), "w", encoding="utf-8").write(text)
PY
copy "$WORK/plausibility.yaml" "$FILE"
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== plausibility check of the node requirements (no record missing for the five)"
    python3 -I ~/.claude/skills/plan-phase/scripts/req_plausibility.py --requirements $(find specs/mia -name requirements.md | sort) --plausibility "$FILE" 2>&1 | grep -E "REQ-GTB-022|REQ-API-004|REQ-API-007|REQ-VPB-002|REQ-CLV-011" || echo none
fi
