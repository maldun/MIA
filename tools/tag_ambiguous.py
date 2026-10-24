"""Keep the cases out of decisions where the owner's label differs from the benchmark label (the audit sample).

Usage (repository root):
    python3 -I tools/tag_ambiguous.py data/eval-external/audit/ambiguous.txt eval/suites/verdicts_vitaminc eval/suites/verdicts_vitaminc.holdout ...
    python3 -I tools/tag_ambiguous.py <ambiguous.txt> data/eval-external/suites/*     (the generated source too, so a rebuild keeps them out)

ambiguous.txt is written by tools/label_agreement.py (one case id per line). Every listed case gets the tags `ambiguous` and
`retired` and a note; the scripts of the agent-app workflow skip `retired` cases (they ignore `ambiguous`). The cases stay in the
file, so old runs remain explainable. Safe to repeat: a case that is tagged already is not changed. Prints only counts."""
import json, pathlib, sys

NOTE = "ambiguous: the owner's label differs from the benchmark label (audit sample, 2026-10-24); kept out of decisions"


def tag_file(cases_file, ids):
    changed = found = 0
    lines = []
    for line in open(cases_file, encoding="utf8"):
        c = json.loads(line)
        if c["id"] in ids:
            found += 1
            if "retired" not in c["tags"] or "ambiguous" not in c["tags"]:
                c["tags"] = sorted(set(c["tags"]) | {"ambiguous", "retired"})
                c["note"] = (c.get("note", "") + " | " if c.get("note") else "") + NOTE
                changed += 1
        lines.append(json.dumps(c, ensure_ascii=False) + "\n")
    pathlib.Path(cases_file).write_text("".join(lines), encoding="utf8")
    return found, changed


def main(ambiguous_file, folders):
    ids = {l.strip() for l in open(ambiguous_file, encoding="utf8") if l.strip()}
    total_found = 0
    for d in folders:
        f = pathlib.Path(d) / "cases.jsonl"
        if not f.exists():
            print("no cases.jsonl in", d)
            continue
        found, changed = tag_file(f, ids)
        total_found += found
        print("%-60s %2d listed cases found, %2d newly tagged" % (d, found, changed))
    print("ids in %s: %d, found in these folders: %d" % (ambiguous_file, len(ids), total_found))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2:]))
