#!/usr/bin/env bash
# T-10 of specs/number-gate/plan.md: stability of single, cops and the gate over 3 repeats (about 55 minutes, dev split only).
#   The cases of the T-06 baseline (48 VitaminC and 50 Wikidata cases after the retirements), 3 repeats, pin MP-light (seed 7, temperature 0), no sample drawn again.
#   Order: the cheap runs first (single, then the gate, then cops), so that a partial result is already useful.
# Run from the repository root:  bash tools/run_t10_stability.sh     (log: data/eval/t10.log; saved runs: data/eval/, variants t10-single, t10-gate, t10-cops)
# Needs the MIA virtualenv (PY) and Ollama with the pinned model. Holdout suites are never touched.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=${PY:-/home/maldun/prog/Python/venvs/mia312/bin/python}
export MIA_SUITES=${MIA_SUITES:-/home/maldun/prog/Python/MIA/eval/suites}
BASELINES=${BASELINES:-/home/maldun/prog/Python/MIA/eval/baselines}
GATE=${GATE:-verify.number_gate@4}
MODEL=gemma4:12b-it-qat
PIN_DIGEST=38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3
mkdir -p data/eval
exec > >(tee -a data/eval/t10.log) 2>&1
echo "=== T-10 $(date -Is) gate $GATE ==="
curl -sf localhost:11434/api/tags | grep -q "$PIN_DIGEST" || { echo "STOP: the model digest is not the pin MP-light (or Ollama is not running)"; exit 1; }

baseline_ids() { "$PY" -I - "$1" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf8") if l.strip()]
print(",".join(sorted({r["case"] for r in rows if "case" in r})))
PY
}

for style in single gate cops; do
  case $style in single) pipeline=verify.single@1;; cops) pipeline=verify.cops@1;; gate) pipeline=$GATE;; esac
  for suite in verdicts_vitaminc verdicts_wikidata; do
    # resumable: a run is saved only when it is complete, so a saved file means "done"; stop the script at any time and start it again
    if ls data/eval/"$suite"__t10-"$style"__*.jsonl >/dev/null 2>&1; then
      echo; echo "--- $style, $suite: already done ($(ls data/eval/"$suite"__t10-"$style"__*.jsonl | head -1)), skipped"
      continue
    fi
    echo; echo "--- $style ($pipeline), $suite, 3 repeats"
    start=$(date +%s)
    "$PY" tools/eval.py run "$suite" --variant "t10-$style" --pipeline "$pipeline" --model "$MODEL" --pin MP-light --repeats 3 --quiet \
          --only "$(baseline_ids "$BASELINES/${suite}__single__devsample.jsonl")"
    echo "seconds: $(( $(date +%s) - start ))"
  done
  echo; echo "--- stability of $style"
  "$PY" -I tools/stability_report.py --latest "t10-$style"
done
echo; echo "=== done $(date -Is) ==="
