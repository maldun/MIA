"""Measures checks.py on the 195 sampled items against the agent's blind labels (judge-claude.json) and on all rep-1 items.
usage: <venv>/bin/python measure_checks.py RUNDIR MARKING.html JUDGE.json
The labels are the agent's first opinion, not truth labels: the numbers are indicative until the owner's marks exist."""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import networkx as nx
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import entity_in_source, relation_in_source

WINDOW = 300  # characters, about one sentence
run, marking, judge = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
meta = json.loads(re.search(r"const META=(\[.*?\]), KEY=", marking.read_text(), re.S).group(1))
lab = {x["id"]: x["decision"] for x in json.loads(judge.read_text())}
cache = {}


def load(doc):
    if doc not in cache:
        d = run / "rep1" / doc.replace(".txt", "")
        chunks = json.loads((d / "kv_store_text_chunks.json").read_text())
        cache[doc] = (nx.read_graphml(d / "graph_chunk_entity_relation.graphml"), {k: v["content"] for k, v in chunks.items()})
    return cache[doc]


def passages(attrs, chunks):
    return [chunks[c] for c in attrs.get("source_id", "").split("<SEP>") if c in chunks]


def run_checks(kind, key, attrs, chunks):
    ps = passages(attrs, chunks)
    if kind == "entity":
        return dict(c1=entity_in_source(key[0], ps), c2=None)
    return dict(c1=relation_in_source(key[0], key[1], ps), c2=relation_in_source(key[0], key[1], ps, WINDOW),
                ends=all(entity_in_source(k, ps) for k in key))


rows = []
for m in meta:
    G, chunks = load(m["doc"])
    k = m["key"]
    attrs = G.nodes[k[0]] if m["kind"] == "entity" else (G.get_edge_data(*k) or G.get_edge_data(k[1], k[0]))
    r = run_checks(m["kind"], k, attrs, chunks)
    # an item passes when its check holds: entity -> name in source; relation -> both ends in one chunk (loose) / one sentence (strict)
    full = [(Path(__file__).resolve().parent / "docs" / (m["doc"] if m["doc"].endswith(".txt") else m["doc"] + ".txt")).read_text()]  # the whole document, not the chunk
    fc = entity_in_source(k[0], full) if m["kind"] == "entity" else relation_in_source(k[0], k[1], full, WINDOW)
    names = all(entity_in_source(x, full) for x in k)
    rows.append(dict(id=m["id"], kind=m["kind"], key=k, label=lab[m["id"]], loose=r["c1"], strict=r["c2"], full=fc, names=names))

print("== on the 195 sampled items (agent labels) ==")
for name, getter in [("check A (loose: name / both ends in the source chunk)", lambda r: r["loose"]),
                     ("check B (strict: relation ends within %d characters)" % WINDOW,
                      lambda r: r["loose"] if r["kind"] == "entity" else r["strict"]),
                     ("check C (whole document, not the chunk; relation ends within %d characters)" % WINDOW,
                      lambda r: r["full"]),
                     ("check D (every name, i.e. each entity / each relation end, occurs in the whole document; no distance rule)",
                      lambda r: r["names"])]:
    flagged = [r for r in rows if not getter(r)]
    tab = Counter((r["label"], not getter(r)) for r in rows)
    print(f"\n{name}: flagged {len(flagged)} of {len(rows)}")
    for L in ("right", "trivial", "wrong", "invented"):
        tot = sum(1 for r in rows if r["label"] == L)
        fl = tab[(L, True)]
        print(f"  label {L:9s}: {tot:3d} items, flagged {fl:3d} ({100 * fl / max(tot, 1):.0f} %)")
    bad = [r for r in rows if r["label"] in ("wrong", "invented")]
    print(f"  catches {sum(1 for r in bad if not getter(r))} of {len(bad)} wrong/invented items;"
          f" false flags on right items: {tab[('right', True)]} of {sum(1 for r in rows if r['label'] == 'right')}")
    for r in flagged:
        print(f"    flagged {r['id']} [{r['label']}] {r['kind']} {r['key']}")
print("\nmissed by check D (wrong/invented but passing):",
      [(r["id"], r["label"]) for r in rows if r["label"] in ("wrong", "invented") and r["names"]])

print("\n== flag rate on ALL rep-1 items (no labels) ==")
tot = defaultdict(Counter)
for doc in sorted(p.name for p in (run / "rep1").iterdir()):
    G, chunks = load(doc + ".txt")
    for n, a in G.nodes(data=True):
        tot[doc]["entities"] += 1
        tot[doc]["entities flagged"] += not entity_in_source(n, passages(a, chunks))
        tot[doc]["entities missing in doc (D)"] += not entity_in_source(n, [(Path(__file__).resolve().parent / "docs" / (doc + ".txt")).read_text()])
    for u, v, a in G.edges(data=True):
        tot[doc]["relations"] += 1
        tot[doc]["relations flagged A"] += not relation_in_source(u, v, passages(a, chunks))
        tot[doc]["relations flagged B"] += not relation_in_source(u, v, passages(a, chunks), WINDOW)
        full = [(Path(__file__).resolve().parent / "docs" / (doc + ".txt")).read_text()]
        tot[doc]["relation ends missing in doc (D)"] += not (entity_in_source(u, full) and entity_in_source(v, full))
for doc, c in tot.items():
    print(f"  {doc:32s}", dict(c))
S = Counter()
for c in tot.values():
    S.update(c)
print("  total", dict(S))
