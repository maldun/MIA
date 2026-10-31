#!/usr/bin/env bash
# Amendment A-58 (N-1.2 Verify finding F5, owner 2026-10-31, D-155): IF-111 v3, the page waits up to 30 s for `ready` (v2 said 15 s), as
# templates/static/chat/character.js (LOAD_TIMEOUT_MS = 30000) does. Text only. Note: specs/mia/amendments/A-58/A-58-note.md
# Protected file that changes:
#   contracts/IF-111-character-bridge.md   v3: the title, the bound "time from iframe load to `ready`", the version line
# Made from the INSTALLED contract at run time (the three lines are replaced, each found exactly once), so a later change of IF-111 is kept; the
# result must equal the draft specs/mia/amendments/A-58/IF-111-character-bridge.md, else the script stops (the draft is stale or the contract moved on).
# Unchanged: the mock, the suite (neither checks the 15 s), specs/mia/test-spec.md (no case names the bound).
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1).
#   bash tools/apply_amendment_a58.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a58.sh --do      install and run the JS contract suite; commit afterwards as "plan: A-58 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-58
BUILT=$(mktemp)
trap 'rm -f "$BUILT"' EXIT
python3 - contracts/IF-111-character-bridge.md "$BUILT" <<'PY'
import sys
installed, out = sys.argv[1:3]
text = open(installed, encoding="utf-8").read()
v2_line = "| v2 | 2026-10-31 | an unknown expression name shows `neutral` again (owner); the Godot bridge and the backend follow | A-48 |\n"
v3_line = "| v3 | 2026-10-31 | the page waits up to 30 s for `ready` (was 15 s), as `character.js` does (owner, D-155) | A-58 |\n"
edits = [
    ("# IF-111 – Character bridge, v2\n", "# IF-111 – Character bridge, v3\n"),
    ("| time from iframe load to `ready` | at most 15 s, else the page treats it as failed (`LOAD_TIMEOUT_MS`) | REQ-FE-006 |\n",
     "| time from iframe load to `ready` | at most 30 s, else the page treats it as failed (`LOAD_TIMEOUT_MS`; A-58, v2 said 15 s) | REQ-FE-006 |\n"),
    (v2_line, v2_line + v3_line),
]
if v3_line in text:
    open(out, "w", encoding="utf-8").write(text)          # installed already: the copy below reports "unchanged"
    sys.exit(0)
for old, new in edits:
    if text.count(old) != 1:
        sys.exit("A-58: this line is not in contracts/IF-111-character-bridge.md exactly once: " + old.strip())
    text = text.replace(old, new)
open(out, "w", encoding="utf-8").write(text)
PY
cmp -s "$BUILT" "$A/IF-111-character-bridge.md" || { echo "A-58: the contract built from the installed one differs from the draft $A/IF-111-character-bridge.md:"; diff "$A/IF-111-character-bridge.md" "$BUILT" || true; exit 1; }
copy "$BUILT" contracts/IF-111-character-bridge.md
finish
echo
node --test tests/acceptance/contract/test_if_111_character_bridge.test.mjs
