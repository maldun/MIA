# Verification report: T-04 structured memory (REQ-CHA-011 to -013)

Verifier: fresh session, 2026-10-26, branch `worktree-verify-t04` from master `d9e2837`. I did not implement T-04 and ran no dev eval. I changed no code, skill, sample or test.

**Verdict: proposal "verified with accepted deviations" (see the closing session below); open until the owner has done the transcript review and the Memory tab demonstration. Earlier status: postponed by the owner (2026-10-26) until there is data from trial runs; the field test is the Phase 7 validation run, so that data comes after this verification.** Evidence so far would support "verified with accepted deviations" (see D-1 to D-5), but the owner decided not to close the verification now. The holdout was run once and stays as recorded; it is not re-run, and the owner's remark that the model had to be started first is noted below. Open before closing: the trial-run data (D-3, D-4), the transcript review (check F) and the Memory tab demonstration.

## Closing session, 2026-10-26 (late), fresh verifier, branch `worktree-verify-t04-close` from local master `f007fd3`
Holdout not opened, nothing tuned, no code, skill, sample or test changed. Measurements ran on copies in the job tmp folder.

**There is no field-test data yet.** The owner clarified: the field test is the first validation run (Phase 7) after everything is implemented, and its data is collected with the first version. The only use of `structured_memory` so far is the owner's single try (option switched on 22:51, last chat 22:53, shutdown). So the items "AC-24 (b) with more records" and "wrong or duplicate records over days" cannot be closed now. What was done is a **preliminary snapshot**:

- **Token cost (`tools/memory_cost.py`, copy of `data/db` and `memories.json`, last 20 user messages of the chat log):** dreaming 5945 tokens per answer, structured mean 0.6, max 11, abstained 19 of 20, "not higher than dreaming". Identical to the first measurement: the store still holds the same 1 record. Weak evidence for the same reason (D-3).
- **Stored records:** 1 record (`175cm tall`, kind `fact`, subject `master`, status `active`, source = the id of the user message "High MIA, I am 175cm tall", checked in the chat log). Correct, English, source traceable (REQ-CHA-011, -012). 0 wrong, 0 duplicate records. No statement on D-5 can be made from one record.
- **Retrieval (D-3) unchanged:** "do you remember my height?" retrieves 0 records; MIA still answered correctly, but from the dreaming history, not from the structured store.
- **Latency of the light memory call** (direct Ollama chat, skill `memory_write` v6 as system text, `think=false` as in `pipeline_model.py`, `num_ctx` 8192, temperature 0.2, 7 calls of one run, warm model): 0.8 s and 1.8 s wall (26 to 87 output tokens). Consistent with the 1.2 s per call of the dev and holdout runs. A first try with thinking on took 4 to 12 s and 200 to 530 tokens; the app does not use that mode for this call.
- **Models and VRAM, 16 GB card (`mem_info_vram_used`):** `gemma4:12b-it-qat` alone 9.7 GB used of 17.2 GB (desktop included, about 2 GB); with `gemma4:26b` loaded 17.08 GB used, so the full model fills the card. **The two models do not stay loaded together**: after every call of the other model `api/ps` listed only one. Cost of a switch: light after full 4.3 and 6.7 s wall (load 3.7 and 5.1 s); full after light 37 s and 63 s wall with 12.5 and 13.2 s load (the 26b cold from disk took 137 s the first time). A full chat answer with thinking (model default, `think` not set in `setup_cfg.json`) took 21 to 47 s of generation for 221 to 1252 tokens. `api/ps` reports 1.2 GiB for the 26b, which does not fit the sysfs number; I trust sysfs and mark `api/ps` as unreliable for this model.
- **Meaning for D-4:** with `structured_memory` on, every chat message that gets a memory call after a full-model answer costs one model swap in each direction when the light model is not the chat model: about 4 to 7 s for the light reload plus about 13 s for the full reload (both numbers only when the 26b is the chat model). With the light model as chat model (the default after the "default light model" change) there is no swap. This is a single run on a host where another model (`xentriom/gemma-4-12B-coder...`, 7.6 GB) was resident at the start and was evicted by the first call; the numbers are indications, not a benchmark (no repeats, no median).

**Still missing for the verdict (owner):**
1. Transcript review (check F) of the holdout log: MEM-S09, MEM-S27 and about 10 more (the log is at `/home/maldun/verify-t04-logs/holdout1.jsonl`).
2. Memory tab demonstration (REQ-CHA-013): list, correct, delete one record, source visible.
3. Field-test data (Phase 7): AC-24 (b) with a filled store, duplicate and wrong records, latency and VRAM with the real chat model (repeats and median), D-3 decision.
4. Last: red-team cases RT-009 (D-6), a separate session.

**Proposed verdict: verified with accepted deviations**, once items 1 and 2 are done. Deviations to accept: D-1, D-3, D-4 and D-5 move to the field test (Phase 7) with the evidence above as the starting point; D-2 is closed (relabel recorded); D-6 and the security work come last. If the transcript review finds a right-for-the-wrong-reason case, the verdict goes back to the owner.

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
| D-2 | low (closed 2026-10-26: owner relabelled MEM-S27 to `fact` after the run; the recorded score stays 10 of 11, the same log would score 11 of 11 with the new label; not re-run) | The score matcher requires equal `kind`; MEM-S27 is right in content, wrong in kind, and the kind of "is vegetarian" (fact vs preference) is ambiguous by label. Not tuned. | Plan: owner decides the label or the matcher by amendment |
| D-3 | low | AC-24 (b) rests on 1 stored record; it says nothing about a full memory. Also "do you remember my height?" retrieved 0 records for the stored height record (no shared word with "175cm tall"): retrieval is word-overlap only. | Phase 7: re-measure with more records; consider a failing test for this question |
| D-4 | medium | Light model for the memory call plus the full model as chat unload each other on the 16 GB card. Measured once (closing session): confirmed, a switch costs about 4 to 7 s (light) and about 13 s (full); no swap when the light model is also the chat model. | Phase 7 field test: repeats and median with the real chat model |
| D-5 | low | Duplicate records for one statement (6 extras in 33 runs, wording changes between repeats). Accepted by the hand-over rule; they will show up as clutter in the Memory tab. | Backlog |
| D-6 | info | Red-team draft file empty; the 4 draft cases for THR-006 (RT-009) are missing. | Plan, owner |
| D-7 | info | Not verified: the Memory tab by hand; pre-existing failures `test_every_shipped_suite_is_valid` and `test_group_stop_...` (not run, not from this task). | owner |

No blocker. Nothing goes back to Implement.

## For the team
Look at: the decision on D-2, the transcript review (F), and whether the demonstration of the Memory tab (REQ-CHA-013) is done before the merge.
