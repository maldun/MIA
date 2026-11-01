#!/usr/bin/env bash
# Amendment A-73 (N-1 integration step 2, 2026-11-01; owner decision D-175): the Character view N-1.2 is integrated. The real side of IF-111 is the Godot bridge
# test ui/godot/tools/test_bridge.gd (D-155), which cannot run inside the node scenario; so READY gets N-1.2, the JS real cases of IF-111 keep a skip whose
# reason names test_bridge.gd, and realSubject('IF-111') is the mock, openly. Note: specs/mia/amendments/A-73/A-73-note.md
# Made from the INSTALLED files at run time (A-72 must be installed), each edit refused when its anchor is not found exactly once:
#   tests/helpers/integration.mjs   READY gets N-1.2; realSubject('IF-111') returns the CharacterMock (A-73)
#   tests/helpers/contract.mjs      the skip reason of IF-111 names test_bridge.gd
#   specs/mia/test-spec.md          the stage column of TC-IF-111-01 to -06 names the real side
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a73.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a73.sh --do      install, run the IF-111 suite and N-1 step_02; commit afterwards as "plan: A-73 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - tests/helpers/integration.mjs tests/helpers/contract.mjs specs/mia/test-spec.md "$WORK" <<'PY'
import os
import re
import sys
integration, contract, spec, work = sys.argv[1:5]
read = lambda path: open(path, encoding="utf-8").read()


def write(name, text):
    open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def edit(text, old, new, where, what, done=None):
    """old -> new exactly once; a text that has the new part already (done) is left as it is."""
    if (done or new) in text:
        return text
    if text.count(old) != 1:
        sys.exit("%s: %s is not found exactly once; install A-73 by hand" % (where, what))
    return text.replace(old, new)


text = read(integration)
throw = "  throw new Error(`the real adapter of ${iface} is added by the integration step of its node`);\n"
text = edit(text, throw,
            "  // A-73 (D-175): the real Character view is Godot; its bridge is checked by ui/godot/tools/test_bridge.gd, not inside this scenario\n"
            "  if (iface === 'IF-111') return new CharacterMock();\n" + throw,
            integration, "the throw in realSubject", done="if (iface === 'IF-111') return new CharacterMock();")
match = re.search(r"^export const READY = new Set\((\[[^\]]*\])?\);(.*)$", text, re.M)
if not match:
    sys.exit("%s: the READY line is not found in its usual form; install A-73 by hand" % integration)
nodes = re.findall(r"'([^']+)'", match.group(1) or "")
if "N-1.2" not in nodes:
    nodes.append("N-1.2")
comment = match.group(2)
if "A-73" not in comment:
    comment = comment.rstrip()[:-1] + "; A-73: the Character view)" if comment.rstrip().endswith(")") else comment.rstrip() + " (A-73: the Character view)"
text = text[:match.start()] + "export const READY = new Set([%s]);%s" % (", ".join("'%s'" % n for n in nodes), comment) + text[match.end():]
write("integration.mjs", text)

text = read(contract)
old = "  'IF-111': 'N-1.2 Character view not integrated yet',\n"
new = "  'IF-111': 'real side: ui/godot/tools/test_bridge.gd in Godot (D-155, A-73)',\n"
write("contract.mjs", edit(text, old, new, contract, "the IF-111 line"))

text = read(spec)
for n in range(1, 7):
    row = "| TC-IF-111-0%d | IF-111 | Contract | " % n
    old, new = row + "1 (mock) and 2 (real) |", row + "1 (mock); real: `ui/godot/tools/test_bridge.gd` (Godot, D-155; the JS real side skips) |"
    text = edit(text, old, new, spec, "the stage column of TC-IF-111-0%d" % n)
write("test-spec.md", text)
PY
copy "$WORK/integration.mjs" tests/helpers/integration.mjs
copy "$WORK/contract.mjs" tests/helpers/contract.mjs
copy "$WORK/test-spec.md" specs/mia/test-spec.md
finish
echo
echo "== IF-111 suite and N-1 steps"
node --test tests/acceptance/contract/test_if_111_character_bridge.test.mjs "tests/integration/N-1/step_0*/test_step.test.mjs" 2>&1 | grep -E "^not ok|^ok .*SKIP|^# (pass|fail|skipped)"
