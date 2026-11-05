"""Scores the owner's marks of spike C against the bar (right >= 68 %, invented <= 5 %, shares of all marked items).
usage: python3 -I score_marks.py MARKS.json [OTHER.json]
MARKS.json = file saved by forms/spike-c-marking.html ({"items": [...], "missing": [...]}).
OTHER.json (optional, a list of {id, decision}, e.g. judge-claude.json) is compared with the marks: agreement and
Cohen's kappa over the four classes and over right-vs-not-right. Unmarked items are left out and counted."""
import json, sys
from collections import Counter

CLASSES = ["right", "trivial", "wrong", "invented"]
BAR_RIGHT, BAR_INVENTED = 0.68, 0.05


def load_marks(path):
    d = json.load(open(path))
    items = d["items"] if isinstance(d, dict) else d
    return {i["id"]: i for i in items}, (d.get("missing", []) if isinstance(d, dict) else [])


def shares(items):
    c = Counter(i["decision"] for i in items)
    n = sum(c.values())
    return n, {k: (c[k] / n if n else 0.0) for k in CLASSES}, c


def kappa(pairs, classes):
    n = len(pairs)
    if not n:
        return float("nan")
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in classes) / n**2
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def main(argv):
    marks, missing = load_marks(argv[1])
    marked = [m for m in marks.values() if m.get("decision") in CLASSES]
    print(f"{len(marked)} of {len(marks)} items marked")
    n, s, c = shares(marked)
    print("overall: " + ", ".join(f"{k} {c[k]} ({100 * s[k]:.1f} %)" for k in CLASSES))
    ok_r, ok_i = s["right"] >= BAR_RIGHT, s["invented"] <= BAR_INVENTED
    print(f"bar: right >= {100 * BAR_RIGHT:.0f} % -> {'PASS' if ok_r else 'FAIL'}; "
          f"invented <= {100 * BAR_INVENTED:.0f} % -> {'PASS' if ok_i else 'FAIL'}")
    for doc in dict.fromkeys(m["doc"] for m in marked):
        dn, ds, dc = shares([m for m in marked if m["doc"] == doc])
        print(f"  {doc:36s} n={dn:2d} right {dc['right']:2d}  useless {dc['trivial']:2d}  wrong {dc['wrong']}  invented {dc['invented']}")
    for m in missing:
        if m.get("note"):
            print(f"missing items, {m['doc']}: {m['note']}")
    for m in marked:
        if m.get("comment"):
            print(f"comment {m['id']} ({m['decision']}): {m['comment']}")
    if len(argv) > 2:
        other = {i["id"]: i["decision"] for i in json.load(open(argv[2]))}
        pairs = [(m["decision"], other[m["id"]]) for m in marked if m["id"] in other]
        agree = sum(a == b for a, b in pairs) / len(pairs)
        print(f"agreement with {argv[2]}: {len(pairs)} items, {100 * agree:.1f} % equal, "
              f"kappa {kappa(pairs, CLASSES):.2f} (4 classes), "
              f"{kappa([(a == 'right', b == 'right') for a, b in pairs], [True, False]):.2f} (right vs not)")
        print("owner -> other, differing pairs:", dict(Counter((a, b) for a, b in pairs if a != b)))


if __name__ == "__main__":
    main(sys.argv)
