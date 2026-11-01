"""The tests near each root check (inventory, not verification): for every TC-MIA row of specs/mia/test-spec.md, the test files whose mark.req ids lead through the
Parent: lines of the node requirements to the FR/NFR of the row.  python3 tools/tc_mia_inventory.py   (prints: id, stage, kind :: files)
"""
import re, glob, collections, sys, os
spec="specs/mia"
parent={}; 
files=[spec+"/requirements.md"]+glob.glob(spec+"/nodes/**/requirements.md",recursive=True)
for f in files:
    for b in re.split(r"\n(?=### )",open(f,encoding="utf-8").read()):
        m=re.match(r"### ((?:REQ-[A-Z0-9]+-\d+)|(?:N?FR-\d+)|(?:NFR-\d+))",b)
        if not m: continue
        p=re.search(r"- Parent: (.*)",b)
        parent[m.group(1)]=re.findall(r"(?:REQ-[A-Z0-9]+-\d+|NFR-\d+|FR-\d+|IF-\d+)",p.group(1)) if p else []
def top(r,seen=()):
    if re.fullmatch(r"N?FR-\d+",r): return {r}
    out=set()
    for p in parent.get(r,[]):
        if p not in seen: out|=top(p,seen+(r,))
    return out
tests=collections.defaultdict(set)   # top req -> files
for f in glob.glob("tests/**/*.py",recursive=True)+glob.glob("tests/**/*.mjs",recursive=True):
    if "/helpers/" in f or "/mocks/" in f: continue
    txt=open(f,encoding="utf-8",errors="ignore").read()
    for ids in re.findall(r"mark\.req\(([^)]*)\)",txt):
        for r in re.findall(r"(?:REQ-[A-Z0-9]+-\d+|N?FR-\d+|NFR-\d+)",ids):
            for t in (top(r) or ({r} if re.fullmatch(r"N?FR-\d+",r) else set())): tests[t].add(f)
# TC rows
rows=[]
for line in open(spec+"/test-spec.md",encoding="utf-8"):
    m=re.match(r"\| (TC-MIA-\d+)(?: \(AC-\d+\))? \| ([^|]*)\| ([^|]*)\| (\d)",line)
    if m: rows.append((m.group(1),re.findall(r"N?FR-\d+|NFR-\d+",m.group(2)),m.group(3).strip(),m.group(4)))
for tc,reqs,kind,stage in rows:
    if len(reqs)==0 and tc!="TC-MIA-020": continue
    fs=set()
    for r in reqs: fs|=tests.get(r,set())
    print(tc, stage, kind, "::", " ".join(sorted(os.path.basename(x).replace("test_","").replace(".py","").replace(".test.mjs","(js)").replace(".mjs","(js)") for x in fs)))
