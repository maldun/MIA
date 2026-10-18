"""
Browse and manage the library of nodes and pipelines (ui/REQUIREMENTS_CORE.md 4a). Run with the MIA virtualenv from the MIA folder:

  python tools/library.py list [nodes|pipelines]          all entries with status
  python tools/library.py search web fetch                entries whose id, title, description or tags contain the words (--tag t, --kind k, --nodes)
  python tools/library.py show check.quote_in_source@1    the entry as JSON (without a version: the one a reference would use)
  python tools/library.py validate                        problems of all files and references (exit code 1 when there are some)
  python tools/library.py reindex                         rebuild the SQLite index from the files
  python tools/library.py stats [ref]                     statistics from the run log (recomputed first)
  python tools/library.py select --tag verify --applies claim_type=numeric --max-seconds 30 [--nodes]   what a selection would answer, with the reasons
  python tools/library.py promote check.quote_in_source@1 tested --note "passed the 30 cases"        status: draft, tested, trusted, retired
  python tools/library.py diff check.x@1 check.x@2        what changed between two versions
  python tools/library.py used-by tool.web_search@1        the pipelines that use a node version

The paths come from setup_cfg.json (library_dir, user_library_dir, library_index, runs_dir).
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

from MIA.library import Library, LibraryError, ref_of  # noqa: E402
from MIA.run_log import RunLog  # noqa: E402


def own(cfg, key, default):
    path = cfg.get(key, default)
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def line(entry):
    kind = entry.get("kind", "pipeline")
    return "%-34s %-9s %-8s %s" % (ref_of(entry["id"], entry["version"]), kind, entry["status"], entry["title"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["list", "search", "show", "validate", "reindex", "stats", "select", "promote", "diff", "used-by"])
    parser.add_argument("words", nargs="*")
    parser.add_argument("--cfg", default=os.path.join(REPO, "setup_cfg.json"))
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--kind")
    parser.add_argument("--nodes", action="store_true", help="search / select among nodes (default: pipelines)")
    parser.add_argument("--applies", action="append", default=[], help="name=value, for select")
    parser.add_argument("--max-seconds", type=float)
    parser.add_argument("--task")
    parser.add_argument("--note", default="")
    args = parser.parse_intermixed_args()

    with open(args.cfg) as fp:
        cfg = json.load(fp)
    library = Library(own(cfg, "library_dir", "library"), own(cfg, "user_library_dir", "data/library"), own(cfg, "library_index", "data/library.sqlite"))
    entry_type = "node" if args.nodes else "pipeline"
    try:
        if args.command == "list":
            which = args.words[0].rstrip("s") if args.words else None
            for kind in ("node", "pipeline"):
                if which in (None, kind):
                    print("--- %ss" % kind)
                    for entry in library.entries(kind):
                        print(line(entry))
        elif args.command == "search":
            for kind in (("node",) if args.nodes else ("node", "pipeline")):
                for entry in library.search(" ".join(args.words) or None, kind, tags=args.tag, kind=args.kind):
                    print(line(entry))
        elif args.command == "show":
            ref = args.words[0]
            name = ref.partition("@")[0]
            entry = library.resolve(ref, "pipeline", allow_draft=True) if library.versions(name, "pipeline") else library.resolve(ref, "node", allow_draft=True)
            print(json.dumps({k: v for k, v in entry.items() if not k.startswith("_")}, indent=1, ensure_ascii=False))
            print("\nfile: %s (%s), status %s%s" % (entry["_path"], entry["_source"], entry["status"], " - " + entry["_status_note"] if entry.get("_status_note") else ""))
            if "kind" in entry:
                print("used by: %s" % (", ".join(library.used_by(ref_of(entry["id"], entry["version"]))) or "no pipeline"))
        elif args.command == "validate":
            for path, problem in library.errors.items():
                print("PROBLEM %s: %s" % (os.path.relpath(path, REPO), problem))
            for warning in library.warnings:
                print("WARNING %s" % warning)
            print("%d nodes, %d pipelines, %d problems" % (len(library.entries("node")), len(library.entries("pipeline")), len(library.errors)))
            sys.exit(1 if library.errors else 0)
        elif args.command == "reindex":
            if os.path.exists(library.index_path):
                os.remove(library.index_path)
            library.reload()
            library.recompute_stats(RunLog(own(cfg, "runs_dir", "data/runs")).read())
            print("index rebuilt: %s" % library.index_path)
        elif args.command == "stats":
            library.recompute_stats(RunLog(own(cfg, "runs_dir", "data/runs")).read())
            refs = args.words or [ref_of(e["id"], e["version"]) for kind in ("pipeline", "node") for e in library.entries(kind)]
            for ref in refs:
                s = library.stats(ref, args.task)
                if s:
                    print("%-34s %4d runs, %4d ok, %4d errors, %.2f s per run" % (ref, s["runs"], s["ok"], s["errors"], s["seconds"]))
                elif args.words:
                    print("%-34s no runs yet" % ref)
        elif args.command == "select":
            applies = dict(item.split("=", 1) for item in args.applies)
            library.recompute_stats(RunLog(own(cfg, "runs_dir", "data/runs")).read())
            result = library.select(entry_type, tags=args.tag, applies_to=applies, max_seconds=args.max_seconds, task=args.task)
            for c in result["selected"]:
                print("%-34s score %.2f  %s" % (c["ref"], c["score"], "; ".join(c["why"])))
            for d in result["dropped"]:
                print("dropped  %-30s %s" % (d["ref"], d["reason"]))
        elif args.command == "promote":
            ref, status = args.words[0], args.words[1]
            library.set_status(ref, status, args.note)
            print("%s is now %s (decision kept in %s)" % (ref, status, library.status_file))
        elif args.command == "diff":
            print(library.diff(args.words[0], args.words[1]))
        elif args.command == "used-by":
            for ref in library.used_by(args.words[0]):
                print(ref)
    except (LibraryError, IndexError) as exc:
        print("error: %s" % (exc if isinstance(exc, LibraryError) else "missing argument (see --help)"))
        sys.exit(1)


if __name__ == "__main__":
    main()
