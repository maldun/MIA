#!/usr/bin/env bash
# A-158 amended: TC-CHA-076 in the Applies to: line of TR-CHAT-006 (protected test-requirements.md). Idempotent; shows the diff.
set -e
cd "$(git rev-parse --show-toplevel)"
P=specs/mia/goals/G-V3.CHAT/amendment-a158/protected-test-requirements-2.patch
if git apply --check -R "$P" 2>/dev/null; then echo "already applied"; exit 0; fi
git apply "$P"; git diff -- specs/mia/test-requirements.md
echo "then: git add specs/mia/test-requirements.md && git commit -m 'plan: A-158 amended, TC-CHA-076 applies to TR-CHAT-006'"
