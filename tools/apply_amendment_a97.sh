#!/usr/bin/env bash
# Amendment A-97 (F-05 follow-up, owner's ratings of 2026-11-08): plausibility records for requirements that have none.
#   REQ-CLV-023, REQ-WFM-031, 033, 034, 035, 037, 039, 059, 068: nine requirements, all rated plausible by the owner.
#   All nine lie outside the scope of G-V2.STORE; the rating belongs to the Plan of their own goals and is recorded here so that
#   req_plausibility has no gap.
# Note: specs/mia/amendments/A-97-note.md
# File that changes (made from the INSTALLED file at run time; a record that is there already is skipped, so a second --do changes nothing):
#   specs/mia/plausibility.yaml   the records are inserted in sorted place; nothing else in the file is touched
#   bash tools/apply_amendment_a97.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a97.sh --do      install and run the plausibility check; commit afterwards as "plan: A-97 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
FILE=specs/mia/plausibility.yaml
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 -I - "$FILE" "$WORK" <<'PY'
import os
import re
import sys
path, work = sys.argv[1:3]
text = open(path, encoding="utf-8").read()

HEAD = "      hardware: HW-target\n      rated: '2026-11-08'\n      rated_by: Stefan Reiterer\n      rating: plausible\n"
NEW = {
    "REQ-CLV-023": "a mock-driven browser check with exact figures; no measured number depends on it; the part that is deferred is recorded as TD-01 (owner rating 2026-11-08)",
    "REQ-WFM-031": "exact figures on a card that the task reported, at most 2 updates per second is a rate limit on a timer; a task that reports nothing gets the time only (owner rating 2026-11-08)",
    "REQ-WFM-033": "pause is a flag checked before each step and 5 s of constant used time is a check on a clock; a step that is running when the pause comes ends first (owner rating 2026-11-08)",
    "REQ-WFM-035": "a stored class per model and one question for a model that is new and not clearly local; exact behaviour in the chat, no measured number (owner rating 2026-11-08)",
    "REQ-WFM-037": "limits from the configuration, refusal that says so and a byte-for-byte download; no measured number; the allowed names and types are fixed by the acceptance criterion (owner rating 2026-11-08)",
    "REQ-WFM-034":"the time cap of 1800 s of work time is a configurable value checked with a fake clock; counting only work time (no pause, no waiting for the user) is a matter of design, not of measurement (owner rating 2026-11-08)",
    "REQ-WFM-068": "exact behaviour and no number: a retired transform or skill is hidden from users and stays loadable by a check that names it (owner rating 2026-11-08)",
    "REQ-WFM-039":"loading a skill from a folder of its own is standard; the inspection that no core file names a skill id is exact; the part that is deferred is recorded as TD-04 (owner rating 2026-11-08)",
    "REQ-WFM-059": "a fixed rule on the dev split of a suite with the same pin; the numbers of the criterion are open in the plan notes and are fixed in the Plan of the conversion goal, so the rating is of the rule, not of a number (owner rating 2026-11-08)",
}


def record(key, basis):
    return "    %s:\n      basis:\n      - %s\n%s" % (key, basis, HEAD)


for key, basis in sorted(NEW.items()):
    if "\n    %s:\n" % key in text:
        continue
    start = text.index("\n  items:\n") + len("\n  items:\n")
    end = text.index("\n  references:", start)
    keys = [(m.group(1), start + m.start()) for m in re.finditer(r"^    ([A-Za-z0-9._-]+):\s*$", text[start:end], re.M)]
    after = [pos for k, pos in keys if k > key]
    at = min(after) if after else end + 1
    text = text[:at] + record(key, basis) + text[at:]
open(os.path.join(work, "plausibility.yaml"), "w", encoding="utf-8").write(text)
PY
copy "$WORK/plausibility.yaml" "$FILE"
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== plausibility check of all requirements: records still missing, and the order of the keys"
    python3 -I ~/.claude/skills/plan-phase/scripts/req_plausibility.py --requirements $(find specs/mia -name requirements.md | sort) --plausibility "$FILE" 2>&1 | grep "no plausibility record" || echo none
    python3 -I - "$FILE" <<'PY2'
import sys
import yaml
keys = list(yaml.safe_load(open(sys.argv[1]))["plausibility"]["items"])
print("keys sorted:", keys == sorted(keys), "| items:", len(keys))
PY2
fi
