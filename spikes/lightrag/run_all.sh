#!/usr/bin/env bash
# Spike C: 10 documents x 3 repeats on the 12B at num_ctx 8192. Needs the venv with lightrag-hku and a running Ollama.
set -u
VENV=/home/maldun/.claude/jobs/e89b06cf/tmp/spike-venv
OUT=/home/maldun/.claude/jobs/e89b06cf/tmp/run1
DOCS=/home/maldun/.claude/jobs/e89b06cf/tmp/docs
HERE=/home/maldun/prog/Python/MIA/.claude/worktrees/explore-ctx-graph/spikes/lightrag
mkdir -p "$OUT"
for rep in 1 2 3; do
  "$VENV/bin/python" "$HERE/run_spike.py" "$OUT" "$rep" "$DOCS"/*.txt > "$OUT/rep$rep.log" 2>&1
done
echo finished > "$OUT/DONE"
