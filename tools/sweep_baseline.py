"""Sweep of the baseline against the HLS: which baseline rows are cited in no bracket, and which cited rows have little of their wording in the HLS text.
Usage (repository root): python3 -I tools/sweep_baseline.py   The output is read by hand; it is a heuristic, not a proof."""
import re

base = open("specs/mia/baseline-requirements.md", encoding="utf8").read()
hls = open("specs/mia/high-level-spec.md", encoding="utf8").read()
sysml = open("specs/mia/architecture.sysml", encoding="utf8").read()

# the HLS body without the id brackets and without the mapping tables
body = re.sub(r"\[[A-Z]{1,2}-\d+[^\]]*\]", " ", hls)
body = body.lower()

STOP = set("""shall should would could which their there these those about after before between during under through within without
because while where being other every other again still often later first second third known built partly proposed postponed
dropped status source source sources requirement requirements baseline """.split())

def tokens(s):
    toks = set()
    for m in re.finditer(r"`([^`]+)`", s):
        toks.add(m.group(1).lower())
    for w in re.findall(r"[a-zA-Z][a-zA-Z\-]{5,}", s):
        w = w.lower()
        if w not in STOP:
            toks.add(w[:7])
    return toks

rows = []
for line in base.split("\n"):
    m = re.match(r"^\| ([A-Z]{1,2}-\d+) \| (.*?) \| ([^|]*) \| ([^|]*) \|\s*$", line)
    if m:
        rows.append(m.groups())

cited = set()
for br in re.findall(r"\[([A-Z]{1,2}-\d+[^\]]*)\]", hls):
    for tok in re.split(r",\s*", br):
        m = re.fullmatch(r"([A-Z]+)-(\d+)\.\.([A-Z]*-?)(\d+)", tok.strip())
        if m:
            for k in range(int(m.group(2)), int(m.group(4)) + 1):
                cited.add(f"{m.group(1)}-{k}")
        else:
            cited.add(tok.strip())

res = []
for rid, text, src, status in rows:
    tk = tokens(text)
    hit = [w for w in tk if w in body or any(w in x for x in [body]) ]
    frac = len(hit) / len(tk) if tk else 1.0
    res.append((frac, rid, rid in cited, status.strip()[:30], text[:150]))
res.sort()
print("rows:", len(rows), " cited in a bracket:", sum(1 for r in res if r[2]))
print("\n-- not cited in any bracket --")
for f, rid, c, st, tx in res:
    if not c:
        print(f"{rid:6} {st:28} {tx}")
print("\n-- cited, but middle word coverage (0.45 to 0.65) --")
for f, rid, c, st, tx in res:
    if c and 0.45 <= f < 0.65:
        print(f"{f:.2f} {rid:6} {st:22} {tx}")
