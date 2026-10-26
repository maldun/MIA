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

(The first line of the v2 log says v1: the script printed a fixed "v1" until run 3; the file name is right.)

What the transcripts show (read for every case that missed or added something):
- **The records come out in a foreign language.** v1 wrote French ("L'utilisateur habite à Graz."), v2 German ("Der Nutzer lebt in Graz."), v3 mostly German phrases ("lebt in Graz") for English messages; the language even changes between repeats. The instruction about the language of the message did not hold on this model; removing the third person helped the *content* (more hits) but not the language.
- **Nothing is stored where nothing should be:** the 18 runs of the cases `none`, `hypothetical`, `untrusted` and `sensitive` stored no record in any of the three versions (the untrusted ones never reach the model).
- **Misses that are not language:** MEM-S17 (a correction without a known record: "Correction: the dog is called Bruno, not Bruni") stored nothing in all three versions; MEM-S06/S08 (two statements in one) are split or reworded; extras such as "schedule the meeting late" as a preference (MEM-S29) and "no recipes with peanuts" as a preference next to the allergy (MEM-S03) are arguable: the owner labelled only the fact.
- **Instability:** most cases differ between repeats (sampling temperature 1).

Stop condition reached: the same weakness (language of the records) after three variants. **Not done, needs the owner:** (a) the fix is probably not in the prompt of this skill but in the model options (a lower temperature, or `think`), or in what the owner wants (records in the language of the message, or always English as a fixed storage language that the answer step translates): a model option or a storage-language rule is the owner's decision; (b) a language-aware matcher for the score, or a decision that records are written in English, then the count above means what it says; (c) a labelled case for "the language of a record equals the language of the message" (proposed, not in a suite: message "I have to renew my licence next month." must give a record in English; message "Ich muss nächsten Monat meinen Führerschein erneuern." must give one in German).
