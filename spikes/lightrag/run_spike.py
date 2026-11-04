"""Throwaway spike C: LightRAG extraction on the 12B at num_ctx 8192. Not an eval run.
usage: run_spike.py OUTDIR REPEAT FILE...
writes OUTDIR/rep<N>/<doc>/ (LightRAG working dir with the graph) and OUTDIR/summary.jsonl"""
import asyncio, json, sys, time
from pathlib import Path
import numpy as np, ollama, networkx as nx
from lightrag import LightRAG
from lightrag.llm.ollama import ollama_model_complete
from lightrag.utils import EmbeddingFunc

HOST, MODEL, CTX = "http://127.0.0.1:11434", "gemma4:12b-it-qat", 8192
client = ollama.AsyncClient(host=HOST)


async def embed(texts):
    # no embedding model is pulled and the server answers 501 for the 12B: a deterministic
    # hash vector keeps LightRAG running; retrieval quality is not under test, extraction is
    import hashlib
    out = []
    for t in texts:
        rng = np.random.default_rng(int(hashlib.sha256(t.encode()).hexdigest()[:8], 16))
        out.append(rng.standard_normal(64))
    return np.array(out)


async def one(doc: Path, work: Path):
    work.mkdir(parents=True, exist_ok=True)
    rag = LightRAG(
        working_dir=str(work), llm_model_func=ollama_model_complete, llm_model_name=MODEL,
        llm_model_kwargs={"host": HOST, "options": {"num_ctx": CTX, "temperature": 0}, "think": False},
        embedding_func=EmbeddingFunc(embedding_dim=64, max_token_size=CTX, func=embed),
        chunk_token_size=800, chunk_overlap_token_size=80, entity_extract_max_gleaning=0,
        llm_model_max_async=1, default_llm_timeout=600)
    await rag.initialize_storages()
    t = time.time()
    err = None
    try:
        await rag.ainsert(doc.read_text())
    except Exception as e:
        err = repr(e)[:300]
    sec = time.time() - t
    g = work / "graph_chunk_entity_relation.graphml"
    nodes = edges = 0
    if g.exists():
        G = nx.read_graphml(g)
        nodes, edges = G.number_of_nodes(), G.number_of_edges()
    await rag.finalize_storages()
    return dict(doc=doc.name, seconds=round(sec, 1), nodes=nodes, edges=edges, error=err)


async def main():
    out, rep, docs = Path(sys.argv[1]), sys.argv[2], [Path(p) for p in sys.argv[3:]]
    for d in docs:
        row = await one(d, out / f"rep{rep}" / d.stem)
        row["rep"] = int(rep)
        print(row, flush=True)
        with open(out / "summary.jsonl", "a") as f:
            f.write(json.dumps(row) + "\n")


asyncio.run(main())
