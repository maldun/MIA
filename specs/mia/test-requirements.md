# Test requirements: MIA

Requirements on the checks of `test-spec.md` (M41): under which conditions a verdict counts. Protected like the checks; changed only by amendment. This file starts with goal G-V2.CONVERT (REQ-WFM-057 to 066, 069, 110 to 115); other goals add their items with their own prefix. No catalog item is adopted: `dev-workflow/assets/test-requirements-catalog.md` is a blank template, so there is no `Source:` line.

## Groups
| Order | Group | What it covers | Test requirements |
|---|---|---|---|
| 1 | Conversion eval runs | conditions under which an equivalence decision of a converted skill counts | TR-CONVERT-001, TR-CONVERT-002, TR-CONVERT-003, TR-CONVERT-004, TR-CONVERT-005 |
| 2 | Conversion stand-ins | the fake model server of the same-calls check | TR-CONVERT-006 |
| 3 | Conversion exact values | hand-checked expected values of the deterministic conversion and snapshot tests | TR-CONVERT-007 |

### TR-CONVERT-001 – Equivalence runs use the pinned model
- Applies to: EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction, TC-WFM-110, TC-WFM-111, TC-WFM-112, TC-WFM-113, TC-WFM-114
- Requirement: REQ-WFM-110, REQ-WFM-111, REQ-WFM-112, REQ-WFM-113, REQ-WFM-114
- Group: Conversion eval runs
- Kind: setup
- Text: The check shall run the old and the converted version of a skill on the model with the digest of pin MP-light and the options num_ctx, temperature and seed of eval-spec.md.
- Rationale: a model tag can point to new weights after a pull and another temperature changes the rates; the baselines of v0.1.0 were measured on this pin (eval-spec.md, Model pins)
- Credibility aspect: numerical settings
- Verified by: inspection
- Status: Draft

### TR-CONVERT-002 – Three repeats, fresh seeds for the re-run
- Applies to: EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction, TC-WFM-110, TC-WFM-111, TC-WFM-112, TC-WFM-113, TC-WFM-114
- Requirement: REQ-WFM-110, REQ-WFM-111, REQ-WFM-112, REQ-WFM-113, REQ-WFM-114
- Group: Conversion eval runs
- Kind: setup
- Text: The check shall run 3 repeats per case, fold them by majority, and decide a failing criterion only on one re-run with fresh seeds.
- Rationale: repeats of one case are not independent observations; the false alarm in the criterion lines (0.0001 to 0.0122) includes the re-run (M19)
- Credibility aspect: repetitions and seeds
- Verified by: inspection of the run header and `eval_decide.py --rerun`
- Status: Draft

### TR-CONVERT-003 – Power of the equivalence rule
- Applies to: EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction, TC-WFM-110, TC-WFM-111, TC-WFM-112, TC-WFM-113, TC-WFM-114
- Requirement: REQ-WFM-110, REQ-WFM-111, REQ-WFM-112, REQ-WFM-113, REQ-WFM-114
- Group: Conversion eval runs
- Kind: setup
- Text: The check shall have a false alarm of at most 0.02 and a miss of at most 0.13 at a true loss of 0.25 right cases, computed with false_alarm.py with the re-run for the size of its suite.
- Rationale: computed on 2026-11-07: false alarm 0.0001 to 0.0122, miss 0.0171 to 0.1242 at a loss of 0.25; at a loss of 0.15 the miss is 0.36 to 0.51, so a small loss is not caught by these suites, which is why REQ-WFM-058 is the main guard
- Credibility aspect: power and false-alarm rate
- Verified by: power analysis (false_alarm.py, commands in test-spec.md, statistical checks)
- Status: Draft

### TR-CONVERT-004 – The baseline is recorded before the converted run
- Applies to: EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction, TC-WFM-110, TC-WFM-111, TC-WFM-112, TC-WFM-113, TC-WFM-114
- Requirement: REQ-WFM-110, REQ-WFM-111, REQ-WFM-112, REQ-WFM-113, REQ-WFM-114
- Group: Conversion eval runs
- Kind: setup
- Text: The check shall use as reference the run of the v0.1.0 version of the skill with 3 repeats on the same cases and the same pin, recorded before the first run of its converted version, and its minimum shall not change after a converted run was seen.
- Rationale: the minimum is the baseline rate minus the margin; four of the five baselines were measured with one repeat (summaries of 2026-10-18 and 2026-10-19), so they are re-recorded at 3 repeats first (M19)
- Credibility aspect: reference accuracy
- Verified by: inspection of the baseline files and their dates
- Status: Draft

### TR-CONVERT-005 – Dev cases are tagged and unchanged
- Applies to: EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction, TC-WFM-110, TC-WFM-111, TC-WFM-112, TC-WFM-113, TC-WFM-114
- Requirement: REQ-WFM-110, REQ-WFM-111, REQ-WFM-112, REQ-WFM-113, REQ-WFM-114
- Group: Conversion eval runs
- Kind: setup
- Text: The check shall run only cases tagged split:dev, and no case shall change between the baseline run and the converted run.
- Rationale: without the tag `eval_decide.py` selects 0 cases for split=dev and fails (checked on a synthetic run on 2026-11-07, amendment A-120); the suites are starter suites seen during prompt work, so the check shows equivalence with the old version, not quality
- Credibility aspect: validity domain
- Verified by: inspection of the case files and `agent_check.py` (A6)
- Status: Draft

### TR-CONVERT-006 – The fake model server is as faithful as the real one
- Applies to: TC-WFM-058
- Requirement: REQ-WFM-058
- Group: Conversion stand-ins
- Kind: setup
- Text: The check shall use a fake model server that passes the contract suite of the model server interface, and a fake model server shall never decide an eval criterion.
- Rationale: the check compares lists of calls, so the fake has to record prompt and options as the real client sends them; rates are decided on the real pinned model only
- Credibility aspect: stand-in fidelity
- Verified by: contract suite
- Status: Draft

### TR-CONVERT-007 – Exact values of the conversion and snapshot tests
- Applies to: TC-WFM-057, TC-WFM-059, TC-WFM-060, TC-WFM-061, TC-WFM-062, TC-WFM-063, TC-WFM-064, TC-WFM-065, TC-WFM-066, TC-WFM-069, TC-WFM-115
- Requirement: REQ-WFM-057, REQ-WFM-059, REQ-WFM-060, REQ-WFM-061, REQ-WFM-062, REQ-WFM-063, REQ-WFM-064, REQ-WFM-065, REQ-WFM-066, REQ-WFM-069, REQ-WFM-115
- Group: Conversion exact values
- Kind: unit
- Text: Each check shall compare exact expected values that are written out in its scenario in test-spec.md and can be recalculated by hand.
- Rationale: counts (8 items, 51 outputs, 17 of 20), versions and statuses are exact
- Credibility aspect: numerical settings
- Verified by: known answer
- Sign-off: skimmed as a group
- Status: Draft
