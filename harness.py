"""
The evaluation harness (ui/REQUIREMENTS_CORE.md 9, L2 to L5): runs a *suite* of cases against a target (the hard checks, a pipeline of the library), records what happened and how much it cost, and
reports the numbers of metrics.py. A change to a prompt, a pipeline, a check or a model is judged by running the same suite before and after and comparing, not by a feeling.

  eval/suites/<name>/suite.json     {"name", "description", "target": {"kind": "checks" | "pipeline", ...}}
  eval/suites/<name>/cases.jsonl    one case per line: {"id", "tags": [...], "claim" | "input": ..., "truth": true | false, "expect": "pass" | "fail" | "open" | ..., "note": "why"}

`truth` says whether the claim is actually correct (the verifier metrics: false passes, coverage ...), `expect` the exact behaviour a regression wants (a near match must stay `open`).
A *variant* is what changes between runs: the skill, a pinned pipeline version, the model; its name is part of the saved file. Runs are saved as JSON lines in `data/eval/`.
"""
import copy
import json
import os
import time

import requests

try:
    from . import checks, extraction, metrics, web_tools
except ImportError:  # used as plain script / in tests
    import checks
    import extraction
    import metrics
    import web_tools

INPUT_KEY = {"checks": "claim", "pipeline": "input", "extraction": "input"}
CASE_KEYS = {"id", "tags", "claim", "input", "truth", "expect", "note", "gold"}
STATUSES = ("pass", "fail", "open", "not_applicable")
MAX_OUTPUT_CHARS = 3000


class SuiteError(Exception):
    pass


class Suite:
    def __init__(self, name, description, target, cases, path=""):
        self.name, self.description, self.target, self.cases, self.path = name, description, target, cases, path

    def select(self, tags=None, only=None, limit=None):
        cases = self.cases
        if only:
            cases = [c for c in cases if c["id"] in only]
        if tags:
            cases = [c for c in cases if set(tags) <= set(c.get("tags", []))]
        return cases[:limit] if limit else cases


def load_suite(folder):
    """a suite from its folder; raises SuiteError with every problem found"""
    name = os.path.basename(os.path.normpath(folder))
    problems = []
    try:
        with open(os.path.join(folder, "suite.json"), encoding="utf-8") as fp:
            meta = json.load(fp)
    except (OSError, ValueError) as exc:
        raise SuiteError("%s: suite.json cannot be read (%s)" % (name, exc))
    if meta.get("name") != name:
        problems.append("suite.json: 'name' must be the folder name '%s'" % name)
    target = meta.get("target")
    if not isinstance(target, dict) or "kind" not in target:
        problems.append("suite.json: 'target' needs a 'kind'")
        target = {"kind": "?"}
    key = INPUT_KEY.get(target["kind"], "input")
    cases, seen = [], set()
    try:
        with open(os.path.join(folder, "cases.jsonl"), encoding="utf-8") as fp:
            lines = [line for line in fp if line.strip()]
    except OSError as exc:
        raise SuiteError("%s: cases.jsonl cannot be read (%s)" % (name, exc))
    for number, line in enumerate(lines, 1):
        label = "cases.jsonl line %d" % number
        try:
            case = json.loads(line)
        except ValueError as exc:
            problems.append("%s: not valid JSON (%s)" % (label, exc))
            continue
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or not case["id"]:
            problems.append("%s: every case needs an 'id'" % label)
            continue
        label = "case '%s'" % case["id"]
        if case["id"] in seen:
            problems.append("%s: the id is used twice" % label)
        seen.add(case["id"])
        for k in case:
            if k not in CASE_KEYS:
                problems.append("%s: unknown field '%s'" % (label, k))
        if key not in case:
            problems.append("%s: needs '%s' for a %s target" % (label, key, target["kind"]))
        if case.get("truth") is None and case.get("expect") is None:
            problems.append("%s: needs 'truth' or 'expect' (what is right?)" % label)
        if target["kind"] == "extraction":
            gold = case.get("gold")
            if not isinstance(gold, list) or not all(isinstance(g, dict) and g.get("type") and g.get("anchor") for g in gold):
                problems.append("%s: an extraction case needs 'gold', a list (maybe empty) of claims with 'type' and 'anchor'" % label)
            elif isinstance(case.get("input"), dict) and any(g["anchor"] not in case["input"].get("text", "") for g in gold):
                problems.append("%s: every gold anchor must be a verbatim part of the input text" % label)
        if case.get("truth") is not None and not isinstance(case["truth"], bool):
            problems.append("%s: 'truth' must be true or false" % label)
        if case.get("expect") is not None and metrics.normalize_status(case["expect"]) not in STATUSES:
            problems.append("%s: 'expect' must be one of %s" % (label, ", ".join(STATUSES)))
        if not isinstance(case.get("tags", []), list):
            problems.append("%s: 'tags' must be a list" % label)
        cases.append(case)
    if not cases:
        problems.append("the suite has no cases")
    if problems:
        raise SuiteError("%s: %s" % (name, "; ".join(problems)))
    return Suite(name, meta.get("description", ""), target, cases, folder)


def list_suites(root):
    suites = []
    if os.path.isdir(root):
        for name in sorted(os.listdir(root)):
            if os.path.isfile(os.path.join(root, name, "suite.json")):
                try:
                    suites.append(load_suite(os.path.join(root, name)))
                except SuiteError as exc:
                    suites.append(exc)
    return suites


class CountingModel:
    """wraps the model of a Core and counts calls and characters (about 4 characters make a token); the harness reads the counts per case"""

    def __init__(self, model):
        self.model, self.calls, self.chars_in, self.chars_out = model, 0, 0, 0

    def chat(self, messages, **kwargs):
        reply = self.model.chat(messages, **kwargs)
        self.calls += 1
        self.chars_in += sum(len(str(m.get("content", ""))) for m in messages)
        self.chars_out += len(str(reply))
        return reply

    def snapshot(self):
        return self.calls, self.chars_in, self.chars_out


# --- recorded web: the real fetcher, safety rules, search and text extraction on fixed pages --------------------------------------------------------------

SEARXNG_FIXTURE_URL = "http://localhost:8590"
FILLER = "The quick brown fox jumps over the lazy dog. "


class FixtureResponse:
    def __init__(self, status=200, body="", content_type="text/html; charset=utf-8", headers=None, json_data=None):
        self.status_code, self._body, self._json = status, body.encode("utf-8"), json_data
        self.headers = dict({"Content-Type": content_type}, **(headers or {}))
        self.encoding, self.raw, self.text = "utf-8", None, body

    def iter_content(self, chunk_size=1):
        for i in range(0, len(self._body), 65536):
            yield self._body[i:i + 65536]

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json

    def close(self):
        pass


class FixtureWebSession:
    """a stand-in for requests.Session that answers from a fixture file: {"pages": {url: {status, content_type, body, headers, error}}, "searches": {query: [results]}}.
    A body may contain {{PAD:n}}, replaced by n characters of filler (long pages). "error": "timeout" or "unreachable" raises like the network would.
    Searches are answered as a SearXNG would; a query without an entry finds nothing; the entry "__down__": true makes the search backend unreachable."""

    def __init__(self, fixtures):
        self.pages, self.searches = fixtures.get("pages", {}), fixtures.get("searches", {})
        self.calls = []

    @staticmethod
    def _pad(body):
        import re
        return re.sub(r"\{\{PAD:(\d+)\}\}", lambda m: (FILLER * (int(m.group(1)) // len(FILLER) + 1))[:int(m.group(1))], body)

    def get(self, url, params=None, **kwargs):
        self.calls.append(url if not params else "%s?q=%s" % (url, params.get("q")))
        if url.startswith(SEARXNG_FIXTURE_URL):
            if self.searches.get("__down__"):
                raise requests.ConnectionError("search backend down")
            return FixtureResponse(json_data={"results": [dict(r, engines=["fixture"], content=r.get("snippet", "")) for r in self.searches.get((params or {}).get("q"), [])],
                                              "unresponsive_engines": []})
        entry = self.pages.get(url)
        if entry is None or entry.get("error") == "unreachable":
            raise requests.ConnectionError("no such host: " + url)
        if entry.get("error") == "timeout":
            raise requests.ConnectTimeout("timed out")
        return FixtureResponse(entry.get("status", 200), self._pad(entry.get("body", "")), entry.get("content_type", "text/html; charset=utf-8"), entry.get("headers"))


def fixture_checks(core, fixtures):
    """a CheckRunner whose web checks (citation, web confirmation) use the recorded web of the fixtures; everything else is the Core's"""
    session = FixtureWebSession(fixtures)
    tools, _, _ = web_tools.build_web_tools({"search_backends": ["searxng"]}, None, session=session, resolver=lambda host: ["93.184.216.34"])
    functions = dict(checks.build_web_checks(tools["web_search"][0], tools["fetch_page"][0]))
    names = list(core.runner.tools) + ["web_search", "fetch_page"]
    return checks.CheckRunner(core.library, lambda: {**core.runner.functions, **functions}, lambda: names, sandbox=core.sandbox), session


class Run:
    def __init__(self, header, records):
        self.header, self.records = header, records

    def save(self, folder):
        os.makedirs(folder, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime(self.header["started"]))
        path = os.path.join(folder, "%s__%s__%s.jsonl" % (self.header["suite"], self.header["variant"]["name"], stamp))
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(json.dumps(dict(self.header, kind="header"), ensure_ascii=False) + "\n")
            for record in self.records:
                fp.write(json.dumps(dict(record, kind="record"), ensure_ascii=False, default=str) + "\n")
        return path


def load_run(path):
    header, records = None, []
    with open(path, encoding="utf-8") as fp:
        for line in fp:
            item = json.loads(line)
            if item.pop("kind", "record") == "header":
                header = item
            else:
                records.append(item)
    if header is None:
        raise SuiteError("%s is not a saved run (no header line)" % path)
    return Run(header, records)


def latest_run(folder, suite, variant=None):
    """the newest saved run of a suite (and a variant), or None"""
    if not os.path.isdir(folder):
        return None
    prefix = "%s__%s__" % (suite, variant) if variant else "%s__" % suite
    names = sorted(n for n in os.listdir(folder) if n.startswith(prefix) and n.endswith(".jsonl"))
    return os.path.join(folder, names[-1]) if names else None


def _clip(value, limit=MAX_OUTPUT_CHARS):
    text = json.dumps(value, ensure_ascii=False, default=str)
    return value if len(text) <= limit else text[:limit] + "...[clipped]"


class Harness:
    def __init__(self, core=None, clock=time.time, targets=None):
        """core: a Core (for the targets 'checks' and 'pipeline'); targets: more kinds, {kind: function(case, variant, context) -> (status, output)}, for tests and new tasks"""
        self.core, self._clock = core, clock
        self.targets = {"checks": self._checks, "pipeline": self._pipeline, "extraction": self._extraction}
        self.targets.update(targets or {})
        self.counter = None
        self._fixture_runners = {}
        if core is not None and getattr(core.runner, "model", None) is not None:
            self.counter = CountingModel(core.runner.model)
            core.runner.model = self.counter

    # -- the targets --
    def _checks(self, case, variant, suite):
        runner = self.core.checks
        if suite.target.get("fixtures"):                                   # recorded web: deterministic and offline
            runner = self._fixture_runners.get(suite.name)
            if runner is None:
                with open(os.path.join(suite.path, suite.target["fixtures"]), encoding="utf-8") as fp:
                    runner = self._fixture_runners[suite.name] = fixture_checks(self.core, json.load(fp))[0]
        outcome = runner.run(case["claim"], include_web=bool(suite.target.get("include_web")))
        return outcome["status"], outcome

    def _pipeline(self, case, variant, suite):
        skill = copy.deepcopy(self.core.skills.get(variant.get("skill") or suite.target["skill"]))
        if skill is None:
            raise SuiteError("there is no skill '%s'" % (variant.get("skill") or suite.target["skill"]))
        if variant.get("pipeline"):
            skill["pipeline"] = variant["pipeline"]
        if variant.get("model"):
            skill["model"] = {"profile": variant["model"]} if variant["model"] in ("light", "full", "current") else {"name": variant["model"]}
        if variant.get("budget"):
            skill["budget"] = dict(skill["budget"], **variant["budget"])
        graph = self.core.graph(skill)[0]
        result = self.core.runner.run(skill, graph, case["input"], task="eval:" + suite.name)
        return self._status_of(result, suite)

    def _status_of(self, result, suite):
        answer = result.answer
        field = suite.target.get("status_field", "status")
        if result.status == "done" and isinstance(answer, dict) and field in answer:
            return answer[field], {"answer": answer, "events": len(result.events)}
        return "error:" + (result.status if result.status != "done" else "no_" + field), {"answer": answer, "error": result.error}

    def _extraction(self, case, variant, suite):
        """a pipeline whose answer is {"claims": [...]}, scored against the gold claims of the case"""
        skill = copy.deepcopy(self.core.skills.get(variant.get("skill") or suite.target["skill"]))
        if skill is None:
            raise SuiteError("there is no skill '%s'" % (variant.get("skill") or suite.target["skill"]))
        for key in ("pipeline", "model"):
            if variant.get(key):
                skill[key] = variant[key] if key == "pipeline" else ({"profile": variant[key]} if variant[key] in ("light", "full", "current") else {"name": variant[key]})
        result = self.core.runner.run(skill, self.core.graph(skill)[0], case["input"], task="eval:" + suite.name)
        if result.status != "done" or not isinstance(result.answer, dict):
            return "error:" + (result.status if result.status != "done" else "no_answer"), {"error": result.error, "answer": result.answer}
        claims = result.answer.get("claims")
        if not isinstance(claims, list):
            return "error:no_claims", {"answer": result.answer}
        score = extraction.score_extraction(case["input"]["text"], claims, case["gold"])
        return ("pass" if score["ok"] else "fail"), {"claims": claims, "score": score}

    # -- a run --
    def run(self, suite, variant=None, repeats=1, tags=None, only=None, limit=None, progress=None):
        variant = dict({"name": "default"}, **(variant or {}))
        cases = suite.select(tags, only, limit)
        target = self.targets.get(suite.target["kind"])
        if target is None:
            raise SuiteError("the harness has no target of kind '%s'" % suite.target["kind"])
        header = {"suite": suite.name, "variant": variant, "repeats": repeats, "cases": len(cases), "started": self._clock(), "target": suite.target}
        if suite.target["kind"] == "pipeline" and self.core is not None:
            skill = self.core.skills.get(variant.get("skill") or suite.target["skill"])
            if skill is not None:
                header["pipeline"] = variant.get("pipeline") or skill["pipeline"]
                header["skill_version"] = skill["version"]
        records, total = [], len(cases) * repeats
        for repeat in range(repeats):
            for case in cases:
                record = self._run_case(target, suite, case, variant, repeat)
                records.append(record)
                if progress:
                    progress(len(records), total, record)
        header["finished"] = self._clock()
        return Run(header, records)

    def _run_case(self, target, suite, case, variant, repeat):
        before = self.counter.snapshot() if self.counter else (0, 0, 0)
        started = self._clock()
        error, output = None, None
        try:
            status, output = target(case, variant, suite)
        except Exception as exc:                                    # a case that breaks the target is a result, not the end of the run
            status, error = "error:%s" % type(exc).__name__, "%s: %s" % (type(exc).__name__, exc)
        after = self.counter.snapshot() if self.counter else (0, 0, 0)
        record = {"case": case["id"], "repeat": repeat, "tags": case.get("tags", []), "status": status, "expect": case.get("expect"), "truth": case.get("truth"),
                  "seconds": round(self._clock() - started, 3), "calls": after[0] - before[0], "chars_in": after[1] - before[1], "chars_out": after[2] - before[2],
                  "output": _clip(output)}
        if error:
            record["error"] = error
        if isinstance(output, dict) and isinstance(output.get("score"), dict):
            record["score"] = output["score"]
        return record


# --- reports -----------------------------------------------------------------------------------------------------------------------------

def _pct(r):
    if r["rate"] is None:
        return "n/a"
    return "%5.1f%%  (95%% interval %.0f to %.0f%%, %d of %d)" % (100 * r["rate"], 100 * r["low"], 100 * r["high"], r["k"], r["n"])


def format_report(run, worst=8):
    h, records = run.header, run.records
    lines = ["suite %s, variant %s: %d cases x %d run(s)%s" % (h["suite"], h["variant"]["name"], h["cases"], h["repeats"],
                                                                "  [pipeline %s]" % h["pipeline"] if h.get("pipeline") else ""),
             "run on %s, %s" % (time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(h["started"])), ", ".join("%s=%s" % (k, v) for k, v in h["variant"].items() if k != "name") or "no changes to the defaults")]
    match = metrics.match_metrics(records)
    if match["n"]:
        lines += ["", "behaves as expected:   " + _pct(match["match"])]
        for r in match["mismatches"][:worst]:
            lines.append("   MISMATCH %-22s got %-14s expected %-14s %s" % (r["case"], r["status"], r["expect"], r.get("error", "")))
        if len(match["mismatches"]) > worst:
            lines.append("   ... and %d more" % (len(match["mismatches"]) - worst))
    v = metrics.verification_metrics(records)
    if v["n"]:
        c = v["counts"]
        lines += ["", "as a verifier, on %d claims (%d true, %d false):" % (v["n"], v["true_claims"], v["false_claims"]),
                  "   decided (coverage)   " + _pct(v["coverage"]), "   right among decided  " + _pct(v["accuracy_decided"]), "   right overall        " + _pct(v["accuracy_overall"]),
                  "   FALSE PASS           " + _pct(v["false_pass"]) + "   <- a wrong claim that passed", "   false fail           " + _pct(v["false_fail"]),
                  "   precision of pass    " + _pct(v["precision_pass"]), "   precision of fail    " + _pct(v["precision_fail"]), "   errors               " + _pct(v["errors"]),
                  "   confusion: pass/true %d  pass/false %d  fail/false %d  fail/true %d  abstained true %d  abstained false %d" %
                  (c["tp"], c["fp"], c["tn"], c["fn"], c["abstain_true"], c["abstain_false"])]
        wrong = [r for r in records if r.get("truth") is not None and not metrics.is_right(r)]
        for r in wrong[:worst]:
            lines.append("   WRONG %-24s said %-14s truth %s" % (r["case"], r["status"], r["truth"]))
    ex = metrics.extraction_metrics(records)
    if ex["cases"]:
        pr = lambda r: "n/a" if r["rate"] is None else "%.1f%% (%d of %d)" % (100 * r["rate"], r["k"], r["n"])   # noqa: E731
        lines += ["", "as an extractor, on %d texts with %d claims to find:" % (ex["cases"], ex["gold"]),
                  "   precision (what it found is right)   " + pr(ex["precision"]) + "  [%d claims found]" % ex["predicted"],
                  "   recall (what is there, it found)     " + pr(ex["recall"]), "   F1                                   " + ("n/a" if ex["f1"] is None else "%.3f" % ex["f1"]),
                  "   texts extracted perfectly            " + pr(ex["perfect"]),
                  "   texts without claims left clean      " + pr(ex["empty_clean"]) + "   <- an invented claim there",
                  "   claims whose text is not in the source " + pr(ex["unanchored"]),
                  "   problems: " + ", ".join("%s %d" % (k, v) for k, v in ex["problems"].items() if v) if any(ex["problems"].values()) else "   no problems"]
        bad = [r for r in records if isinstance(r.get("score"), dict) and not r["score"]["ok"]]
        for r in bad[:worst]:
            s = r["score"]
            parts = [("missed " + "; ".join(m["anchor"][:40] for m in s["missed"])) if s["missed"] else "", ("wrong data " + str([w["keys"] for w in s["wrong_data"]])) if s["wrong_data"] else "",
                     ("wrong type " + str([(w["wanted"], w["got"]) for w in s["wrong_type"]])) if s["wrong_type"] else "", ("spurious " + str(len(s["spurious"]))) if s["spurious"] else "",
                     ("duplicate " + str(len(s["duplicates"]))) if s["duplicates"] else "", ("unanchored " + str(len(s["unanchored"]))) if s["unanchored"] else ""]
            lines.append("   NOT PERFECT %-22s %s" % (r["case"], " | ".join(x for x in parts if x)))
    table = metrics.breakdown(records)
    if len(table) > 1:
        lines += ["", "by tag (right / cases):"]
        lines += ["   %-22s %s" % (tag, _pct(r)) for tag, r in table.items()]
    if h["repeats"] > 1:
        lines += ["", "stability over repeats (same status every time): " + _pct(metrics.stability(records))]
    cost = metrics.cost(records)
    lines += ["", "cost: %.1f s in total, %.2f s per run, %d model calls, %d characters sent, %d received" % (cost["seconds"], cost["seconds_per_run"], cost["calls"], cost["chars_in"], cost["chars_out"])]
    return "\n".join(lines)


def format_compare(run_a, run_b):
    c = metrics.compare(run_a.records, run_b.records)
    name = lambda r: "%s/%s" % (r.header["suite"], r.header["variant"]["name"])   # noqa: E731
    lines = ["A = %s    B = %s" % (name(run_a), name(run_b)), "on the %d cases both ran (a case with repeats counts as the share of right runs):" % c["cases"],
             "   A right on %.1f, B right on %.1f" % (c["a_right"], c["b_right"]),
             "   only A right: %d   only B right: %d   exact sign test p = %.3f %s" % (len(c["only_a"]), len(c["only_b"]), c["p_value"],
                                                                                         "(a difference you can believe)" if c["p_value"] < 0.05 else "(not distinguishable from chance with these cases)")]
    if c["only_a"]:
        lines.append("   only A: " + ", ".join(c["only_a"][:15]))
    if c["only_b"]:
        lines.append("   only B: " + ", ".join(c["only_b"][:15]))
    for label, run in (("A", run_a), ("B", run_b)):
        v, k = metrics.verification_metrics(run.records), metrics.cost(run.records)
        if v["n"]:
            lines.append("   %s: false pass %s, coverage %s, %.1f s per run, %d calls" % (label, "n/a" if v["false_pass"]["rate"] is None else "%d of %d" % (v["false_pass"]["k"], v["false_pass"]["n"]),
                                                                                         "n/a" if v["coverage"]["rate"] is None else "%.0f%%" % (100 * v["coverage"]["rate"]), k["seconds_per_run"], k["calls"]))
    if c["missing_in_a"] or c["missing_in_b"]:
        lines.append("   not in both: %d only in B, %d only in A" % (len(c["missing_in_a"]), len(c["missing_in_b"])))
    return "\n".join(lines)
