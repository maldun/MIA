"""Tags the five smoke cases of the number gate (specs/number-gate/test-spec.md, SMOKE-GATE-001) with `smoke` in the dev suites.

Usage (repository root; the suites of the main checkout):
    python3 -I tools/tag_smoke_cases.py /home/maldun/prog/Python/MIA/eval/suites            dry run: shows what it would tag
    python3 -I tools/tag_smoke_cases.py /home/maldun/prog/Python/MIA/eval/suites --apply     writes the tag
The cases were chosen from the dev runs of T-06: same answer in both runs and both styles. Change CASES to choose others. Only dev folders are touched (a suite folder
ending in .holdout is refused), only the field `tags` of the named cases changes, and running it twice changes nothing more. Prints only counts and ids."""
import json
import pathlib
import sys

CASES = {"verdicts_vitaminc": ["vc-5ed7ad02c9e77c00084a6f6d_1", "vc-5ed50882c9e77c000848f869_2"],
         "verdicts_wikidata": ["wd-Q1049868-tower-height-true", "wd-Q180558-river-length-false", "wd-Q110994774-bridge-year-true"]}


def main(suites, apply):
    problems, pending = 0, []
    for suite, ids in CASES.items():
        if suite.endswith(".holdout"):
            print("refused: %s is a holdout suite" % suite)
            return 1
        path = pathlib.Path(suites) / suite / "cases.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line.strip()]
        by_id = {row["id"]: row for row in rows}
        for case_id in ids:
            if case_id not in by_id:
                print("%s: no case %s" % (suite, case_id))
                problems += 1
                continue
            row = by_id[case_id]
            if "split:dev" not in row.get("tags", []):
                print("%s: %s is not a dev case; not tagged" % (suite, case_id))
                problems += 1
                continue
            has = "smoke" in row["tags"]
            print("%-18s %-34s %s" % (suite, case_id, "already tagged" if has else ("tagged" if apply else "would be tagged")))
            if apply and not has:
                row["tags"] = sorted(set(row["tags"]) | {"smoke"})
        pending.append((path, rows))
    if problems:
        print("%d problem(s): nothing written" % problems)
        return 1
    if apply:
        for path, rows in pending:
            path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf8")
    print("done" if apply else "dry run: nothing written")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--apply"]
    if len(args) != 1:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args[0], "--apply" in sys.argv))
