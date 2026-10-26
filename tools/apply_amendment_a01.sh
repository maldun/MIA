#!/usr/bin/env bash
# Amendment A-01 (owner, 2026-10-26): in the root integration order the Web Frontend (N-1) comes before the Evaluation and operation (N-4), so users can
# click through the chat on the mocks early. The protected step tests of N-0 are named by their number, so five installed files change:
#   tests/integration/N-0/scenario.py and step_02 to step_05/test_step.py.
# Run it yourself in the MAIN checkout (the coding agent may not write there), after the branch with the amendment is merged:
#   bash tools/apply_amendment_a01.sh          (shows what differs)
#   bash tools/apply_amendment_a01.sh --do     (copies the drafts over the installed files; commit them afterwards as "plan: A-01 ...")
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
SRC=specs/mia/integration-drafts
do_it=0
[ "${1:-}" = "--do" ] && do_it=1
changed=0
for rel in tests/integration/N-0/scenario.py tests/integration/N-0/step_02/test_step.py tests/integration/N-0/step_03/test_step.py \
           tests/integration/N-0/step_04/test_step.py tests/integration/N-0/step_05/test_step.py; do
    if [ ! -e "$rel" ]; then echo "MISSING   $rel (install the integration drafts first)"; exit 1; fi
    if cmp -s "$SRC/$rel" "$rel"; then echo "unchanged $rel"; continue; fi
    changed=$((changed + 1))
    if [ "$do_it" = 1 ]; then cp "$SRC/$rel" "$rel" && echo "updated   $rel"; else echo "DIFFERS   $rel"; fi
done
[ "$do_it" = 1 ] || { [ "$changed" = 0 ] || echo "$changed file(s) differ: run again with --do"; }
python3 -I tools/run_integration_steps.py . | tail -3
