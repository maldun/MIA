#!/usr/bin/env bash
# Bring the approved plan package into master and tag the baseline (the human merge of the plan gate). Run it yourself in the MAIN checkout:
#   bash tools/merge_plan_baseline.sh            (a dry run: it only checks and says what it would do)
#   bash tools/merge_plan_baseline.sh --do       (merge, commit the installed protected tests, tag)
# Idempotent: it stops with a message where something is not as expected and changes nothing before all checks passed.
# What it does with --do:
#   1. merges the branch worktree-sysml-fresh-start into the current branch (must be master) with a merge commit;
#   2. commits the installed protected tests (tests/helpers, tests/acceptance/contract, tests/integration) if they are still untracked or changed;
#   3. tags that commit  decomp-baseline  (the approved root record, mocks, contract suites and red integration tests).
set -eu
cd "$(dirname "$0")/.."
BRANCH=worktree-sysml-fresh-start
TAG=decomp-baseline
do_it=0
[ "${1:-}" = "--do" ] && do_it=1

current=$(git branch --show-current)
[ "$current" = "master" ] || { echo "NOT READY: the current branch is '$current', not master"; exit 1; }
git rev-parse --verify -q "$BRANCH" >/dev/null || { echo "NOT READY: branch $BRANCH not found"; exit 1; }
if git rev-parse --verify -q "$TAG" >/dev/null; then echo "NOT READY: the tag $TAG exists already"; exit 1; fi

# only the installed protected tests may be untracked or modified; anything else would be swept into the merge
other=$(git status --porcelain | grep -v -E '^\?\? tests/(helpers|acceptance/contract|integration)/|^ ?M tests/(helpers|acceptance/contract|integration)/' || true)
if [ -n "$other" ]; then echo "NOT READY: other changes in the working tree:"; echo "$other"; exit 1; fi

# the installed tests must equal the drafts of the plan branch
for kind in contract integration; do
    src=specs/mia/$kind-drafts/tests
    git cat-file -e "$BRANCH:$src" 2>/dev/null || { echo "NOT READY: $src is not in $BRANCH"; exit 1; }
done
bad=0
for kind in contract integration; do
    while IFS= read -r rel; do
        file=${rel#"specs/mia/$kind-drafts/"}
        case "$file" in *__pycache__*) continue;; esac
        if [ ! -e "$file" ]; then echo "MISSING   $file (run tools/install_${kind}_drafts.sh)"; bad=1
        elif ! git show "$BRANCH:$rel" | cmp -s - "$file"; then echo "DIFFERS   $file (installed copy is not the draft of the branch)"; bad=1; fi
    done < <(git ls-tree -r --name-only "$BRANCH" "specs/mia/$kind-drafts/tests" | grep -E '\.(py|mjs)$')
done
[ "$bad" = 0 ] || { echo "NOT READY: fix the lines above (amendments to protected files are copied by hand)"; exit 1; }

echo "READY: $BRANCH ($(git rev-list --count master.."$BRANCH") commits) into master; $(git status --porcelain | wc -l) installed test files to commit; tag $TAG"
[ "$do_it" = 1 ] || { echo "dry run: nothing changed. Run again with --do."; exit 0; }

git merge --no-ff "$BRANCH" -m "plan: approved plan package of MIA (root record, 31 node specs, interface contracts, mocks, contract suites, integration drafts, plausibility record)"
git add tests/helpers tests/acceptance/contract tests/integration
git commit -m "tests: protected tests of the plan gate (contract suites, mocks, integration steps, helpers)" || echo "(no test changes to commit)"
git tag -a "$TAG" -m "Plan gate approved 2026-10-26: approved requirements, interface mocks, contract suites and red integration tests"
echo "done: master is at $(git rev-parse --short HEAD), tag $TAG"
