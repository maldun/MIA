# Spikes of the skill rework (throwaway, not eval runs)

## Spike C: LightRAG extraction on the 12B (run 2026-11-04)
- **Setup:** `lightrag-hku` 1.5.7 in a throwaway venv (Python 3.12, outside `requirements.txt`); Ollama with `gemma4:12b-it-qat`, `num_ctx` 8192, temperature 0, thinking off (with thinking on the 12B spent its whole output budget on reasoning and returned nothing); chunks of 800 tokens, no gleaning; embeddings are deterministic hash vectors (the server answers 501 for embeddings and no embedding model is pulled), so **nothing is known about LightRAG's retrieval side**.
- **Documents:** 10 pages fetched from the web (8 Wikipedia articles capped at 12 000 characters: citation, knowledge graph, meta-analysis, ontology, peer review, prompt injection, RAG, systematic review; abstracts of the LightRAG and original RAG papers). 3 repeats each. Scripts: `spikes/lightrag/`.
- **Measured:** 30 runs, 0 errors, 37 min in all. Pages of about 12 000 characters: 70 to 130 s, 45 to 80 nodes and 23 to 67 edges; abstracts: 14 to 20 s, 8 to 12 nodes. At temperature 0 the repeats give nearly the same node counts, so repeats add little; more documents add more.
- **Observed:** several results have fewer edges than nodes (e.g. 77 nodes, 40 edges): isolated entities, to check in the marking.
- **Still open:** the quality (right, useless, wrong, invented), judged by the owner on a sample of 195 items with their source passages: `forms/spike-c-marking.html`. The bar for "good enough" was set by the owner before reading the result (below).
- **Not compared yet:** option 1 (own builder on the runner) on the same documents. Needs the owner's marking first.

**Bar for spike C (owner, 2026-11-05, set before the marking):** at least 68 % of the marked items *right* (one sigma) and at most 5 % *invented*. Agent's reading, to confirm: the shares are of all marked items; "right but useless" and "wrong" do not count as right and are reported on their own; the missing-items note per document is reported but does not decide. Option 1 is run on the same documents against the same bar after the marking.

## Spike C, first opinion and hard checks (2026-11-05)
- **Agent's blind labels** (not truth labels, `spikes/lightrag/judge-claude.json`, made before the owner's marking, read against the full documents): 168 right (86.2 %), 22 right but useless (11.3 %), 3 wrong (1.5 %), 2 invented (1.0 %). Errors: a name cut from "PRIMSA flow diagram" (2 items), two edges inferred, not stated (Boolean operators with PubMed and Embase), one reversed edge (Bluebook). Useless items are mostly generic nouns, example details and duplicates.
- **Chunker finding:** LightRAG cuts chunks at token borders, mid-word: "PRIMSA" was split into "PRIM" and "SA flow diagram", so a check against the *chunk* passes the mangled name. Our own builder must chunk at sentence or paragraph borders and check against the whole document.
- **Hard checks** (`spikes/lightrag/checks.py`, test `test_checks.py`, measurement `measure_checks.py`; the plural handling was added after the first measurement showed two false flags from plurals, so the numbers below are for the corrected check, tuned on a failing unit test and not on the labels):

| Check | Flagged of 195 | Catches of the 5 wrong/invented | False flags on 168 "right" |
|---|---|---|---|
| A: name or both ends in the source chunk | 2 | 0 | 0 |
| B: relation ends within 300 characters in the chunk | 17 | 0 | 14 |
| C: as B, against the whole document | 18 | 2 | 14 |
| **D: every name occurs in the whole document (no distance rule)** | **3** | **2** | **0** |

  Over all 818 items of repeat 1, check D flags 9 of 494 entities (1.8 %) and 9 of 324 relations (2.8 %). The distance rule (B, C) flags correct relations that span sentences and is not worth it. D is cheap and has no false flags here, but it **cannot** catch a reversed or inferred relation (I015, I057, I059): those need the source quote of the relation plus a judge (model) that asks whether the quote states the relation, calibrated against the owner.
- **Reading:** on the agent's labels LightRAG on the 12B clears the owner's bar by a wide margin on right and invented. This is an opinion until the owner's marks exist; the agreement of the two sets decides whether a model can serve as a judge (kappa >= 0.6).
