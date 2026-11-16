#!/usr/bin/env bash
# All holdout evaluations that can run today. Run by the OWNER only: an agent never runs or opens a holdout (CLAUDE.md, agent-app). A holdout is for the Verify of its goal and is
# spent when it has been seen: look first, then run what belongs to the goal you are verifying (--only).
#   holdout_all.sh                      look only: lists every holdout suite, what kind it is and whether it can run; changes nothing
#   holdout_all.sh --do                 asks you to type YES, then runs every runnable holdout suite once (3 repeats) on MP-light
#   holdout_all.sh --do --only NAME     the same for one suite (skill_turns.holdout, verdicts_wikidata.holdout, ...)
#   holdout_all.sh --do --yes           no question (for a script)
# What runs, decided by the target kind of the DEV suite of the same name (the holdout files are not read by this script):
#   digest    (skill_turns)           -> tools/holdout_skill_turns.sh --do (run, then the labelling form in ~/Downloads); the decision is `tools/holdout_skill_turns.sh decide RUN`
#   pipeline  (verdicts_*)            -> tools/eval.py --holdout run SUITE --pin MP-light --repeats $REPEATS --pipeline P for every P in $PIPELINES (default: verify.single@1 verify.cops@1;
#                                        these defaults are NOT from a specification: set PIPELINES and REPEATS in the environment to what the Verify of your goal says)
#   pending   (the seven rt_* suites) -> skipped: the dev suite has no target yet, so there is nothing to run
# A failing criterion is re-run once with fresh seeds, never more; seeds, repeats and thresholds are never changed to get a pass.
set -euo pipefail

WT="$(cd "$(dirname "$0")/.." && pwd)"
PY=${PY:-/home/maldun/prog/Python/venvs/mia312/bin/python}
PIPELINES=${PIPELINES:-"verify.single@1 verify.cops@1"}
REPEATS=${REPEATS:-3}
do_it=0; yes=0; only=""
while [ $# -gt 0 ]; do
    case "$1" in
        --do) do_it=1 ;;
        --yes) yes=1 ;;
        --only) only="${2:?--only needs a suite name}"; shift ;;
        *) echo "usage: $0 [--do] [--only SUITE] [--yes]"; exit 2 ;;
    esac
    shift
done
cd "$WT"

echo "== state"
branch=$(git rev-parse --abbrev-ref HEAD); echo "branch $branch, HEAD $(git rev-parse --short HEAD)"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then echo "STOP: tracked files changed (commit or discard first); the run header names the commit"; exit 1; fi

kind_of() {     # the target kind of the dev suite of the same name
    $PY - "$1" <<'EOF'
import json, sys
name = sys.argv[1].replace(".holdout", "")
try:
    print(json.load(open("eval/suites/%s/suite.json" % name)).get("target", {}).get("kind", "unknown"))
except Exception:
    print("unknown")
EOF
}

echo; echo "== holdout suites"
runnable=()
for dir in eval/suites/*.holdout; do
    suite=$(basename "$dir")
    [ -z "$only" ] || [ "$only" = "$suite" ] || continue
    kind=$(kind_of "$suite")
    case "$kind" in
        digest)   echo "$suite: kind digest -> tools/holdout_skill_turns.sh --do"; runnable+=("$suite:digest") ;;
        pipeline) echo "$suite: kind pipeline -> $REPEATS repeats, pipelines: $PIPELINES"; runnable+=("$suite:pipeline") ;;
        pending)  echo "$suite: SKIPPED, the dev suite has target kind 'pending' (nothing to run yet)" ;;
        *)        echo "$suite: SKIPPED, target kind '$kind' is not known to this script" ;;
    esac
done
[ -z "$only" ] || [ ${#runnable[@]} -gt 0 ] || { echo "nothing runnable for --only $only"; exit 1; }
[ "$do_it" = 1 ] || { echo; echo "look only: nothing was run. Add --do (and --only SUITE for one suite)."; exit 0; }
[ ${#runnable[@]} -gt 0 ] || { echo "nothing to run"; exit 0; }

echo; echo "== model server and pin"
if ! curl -sf localhost:11434/api/tags >/dev/null; then
    echo "Ollama is not answering: starting the container"; podman start ollama >/dev/null
    for _ in $(seq 30); do curl -sf localhost:11434/api/tags >/dev/null && break; sleep 1; done
fi
curl -sf localhost:11434/api/tags >/dev/null || { echo "STOP: no model server on localhost:11434"; exit 1; }
echo "model server answers (the digest of the pin is checked by tools/holdout_skill_turns.sh and written into the header of every run)"

if [ "$yes" = 0 ]; then
    echo; echo "These holdout suites are spent once they have been seen: ${runnable[*]}"
    read -r -p "Type YES to run them: " answer
    [ "$answer" = YES ] || { echo "not confirmed, nothing was run"; exit 1; }
fi

summary=()
for item in "${runnable[@]}"; do
    suite=${item%%:*}; kind=${item##*:}
    echo; echo "== $suite ($kind)"
    case "$kind" in
        digest)
            tools/holdout_skill_turns.sh --do
            summary+=("$suite: run file and form: see the end of the output above; then: tools/holdout_skill_turns.sh decide <run file>") ;;
        pipeline)
            for pipeline in $PIPELINES; do
                echo "-- $suite with $pipeline"
                out=$($PY tools/eval.py --holdout run "$suite" --pin MP-light --repeats "$REPEATS" --pipeline "$pipeline" 2>&1 | tee /dev/stderr)
                run=$(printf '%s\n' "$out" | sed -n 's/^saved: //p' | tail -1)
                summary+=("$suite $pipeline: ${run:-NO RUN FILE (see the output)}")
            done ;;
    esac
done

echo; echo "== summary"
printf '%s\n' "${summary[@]}"
echo
echo "Next: label what needs people's labels (the form of skill_turns), then decide each criterion with ~/.claude/skills/agent-app/scripts/eval_decide.py against its baseline."
