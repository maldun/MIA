"""Records the oracle of G-V4.GRAPHAPI.RUN (TR-RUN-002): the answers of the code of `goal/v4` before RUN changes anything.

Run it once, in a checkout whose code (everything outside specs/) equals `goal/v4`:
    /home/maldun/prog/Python/venvs/mia312/bin/python tools/record_run_oracle.py [--out FILE]

It records, as one JSON file with the commit in its header:
- `rule_report` and `run_check` (IF-301 v4) on the 15 converted skill graphs, the 500 random graphs (tests/helpers/run_graphs.py) and golden 24 to 31;
- `order_of` of today's graph_model on the converted graphs and on every acyclic random graph;
- the model calls and the answer of the six skills with an equivalence suite on the scripted replies of TC-WFM-058 (old runner, empty store).
The file is protected material (tests/helpers/run_oracle.json); the agent stages it, the owner's script tools/apply_amendment_a187.sh copies it.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGED = os.path.join(REPO, "specs", "mia", "amendments", "A-187", "tests", "helpers")
for path in (REPO, os.path.join(REPO, "tests", "helpers"), os.path.join(REPO, "tests", "helpers", "mocks"), STAGED):
    sys.path.append(path)
sys.path.insert(0, REPO)

from rules_graphs import connection, converted_skills, data, graph, step, transform   # noqa: E402
from run_graphs import acyclic, random_graphs                                          # noqa: E402
from graph_model import order_of                                                       # noqa: E402
from graph_rule_set import rule_report, run_check                                      # noqa: E402
from call_recording import Recording, RecordingModel, RecordingTool, ScriptedModel     # noqa: E402
from core import Core                                                                  # noqa: E402
from library import Library                                                           # noqa: E402

INPUTS = {"research": {"question": "When did the Rivertown Bridge open to traffic?"},
          "plan_question": {"question": "Which is older, the Tarn Museum or the company that built the Rivertown Bridge?"},
          "verify_claim": {"claim": "The Pacific is the largest ocean on Earth.", "evidence": "", "rounds": 3, "experts": []},
          "verify_computable": {"claim": "1628.89 euros is what 1000 euros grow to at 5 percent interest per year in 10 years", "data_description": "principal, rate, years, claimed",
                                "data": {"principal": 1000, "rate": 5, "years": 10, "claimed": 1628.89}},
          "extract_claims": {"text": "Quick check of the budget: 12 * 1.5 + 3 = 21, so we stay within limits."},
          "extract_claims_rules": {"text": "Quick check of the budget: 12 * 1.5 + 3 = 21, so we stay within limits."}}


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


def named_commit():
    """goal/v4's tip; the code of this checkout must equal it (only specs/ may differ), or the oracle would record changed code"""
    commit = git("rev-parse", "goal/v4")
    if subprocess.run(["git", "diff", "--quiet", commit, "--", ".", ":!specs"], cwd=REPO).returncode or git("status", "--porcelain", "--", ".", ":!specs", ":!tools/record_run_oracle.py"):
        sys.exit("the code of this checkout differs from goal/v4 %s: no oracle recorded" % commit[:8])
    return commit


def checked(g, given=None):
    return {"rule_report": rule_report(g), "run_check": run_check(g, given)}


def golden():
    """the graphs of golden 24 to 31 that take a graph (24 is the registry, the answers of kinds() are fixed by its test)"""
    g26 = graph([data("d1"), transform("t1"), transform("t2")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d1"), connection("e3", "t2", "d1")])
    g27 = graph([data("d1"), transform("t1"), transform("t2")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d1"), connection("e3", "t2", "d1"), connection("e9", "t1", "z")])
    chat = dict(dict(converted_skills())["chat.md"])
    cases = {
        "25 chat with kind": (dict(chat, kind="workflow"), None), "25 chat without kind": ({k: v for k, v in chat.items() if k != "kind"}, None),
        "26": (g26, None), "27": (g27, None),
        "28 doubled": (graph([step("c1", "entity"), step("c2", "entity")], [connection("e1", "c1", "c2"), connection("e2", "c1", "c2")], kind="context"), None),
        "28 cycle": (graph([step("c1", "entity"), step("c2", "entity")], [connection("e1", "c1", "c2"), connection("e2", "c2", "c1")], kind="context"), None),
        "29 swarm": (dict(g26, kind="swarm"), None), "29 context": (graph([step("c1", "entity")], [], kind="context"), None),
        "30 none given": (chat, None), "30 hello": (chat, {"input.text": "hello"}), "30 None": (chat, {"input.text": None}),
        "31 step is 5": (graph([5], []), None),
        "31 connection data list": (graph([data("a"), transform("t")], [{"id": "e1", "from": "a", "to": "t", "data": []}]), None),
        "31 step without id": (graph([{"data": {"type": "data"}}], []), None),
        "31 connection without from": (graph([data("a"), transform("t")], [{"id": "e1", "to": "t", "data": {}}]), None),
        "31 nodes is a text": ({"id": "g", "nodes": "x", "edges": []}, None),
    }
    return {name: checked(g, given) for name, (g, given) in cases.items()}


def old_run(skill, folder):
    rec = Recording()
    tools = {"web_search": RecordingTool("web_search", lambda **kw: [], rec), "fetch_page": RecordingTool("fetch_page", lambda **kw: {"text": ""}, rec)}
    core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), folder, model=RecordingModel(ScriptedModel(), rec), tools=tools)
    result = core.run(skill, INPUTS[skill], started_by="command")
    if result.status != "done":
        sys.exit("the scripted old run of %s ended with %s: %s" % (skill, result.status, result.error))
    return {"model_calls": rec.model_calls(), "tool_calls": rec.tool_calls(), "answer": result.answer}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(STAGED, "run_oracle.json"))
    out = parser.parse_args().out
    commit = named_commit()
    os.chdir(REPO)
    skills = dict(converted_skills())
    randoms = random_graphs()
    flags = [acyclic(g, order_of) for g in randoms]
    oracle = {
        "header": {"commit": commit, "branch": "goal/v4", "contract": "IF-301 v4", "recorded_by": "tools/record_run_oracle.py", "seed": 7,
                   "random_graphs": len(randoms), "random_acyclic": sum(flags), "converted_skills": sorted(skills)},
        "converted": {name: dict(checked(g), order=order_of(g)) for name, g in skills.items()},
        "random": [dict(checked(g), order=order_of(g) if ok else None) for g, ok in zip(randoms, flags)],
        "golden": golden(),
        "old_runner": {},
    }
    for skill in INPUTS:
        with tempfile.TemporaryDirectory() as folder:
            oracle["old_runner"][skill] = old_run(skill, folder)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fp:
        json.dump(oracle, fp, indent=1, sort_keys=True)
        fp.write("\n")
    print("oracle at goal/v4 %s: %d converted, %d random (%d acyclic), %d golden, %d skills -> %s"
          % (commit[:8], len(skills), len(randoms), sum(flags), len(oracle["golden"]), len(oracle["old_runner"]), out))


if __name__ == "__main__":
    main()
