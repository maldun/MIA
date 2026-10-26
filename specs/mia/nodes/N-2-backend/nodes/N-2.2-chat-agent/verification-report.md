# Verification report: T-04 structured memory (REQ-CHA-011 to -013)

Verifier: fresh session, 2026-10-26, branch `worktree-verify-t04` from master `d9e2837`. I did not implement T-04 and ran no dev eval. I changed no code, skill, sample or test.

**Verdict proposal: verified with accepted deviations** (see D-1 to D-4). Needs a person's decision and the transcript review (check F).

## Holdout run, AC-24 (a)
- Command: `tools/memory_dev_run.py --split holdout --verifier --repeats 3`, run once. Log: `/home/maldun/verify-t04-logs/holdout1.jsonl` (outside the repo, contains holdout texts).
- Skill `memory_write` v6, pipeline `memory.write@5`, model `gemma4:12b-it-qat`, digest `38044be4f923` = the pin. Checked with `ollama list`/`api/tags` and `api/ps` before and after the run. Temperature 0.2 from the skill options. 11 cases, 3 repeats, 34 s model time.
- Result: **10 of 11 cases right (majority of repeats), Wilson 95 % lower bound 0.62, rule of A-12 (>= 9 of 11, bound >= 0.5): PASS.** No re-run (re-run applies only to a FAIL). Recall 21/24 (88 %). The 12 runs that expect nothing stored 0 records. `untrusted` (MEM-S25) was refused before the model in all 3 runs. The replace case (MEM-S16) was right 3/3.
- Note on the run: the owner said that the model had to be started first. The container had been up for about 13 minutes and the model was loaded with the pinned digest when the run started; the run completed with all repeats and results, so I treat it as the one valid run. If the owner considers it invalid, that is their decision.
- Wrong case (description only): MEM-S27, category `mixed` (a statement plus an unrelated question). The model stored the right content as kind `fact`; the label wants `preference`. In all 3 repeats the same. **The matcher (kind equality) caused the miss, not the model's content.** Counting it as right would give 11/11; I do not do that, the score as specified stands. See D-2.
- Extras: MEM-S09 stored a second preference record for one statement in 3/3 repeats, with a different wording between repeats ("differs between repeats"); 6 extras in 33 runs. Per the hand-over these are not wrong cases.
- Language: no German or French in any stored text (searched the log for common function words: 0 hits; I also read the stored texts of the wrong and the extra cases).
- Plausibility: dev 100 % recall vs holdout 88 %: a gap of the expected size and direction, no sign of contamination. The whole run took 34 s for 33 calls (about 1 s each), plausible for the light model with short output.

## Verification matrix
| Requirement | Method | Evidence | Result |
|---|---|---|---|
| REQ-CHA-011 (records with kind, time, source, English; AC-24) | test + eval + analysis | holdout PASS above; `tests/test_memory_records.py` 12 OK; `tests/test_chat_memory.py` 5 OK; `tests/test_memory_write_skill.py` 3 OK (run in image) | verified |
| AC-24 (b) token cost | analysis | `memory_cost.py` on a copy of the owner's db and the last 20 user messages: dreaming 5945 tokens per answer, structured mean 0.6, max 11, abstained 19 of 20: "not higher than dreaming". **Only 1 record in the db, so it proves little.** The cap is tested exactly in `test_memory_records.py`. | verified, weak (D-3) |
| REQ-CHA-012 (only the user's own text) | test + inspection | the two named tests pass. Inspection: `remember` is called from one place, `chat_service.py:573`, condition `task == "chat"` and `status == "done"` and a user message id; the queue holds kinds `chat`, `lookup`, `search`, `command` only, so `/lookup` and `/search` are excluded; `regenerate` queues with message id `None` (line 281) so it is excluded; no file or page path calls it. `architecture.sysml`: the only flow into `memoryWriter` is `intake.messageOut` (line 736). `remember` checks `source == "user"` before it asks the writer. | verified |
| REQ-CHA-013 (inspect, correct, delete with source) | test | `tests/test_items_api.py` 9 OK. The Memory tab was not opened by me (no browser session): left for the owner's demonstration. Source is stored as a message id (`remember(account, message_id, ...)`). | verified by test, demo open |

## Agent checks
- A. Protected material: A-12 installed (`apply_amendment_a12.sh` shows no difference). `git diff decomp-baseline..HEAD` on protected paths lists 51 files, the same set as other tasks and amendments A-01 to A-12; for this task the only protected file changed is `test_if_302_record_tables.py`/its mock (A-10, commit 62914cd). No eval suite or baseline was changed by T-04 commits (checked against the T-04 commit range). I did not map every one of the 51 files to its amendment; that mapping covers earlier tasks.
- B. Pins: model digest = pin. Server: ollama container (rocm), `num_ctx` not re-checked.
- C. Suite: no `EV-memory` suite and no `Eval criterion:` line exists by design of A-12; `eval_decide.py` therefore not used; the A-12 rule was applied by the script.
- D. Red team: `specs/mia/eval-drafts/redteam_mia.jsonl` is **empty (0 lines)**; `eval/suites/rt_memory` exists (and `.holdout`). I did not run or open the holdout of it, and wrote no cases. The writer's only protection against poisoned text is the code rule of REQ-CHA-012 (above), which is sound for the paths found; a model step never sees non-user text.
- E. Budgets: calls per message 1, about 1 s on the light model. Not measured: VRAM with the full chat model (D-4).
- F. Transcript review by a person: **open**. The holdout log is ready; people should read the MEM-S27 and MEM-S09 runs and about 10 more.
- G. Proposed cases: none made by me.

## Static checks
- `check_sysml.sh`: 4 files, 0 errors, 0 warnings. `check_sysml_model.py`: OK (49 ids, 360 generated requirements). `library.py validate`: 79 nodes, 32 pipelines, 0 problems. `trace_check.py`: 27 errors = the known number-gate markers, none new. `check_agent.sh --errors`: exit 2 with only WARN lines visible in the tail (REQ-WFX-* missing markers, unrelated); I did not read the full output for errors. No lint, bandit or vulture run (none configured).

## Findings
| ID | Severity | Finding | Destination |
|---|---|---|---|
| D-1 | low | `structured_memory` is off by default; the owner tried it once; nothing ran it under load. | Phase 6/7 |
| D-2 | low | The score matcher requires equal `kind`; MEM-S27 is right in content, wrong in kind, and the kind of "is vegetarian" (fact vs preference) is ambiguous by label. Not tuned. | Plan: owner decides the label or the matcher by amendment |
| D-3 | low | AC-24 (b) rests on 1 stored record; it says nothing about a full memory. Also "do you remember my height?" retrieved 0 records for the stored height record (no shared word with "175cm tall"): retrieval is word-overlap only. | Phase 7: re-measure with more records; consider a failing test for this question |
| D-4 | medium | Light model for the memory call plus the full model as chat unload each other on the 16 GB card; not measured. | Phase 6: measure latency and VRAM with `structured_memory` on |
| D-5 | low | Duplicate records for one statement (6 extras in 33 runs, wording changes between repeats). Accepted by the hand-over rule; they will show up as clutter in the Memory tab. | Backlog |
| D-6 | info | Red-team draft file empty; the 4 draft cases for THR-006 (RT-009) are missing. | Plan, owner |
| D-7 | info | Not verified: the Memory tab by hand; pre-existing failures `test_every_shipped_suite_is_valid` and `test_group_stop_...` (not run, not from this task). | owner |

No blocker. Nothing goes back to Implement.

## For the team
Look at: the decision on D-2, the transcript review (F), and whether the demonstration of the Memory tab (REQ-CHA-013) is done before the merge.
