#!/usr/bin/env bash
# Amendment A-101 (G-V2.STORE, owner's ratings of 2026-11-08): plausibility records for REQ-SLY-013 and REQ-SLY-014 (the requirements of A-100). Both plausible.
# Note: specs/mia/amendments/A-101-note.md
# File that changes (made from the INSTALLED file at run time; a record that is there already is skipped, so a second --do changes nothing):
#   specs/mia/plausibility.yaml   two records inserted in sorted place; nothing else in the file is touched
#   bash tools/apply_amendment_a101.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a101.sh --do      install and run the plausibility check; commit afterwards as "plan: A-101 installed"
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
import yaml
path, work = sys.argv[1:3]
text = open(path, encoding="utf-8").read()

HEAD = "      hardware: HW-target\n      rated: '2026-11-08'\n      rated_by: maldun\n      rating: plausible\n"
NEW = {
    "REQ-SLY-013": "one fixed number, 200 levels of nesting with the document as level 1, the same limit as REQ-GTB-027 and checked exactly on both sides (200 stored, 201 refused); the deepest real document in library, skills and eval has 19 levels (probe of 193 files on 2026-11-08), so the limit is about ten times that and far below the recursion limit of the interpreter (about 496 levels); the check is iterative and takes a few milliseconds (owner rating 2026-11-08)",
    "REQ-SLY-014": "the only number is the limit of one second; the walk is iterative and visits each container once, so the limit has a very large margin; only Python callers can build such a document, JSON has no cycles; behaviour is exact (refused or not) and is tested with a time limit on both backends (owner rating 2026-11-08)",
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
items = yaml.safe_load(text)["plausibility"]["items"]
bad = [k for k in NEW if not isinstance(items[k]["basis"][0], str)]
if bad:
    sys.exit("the basis of %s is not text (a colon followed by a space makes YAML read a mapping); install A-101 by hand" % bad)
open(os.path.join(work, "plausibility.yaml"), "w", encoding="utf-8").write(text)
PY
copy "$WORK/plausibility.yaml" "$FILE"
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== plausibility check of all requirements (the output is kept, so a crash cannot look like no error)"
    if python3 -I ~/.claude/skills/plan-phase/scripts/req_plausibility.py --requirements $(find specs/mia -name requirements.md | sort) --plausibility "$FILE" > "$WORK/check.txt" 2>&1; then echo "exit 0"; else echo "exit $?"; fi
    grep -c "Traceback" "$WORK/check.txt" | sed 's/^/tracebacks: /'
    grep "| ERROR |" "$WORK/check.txt" || echo "errors: none"
    python3 -I - "$FILE" <<'PY2'
import sys
import yaml
items = yaml.safe_load(open(sys.argv[1]))["plausibility"]["items"]
keys = list(items)
print("keys sorted:", keys == sorted(keys), "| items:", len(keys), "| raters:", sorted({v.get("rated_by") for v in items.values()}))
PY2
fi
