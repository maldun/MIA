#!/usr/bin/env bash
# Amendment A-111 (G-V2.TOOLBOX): the part `transforms` of IF-203 v1 (kind `transforms`, trust and lifecycle with get_meta, set_meta, get_trust, set_trust, get_lifecycle,
# set_lifecycle), the text that the mock tests/helpers/mocks/if_203_transforms.py, the suite tests/acceptance/contract/test_if_203_v1_transforms.py and the real library fix.
# Note: specs/mia/amendments/A-111-note.md. A-110 and A-112 (the tables transform_meta and transforms) are installed.
# Files that change (made from the INSTALLED file at run time; every edit is skipped when it is done already and refused when its anchor is not found exactly once, so a second
# --do changes nothing; if MODEL or CONVERT changed the same lines first, the anchor fails and nothing is written: merge by hand):
#   contracts/IF-203-workflow-library.md   operations, errors, golden examples, version history; the version number goes up by one (v0 -> v1 today)
#   specs/mia/review-log.md   row D-nnn (installed), the next free id of the TOOLBOX range D-220..239, appended
# NOT changed here: the mock, the suite and the library (installed and built already), the snapshot part (CONVERT, A-121) and the kind `skills` (MODEL).
#   bash tools/apply_amendment_a111.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a111.sh --do      install; commit afterwards as "contracts: A-111 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
C203=${A111_IF203:-contracts/IF-203-workflow-library.md}
LOG=${A111_LOG:-specs/mia/review-log.md}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$C203" "$LOG" "$WORK" <<'PY'
import os
import re
import sys
c203, log, work = sys.argv[1:4]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def once(text, old, new, where):
    if new in text:
        return text
    if text.count(old) == 1:
        return text.replace(old, new)
    sys.exit("anchor not found exactly once (%d) in %s: %r" % (text.count(old), where, old[:70]))


t = read(c203)
done = "A-111" in t
m = re.match(r"(# IF-203 – [^\n]*, v)(\d+)\n", t)
if not m:
    sys.exit("no version in the title of " + c203)
version = int(m.group(2)) + (0 if done else 1)
if not done:
    t = m.group(1) + str(version) + "\n" + t[m.end():]
V = "**[v%d]**" % version

OPS = (
    "| " + V + " `list_ids(\"transforms\")`, `read(\"transforms\", id, version=None)`, `save(\"transforms\", id, doc, author, expected_version=None)`, `history(\"transforms\", id)` | the kind `transforms` | as for the other kinds | "
    "`doc` is {id, version, inputs, outputs, code}: the versioned code of a transform (table `transforms`, IF-302 v9), `version` is the version of the code as the file states it; a missing, empty or null `code` is valid (a stub transform); "
    "every save is a new immutable version; `read` also gives `trust` and `lifecycle`; the first `save` of an id creates the meta record (table `transform_meta`, IF-302 v8) with trust `untrusted` and lifecycle `draft`, a later save leaves it as it is (REQ-WFM-092) |\n"
    "| " + V + " `get_meta(id)` | a transform id | `{\"trust\",\"lifecycle\"}` and the optional `reason`, `evidence`, `baseline_allowed`, `shipped`, `changed_by` | |\n"
    "| " + V + " `get_trust(id)`, `get_lifecycle(id)` | a transform id | the value | the read side of the two setters |\n"
    "| " + V + " `set_trust(id, trust, author)` | `untrusted`, `trusted` | `{\"trust\"}` | who may set it (only the owner trusts, REQ-WFM-054) is a rule of the Workflow management, not of the library |\n"
    "| " + V + " `set_lifecycle(id, lifecycle, author, evidence=None)` | `draft`, `tested`, `retired` | `{\"lifecycle\"}` | `evidence` is stored when given; that `tested` needs it is a rule of the Workflow management (REQ-WFM-067) |\n"
    "| " + V + " `set_meta(id, author, **fields)` | trust, lifecycle, reason, evidence, baseline_allowed (boolean), shipped (boolean), changed_by | the meta record | one new version of the meta record; `changed_by` is set to the author |\n")
estimate = [l for l in t.split("\n") if l.startswith("| `estimate(id, version=None)`")]
if len(estimate) != 1:
    sys.exit("anchor not found exactly once: the estimate row of " + c203)
if "get_meta(id)" not in t:
    t = t.replace(estimate[0] + "\n", estimate[0] + "\n" + OPS, 1)

ERRORS = ("| " + V + " a value outside the lists of trust or lifecycle, an optional meta field of the wrong type or an unknown field | `ServiceError(\"invalid\", rule=\"schema\", detail=<field>)` | the meta record is unchanged |\n")
promo = [l for l in t.split("\n") if l.startswith("| promotion without specification or benchmark")]
if len(promo) != 1:
    sys.exit("anchor not found exactly once: the promotion row of " + c203)
if 'detail=<field>' not in t:
    t = t.replace(promo[0] + "\n", promo[0] + "\n" + ERRORS, 1)

GOLD = (
    "4. " + V + " Typical: a new transform is untrusted and draft; a second save is version 2 (TC-IF-203-05).\n"
    "5. " + V + " Typical: trusted and tested (evidence `run-1`) survive version 2; version 1 still reads its own document (TC-IF-203-06).\n"
    "6. " + V + " Failure: `fine` is refused for trust and for lifecycle with the field as detail, the statuses stay (TC-IF-203-07).\n"
    "7. " + V + " Edge: the optional meta fields are kept, a boolean field with a text is refused (TC-IF-203-08); unknown ids and stale versions are `not_found` and `conflict` (TC-IF-203-09).\n")
t = once(t, "3. Edge: `estimate` of a graph with a session node counts its maximum cycles times the cost of one cycle.\n",
         "3. Edge: `estimate` of a graph with a session node counts its maximum cycles times the cost of one cycle.\n" + GOLD, c203)

lines = t.split("\n")
if "A-111" not in "\n".join(lines).split("## Version history")[-1]:
    last = max(i for i, l in enumerate(lines) if re.match(r"\| v\d+ \|", l))
    lines.insert(last + 1, "| v%d | 2026-11-11 | the kind `transforms` and its meta record: operations `get_meta`, `get_trust`, `get_lifecycle`, `set_trust`, `set_lifecycle`, `set_meta`, golden examples 4 to 7 (suite TC-IF-203-05 to 09) | A-90, A-111 |" % version)
out("if203", "\n".join(lines))

l = read(log)
if "A-111 installed" not in l:
    used = [int(n) for n in re.findall(r"^\| D-(2[23]\d) \|", l, re.M)]
    new_id = "D-%d" % (max(used) + 1 if used else 220)
    l = l + ("" if l.endswith("\n") else "\n") + (
        "| %s | **A-111 installed, G-V2.TOOLBOX, 2026-11-11.** `contracts/IF-203-workflow-library.md` v%d has the kind `transforms` with trust and lifecycle "
        "(the table `transforms` of IF-302 v9, the meta record in `transform_meta` of IF-302 v8). Mock, suite and library were installed before. |\n" % (new_id, version))
out("log", l)
PY
copy "$WORK/if203" "$C203"
copy "$WORK/log" "$LOG"
finish
if [ "$do_it" = 1 ]; then
    echo "checks after --do:"
    python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia 2>&1 | tail -3 || true
fi
