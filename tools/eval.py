"""
The evaluation harness on the command line (ui/REQUIREMENTS_CORE.md 9). Run with the MIA virtualenv from the MIA folder:

  python tools/eval.py list                                   the suites and how many cases they have
  python tools/eval.py run hard_checks                        run a suite (no model needed for the hard checks), print the report, save the run in data/eval/
  python tools/eval.py run computable --repeats 3             the same case 3 times: shows how stable the model is
  python tools/eval.py run computable --variant light --model light
  python tools/eval.py run computable --variant full --model gemma4:26b --pipeline verify.computable@1
  python tools/eval.py run hard_checks --tag numeric --limit 10        only some cases
  python tools/eval.py report hard_checks                     the report of the newest saved run of a suite (or of a file)
  python tools/eval.py compare data/eval/a.jsonl data/eval/b.jsonl     the same cases under two variants, with the exact sign test
  python tools/eval.py compare computable light full          the newest runs of two variants of a suite
  python tools/eval.py cases hard_checks --tag trap           show the cases

Without a name the variant is called "default". The variant options (--skill, --pipeline, --model) change what runs; everything else stays the same, so two runs can be compared.
"""
import argparse
import json
import os
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)
from MIA.config import default_path as default_config  # noqa: E402

from MIA import harness  # noqa: E402
from MIA.core import Core  # noqa: E402
from MIA.library import Library  # noqa: E402
from MIA.sandbox import create_router  # noqa: E402

SUITES = os.path.join(REPO, "eval", "suites")


def own(cfg, key, default):
    path = cfg.get(key, default)
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def build_core(cfg, need_model, need_sandbox):
    model = None
    if need_model:
        from ollama import Client
        from MIA.pipeline_model import OllamaModel
        profiles = {"full": (cfg["version"], cfg.get("llm_options")), "light": (cfg.get("version_light"), cfg.get("llm_options_light"))}
        current = profiles["light"] if cfg.get("default_profile") == "light" and cfg.get("version_light") else profiles["full"]
        client = Client(host="http://%s:%s" % (cfg.get("address", "localhost"), cfg.get("port", 11434)))
        model = OllamaModel(client, lambda p: profiles.get(p) if profiles.get(p, (None,))[0] else None, lambda: current, keep_alive=cfg.get("keep_alive"))
    work = tempfile.mkdtemp(prefix="mia-eval-")
    library = Library(own(cfg, "library_dir", "library"), None, os.path.join(work, "library.sqlite"))
    return Core(own(cfg, "skills_dir", "skills"), library, work, model=model, sandbox=create_router(cfg) if need_sandbox else None)


def show_progress(done, total, record):
    mark = "ok " if (record["expect"] is not None and harness.metrics.normalize_status(record["status"]) == harness.metrics.normalize_status(record["expect"])) or \
                    (record["expect"] is None and harness.metrics.is_right(record)) else "-- "
    print("  [%3d/%d] %s%-28s %-14s %.1fs" % (done, total, mark, record["case"], record["status"], record["seconds"]), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["list", "run", "report", "compare", "cases"])
    parser.add_argument("args", nargs="*")
    parser.add_argument("--cfg", default=default_config(REPO))
    parser.add_argument("--variant", default="default")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--only", help="comma separated case ids")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--skill")
    parser.add_argument("--pipeline")
    parser.add_argument("--model")
    parser.add_argument("--results", default=None, help="folder of saved runs (default: data/eval)")
    parser.add_argument("--no-save", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_intermixed_args()
    with open(args.cfg) as fp:
        cfg = json.load(fp)
    results = args.results or own(cfg, "eval_dir", "data/eval")

    def resolve_run(name):
        if os.path.isfile(name):
            return harness.load_run(name)
        path = harness.latest_run(results, name.split(":")[0], name.split(":")[1] if ":" in name else None)
        if not path:
            sys.exit("no saved run for '%s' in %s" % (name, results))
        return harness.load_run(path)

    if args.command == "list":
        for suite in harness.list_suites(SUITES):
            if isinstance(suite, Exception):
                print("PROBLEM %s" % suite)
                continue
            tags = {}
            for case in suite.cases:
                for tag in case.get("tags", []):
                    tags[tag] = tags.get(tag, 0) + 1
            print("%-14s %3d cases  target %s%s\n   %s\n   tags: %s" % (suite.name, len(suite.cases), suite.target["kind"], " (needs a model)" if suite.target["kind"] in ("pipeline", "research", "plan") else "",
                                                                       suite.description[:150], ", ".join("%s %d" % t for t in sorted(tags.items()))))
        return
    if args.command == "cases":
        suite = harness.load_suite(os.path.join(SUITES, args.args[0]))
        for case in suite.select(args.tag or None, args.only.split(",") if args.only else None, args.limit):
            print("%-28s %-30s truth=%-5s expect=%-14s %s" % (case["id"], ",".join(case.get("tags", [])), case.get("truth"), case.get("expect"), case.get("note", "")))
        return
    if args.command == "report":
        print(harness.format_report(resolve_run(args.args[0])))
        return
    if args.command == "compare":
        a, b = args.args[0], args.args[1]
        if len(args.args) == 3:                                     # compare <suite> <variant a> <variant b>
            a, b = "%s:%s" % (args.args[0], args.args[1]), "%s:%s" % (args.args[0], args.args[2])
        print(harness.format_compare(resolve_run(a), resolve_run(b)))
        return

    suite = harness.load_suite(os.path.join(SUITES, args.args[0]))
    need_model = suite.target["kind"] in ("pipeline", "research", "plan") or (suite.target["kind"] == "extraction" and bool(args.skill or args.pipeline))
    core = build_core(cfg, need_model, need_sandbox=need_model)
    variant = {"name": args.variant}
    for key in ("skill", "pipeline", "model"):
        if getattr(args, key):
            variant[key] = getattr(args, key)
    print("running %s (%d cases x %d) as variant '%s' ...\n" % (suite.name, len(suite.select(args.tag or None, args.only.split(",") if args.only else None, args.limit)), args.repeats, args.variant))
    run = harness.Harness(core).run(suite, variant, args.repeats, args.tag or None, args.only.split(",") if args.only else None, args.limit, None if args.quiet else show_progress)
    print("\n" + harness.format_report(run))
    if not args.no_save:
        print("\nsaved: %s" % run.save(results))


if __name__ == "__main__":
    main()
