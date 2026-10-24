"""Draw three views of specs/mia/architecture.sysml as SVG with Graphviz (no size limit).

Usage: python3 -I tools/sysml_to_svg.py <repository root> [output folder]
Views: architecture.svg (subsystems and parts, colour = build status), allocation.svg (requirements to
subsystems), agent-view.svg (untrusted text flowing into model steps, with trust boundaries).
Reads the text with regular expressions; it does not parse SysML. Needs the Graphviz program `dot`."""
import re, shutil, subprocess, sys, pathlib

root = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else root / "specs/mia/diagrams"
out.mkdir(parents=True, exist_ok=True)
text = (root / "specs/mia/architecture.sysml").read_text(encoding="utf8")

FILL = {"built": "#b7e1b0", "partly": "#ffe699", "proposed": "#a9c8ee", "postponed": "#d0d0d0", "dropped": "#f4b6b6"}

def block(src, start):
    """text of the {...} block that opens at src[start] == '{'"""
    depth = 0
    for i in range(start, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[start + 1:i]
    raise ValueError("unbalanced")

def part_defs(src):
    return {m.group(1): block(src, m.end() - 1) for m in re.finditer(r"part def (\w+) \{", src)}

defs = part_defs(text)
system = defs["MiaSystem"]
subs = re.findall(r"^\s{8}part (\w+) : (\w+);", system, flags=re.M)      # (usage, def)

def leaves(body):
    res = []
    for m in re.finditer(r"^\s{8}part (\w+) \{", body, flags=re.M):
        b = block(body, m.end() - 1)
        st = re.search(r"status = ImplementationStatus::(\w+)", b)
        res.append((m.group(1), st.group(1) if st else "proposed"))
    return res

def esc(s):
    return s.replace('"', "'")

def render(name, dot):
    (out / (name + ".dot")).write_text(dot, encoding="utf8")
    if shutil.which("dot"):
        subprocess.run(["dot", "-Tsvg", str(out / (name + ".dot")), "-o", str(out / (name + ".svg"))], check=True)
        print("wrote", out / (name + ".svg"))
    else:
        print("dot not found; wrote", out / (name + ".dot"))

# ---------------------------------------------------------------- architecture
# one table per subsystem (parts coloured by status), four tables per row
counts = {}
tables = []
for usage_name, d in subs:
    rows = "".join('<TR><TD ALIGN="LEFT" BGCOLOR="%s">%s</TD></TR>' % (FILL[st], leaf) for leaf, st in leaves(defs[d]))
    for leaf, st in leaves(defs[d]):
        counts[st] = counts.get(st, 0) + 1
    tables.append((usage_name, '<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
                   '<TR><TD BGCOLOR="#444444"><FONT COLOR="white"><B>%s</B></FONT></TD></TR>%s</TABLE>>' % (usage_name, rows)))
g = ['digraph A {', 'rankdir=TB; fontname="Helvetica"; node [shape=plain, fontname="Helvetica", fontsize=10]; edge [style=invis];',
     'label="MIA: subsystems and parts (colour = status in the code base)"; labelloc=t; fontsize=16;']
for n, label in tables:
    g.append(f'"{n}" [label={label}];')
legend = "".join('<TR><TD BGCOLOR="%s">%s (%d)</TD></TR>' % (v, k, counts.get(k, 0)) for k, v in FILL.items())
g.append('"legend" [label=<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4"><TR><TD><B>legend</B></TD></TR>%s</TABLE>>];' % legend)
names = [n for n, _ in tables] + ["legend"]
per_row = 4
for i in range(0, len(names), per_row):
    row = names[i:i + per_row]
    g.append("{ rank=same; " + "; ".join(f'"{n}"' for n in row) + "; }")
    for a, b in zip(row, row[1:]):
        g.append(f'"{a}" -> "{b}";')
    if i + per_row < len(names):
        g.append(f'"{row[0]}" -> "{names[i + per_row]}";')
g.append("}")
render("architecture", "\n".join(g))

# ---------------------------------------------------------------- allocation
alloc = re.findall(r"allocate (\w+) to mia\.(\w+)\.(\w+);", text)
rid = dict((m.group(2), m.group(1)) for m in re.finditer(r"requirement def <'([A-Z]+-\d+)'> (\w+)", text))
usage = dict((m.group(1), m.group(2)) for m in re.finditer(r"^\s+requirement (\w+) : (\w+);", text, flags=re.M))
edges = {}
for r, sub, leaf in alloc:
    edges.setdefault((r, sub), []).append(leaf)
g = ['digraph B {', 'rankdir=LR; fontname="Helvetica"; node [fontname="Helvetica", fontsize=10];',
     'label="Requirements allocated to subsystems (edge label = number of parts)"; labelloc=t; fontsize=16;']
for r in sorted({r for r, _ in edges}, key=lambda x: (re.sub(r"\d", "", x), int(re.sub(r"\D", "", x)))):
    g.append(f'"{r}" [label="{rid[usage[r]]}", shape=box, style=filled, fillcolor="#eeeeee"];')
for usage_name, _ in subs:
    g.append(f'"S_{usage_name}" [label="{usage_name}", shape=box, style="filled,rounded", fillcolor="#dde8f7"];')
for (r, sub), ls in sorted(edges.items()):
    g.append(f'"{r}" -> "S_{sub}" [label="{len(ls)}", fontsize=8, tooltip="{esc(", ".join(ls))}"];')
g.append("}")
render("allocation", "\n".join(g))

# ---------------------------------------------------------------- agent view
agent = defs["MiaAgent"]
parts = dict(re.findall(r"^\s{8}part (\w+) : (\w+);", agent, flags=re.M))
g = ['digraph C {', 'rankdir=LR; fontname="Helvetica"; node [fontname="Helvetica", fontsize=10, shape=box];',
     'label="Agent view: untrusted text into model steps (orange = model step, grey = code, label = trust boundary)"; labelloc=t; fontsize=16;']
for p, d in parts.items():
    b = defs[d]
    if "@ModelStep" in b:
        tb = re.search(r'boundary = "([^"]+)"', b)
        pin = re.search(r'pin = "([^"]+)"', b)
        g.append(f'"{p}" [label="{p}\\n{tb.group(1) if tb else ""}\\n{pin.group(1) if pin else ""}", style="filled,rounded", fillcolor="#ffd8a8"];')
    else:
        g.append(f'"{p}" [label="{p}", style=filled, fillcolor="#e6e6e6"];')
for item, a, b in re.findall(r"flow of (\w+) from (\w+)\.\w+ to (\w+)\.\w+;", agent):
    org = re.search(r"item def %s \{ @Untrusted \{ origin = \"(\w+)\"" % item, text)
    g.append(f'"{a}" -> "{b}" [label="{item}\\n({org.group(1) if org else "?"})", fontsize=8];')
g.append("}")
render("agent-view", "\n".join(g))
