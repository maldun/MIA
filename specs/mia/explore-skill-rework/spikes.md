# Spikes of the skill rework (throwaway, not eval runs)

## Spike C: LightRAG extraction on the 12B (run 2026-11-04)
- **Setup:** `lightrag-hku` 1.5.7 in a throwaway venv (Python 3.12, outside `requirements.txt`); Ollama with `gemma4:12b-it-qat`, `num_ctx` 8192, temperature 0, thinking off (with thinking on the 12B spent its whole output budget on reasoning and returned nothing); chunks of 800 tokens, no gleaning; embeddings are deterministic hash vectors (the server answers 501 for embeddings and no embedding model is pulled), so **nothing is known about LightRAG's retrieval side**.
- **Documents:** 10 pages fetched from the web (8 Wikipedia articles capped at 12 000 characters: citation, knowledge graph, meta-analysis, ontology, peer review, prompt injection, RAG, systematic review; abstracts of the LightRAG and original RAG papers). 3 repeats each. Scripts: `spikes/lightrag/`.
- **Measured:** 30 runs, 0 errors, 37 min in all. Pages of about 12 000 characters: 70 to 130 s, 45 to 80 nodes and 23 to 67 edges; abstracts: 14 to 20 s, 8 to 12 nodes. At temperature 0 the repeats give nearly the same node counts, so repeats add little; more documents add more.
- **Observed:** several results have fewer edges than nodes (e.g. 77 nodes, 40 edges): isolated entities, to check in the marking.
- **Still open:** the quality (right, useless, wrong, invented), judged by the owner on a sample of 195 items with their source passages: `forms/spike-c-marking.html`. The bar for "good enough" is set by the owner before reading the result: **not yet set**.
- **Not compared yet:** option 1 (own builder on the runner) on the same documents. Needs the owner's marking first.
