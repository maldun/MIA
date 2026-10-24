#!/usr/bin/env bash
# T-09 of specs/number-gate/plan.md, starting point: the gate verify.number_gate@1 on the same dev samples as the T-06 baselines (about 8 minutes, dev split only).
#   50 VitaminC cases and 50 Wikidata cases (seed 7, the sample of T-06) and the 12 dev cases of the injection suite, 1 repeat, pin MP-light.
# Run from the repository root:  bash tools/run_t09_start.sh     (log: data/eval/t09.log; saved runs: data/eval/, variant t09-gate; optional first argument: the variant name)
# Holdout suites are never touched.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PY:-/home/maldun/prog/Python/venvs/mia312/bin/python}
export MIA_SUITES=${MIA_SUITES:-/home/maldun/prog/Python/MIA/eval/suites}
VARIANT=${1:-t09-gate}
PIPELINE=${PIPELINE:-verify.number_gate@1}
MODEL=gemma4:12b-it-qat
PIN_DIGEST=38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3
mkdir -p data/eval
exec > >(tee -a data/eval/t09.log) 2>&1
echo "=== T-09 start $(date -Is) variant $VARIANT pipeline $PIPELINE ==="

curl -sf localhost:11434/api/tags | grep -q "$PIN_DIGEST" || { echo "STOP: the model digest is not the pin MP-light (or Ollama is not running)"; exit 1; }

run() { "$PY" tools/eval.py run "$@" --variant "$VARIANT" --pipeline "$PIPELINE" --model "$MODEL" --pin MP-light --repeats 1 --quiet; }

for suite in verdicts_vitaminc verdicts_wikidata; do
  echo; echo "--- $suite, 50 cases"
  start=$(date +%s)
  run "$suite" --sample 50 --sample-seed 7
  echo "seconds: $(( $(date +%s) - start ))"
done
echo; echo "--- verdicts_injection, all 12 dev cases"
run verdicts_injection
echo; echo "=== done ==="
