#!/usr/bin/env bash
# Repair of the commit "plan: A-22, A-24 installed" (fe2738b): it was made with `git add -A` and so swept 455 files of the working directory into master (videos, voice models, memories.json,
# long_time_history.json, templates/node_modules, links of .claude/worktrees ...). The plan of this script: undo only that commit (the files stay on disk, untracked again), commit again
# only the 11 files that belong to A-22 and A-24 (contracts/, specs/, tests/), and move the branch t11-extensions onto the new master.
# Run it in the MAIN checkout:
#   bash tools/undo_swept_commit.sh           show what it would do (changes nothing)
#   bash tools/undo_swept_commit.sh --do      do it
# Refuses to run when the commit is already pushed. Idempotent: when master no longer has the swept commit it says so.
set -eu
cd "$(dirname "$0")/.."
BAD=$(git log --format=%H --grep='^plan: A-22, A-24 installed$' -n 1 master)
if [ -z "$BAD" ]; then echo "no swept commit on master: nothing to do"; exit 0; fi
if git branch -r --contains "$BAD" 2>/dev/null | grep -q .; then echo "the commit $BAD is already on a remote branch: do not rewrite it; ask first"; exit 1; fi
[ "$(git rev-parse HEAD)" = "$BAD" ] || { echo "master is not at $BAD (other commits on top); run by hand"; exit 1; }
KEEP=$(git show --name-only --format= "$BAD" | grep -E '^(contracts|specs|tests)/')
echo "swept commit: $BAD  ($(git show --stat --format= "$BAD" | tail -1 | sed 's/^ *//'))"
echo "files that stay in the commit:"; echo "$KEEP" | sed 's/^/   /'
echo "files that become untracked again (not deleted): $(git show --name-only --format= "$BAD" | grep -vcE '^(contracts|specs|tests)/')"
if [ "${1:-}" != "--do" ]; then echo; echo "look only; --do rewrites master (local, not pushed)"; exit 0; fi
git reset --soft HEAD~1
git reset -q
echo "$KEEP" | xargs git add --
git commit -q -m "plan: A-22, A-24 installed

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
NEW=$(git rev-parse HEAD)
echo "new master: $NEW"
if git rev-parse -q --verify t11-extensions >/dev/null; then
    git rebase --onto "$NEW" "$BAD" t11-extensions && git checkout -q master
    echo "t11-extensions moved onto the new master"
fi
git status --short | head -5
git show --stat --format=%s HEAD | tail -3
