#!/usr/bin/env bash
# A-160: the red acceptance tests TC-CHA-077 to 080 and TC-WFM-142 as a new protected file tests/acceptance/test_end_message.py. Idempotent; shows what it adds.
# Run tools/apply_amendment_a160.sh first (requirements, test specs, test requirements). The tests stay red until A-160 is built.
set -e
cd "$(git rev-parse --show-toplevel)"
P=specs/mia/goals/G-V3.CHAT/amendment-a160/protected-red-tests.patch
if git apply --check -R "$P" 2>/dev/null; then echo "already applied"; exit 0; fi
git apply --stat "$P"; git apply "$P"
echo "applied: tests/acceptance/test_end_message.py (5 tests, red until the code of A-160 exists)"
echo "then: git add tests/acceptance/test_end_message.py && git commit -m 'plan: A-160 red acceptance tests TC-CHA-077 to 080 and TC-WFM-142'"
