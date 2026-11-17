#!/usr/bin/env bash
# A-158: corrects the assertion of TC-CHA-075 (filters the events to chat_run_status and chat_message). Idempotent; shows the diff.
set -e
cd "$(git rev-parse --show-toplevel)"
P=specs/mia/goals/G-V3.CHAT/amendment-a158/protected-fix-tc-cha-075.patch
if git apply --check -R "$P" 2>/dev/null; then echo "already applied"; exit 0; fi
git apply "$P"; git diff -- tests/acceptance/test_chat_skill_turns.py
echo "then: git add tests/acceptance/test_chat_skill_turns.py && git commit -m 'plan: A-158 TC-CHA-075 compares only the status and message events'"
