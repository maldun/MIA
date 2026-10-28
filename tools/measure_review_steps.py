"""Seconds and prompt sizes of the review skills on the toy world (T-07, A-18/A-19): the whole ReviewRun with the real light model on one case of eval/suites/review_toy, every skill timed.
Feedback for the step budgets and the first look at the judgements; not an eval decision (one case, one run, a deterministic starter suite with fictional papers).

  ~/prog/Python/venvs/mia312/bin/python tools/measure_review_steps.py [--case canary-failed-releases] [--log FILE]

Needs Ollama with the light model (one 12B model in 16 GB: stop other users of the GPU first). The world is read, never written."""
import argparse
import json
import os
import statistics
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LINK = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK, "MIA"))
sys.path.insert(0, _LINK)

from ollama import Client                                # noqa: E402
from MIA.config import default_path                      # noqa: E402
from MIA.core import Core                                # noqa: E402
from MIA.library import Library                          # noqa: E402
from MIA.pipeline_model import OllamaModel              # noqa: E402
from MIA import review_stages, review_models, scholar    # noqa: E402
from MIA.review_request import ReviewRequest             # noqa: E402

SUITE = os.path.join(REPO, "eval", "suites", "review_toy")
CRITERIA_CODES = ("off_topic", "outdated", "wrong_type", "language")


def load_world():
    with open(os.path.join(SUITE, "world.json"), encoding="utf-8") as fp:
        return {w["doi"]: w for w in json.load(fp)["works"]}


def as_work(raw):
    work = scholar.new_work("toy", doi=raw["doi"], title=raw["title"], date=raw["date"], year=int(raw["date"][:4]), abstract=raw["abstract"], oa_url="toy://" + raw["doi"])
    if raw.get("retraction"):
        work["retraction"] = {"status": "retracted", "notices": [{"type": "retracted", "date": raw["retraction"]["date"]}], "hints": []}
    return work


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default="canary-failed-releases")
    parser.add_argument("--cfg", default=default_path(REPO))
    parser.add_argument("--log", default=os.path.join(tempfile.gettempdir(), "review_steps_run.jsonl"))
    args = parser.parse_args()
    case = next(c for c in map(json.loads, open(os.path.join(SUITE, "cases.jsonl"), encoding="utf-8")) if c["id"] == args.case)
    world = load_world()
    cfg = json.load(open(args.cfg))
    light = cfg.get("version_light")
    client = Client(host="http://%s:%s" % (cfg.get("address", "localhost"), cfg.get("port", 11434)))
    profiles = {"light": (light, cfg.get("llm_options_light"))}
    model = OllamaModel(client, lambda p: profiles.get(p), lambda: profiles["light"], keep_alive=cfg.get("keep_alive"))
    calls = []
    plain_chat = model.chat

    def timed_chat(messages, *a, **kw):
        started = time.time()
        try:
            return plain_chat(messages, *a, **kw)
        finally:
            calls.append({"seconds": time.time() - started, "chars": sum(len(m["content"]) for m in messages)})
    model.chat = timed_chat
    work_dir = tempfile.mkdtemp()
    core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library"), os.path.join(work_dir, "user"), os.path.join(work_dir, "library.sqlite")), work_dir, model=model)
    per_skill = {}

    def run_skill(name, inputs):
        before = len(calls)
        result = core.run(name, inputs)
        per_skill.setdefault(name, []).extend(calls[before:])
        if result.status != "done":
            raise RuntimeError("%s: %s" % (name, result.error))
        return result.answer

    question, until = case["input"]["question"], case["input"]["until"]
    concepts, criteria = review_models.plan_keywords(run_skill, question)
    keywords = [k for words in concepts.values() for k in words]
    print("model %s, case %s\nkeywords: %s\ncriteria: %s" % (light, case["id"], keywords, [c["code"] for c in criteria]))

    def search(keyword, query):
        stems = [w for w in keyword.lower().split() if len(w) >= 4]
        return [as_work(w) for w in world.values() if any(s[:5] in (w["title"] + " " + w["abstract"]).lower() for s in stems)]

    def full_text(work):
        sections = world[work["doi"]]["sections"]
        return {"sections": [{"name": n.title(), "text": t} for n, t in sections.items() if n != "conclusion"], "conclusion": sections.get("conclusion", "")}

    abstract, full = review_models.make_screeners(run_skill, question, criteria)
    request = ReviewRequest(question, until=until)
    started = time.time()
    run = review_stages.ReviewRun(request, keywords, {c["code"] for c in criteria} or set(CRITERIA_CODES), search=search, screen_abstract=abstract, screen_full=full, full_text=full_text,
                                  agree=lambda report: True, approve_terms=lambda proposals: [], summarize=review_models.make_summarizer(run_skill, question))
    report = run.run()
    total = time.time() - started
    gold_in, gold_out = set(case["gold"]["included"]), {e["doi"]: e["reason"] for e in case["gold"]["excluded"]}
    print("\nflow: %s   ended by %s   %.0f s" % (report["flow"], report["ended_by"], total))
    print("%-16s %-8s %5s  %-8s %-14s %s" % ("work", "gold", "grade", "decision", "reason", "abstract only"))
    for w in report["works"]:
        gold = "in" if w["doi"] in gold_in else ("out:" + gold_out[w["doi"]] if w["doi"] in gold_out else "-")
        print("%-16s %-8s %5s  %-8s %-14s %s" % (w["doi"], gold, w["grade"], w["decision"], w["reason"], w["abstract_only"]))
    print("dropped before screening: %s" % [(d["work"]["doi"], d["code"]) for d in report["dropped"]])
    print("\nsummary (needs a person's check): %s" % json.dumps(report.get("summary"), ensure_ascii=False, indent=1)[:2500])
    print("\nskill       calls  mean s   max s  max prompt chars")
    for name, rows in per_skill.items():
        print("%-12s %4d  %6.1f  %6.1f  %6d" % (name, len(rows), statistics.mean(r["seconds"] for r in rows), max(r["seconds"] for r in rows), max(r["chars"] for r in rows)))
    with open(args.log, "w", encoding="utf-8") as fp:
        fp.write(json.dumps({"model": light, "case": case["id"], "per_skill": per_skill, "report": report}, ensure_ascii=False, default=str) + "\n")
    print("log: %s" % args.log)


if __name__ == "__main__":
    main()
