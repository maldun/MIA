#!/usr/bin/env bash
# The 3D character from its source in one command: mia.blend -> VRM -> Godot import -> web export (ui/godot/build/web, which MIA serves).
# usage: ui/tools/setup_character.sh [path/to/mia.blend]
#   without an argument: $MIA_BLEND, else ui/character/mia.blend
# Both results are derived files (git-ignored) and can be made again at any time: the VRM comes out byte for byte the same from the same .blend (13 s),
# the web export is deterministic (8 s). Needs the flatpaks of Blender and Godot, the VRM add-on and the Godot export templates (one time, see ui/README.md).
set -euo pipefail
UI="$(cd "$(dirname "$0")/.." && pwd)"
BLEND="${1:-${MIA_BLEND:-$UI/character/mia.blend}}"
if [ ! -f "$BLEND" ]; then
  echo "The Blender file is missing: $BLEND"
  echo "Give its path as an argument, set MIA_BLEND, or put it at ui/character/mia.blend (git-ignored, see ui/character/README.md)."
  exit 1
fi
"$UI/tools/export_character.sh" "$BLEND"
"$UI/tools/build_web.sh"
echo "done: the character is in $UI/godot/build/web (MIA serves it under /character/)"
