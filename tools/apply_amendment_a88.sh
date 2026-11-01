#!/usr/bin/env bash
# Amendment A-88 (merge gate of G-V1, 2026-11-01; owner decision D-182): the smoke tests leave the merge gate and go to the Deploy phase, with a record.
#   TD-25  tests/smoke/ (SMOKE-MIA-001, SMOKE-MIA-003, SMOKE-GATE-001, -002) are not run by the stage ladder: the files are named smoke_*.py, so the step `smoke` found no test and
#          failed ("NO TESTS RAN"), and the tests need the owner's workstation (the full compose stack, the real Ollama), where Phase 6 runs them (deploy-plan.md)
# Note: specs/mia/amendments/A-88/A-88-note.md
# Made from the INSTALLED files at run time, each edit refused when its anchor is not found as expected:
#   specs/mia/deferred.md        TD-25 appended
#   specs/mia/requirements.md    NFR-9 gets `Relaxed: TD-25`, `Target`, History
#   stages.yaml                  the step `smoke` is removed (a comment says where the smoke tests run)
# INSTALL IT ON THE LINE OF WORK goal/v1 (A-87 installed).
#   bash tools/apply_amendment_a88.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a88.sh --do      install and run the trace check; commit afterwards as "plan: A-88 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - specs/mia/deferred.md specs/mia/requirements.md stages.yaml "$WORK" <<'PY'
import os
import re
import sys
deferred, requirements, stages, work = sys.argv[1:5]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)
TARGET = "the smoke tests of `tests/smoke/` have run on the owner's workstation in the Deploy phase of G-V1 (`goals/G-V1/deploy-plan.md`), their results are in `deployment-record.md`, and the stage ladder has a smoke step that finds them (pattern `smoke_*.py`)"

text = read(deferred)
if "## TD-25 " not in text:
    if text.count("## TD-24 ") != 1:
        sys.exit("%s: TD-24 is not found exactly once; install A-88 by hand (A-87 must be installed)" % deferred)
    block = ("## TD-25 – The smoke tests are not part of the merge gate\n- Kind: defer\n- Requirement: NFR-9\n"
             "- Interim criterion: the same ground is covered by the stage 3 steps `container-alone` (TC-API-013) and `contract-postgres` (IF-102 on a throwaway postgres:16), by the stage 2 integration steps and by the tests of the compose files (`tests/test_deploy.py`, `tests/test_delivery_on_stack.py`); the smoke tests themselves are run in Deploy\n"
             "- Target: %s\n"
             "- Reason: `tests/smoke/` holds `smoke_fresh_install.py` (SMOKE-MIA-001), `smoke_stack.py` (SMOKE-MIA-003) and `smoke_gate.py` (SMOKE-GATE-001, -002). The step `smoke` used the pattern `test_*.py`, found no test and failed with NO TESTS RAN. The files themselves say they run on the owner's workstation in Phase 6: the first two bring up the whole compose stack (this machine cannot run it, fatal CPU machine checks at shutdown under load), the third runs the number gate through the real Ollama, which is an eval-style run (none belongs in this Verify, D-178); found at the merge gate of G-V1, the owner chose this (D-182)\n"
             "- Effort: about half a day on the workstation (three commands, then the record), and one line in `stages.yaml`\n"
             "- Risk of the gap: a fresh install that does not start, or a stack whose front does not answer, is found in Deploy and not at the merge. Mitigation: `container-alone`, `contract-postgres` and the stack test of N-1.3 run in the gate\n"
             "- Owner: Stefan Reiterer\n- Trigger: the Deploy phase of G-V1, or 2026-12-31, whichever first\n- Target check: specified only\n- Decision: D-182, 2026-11-01, Stefan Reiterer\n- Status: open\n") % TARGET
    text = text.rstrip("\n") + "\n\n" + block
out("deferred.md", text)

req = read(requirements)
m = re.search(r"^### NFR-9 – [^\n]*\n(?:(?!^### ).*\n)*", req, re.M)
if not m:
    sys.exit("%s: the block of NFR-9 is not found; install A-88 by hand" % requirements)
b = m.group(0)
if "- Relaxed: TD-25\n" not in b:
    if "- Relaxed:" in b or b.count("\n- Status: Approved\n") != 1 or b.count("\n- History: –\n") != 1:
        sys.exit("%s: NFR-9 has a Relaxed line already, or no single 'Status: Approved' and 'History: –' line; install A-88 by hand" % requirements)
    nb = b.replace("\n- Status: Approved\n", "\n- Status: Approved\n- Relaxed: TD-25\n- Target: %s\n" % TARGET, 1).replace("\n- History: –\n", "\n- History: A-88 (2026-11-01): Relaxed TD-25 (D-182)\n", 1)
    req = req.replace(b, nb, 1)
out("requirements.md", req)

text = read(stages)
m = re.search(r"^  - \{id: smoke,[^\n]*\n", text, re.M)
if m:
    if len(re.findall(r"^  - \{id: smoke,", text, re.M)) != 1:
        sys.exit("%s: the step smoke is not found exactly once; install A-88 by hand" % stages)
    text = text.replace(m.group(0), "  # no smoke step (A-88, TD-25): tests/smoke/ runs on the owner's workstation in the Deploy phase (goals/G-V1/deploy-plan.md)\n", 1)
out("stages.yaml", text)
PY
copy "$WORK/deferred.md" specs/mia/deferred.md
copy "$WORK/requirements.md" specs/mia/requirements.md
copy "$WORK/stages.yaml" stages.yaml
finish
echo
echo "== trace_check, errors about TD-25 (none expected)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E "ERROR.*TD-25" || echo none
echo "== the stage ladder has no smoke step"
python3 ~/.claude/skills/dev-workflow/scripts/run_stages.py --stages stages.yaml --upto 3 --dry-run | grep -c smoke || true
