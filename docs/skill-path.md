# From an idea to a promoted skill

The path every workflow takes in MIA (FR-20, REQ-EVL-006): a user has an idea, writes a skill file and a pipeline, checks them, specifies and measures them, declares what they may do, keeps them as a draft until a person promotes them, and the time from the idea to the promotion is on record. Nothing on this path changes the platform: a new workflow is a new valid library entry.

The example all the way is the **lookup**: "answer a factual question with sources and verbatim quotes, or say unknown" (FR-10). Its simplest form is the pipeline `research.baseline@1` (search, read the first pages, choose passages, one model call, quotes checked in code); the skill `research` points to the strategies built on it. Every block marked *run* below is executed by `tests/test_skill_path_doc.py` with a scripted model, so the examples stay true. Nothing here needs the real model, a network or Ollama; the real-model commands are shown without the mark.

| Step | You | Where it lives |
|---|---|---|
| 1 Idea | one sentence: input, output, what "right" means | the issue or note, later the `goal` of the pipeline |
| 2 Skill file and pipeline | write `skills/<name>.md` and a library entry | [skills/research.md](../skills/research.md), [library/pipelines/research.baseline/1.json](../library/pipelines/research.baseline/1.json) |
| 3 Validation | the library and the skill check themselves | `tools/library.py validate` |
| 4 Specification and benchmark | requirements with an eval criterion, a suite with a holdout, a baseline | [eval/suites/research](../eval/suites/research), [eval/baselines](../eval/baselines) |
| 5 Declaration | `safety`, `needs`, `cost`, `max_safety` in the entry and the skill | the library entry |
| 6 Draft and promotion | the entry is a draft until a person promotes it | `tools/library.py promote` |
| 7 Time record | the library keeps when the draft was made and when it was promoted | `origin.created`, `status.json` |

## Step 1: the idea

Write one sentence for the input, one for the output and one for the right answer. For the lookup: *input* a question; *output* an answer with sources and quotes, or `unknown`; *right* means every quote occurs word for word in the page it cites, and a question without an answer gets `unknown`. If you cannot say what right is, you cannot measure it in step 4: stop here.

## Step 2: skill file and pipeline

A skill is one file in `skills/`: the model profile, the pipeline it runs, the tools it may use and the budget. A pipeline is a library entry: a tree of nodes (model, tool, code, map, branch, loop) with references between them. Look at the lookup:

```bash run
python tools/library.py show research.baseline@1 | head -n 12
```

The same pipeline runs here with a scripted model over the recorded web of the research suite, for the question "When did the bridge open?" (a real run is `python tools/eval.py run research --variant baseline --repeats 3`, see the section Core, phase 5c in [ui/README.md](../ui/README.md)):

```python run
import json, os, tempfile
import harness
from core import Core
from library import Library

class Scripted:
    """a fake model: it answers with the first words of the first passage and quotes them"""
    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        prompt = messages[-1]["content"]
        first = prompt.split("Passages:\n", 1)[1].split("<<<WEB TEXT", 1)[1].split("\n", 1)[1].split(">>>")[0].strip()
        return json.dumps({"answer": first[:300], "status": "answered", "sources": [{"n": 1, "quote": first[:60]}]})

core = Core("skills", Library("library"), tempfile.mkdtemp(), model=Scripted())
suite = harness.load_suite("eval/suites/research")
run = harness.Harness(core).run(suite, {"name": "doc", "pipeline": "research.baseline@1"}, only=["bridge-date"])
record = run.records[0]
print(record["case"], record["status"], "model calls:", record["calls"])
assert record["status"] == "pass" and record["calls"] == 1
```

## Step 3: validation

Two checks that need no model: the library (every file, every reference, every version) and the skills with their pipelines. Both stop at the first thing that cannot work, long before a real run:

```bash run
python tools/library.py validate
```

With the app's virtualenv, `python tools/try_pipeline.py --check` checks all skills against the library and `python tools/try_pipeline.py research "When did the bridge open?"` runs one with the real model.

## Step 4: specification and benchmark

A workflow without a specification, a context graph and a benchmark with a recorded baseline stays a draft (REQ-BE-039). For the lookup:

- the **requirements** say what is measured: a quote that is not on its page is the worst error; `unknown` where nothing is to be found is right; each requirement has an `Eval criterion:` line (suite, metric, threshold, repeats, model pin, decision rule), fixed before the first run;
- the **suite** is `eval/suites/research` (the development cases) and its holdout; the cases carry the truth, which a person labelled; the web is recorded, so a run is the same every time;
- the **baseline** is the run of the current version on the pinned model, saved in `eval/baselines/<suite>__<variant>__baseline.jsonl`. Later versions are judged against it and only on the holdout, by the decision rule (`tools/decide_guard.py` refuses a dev-split run).

Which workflows lack a baseline file is a check, not a feeling:

```bash run exit=1
set -o pipefail
python tools/check_baselines.py | tail -n 3
```

(exit code 1 is the answer "some workflows lack one"; today it names them.)

## Step 5: the declaration

The entry says what the workflow may do, in plain flags, and the skill says how far it may go: `safety` (`reads_web`, `runs_code` and so on) on a node, `max_safety` in the skill file, `needs` (the tools), the `cost` class and the budget (steps, seconds, calls). The core refuses to run a pipeline that needs a flag the skill's `max_safety` does not allow. The lookup declares `max_safety: {reads_web: true}`: it may read the web, not run code or write files.

## Step 6: draft and promotion

A new entry is always a **draft**; only a person promotes it to `tested` or `trusted`, with a note. Versions are immutable: a changed entry is a new version. The example below makes a copy of the lookup in a throw-away folder, adds it as a draft and promotes it:

```python run
import json, os, tempfile
from library import Library

tick = [1000.0]
lib = Library("library", user_dir=tempfile.mkdtemp(), clock=lambda: tick[0])
entry = json.load(open("library/pipelines/research.baseline/1.json"))
entry["id"], entry["version"] = "research.doc_example", 1
ref = lib.add_draft("pipeline", entry, by="doc")
print(ref, lib.pipelines[("research.doc_example", 1)]["status"])
assert lib.pipelines[("research.doc_example", 1)]["status"] == "draft"
tick[0] += 3 * 3600                                   # three hours later a person has seen the numbers
lib.set_status(ref, "tested", note="passed the holdout of the doc example", by="owner")
assert lib.pipelines[("research.doc_example", 1)]["status"] == "tested"
```

On the command line the promotion is `python tools/library.py promote research.baseline@1 tested --note "why"`.

## Step 7: the time record

The library writes down when the draft was made (`origin.created` in the entry) and when it was promoted (`at` in `status.json`, with who and why). The time from the idea to the promotion is the difference, and it is on record for every workflow without extra work:

```python run
import json, os, tempfile, time
from library import Library

tick = [1000.0]
user = tempfile.mkdtemp()
lib = Library("library", user_dir=user, clock=lambda: tick[0])
entry = json.load(open("library/pipelines/research.baseline/1.json"))
entry["id"], entry["version"] = "research.doc_time", 1
ref = lib.add_draft("pipeline", entry, by="doc")
tick[0] += 90 * 60
lib.set_status(ref, "tested", note="time record", by="owner")
made = lib.pipelines[("research.doc_time", 1)]["origin"]["created"]
promoted = json.load(open(os.path.join(user, "status.json")))[ref]["at"]
parse = lambda s: time.mktime(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
print("idea to promotion:", int(parse(promoted) - parse(made)) // 60, "minutes")
assert int(parse(promoted) - parse(made)) == 90 * 60
```

The idea itself (the day someone wrote the sentence of step 1) is the date of the issue or note; keep it with the entry in `origin.note`. FR-20 asks for the lookup first and the literature review within a month after its promotion: the same seven steps.
