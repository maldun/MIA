#!/usr/bin/env bash
# Spike C: 10 documents x 3 repeats on the 12B at num_ctx 8192. Needs a running Ollama.
# usage: run_all.sh OUTDIR [VENV]   (VENV = Python 3.12 venv with lightrag-hku==1.5.7 and ollama; default OUTDIR/venv)
# Documents are the ones kept in the repo (docs/). Option 1 (no venv needed): python3 -I option1.py OUTDIR/option1 docs/*.txt
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:?usage: run_all.sh OUTDIR [VENV]}"
VENV="${2:-$OUT/venv}"
mkdir -p "$OUT"
[ -x "$VENV/bin/python" ] || { python3.12 -m venv "$VENV" && "$VENV/bin/pip" install -q lightrag-hku==1.5.7 ollama; }
for rep in 1 2 3; do
  "$VENV/bin/python" "$HERE/run_spike.py" "$OUT" "$rep" "$HERE"/docs/*.txt > "$OUT/rep$rep.log" 2>&1
done
echo finished > "$OUT/DONE"
