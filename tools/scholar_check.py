#!/usr/bin/env python
"""
Try the scholarly sources from the command line (research phase 1, ui/REQUIREMENTS_RESEARCH.md): search, de-duplicate, apply a date cut-off, look up retraction
notices and show the trust class of every work. Only the query leaves the machine; the requests are in the web log (data/runs).

  python tools/scholar_check.py "electrical network squared square" --until 1999-12-31
  python tools/scholar_check.py "fish oil Raynaud" --backends pubmed,crossref --limit 5 --retraction
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import scholar as S                                      # noqa: E402
import source_trust as T                                 # noqa: E402
from config import default_path                          # noqa: E402


def load_cfg():
    with open(default_path(ROOT), encoding="utf-8") as fp:          # this machine's setup_cfg.json, else the example
        return json.load(fp)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query")
    parser.add_argument("--until", help="cut-off date (YYYY-MM-DD): only works published up to then")
    parser.add_argument("--since")
    parser.add_argument("--limit", type=int, default=5, help="results per source")
    parser.add_argument("--backends", help="comma separated: %s" % ", ".join(S.BACKENDS))
    parser.add_argument("--retraction", action="store_true", help="ask Crossref for retraction notices of every DOI")
    args = parser.parse_args(argv)
    cfg = load_cfg()
    if args.backends:
        cfg["scholar_backends"] = [b.strip() for b in args.backends.split(",") if b.strip()]
    scholar, http = S.build_scholar(cfg, runs_dir=os.path.join(ROOT, cfg.get("runs_dir", "data/runs")))
    trust = T.build_trust(cfg)
    result = scholar.search(args.query, limit=args.limit, until=args.until, since=args.since, check_retraction=args.retraction)
    for work in result["works"]:
        t = trust.for_work(work, as_of=args.until)
        state = S.retraction_state(work, args.until)
        print("%-4s %-8s %s  [%s]" % (work["date"] or "?", t["class"], work["title"][:90], "+".join(work["sources"])))
        print("     trust %.2f%s  retraction: %s%s  doi: %s" % (t["score"], "" if t["usable"] else " (NOT USABLE)", state["status"], " (unconfirmed hint)" if state["unconfirmed"] else "", work["doi"] or "-"))
    print("\n%d works, %d merged duplicates, %d dropped by the cut-off, requests: %d" % (len(result["works"]), result["merged"], len(result["dropped"]), http.requests_made))
    for d in result["dropped"][:5]:
        print("  dropped: %s (%s)" % (d["title"][:60], d["reason"]))
    for name, message in result["errors"].items():
        print("  ERROR %s: %s" % (name, message))
    return 0


if __name__ == "__main__":
    sys.exit(main())
