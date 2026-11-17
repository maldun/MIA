#!/usr/bin/env bash
# A-158 (T-09): the integration check TC-CHA-068 follows A-156 and A-158 (it was red since A-156: it expected one status message per phase). Idempotent; shows the diff.
set -e
cd "$(git rev-parse --show-toplevel)"
P=specs/mia/goals/G-V3.CHAT/amendment-a158/protected-integration-tc-cha-068.patch
if git apply --check -R "$P" 2>/dev/null; then echo "already applied"; exit 0; fi
git apply "$P"; git diff -- tests/integration/G-V3/test_run_end_to_end.py
echo "then: git add tests/integration/G-V3/test_run_end_to_end.py && git commit -m 'plan: A-158 integration check TC-CHA-068 follows A-156 and A-158'"
