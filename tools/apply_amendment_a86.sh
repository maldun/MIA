#!/usr/bin/env bash
# Amendment A-86 (goal Verify of G-V1, 2026-11-01; owner decision D-180: "defer all"): two deferral records from the findings F-01 and F-02 of the verification report.
# TD-21: NFR-8 and CON-7 (the state lives in PostgreSQL) are not met in the product, the app keeps its state in the file backend. TD-22: NFR-3, the red-team half of
# TC-MIA-006 (0 failures over all red-team cases) is not held, the seven rt_* suites have 2 dev cases each. Note: specs/mia/amendments/A-86/A-86-note.md
# Made from the INSTALLED files at run time, each edit refused when its anchor is not found as expected:
#   specs/mia/deferred.md      TD-21 and TD-22 appended (when TD-21 is not there yet)
#   specs/mia/requirements.md  NFR-8, CON-7 (TD-21) and NFR-3 (TD-22) get `Relaxed`, `Target` and a History entry
# INSTALL IT ON THE LINE OF WORK goal/v1 (A-85 installed).
#   bash tools/apply_amendment_a86.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a86.sh --do      install and run the trace check; commit afterwards as "plan: A-86 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - specs/mia/deferred.md specs/mia/requirements.md "$WORK" <<'PY'
import os
import re
import sys
deferred, requirements, work = sys.argv[1:4]
read = lambda path: open(path, encoding="utf-8").read()
OWNER = "Stefan Reiterer"
TRIGGER = "the Plan of the next iteration, or 2026-12-31, whichever first"
RECORDS = [
    ("TD-21", ["NFR-8", "CON-7"], "The state is in PostgreSQL",
     "the storage layer behind IF-102 works on files and is tested there (`tests/test_storage.py`, the IF-102 contract suite on the file backend) and on PostgreSQL where psycopg exists (`tests/test_storage_postgres.py`, `tools/contract_postgres.sh`, not run in the goal Verify); the stack starts the database and `deploy/up.sh backup` and `restore` save and restore it together with the data folder; the app keeps its state in the file backend (`web_app.py`), accounts, history, records and workflows alike",
     "the app reads `MIA_DATABASE_URL`, the `mia` image holds psycopg (`requirements-db.txt`), the shared state is in PostgreSQL, files to database and back give identical files, a change by one user is visible on a second connection within 5 s with its author, and backup and restore return the same records (AC-15, TC-MIA-015)",
     "the storage layer was built and verified node by node (N-3.1 to N-3.3), but wiring the app and the image to it was never planned as a task; recorded at node level (D-139 (4), N-4.2 F3) and found at the goal Verify (F-01); the owner chose to defer it (D-180)",
     "about 2 days (wire `web_app.py` to `Storage` on PostgreSQL, add psycopg to the image, the move command, run the PostgreSQL contract suites, rebuild the image)",
     "a lost or damaged data volume loses the state; the database that runs is empty. Mitigation: `deploy/up.sh backup` saves the data folder, to be done before every update"),
    ("TD-22", ["NFR-3"], "Red-team cases of the untrusted inputs",
     "the deterministic mitigations pass: the tool door and its untrusted-input handling (`tests/test_tool_calls_untrusted.py`, `tests/test_tool_calls_web_log.py`), the sandbox tests, the injection signal checks and the PDF wall (`tests/test_pdf_text.py` with bwrap); the compose stack runs with `sandbox_backend: none`, so the script check is off there",
     "0 failures over all red-team cases: the seven `rt_*` suites hold enough labelled cases (not 2 each, target kind `pending`) and the injection suites `verdicts_injection` run with their holdouts on MP-light (TC-MIA-006, AC-6)",
     "the red-team suites are drafts of 2 cases each, their cases are the owner's to label and the runs belong to the stage 4 evals that were deferred (D-178); `tests/test_harness.py` fails on the same fact (rt_edit has 2 cases, wants 30); found at the goal Verify (F-02), the owner chose to defer it (D-180)",
     "about 3 days plus GPU time, the labelling is the owner's",
     "an injected instruction in a page or paper may change a verdict or start a tool without a test noticing. Mitigation: the tool set per step is the protection (THR entries), the deterministic tests above, and the users are trusted (CON-6)"),
]


def td_block(td, reqs, title, interim, target, reason, effort, risk):
    return ("## %s – %s\n- Kind: defer\n- Requirement: %s\n- Interim criterion: %s\n- Target: %s\n- Reason: %s\n- Effort: %s (proposed)\n- Risk of the gap: %s\n- Owner: %s\n"
            "- Trigger: %s\n- Target check: specified only\n- Decision: D-180, 2026-11-01, %s\n- Status: open\n"
            % (td, title, ", ".join(reqs), interim, target, reason, effort, risk, OWNER, TRIGGER, OWNER))


text = read(deferred)
if "## TD-21 " not in text:
    if text.count("## TD-20 ") != 1:
        sys.exit("%s: TD-20 is not found exactly once; install A-86 by hand (A-83 must be installed)" % deferred)
    text = text.rstrip("\n") + "\n\n" + "\n".join(td_block(*r) for r in RECORDS)
open(os.path.join(work, "deferred.md"), "w", encoding="utf-8").write(text)

req = read(requirements)
for td, reqs, title, interim, target, *_ in RECORDS:
    for rid in reqs:
        m = re.search(r"^### %s – [^\n]*\n(?:(?!### ).*\n)*" % re.escape(rid), req, re.M)
        if not m:
            sys.exit("%s: the block of %s is not found; install A-86 by hand" % (requirements, rid))
        block = m.group(0)
        if "- Relaxed: %s\n" % td in block:
            continue
        if "- Relaxed:" in block or block.count("\n- Status: Approved\n") != 1:
            sys.exit("%s: %s has a Relaxed line already or no single 'Status: Approved' line; install A-86 by hand" % (requirements, rid))
        new = block.replace("\n- Status: Approved\n", "\n- Status: Approved\n- Relaxed: %s\n- Target: %s\n" % (td, target), 1)
        if re.search(r"^- History: –$", new, re.M):
            new = re.sub(r"^- History: –$", "- History: A-86 (2026-11-01): Relaxed %s (D-180)" % td, new, flags=re.M)
        else:
            new = re.sub(r"^(- History: .*)$", r"\1; A-86 (2026-11-01): Relaxed %s (D-180)" % td, new, count=1, flags=re.M)
        req = req.replace(block, new, 1)
open(os.path.join(work, "requirements.md"), "w", encoding="utf-8").write(req)
PY
copy "$WORK/deferred.md" specs/mia/deferred.md
copy "$WORK/requirements.md" specs/mia/requirements.md
finish
echo
echo "== trace_check, errors about TD-21, TD-22, NFR-8, CON-7, NFR-3 (none expected)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E "ERROR.*(TD-2[12]|NFR-8|CON-7|NFR-3)" || echo none
