"""Retires named cases of dev suites: tags `ambiguous` and `retired` and adds a note with the reason. The agent-app scripts and the harness skip `retired` cases; the cases stay
in the file, so old runs remain explainable.

Usage (repository root):
    python3 -I tools/retire_cases.py "reason" <suite folder> [<suite folder> ...] --ids ID [ID ...]            dry run
    python3 -I tools/retire_cases.py "reason" <suite folder> [...] --ids ID [ID ...] --apply                   writes
Example (the two cases of 2026-10-25, in the installed suite and in the generated source, so that a rebuild keeps them out):
    python3 -I tools/retire_cases.py "Makaveli is an alias of Tupac Shakur, the claim is arguably true (owner, 2026-10-25)" \\
        /home/maldun/prog/Python/MIA/eval/suites/verdicts_vitaminc /home/maldun/prog/Python/MIA/data/eval-external/suites/verdicts_vitaminc \\
        --ids vc-5ece9462c9e77c0008466cba_2 vc-5ece9462c9e77c0008466cba_3 --apply
Refuses folders ending in .holdout; changes nothing if an id is missing in a folder; safe to repeat. Prints only ids and counts."""
import json
import pathlib
import sys


def main(reason, folders, ids, apply):
    pending = []
    for folder in folders:
        if folder.rstrip("/").endswith(".holdout"):
            print("refused: %s is a holdout suite" % folder)
            return 1
        path = pathlib.Path(folder) / "cases.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line.strip()]
        by_id = {row["id"]: row for row in rows}
        missing = [i for i in ids if i not in by_id]
        if missing:
            print("%s: no case %s; nothing written" % (folder, ", ".join(missing)))
            return 1
        for case_id in ids:
            row = by_id[case_id]
            done = "retired" in row["tags"] and "ambiguous" in row["tags"]
            print("%-60s %-34s %s" % (folder[-60:], case_id, "already retired" if done else ("retired" if apply else "would be retired")))
            if apply and not done:
                row["tags"] = sorted(set(row["tags"]) | {"ambiguous", "retired"})
                row["note"] = (row["note"] + " | " if row.get("note") else "") + "retired: " + reason
        pending.append((path, rows))
    if apply:
        for path, rows in pending:
            path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf8")
    print("done" if apply else "dry run: nothing written")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--ids" not in args or len(args) < 4:
        print(__doc__)
        sys.exit(2)
    split = args.index("--ids")
    reason, folders = args[0], [a for a in args[1:split]]
    ids = [a for a in args[split + 1:] if a != "--apply"]
    sys.exit(main(reason, folders, ids, "--apply" in args))
