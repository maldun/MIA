#!/usr/bin/env bash
# Amendment A-96 (G-V2.STORE Verify, F-05, owner's decision of 2026-11-08): give back the rater, the rating date and the date and owner of an
# accepted risk that the rewrite of specs/mia/plausibility.yaml (commit d80fdb5) changed without a reason.
#   For every record that is in the tag plan-baseline-it2-store AND in the file now, with the same rating AND the same basis, the fields `rated`,
#   `rated_by` and (when the record has one) `accepted_risk.decided` and `accepted_risk.owner` are set to the values of the tag.
#   Not touched: records added since the tag (including the five of A-95), records whose basis was reworded (31, decision open: they are shown
#   in specs/mia/amendments/A-96-basis-pairs.md), every rating, every basis, every other field, the layout of the file.
# Note: specs/mia/amendments/A-96-note.md
#   bash tools/apply_amendment_a96.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a96.sh --do      install and run the checks; commit afterwards as "plan: A-96 installed"
# TAG_FILE=<path> reads the plausibility file of the tag from a file instead of `git show` (for a scratch copy without git).
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
FILE=specs/mia/plausibility.yaml
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
if [ -n "${TAG_FILE:-}" ]; then cp "$TAG_FILE" "$WORK/tag.yaml"; else git show plan-baseline-it2-store:specs/mia/plausibility.yaml > "$WORK/tag.yaml"; fi
python3 -I - "$FILE" "$WORK" <<'PY'
import os
import re
import sys
import yaml

path, work = sys.argv[1:3]
text = open(path, encoding="utf-8").read()
tag = yaml.safe_load(open(os.path.join(work, "tag.yaml"), encoding="utf-8"))["plausibility"]["items"]
now = yaml.safe_load(text)["plausibility"]["items"]


def scalar(value):
    """The value as PyYAML writes it in this file (a date as '2026-10-26' in quotes, a name plain)."""
    return yaml.safe_dump(value, default_flow_style=True, allow_unicode=True, width=10 ** 6).split("\n...")[0].strip()


# the records to restore: in both, the same rating and the same basis
keys = [k for k in tag if k in now and tag[k].get("rating") == now[k].get("rating") and tag[k].get("basis") == now[k].get("basis")]
want = {}
for k in keys:
    fields = {"rated": tag[k].get("rated"), "rated_by": tag[k].get("rated_by")}
    risk_tag, risk_now = tag[k].get("accepted_risk"), now[k].get("accepted_risk")
    if isinstance(risk_tag, dict) and isinstance(risk_now, dict):
        fields["decided"], fields["owner"] = risk_tag.get("decided"), risk_tag.get("owner")
    want[k] = fields

lines = text.split("\n")
out, current, in_items, changed = [], None, False, 0
for line in lines:
    if line.startswith("  items:"):
        in_items = True
    elif in_items and re.match(r"^  \S", line):
        in_items = False
    m = re.match(r"^    ([A-Za-z0-9._-]+):\s*$", line) if in_items else None
    if m:
        current = m.group(1)
    fields = want.get(current) if in_items else None
    if fields:
        for name, indent in (("rated", 6), ("rated_by", 6), ("decided", 8), ("owner", 8)):
            m2 = re.match(r"^%s%s: (.*)$" % (" " * indent, name), line)
            if m2 and name in fields and fields[name] is not None:
                new = "%s%s: %s" % (" " * indent, name, scalar(fields[name]))
                if new != line:
                    line, changed = new, changed + 1
                break
    out.append(line)
if "\n".join(out).count("\n") != text.count("\n"):
    sys.exit("%s: the number of lines changed; install A-96 by hand" % path)
open(os.path.join(work, "plausibility.yaml"), "w", encoding="utf-8").write("\n".join(out))
print("records restored: %d, lines changed: %d" % (len(keys), changed), file=sys.stderr)
PY
copy "$WORK/plausibility.yaml" "$FILE"
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== the restored records equal the tag in rated, rated_by and the accepted risk's decided and owner; ratings and bases unchanged"
    python3 -I - "$FILE" "$WORK/tag.yaml" <<'PY2'
import sys
import yaml
now = yaml.safe_load(open(sys.argv[1]))["plausibility"]["items"]
tag = yaml.safe_load(open(sys.argv[2]))["plausibility"]["items"]
same = [k for k in tag if k in now and tag[k].get("rating") == now[k].get("rating") and tag[k].get("basis") == now[k].get("basis")]
bad = [k for k in same if now[k] != tag[k]]
print("records with the same rating and basis: %d, of them not identical to the tag: %d %s" % (len(same), len(bad), bad[:10]))
PY2
    python3 -I ~/.claude/skills/plan-phase/scripts/req_plausibility.py --requirements $(find specs/mia -name requirements.md | sort) --plausibility "$FILE" 2>&1 | grep -c "| ERROR |" || true
fi
