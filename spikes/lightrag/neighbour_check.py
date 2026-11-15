"""Throwaway: of the relations option1.py refused for 'quote does not contain both ends', how many would pass if both
ends may also occur in the two neighbouring sentences (candidate FR-42 text)? Passing is NOT the same as right: the owner reads them.
usage: python3 -I neighbour_check.py DOCS_DIR RUNDIR [RUNDIR...]"""
import json, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from pathlib import Path
from option1 import split_sentences
from checks import norm, relation_in_source
docs = Path(sys.argv[1]); rows = []
for run in sys.argv[2:]:
    for f in sorted(Path(run).glob("*.json")):
        sents = list(split_sentences((docs / f"{f.stem}.txt").read_text()))
        ns = [norm(s) for s in sents]
        for r in json.load(open(f))["refused"]:
            it = r["item"]
            if r["reason"] != "quote does not contain both ends": continue
            q = norm(it["quote"])
            i = next((k for k, s in enumerate(ns) if q in s or s in q), None)
            if i is None: rows.append((f.stem, it, "quote not located", False)); continue
            win = " ".join(sents[max(0, i - 1): i + 2])
            rows.append((f.stem, it, win, relation_in_source(it["source"], it["target"], [win])))
ok = [r for r in rows if r[3]]
print(f"{len(rows)} refused for both ends; {len(ok)} pass with neighbours, {len(rows) - len(ok)} still refused")
for d, it, w, p in rows:
    print(("PASS " if p else "FAIL ") + d, "|", it["source"], "-", it["relation"], "-", it["target"], "|", it["quote"][:110])
