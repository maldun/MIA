#!/usr/bin/env bash
# Run python tests inside the MIA image with this checkout mounted (the host python lacks flask and friends).
#   bash tools/run_in_image.sh tests/test_chat_backend.py tests/test_config.py
# Each test file is run in its own container (with --init: a killed child must not stay a zombie, test_shutdown; the mount is labelled
# shared, :z, so that runs in parallel and other worktrees do not lock each other out, F17 of the N-2.4.1 verification); prints the last lines of each and exits 1 if one failed.
set -u
cd "$(dirname "$0")/.."
status=0
for test in "$@"; do
    echo "== $test"
    out=$(timeout 300 podman run --rm --init --user 0 -v "$PWD:/work:z" -w /work "${MIA_IMAGE:-localhost/mia:latest}" python "$test" 2>&1); code=$?
    echo "$out" | tail -n 3
    [ $code -eq 0 ] || status=1
done
exit $status
