#!/usr/bin/env bash
# Put the generated suites (VitaminC and Wikidata) where the harness reads them, and keep the ambiguous cases out of decisions.
#
# Usage, from anywhere:  bash tools/install_external_suites.sh [--generate]
#   --generate   run tools/make_external_suite.py first (about 2 minutes, needs the internet; 150 VitaminC groups, 150 Wikidata pairs)
#
# Steps (safe to repeat):
#   1. optionally generate into data/eval-external (the source of truth, ignored by git)
#   2. remove a stray copy in data/eval (that folder is for saved runs only), but only if it is identical to the source
#   3. tag the cases listed in data/eval-external/audit/ambiguous.txt as ambiguous and retired in the source,
#      and tag every case with the requirement ids its criterion selects (specs/number-gate/case-requirements.json)
#   4. copy the four suite folders to eval/suites/ (the harness reads eval/suites), so the copies carry the tags
#   5. make sure .gitignore keeps the VitaminC cases out of git (CC BY-SA 3.0)
#   6. print the case counts and run `tools/eval.py list`
# Set MIA_ROOT to work on another checkout.
set -euo pipefail

ROOT="${MIA_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$ROOT"
SRC="data/eval-external"
DST="eval/suites"
NAMES=(verdicts_vitaminc verdicts_vitaminc.holdout verdicts_wikidata verdicts_wikidata.holdout)

say() { printf '== %s\n' "$*"; }

if [[ "${1:-}" == "--generate" ]]; then
  say "1. generating the suites (progress lines follow)"
  python3 -I tools/make_external_suite.py --out "$SRC" --n-vitaminc 150 --n-wikidata 150 > /dev/null
fi

say "check: the generated source exists"
for n in "${NAMES[@]}"; do
  [[ -f "$SRC/suites/$n/cases.jsonl" ]] || { echo "missing $SRC/suites/$n/cases.jsonl: run with --generate first"; exit 1; }
done
[[ -d "$DST" ]] || { echo "missing $DST: is $ROOT the MIA checkout?"; exit 1; }

say "2. stray copy in data/eval (compared before the tagging, so an untouched copy counts as identical)"
if [[ -d data/eval/suites ]]; then
  same=1
  for n in "${NAMES[@]}"; do
    cmp -s "$SRC/suites/$n/cases.jsonl" "data/eval/suites/$n/cases.jsonl" || same=0
  done
  if [[ $same == 1 ]]; then
    rm -rf data/eval/suites data/eval/audit data/eval/manifest.json
    echo "removed the identical copy (your saved runs in data/eval stay)"
  else
    echo "data/eval/suites differs from the source: left alone, look at it by hand"
  fi
else
  echo "none"
fi

say "3. tag the ambiguous cases in the source (before copying, so the copies are tagged too)"
AMB="$SRC/audit/ambiguous.txt"
if [[ -f "$AMB" ]]; then
  python3 -I tools/tag_ambiguous.py "$AMB" "$SRC"/suites/*
else
  echo "no $AMB yet: run tools/label_agreement.py after labelling the audit sheet, then call this script again"
fi

say "3b. tag the cases with the requirement ids of the criteria (specs/number-gate/case-requirements.json)"
MAP="specs/number-gate/case-requirements.json"
if [[ -f "$MAP" ]]; then
  python3 -I tools/tag_requirements.py "$MAP" "$SRC/suites"
else
  echo "no $MAP: the cases keep the tags of the generator"
fi

say "4. copy to $DST"
for n in "${NAMES[@]}"; do
  rm -rf "$DST/$n"
  cp -r "$SRC/suites/$n" "$DST/$n"
done

say "5. .gitignore"
if grep -q '^eval/suites/verdicts_vitaminc' .gitignore 2>/dev/null; then
  echo "VitaminC cases are ignored by git"
else
  printf '\n# VitaminC cases (CC BY-SA 3.0, may not be compatible with GPL-3.0): regenerate with tools/make_external_suite.py\neval/suites/verdicts_vitaminc*/\n' >> .gitignore
  echo "added the line to .gitignore"
fi

say "6. result"
for n in "${NAMES[@]}"; do
  printf '   %-28s %4d cases, %2d retired\n' "$n" "$(wc -l < "$DST/$n/cases.jsonl")" "$(grep -c '"retired"' "$DST/$n/cases.jsonl" || true)"
done
python3 tools/eval.py list | grep -E "verdicts_(vitaminc|wikidata)" || echo "the harness does not list the new suites: look at the output of: python3 tools/eval.py list"
