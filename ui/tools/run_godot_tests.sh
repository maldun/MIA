#!/usr/bin/env bash
# Runs the headless tests of the character (ui/godot/tools/test_*.gd) and prints one RESULT line per test.
#   bash ui/tools/run_godot_tests.sh              all tests
#   bash ui/tools/run_godot_tests.sh bridge       only test_bridge.gd (the name without test_ and .gd)
# Godot: $GODOT (a binary), else the Flatpak org.godotengine.Godot. The model ui/godot/assets/mia.vrm must exist (git-ignored; made by
# ui/tools/export_character.sh) and Godot must have imported the project once:  godot --headless --path ui/godot --import
set -u
cd "$(dirname "$0")/../.."
ROOT="$PWD"
run_godot() {
    if [ -n "${GODOT:-}" ]; then "$GODOT" "$@"; else flatpak run --filesystem="$ROOT" org.godotengine.Godot "$@"; fi
}
[ -f ui/godot/assets/mia.vrm ] || { echo "ui/godot/assets/mia.vrm is missing (see ui/README.md)"; exit 1; }
status=0
for test in ui/godot/tools/test_${1:-*}.gd; do
    name=$(basename "$test" .gd)
    case "$name" in *_live) if [ -z "${MIA_URL:-}" ]; then printf '%-26s %s\n' "$name" "skipped (needs a running MIA: set MIA_URL and MIA_TOKEN_FILE)"; continue; fi ;; esac
    out=$(timeout "${GODOT_TEST_TIMEOUT:-300}" bash -c "$(declare -f run_godot); ROOT='$ROOT'; GODOT='${GODOT:-}'; run_godot --headless --path ui/godot -s res://tools/$name.gd" 2>&1)
    result=$(echo "$out" | grep -E "^RESULT" | tail -1)
    [ -n "$result" ] || result="RESULT none (timeout or script error: $(echo "$out" | grep -E 'ERROR' | head -1 | cut -c1-100))"
    printf '%-26s %s\n' "$name" "$result"
    echo "$result" | grep -q "ALL PASSED" || status=1
done
exit $status
