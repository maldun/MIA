#!/usr/bin/env bash
# Downloads the two Kokoro voice files (README.md, "Kokoro TTS"; deploy/RUNBOOK.md, "Files a fresh checkout lacks") and checks them by SHA-256.
#   bash tools/fetch_kokoro.sh [FOLDER]        default voice/models/kokoro
# Safe to repeat: a file with the right hash stays. A wrong hash removes the download and stops (exit 1); nothing half-written is left behind.
# The hashes are those of the files in use on the owner's machine (2026-11-02), taken from the release model-files-v1.0.
# MIA_KOKORO_BASE_URL, KOKORO_SHA_ONNX and KOKORO_SHA_VOICES override the source and the hashes (the test uses a file:// folder).
set -eu
cd "$(dirname "$0")/.."
dir="${1:-voice/models/kokoro}"
base="${MIA_KOKORO_BASE_URL:-https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0}"
sha_onnx="${KOKORO_SHA_ONNX:-7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5}"
sha_voices="${KOKORO_SHA_VOICES:-bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d}"
command -v curl >/dev/null 2>&1 || { echo "FAIL: curl is not installed"; exit 1; }
mkdir -p "$dir"

fetch() {   # name, expected hash
    local name="$1" want="$2" target="$dir/$1"
    if [ -f "$target" ] && [ "$(sha256sum "$target" | cut -d' ' -f1)" = "$want" ]; then
        echo "ok:   $name in place"; return 0
    fi
    echo "get:  $name"
    curl -fL --retry 3 -o "$target.part" "$base/$name" || { rm -f "$target.part"; echo "FAIL: download of $name"; return 1; }
    if [ "$(sha256sum "$target.part" | cut -d' ' -f1)" != "$want" ]; then
        rm -f "$target.part"; echo "FAIL: hash of $name differs from the pin"; return 1
    fi
    mv "$target.part" "$target"
    echo "ok:   $name downloaded and checked"
}

fetch kokoro-v1.0.onnx "$sha_onnx"
fetch voices-v1.0.bin "$sha_voices"
