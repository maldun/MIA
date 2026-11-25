"""
Smoke check SMOKE-RUN-001 of G-V4.GRAPHAPI.RUN (REQ-RUN-042, REQ-RUN-044; TR-RUN-009): a skill runs from its stored graph on the real model.

On the owner's host (Deploy) or on the branch (T-04): the converted graph of verify_claim (`verify.single@1`) is saved through CORE's save path into a
throw-away files store (a new temporary folder, tests/helpers/run_store.py), and Core with `graph_store=` that store runs verify_claim once on MP-light
with the claim of the case `true-pacific` of EV-verdicts dev. Green when the graph was read from the store, the run ends `done` and its run record
names the graph `verify.single@1` and version 1. The verdict is printed, not judged (one run decides nothing: the eval criteria do that).
The pin decides the model: its name, seed and temperature reach every model call, and the check cannot run when the server does not hold its digest.
MIA's own stores are never written: the store and the run log live in temporary folders that are removed afterwards.

Needs a running Ollama and the labelled suites (eval/suites, or MIA_SUITES as for tools/eval.py). Protected: change only through a plan amendment.
Run with the MIA virtualenv (it needs the ollama client):
  python tests/smoke/smoke_run.py [http://localhost:11434]        (exit 0 = green, 1 = red, 2 = cannot run)
"""
import json
import os
import shutil
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))

PIN = {"id": "MP-light", "name": "gemma4:12b-it-qat", "digest": "sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3",
       "seed": 7, "temperature": 0, "num_ctx": 8192}                # the pin of specs/mia/eval-spec.md, as tools/eval.py has it
SUITE, CASE = "verdicts", "true-pacific"
SKILL, GRAPH_ID, VERSION = "verify_claim", "verify.single@1", 1


def server_digest(url, name):
    tags = json.load(urllib.request.urlopen(url.rstrip("/") + "/api/tags", timeout=10))
    for model in tags["models"]:
        if model["name"] == name:
            return "sha256:" + model["digest"].replace("sha256:", "")
    return None


def dev_case(suite, case_id):
    """the input of one dev case of a labelled suite, or None; a case tagged split:holdout is never read"""
    folder = os.environ.get("MIA_SUITES") or os.path.join(REPO, "eval", "suites")
    with open(os.path.join(folder, suite, "cases.jsonl"), encoding="utf-8") as f:
        for line in f:
            case = json.loads(line) if line.strip() else {}
            if case.get("id") == case_id:
                return case["input"] if "split:dev" in case.get("tags", []) else None
    return None


class Pinned:
    """the model of the run: the pin's name, seed, temperature and context length reach every call, whatever the skill or step asks for"""

    def __init__(self, model, pin):
        self.model, self.pin = model, pin

    def _fixed(self, options):
        return dict(options or {}, **{k: self.pin[k] for k in ("seed", "temperature", "num_ctx")})

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        return self.model.chat(messages, schema, self.pin["name"], None, self._fixed(options))

    def chat_with_usage(self, messages, schema=None, model=None, profile=None, options=None):
        return self.model.chat_with_usage(messages, schema, self.pin["name"], None, self._fixed(options))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    url = argv[0] if argv else "http://localhost:11434"
    try:
        held = server_digest(url, PIN["name"])
    except OSError as err:
        print("cannot run: the model server %s does not answer: %s" % (url, err))
        return 2
    if held != PIN["digest"]:
        print("cannot run: the server holds %s as %s, the pin %s is %s" % (PIN["name"], held, PIN["id"], PIN["digest"]))
        return 2
    try:
        inputs = dev_case(SUITE, CASE)
        from ollama import Client
    except (OSError, ImportError) as err:
        print("cannot run: %s" % err)
        return 2
    if inputs is None:
        print("cannot run: no dev case %s in the suite %s" % (CASE, SUITE))
        return 2

    from core import Core
    from library import Library
    from pipeline_model import OllamaModel
    from rules_graphs import converted_skills
    from run_store import LIBRARY, SKILLS, ThrowAwayStore, run_record

    current = (PIN["name"], {"num_ctx": PIN["num_ctx"]})
    model = Pinned(OllamaModel(Client(host=url), lambda profile: current, lambda: current), PIN)
    store, runs = ThrowAwayStore(), tempfile.mkdtemp(prefix="mia-smoke-run-")
    results = []
    try:
        graph = dict(converted_skills())[SKILL + ".md"]
        saved = store.save(graph)
        results.append(("saved", graph.get("id") == GRAPH_ID and saved == VERSION, "%s version %s into %s" % (graph.get("id"), saved, store.folder)))
        core = Core(SKILLS, Library(LIBRARY), runs, model=model, graph_store=store)
        result = core.run(SKILL, inputs, started_by="command")
        results.append(("read from store", store.reads == [(GRAPH_ID, None)], "reads %s" % store.reads))
        results.append(("run done", result.status == "done", "%s in %.1fs%s" % (result.status, result.seconds or 0, ", " + str(result.error)[:120] if result.error else "")))
        record = run_record(core, result)
        named = (record.get("graph"), record.get("graph_version"))
        results.append(("record names graph", named == (GRAPH_ID, VERSION), "graph %s, version %s" % named))
        print("claim: %s\nanswer (not judged): %s" % (inputs["claim"], json.dumps(result.answer, ensure_ascii=False)[:300]))
    except Exception as err:            # a part that raises is red with its reason
        results.append(("run", False, "%s: %s" % (type(err).__name__, str(err)[:160])))
    finally:
        store.close()
        shutil.rmtree(runs, ignore_errors=True)
        results.append(("store removed", not os.path.exists(store.folder) and not os.path.exists(runs), store.folder))

    for name, ok, detail in results:
        print("%-20s %s  %s" % (name, "ok" if ok else "FAILED", detail))
    failed = sum(not ok for _, ok, _ in results)
    print("SMOKE-RUN-001:", "green" if not failed else "red (%d of %d parts failed)" % (failed, len(results)))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
