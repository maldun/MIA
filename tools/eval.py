"""
The evaluation harness on the command line (ui/REQUIREMENTS_CORE.md 9). Run with the MIA virtualenv from the MIA folder:

  python tools/eval.py list                                   the suites and how many cases they have
  python tools/eval.py run hard_checks --pin MP-light         run a suite (no model needed for the hard checks), print the report, save the run in data/eval/
  python tools/eval.py run computable --pin MP-light --repeats 3             the same case 3 times: shows how stable the model is
  python tools/eval.py run computable --pin MP-light --variant c1 --pipeline verify.computable@1
  python tools/eval.py run hard_checks --pin MP-light --tag numeric --limit 10        only some cases
  python tools/eval.py run verdicts --pin MP-light --repeats 3 --variant stored --stored      the skill runs from its graph saved into a throw-away store (REQ-WFM-110 to 114)
  python tools/eval.py run verdicts_vitaminc --pipeline verify.single@1 --pin MP-light --sample 100 --repeats 1     seeded sample, pinned model setting
  python tools/eval.py report hard_checks                  the report of the newest saved run of a suite (or of a file)
  python tools/eval.py compare data/eval/a.jsonl data/eval/b.jsonl     the same cases under two variants, with the exact sign test
  python tools/eval.py compare computable light full          the newest runs of two variants of a suite
  python tools/eval.py cases hard_checks --tag trap           show the cases

Holdout suites (*.holdout) are left out of list and refused by cases, run, report and compare (also their saved runs) unless --holdout is given: they are for Verify only.
Every run needs --pin (REQ-EVL-004), and the pin decides the model (--model is refused next to it, D-166); a suite of kind "workflow" runs through IF-105 on the workflows of the app's storage.
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

from MIA import harness, pipeline_graph, skill_converter  # noqa: E402
from MIA.core import Core  # noqa: E402
from MIA.events import environment, model_digests  # noqa: E402
from MIA.graph_model import GraphModel  # noqa: E402
from MIA.library import Library  # noqa: E402
from MIA.run_workflow import WorkflowRuns  # noqa: E402
from MIA.sandbox import create_router  # noqa: E402
from MIA.storage import Storage  # noqa: E402
from MIA.storage_files import FileBackend  # noqa: E402
from MIA.workflow_library import WorkflowLibrary  # noqa: E402

SUITES = os.environ.get("MIA_SUITES") or os.path.join(REPO, "eval", "suites")       # a worktree finds the labelled suites of the main checkout this way
# the model pins of specs/number-gate/eval-spec.md ("Model pins"); a change of a pin is an amendment there first
PINS = {"MP-light": {"name": "gemma4:12b-it-qat", "digest": "sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3", "seed": 7, "temperature": 0, "num_ctx": 8192}}


def pin_record(pin_id):
    """the pin the harness gets: the entry of PINS with its id, which IF-105 takes as `model_pin` (the name is the model tag)"""
    return dict(PINS[pin_id], id=pin_id)


def own(cfg, key, default):
    path = cfg.get(key, default)
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def build_core(cfg, need_model, need_sandbox):
    model = None
    if need_model:
        from MIA.pipeline_model import OllamaModel
        profiles = {"full": (cfg["version"], cfg.get("llm_options")), "light": (cfg.get("version_light"), cfg.get("llm_options_light"))}
        current = profiles["light"] if cfg.get("default_profile") == "light" and cfg.get("version_light") else profiles["full"]
        client = model_client(cfg)
        model = OllamaModel(client, lambda p: profiles.get(p) if profiles.get(p, (None,))[0] else None, lambda: current, keep_alive=cfg.get("keep_alive"))
    work = tempfile.mkdtemp(prefix="mia-eval-")
    library = Library(own(cfg, "library_dir", "library"), None, os.path.join(work, "library.sqlite"))
    return Core(own(cfg, "skills_dir", "skills"), library, work, model=model, sandbox=create_router(cfg) if need_sandbox else None)


def core_needs(kind, with_pipeline):
    """(a model, a sandbox) for the core of a run: the digest step calls the pinned model and has no tool, so no sandbox (G-V3.CHAT T-05)"""
    need_model = kind in ("pipeline", "research", "plan", "workflow", "digest") or (kind == "extraction" and with_pipeline)
    return need_model, need_model and kind != "digest"


def model_client(cfg):
    from ollama import Client
    return Client(host="http://%s:%s" % (cfg.get("address", "localhost"), cfg.get("port", 11434)))


def build_platform(cfg, core):
    """IF-105 for workflow suites (REQ-EVL-011, D-164): the runner of the app over the workflow library in the app's storage, with the pins of
    PINS by id; a pin runs only when the model server holds its digest (asked at the first run, never a fallback to another model)"""
    library = WorkflowLibrary(Storage(FileBackend(own(cfg, "accounts_dir", "data/db"))))

    def held():
        return {d["name"]: d["digest"] for d in model_digests(model_client(cfg), [p["name"] for p in PINS.values()]) if d["digest"]}
    return WorkflowRuns(library, core, pins={i: {"name": p["name"], "digest": p["digest"]} for i, p in PINS.items()}, held=held)


def make_harness(cfg, core, stored=None):
    if stored:
        return StoredHarness(core, stored, platform=build_platform(cfg, core))
    return harness.Harness(core, platform=build_platform(cfg, core))


def store_skill_graph(core, skill_name, folder):
    """saves the skill's graph, converted and bound as the graph path converts it in memory (skill_converter.run_converted), through CORE's save path
    into a new files store in `folder`, and gives that store to the core (REQ-RUN-042, D-476); returns (graph ID, version)"""
    skill = core.skills.get(skill_name)
    if skill is None:
        sys.exit("there is no skill '%s'" % skill_name)
    pipeline = core.library.resolve(skill["pipeline"], "pipeline")
    nodes = skill_converter._latest_nodes(os.path.join(core.library.shipped_dir, "nodes"))
    found = pipeline_graph.convert({k: v for k, v in pipeline.items() if not k.startswith("_")}, nodes, (skill.get("budget") or {}).get("seconds", 300))
    if found["graph"] is None:
        sys.exit("%s cannot be converted, so it has no stored graph: %s" % (skill_name, found["refused"]))
    store = GraphModel(Storage(FileBackend(folder)), "eval")
    saved = store.save_graph(pipeline_graph.bind_skill(found["graph"], nodes, skill, None))
    if not saved.saved:
        sys.exit("the graph of %s was not saved: %s" % (skill_name, saved.rules or saved.rule))
    core.graph_store = store
    return skill_converter.pipeline_ref(pipeline), saved.version


class StoredHarness(harness.Harness):
    """the harness on the stored-graph path (T-04): a skill runs through Core.run with the store, as the app runs it (REQ-RUN-042), on the model of the pin
    as on the converted path; `stored` = (graph ID, version) goes into the run header"""

    def __init__(self, core, stored, **kwargs):
        super().__init__(core, **kwargs)
        self.stored = stored

    def run(self, *args, **kwargs):
        run = super().run(*args, **kwargs)
        run.header["stored_graph"] = {"path": "Core graph_store (REQ-RUN-042)", "graph": self.stored[0], "version": self.stored[1]}
        return run

    def _run_skill(self, skill, inputs, suite, variant, tools=None):
        if not variant.get("stored"):
            return super()._run_skill(skill, inputs, suite, variant, tools)
        model = self.core.runner.model
        self.core.runner.model = harness._PinnedChat(model, self.pin)
        try:
            result = self.core.run(skill["name"], inputs, started_by="command", **({"tools": tools} if tools else {}))
        finally:
            self.core.runner.model = model
        # the core falls back to the old runner when it finds no stored graph or cannot convert: that answer is not the one measured here
        if not result.cost.get("converted"):
            raise harness.SuiteError("%s did not run from the stored graph %s (the core ran the old runner)" % (skill["name"], self.stored[0]))
        return result


def is_holdout(name):
    return name.endswith(".holdout")


def open_suite(name, holdout):
    """a suite by name; a holdout suite only with --holdout (REQ-EVL-002, D-164: the holdout is for Verify), refused before anything of it is read"""
    if not name or name in (".", "..") or "/" in name or os.sep in name:
        sys.exit("'%s' is not a suite name (a suite is a folder name in %s)" % (name, SUITES))
    if is_holdout(name) and not holdout:
        sys.exit("%s is a holdout suite: only with --holdout (Verify)" % name)
    if not os.path.isfile(os.path.join(SUITES, name, "suite.json")):
        known = sorted(n for n in os.listdir(SUITES) if os.path.isfile(os.path.join(SUITES, n, "suite.json")) and (holdout or not is_holdout(n)))
        sys.exit("no suite '%s' (there are: %s)" % (name, ", ".join(known) or "none"))
    try:
        suite = harness.load_suite(os.path.join(SUITES, name))
    except harness.SuiteError as exc:
        sys.exit(str(exc))
    if is_holdout(suite.name) and not holdout:
        sys.exit("%s is the holdout suite %s: only with --holdout (Verify)" % (name, suite.name))
    return suite


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
    parser.add_argument("--converted", action="store_true", help="run the skill on the graph path (skill_converter.run_converted), for the targets extraction, pipeline, plan and research (REQ-WFM-110 to 114)")
    parser.add_argument("--stored", action="store_true", help="run the skill from its graph saved into a throw-away store, through Core with graph_store= (REQ-WFM-110 to 114, G-V4.GRAPHAPI.RUN T-04); the header names the graph and its version")
    parser.add_argument("--model", help="refused by run: the model of a run is the one of --pin (D-166)")
    parser.add_argument("--pin", choices=sorted(PINS), help="model pin of eval-spec.md, required by run: its seed and temperature go to every model call and the pin is written to the run header")
    parser.add_argument("--sample", type=int, metavar="N", help="a seeded sample of N active cases; the two halves of a pair stay together")
    parser.add_argument("--sample-seed", type=int, default=7, help="seed of --sample (default 7)")
    parser.add_argument("--include-retired", action="store_true", help="also run the cases tagged retired")
    parser.add_argument("--holdout", action="store_true", help="list, show, run, report or compare holdout suites and their runs (*.holdout): for Verify only, never during development")
    parser.add_argument("--results", default=None, help="folder of saved runs (default: data/eval)")
    parser.add_argument("--no-save", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_intermixed_args()
    with open(args.cfg) as fp:
        cfg = json.load(fp)
    results = args.results or own(cfg, "eval_dir", "data/eval")

    def resolve_run(name):
        """a saved run by file or by suite[:variant]; a run of a holdout suite only with --holdout (R5, D-172), by name before it is read"""
        if not os.path.isfile(name):
            suite_name = name.split(":")[0]
            if is_holdout(suite_name) and not args.holdout:
                sys.exit("%s is a holdout suite: its runs only with --holdout (Verify)" % suite_name)
            name = harness.latest_run(results, suite_name, name.split(":")[1] if ":" in name else None)
            if not name:
                sys.exit("no saved run for '%s' in %s" % (suite_name, results))
        run = harness.load_run(name)
        if is_holdout(run.header["suite"]) and not args.holdout:
            sys.exit("%s is a run of the holdout suite %s: only with --holdout (Verify)" % (name, run.header["suite"]))
        return run

    if args.command == "list":
        for suite in harness.list_suites(SUITES, holdout=args.holdout):
            if isinstance(suite, Exception):
                print("PROBLEM %s" % suite)
                continue
            if is_holdout(suite.name) and not args.holdout:
                continue
            tags = {}
            for case in suite.cases:
                for tag in case.get("tags", []):
                    tags[tag] = tags.get(tag, 0) + 1
            print("%-14s %3d cases  target %s%s\n   %s\n   tags: %s" % (suite.name, len(suite.cases), suite.target["kind"], " (needs a model)" if suite.target["kind"] in ("pipeline", "research", "plan") else "",
                                                                       suite.description[:150], ", ".join("%s %d" % t for t in sorted(tags.items()))))
        return
    if args.command == "cases":
        suite = open_suite(args.args[0], args.holdout)
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
        run_a, run_b = resolve_run(a), resolve_run(b)
        try:
            harness.require_same_cases(run_a, run_b)                # REQ-EVL-008: only the same cases with the same repeats are compared
        except harness.SuiteError as exc:
            raise SystemExit("not compared: %s" % exc)
        print(harness.format_compare(run_a, run_b))
        return

    if not args.pin:                                                # REQ-EVL-004, D-164: every run records its model pin
        sys.exit("a run needs --pin (%s)" % ", ".join(sorted(PINS)))
    if args.model:                                                  # D-166: the pin decides the model, so the header names what ran
        sys.exit("--model together with --pin: the pin decides the model of a run (%s); drop --model" %
                 ", ".join("%s = %s" % (i, p["name"]) for i, p in sorted(PINS.items())))
    if args.stored and (args.pipeline or args.converted):            # the stored graph is the skill's own graph: another pipeline or the in-memory conversion would not be it
        sys.exit("--stored runs the skill's own graph: drop --pipeline and --converted")
    suite = open_suite(args.args[0], args.holdout)
    need_model, need_sandbox = core_needs(suite.target["kind"], bool(args.skill or args.pipeline or args.stored))
    core = build_core(cfg, need_model, need_sandbox)
    stored = store_skill_graph(core, args.skill or suite.target["skill"], tempfile.mkdtemp(prefix="mia-eval-store-")) if args.stored else None
    variant = {"name": args.variant}
    for key in ("skill", "pipeline", "model"):
        if getattr(args, key):
            variant[key] = getattr(args, key)
    if args.converted:
        variant["converted"] = True
    if args.stored:
        variant["stored"] = True
    only = args.only.split(",") if args.only else None
    if args.sample:
        sampled = [c["id"] for c in harness.sample_cases(suite.select(args.tag or None, only, None, args.include_retired), args.sample, args.sample_seed)]
        if not sampled:
            sys.exit("the sample is empty: %d is too small for the cases or pairs of this suite" % args.sample)
        only = sampled
    count = len(suite.select(args.tag or None, only, args.limit, args.include_retired))
    print("running %s (%d cases x %d) as variant '%s' ...\n" % (suite.name, count, args.repeats, args.variant))
    run = make_harness(cfg, core, stored).run(suite, variant, args.repeats, args.tag or None, only, args.limit, None if args.quiet else show_progress,
                                      pin=pin_record(args.pin), include_retired=args.include_retired)
    run.header["commit"] = environment(root=REPO)["commit"]          # the version of the code that ran (the only one of a code target)
    print("\n" + harness.format_report(run))
    if not args.no_save:
        print("\nsaved: %s" % run.save(results))


if __name__ == "__main__":
    main()
