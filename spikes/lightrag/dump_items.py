"""Dumps the items of the marking page as plain text per document (for a blind judge): id | kind | head | description.
usage: python3 -I dump_items.py MARKING.html OUTDIR"""
import html, re, sys
from pathlib import Path

h = Path(sys.argv[1]).read_text()
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
doc, rows = None, {}
for m in re.finditer(r'<h2 class="doc">(.*?)</h2>|<section class="card" data-id="(I\d+)">\s*<h3>(.*?)</h3>\s*<p class="desc">(.*?)</p>', h, re.S):
    if m.group(1):
        doc = html.unescape(m.group(1))
        rows[doc] = []
    else:
        head = html.unescape(m.group(3)).split(" · ", 1)[1]
        rows[doc].append(f"{m.group(2)} | {head} | {html.unescape(m.group(4))}")
for d, r in rows.items():
    (out / (d.replace(".txt", "") + ".items.txt")).write_text("\n".join(r) + "\n")
    print(d, len(r))
