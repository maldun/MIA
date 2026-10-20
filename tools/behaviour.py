"""
The speech rules (behaviour.py) from the command line, and what the run log has recorded about them. Run with the MIA virtualenv from the MIA folder:

  python tools/behaviour.py rules                      the rules with severity, what is wanted, and a bad and a good example
  python tools/behaviour.py check "text"               the violations of a text (or --file path, or the text on stdin with -)
  python tools/behaviour.py repair "text"              the text as the silent repair would make it, and what remains
  python tools/behaviour.py report [--recent n]        from the run log: hits per rule (penalties, rewards, runs), the share of chat answers with a hit, the latest hits

The run log folder comes from setup_cfg.json (runs_dir).
"""
import argparse
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)
from MIA.config import default_path as default_config  # noqa: E402

from MIA import behaviour  # noqa: E402
from MIA.run_log import RunLog  # noqa: E402


def own(cfg, key, default):
    path = cfg.get(key, default)
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def text_of(args):
    if args.file:
        with open(args.file, encoding="utf-8") as fp:
            return fp.read()
    if args.text == ["-"]:
        return sys.stdin.read()
    return " ".join(args.text)


def show_rules():
    for rule in behaviour.describe():
        print("%-28s %-6s %s%s" % (rule["name"], rule["severity"], rule["wanted"], "" if rule["repairable"] else "  (cannot be repaired by code)"))
        print("    bad : %s\n    good: %s" % (rule["bad"][0] if rule["bad"] else "-", rule["good"][0] if rule["good"] else "-"))


def show_check(text):
    found = behaviour.check_text(text)["violations"]
    if not found:
        print("no violations")
    for v in found:
        print("%-28s at %d-%d  %r  (%s)" % (v["rule"], v["start"], v["end"], v["match"][:60], v["detail"]))
    return 1 if found else 0


def show_repair(text):
    result = behaviour.repair_text(text)
    print(result["text"])
    if result["fixed"]:
        print("\nfixed: %s" % ", ".join(result["fixed"]))
    if result["remaining"]:
        print("remaining (a retry has to name them): %s" % ", ".join(result["remaining"]))
    return 1 if result["remaining"] else 0


def show_report(log, recent):
    runs = log.read()
    answers = [r for r in runs if r.get("task") == "chat" or r.get("skill") == "chat"]
    with_hits = [r for r in answers if r.get("signals")]
    print("%d runs in the log, %d chat answers, %d of them with at least one hit%s" % (len(runs), len(answers), len(with_hits),
                                                                              " (%.0f %%)" % (100.0 * len(with_hits) / len(answers)) if answers else ""))
    table = log.signals_by_rule()
    if not table:
        print("\nno signals recorded yet: they are written for every chat answer once MIA runs with this version")
        return
    print("\n%-28s %9s %7s %5s" % ("rule", "penalties", "rewards", "runs"))
    for rule, row in sorted(table.items(), key=lambda kv: -kv[1]["penalty"]):
        print("%-28s %9d %7d %5d" % (rule, row["penalty"], row["reward"], row["runs"]))
    latest = [(r["created"], s) for r in runs for s in r.get("signals", [])]
    print("\nthe latest hits:")
    for created, s in sorted(latest, key=lambda x: x[0])[-recent:]:
        print("  %s  %-28s %r" % (created, s["rule"], s.get("text", "")))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["rules", "check", "repair", "report"])
    parser.add_argument("text", nargs="*")
    parser.add_argument("--file")
    parser.add_argument("--recent", type=int, default=10)
    parser.add_argument("--cfg", default=default_config(REPO))
    args = parser.parse_args()
    if args.command == "rules":
        show_rules()
        return 0
    if args.command in ("check", "repair"):
        text = text_of(args)
        return show_check(text) if args.command == "check" else show_repair(text)
    with open(args.cfg) as fp:
        cfg = json.load(fp)
    show_report(RunLog(own(cfg, "runs_dir", "data/runs")), args.recent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
