#!/usr/bin/env bash
# Amendment A-99 (G-V2.STORE, owner's ratings of 2026-11-08): plausibility records for REQ-GTB-023 to REQ-GTB-027 (the requirements of A-98).
#   REQ-GTB-023 to 026: plausible. REQ-GTB-027: first rated "questionable, needs a probe", then plausible after the probe (193 real JSON and YAML files in
#   library/, skills/ and eval/, deepest document 19 levels against the limit of 200), rated by the owner.
# Note: specs/mia/amendments/A-99-note.md
# File that changes (made from the INSTALLED file at run time; a record that is there already is skipped, so a second --do changes nothing):
#   specs/mia/plausibility.yaml   five records inserted in sorted place; nothing else in the file is touched
#   bash tools/apply_amendment_a99.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a99.sh --do      install and run the plausibility check; commit afterwards as "plan: A-99 installed"
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
    "REQ-GTB-023": "no number, measurement or model quality depends on it; the behaviour (six record tables, versioned, never deleted) is fixed by an acceptance criterion, golden 17, the contract mock and TC-GTB-024; realised in T-08 (owner rating 2026-11-08)",
    "REQ-GTB-024": "no number, measurement or model quality depends on it; the shape rules are fixed by an acceptance criterion, golden 17, the contract mock and TC-GTB-025; realised in T-08 (owner rating 2026-11-08)",
    "REQ-GTB-025": "no number, measurement or model quality depends on it; the lookup of the ends in the context nodes is fixed by an acceptance criterion, golden 18, the contract mock and TC-GTB-026; realised in T-08 (owner rating 2026-11-08)",
    "REQ-GTB-026": "no number, measurement or model quality depends on it; the lookup of the members by the kind of the header is fixed by an acceptance criterion, golden 19, the contract mock and TC-GTB-027; realised in T-08 (owner rating 2026-11-08)",
    "REQ-GTB-027": "one fixed number, 200 levels of nesting with the record as level 1, checked iteratively and exactly on both sides (150 accepted, 300 refused); probe done on 2026-11-08 over 193 real JSON and YAML files in library, skills and eval, the deepest document has 19 levels (a whole pipeline), so the limit is about ten times the deepest real document and far below the recursion limit of about 1000 (owner rating 2026-11-08 after the probe)",
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
    sys.exit("the basis of %s is not text (a colon followed by a space makes YAML read a mapping); install A-99 by hand" % bad)
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
