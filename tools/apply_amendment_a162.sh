#!/usr/bin/env bash
# Amendment A-162 (G-V3.CHAT follow-up, owner maldun, 2026-11-19): the eval target `digest` runs the step as the app runs it (REQ-EVL-012 to 015).
# Source: specs/mia/amendments/A-162-draft-eval-digest-target-runs-the-step-as-production.md. Made from the INSTALLED files at run time; every edit is skipped when it is done already and
# refused when its anchor is not found exactly once, so a second --do changes nothing.
# Needs first: REQ-EVL-012 to 015 as Draft in the requirements of N-4.1 (branch docs/a162-place, commit b0b396e5); the script refuses without them.
# Files that change:
#   specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation/test-spec.md   rows and scenarios of TC-EVL-012 to 015
#   specs/mia/test-requirements.md   (protected) TR-CHAT-012 (setup kind, stand-in fidelity) and its place in the group "Fakes (CHAT)"
#   specs/mia/review-log.md          one row (the amendment); id: the next free one (A162_FIRST_ID=nnn overrides)
# NOT changed here: tests/acceptance (TC-EVL-012 to 015 are written red in the next step: patch plus apply script), the code, the status of the requirements (Draft until Commit).
#   bash tools/apply_amendment_a162.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a162.sh --do      install and run the checks; commit afterwards with the paths named (never git add -A)
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
N41=specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation
REQ=$N41/requirements.md; TS=$N41/test-spec.md; TR=specs/mia/test-requirements.md; LOG=specs/mia/review-log.md
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$REQ" "$TS" "$TR" "$LOG" "$WORK" "${A162_FIRST_ID:-}" <<'PY'
import os
import re
import sys

req, ts, tr, log, work, first_id = sys.argv[1:7]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def die(message):
    sys.exit("REFUSED: " + message)


def edit(text, old, new, label):
    if new in text:
        return text                       # done already
    if text.count(old) != 1:
        die("anchor of %s found %d times (need exactly once)" % (label, text.count(old)))
    return text.replace(old, new, 1)


requirements = read(req)
for n in (12, 13, 14, 15):
    if "### REQ-EVL-0%d " % n not in requirements:
        die("REQ-EVL-0%d is not in %s: merge branch docs/a162-place first" % (n, req))

# ------------------------------------------------------------------------------------------------------------------ test-spec of N-4.1
rows = [
    "| TC-EVL-012 | REQ-EVL-012 | Component | 1 | the digest target with a scripted model that records the keyword arguments of every call; three cases (a summary of 20 000 characters, a failed and a stopped case) | every call carries num_predict 1024, seed 7 and temperature 0 | exact |",
    "| TC-EVL-013 | REQ-EVL-013 | Component | 1 | the digest target with the same scripted model and an app whose current model is not the pin | every call carries num_ctx 8192 | exact |",
    "| TC-EVL-014 | REQ-EVL-014 | Component | 1 | a file of 5 000 characters and a case with its path and SHA-256 and no result | the step receives exactly the text of the file | exact |",
    "| TC-EVL-015 | REQ-EVL-015 | Component | 1 | the case of TC-EVL-014 with the file removed and with one character changed | the run stops with an error that names the case; no model call is recorded | exact |",
]
scenarios = """
### TC-EVL-012 – The step runs with its own options
- Verifies: REQ-EVL-012
- Given: a scripted model that records the keyword arguments of every call, a pin with seed 7 and temperature 0, and three digest cases (a summary of 20 000 characters that needs pieces, a failed case and a stopped case)
- When: the harness runs the three cases
- Then: every recorded call carries num_predict 1024, seed 7 and temperature 0
- And: the first case needs more than one call

### TC-EVL-013 – The step runs with the context length of the pin
- Verifies: REQ-EVL-013
- Given: the same scripted model and an app whose current model is another model than the pin
- When: the harness runs one digest case
- Then: every recorded call carries num_ctx 8192

### TC-EVL-014 – A case reads its input from a referenced file
- Verifies: REQ-EVL-014
- Given: a file of 5 000 characters of known text and a case that holds its path and SHA-256 and no result
- When: the harness runs the case
- Then: the step receives exactly the text of the file, compared character by character

### TC-EVL-015 – A reference that does not match stops the run
- Verifies: REQ-EVL-015
- Given: the case of TC-EVL-014 once with the file removed and once with one character of the file changed
- When: the harness runs it
- Then: the run stops with an error that holds the case id
- And: the scripted model has recorded no call
"""
text = read(ts)
anchor = [line for line in text.split("\n") if line.startswith("| TC-EVL-011 |")]
if len(anchor) != 1:
    die("table row of TC-EVL-011 not found exactly once in the test-spec")
if "| TC-EVL-012 |" not in text:
    text = text.replace(anchor[0], anchor[0] + "\n" + "\n".join(rows), 1)
if "### TC-EVL-012 " not in text:
    text = text.rstrip("\n") + "\n" + scenarios
out("test-spec.md", text)

# ------------------------------------------------------------------------------------------------------------------ test requirements
tr_block = """
### TR-CHAT-012 – the scripted model of the digest target takes the arguments of the real model
- Applies to: TC-EVL-012, TC-EVL-013, TC-EVL-014, TC-EVL-015
- Requirement: REQ-EVL-012
- Group: Fakes (CHAT)
- Kind: setup
- Text: The scripted model of the digest target checks shall take the same arguments as `OllamaModel.chat` (messages, schema, model, profile, options) and fail on an unknown argument.
- Rationale: stand-in fidelity: a change of the signature of the real model must break these checks
- Credibility aspect: stand-in fidelity
- Verified by: a signature check in the test itself
- Status: Draft
- History: A-162 (2026-11-19), new
"""
text = read(tr)
text = edit(text, "| 10 | Fakes (CHAT) | The fake model server (G-V3.CHAT) | TR-CHAT-006, TR-CHAT-009 |",
            "| 10 | Fakes (CHAT) | The fake model server (G-V3.CHAT) | TR-CHAT-006, TR-CHAT-009, TR-CHAT-012 |", "group row of Fakes (CHAT)")
if "### TR-CHAT-012 " not in text:
    # the G-V3.CHAT section ends before the next "## " heading
    m = re.search(r"\n## G-V2\.TOOLBOX", text)
    if not m:
        die("the section of G-V2.TOOLBOX (end of the G-V3.CHAT test requirements) not found")
    text = text[:m.start()].rstrip("\n") + "\n" + tr_block + text[m.start():]
out("test-requirements.md", text)

# ------------------------------------------------------------------------------------------------------------------ review log
text = read(log)
row = ("**Amendment A-162: the eval target digest runs the step as the app runs it, owner maldun, 2026-11-19.** Findings of the feedback run 8 of EV-skill_turns "
       "(the long case: 16 calls, 608 s): the harness sends neither the options of the step (num_predict 1024) nor num_ctx. REQ-EVL-012 to 015 (options, context length, "
       "input by reference, reference that does not match) are Draft; checks TC-EVL-012 to 015 and TR-CHAT-012 are placed; no hand plausibility rating (the review is in small batches). "
       "Not part of this step: the protected tests (patch plus apply script), the code of `harness.py` and `tools/eval.py`.")
if "Amendment A-162" not in text:
    taken = {int(n) for n in re.findall(r"^\| D-(\d+) \|", text, re.M)}
    number = int(first_id) if first_id else max(taken) + 1
    if number in taken:
        die("D-%d is taken" % number)
    if not text.endswith("\n"):
        text += "\n"
    text += "| D-%d | %s |\n" % (number, row)
out("review-log.md", text)
PY
copy "$WORK/test-spec.md" "$TS"
copy "$WORK/test-requirements.md" "$TR"
copy "$WORK/review-log.md" "$LOG"
finish
if [ "$do_it" = 1 ]; then
    echo "══ the checks"
    "$PY" ~/.claude/skills/plan-phase/scripts/req_lint.py "$REQ" --glossary specs/mia/glossary.md 2>&1 | tail -3
    "$PY" ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | tail -4
    python3 -I tools/check_sysml_model.py . 2>&1 | tail -2
    echo "then: git add tools/apply_amendment_a162.sh $TS $TR $LOG && git commit -m 'plan: A-162 checks TC-EVL-012 to 015, TR-CHAT-012, review log'"
fi
