#!/usr/bin/env bash
# Owner step: signs TD-86 to TD-90 in specs/mia/deferred.md (a protected file):
# removes " (DRAFT)" from their titles and sets "Sign-off: pending" to "Sign-off: <who>, <date>".
# usage: bash tools/sign_deferred_g_v2.sh [--do]   without --do it shows the diff and changes nothing; a second --do changes nothing.
set -u
cd "$(dirname "$0")/.." || exit 1
f=specs/mia/deferred.md; who="maldun"; day="2026-11-20"
tmp=$(mktemp)
awk -v who="$who" -v day="$day" '
/^## TD-/ { inb = ($2 ~ /^TD-(86|87|88|89|90)$/) }
inb && /^## / { sub(/ \(DRAFT\)$/, "") }
inb && /^- Sign-off: pending$/ { print "- Sign-off: " who ", " day; next }
{ print }' "$f" > "$tmp"
if cmp -s "$f" "$tmp"; then echo "nothing to do: TD-86 to TD-90 are signed already"; rm -f "$tmp"; exit 0; fi
echo "compared: $f  ->  edited copy"; diff -u "$f" "$tmp"
if [ "${1:-}" = "--do" ]; then cp "$tmp" "$f"; echo "written $f"; else echo "(look only; --do writes)"; fi
rm -f "$tmp"
