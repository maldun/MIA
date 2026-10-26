#!/usr/bin/env bash
# Run python tests inside the MIA image with this checkout mounted (the host python lacks flask and friends).
#   bash tools/run_in_image.sh tests/test_chat_backend.py tests/test_config.py
# Each test file is run in its own container; prints the last lines of each and exits 1 if one failed.
set -u
cd "$(dirname "$0")/.."
status=0
for test in "$@"; do
    echo "== $test"
    out=$(timeout 300 podman run --rm --user 0 -v "$PWD:/work:Z" -w /work "${MIA_IMAGE:-localhost/mia:latest}" python "$test" 2>&1); code=$?
    echo "$out" | tail -n 3
    [ $code -eq 0 ] || status=1
done
exit $status
