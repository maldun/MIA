#!/usr/bin/env bash
# A-156 (FB-09): applies the protected part of the amendment to the checkout it is run in. Idempotent: stops if already applied.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
P=specs/mia/goals/G-V3.CHAT/amendment-a156/protected.patch
if git apply --check -R "$P" 2>/dev/null; then echo "already applied"; exit 0; fi
git apply --check "$P"
git apply --stat "$P"
git apply "$P"
bash tools/check_sysml.sh specs/mia/architecture.sysml && python3 -I tools/check_sysml_model.py .
echo "now: git add the 6 files named above, and requirements.md; commit; red tests: python tests/acceptance/test_chat_skill_turns.py (6 red expected)"
