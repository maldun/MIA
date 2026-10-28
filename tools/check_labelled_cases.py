"""The labelled proposed cases of the review skills (specs/mia/eval-drafts/review_proposed_cases.jsonl, only those with confirmed: true), run with the real light model and repeats.
Feedback for the implementer (a handful of cases, fictional toy papers), never a decision: the verdict needs a real suite.

  ~/prog/Python/venvs/mia312/bin/python tools/check_labelled_cases.py [--repeats 5]

RVP-001 (keywords): per run the keywords labelled drop that came back, and the keywords nobody has labelled yet (for the person to label).
RVP-002 (eligibility): per run the decision, reason and grade of the work, first at the abstract and then after the full text (toy world sections), against the label."""
import argparse
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LINK = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK, "MIA"))
sys.path.insert(0, _LINK)

from ollama import Client                                # noqa: E402
from MIA.config import default_path                      # noqa: E402
from MIA.core import Core                                # noqa: E402
from MIA.library import Library                          # noqa: E402
from MIA.pipeline_model import OllamaModel              # noqa: E402
from MIA import review_models, review_stages            # noqa: E402

CASES = os.path.join(REPO, "specs", "mia", "eval-drafts", "review_proposed_cases.jsonl")
WORLD = os.path.join(REPO, "eval", "suites", "review_toy", "world.json")


def read_cases():
    text, i, out, dec = open(CASES, encoding="utf-8").read(), 0, [], json.JSONDecoder()
    while i < len(text):
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            break
        case, i = dec.raw_decode(text, i)
        out.append(case)
    return {c["id"]: c for c in out if c.get("confirmed") is True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--cfg", default=default_path(REPO))
    args = parser.parse_args()
    cases = read_cases()
    cfg = json.load(open(args.cfg))
    light = cfg.get("version_light")
    client = Client(host="http://%s:%s" % (cfg.get("address", "localhost"), cfg.get("port", 11434)))
    profiles = {"light": (light, cfg.get("llm_options_light"))}
    model = OllamaModel(client, lambda p: profiles.get(p), lambda: profiles["light"], keep_alive=cfg.get("keep_alive"))
    work_dir = tempfile.mkdtemp()
    core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library"), os.path.join(work_dir, "user"), os.path.join(work_dir, "library.sqlite")), work_dir, model=model)

    def run_skill(name, inputs):
        result = core.run(name, inputs)
        if result.status != "done":
            raise RuntimeError("%s: %s" % (name, result.error))
        return result.answer
    versions = {n: open(os.path.join(REPO, "skills", n + ".md"), encoding="utf-8").read().split("version:")[1].split()[0] for n in ("review_keywords", "review_abstract", "review_full")}
    print("model %s, skills %s, confirmed cases %s, %d repeats" % (light, versions, sorted(cases), args.repeats))
    if "RVP-001" in cases:
        case = cases["RVP-001"]
        labels = case["YOUR_LABELS"]
        dropped_total, per_run = 0, []
        for _ in range(args.repeats):
            concepts, _criteria = review_models.plan_keywords(run_skill, case["question"])
            words = [k for ks in concepts.values() for k in ks]
            bad = [k for k in words if labels.get(k) == "drop"]
            unknown = [k for k in words if k not in labels]
            per_run.append((len(words), bad, unknown))
            dropped_total += len(bad)
        print("\nRVP-001 keywords: labelled-drop keywords returned per run: %s of %s keywords" % ([len(b) for _n, b, _u in per_run], [n for n, _b, _u in per_run]))
        print("  labelled keep returned: not counted; unlabelled keywords to label: %s" % sorted({k for _n, _b, u in per_run for k in u}))
    if "RVP-002" in cases:
        case = cases["RVP-002"]
        label = case["YOUR_LABELS"]
        raw = {w["doi"]: w for w in json.load(open(WORLD, encoding="utf-8"))["works"]}[case["work"]["doi"]]
        criteria = [{"code": c, "text": t} for c, t in (("off_topic", "the work is not about the research question"), ("outdated", "older than twenty years without a lasting method"),
                                                     ("wrong_type", "not a study (editorial, news, advertisement)"), ("language", "not in a language the team can read"))]
        abstract, full = review_models.make_screeners(run_skill, case["question"], criteria)
        work = {"doi": raw["doi"], "title": raw["title"], "date": raw["date"], "abstract": raw["abstract"]}
        text = {"sections": [{"name": n.title(), "text": t} for n, t in raw["sections"].items() if n != "conclusion"], "conclusion": raw["sections"]["conclusion"]}
        rows = []
        for _ in range(args.repeats):
            a = review_stages.check_judgement(abstract(work), work["abstract"], {c["code"] for c in criteria})
            f = review_stages.combine(a, review_stages.check_full(full({**work, "abstract_statement": a["statement"]}, text), text, {c["code"] for c in criteria}))
            rows.append((a["decision"], a["reason"] or "none", a["grade"], f["decision"], f["reason"] or "none", f["grade"]))
        want = (label["decision"], label["reason"], int(label["grade"]))
        print("\nRVP-002 rt.0003, label %s; per run (abstract decision/reason/grade -> final decision/reason/grade):" % (want,))
        for r in rows:
            print("  %s/%s/%s -> %s/%s/%s%s" % (*r, "   MATCH" if (r[3], r[4], r[5]) == want else ""))
        print("  final decision equals the label in %d of %d runs; final decision+reason+grade in %d of %d" % (
            sum(r[3] == want[0] for r in rows), len(rows), sum((r[3], r[4], r[5]) == want for r in rows), len(rows)))


if __name__ == "__main__":
    main()
