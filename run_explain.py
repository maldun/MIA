"""
Looking at what a run did (ui/REQUIREMENTS_CORE.md 13d step 5, CG15): the runs of the run log as graphs, in text.

  list                 the runs, newest last: id, task, status, seconds, the question
  show RUN             the summary and the view of the run within a token budget (--budget, --focus)
  explain RUN [NODE]   how a node came about, back to the query; without NODE: every sentence of the draft (or every claim)
  cost RUN             model calls, seconds and tokens per actor
  problems RUN         what is wrong with the log or the graph of the run
  diff RUN RUN         the differences of the graphs of two runs
  export RUN           the view as Graphviz (--format dot) or Mermaid source
  call RUN SEQ         the prompt and the answer of one model call, from the content store
  reproduce RUN        repeat the run offline from the recording and say whether it came out the same

RUN is an id, the start of an id, or "last". No graph viewer or editor exists on purpose: graphs are data in text files (ui/REQUIREMENTS_CORE.md 10).
"""
import argparse
import json
import os
import sys
import tempfile

try:
    from . import context_graph as CG
    from . import events as ev
    from .content_store import ContentStore
    from .run_log import RunLog
except ImportError:  # used as plain script / in tests
    import context_graph as CG
    import events as ev
    from content_store import ContentStore
    from run_log import RunLog

HERE = os.path.dirname(os.path.abspath(__file__))


class ExplainError(Exception):
    pass


def find_run(runs, ref):
    if not runs:
        raise ExplainError("the run log is empty")
    if ref in (None, "last"):
        return runs[-1]
    found = [r for r in runs if r["id"].startswith(ref)]
    if not found:
        raise ExplainError("no run %r (try: list)" % ref)
    if len(found) > 1:
        raise ExplainError("%r is not enough to tell %d runs apart: %s" % (ref, len(found), ", ".join(r["id"] for r in found[:5])))
    return found[0]


def _question(record):
    for e in record.get("events") or []:
        if e.get("kind") == "run_start":
            return (e.get("payload") or {}).get("question") or ""
    return ""


def cmd_list(runs, out, limit=20, **_):
    for record in runs[-limit:]:
        out("%-22s %-10s %-8s %6.1fs  %s" % (record["id"], record.get("task") or "?", record.get("status") or "?", record.get("seconds") or 0.0, ev.excerpt(_question(record), 70)))
    if not runs:
        out("(no runs)")


def cmd_show(record, out, budget=600, focus=None, **_):
    graph = CG.replay_run(record)
    summary = graph.summary()
    out("run %s: %s, %s, %.1fs" % (record["id"], record.get("task"), record.get("status"), record.get("seconds") or 0.0))
    out("graph: %d nodes, %d edges, claims %s, %d open slot(s), %d problem(s)" % (summary["nodes"], summary["edges"], {k: v for k, v in summary["claims"].items() if v}, summary["open_slots"], summary["problems"]))
    if graph.meta["stop"]:
        out("ended: %(reason)s %(detail)s" % {"reason": graph.meta["stop"]["reason"], "detail": graph.meta["stop"].get("detail") or ""})
    text, expanded = CG.render(CG.default_view(graph), budget_tokens=budget, focus=focus)
    out("")
    out(text)


def cmd_explain(record, out, node=None, **_):
    graph = CG.replay_run(record)
    targets = [node] if node else [n["id"] for n in graph.data("draft")] or [n["id"] for n in graph.data("claim")]
    if not targets:
        out("(nothing was claimed in this run)")
        return
    for target in targets:
        if target not in graph.nodes:
            matches = [i for i in graph.nodes if i.startswith(target) or i.endswith(":" + target)]
            if len(matches) != 1:
                raise ExplainError("no node %r%s" % (target, "" if not matches else " (could be: %s)" % ", ".join(matches[:5])))
            target = matches[0]
        for line in graph.explain(target):
            out(line)
        out("")


def cmd_cost(record, out, **_):
    cost = CG.replay_run(record).cost_by_actor()
    if not cost:
        out("(no model calls)")
    for actor, row in sorted(cost.items()):
        out("%-20s %3d calls %8.1fs  tokens in/out %s/%s%s" % (actor, row["calls"], row["seconds"], row["tokens_in"] or "?", row["tokens_out"] or "?", "  (%d invalid)" % row["invalid"] if row["invalid"] else ""))


def cmd_problems(record, out, **_):
    problems = CG.replay_run(record).validate()
    for p in problems:
        out("- " + p)
    out("%d problem(s)" % len(problems))
    return 1 if problems else 0


def cmd_diff(a, b, out, **_):
    differences = CG.diff(CG.replay_run(a), CG.replay_run(b))
    for line in differences:
        out("- " + line)
    out("the same" if not differences else "%d difference(s)" % len(differences))
    return 1 if differences else 0


def cmd_export(record, out, format="dot", **_):
    view = CG.default_view(CG.replay_run(record))
    out(CG.to_dot(view) if format == "dot" else CG.to_mermaid(view))


def cmd_call(record, out, store, seq, **_):
    event = next((e for e in record.get("events") or [] if e.get("seq") == seq and e.get("type") == "model_call"), None)
    if event is None:
        raise ExplainError("event %s is not a model call of this run" % seq)
    p = event["payload"]
    prompt, answer = store.get_json(p["prompt_hash"]), store.get(p["response_hash"])
    out("call %s by %s: %s, %.1fs, %s" % (seq, event.get("actor"), p.get("model") or "model", p.get("seconds") or 0.0, "valid" if p.get("valid") else "did not fit the schema"))
    if prompt is None:
        out("(the texts of this run are not in the store: they were not kept, or have been pruned)")
        return 1
    for message in prompt:
        out("\n[%s]\n%s" % (message.get("role"), message.get("content")))
    out("\n[answer]\n%s" % answer)


def cmd_reproduce(record, out, store, core_factory, **_):
    from reproduce import reproduce
    result = reproduce(record, store, core_factory)
    out("model calls replayed: %d of %d; status %s -> %s" % (result["model_calls"][0], result["model_calls"][1], result["status"][0], result["status"][1]))
    for d in result["divergences"]:
        out("DIVERGED: " + d["what"])
        if d["diff"]:
            out(d["diff"])
    for line in result["differences"]:
        out("- " + line)
    out("reproduced: the same status, the same graph" if result["reproduced"] else "NOT reproduced")
    return 0 if result["reproduced"] else 1


# --- the command line -----------------------------------------------------------------------------------------------------------------------

def _config():
    sys.path.insert(0, HERE)
    from config import default_path
    with open(default_path(HERE), encoding="utf-8") as fp:
        return json.load(fp)


def _path(cfg, key, default):
    value = cfg.get(key, default)
    return value if os.path.isabs(value) else os.path.join(HERE, value)


def make_core_factory(cfg):
    """a Core with the skills and the library of this installation, a throw-away run log and index, for the reproduction"""
    def factory(model, tools):
        from core import Core
        from library import Library
        scratch = tempfile.mkdtemp(prefix="mia-reproduce-")
        library = Library(_path(cfg, "library_dir", "library"), os.path.join(scratch, "user_library"), os.path.join(scratch, "library.sqlite"))
        return Core(_path(cfg, "skills_dir", "skills"), library, scratch, model=model, tools=tools)
    return factory


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-dir", help="the folder of the run log (default: runs_dir of the configuration)")
    parser.add_argument("--store-dir", help="the content store (default: store_dir of the configuration)")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("list")
    p.add_argument("--limit", type=int, default=20)
    for name in ("show", "explain", "cost", "problems", "export", "reproduce"):
        p = sub.add_parser(name)
        p.add_argument("run", nargs="?", default="last")
        if name == "show":
            p.add_argument("--budget", type=int, default=600)
            p.add_argument("--focus")
        if name == "explain":
            p.add_argument("node", nargs="?")
        if name == "export":
            p.add_argument("--format", choices=("dot", "mermaid"), default="dot")
    p = sub.add_parser("diff")
    p.add_argument("run_a")
    p.add_argument("run_b")
    p = sub.add_parser("call")
    p.add_argument("run")
    p.add_argument("seq", type=int)
    return parser


def main(argv=None, out=print, core_factory=None):
    args = build_parser().parse_args(argv)
    cfg = None
    if args.runs_dir is None or args.store_dir is None or (args.command == "reproduce" and core_factory is None):
        cfg = _config()
    runs = RunLog(args.runs_dir or _path(cfg, "runs_dir", "data/runs")).read()
    store = ContentStore(args.store_dir or _path(cfg, "store_dir", "data/store"))
    try:
        if args.command == "list":
            return cmd_list(runs, out, limit=args.limit) or 0
        if args.command == "diff":
            return cmd_diff(find_run(runs, args.run_a), find_run(runs, args.run_b), out)
        record = find_run(runs, args.run)
        handler = {"show": cmd_show, "explain": cmd_explain, "cost": cmd_cost, "problems": cmd_problems, "export": cmd_export, "call": cmd_call, "reproduce": cmd_reproduce}[args.command]
        extra = {"store": store, "core_factory": core_factory or (make_core_factory(cfg) if cfg is not None else None)}
        return handler(record, out, **{**vars(args), **extra}) or 0
    except ExplainError as exc:
        out("error: %s" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
