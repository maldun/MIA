"""Turn labelled draft cases into the two folders of a suite (dev and holdout).

Usage (repository root):
    python3 -I tools/promote_drafts.py specs/number-gate/eval-drafts/verdicts_injection.jsonl verdicts_injection eval/suites --labelled
Reads the drafts, sorts them by their tag split:dev or split:holdout, and writes <suites>/<name>/ and <suites>/<name>.holdout/ with suite.json and cases.jsonl
(target: pipeline, skill verify_claim, like the suite verdicts). Without --labelled it only shows what it would do. With --labelled it also adds the tag
label:people and removes source:draft: say that only after you have checked the truth of EVERY case yourself (the workflow: a person labels, not the coding agent).
A draft without a split tag stops the tool. Existing folders are not overwritten. Prints only counts."""
import json, pathlib, sys

TARGET = {"kind": "pipeline", "skill": "verify_claim"}


def main(drafts, name, suites, labelled):
    cases = [json.loads(l) for l in open(drafts, encoding="utf8") if l.strip()]
    parts = {"dev": [], "holdout": []}
    for c in cases:
        split = [t[6:] for t in c["tags"] if t.startswith("split:")]
        if len(split) != 1 or split[0] not in parts:
            print("case %s has no single split tag; stopped" % c["id"])
            return 1
        if labelled:
            c["tags"] = sorted(set(c["tags"]) - {"source:draft"} | {"label:people"})
        parts[split[0]].append(c)
    for kind, rows in parts.items():
        folder = pathlib.Path(suites) / (name if kind == "dev" else name + ".holdout")
        print("%-12s %3d cases -> %s%s" % (kind, len(rows), folder, "" if labelled else "  (dry run)"))
        if not labelled:
            continue
        if folder.exists():
            print("  %s exists already: not overwritten" % folder)
            return 1
        folder.mkdir(parents=True)
        (folder / "suite.json").write_text(json.dumps({"name": folder.name, "description": "Red-team cases for the verification gate: instructions in the evidence, in the claim, hidden instructions, role confusion, oversized evidence. Fictional entities, labelled by the owner.", "target": TARGET}, indent=1) + "\n", encoding="utf8")
        (folder / "cases.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf8")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--labelled"]
    if len(args) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args[0], args[1], args[2], "--labelled" in sys.argv))
