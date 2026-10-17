#!/usr/bin/env bash
# Exports the Godot project to ui/godot/build/web (single-threaded web build).
# Needs the Godot export templates (Editor > Manage Export Templates, or see ui/README.md).
set -euo pipefail
UI="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$UI/godot/build/web"
flatpak run --filesystem="$UI" org.godotengine.Godot --headless --path "$UI/godot" --import >/dev/null 2>&1 || true
flatpak run --filesystem="$UI" org.godotengine.Godot --headless --path "$UI/godot" --export-release Web build/web/index.html 2>&1 | grep -vE "^\s*$" | tail -15
du -ch "$UI"/godot/build/web/* | tail -20
