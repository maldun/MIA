# T-04 structured memory (REQ-CHA-011 to -013): design from literature, draft for the owner (2026-10-27)

Status: **draft, nothing built**. Owner decision 2026-10-27: evidence from the literature instead of a large labelled test set, plus a small sample of 30 cases that the owner checks (`memory_sample.jsonl`, same folder). Nothing here changes a requirement yet; the proposed rewording of REQ-CHA-011 at the end becomes an amendment after approval.

## What the literature gives (checked by search on 2026-10-27; claims I could not check are marked)
| Source | What it supports for MIA |
|---|---|
| Packer et al., *MemGPT: Towards LLMs as Operating Systems*, arXiv:2310.08560 (2023) | Tiers: a small working context plus an external store the agent pages in and out; evaluated on multi-session chat. Supports: the prompt holds only a retrieved slice, the store is outside it. |
| Park et al., *Generative Agents*, arXiv:2304.03442 (2023) | A memory stream of natural-language records with creation time and last access; retrieval scores **relevance, recency and importance**. Supports: records carry a time, retrieval ranks by more than similarity. (The decay rate 0.99 and equal weights come from a blog about an implementation, not the paper: do not copy them without reading the paper.) |
| Chhikara et al., *Mem0*, arXiv:2504.19413 (ECAI 2025) | Extracting short facts from conversation and retrieving them instead of the full history: the abstract reports 91 % lower p95 latency and more than 90 % lower token cost than full context, and a better LLM-judge score than an OpenAI baseline on LoCoMo. Later vendor figures (92.5 on LoCoMo, about 7 k tokens per call) are marketing, not from the paper, and not independent. Supports: a fact store costs fewer tokens than replaying history. |
| Wu et al., *LongMemEval*, arXiv:2410.10813 (NeurIPS 2024, ICLR 2025) | Five abilities to test: information extraction, multi-session reasoning, temporal reasoning, **knowledge updates**, **abstention**. Commercial assistants and long-context models lost about 30 % accuracy over sustained interaction. Optimisations that helped: session decomposition, **fact-augmented keys**, **time-aware query expansion**. Supports: the categories of the 30-case sample, and storing facts with a time. |

What the literature does **not** give: a number for a 12B local model with a 8192-token context on MIA's own chats. That is why the sample and a token measurement remain.

## Design (mine, to be approved)
- **Record** in the `memory` table (IF-302 v2, an amendment): `text`, `kind` (`fact`, `preference`, `commitment`), `source` (a chat message id, or `owner` for a record typed on the page; never a url of web or file text: REQ-CHA-012), `subject` (the account the record is about), `created`, `updated` (time-aware retrieval and knowledge updates, LongMemEval), `status` (`active` or `replaced`; a correction keeps the old version in the history of the table, so it stays inspectable: REQ-CHA-013).
- **Writer**: one model step after an answer, input = the user's own message(s) only, output = a list of `{kind, text}` or none. Text from `/lookup`, `/search`, files or pages is never an input of this step (a structural rule, tested exactly: AC-6).
- **Retrieval**: score = relevance (word overlap first; embeddings would be a new part and need approval) + recency + kind weight, then the best records up to a token budget (`memory_budget_tokens`, default 400 of the 8192). Commitments with a `due` are the tasks (A-09), not memory.
- **Abstention** (LongMemEval): when nothing scores above a threshold, the model gets no memory block rather than a poor one.

## Measurement without a big test set
1. **Cost**: tokens of the memory block per answer, today's dreaming versus the retrieval slice, over the same 20 real chats of the owner (no labels needed). Criterion: not higher than dreaming.
2. **Quality**: the 30-case sample in `memory_sample.jsonl`, with the owner's labels. Two numbers: the writer's recall of the labelled records and its false-memory rate (a memory the owner marks as wrong or forbidden, for example from web text, must be 0 in the exact cases). With n = 30 the result is a **feedback figure, not a statistical proof**: it can show a clear failure, not a small difference to dreaming; the sample says so in the report.
3. **Structure**: the exact tests (REQ-CHA-012 no record from web text; REQ-CHA-013 inspect, correct, delete with source) stay as they are.

## Proposed rewording of REQ-CHA-011 (not applied)
Text: *The Chat agent shall keep facts, preferences and commitments as records with a kind, a time and a source, and give the model the most relevant records within a token budget.*
Acceptance criterion: *AC-24: on 20 recorded chats the memory block costs no more tokens than today's dreaming; on the checked sample of 30 cases the writer finds the labelled records and stores none of the forbidden ones; the design follows the cited literature (this document).* Verification: Measurement. Changing it is a requirement amendment (owner).

## Open for the owner
1. Approve the design and the rewording (then A-10: IF-302 v2 for the `memory` fields, test first).
2. Check the 30 cases: delete or fix what is wrong, set `label`, and say which cases are the dev part (I do not split them).
3. Word overlap versus embeddings for retrieval (embeddings = a new part).
