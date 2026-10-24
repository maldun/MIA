"""Consistency checks for docs/fresh-start (no SysML parser is available offline).

Usage: python3 -I tools/check_sysml_model.py <repository root>
Checks bracket balance, id parity between the SysML model and 02_high_level_requirements.md,
satisfy/allocate coverage, allocation paths, existence of the code files named in the model and
the baseline ids cited. It does not parse SysML."""
import re, sys, pathlib

root = pathlib.Path(sys.argv[1])
sysml = root / "docs/fresh-start/sysml"
files = sorted(sysml.glob("*.sysml"))
problems = []

def strip(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    t = re.sub(r"//[^\n]*", "", t)
    t = re.sub(r'"[^"]*"', '""', t)
    return t

# 1. balance
for f in files:
    t = strip(f.read_text())
    for o, c in ("{}", "()", "[]"):
        if t.count(o) != t.count(c):
            problems.append(f"{f.name}: unbalanced {o}{c}: {t.count(o)} vs {t.count(c)}")
    # statements: every non-brace line should end in ; { } or be a continuation; weak check on 'part|action..' lines
    depth = 0
    for i, line in enumerate(t.splitlines(), 1):
        depth += line.count("{") - line.count("}")
        if depth < 0:
            problems.append(f"{f.name}:{i}: negative depth")
            break
    if depth != 0:
        problems.append(f"{f.name}: depth {depth} at end")

# 2. ids
req = (sysml / "MIA_Requirements.sysml").read_text()
ids_sysml = re.findall(r"requirement def <'((?:HLR|CON)-\d+)'> (\w+)", req)
prose = (root / "docs/fresh-start/02_high_level_requirements.md").read_text()
ids_prose = set(re.findall(r"\*\*(HLR-\d+) ", prose)) | set(re.findall(r"\| (CON-\d) \|", prose))
ids_model = {i for i, _ in ids_sysml}
print("model ids:", len(ids_model), "prose ids:", len(ids_prose))
if ids_model != ids_prose:
    problems.append(f"id mismatch: model-only {sorted(ids_model - ids_prose)} prose-only {sorted(ids_prose - ids_model)}")

# titles prose vs model (loose)
for i, name in ids_sysml:
    m = re.search(r"\*\*%s ([^*]+)\.\*\*" % i, prose)
    if m:
        words = re.sub(r"[^a-z]", "", m.group(1).lower().split("(")[0])
        if re.sub(r"[^a-z]", "", name.lower()) not in words and words not in re.sub(r"[^a-z]", "", name.lower()):
            print(f"  note: title differs {i}: prose '{m.group(1)}' vs model '{name}'")

# usages in tree
tree = dict((n, d) for n, d in re.findall(r"requirement (\w+) : (\w+);", req))
defs = {n for _, n in ids_sysml}
for n, d in tree.items():
    if d not in defs:
        problems.append(f"tree usage {n} has unknown def {d}")
for _, n in ids_sysml:
    if n not in tree.values():
        problems.append(f"def {n} has no usage in miaRequirements")

# 3. allocation
alloc = (sysml / "MIA_Allocation.sysml").read_text()
sat = set(re.findall(r"satisfy (\w+) by mia;", alloc))
al = re.findall(r"allocate (\w+) to mia\.(\w+)\.(\w+);", alloc)
for n in tree:
    if n not in sat:
        problems.append(f"{n}: no satisfy")
    if not any(a == n for a, _, _ in al):
        problems.append(f"{n}: no allocate")

arch = (sysml / "MIA_Architecture.sysml").read_text()
sys_parts = dict(re.findall(r"part (\w+) : (\w+);", arch.split("part def MiaSystem")[1].split("part mia :")[0]))
# leaf parts per subsystem def
subdefs = {}
for m in re.finditer(r"part def (\w+) \{(.*?)\n    \}\n", arch, flags=re.S):
    subdefs[m.group(1)] = set(re.findall(r"^\s{8}part (\w+)", m.group(2), flags=re.M))
for n, sub, leaf in al:
    d = sys_parts.get(sub)
    if d is None:
        problems.append(f"allocate {n}: unknown subsystem {sub}")
    elif leaf not in subdefs.get(d, set()):
        problems.append(f"allocate {n}: {sub}.{leaf} not a part of {d}")

# parts never allocated
allocated = {(s, l) for _, s, l in al}
for s, d in sys_parts.items():
    for leaf in sorted(subdefs.get(d, ())):
        if (s, leaf) not in allocated:
            print(f"  note: part {s}.{leaf} carries no requirement")

# 4. modules exist
missing = set()
for mod in re.findall(r'"([^"]+\.(?:py|json|md|sh|yaml|html|js)|[^"]+/[^"]*)"', arch):
    if not (root / mod).exists():
        missing.add(mod)
if missing:
    problems.append(f"modules not found in repo: {sorted(missing)}")

# 5. baseline ids
base = (root / "docs/fresh-start/01_current_requirements.md").read_text()
base_ids = set(re.findall(r"^\| ([A-Z]{1,2}-\d+) \|", base, flags=re.M))
for ids in re.findall(r":>> baseline = \(([^)]*)\)", req):
    for b in re.findall(r'"([^"]+)"', ids):
        if b not in base_ids:
            problems.append(f"baseline id {b} not in 01_current_requirements.md")
# baseline ids named in prose
for b in set(re.findall(r"\b([A-Z]{1,2}-\d+)\b", prose)):
    if b.startswith(("HLR", "CON")):
        continue
    if b not in base_ids:
        problems.append(f"prose cites unknown baseline id {b}")

print("PROBLEMS:" if problems else "OK")
for p in problems:
    print(" -", p)
