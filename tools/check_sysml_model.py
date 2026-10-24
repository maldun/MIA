"""Consistency checks for specs/mia (no SysML parser is available offline).

Usage: python3 -I tools/check_sysml_model.py <repository root>
Checks bracket balance of every .sysml file, id parity between architecture.sysml and the
high-level spec (FR, NFR, CON), satisfy/allocate coverage, allocation paths, existence of the code
files named in the model, and that baseline ids cited by the model and the spec exist in
baseline-requirements.md. It does not parse SysML."""
import re, sys, pathlib

root = pathlib.Path(sys.argv[1])
spec = root / "specs/mia"
arch_path = spec / "architecture.sysml"
files = sorted(spec.glob("**/*.sysml"))
problems = []


def strip(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    t = re.sub(r"//[^\n]*", "", t)
    return re.sub(r'"[^"]*"', '""', t)


# 1. balance
for f in files:
    t = strip(f.read_text())
    for o, c in ("{}", "()", "[]"):
        if t.count(o) != t.count(c):
            problems.append(f"{f.name}: unbalanced {o}{c}: {t.count(o)} vs {t.count(c)}")
    depth = 0
    for i, line in enumerate(t.splitlines(), 1):
        depth += line.count("{") - line.count("}")
        if depth < 0:
            problems.append(f"{f.name}:{i}: negative depth")
            break
    if depth != 0:
        problems.append(f"{f.name}: depth {depth} at end")

arch = arch_path.read_text()

# 2. ids: model vs HLS
hls = (spec / "high-level-spec.md").read_text()
ids_model = set(re.findall(r"requirement def <'((?:FR|NFR|CON)-\d+)'>", arch))
ids_hls = set(re.findall(r"- \*\*((?:FR|NFR)-\d+) ", hls)) | set(re.findall(r"- \*\*(CON-\d)\*\*", hls))
print("model ids:", len(ids_model), "HLS ids:", len(ids_hls))
if ids_model != ids_hls:
    problems.append(f"id mismatch: model-only {sorted(ids_model - ids_hls)} HLS-only {sorted(ids_hls - ids_model)}")

# usages and defs
defs = dict((i, n) for i, n in re.findall(r"requirement def <'((?:FR|NFR|CON)-\d+)'> (\w+)", arch))
tree = dict(re.findall(r"^\s+requirement (\w+) : (\w+);", arch, flags=re.M))
for n, d in tree.items():
    if d not in defs.values():
        problems.append(f"tree usage {n} has unknown def {d}")
for i, n in defs.items():
    if n not in tree.values():
        problems.append(f"{i} ({n}) has no usage in miaRequirements")

# 3. satisfy / allocate
sat = set(re.findall(r"satisfy (\w+) by mia;", arch))
al = re.findall(r"allocate (\w+) to mia\.(\w+)\.(\w+);", arch)
for n in tree:
    if n not in sat:
        problems.append(f"{n}: no satisfy")
    if not any(a == n for a, _, _ in al):
        problems.append(f"{n}: no allocate")

system = arch.split("part def MiaSystem")[1].split("part mia :")[0]
sys_parts = dict(re.findall(r"part (\w+) : (\w+);", system))
subdefs = {}
for m in re.finditer(r"part def (\w+) \{(.*?)\n    \}\n", arch, flags=re.S):
    subdefs[m.group(1)] = set(re.findall(r"^\s{8}part (\w+)", m.group(2), flags=re.M))
for n, sub, leaf in al:
    d = sys_parts.get(sub)
    if d is None:
        problems.append(f"allocate {n}: unknown subsystem {sub}")
    elif leaf not in subdefs.get(d, set()):
        problems.append(f"allocate {n}: {sub}.{leaf} not a part of {d}")
allocated = {(s, l) for _, s, l in al}
for s, d in sys_parts.items():
    for leaf in sorted(subdefs.get(d, ())):
        if (s, leaf) not in allocated:
            print(f"  note: part {s}.{leaf} carries no requirement")

# 4. code files named in the model exist
missing = set()
for mod in re.findall(r'"([^"]+\.(?:py|json|md|sh|yaml|html|js)|[^"]+/[^"]*)"', arch):
    if " " in mod or mod.endswith(".schema.json") or mod.startswith("none"):
        continue
    if not (root / mod).exists():
        missing.add(mod)
if missing:
    problems.append(f"files not found in repo: {sorted(missing)}")

# 5. baseline ids
base = (spec / "baseline-requirements.md").read_text()
base_ids = set(re.findall(r"^\| ([A-Z]{1,2}-\d+) \|", base, flags=re.M))
def expand(tok):
    m = re.fullmatch(r"([A-Z]+)-(\d+)\.\.(?:[A-Z]+-)?(\d+)", tok)
    if m:
        return [f"{m.group(1)}-{k}" for k in range(int(m.group(2)), int(m.group(3)) + 1)]
    return [tok]
cited = set()
for ids in re.findall(r":>> baseline = \(([^)]*)\)", arch):
    cited |= set(re.findall(r'"([^"]+)"', ids))
for br in re.findall(r"\[([A-Z]{1,2}-\d+[^\]]*)\]", hls):
    for tok in re.split(r",\s*", br):
        tok = tok.strip()
        if re.fullmatch(r"[A-Z]{1,2}-\d+(\.\.[A-Z]*-?\d+)?", tok):
            cited |= set(expand(tok))
for b in sorted(cited):
    if b not in base_ids:
        problems.append(f"baseline id {b} not in baseline-requirements.md")

# 6. the doc of each requirement in the model is the sentence of the HLS (the HLS is the source)
def norm(s):
    return re.sub(r"\s+", " ", s.replace("**", "").replace("`", "")).strip()
hls_text = {}
for line in hls.split("\n"):
    m = re.match(r"^- \*\*((?:N?FR)-\d+) [^*]+\*\*(?: \([^)]*\))? \[[^\]]*\] \([^)]*\)\. (.*)$", line)
    if m:
        hls_text[m.group(1)] = norm(m.group(2))
    m = re.match(r"^- \*\*(CON-\d)\*\* (.*)$", line)
    if m:
        hls_text[m.group(1)] = norm(m.group(2))
for rid in sorted(defs):
    m = re.search(r"requirement def <'%s'> \w+ \{\s*subject mia : MiaSystem;\s*doc /\*(.*?)\*/" % re.escape(rid), arch, re.S)
    if m and norm(m.group(1)) != hls_text.get(rid):
        problems.append(f"{rid}: the doc in architecture.sysml differs from the HLS sentence")

print("PROBLEMS:" if problems else "OK")
for p in problems:
    print(" -", p)
sys.exit(1 if problems else 0)
