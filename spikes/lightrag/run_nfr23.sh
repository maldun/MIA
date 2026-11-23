#!/usr/bin/env bash
# NFR-23 samples (specs/mia/goals/G-V4.BUILDER/nfr23-sample-plan.md): one run per document, strictly one after the other.
# B: items and relations, option1.py on the full model; A: definitions and facts, option_df.py on the light model.
# usage: run_nfr23.sh OUTDIR      (needs a running Ollama on 127.0.0.1:11434; uses the GPU for about one to two hours)
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:?usage: run_nfr23.sh OUTDIR}"
mkdir -p "$OUT/b-full-items" "$OUT/a-light-df"
MIA_SPIKE_MODEL=gemma4:26b python3 -I "$HERE/option1.py" "$OUT/b-full-items" "$HERE"/docs/*.txt "$HERE"/docs-n6/*.txt > "$OUT/b.log" 2>&1
MIA_SPIKE_MODEL=gemma4:12b-it-qat python3 -I "$HERE/option_df.py" "$OUT/a-light-df" "$HERE"/docs/*.txt "$HERE"/docs-n6/*.txt > "$OUT/a.log" 2>&1
echo finished > "$OUT/DONE"
