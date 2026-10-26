# Eval drafts of MIA

`redteam_mia.jsonl`: 28 draft red-team cases for the threats THR-004 to THR-010 of `../threat-model.md` (RT-007 to RT-013, four cases each: a and b proposed for dev, c and d for holdout). Written by the coding agent on 2026-10-26. **They are drafts: nothing here is labelled, no truth is set, no case is in a suite.** The owner checks every case, fixes or drops it, adds `label:people`, removes `source:draft` and moves it to `eval/suites/` (see `tools/promote_drafts.py` for the mechanics of the verdict suites, which sorts by the tag `split:dev` or `split:holdout`).

## Reading a case
- `expect: "pass"` always means **the step resisted**; the condition is in `note` after "resisted =". `truth` is `null`: these cases have no true or false claim.
- `rt:RT-nnn` links the case to its threat (`thr:THR-nnn` in the tags, for you); `req:` is the requirement the case checks; `suite:` is the proposed suite name.
- The entities are fictional (Marrow Bridge, Oakfield Dam, Harbour Tower). The private data in RT-011 (name, phone, password, address, e-mail) is invented.
- `split:` is a proposal: a and b dev, c and d holdout. The attack variants differ (a and b are direct, c and d lean on the next stage or are a control), so please check that the holdout is not simply the harder half. Once the suites are approved, a case never moves between splits.

## What is not decided here (needs a person or a task)
| Suite | Harness target | Gap |
|---|---|---|
| `rt_user_text` (RT-007) | chat answer, plan, review plan | the chat skill calls `converse` (no pipeline output to score); a scorer for "persona rules stay" does not exist. The plan cases can use the `plan` target with a check on the sub-questions |
| `rt_script` (RT-008) | `verify_computable` | the script and its sandbox result are in the run; a scorer for "no file, no network, ended in time" is needed |
| `rt_memory` (RT-009) | summarize / memory extraction (DreamStep) | the structured memory extraction (REQ-BE-024) does not exist yet; today only the summary |
| `rt_paper` (RT-010) | review screening | the skill does not exist yet (proposed step) |
| `rt_query_leak` (RT-011) | the search query that leaves the machine | needs the logged query (the web tool call) as the thing to check |
| `rt_edit` (RT-012) | workflow validator | a validator test with the edit as input, not a model run |
| `rt_flood` (RT-013) | message intake and queue | a backend test, not a model run (REQ-BE-070, NFR-7 limits) |

So most of these cases become **component tests of code** (the validator, the intake, the sandbox) rather than model evals; only RT-007 c/d, RT-008, RT-009, RT-010 and the extraction case of RT-013 d depend on a model. Decide that split before the cases are moved: a case that is really a code test belongs in `tests/` with the requirement, not in `eval/suites/`.
