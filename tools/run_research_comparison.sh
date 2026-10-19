#!/bin/bash
# The measurements of the research planners (ui/REQUIREMENTS_CORE.md 13b), 3 repeats each, about 30 minutes with MIA idle (it needs the GPU).
# Run from anywhere:  bash tools/run_research_comparison.sh [output folder]     (default: data/eval/comparison-<date>)
# Each run is saved by the harness in data/eval; the reports and the paired comparisons are written to the output folder.
# Reference results so far: eval/baselines/research-planners.md and research-escalate.md.
cd "$(dirname "$0")/.." || exit 1
PYTHON="${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia/bin/python}"
OUT="${1:-data/eval/comparison-$(date +%Y%m%d)}"
mkdir -p "$OUT"
run() { "$PYTHON" -W ignore tools/eval.py "$@"; }
# 1. the typed planner alone (variant C) against the checked planner (B), 36 plans
run run plans --variant typed --pipeline plan.typed@1 --repeats 3 --quiet > "$OUT/plans_typed.txt" 2>&1
# 2. the pipelines with the typed plan (escalate@3) on both research suites
run run research_compound --variant escalate3 --pipeline research.escalate@3 --repeats 3 --quiet > "$OUT/compound_escalate3.txt" 2>&1
run run research --variant escalate3 --pipeline research.escalate@3 --repeats 3 --quiet > "$OUT/research_escalate3.txt" 2>&1
# 3. escalate@2 again, now with the fix of the verbatim rule (the first measurement had the bug)
run run research_compound --variant escalate2b --pipeline research.escalate@2 --repeats 3 --quiet > "$OUT/compound_escalate2b.txt" 2>&1
# 4. paired comparisons (the variants plans/checked, research_compound/escalate and research/escalate are in data/eval already if it was not cleaned)
run compare plans checked typed > "$OUT/cmp_plans.txt" 2>&1
run compare research_compound escalate escalate3 > "$OUT/cmp_compound_escalate3.txt" 2>&1
run compare research escalate escalate3 > "$OUT/cmp_research_escalate3.txt" 2>&1
run compare research_compound escalate escalate2b > "$OUT/cmp_compound_escalate2b.txt" 2>&1
echo "done: $OUT"
