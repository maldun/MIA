#!/usr/bin/env bash
# The holdout run of EV-skill_turns for the Verify of G-V3.CHAT (REQ-CHA-049, 053, 054). Run by the OWNER only: an agent never runs or opens the holdout (CLAUDE.md, agent-app).
# Three steps, each safe to repeat:
#   holdout_skill_turns.sh              look only: checks the branch, the model server and the pin, prints what --do would do
#   holdout_skill_turns.sh --do         starts Ollama if needed, runs the holdout (3 repeats, pin MP-light), builds the labelling form in ~/Downloads (NOT in the repo)
#   holdout_skill_turns.sh decide RUN   after you labelled and applied the marks: decides the three criteria with eval_decide.py against the baseline
# A failing criterion is re-run once with fresh seeds, never more (eval-spec.md): `decide` says so; seeds, repeats, n and thresholds are never changed.
set -euo pipefail

WT=/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v3-chat
PY=/home/maldun/prog/Python/venvs/mia312/bin/python
PIN_DIGEST=sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3
FORM="$HOME/Downloads/skill-turns-holdout-labels.html"
BASELINE=eval/baselines/skill_turns__nodigest__baseline.jsonl
REQS=specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md
mode=look; run_file=""
case "${1:-}" in
    --do) mode=do ;;
    decide) mode=decide; run_file="${2:?usage: holdout_skill_turns.sh decide RUNFILE}" ;;
    "") ;;
    *) echo "usage: $0 [--do | decide RUNFILE]"; exit 2 ;;
esac
cd "$WT"

echo "== state"
branch=$(git rev-parse --abbrev-ref HEAD); head=$(git rev-parse --short HEAD)
echo "branch $branch, HEAD $head"
[ "$branch" = "goal/v3.chat" ] || { echo "STOP: not on goal/v3.chat"; exit 1; }
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then echo "STOP: tracked files changed (commit or discard first); the run header names the commit"; exit 1; fi

if [ "$mode" = decide ]; then
    [ -f "$run_file" ] || { echo "STOP: no such run file: $run_file"; exit 1; }
    echo "== decide $run_file (labels: eval/labels/, applied with tools/apply_digest_labels.py)"
    for id in REQ-CHA-049 REQ-CHA-053 REQ-CHA-054; do
        line=$(grep -h "^- Eval criterion:" "$REQS" | grep -F "req:$id" | head -1 | sed 's/^- Eval criterion: //')
        [ -n "$line" ] || { echo "no criterion line for $id"; continue; }
        echo; echo "-- $id: $line"
        $PY ~/.claude/skills/agent-app/scripts/eval_decide.py --run "$run_file" --baseline "$BASELINE" --criterion "$line" --select "req:$id" || true
    done
    echo; echo "A criterion that FAILS may be re-run ONCE with fresh seeds (tell the agent or do it with eval.py); NOT DECIDED is not a pass."
    exit 0
fi

echo "== model server and pin"
if ! curl -sf localhost:11434/api/tags >/dev/null; then
    echo "Ollama is not answering on localhost:11434"
    if [ "$mode" = do ]; then podman start ollama >/dev/null; for _ in $(seq 20); do curl -sf localhost:11434/api/tags >/dev/null && break; sleep 1; done
    else echo "(--do would run: podman start ollama)"; fi
fi
if curl -sf localhost:11434/api/tags >/dev/null; then
    have=$(curl -s localhost:11434/api/tags | $PY -c "import json,sys; print(next((m['digest'] for m in json.load(sys.stdin)['models'] if m['name']=='gemma4:12b-it-qat'), 'missing'))")
    [ "sha256:$have" = "$PIN_DIGEST" ] || [ "$have" = "$PIN_DIGEST" ] || { echo "STOP: gemma4:12b-it-qat is $have, the pin says $PIN_DIGEST"; exit 1; }
    echo "pin MP-light: digest matches"
fi

echo "== plan"
echo "1. $PY tools/eval.py --holdout run skill_turns.holdout --pin MP-light --repeats 3   (about 4 minutes; saved in data/eval/)"
echo "2. $PY -I tools/make_digest_label_form.py RUN eval/suites/skill_turns.holdout/cases.jsonl $FORM   (outside the repo: holdout texts are never committed)"
echo "3. you label the form, download the marks, then apply them:"
echo "   $PY -I tools/apply_digest_labels.py ~/Downloads/digest-marks.json skill_turns.holdout --by maldun --do"
echo "4. $0 decide data/eval/<the run file>"
[ "$mode" = do ] || { echo; echo "look only: nothing was run. Add --do to start."; exit 0; }

echo "== run"
out=$($PY tools/eval.py --holdout run skill_turns.holdout --pin MP-light --repeats 3 2>&1 | tee /dev/stderr)
run=$(printf '%s\n' "$out" | sed -n 's/^saved: //p' | tail -1)
[ -n "$run" ] || { echo "STOP: no 'saved:' line in the output"; exit 1; }
echo "== form"
$PY -I tools/make_digest_label_form.py "$run" eval/suites/skill_turns.holdout/cases.jsonl "$FORM"
echo
echo "run file: $run"
echo "form:     $FORM   (open it in the browser, label every card, download the marks)"
echo "next:     apply the marks (step 3 above), then:  $0 decide $run"
