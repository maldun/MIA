#!/usr/bin/env bash
# Amendment A-83 (goal Verify of G-V1, 2026-11-01; owner decision D-178): the nine stage 4 checks of the root table are deferred. TC-MIA-002, -003, -009,
# -011, -019, -022, -024, -025 and -028 are eval, benchmark or statistical checks that need criteria, suites and pins (eval-spec.md) the plan does not have yet.
# Each gets a deferral record (TD-12 to TD-20) and its requirements carry `Relaxed` and `Target`; the target check stays "specified only".
# Note: specs/mia/amendments/A-83/A-83-note.md
# Made from the INSTALLED files at run time, each edit refused when its anchor is not found exactly once:
#   specs/mia/deferred.md        TD-12 to TD-20 appended (when TD-12 is not there yet)
#   specs/mia/requirements.md    14 top-level requirements get `Relaxed: TD-nn` and `Target`, and a History entry
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a83.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a83.sh --do      install and run the trace check; commit afterwards as "plan: A-83 installed"
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
TRIGGER = "the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first"
NODE_TESTS = "the node tests of the row pass (listed for the row in `specs/mia/tc-mia-status.md`)"
RECORDS = [
    ("TD-12", "TC-MIA-002", ["FR-9", "FR-10"], "Verify before asserting; lookup",
     NODE_TESTS + ", among them the number gate (`tests/acceptance/test_number_gate.py`), `tests/test_claim_pipelines_check_first.py`, `tests/test_verify_workflow.py`, `tests/test_search_command.py`; the pipelines run on the fake model",
     "the suites of the verify workflow (VitaminC and Wikidata, holdout, MP-light, single voice as baseline, 3 repeats) are decided by `eval_decide.py` against the baseline: the chosen gate passes fewer wrong claims and loses no more true claims among those with evidence (AC-2)",
     "the criteria, suites, holdout labels and model pins are not fixed (no `eval-spec.md` for MIA); the holdout is the owner's", "about 2 days plus GPU time", "a gate that passes more wrong claims than the single voice is not seen; the owner's use shows it"),
    ("TD-13", "TC-MIA-003", ["FR-11", "FR-12", "NFR-4"], "Literature review quality",
     NODE_TESTS + ", among them `tests/test_review_stages.py`, `tests/test_review_request.py`, `tests/test_gate_limits.py` and the scholarly source contract (IF-405)",
     "the review benchmark per tier: source recall and precision against the recorded baseline, 0 violations of the cut-off, 0 invented references, 100 % of quotes anchored (AC-3)",
     "the review entry is out of G-V1 (REQ-RUN-013 partly, D-128, D-130) and no benchmark with baseline exists", "about 3 days plus GPU time and the owner's labels", "invented references or unanchored quotes in a review are found by a reader only; the cut-off and the retraction rules are tested in code"),
    ("TD-14", "TC-MIA-009", ["FR-20"], "The skill path",
     NODE_TESTS + ", among them `tests/test_skill_path_doc.py`, `tests/test_seed_workflows.py`, `tests/test_check_baselines.py`, `tests/test_workflow_library.py`",
     "the record of the skill path: lookup as the documented example, the literature review added by the same path with specification, context graph and benchmark with holdout and baseline, and the review promoted within one month of the lookup (AC-9)",
     "the review is the next goal's (VAL-002 moved, D-134) and benchmarks with baselines are not recorded", "about 1 day to read the record once the review is promoted", "the path may not work for a second workflow; found when the review is added"),
    ("TD-15", "TC-MIA-011", ["FR-29"], "Adaptation to negative feedback",
     NODE_TESTS + ", among them `tests/test_chat_behaviour.py`, `tests/test_converse_behaviours.py`, `tests/test_chat_answers.py`",
     "the statistical run of AC-11: after 5 net negative votes at most 10 appearances in 1000 opportunities with fixed seeds, a higher rate after a positive vote, a vote on a fact leaves the fact unchanged; the implemented rate is 0.5 %, not 1 % (finding F-1 of the test table)",
     "the statistical run is stage 4 and its seeds, repeats and rate (0.5 % against 1 %) are not yet decided", "about half a day", "the rate after votes may differ from the wording; the unit tests of the mechanism pass"),
    ("TD-16", "TC-MIA-019", ["NFR-7"], "Speed and frame rate",
     NODE_TESTS + ", among them `tests/test_measure_latency.py`, `tests/test_runner_budgets.py`, `tests/test_model_turns.py`; the order of the turns is tested",
     "BM-MIA-001 (first text within 10 s on MP-light, also while a review slice runs) and BM-MIA-002 (30 fps or more on any phone inside the network and on desktop), median of repeated runs on the reference hardware (AC-19)",
     "the 10 s part is out of G-V1 (REQ-RUN-009 partly, D-128; REQ-RUN-007) and the phones' frame rate is a field measurement (D-62)", "about 1 day plus the field measurement", "slow first text or low frame rates are found by the users; VAL-006 collects them in use"),
    ("TD-17", "TC-MIA-022", ["NFR-2", "FR-17", "FR-18"], "Cost of the first try; comparing variants; learned choices",
     NODE_TESTS + ", among them `tests/test_runner_context_share.py`, `tests/test_eval_platform.py`, `tests/test_judge_calibration.py`",
     "the lookup suites on MP-light: fewer than 15 model calls per question, every model input at most 50 % of the context window, variants compared on the same cases with repeats, a learned choice logged next to the default and reversible (AC-22)",
     "the AC-22 measurement is out of G-V1 (REQ-RUN-005 partly, D-128) and the learning layer is not built (REQ-RUN-004 out, D-119)", "about 2 days plus GPU time", "the first try may need more calls than planned; the budget refusal of the runner holds"),
    ("TD-18", "TC-MIA-024", ["FR-14"], "Memory that improves",
     NODE_TESTS + ", among them `tests/test_memory_records.py`, `tests/test_chat_memory.py`, `tests/test_items_api.py`, `tests/test_memory_write_skill.py`",
     "the memory test set (store, update, contradict, recall, unknown) is passed at least as well as today's summary-based dreaming at equal or lower token cost; every record shows its source and can be corrected and deleted (AC-24)",
     "the check is marked later and Should in the root table; the test set and its labels do not exist", "about 3 days plus GPU time", "memory quality is judged by the users; records can be corrected and deleted"),
    ("TD-19", "TC-MIA-025", ["FR-15"], "Speech rules",
     NODE_TESTS + ", among them `tests/test_chat_repair.py` and `tests/test_speech_repair.py`",
     "the behaviour suite with the speech-rule detectors keeps the recorded precision and recall; a violation is repaired silently and never enters the memory as a scolding (AC-25)",
     "the recorded precision and recall and the behaviour suite are not in `eval/baselines`", "about 1 day", "a detector may drift without a number; the repair tests pass"),
    ("TD-20", "TC-MIA-028", ["FR-33"], "Estimate before a run",
     NODE_TESTS + ", among them `tests/test_workflow_library.py` and the IF-202 and IF-203 contract suites; the refusal of a run whose estimate exceeds its budget is tested",
     "on the recorded lookup runs the estimate of time, calls and tokens lies within a factor of 3 of the measured time, either way (AC-28, OPEN-3)",
     "no recorded lookup runs exist as a reference set and the lookup suites have no eval-spec", "about 1 day once runs are recorded", "the estimate may be off by more than 3; the user sees the estimate and the run still works"),
]


def td_block(td, tc, reqs, title, interim, target, reason, effort, risk):
    return (
        "## %s – %s (%s)\n- Kind: defer\n- Requirement: %s\n- Interim criterion: %s\n- Target: %s\n- Reason: %s; the stage 4 rows of the root table were deferred at the goal Verify of G-V1\n"
        "- Effort: %s (proposed)\n- Risk of the gap: %s\n- Owner: %s\n- Trigger: %s\n- Target check: specified only\n- Decision: D-178, 2026-11-01, %s\n- Status: open\n"
        % (td, title, tc, ", ".join(reqs), interim, target, reason, effort, risk, OWNER, TRIGGER, OWNER))


text = read(deferred)
if "## TD-12 " not in text:
    if text.count("## TD-11 ") != 1:
        sys.exit("%s: TD-11 is not found exactly once; install A-83 by hand" % deferred)
    text = text.rstrip("\n") + "\n\n" + "\n".join(td_block(*r) for r in RECORDS)
open(os.path.join(work, "deferred.md"), "w", encoding="utf-8").write(text)

req = read(requirements)
for td, tc, reqs, title, interim, target, *_ in RECORDS:
    for rid in reqs:
        m = re.search(r"^### %s – [^\n]*\n(?:(?!### ).*\n)*" % re.escape(rid), req, re.M)
        if not m:
            sys.exit("%s: the block of %s is not found; install A-83 by hand" % (requirements, rid))
        block = m.group(0)
        if "- Relaxed: %s\n" % td in block:
            continue
        if "- Relaxed:" in block or block.count("\n- Status: ") != 1:
            sys.exit("%s: %s has a Relaxed line already or no single Status line; install A-83 by hand" % (requirements, rid))
        new = block.replace("\n- Status: Approved\n", "\n- Status: Approved\n- Relaxed: %s\n- Target: %s\n" % (td, target_of(td) if False else target), 1)
        new = re.sub(r"^- History: –$", "- History: A-83 (2026-11-01): Relaxed %s (D-178)" % td, new, flags=re.M)
        if new == block or "Relaxed: %s" % td not in new:
            sys.exit("%s: %s has no 'Status: Approved' line; install A-83 by hand" % (requirements, rid))
        req = req.replace(block, new, 1)
open(os.path.join(work, "requirements.md"), "w", encoding="utf-8").write(req)
PY
copy "$WORK/deferred.md" specs/mia/deferred.md
copy "$WORK/requirements.md" specs/mia/requirements.md
finish
echo
echo "== trace_check, lines about TD-12 to TD-20 (none expected)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E "TD-(1[2-9]|20)" || echo none
