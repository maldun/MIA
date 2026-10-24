# Amendments: number gate (Plan iteration 1)

## A-01 – No evidence, no verdict; a failed number check informs the judge (2026-10-24)
**Decided by:** the owner (decision 1 of the T-07 report; HLS amendment 4, D-44). **Trigger:** T-06 baseline and the first T-07 evidence (`implementation-log.md`).

### What changed
| Item | Before | After |
|---|---|---|
| REQ-GATE-002 | a failed number check returns refuted without a model call | a failed check puts the line "Number check: fail ..." in the judge's evidence; the judge's verdict stands (3 model calls) |
| REQ-GATE-003 | style also runs when the check is not_applicable | style runs for pass, fail, inconclusive |
| REQ-GATE-006 (new) | – | claim with a number and empty evidence: verdict unclear, status inconclusive, 0 model calls |
| REQ-VER-002 | false pass at most 5 % (doubtful) | unchanged text and criterion; plausibility now "by construction" |
| REQ-VER-004 | right at least 90 % of the true Wikidata claims | false fail at most 5 % (no true claim refuted), same size and rule as REQ-VER-002, false alarm 1.3 % |
| IF-003 | calls 0 when the number check decides | calls 0 when the claim has a number and no evidence |
| HLS AC-2(a) | "loses no more true claims" | "... among the claims that come with evidence"; Wikidata claims answer unclear |
| THR-001 | mitigation REQ-GATE-002 | mitigation REQ-GATE-006; residual risk: an instruction in the evidence can now reach the verdict of a number claim (measured by EV-verdicts_injection) |

Documents changed: `requirements.md`, `test-spec.md`, `eval-spec.md`, `threat-model.md`, `architecture.sysml`, `plan.md`, `specs/mia/high-level-spec.md`, `specs/mia/review-log.md`. A new baseline is not needed for the Wikidata criteria (the new gate abstains by construction); the VitaminC baselines (T-06, T-11) are of `verify.single@1` and `verify.cops@1` and stay valid.

### Protected tests that must change (to be written by the owner, outside the implementing session)
All in `tests/acceptance/`. Everything else in these files stays as it is. Helpers (`tests/helpers/gate_lab.py`) need no change.

**`test_number_gate.py`**
1. `test_a_failed_check_decides_without_a_model_call` (TC-GATE-002, REQ-GATE-002) is replaced. Suggested body, same claim and evidence, a judge that always says supported:
   ```python
   @mark.req("REQ-GATE-002")
   def test_a_failed_check_goes_to_the_judge(self):
       """TC-GATE-002: the check says fail; the judge sees the line and decides; the verdict is the judge's."""
       result, model = gate_run(cops_answer("supported"), TOWER, "The tower is 1,020 m tall.")
       answer = self.done(result)
       self.assertEqual(len(model.prompts), 3)
       self.assertIn("Number check: fail", model.prompts[2])
       self.assertEqual((answer["verdict"], answer["status"]), ("supported", "pass"))
   ```
2. `test_a_claim_the_check_leaves_open_goes_to_one_judgement_style` (TC-GATE-003): remove the third pair `(TOWER, "")` from the loop (an empty evidence now abstains, TC-GATE-006); the loop keeps `(TOWER, "The tower is 1,200 m tall.")` and `("The hall is 40 m long.", "The hall has 40 seats.")`. The single-style part stays.
3. New `test_a_number_claim_without_evidence_is_not_decided` (TC-GATE-006, REQ-GATE-006): for 5 claims with a number (`TOWER`, "The group sold 4.8 million records.", "The road is 453 kilometres long.", "The bridge was built in 1937.", "The album has 12 tracks.") and evidence `""`: `gate_run(cops_answer("supported"), claim, "")` is done, `answer["verdict"] == "unclear"`, `answer["status"] == "inconclusive"`, `answer["calls"] == 0`, `answer["facts"] == []`, `len(model.prompts) == 0`.
4. `test_the_result_record_has_verdict_status_calls_seconds_and_facts` (TC-IF-003): the first block (`decided`) uses `(TOWER, "")` instead of `(TOWER, "The tower is 1,020 m tall.")`; the assertions stay (calls 0, facts []; the verdict/status table, for `unclear`/`inconclusive`). The loop over the three words with `("The hall is 40 m long.", "The hall has 40 seats.")` stays.
5. `test_the_number_check_runs_before_the_first_model_call` (TC-GATE-001) needs no change (its two claims with empty evidence still run no check, and the pipeline is done).

**`tests/smoke/smoke_gate.py`**: the Wikidata smoke cases now expect the verdict unclear (see SMOKE-GATE-001); change the expectation if it names refuted/supported for those cases.

### Consequences for the plan
T-08 now implements REQ-GATE-001..006 and IF-003 and turns TC-GATE-001..006 and TC-IF-003 green once the tests above are changed. T-09 gets a second target: the judge must treat the "Number check: fail" line as strong evidence and must resist an instruction in the evidence that argues against it (injection suite). The cost table improves: a Wikidata claim costs no model call.
