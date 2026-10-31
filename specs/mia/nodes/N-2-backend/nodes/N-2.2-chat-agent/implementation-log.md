# Implementation log: N-2.2 Chat agent

Only the parts that the earlier jobs did not log elsewhere (they are in `specs/mia/review-log.md`, D-45 to D-81, and `specs/mia/HANDOVER.md`).

## T-04 Structured memory: eval runs of the skill `memory_write` (dev split only)

Feedback for the implementer, **not a verification and not a decision**. The criterion AC-24 has no formal eval line yet (it comes with the reworded REQ-CHA-011), so there is no `eval_decide.py` table, no baseline and no decision rule; the numbers below are a rough count by `tools/memory_dev_run.py`.

- Cases: the 20 cases with `split: dev` of `specs/mia/eval-drafts/memory_sample.jsonl` (labels: all `ok`, the owner, 2026-10-27). Holdout lines are skipped before they are parsed; none was read.
- Model: skill profile `light` = `gemma4:12b-it-qat`, digest `38044be4f923`, `num_ctx` 8192, Ollama defaults for the rest (temperature 1, top_p 0.95, top_k 64). Three repeats (no `eval-spec.md` exists for `specs/mia`; 3 is the usual number of the suites).
- Scoring: a stored record matches an expected one when the kind is equal and at least half of the expected words occur in it. **The matcher is English-only**, so a record in another language counts as "extra" and as a miss: it measures the language problem below as much as the memory. Update cases are seeded with the record they replace.
- Cases 24 and 26 (web and file text) are refused in code before the model is asked (6 runs, no model call).

| Run | Skill / pipeline / node | Change | Recall | Extra records | Stored in the 18 runs that expect nothing | Replaced right | Model seconds | Log |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 / `memory.write@1` / `view.memory_write@1` | starting point | 15/48 (31 %) | 33 | 0 | 2/3 | 62 | `eval-drafts/runs/memory_write_v1_dev_1.jsonl` |
| 2 | 2 / `@2` / `@2` | the records "in the same language as the message, never translate" | 7/48 (15 %) | 43 | 0 | 2/3 | 66 | `memory_write_v2_dev_1.jsonl` |
| 3 | 3 / `@3` / `@3` | "a short phrase without a subject" instead of "third person" | 26/48 (54 %) | 30 | 0 | 2/3 | 59 | `memory_write_v3_dev_1.jsonl` |

| 4 | 4 / `@4` / `@4` | **owner 2026-10-27: records are always English**, translate | 44/48 (92 %) | 12 | 0 | 2/3 | 63 | `memory_write_v4_dev_1.jsonl` |
| 5 | 5 / `@4` / `@4` | **owner: lower temperature**: `options: {temperature: 0.2}` in the skill file (merged over the profile's `num_ctx`) | 45/48 (94 %) | 13 | 0 | 2/3 | 62 | `memory_write_v5_dev_1.jsonl` |
| 6 | 6 / `@5` / `@5` | a correction is recorded even when no known record matches | 45/48 (94 %) | 12 | 0 | 3/3 | 62 | `memory_write_v6_dev_1.jsonl` |
| 7 | 6 / `@5` / `@5` | **code, not prompt:** `MemoryRecords.add` keeps a record whose `replaces` is unknown (the model wrote `"replaces": "1"` for MEM-S17 and the store dropped the whole record) | 48/48 (100 %) | 13 | 0 | 3/3 | 63 | `memory_write_v6_dev_2.jsonl` |

(The first line of the v2 log says v1: the script printed a fixed "v1" until run 3; the file name is right.)

What the transcripts show (read for every case that missed or added something):
- **The records come out in a foreign language.** v1 wrote French ("L'utilisateur habite à Graz."), v2 German ("Der Nutzer lebt in Graz."), v3 mostly German phrases ("lebt in Graz") for English messages; the language even changes between repeats. The instruction about the language of the message did not hold on this model; removing the third person helped the *content* (more hits) but not the language.
- **Nothing is stored where nothing should be:** the 18 runs of the cases `none`, `hypothetical`, `untrusted` and `sensitive` stored no record in any of the three versions (the untrusted ones never reach the model).
- **Misses that are not language:** MEM-S17 (a correction without a known record: "Correction: the dog is called Bruno, not Bruni") stored nothing in all three versions; MEM-S06/S08 (two statements in one) are split or reworded; extras such as "schedule the meeting late" as a preference (MEM-S29) and "no recipes with peanuts" as a preference next to the allergy (MEM-S03) are arguable: the owner labelled only the fact.
- **Instability:** most cases differ between repeats (sampling temperature 1).

**Stop condition after run 3** (the same weakness, the language of the records, after three variants). **Resolved by the owner's decisions of 2026-10-27** (always English; lower temperature; the language cases added): runs 4 to 7. **Not done, needs the owner:** (a) the fix is probably not in the prompt of this skill but in the model options (a lower temperature, or `think`), or in what the owner wants (records in the language of the message, or always English as a fixed storage language that the answer step translates): a model option or a storage-language rule is the owner's decision; (b) a language-aware matcher for the score, or a decision that records are written in English, then the count above means what it says; (c) a labelled case for "the language of a record equals the language of the message" (proposed, not in a suite: message "I have to renew my licence next month." must give a record in English; message "Ich muss nächsten Monat meinen Führerschein erneuern." must give one in German).

## After the decisions of 2026-10-27 (runs 4 to 7)

- The English rule fixed the language at once (recall 31 % -> 92 %); the temperature 0.2 made the repeats stable (only 2 of 20 cases still differ between repeats; before: most). The temperature is set by the skill file (`options`), the profile `light` and the model digest are unchanged.
- The one miss left, MEM-S17 (a correction with nothing known to replace), was a **bug in the store, not in the prompt**: found by asking the model once for the raw answer of that dev case (`{"kind": "fact", "text": "dog is called Bruno", "replaces": "1"}`); `add` dropped records with an unknown `replaces`. Test first (`tests/test_memory_records.py`), then the fix in `memory_records.py`.
- **The 100 % is feedback on the cases the prompt was tuned against (20 dev cases, 7 runs), not evidence.** Only the holdout in Verify decides.
- Extras (13 records in 60 runs, the same cases each time): one statement stored as two records (a fact and a derived preference: S03 allergy and "no recipes with peanuts"; S07 "be called Steffi" and "not be called master"; S08 "likes jazz" and "never listens to metal"; S29 "Tom hates mornings" and "schedule meetings late"). The owner's labels name one record each; whether the second is wrong is a labelling question (the proposals are `ok`, so as labelled these count as extra).
- Cost: about 62 model seconds for 51 calls, so about 1.2 s a call on the light model.
- Cases added by the agent as proposals, **not labelled, no split** (the owner decides; `tools/set_memory_split.py` now leaves unlabelled cases alone): MEM-S31 (a German commitment must give an English record) and MEM-S32 (German facts must give English records). Not run.

## Wiring and run 8 (2026-10-27)

- The owner labelled the two language cases: MEM-S31 `ok`, split `dev`; MEM-S32 `ok`, split `holdout` (not read). The dev split has 21 cases, the holdout 11.
- Run 8: skill 6 (`memory.write@5`), 21 dev cases, 3 repeats, same model and digest: recall 51/51 (100 %), 11 extra records, 0 stored in the 18 runs that expect nothing, replacements 3/3, 68 model seconds; MEM-S31 (a German commitment) gives an English record in 3 of 3 repeats (the wording differs). Log: `eval-drafts/runs/memory_write_v6_dev_3.jsonl`. The script read the owner's file in the main checkout (`--sample`).
- Still feedback on tuned cases, not evidence.

## Run 9 (2026-10-27, before the hand-over to Verify)

Skill 6 unchanged, 21 dev cases, 3 repeats, same model and digest, with the new per-case measure of the script (a case is right when the majority of its repeats stored every wanted record and, where nothing was wanted, nothing): **21 of 21 cases right, Wilson 95 % lower bound 0.85**; recall 51/51, 12 extra records, 0 stored in the 18 runs that expect nothing, 68 model seconds (`eval-drafts/runs/memory_write_v6_dev_4.jsonl`). Feedback on tuned cases only. The decision run on the holdout is for the independent verifier: `specs/mia/verify-handover-t04.md`.

## Note (2026-10-31, D-137)
REQ-CHV-006 of N-1.2 (shocked expression and line after a minus) is built together with the votes of this node: a `shocked` preset (N-1.2) and the shocked line sent by the backend.

## Session 2026-10-31 (evening, fresh context, branch `v1-n22` from goal/v1 `ee64d7d`)

Starting point: every test that names an id of this node (24 files, incl. the contract suites IF-101, IF-201, IF-302) and `test_chat_backend.py`, `test_chat_tasks.py`, `test_behaviour.py`, `test_record_tables.py` ran green in the image before any change. Skips: IF-201 (expression and audio of an answer: N-2.5; `stop` before the answer started: T-01), IF-101 (the same two and the variant event: REQ-CHV-008, out of G-V1).

| Task | State | Commit | Tests reported green (feedback, not verification) |
|---|---|---|---|
| T-01 | done before except the stop of an answer that has not started: **done now** | see below | `test_chat_backend.py` 42 OK (new: `test_stop_before_the_answer_starts`, red first: a chat_delta came after the stop) |

### T-01 rest: stop before the answer starts (REQ-CHA-004, TC-CHA-004, TC-IF-201-04, TC-IF-101-06)
- Finding (test first): a `stop` between `send` and the moment the worker takes the message returned True but was lost: `_work` cleared the stop flag when it took the message, and the answer ran in full. Test: `tests/test_chat_backend.py::ServiceTest::test_stop_before_the_answer_starts`.
- Fix (`chat_service.py`): `stop()` looks at the running item or, before the worker took one, the head of the queue (a command is still not stoppable); a stop before the first item sets `_stop_next`, which keeps the flag when the worker takes it; `_do_chat` does not ask the model when the stop is already set (chat_done `stopped`, text empty, logged). The next message is answered as usual (same test).
- **Shared code with N-1.3:** this touches `ChatService.stop` and `_work` (the stop path that the N-1.3 agent on `v1-n13d` may also touch); the change is 10 lines, a merge conflict there is resolved by keeping both.
- **A-56 (draft):** the real sides of TC-IF-201-04 and TC-IF-101-06 skip in the protected adapters of `tests/helpers/contract.py`. Note `specs/mia/amendments/A-56/A-56-note.md`, script `tools/apply_amendment_a56.sh` (builds the change from the installed file at install time). Scratch check (copy of HEAD in the job scratch folder, `--do`): with the old `chat_service.py` both suites red (1 failure each: the stop), with the new one IF-201 16 OK (1 skip: N-2.5), IF-101 60 OK (2 skips: N-2.5, REQ-CHV-008); a second run reports the file unchanged.
