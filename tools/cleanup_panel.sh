#!/usr/bin/env bash
# Cleanup after G-V3.PANEL (merged into master as 772abc2): removes the worktrees `goal-v3` and `panel-status` and the local branches `goal/v3` and `panel-status`.
#   cleanup_panel.sh          look only: checks every condition and prints what --do would do (nothing is changed)
#   cleanup_panel.sh --do     does it
# Safe by checks, each of which stops the script: a branch must have no commit that master lacks; a tracked file that a worktree changed must equal master's copy; untracked files
# are copied to ~/MIA-removed-worktrees/<date>/ before the worktree goes. Not touched: the shared git stash (two entries from other sessions), the remote branches (the command to delete
# them is printed, you type it yourself), every other worktree (goal-v3-chat, goal-v2-*, ...).
set -euo pipefail

REPO=/home/maldun/prog/Python/MIA
KEEP="$HOME/MIA-removed-worktrees/$(date +%F)"
WORKTREES=(goal-v3 panel-status)
BRANCHES=(goal/v3 panel-status)
do_it=0; [ "${1:-}" = "--do" ] && do_it=1
[ -z "${1:-}" ] || [ "${1:-}" = "--do" ] || { echo "usage: $0 [--do]"; exit 2; }
cd "$REPO"
[ "$(git rev-parse --abbrev-ref HEAD)" = master ] || { echo "STOP: the main checkout is not on master"; exit 1; }
[ "$do_it" = 1 ] && echo "mode: --do" || echo "mode: look only (nothing is changed; --do does it)"

echo; echo "== branches (must be fully merged into master)"
for b in "${BRANCHES[@]}"; do
    git rev-parse --verify -q "refs/heads/$b" >/dev/null || { echo "$b: already gone"; continue; }
    ahead=$(git rev-list --count "master..$b")
    [ "$ahead" = 0 ] || { echo "STOP: $b has $ahead commit(s) that master lacks"; exit 1; }
    echo "$b: $(git log --oneline -1 "$b") (0 commits ahead of master)"
done

echo; echo "== worktrees"
for w in "${WORKTREES[@]}"; do
    dir="$REPO/.claude/worktrees/$w"
    if [ ! -d "$dir" ]; then echo "$w: already gone"; continue; fi
    echo "-- $w"
    while IFS= read -r line; do
        [ -n "$line" ] || continue
        code="${line:0:2}"; file="${line:3}"
        case "$code" in
            "??") echo "   untracked: $file  (copied to $KEEP/$w/ before removal)"
                  [ "$do_it" = 1 ] && { mkdir -p "$KEEP/$w/$(dirname "$file")"; cp -a "$dir/$file" "$KEEP/$w/$file"; } ;;
            *)    if git -C "$dir" diff --quiet master -- "$file" 2>/dev/null && [ -z "$(git -C "$dir" diff master -- "$file")" ]; then
                      echo "   changed, equal to master: $file  (nothing to keep)"
                  else
                      echo "STOP: $file in $w differs from master: look at it with: git -C $dir diff -- $file"; exit 1
                  fi ;;
        esac
    done < <(git -C "$dir" status --short)
    [ "$do_it" = 1 ] && git worktree remove --force "$dir" && echo "   worktree removed"
done

echo; echo "== local branches"
for b in "${BRANCHES[@]}"; do
    git rev-parse --verify -q "refs/heads/$b" >/dev/null || continue
    if [ "$do_it" = 1 ]; then git branch -d "$b"; else echo "would run: git branch -d $b"; fi
done
[ "$do_it" = 1 ] && git worktree prune

echo; echo "== not touched"
echo "stash entries (shared by all worktrees): $(git stash list | wc -l)"
echo "remote branches (type yourself if you want them gone):"
for b in "${BRANCHES[@]}"; do git rev-parse --verify -q "refs/remotes/origin/$b" >/dev/null && echo "   git push origin --delete $b"; done || true
[ "$do_it" = 1 ] || { echo; echo "look only: nothing was changed."; }
