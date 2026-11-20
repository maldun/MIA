#!/usr/bin/env bash
# Owner step: lets TD-86 lead with REQ-WFM-060 and TD-89 with REQ-WFM-059 in specs/mia/deferred.md (protected),
# so that each requirement carries one TD (trace_check reads the first requirement id of a TD). TD-90 keeps REQ-WFM-058.
# usage: bash tools/reorder_deferred_g_v2.sh [--do]   without --do it shows the diff and changes nothing; a second --do changes nothing.
set -u
cd "$(dirname "$0")/.." || exit 1
f=specs/mia/deferred.md; tmp=$(mktemp)
awk '
/^## TD-/ { td=$2 }
td=="TD-86" && /^- Requirement: REQ-WFM-058, REQ-WFM-060 / { sub(/REQ-WFM-058, REQ-WFM-060 /, "REQ-WFM-060, REQ-WFM-058 ") }
td=="TD-89" && /^- Requirement: REQ-WFM-058, REQ-WFM-110 / { sub(/REQ-WFM-058, REQ-WFM-110 /, "REQ-WFM-059, REQ-WFM-058, REQ-WFM-110 ") }
{ print }' "$f" > "$tmp"
if cmp -s "$f" "$tmp"; then echo "nothing to do: already reordered"; rm -f "$tmp"; exit 0; fi
echo "compared: $f -> edited copy"; diff -u "$f" "$tmp" | cut -c1-120
if [ "${1:-}" = "--do" ]; then cp "$tmp" "$f"; echo "written $f"; else echo "(look only; --do writes)"; fi
rm -f "$tmp"
