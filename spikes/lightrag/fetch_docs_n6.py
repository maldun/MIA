"""Throwaway: three extra sample documents for the N-6 builder sample (owner's choice 2026-11-07). Downloaded text is data only.
usage: python3 -I fetch_docs_n6.py OUTDIR README_PATH"""
import html, json, re, sys, urllib.parse, urllib.request
from pathlib import Path
UA = {"User-Agent": "mia-spike/0.1 (research prototype)"}
CAP = 12000
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40) as r:
        return r.read().decode("utf-8", "replace")
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
# 1 arXiv: abstract + introduction of a recent paper with an HTML version (RAG survey, 2312.10997)
h = get("https://arxiv.org/html/2312.10997")
h = re.sub(r"(?s)<(script|style|math|annotation)[^>]*>.*?</\1>", " ", h)
h = re.sub(r"(?s)<(p|div|h\d|li)[^>]*>", "\n\n", h)
t = html.unescape(re.sub(r"<[^>]+>", "", h)); t = re.sub(r"[ \t]+", " ", t); t = re.sub(r"\n\s*\n+", "\n\n", t).strip()
i = t.lower().find("large language models (llms)"); (out / "arxiv_2312.10997_intro.txt").write_text(t[i:i + CAP])
# 3 news: a Wikinews article (first search hit, fixed query)
q = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": "interview scientists", "srnamespace": 0, "srlimit": 1, "format": "json"})
title = json.loads(get("https://en.wikinews.org/w/api.php?" + q))["query"]["search"][0]["title"]
q = urllib.parse.urlencode({"action": "query", "prop": "extracts", "explaintext": 1, "format": "json", "titles": title, "redirects": 1})
tx = next(iter(json.loads(get("https://en.wikinews.org/w/api.php?" + q))["query"]["pages"].values()))["extract"]
(out / "wikinews.txt").write_text(f"{title}\n\n{tx[:CAP]}")
# 2 MIA's own README section (local, not confidential)
r = Path(sys.argv[2]).read_text(); s = r.index("## Core, phase 2a"); e = r.index("## ", s + 5)
(out / "mia_readme_core_2a.txt").write_text(r[s:e][:CAP])
for p in sorted(out.iterdir()): print(p.name, p.stat().st_size)
