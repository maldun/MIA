# G-V3.CHAT: decision of the holdout of EV-skill_turns (REQ-CHA-049, 053, 054)

Run by the owner (maldun), 2026-11-16, on the pin MP-light (`gemma4:12b-it-qat`, seed 7, temperature 0), step `VERSION` 7 (prompt version 4 and the cleaning of A-150 to A-153), 24 cases times 3 repeats. The numbers below are copied from the owner's output of `tools/holdout_skill_turns.sh decide`; no agent opened the holdout files, the cases, the outputs or the labels.

## Result: all three criteria PASS (first run)
| Requirement | Criterion | Result | Cases | Rate | 95 % interval | Checks |
|---|---|---|---|---|---|---|
| REQ-CHA-049 | pass (the quoted instruction is reported, not followed), min 1.0, fold all | **PASS** | 6 of 6 | 1.000 | 0.610 to 1.000 | point 1.000 >= 1.0; repeats 3-3 |
| REQ-CHA-053 | faithful, min 0.85, low >= 0.70, rule both | **PASS** | 23 of 24 | 0.958 | 0.798 to 0.993 | point 0.958 >= 0.85; bound 0.798 >= 0.70; sign test p = 1.000; repeats 3-3 |
| REQ-CHA-054 | persona, min 0.80, low >= 0.70, rule both | **PASS** | 24 of 24 | 1.000 | 0.862 to 1.000 | point 1.000 >= 0.80; bound 0.862 >= 0.70; sign test p = 1.000; repeats 3-3 |

## How it was made (facts for the Verify record)
- **The run that decides:** `data/eval/skill_turns.holdout__default__20261115-232140.jsonl` (the first holdout run). Three more holdout runs of the same suite exist (`…232642`, `…232956`, `…233317`, the last made by `tools/holdout_all.sh`); they use the same seed and temperature and are repeats, **not** fresh-seed re-runs, and they did not decide anything. No criterion failed, so no re-run with fresh seeds was needed.
- **Labels:** 27 lines in `eval/labels/skill_turns.holdout.jsonl`, set by the owner (24 from the first form, 3 for the long summaries whose text differs between repeats, `st-long-h1` to `st-long-h3`). A stale file made from the dev marks was deleted by the owner before labelling.
- **Rescoring:** a run is scored while it runs, before its holdout outputs have a label, so the stored run said `open` everywhere and `eval_decide` first reported 0 of 6 and "no case selected". That was a gap in the decision step, not a result. `tools/rescore_digest_run.py` scores the **same stored outputs** again with the labels (no model, no new run, the run file unchanged; it also updates the second copy of the score that `eval_decide` reads, found and fixed `bf0edc3`). The first decide output (REQ-CHA-049 0 of 6, 053 and 054 no case) is therefore not a verdict and not counted as a first FAIL.
- **Baseline:** `eval/baselines/skill_turns__nodigest__baseline.jsonl` has no cases, so the sign test ("not worse than the baseline") is vacuous (0 of 0 shared cases, p = 1.000). The point and bound checks are the substance of REQ-CHA-053 and 054.
- **One case is unfaithful** (23 of 24 for REQ-CHA-053): the owner labelled it so. Read its transcript before it goes into Validate (VAL-013, real summaries in use).

## What this does and does not settle
- It settles the three evaluated criteria of G-V3.CHAT on the holdout: the owner's decision, per the Verify rules.
- It does not change the verdict of the last Verify run (Not verified because of F-33 to F-35, accepted by the owner as D-339 and TD-85). The holdout shows the digest step on the pin; the cleaning of the model text in the chat path is tested by unit tests and the Verify runs, not by this suite.
- The holdout of `skill_turns` is spent: it has been seen. A later change of the prompt needs new holdout cases (`eval-spec.md`: no case moves between splits).
