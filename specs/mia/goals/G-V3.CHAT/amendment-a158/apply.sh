#!/usr/bin/env bash
# A-158: the protected files (test-requirements.md: Applies to: lines; tests/acceptance/test_chat_skill_turns.py: TC-CHA-073..075, red). Idempotent; shows the diff.
set -e
cd "$(git rev-parse --show-toplevel)"
for P in specs/mia/goals/G-V3.CHAT/amendment-a158/protected-test-requirements.patch specs/mia/goals/G-V3.CHAT/amendment-a158/protected-test-chat-skill-turns.patch; do
  if git apply --check -R "$P" 2>/dev/null; then echo "already applied: $P"; continue; fi
  git apply --stat "$P"; git apply "$P"
done
git diff --stat -- specs/mia/test-requirements.md tests/acceptance/test_chat_skill_turns.py
echo "then: git add specs/mia/test-requirements.md tests/acceptance/test_chat_skill_turns.py && git commit -m 'plan: A-158 test requirements and red acceptance tests TC-CHA-073..075'"
