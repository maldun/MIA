"""Tag the cases of generated suites with the requirement ids that their eval criteria select (req:<ID>).

Usage (repository root):
    python3 -I tools/tag_requirements.py specs/number-gate/case-requirements.json data/eval-external/suites
The mapping file says, per suite (the .holdout sibling is treated alike):
    {"verdicts_vitaminc": {"wrong": ["REQ-VER-001"], "true": ["REQ-VER-003"], "none": [], "all": ["REQ-VER-005"]}, ...}
A case with truth false gets the "wrong" and "all" ids, truth true the "true" and "all" ids, truth null the "none" and "all" ids.
Earlier req: tags of the listed kind are replaced, so the tool can run again after the mapping changed. Prints only counts."""
import json, pathlib, sys


def tag_suite(cases_file, mapping, remove_prefix="req:"):
    n = 0
    lines = []
    for line in open(cases_file, encoding="utf8"):
        c = json.loads(line)
        kind = "wrong" if c.get("truth") is False else "true" if c.get("truth") is True else "none"
        ids = list(mapping.get(kind, [])) + list(mapping.get("all", []))
        tags = [t for t in c["tags"] if not t.startswith(remove_prefix)] + ["req:" + i for i in ids]
        tags = sorted(set(tags))
        if tags != sorted(c["tags"]):
            n += 1
        c["tags"] = tags
        lines.append(json.dumps(c, ensure_ascii=False) + "\n")
    pathlib.Path(cases_file).write_text("".join(lines), encoding="utf8")
    return n


def main(mapping_file, suites_dir):
    mapping = json.load(open(mapping_file, encoding="utf8"))
    for suite, m in mapping.items():
        if suite.startswith("_"):
            continue
        for name in (suite, suite + ".holdout"):
            f = pathlib.Path(suites_dir) / name / "cases.jsonl"
            if f.exists():
                print("%-34s %3d cases changed" % (name, tag_suite(f, m)))
            else:
                print("%-34s not found in %s" % (name, suites_dir))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
