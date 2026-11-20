#!/usr/bin/env bash
# Owner step (A-165, D-356): appends the entries TD-89 of specs/mia/amendments/A-165-deferred-entry-td-89.md to specs/mia/deferred.md (a protected file).
# usage: bash tools/apply_deferred_g_v2.sh [--do]   without --do it shows what would be appended and changes nothing; run twice with --do changes nothing the second time.
set -u
cd "$(dirname "$0")/.." || exit 1
draft=specs/mia/amendments/A-165-deferred-entry-td-89.md; target=specs/mia/deferred.md
block=$(awk 'f{print} /^---$/{f=1}' "$draft" | sed '1{/^$/d}')
have=$(grep -c "^## TD-89 " "$target")
echo "entries in the draft: $(printf '%s\n' "$block" | grep -c '^## TD-'), already in $target: $have"
if [ "$have" != 0 ]; then echo "nothing to do: TD-89 are in $target already"; exit 0; fi
printf '%s\n' "$block" | sed 's/^/+ /' | head -80
if [ "${1:-}" = "--do" ]; then printf '\n%s\n' "$block" >> "$target"; echo "appended to $target"; else echo "(look only; --do appends)"; fi
