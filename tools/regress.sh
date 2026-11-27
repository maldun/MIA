#!/usr/bin/env bash
# The regression set of a task, strictly one after the other (implement-phase "Done when"): the unit suite, then every acceptance script on its
# own, and with --base the acceptance scripts again on a `git archive` export of an earlier commit, to tell new reds from old ones.
#   bash tools/regress.sh --out DIR [--python PY] [--base COMMIT]
# Writes DIR/unit.log, DIR/acceptance.txt (one line per script: path and its last output line), DIR/acceptance_base.txt; prints the unit
# summary, the scripts that are not OK, and with --base the lines that differ from the base. Exit 0 when the unit suite and every acceptance
# script are OK, 1 otherwise.
# Rules it keeps: one run per worktree at a time (a lock in the git folder: two runs share mia.log and the checkout); bytecode removed first
# (a stale .pyc once hid a restored file, TRANSFER T-06). Do not edit files of the worktree while it runs (test_checkout_untouched.py).
set -u
OUT="" PY=/home/maldun/prog/Python/venvs/mia312/bin/python BASE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --python) PY="$2"; shift 2 ;;
    --base) BASE="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ -n "$OUT" ] || { echo "usage: bash tools/regress.sh --out DIR [--python PY] [--base COMMIT]" >&2; exit 2; }
cd "$(dirname "$0")/.."
ROOT=$(pwd)
mkdir -p "$OUT"
exec 9>"$(git rev-parse --git-dir)/regress.lock"
flock -n 9 || { echo "another regression run holds this worktree" >&2; exit 2; }

acceptance() {   # $1 = folder of a checkout, $2 = result file; per script its unittest result line (OK, FAILED), else its last line
  (cd "$1" && for f in $(find tests/acceptance -name 'test_*.py' | sort); do
     out=$(timeout 1200 "$PY" "$f" 2>&1)
     line=$(printf '%s\n' "$out" | grep -E '^(OK|FAILED)' | tail -1)     # some scripts print a note after the result
     printf '%s %s\n' "$f" "${line:-$(printf '%s\n' "$out" | tail -1)}"
   done) > "$2"
}

find "$ROOT" -name __pycache__ -type d -not -path '*/.git/*' -prune -exec rm -rf {} +
status=0
"$PY" -m unittest discover -s tests > "$OUT/unit.log" 2>&1 || status=1
echo "== unit suite: $(grep -E '^(Ran|OK|FAILED)' "$OUT/unit.log" | tr '\n' ' ')"
grep -E '^(FAIL|ERROR):' "$OUT/unit.log"
acceptance "$ROOT" "$OUT/acceptance.txt"
echo "== acceptance scripts not OK:"
grep -v -E ' OK( \(.*\))?$' "$OUT/acceptance.txt" && status=1
if [ -n "$BASE" ]; then
  rm -rf "$OUT/base" && mkdir -p "$OUT/base"
  git archive "$BASE" | tar -x -C "$OUT/base"
  acceptance "$OUT/base" "$OUT/acceptance_base.txt"
  echo "== acceptance lines that differ from $BASE (< base, > now):"
  diff "$OUT/acceptance_base.txt" "$OUT/acceptance.txt"
fi
exit $status
