"""Agreement between your labels and the benchmark labels of the audit sample.

Usage (repository root):
    python3 -I tools/label_agreement.py data/eval-external/audit/sample_sheet.csv data/eval-external/audit/key.json

Fill the column "label (true / false / unknown)" of the sheet first, without opening key.json. Rows you leave empty
are skipped. It prints the agreement, Cohen's kappa, the confusion table and the ids where you and the benchmark
differ, and writes them to ambiguous.txt next to the sheet: tag those cases `ambiguous` (they stay out of decisions)
or rewrite them. Standard library only."""
import csv, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from make_external_suite import cohen_kappa     # noqa: E402  (same formula, tested there)


def main(sheet, key_file):
    key = json.load(open(key_file, encoding="utf8"))
    mine, bench, ids = [], [], []
    with open(sheet, newline="", encoding="utf8") as f:
        rows = list(csv.reader(f))
    for r in rows[1:]:
        label = r[3].strip().lower() if len(r) > 3 else ""
        if label in ("true", "false", "unknown") and r[0] in key:
            mine.append(label)
            bench.append(key[r[0]]["truth"])
            ids.append(key[r[0]]["case"])
    if not ids:
        print("no labelled rows found")
        return 1
    agree = sum(1 for a, b in zip(mine, bench) if a == b)
    print("labelled rows: %d, agreement: %d (%.0f %%), Cohen's kappa: %.2f" % (len(ids), agree, 100 * agree / len(ids), cohen_kappa(mine, bench)))
    cats = ["true", "false", "unknown"]
    print("rows = benchmark, columns = you   " + "  ".join("%7s" % c for c in cats))
    for c in cats:
        print("%-31s" % c + "  ".join("%7d" % sum(1 for a, b in zip(mine, bench) if b == c and a == d) for d in cats))
    diff = [i for i, a, b in zip(ids, mine, bench) if a != b]
    path = pathlib.Path(sheet).with_name("ambiguous.txt")
    path.write_text("\n".join(diff) + ("\n" if diff else ""), encoding="utf8")
    print("differing ids (%d) written to %s" % (len(diff), path))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
