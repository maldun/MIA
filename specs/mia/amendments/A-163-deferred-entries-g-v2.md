# A-163 draft: three deferred entries for G-V2 (TD-86, TD-87, TD-88)

Owner decisions of 2026-11-20 (D-355). `specs/mia/deferred.md` is protected: the owner appends the block below at the end of the file (after TD-85), or runs `bash tools/apply_deferred_g_v2.sh --do`. The Sign-off lines are yours to tick: nothing is signed here.

---

## TD-86 – Converted runs read a fresh seeded toolbox, not the live trust and lifecycle of the owner (DRAFT)
- Kind: defer
- Requirement: REQ-WFM-058, REQ-WFM-060 (finding F-07 of the Verify of G-V2.CONVERT: trust and lifecycle of a node are not live on the converted path)
- Interim criterion: each converted run builds a fresh in-memory toolbox and seeds the node code shipped in `library/nodes` as trusted and tested; the code text comes from the repository, so no code that the owner has not reviewed runs; the five accepted skills use only those nodes
- Target: a test with `code.normalize_plan` set untrusted by the owner: `Core.run("plan_question")` refuses and says why; the converted path reads the toolbox store of the app
- Reason: the owner decided on 2026-11-17 that this belongs to the sub goal that improves the skills; no skill breaks today
- Effort: about half a day (wire the real toolbox into `Core._run_converted`, one protected check)
- Risk of the gap: an untrusted or retired node that the owner sets in the toolbox still runs in a converted skill, as long as its text is in `library/nodes`
- Owner: Stefan Reiterer
- Trigger: the start of the sub goal "improve the skills", or the first node that is not shipped in the repository, whichever first
- Target check: specified only
- Decision: D-355, 2026-11-20 (F-07 first decided 2026-11-17)
- Sign-off: pending
- Status: open

## TD-87 – Budgets and a stop request on the converted path have no requirement (REQ-WFM-143 stays a draft) (DRAFT)
- Kind: defer
- Requirement: FR-45 (finding F-05 of the Verify of G-V2.CONVERT: seconds and steps are checked only inside controllers, calls and tokens not at all, a stop is read only at the start and in controllers)
- Interim criterion: the five converted skills declare only steps, seconds and tool budgets and are short; the tool budgets and the IF-402 door are checked by `tests/test_converted_tools.py`; the old runner remains the path of a skill whose converted run fails its criterion
- Target: REQ-WFM-143 as drafted in section 4 of `amendments/A-159-draft-split-snapshots.md` (the Workflow execution checks the declared budgets and the stop request before each step and ends the run with status `budget` naming the key, or `stopped`), with the check TC-WFM-143 and a test requirement; implementation in the sub goal that improves the skills (it also lists "`model_step` has no budget")
- Reason: the owner decided on 2026-11-20 (D-355) to accept the deviation for G-V2 and not to write the requirement now
- Effort: a requirement block with review and plausibility record (about 1 hour of the owner), then about a day of code and tests
- Risk of the gap: a converted run can overrun calls or tokens and a stop that comes in the middle of a top-level step is seen late
- Owner: Stefan Reiterer
- Trigger: the start of the sub goal "improve the skills", or the first converted skill with a budget of calls or tokens, whichever first
- Target check: specified only
- Decision: D-355, 2026-11-20
- Sign-off: pending
- Status: open

## TD-88 – AC-34 is decided on the dev split only, the suites of research, plans, verdicts, computable and extraction have no holdout (DRAFT)
- Kind: defer
- Requirement: AC-34, REQ-WFM-110 to 114 (equivalence of the converted skills with the old runner)
- Interim criterion: each criterion is decided on the dev split as AC-34 says, with the pin MP-light (digest `38044be4f923`, seed 7, temperature 0), 3 repeats and the baselines of the old runner of 2026-11-15; a criterion that fails and cannot be re-run with fresh seeds (the pin fixes the seed, `tools/eval.py` has no seed option) is NOT DECIDED, accepted by the owner, and that skill stays on the old runner
- Target: holdout suites for the five skills, cases labelled by the owner, decided once with `eval_decide.py` in a Verify, and a way to re-run with fresh seeds (an amendment of `eval-spec.md`)
- Reason: AC-34 names the dev split; the owner chose on 2026-11-20 (D-355) to verify G-V2 on dev and not to build holdouts now
- Effort: labelling 20 to 50 holdout cases per suite by the owner, about a day; a seed option about 2 hours
- Risk of the gap: a prompt or graph detail tuned on the dev cases can pass the dev criterion and be worse on unseen cases; the dev-holdout gap is not measured
- Owner: Stefan Reiterer
- Trigger: the first change of a converted skill that is tuned on its dev cases (the sub goal "improve the skills"), or the Validate of G-V2 (VAL-007), whichever first
- Target check: specified only
- Decision: D-355, 2026-11-20
- Sign-off: pending
- Status: open
