#!/usr/bin/env bash
# A-158: the protected test-requirements.md (Applies to: lines of TC-CHA-073..075 and TC-CLV-053). Idempotent; shows the diff.
set -e
cd "$(git rev-parse --show-toplevel)"
P=specs/mia/goals/G-V3.CHAT/amendment-a158/protected-test-requirements.patch
if git apply --check -R "$P" 2>/dev/null; then echo "already applied"; exit 0; fi
git apply --stat "$P"; git apply "$P"; git diff -- specs/mia/test-requirements.md
echo "then: git add specs/mia/test-requirements.md && git commit -m 'plan: A-158 test requirements apply to TC-CHA-073..075, TC-CLV-053'"
