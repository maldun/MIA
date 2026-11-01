#!/usr/bin/env bash
# The stage ladder and the merge gate on this machine (blueprint M27). MIA has no CI, so the evidence is a local run: the gate needs --allow-local for it, and the owner decides
# whether a local run is enough. This script never gives an approval: the person types it (the last line printed shows the command).
#   bash tools/run_merge_gate.sh                 venv (Python 3.12, requirements.txt and requirements-db.txt), stages 0 to 2, then the gate without an approval
#   MIA_GATE_UPTO=3 bash tools/run_merge_gate.sh also stage 3: it starts podman containers (container-alone, a throwaway postgres:16, the compose stack). Do this when the
#                                                machine is idle; there is a hardware problem at MIA shutdown (fatal CPU machine checks), back up first.
#   MIA_GATE_DRY=1 bash tools/run_merge_gate.sh  only prints the steps (no venv, no run)
# The log is .stages/log.jsonl (not in git). Refuses on a dirty tracked tree: the gate reads the exact commit.
set -eu
cd "$(dirname "$0")/.."
SK="$HOME/.claude/skills/dev-workflow/scripts"
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "the tracked tree is not clean: the gate reads the exact commit"; exit 1; }
if [ "${MIA_GATE_DRY:-0}" = 1 ]; then
    python3 "$SK/run_stages.py" --stages stages.yaml --upto "${MIA_GATE_UPTO:-2}" --dry-run
    exit 0
fi
PY312=$(command -v python3.12 || true)
[ -n "$PY312" ] || { echo "python3.12 is not installed (the project runs on 3.12)"; exit 1; }
if [ ! -x .venv-gate/bin/python ]; then
    "$PY312" -m venv .venv-gate
    .venv-gate/bin/pip install -q -r requirements.txt -r requirements-db.txt
fi
export PATH="$PWD/.venv-gate/bin:$PATH"
mkdir -p .stages
python "$SK/run_stages.py" --stages stages.yaml --upto "${MIA_GATE_UPTO:-2}" --log .stages/log.jsonl --keep-going || true
python "$SK/stage_report.py" --log .stages/log.jsonl 2>/dev/null | tail -20 || true
echo
python "$SK/merge_gate.py" --stages stages.yaml --log .stages/log.jsonl --commit HEAD --allow-local || true
echo
echo "To approve (you, after reading the verification report):"
echo "  python $SK/merge_gate.py --stages stages.yaml --log .stages/log.jsonl --commit HEAD --allow-local --approved-by \"<your name>\""
