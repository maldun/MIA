"""The stability of saved runs with repeats (REQ-STAB-001, REQ-STAB-002): the share of cases whose repeats agree in status and facts, its Wilson 95 % interval, the unstable cases.

Usage (repository root):
    python3 -I tools/stability_report.py <run.jsonl> [<run.jsonl> ...]
    python3 -I tools/stability_report.py --latest <variant> [--results data/eval]     the newest run of each suite for a variant name (needs the suites of the run's name)
A case counts only when it has at least two repeats. Records without a `facts` field compare by status alone (the gate and the styles give a verdict, a lookup gives facts).
Prints counts and case ids only."""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import metrics  # noqa: E402


def load(path):
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    return rows[0], [r for r in rows[1:] if "case" in r]


def report(path):
    header, records = load(path)
    result = metrics.stability_report(records)
    name = "%s / %s" % (header.get("suite"), header.get("variant", {}).get("name"))
    print("%-48s repeats %s, cases with repeats %3d, stable %5.1f %% (95 %% interval %2.0f to %2.0f %%), unstable %d" % (
        name, header.get("repeats"), result["n"], 100 * result["share"], 100 * result["low"], 100 * result["high"], len(result["unstable"])))
    for case in result["unstable"][:12]:
        print("     unstable:", case)
    return result


def main(args):
    if args and args[0] == "--latest":
        variant = args[1]
        folder = args[args.index("--results") + 1] if "--results" in args else os.path.join(os.path.dirname(HERE), "data", "eval")
        found = {}
        for path in sorted(glob.glob(os.path.join(folder, "*__%s__*.jsonl" % variant))):
            found[os.path.basename(path).split("__")[0]] = path
        paths = list(found.values())
    else:
        paths = args
    if not paths:
        print(__doc__)
        return 2
    for path in paths:
        report(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
