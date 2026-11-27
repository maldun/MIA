#!/usr/bin/env bash
# Amendment A-185 (G-V4.GRAPHAPI.RULES, 2026-11-22, D-461; Verify finding V-2): one sentence of IF-301 v4. The save asks the rule report after the check
# of the kind and BEFORE the record checks (the text said "after"; the code, CORE and the protected checks TC-WFM-184 and TC-GTB-046 rely on "before":
# a refused save names every broken rule even when a record would also be refused, REQ-WFM-163). No code or test changes. Draft in specs/mia/amendments/A-185/.
# INSTALL IT ON THE LINE OF WORK goal/v4.graphapi.rules.
#   bash tools/apply_amendment_a185.sh           show the diff (changes nothing)
#   bash tools/apply_amendment_a185.sh --do      install; commit afterwards as "plan: A-185 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/amendments/A-185/IF-301-graph-tables.md contracts/IF-301-graph-tables.md
finish
