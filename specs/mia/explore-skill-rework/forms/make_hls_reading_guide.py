"""Builds hls-reading-guide.html: what changed in the HLS between its state before iteration 2 (parent of 1c29d94) and now,
side by side, per requirement ID (FR, NFR, CON, AC, TB, N) and per other changed line of a section.
usage: python3 -I make_hls_reading_guide.py OUT.html   (run in the repository)"""
import difflib, html, re, subprocess, sys

OLD_REV = "1c29d94^"
OLD = subprocess.check_output(["git", "show", f"{OLD_REV}:specs/mia/high-level-spec.md"], text=True).splitlines()
NEW = open("specs/mia/high-level-spec.md").read().splitlines()
ID = re.compile(r"^(?:- \*\*|\| \*{0,2})((?:FR|NFR|CON|AC|TB|N|IF)-[\w.]+?)(?=[\s*:|)\]])")


def blocks(lines):
    out, sec, other = {}, "", {}
    for l in lines:
        if l.startswith("#"):
            sec = l.lstrip("# ").strip()
        m = ID.match(l)
        if m:
            out[m.group(1)] = (sec, l)
        else:
            other.setdefault(sec, []).append(l)
    return out, other


def inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", s)


def clean(l):
    return re.sub(r"^- ", "", l.strip().strip("|").strip())


def worddiff(a, b):
    aw, bw = a.split(" "), b.split(" ")
    sm = difflib.SequenceMatcher(None, aw, bw, autojunk=False)
    ra, rb = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        x, y = " ".join(aw[i1:i2]), " ".join(bw[j1:j2])
        if op == "equal":
            ra.append(x); rb.append(y)
        else:
            if x: ra.append(f"\x01{x}\x02")
            if y: rb.append(f"\x03{y}\x04")
    def fin(t, o, c, tag):
        return inline(t).replace(o, f"<{tag}>").replace(c, f"</{tag}>")
    return fin(" ".join(ra).replace("\x03", "").replace("\x04", ""), "\x01", "\x02", "del"), \
           fin(" ".join(rb).replace("\x01", "").replace("\x02", ""), "\x03", "\x04", "ins")


old_b, old_o = blocks(OLD)
new_b, new_o = blocks(NEW)
rows = []
for k, (sec, l) in new_b.items():
    if k not in old_b:
        rows.append((sec, k, "new", "", inline(clean(l))))
    elif old_b[k][1] != l:
        a, b = worddiff(clean(old_b[k][1]), clean(l))
        rows.append((sec, k, "changed", a, b))
for k, (sec, l) in old_b.items():
    if k not in new_b:
        rows.append((sec, k, "removed", inline(clean(l)), ""))

other = []
for sec in dict.fromkeys(list(old_o) + list(new_o)):
    a, b = old_o.get(sec, []), new_o.get(sec, [])
    d = [x for x in difflib.ndiff(a, b) if x[:2] in ("- ", "+ ") and x[2:].strip()]
    if d:
        other.append((sec, d))

css = """:root{--bg:#fff;--fg:#1d2330;--card:#f4f6fa;--line:#c9d0dc;--new:#d9f2dd;--del:#fadadd;--acc:#2a5bd7}
@media(prefers-color-scheme:dark){:root{--bg:#141821;--fg:#e6e9f0;--card:#1e2430;--line:#38405a;--new:#1f4a2a;--del:#5a2530;--acc:#7ea2ff}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1200px;padding:16px}
h1{font-size:1.3rem}h2{font-size:1.1rem;margin-top:30px;border-bottom:1px solid var(--line)}h3{font-size:.95rem;margin:14px 0 4px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}.cell{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:6px 10px}
.hd{font-size:.8rem;opacity:.7}ins{background:var(--new);text-decoration:none}del{background:var(--del)}
.tag{font-size:.75rem;border:1px solid var(--line);border-radius:10px;padding:0 8px;margin-left:6px}
.empty{opacity:.5;font-style:italic}code{font-size:.85em}
@media(max-width:700px){.row{grid-template-columns:1fr}}nav a{color:var(--acc);margin-right:10px}"""
parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>HLS reading guide</title><style>{css}</style></head><body>",
         "<h1>HLS reading guide: iteration 2 (skill rework), old and new side by side</h1>",
         f"<p>Left: the HLS before iteration 2 (<code>{OLD_REV}</code>). Right: the HLS now (draft, not approved). Deleted words are red, added words green. "
         f"{sum(r[2]=='new' for r in rows)} requirements, criteria or rows are new, {sum(r[2]=='changed' for r in rows)} changed, {sum(r[2]=='removed' for r in rows)} removed. "
         "Unchanged text is not shown; read it in <code>high-level-spec.md</code>. Below the ID rows are other changed lines per section.</p>"]
secs = list(dict.fromkeys(r[0] for r in rows))
parts.append("<nav>" + "".join(f"<a href='#s{i}'>{html.escape(s[:40])}</a>" for i, s in enumerate(secs)) + "<a href='#other'>Other changed lines</a></nav>")
for i, s in enumerate(secs):
    parts.append(f"<h2 id='s{i}'>{html.escape(s)}</h2>")
    for sec, k, kind, a, b in rows:
        if sec == s:
            parts.append(f"<h3>{k}<span class='tag'>{kind}</span></h3><div class='row'><div class='cell'><div class='hd'>before</div>{a or '<span class=empty>(did not exist)</span>'}</div>"
                         f"<div class='cell'><div class='hd'>now</div>{b or '<span class=empty>(removed)</span>'}</div></div>")
parts.append("<h2 id='other'>Other changed lines (headings, prose, table rows without an ID)</h2>")
for sec, d in other:
    parts.append(f"<h3>{html.escape(sec or '(top)')}</h3>")
    for x in d:
        parts.append(f"<div class='cell' style='margin:3px 0'>{'<del>' if x[0]=='-' else '<ins>'}{inline(clean(x[2:]))}{'</del>' if x[0]=='-' else '</ins>'}</div>")
parts.append("</body></html>")
open(sys.argv[1], "w").write("\n".join(parts))
print(len(rows), "id rows,", len(other), "sections with other changes ->", sys.argv[1])
