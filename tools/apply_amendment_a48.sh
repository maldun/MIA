#!/usr/bin/env bash
# Amendment A-48 (N-1.2, owner 2026-10-31, correcting D-137 (4)): IF-111 v2, an unknown expression name shows `neutral` (v1, A-04: kept the current one).
# Protected files that change:
#   contracts/IF-111-character-bridge.md                               v2: the expression row, golden example 3, the version line
#   tests/helpers/mocks/if_111_character_bridge.mjs                    an unknown name sets `neutral`
#   tests/acceptance/contract/test_if_111_character_bridge.test.mjs    TC-IF-111-02 expects `neutral`
#   specs/mia/test-spec.md                                             the row of TC-IF-111-02 (made from the installed file at run time, so it cannot go stale)
# After the install the real side of TC-IF-111-02 (the Godot bridge) is red until N-1.2 changes the bridge and the backend (test-first, branch v1-n12).
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1).
#   bash tools/apply_amendment_a48.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a48.sh --do      install and run the JS contract suites; commit afterwards as "plan: A-48 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-48
D=specs/mia/contract-drafts
SPEC=$(mktemp)
trap 'rm -f "$SPEC"' EXIT
python3 - specs/mia/test-spec.md "$SPEC" <<'PY'
import sys
old = "| TC-IF-111-02 | IF-111 | Contract | 1 (mock) and 2 (real) | golden 3: an unknown expression keeps the current one | exact |"
new = "| TC-IF-111-02 | IF-111 | Contract | 1 (mock) and 2 (real) | golden 3: an unknown expression shows `neutral` (A-48) | exact |"
text = open(sys.argv[1], encoding="utf-8").read()
if old not in text and new not in text:
    sys.exit("the row of TC-IF-111-02 is neither the old nor the new one: check specs/mia/test-spec.md")
open(sys.argv[2], "w", encoding="utf-8").write(text.replace(old, new))
PY
copy $A/IF-111-character-bridge.md contracts/IF-111-character-bridge.md
copy $D/tests/helpers/mocks/if_111_character_bridge.mjs tests/helpers/mocks/if_111_character_bridge.mjs
copy $D/tests/acceptance/contract/test_if_111_character_bridge.test.mjs tests/acceptance/contract/test_if_111_character_bridge.test.mjs
copy "$SPEC" specs/mia/test-spec.md
finish
echo
node --test tests/acceptance/contract/test_if_111_character_bridge.test.mjs
