"""Blind first-opinion labels of spike C by the coding agent (Claude), written before the owner's marking. Not truth labels.
Every item was read against the full source document. Default = right; the lists are the exceptions.
usage: python3 -I judge_claude.py MARKING.html OUT.json"""
import json, re, sys
from collections import Counter

TRIVIAL = "I002 I005 I008 I011 I012 I017 I025 I030 I031 I045 I046 I072 I080 I085 I092 I097 I101 I130 I132 I151 I170 I181".split()
WRONG = "I015 I041 I058".split()  # I015 direction/meaning wrong; I041/I058 mangled name "SA Flow Diagram" (PRIMSA)
INVENTED = "I057 I059".split()  # Boolean operators <-> PubMed/Embase: an inference, the text does not state it
NOTES = {
    "I015": "edge says Bluebook derived from inline citations; the text says systems derived from the Bluebook",
    "I041": "name cut from 'PRIMSA flow diagram'", "I058": "same mangled node as I041",
    "I057": "text only says Boolean operators assist literature searches and lists PubMed as a database",
    "I059": "same inference for Embase",
    "I097": "target node 'Technical Review' is a paraphrase of 'engineering review' (I092), duplicate chain",
    "I031": "duplicate of I022", "I046": "duplicate of I044 (case only)", "I080": "duplicate of I073",
}
h = open(sys.argv[1]).read()
ids = re.findall(r'<section class="card" data-id="(I\d+)">', h)
docs, cur = {}, None
for m in re.finditer(r'<h2 class="doc">(.*?)</h2>|data-id="(I\d+)"', h):
    if m.group(1):
        cur = m.group(1)
    else:
        docs[m.group(2)] = cur
lab = {}
for i in ids:
    lab[i] = "trivial" if i in TRIVIAL else "wrong" if i in WRONG else "invented" if i in INVENTED else "right"
json.dump([dict(id=i, doc=docs[i], decision=lab[i], note=NOTES.get(i, "")) for i in ids], open(sys.argv[2], "w"), indent=1)
n = len(ids)
c = Counter(lab.values())
print(f"{n} items:", {k: f"{v} ({100 * v / n:.1f} %)" for k, v in c.items()})
for d in dict.fromkeys(docs.values()):
    cc = Counter(lab[i] for i in ids if docs[i] == d)
    print(f"  {d:36s} right {cc['right']:2d}  useless {cc['trivial']:2d}  wrong {cc['wrong']}  invented {cc['invented']}")
