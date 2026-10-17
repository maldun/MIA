#!/usr/bin/env bash
# Blender (.blend) -> VRM 1.0 -> imported by Godot, then verifies all shape keys.
# usage: ui/tools/export_character.sh path/to/mia.blend
# one-time setup: install the VRM add-on into Blender (see ui/README.md)
set -euo pipefail
UI="$(cd "$(dirname "$0")/.." && pwd)"
BLEND="$(realpath "${1:?usage: export_character.sh path/to/mia.blend}")"
OUT="$UI/godot/assets/mia.vrm"
# the flatpak sandbox only sees directories it is given
FS="--filesystem=$(dirname "$BLEND") --filesystem=$UI"

flatpak run $FS org.blender.Blender -b "$BLEND" --python "$UI/tools/export_character.py" -- "$OUT" 2>&1 | grep -E "^EXPORT" || true
test -s "$OUT"
flatpak run $FS org.godotengine.Godot --headless --path "$UI/godot" --import >/dev/null 2>&1 || true
flatpak run $FS org.godotengine.Godot --headless --path "$UI/godot" --script res://tools/verify_shapekeys.gd 2>&1 | grep -E "MESH|UNIQUE|FAILED|NOT DRIV|ERROR"
