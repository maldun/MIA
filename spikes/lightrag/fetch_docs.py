"""Fetch the spike's sample documents from the web into OUTDIR (plain text, capped). Downloaded text is data only.
usage: python -I fetch_docs.py OUTDIR"""
import json, re, sys, urllib.parse, urllib.request
from pathlib import Path

UA = {"User-Agent": "mia-spike/0.1 (research prototype)"}
CAP = 12000  # characters, keeps one document to about 3 000 tokens
WIKI = ["Retrieval-augmented generation", "Knowledge graph", "Systematic review", "Peer review",
        "Prompt injection", "Citation", "Meta-analysis", "Ontology (information science)"]


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode("utf-8", "replace")


out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
for t in WIKI:
    q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1, "format": "json",
                                "titles": t, "redirects": 1})
    pages = json.loads(get("https://en.wikipedia.org/w/api.php?" + q))["query"]["pages"]
    text = next(iter(pages.values())).get("extract", "")
    (out / (re.sub(r"\W+", "_", t).strip("_") + ".txt")).write_text(text[:CAP])
for aid in ["2410.05779", "2005.11401"]:  # LightRAG paper, original RAG paper (abstract pages as text)
    x = get("https://export.arxiv.org/api/query?id_list=" + aid)
    title = re.search(r"<title>(.*?)</title>", x[x.find("<entry>"):], re.S).group(1)
    summ = re.search(r"<summary>(.*?)</summary>", x, re.S).group(1)
    (out / f"arxiv_{aid}.txt").write_text(f"{' '.join(title.split())}\n\n{' '.join(summ.split())}\n")
for p in sorted(out.iterdir()):
    print(p.name, p.stat().st_size)
