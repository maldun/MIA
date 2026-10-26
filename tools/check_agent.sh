#!/usr/bin/env bash
# The agent checks of the plan phase (agent-app skill) on specs/mia: A1 to A15 over requirements, agent view, threat model and suites.
#   bash tools/check_agent.sh            all findings, errors first in the summary line
#   bash tools/check_agent.sh --errors   only the errors
# Environment: EVAL_DIR = folder with suites/ and baselines/ (default: ./eval of this checkout; the injection suites are untracked files of the main checkout),
#              SPEC_DIR = default specs/mia. Read-only. Exit code of agent_check.py (1 with errors).
set -u
cd "$(dirname "$0")/.."
SPEC_DIR="${SPEC_DIR:-specs/mia}"
EVAL_DIR="${EVAL_DIR:-eval}"
SCRIPT="$HOME/.claude/skills/agent-app/scripts/agent_check.py"
[ -f "$SCRIPT" ] || { echo "agent_check.py not found: $SCRIPT"; exit 2; }
out=$(python3 "$SCRIPT" --spec-dir "$SPEC_DIR" --eval-dir "$EVAL_DIR"); code=$?
if [ "${1:-}" = "--errors" ]; then echo "$out" | grep -E "^# |\| ERROR \|"; else echo "$out"; fi
exit $code
