#!/usr/bin/env bash
# T-06 of specs/number-gate/plan.md: dev-sample baseline of the current release (about 15 minutes, one model, dev split only).
#   100 dev cases = 50 per suite (VitaminC, Wikidata), seed 7, groups of one claim kept together, 1 repeat, pin MP-light,
#   through verify.single@1 and verify.cops@1 (immutable versions: they are the baselines).
# Run from the repository root of the checkout that has tools/eval.py:  bash tools/run_t06_baseline.sh
# Saved runs: data/eval/ (variants t06-single and t06-cops). Baseline copies: eval/baselines/<suite>__<style>__devsample.jsonl (never overwritten).
# Holdout suites are never touched. Log: data/eval/t06.log
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PY:-/home/maldun/prog/Python/venvs/mia312/bin/python}
export MIA_SUITES=${MIA_SUITES:-/home/maldun/prog/Python/MIA/eval/suites}
MODEL=gemma4:12b-it-qat
PIN_DIGEST=38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3
mkdir -p data/eval eval/baselines
exec > >(tee -a data/eval/t06.log) 2>&1
echo "=== T-06 $(date -Is) ==="

podman start ollama >/dev/null 2>&1 || true
for _ in $(seq 1 30); do curl -sf localhost:11434/api/tags >/dev/null && break; sleep 2; done
curl -sf localhost:11434/api/tags | grep -q "$PIN_DIGEST" || { echo "STOP: the model digest is not the pin MP-light"; exit 1; }
echo "digest of $MODEL is the pin"

for style in single cops; do
  for suite in verdicts_vitaminc verdicts_wikidata; do
    echo; echo "--- $suite, $style, 50 cases"
    start=$(date +%s)
    "$PY" tools/eval.py run "$suite" --variant "t06-$style" --pipeline "verify.$style@1" --model "$MODEL" --pin MP-light \
          --repeats 1 --sample 50 --sample-seed 7 --quiet
    echo "seconds: $(( $(date +%s) - start ))"
  done
done

echo; echo "--- baseline copies"
for suite in verdicts_vitaminc verdicts_wikidata; do
  for style in single cops; do
    newest=$(ls -t data/eval/"$suite"__t06-"$style"__*.jsonl | head -1)
    target=eval/baselines/"$suite"__"$style"__devsample.jsonl
    if [ -e "$target" ]; then echo "exists, not overwritten: $target"; else cp "$newest" "$target"; echo "$newest -> $target"; fi
  done
done
echo; echo "=== done: tell me to read data/eval/t06.log ==="
