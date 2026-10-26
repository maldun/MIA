#!/usr/bin/env bash
# Start what a person can test now. It grows with the nodes: a stage is one file in tools/testing_stages.d/ (NN-name.sh with the commands
# describe, available, auto, start, stop, status); a new node that users can try adds one file and nothing else.
#   bash tools/start_testing.sh                 list the stages and say which ones are available
#   bash tools/start_testing.sh start           start every available stage that is marked `auto` (the light ones)
#   bash tools/start_testing.sh start NAME...   start the named stages (e.g. full-app)
#   bash tools/start_testing.sh stop [NAME...]  stop the named stages (without names: the auto ones; containers only when named)
#   bash tools/start_testing.sh status
# Environment: MIA_PYTHON = python of the MIA virtualenv (needed for the stub stage if the active python lacks flask); MIA_TESTING_DIR = state folder.
set -u
DIR="$(cd "$(dirname "$0")/testing_stages.d" && pwd)"
cmd="${1:-list}"; shift || true

stages() { for f in "$DIR"/[0-9]*.sh; do basename "$f" .sh | sed 's/^[0-9]*-//'; done; }
file_of() { ls "$DIR"/[0-9]*-"$1".sh 2>/dev/null | head -1; }
run() { bash "$(file_of "$1")" "$2"; }

list() {
    printf '%-14s %-10s %s\n' STAGE STATE DESCRIPTION
    for s in $(stages); do
        if reason=$(run "$s" available 2>&1); then state=available; else state="not ready"; fi
        printf '%-14s %-10s %s\n' "$s" "$state" "$(run "$s" describe)"
        [ "$state" = available ] || printf '%-14s %-10s   -> %s\n' "" "" "$reason"
    done
}

case "$cmd" in
    list) list ;;
    status) for s in $(stages); do printf '%-14s ' "$s"; run "$s" status; done ;;
    start)
        names=("$@")
        if [ ${#names[@]} -eq 0 ]; then
            for s in $(stages); do run "$s" auto && names+=("$s"); done
        fi
        [ ${#names[@]} -gt 0 ] || { echo "no stage is marked auto; name one:"; list; exit 1; }
        for s in "${names[@]}"; do
            [ -n "$(file_of "$s")" ] || { echo "unknown stage: $s"; exit 1; }
            echo "== $s"
            if reason=$(run "$s" available 2>&1); then run "$s" start; else echo "skipped: $reason"; fi
        done ;;
    stop)
        names=("$@")                                 # without names only the light auto stages stop; a stack you started yourself is stopped by naming it
        if [ ${#names[@]} -eq 0 ]; then for s in $(stages); do run "$s" auto && names+=("$s"); done; fi
        for s in "${names[@]}"; do echo "== $s"; run "$s" stop; done ;;
    *) sed -n '2,10p' "$0"; exit 2 ;;
esac
