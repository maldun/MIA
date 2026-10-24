#!/usr/bin/env bash
# T-05 of specs/number-gate/plan.md: smoke run and spike on the real model, dev split only (about 5 minutes).
#   1. starts Ollama (podman) if needed and checks that the model digest is the pin MP-light
#   2. 10 dev cases (pairs kept together) of each suite through verify.single@1 and verify.cops@1, seed 7, temperature 0
#   3. determinism spike: the same 6 dev cases twice with the single style, then a comparison of the two runs
# Run from anywhere:  bash tools/run_t05_smoke.sh      (log: data/eval/t05.log; saved runs: data/eval/)
# Safe to run again; every run is saved under its own variant name and time. Holdout suites are never touched.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PY:-/home/maldun/prog/Python/venvs/mia312/bin/python}
export MIA_SUITES=${MIA_SUITES:-/home/maldun/prog/Python/MIA/eval/suites}
MODEL=gemma4:12b-it-qat
PIN_DIGEST=38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3
mkdir -p data/eval
LOG=data/eval/t05.log
exec > >(tee -a "$LOG") 2>&1
echo "=== T-05 $(date -Is) ==="

podman start ollama >/dev/null 2>&1 || true
for _ in $(seq 1 30); do curl -sf localhost:11434/api/tags >/dev/null && break; sleep 2; done
if ! curl -sf localhost:11434/api/tags | grep -q "$PIN_DIGEST"; then
  echo "STOP: $MODEL on this server does not have the digest of the pin MP-light ($PIN_DIGEST)"; exit 1
fi
echo "digest of $MODEL is the pin"

run() { "$PY" tools/eval.py run "$@" --model "$MODEL" --pin MP-light --repeats 1 --quiet; }

for suite in verdicts_vitaminc verdicts_wikidata; do
  for style in single cops; do
    echo; echo "--- $suite, $style, 10 cases"
    start=$(date +%s)
    run "$suite" --variant "t05-$style" --pipeline "verify.$style@1" --sample 10
    echo "seconds: $(( $(date +%s) - start ))"
  done
done

echo; echo "--- determinism: the same 6 cases twice (verdicts_vitaminc, single)"
for k in a b; do
  run verdicts_vitaminc --variant "t05-det-$k" --pipeline "verify.single@1" --sample 6
done
"$PY" tools/eval.py compare verdicts_vitaminc t05-det-a t05-det-b

echo; echo "=== done: send me the end of $LOG or tell me to read it ==="
