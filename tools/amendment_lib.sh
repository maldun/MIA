#!/usr/bin/env bash
# Shared part of the amendment scripts (tools/apply_amendment_aNN.sh): compare a draft with the installed protected file, show the difference at a glance,
# copy only with --do. Source it, then call `copy DRAFT INSTALLED` for every file and `finish` at the end:
#
#   . "$(dirname "$0")/amendment_lib.sh"; amendment_args "$@"
#   copy specs/mia/amendments/A-06/X.md contracts/X.md
#   finish                      # summary table; returns 0, and exits early with a hint when files differ and --do was not given
#
# Options of every amendment script:  (none) show the compared files and the diff, change nothing   --do  copy the drafts over the installed files
#                                      --report  show the change readably (changed words marked inside the line, requirements by requirement; tools/amendment_report.py) instead of the unified diff
#                                      --full  do not cut the diff of a file after 60 lines (MAX_DIFF_LINES=n changes the cut)
# Each file is reported as: unchanged | DIFFERS (+added -removed lines, then the diff) | updated (after --do) | MISSING (the installed file does not exist).
# Lines with + are in the draft and not installed yet, lines with - are installed and go away.
do_it=0; full=0; report=0; changed=0; compared=()

amendment_args() {
    for arg in "$@"; do
        case "$arg" in
            --do) do_it=1 ;;
            --full) full=1 ;;
            --report) report=1 ;;
            *) echo "unknown option: $arg (use --do, --full or --report)"; exit 2 ;;
        esac
    done
    [ "$do_it" = 1 ] && echo "mode: --do (the installed files are overwritten by the drafts)" || echo "mode: look only (nothing is changed; --do installs)"
    echo
}

copy() {   # draft installed
    local draft="$1" installed="$2" limit="${MAX_DIFF_LINES:-60}" added removed
    if [ ! -e "$draft" ]; then echo "MISSING draft: $draft"; exit 1; fi
    if [ ! -e "$installed" ]; then
        echo "── $installed   <-   $draft"
        changed=$((changed + 1))
        if [ "$do_it" = 1 ]; then cp "$draft" "$installed"; echo "   -> created (the installed file did not exist)"; compared+=("created   $installed")
        else echo "   MISSING: the installed file does not exist; --do creates it from the draft"; compared+=("MISSING   $installed (--do creates it)"); fi
        echo
        return 0
    fi
    echo "── $installed   <-   $draft"
    if cmp -s "$draft" "$installed"; then echo "   unchanged (identical)"; echo; compared+=("unchanged $installed"); return; fi
    changed=$((changed + 1))
    added=$(diff "$installed" "$draft" | grep -c '^>') || true
    removed=$(diff "$installed" "$draft" | grep -c '^<') || true
    echo "   DIFFERS: +$added -$removed lines"
    if [ "$full" = 1 ]; then limit=100000; fi
    if [ "$report" = 1 ]; then
        shown=$(python3 "$(dirname "${BASH_SOURCE[0]}")/amendment_report.py" "$installed" "$draft" --color "$([ -t 1 ] && echo always || echo never)")
        printf '%s\n' "$shown" | sed 's/^/   /' | head -n "$limit" || true
        if [ "$(printf '%s\n' "$shown" | wc -l)" -gt "$limit" ]; then echo "   ... (cut after $limit lines; --full shows all)"; fi
    else
        diff -u --label "installed: $installed" --label "draft: $draft" "$installed" "$draft" | sed 's/^/   /' | head -n "$limit" || true
        if [ "$(diff -u "$installed" "$draft" | wc -l)" -gt "$limit" ]; then echo "   ... (cut after $limit lines; --full shows all)"; fi
    fi
    if [ "$do_it" = 1 ]; then cp "$draft" "$installed" && echo "   -> updated"; compared+=("updated   $installed (+$added -$removed)"); else compared+=("DIFFERS   $installed (+$added -$removed)"); fi
    echo
}

finish() {
    echo "══ compared ${#compared[@]} file(s)"
    printf '   %s\n' "${compared[@]}"
    if [ "$do_it" = 0 ] && [ "$changed" -gt 0 ]; then echo "$changed file(s) differ: run again with --do to install them"; exit 0; fi
    [ "$changed" = 0 ] && echo "nothing to do: everything is installed already"
    return 0
}
