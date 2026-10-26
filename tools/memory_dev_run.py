"""Dev run of the skill memory_write on the DEV cases of the memory sample (T-04, D-78): feedback for the implementer, never a decision (the holdout decides, in Verify).

  ~/prog/Python/venvs/mia312/bin/python tools/memory_dev_run.py [--repeats 3] [--log FILE]

Needs Ollama with the light model loaded. Lines of the sample whose split is not "dev" are skipped before they are parsed: holdout content is never read or printed.
Per case and repeat a fresh store is used; update cases are seeded with the record they replace (named in the proposal after "replaces:"); cases whose source is not the
user's own message go through MemoryRecords.remember, which refuses them before the model is asked. A stored record matches an expected one when the kind is equal and at
least half of the expected words occur in it (a rough feedback measure, the owner's labels are the truth). Prints a table per case and totals; the raw predictions go to the log.
"""
import argparse
import json
import os
import re
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
from MIA.memory_records import MemoryRecords, MemoryRefused, _words    # noqa: E402
from MIA.storage import Storage                          # noqa: E402
from MIA.storage_files import FileBackend                # noqa: E402

SAMPLE = os.path.join(REPO, "specs", "mia", "eval-drafts", "memory_sample.jsonl")
DEV = re.compile(r'"split":\s*"dev"')
REPLACES = re.compile(r"^(.*?)\s*\(replaces:\s*(.*?)\)\s*$")


def dev_cases():
    with open(SAMPLE, encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if DEV.search(line)]


def expected_of(case):
    """[(kind, text, replaced text or None)]"""
    out = []
    for item in case["proposal"]:
        match = REPLACES.match(item["text"])
        out.append((item["kind"], match.group(1) if match else item["text"], match.group(2) if match else None))
    return out


def matches(kind, text, want_kind, want_text):
    words = _words(want_text)
    return kind == want_kind and bool(words) and len(words & _words(text)) / len(words) >= 0.5


def run_case(core, case, work):
    storage = Storage(FileBackend(tempfile.mkdtemp(dir=work)))
    memory = MemoryRecords(storage)
    seeded = {}
    for kind, _text, old in expected_of(case):
        if old:
            seeded[old] = memory.add("anna", "seed", [{"kind": "fact", "text": old}], "user")[0]
    before = set(storage.ids("memory"))
    text = "\n".join(turn["text"] for turn in case["turns"])
    calls = []

    def ask(message, known):
        result = core.run("memory_write", {"text": message, "known": known})
        calls.append(result.seconds)
        if result.status != "done":
            raise RuntimeError(result.error)
        return result.answer.get("records", [])

    refused = False
    try:
        memory.remember("anna", "m1", text, case["source_kind"], ask)
    except MemoryRefused:
        refused = True
    stored = [storage.get("memory", i)["doc"] for i in storage.ids("memory") if i not in before]
    expected = expected_of(case)
    hit = [any(matches(d["kind"], d["text"], k, t) for d in stored) for k, t, _old in expected]
    extra = [d for d in stored if not any(matches(d["kind"], d["text"], k, t) for k, t, _old in expected)]
    replaced_ok = [storage.get("memory", seeded[old])["doc"]["status"] == "replaced" for _k, _t, old in expected if old]
    return {"id": case["id"], "category": case["category"], "refused": refused, "calls": len(calls), "seconds": round(sum(calls), 1), "expected": len(expected),
            "hits": sum(hit), "extra": len(extra), "replaced_ok": replaced_ok, "stored": [[d["kind"], d["text"]] for d in stored]}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--cfg", default=default_path(REPO))
    parser.add_argument("--log", default=os.path.join(tempfile.gettempdir(), "memory_write_dev_run.jsonl"))
    args = parser.parse_args()
    with open(args.cfg) as fp:
        cfg = json.load(fp)
    light = cfg.get("version_light")
    client = Client(host="http://%s:%s" % (cfg.get("address", "localhost"), cfg.get("port", 11434)))
    profiles = {"light": (light, cfg.get("llm_options_light"))}
    model = OllamaModel(client, lambda p: profiles.get(p), lambda: profiles["light"], keep_alive=cfg.get("keep_alive"))
    work = tempfile.mkdtemp()
    core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library"), os.path.join(work, "user"), os.path.join(work, "library.sqlite")), work, model=model)
    digest = None
    try:
        digest = next((m.get("digest") for m in client.list().get("models", []) if light in (m.get("model"), m.get("name"))), None)
    except Exception:
        pass
    cases = dev_cases()
    version = re.search(r"^version:\s*(\d+)", open(os.path.join(REPO, "skills", "memory_write.md"), encoding="utf-8").read(), re.M).group(1)
    print("skill memory_write v%s, model %s (digest %s), %d dev cases, %d repeats, started %s"
          % (version, light, (digest or "?")[:12], len(cases), args.repeats, time.strftime("%Y-%m-%d %H:%M")))
    rows = []
    for case in cases:
        runs = [run_case(core, case, work) for _ in range(args.repeats)]
        rows.append((case, runs))
        stable = len({json.dumps(sorted(r["stored"])) for r in runs}) == 1
        print("%-8s %-12s expected %d  hits %s  extra %s  %s%s" % (case["id"], case["category"], runs[0]["expected"], [r["hits"] for r in runs], [r["extra"] for r in runs],
                                                              "refused before the model" if runs[0]["refused"] else "", "" if stable else "  (differs between repeats)"))
    with open(args.log, "w", encoding="utf-8") as fp:
        for case, runs in rows:
            fp.write(json.dumps({"case": case["id"], "runs": runs}, ensure_ascii=False) + "\n")
    runs = [r for _c, rs in rows for r in rs]
    expected, hits = sum(r["expected"] for r in runs), sum(r["hits"] for r in runs)
    quiet = [r for r in runs if r["expected"] == 0]
    replaced = [x for r in runs for x in r["replaced_ok"]]
    print("\nrecall %d/%d (%.0f %%)   extra records %d   in the %d runs that expect nothing: %d stored   replaced right %d/%d   refused before the model %d runs   model seconds %.0f"
          % (hits, expected, 100.0 * hits / max(1, expected), sum(r["extra"] for r in runs), len(quiet), sum(r["extra"] for r in quiet), sum(replaced), len(replaced),
             sum(r["refused"] for r in runs), sum(r["seconds"] for r in runs)))
    print("raw predictions: %s (feedback on the dev cases only, not a decision)" % args.log)


if __name__ == "__main__":
    main()
