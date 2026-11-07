#!/usr/bin/env bash
# Amendment A-96 (G-V2.STORE Verify, F-05, owner's decisions of 2026-11-08): undo the unexplained changes of specs/mia/plausibility.yaml
# (rewrite of commit d80fdb5) and use one rater name.
#   1. For every record that is in the tag plan-baseline-it2-store AND in the file now with the same rating, the fields `rated`, `rated_by` and
#      (when the record has one) `accepted_risk.decided` and `accepted_risk.owner` are set to the values of the tag (433 records with the same
#      basis, 31 more with a reworded basis).
#   2. For the 31 records whose basis was reworded to one generic sentence, the basis of the tag is restored as well (the pairs are in
#      specs/mia/amendments/A-96-basis-pairs.md). The four records of A-95 (re-rated on their current text) keep their basis.
#   3. The owner's name is `maldun` everywhere in the file: every `rated_by`, every `accepted_risk.owner` and every "... by Stefan Reiterer" in
#      `accepted_risk.decided` (the owner's decision: maldun is the nickname of Stefan Reiterer; the records of A-95 and the added ones follow).
#   Not touched: any rating, any other basis, any other field, the layout of the file (same number of lines apart from the basis texts).
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
tag_text = open(os.path.join(work, "tag.yaml"), encoding="utf-8").read()
tag = yaml.safe_load(tag_text)["plausibility"]["items"]
now = yaml.safe_load(text)["plausibility"]["items"]
A95 = {"REQ-API-004", "REQ-API-007", "REQ-CLV-011", "REQ-VPB-002"}   # re-rated on their current text: they keep their basis
NAME = "maldun"
OLD_NAME = "Stefan Reiterer"


def scalar(value):
    """The value as PyYAML writes it in this file (a date as '2026-10-26' in quotes, a name plain)."""
    return yaml.safe_dump(value, default_flow_style=True, allow_unicode=True, width=10 ** 6).split("\n...")[0].strip()


def basis_blocks(source):
    """{record key: the lines of its `basis:` block, exactly as written} from the text of a plausibility file."""
    found, key, block = {}, None, None
    for line in source.split("\n"):
        m = re.match(r"^    ([A-Za-z0-9._-]+):\s*$", line)
        if m:
            key, block = m.group(1), None
        elif key and line == "      basis:":
            block = [line]
            found[key] = block
        elif block is not None:
            if re.match(r"^      [A-Za-z_]+:", line) or not line.startswith("      "):
                block = None
            else:
                block.append(line)
    return found


same = [k for k in tag if k in now and tag[k].get("rating") == now[k].get("rating") and tag[k].get("basis") == now[k].get("basis")]
reworded = [k for k in tag if k in now and k not in A95 and tag[k].get("rating") == now[k].get("rating") and tag[k].get("basis") != now[k].get("basis")]
want = {}
for k in same + reworded:
    fields = {"rated": tag[k].get("rated"), "rated_by": tag[k].get("rated_by")}
    risk_tag, risk_now = tag[k].get("accepted_risk"), now[k].get("accepted_risk")
    if isinstance(risk_tag, dict) and isinstance(risk_now, dict):
        fields["decided"], fields["owner"] = risk_tag.get("decided"), risk_tag.get("owner")
    want[k] = fields
tag_basis = basis_blocks(tag_text)
for k in reworded:
    if k not in tag_basis:
        sys.exit("%s: no basis block of %s in the tag; install A-96 by hand" % (path, k))

out, current, in_items, skipping = [], None, False, False
for line in text.split("\n"):
    if line.startswith("  items:"):
        in_items = True
    elif in_items and re.match(r"^  \S", line):
        in_items = False
    m = re.match(r"^    ([A-Za-z0-9._-]+):\s*$", line) if in_items else None
    if m:
        current, skipping = m.group(1), False
    if skipping:                                  # the lines of the reworded basis go; the tag's block was written already
        if re.match(r"^      [A-Za-z_]+:", line):
            skipping = False
        else:
            continue
    if in_items and current in reworded and line == "      basis:":
        out.extend(tag_basis[current])
        skipping = True
        continue
    fields = want.get(current) if in_items else None
    for name, indent in (("rated", 6), ("rated_by", 6), ("decided", 8), ("owner", 8)):
        m2 = re.match(r"^%s%s: (.*)$" % (" " * indent, name), line) if in_items else None
        if m2:
            if fields and name in fields and fields[name] is not None:
                line = "%s%s: %s" % (" " * indent, name, scalar(fields[name]))
            break
    out.append(line)

# the owner's name: one name everywhere in the items (rater, risk owner, "decided ... by <name>")
final = []
for number, line in enumerate(out):
    if number == 0:                                # the header comment names the rater too (the tag says maldun)
        line = line.replace("rated by %s." % OLD_NAME, "rated by %s." % NAME)
    line = re.sub(r"^(      rated_by|        owner): %s$" % re.escape(OLD_NAME), r"\1: %s" % NAME, line)
    line = re.sub(r"^(        decided: .*) by %s$" % re.escape(OLD_NAME), r"\1 by %s" % NAME, line)
    final.append(line)
open(os.path.join(work, "plausibility.yaml"), "w", encoding="utf-8").write("\n".join(final))
print("records restored: %d (basis restored: %d)" % (len(want), len(reworded)), file=sys.stderr)
PY
copy "$WORK/plausibility.yaml" "$FILE"
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== restored records equal the tag; no other rater or owner name than maldun; ratings unchanged"
    python3 -I - "$FILE" "$WORK/tag.yaml" <<'PY2'
import sys
import yaml
now = yaml.safe_load(open(sys.argv[1]))["plausibility"]["items"]
tag = yaml.safe_load(open(sys.argv[2]))["plausibility"]["items"]
A95 = {"REQ-API-004", "REQ-API-007", "REQ-CLV-011", "REQ-VPB-002"}
common = [k for k in tag if k in now and k not in A95]
bad = [k for k in common if now[k] != tag[k]]
names = {now[k].get("rated_by") for k in now} | {(now[k].get("accepted_risk") or {}).get("owner") for k in now} - {None}
print("records in the tag (without A-95's four): %d, not identical to the tag: %d %s" % (len(common), len(bad), bad[:10]))
print("rater and owner names in the file:", sorted(names))
print("ratings changed against the tag:", [k for k in tag if k in now and tag[k]["rating"] != now[k]["rating"]])
PY2
    python3 -I ~/.claude/skills/plan-phase/scripts/req_plausibility.py --requirements $(find specs/mia -name requirements.md | sort) --plausibility "$FILE" 2>&1 | grep -c "| ERROR |" || true
fi
