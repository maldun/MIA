"""
Tests for the script checks: the contract of a check script (holds + values), the interpretation of every sandbox outcome, the choice of the wall (operation: kind, origin, taint, stakes),
the dispatcher with and without a sandbox, the script node of the runner, and the pipeline in which a model writes the check. The sandbox is real where a test is about the wall and a
fake where it is about the logic; tests that need a real backend are skipped when it is missing. Run with the MIA virtualenv: python tests/test_script_checks.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

import checks as C                                    # noqa: E402
import sandbox as S                                   # noqa: E402
from core import Core                                 # noqa: E402
from library import Library                           # noqa: E402
from pipeline import PipelineError, Tool              # noqa: E402
import test_sandbox as TS                             # noqa: E402

PASS, FAIL, INC, NA = C.PASS, C.FAIL, C.INCONCLUSIVE, C.NOT_APPLICABLE
BWRAP = S.BubblewrapSandbox()
PODMAN = S.PodmanSandbox()
needs_bwrap = unittest.skipUnless(BWRAP.available, "no bubblewrap sandbox: %s" % BWRAP.reason)
needs_podman = unittest.skipUnless(PODMAN.available, "no podman sandbox: %s" % PODMAN.reason)


class FakeRouter:
    """records the operations and answers with a prepared SandboxResult"""

    def __init__(self, result=None):
        self.result, self.calls, self.available = result, [], True

    def run(self, code, data=None, operation=None, broker=None, **kw):
        self.calls.append({"code": code, "data": data, "operation": operation.as_dict() if operation else None, "broker": broker, "kw": kw})
        outcome = self.result
        outcome.script_hash, outcome.backend, outcome.tier = "abc123", "bubblewrap", "standard"
        return outcome

    def available_for(self, operation=None):
        return True


def sr(status="ok", result=None, **kw):
    return S.SandboxResult(status, result=result, **kw)


def holds(value=True, values=None, **extra):
    return {"holds": value, "values": {"x": 1} if values is None else values, **extra}


class ScriptCheckLogic(unittest.TestCase):
    def check(self, outcome, web=False, factory=None, **kwargs):
        router = FakeRouter(outcome)
        kwargs.setdefault("script", "result = 1")
        return C.make_script_check(router, factory, web=web)(**kwargs), router

    def test_the_contract_holds_and_values(self):
        outcome, router = self.check(sr(result=holds(True, {"principal": 1000}, explanation="the sum is 1628.89")))
        self.assertEqual((outcome["status"], outcome["detail"]), (PASS, "the sum is 1628.89"))
        evidence = outcome["evidence"][0]
        self.assertEqual((evidence["values"], evidence["script_hash"], evidence["backend"], evidence["tier"]), ({"principal": 1000}, "abc123", "bubblewrap", "standard"))
        self.assertEqual(self.check(sr(result=holds(False, {"principal": 1000})))[0]["status"], FAIL)
        self.assertEqual(self.check(sr(result=holds(True)))[0]["detail"], "the script confirms the claim")

    def test_a_verdict_without_values_cannot_be_reviewed(self):
        for report in ({"holds": True}, {"holds": True, "values": {}}, {"holds": False, "values": None}, {"holds": True, "values": [1, 2]}):
            outcome = self.check(sr(result=report))[0]
            self.assertEqual(outcome["status"], INC, report)
            self.assertIn("values", outcome["detail"])
        outcome = self.check(sr(result={"holds": "yes", "values": {"a": 1}}))[0]
        self.assertEqual((outcome["status"], outcome["detail"]), (INC, "`holds` must be true or false"))

    def test_expected_value_instead_of_holds(self):
        self.assertEqual(self.check(sr(result={"value": 1628.89}), expect=1628.89)[0]["status"], PASS)
        self.assertEqual(self.check(sr(result={"value": 1628.89}), expect="1,628.9")[0]["status"], PASS)             # the rounding of the claim is allowed
        self.assertEqual(self.check(sr(result={"value": 1628.89}), expect=1700)[0]["status"], FAIL)
        self.assertEqual(self.check(sr(result={"value": "Tuesday"}), expect="Tuesday")[0]["status"], PASS)
        self.assertEqual(self.check(sr(result={"value": "Tuesday"}), expect="Monday")[0]["status"], FAIL)
        for report in ({"value": 5}, "text", None, 5, {"other": 1}):
            self.assertEqual(self.check(sr(result=report))[0]["status"], INC, report)                               # no `holds`, no expectation

    def test_every_sandbox_outcome_is_understood(self):
        cases = [(sr("rejected", problems=["line 1: importing 'os' is not allowed"]), "not run", "importing 'os'"),
                 (sr("unavailable", error={"message": "no strong backend"}), "no sandbox", "no strong backend"),
                 (sr("timeout", error={"message": "the script did not finish within 10 seconds", "line": None}), "did not finish", "10 seconds"),
                 (sr("crashed", error={"message": "the sandbox ended without an answer", "line": None}), "was stopped", "without an answer"),
                 (sr("error", error={"type": "ZeroDivisionError", "message": "division by zero", "line": 3}), "failed", "line 3")]
        for outcome, first, second in cases:
            got = self.check(outcome)[0]
            self.assertEqual(got["status"], INC, outcome.status)
            self.assertIn(first, got["detail"])
            self.assertIn(second, got["detail"])

    def test_a_key_error_names_the_keys_that_exist(self):
        error = sr("error", error={"type": "KeyError", "message": "'data'", "line": 5})
        outcome = self.check(error, data={"numbers": [1, 2], "claimed": 3})[0]
        self.assertEqual(outcome["status"], INC)
        self.assertIn("`data` has only the keys 'numbers', 'claimed'", outcome["detail"])
        self.assertNotIn("has only the keys", self.check(sr("error", error={"type": "ValueError", "message": "x", "line": 1}), data={"a": 1})[0]["detail"])
        self.assertNotIn("has only the keys", self.check(error, data=[1, 2])[0]["detail"])                        # a list has no keys

    def test_the_operation_follows_what_the_script_is(self):
        outcome, router = self.check(sr(result=holds()), tainted=True, origin="external", stakes="high")
        self.assertEqual(router.calls[0]["operation"], {"kind": "compute", "origin": "external", "tainted": True, "stakes": "high"})
        outcome, router = self.check(sr(result=holds()))
        self.assertEqual(router.calls[0]["operation"], {"kind": "compute", "origin": "model", "tainted": False, "stakes": "normal"})
        self.assertEqual((router.calls[0]["kw"]["timeout"], router.calls[0]["broker"]), (10, None))

    def test_web_scripts_get_a_broker_per_run_and_the_strong_kind(self):
        made = []

        class Broker:
            log = [{"op": "get", "arg": "https://a.example/"}]

            def __enter__(self):
                made.append("enter")
                return self

            def __exit__(self, *exc):
                made.append("exit")

        outcome, router = self.check(sr(result=holds()), web=True, factory=Broker)
        self.assertEqual(outcome["status"], PASS)
        self.assertEqual((router.calls[0]["operation"]["kind"], isinstance(router.calls[0]["broker"], Broker), router.calls[0]["kw"]["timeout"]), ("web_script", True, 60))
        self.assertEqual(made, ["enter", "exit"])
        self.assertEqual(outcome["evidence"][0]["web_log"], Broker.log)
        self.assertEqual(self.check(sr(result=holds()), web=True, factory=None)[0]["status"], NA)

    def test_unusable_requests(self):
        for script in ("", "   ", None, 5):
            self.assertEqual(C.make_script_check(FakeRouter(sr()), None)(script)["status"], NA)
        self.assertEqual(C.make_script_check(None, None)("result = 1")["status"], INC)                              # no sandbox configured: never run unprotected

    def test_long_scripts_and_output_are_clipped_in_the_evidence(self):
        outcome = self.check(sr(result=holds(), stdout="y" * 5000), script="result = 1\n# " + "x" * 5000)[0]
        self.assertLess(len(outcome["evidence"][0]["script"]), 1700)
        self.assertLess(len(outcome["evidence"][0]["stdout"]), 600)


COMPOUND = ("from decimal import Decimal\nv = Decimal(str(data['principal'])) * (1 + Decimal(str(data['rate'])) / 100) ** data['years']\n"
            "result = {'holds': abs(float(v) - data['claimed']) <= 0.01, 'values': {'computed': round(float(v), 2), 'claimed': data['claimed']}, 'explanation': 'compound interest recomputed'}\n")


@needs_bwrap
class RealScriptChecks(unittest.TestCase):
    def setUp(self):
        self.router = S.SandboxRouter({"bubblewrap": BWRAP, "podman": PODMAN}, force="bubblewrap")
        self.check = C.make_script_check(self.router)

    def test_a_claim_is_recomputed(self):
        right = self.check(COMPOUND, {"principal": 1000, "rate": 5, "years": 10, "claimed": 1628.89})
        self.assertEqual((right["status"], right["evidence"][0]["values"]["computed"]), (PASS, 1628.89))
        wrong = self.check(COMPOUND, {"principal": 1000, "rate": 5, "years": 10, "claimed": 1700.0})
        self.assertEqual(wrong["status"], FAIL)
        self.assertEqual(wrong["evidence"][0]["values"], {"computed": 1628.89, "claimed": 1700.0})

    def test_bad_scripts_are_inconclusive_and_say_why(self):
        self.assertIn("importing 'os'", self.check("import os\nresult = {'holds': True, 'values': {'a': 1}}")["detail"])
        out = self.check("x = 1\ny = 1 / (x - 1)\nresult = {'holds': True, 'values': {'a': 1}}")
        self.assertEqual(out["status"], INC)
        self.assertIn("line 2", out["detail"])
        out = self.check("while True:\n    pass", timeout=1.5)
        self.assertEqual(out["status"], INC)
        self.assertIn("did not finish", out["detail"])
        self.assertEqual(self.check("result = {'holds': True}")["status"], INC)

    def test_the_script_cannot_reach_out(self):
        out = self.check("import math\nresult = {'holds': True, 'values': {'a': math.pi}}\nweb.get('https://example.com')")
        self.assertEqual(out["status"], INC)                                                                        # `web` is not available without a broker
        self.assertIn("web access", out["detail"])


def library_with(extra_pipelines=(), extra_nodes=()):
    tmp = tempfile.mkdtemp()
    library = Library(os.path.join(REPO, "library"), tmp)
    for entry in extra_nodes:
        library.add_draft("node", entry)
        library.set_status("%s@%d" % (entry["id"], entry["version"]), "trusted")
    for entry in extra_pipelines:
        library.add_draft("pipeline", entry)
        library.set_status("%s@%d" % (entry["id"], entry["version"]), "trusted")
    return library, tmp


def core_for(router, library, tmp, skills=None, model=None, broker_factory=None, tools=None):
    folder = os.path.join(tmp, "skills")
    os.makedirs(folder, exist_ok=True)
    for name, text in (skills or {}).items():
        with open(os.path.join(folder, name + ".md"), "w") as fp:
            fp.write(text)
    return Core(folder, library, os.path.join(tmp, "runs"), model=model, sandbox=router, broker_factory=broker_factory, tools=tools)


class UnavailableBackend:
    name, available, reason = "podman", False, "no image"

    def info(self):
        return {"backend": "podman", "available": False}

    def run(self, *a, **k):
        raise AssertionError("must not run")


@needs_bwrap
class DispatcherWithSandbox(unittest.TestCase):
    CLAIM = {"type": "computable", "text": "1000 at 5% for 10 years is 1628.89", "data": {"script": COMPOUND, "data": {"principal": 1000, "rate": 5, "years": 10, "claimed": 1628.89}}}

    def runner(self, backends=None, **kw):
        library, tmp = library_with()
        router = S.SandboxRouter(backends or {"bubblewrap": BWRAP, "podman": UnavailableBackend()}, **kw)
        return core_for(router, library, tmp).checks

    def test_a_computable_claim_runs_the_script_check(self):
        outcome = self.runner().run(self.CLAIM)
        self.assertEqual((outcome["status"], outcome["verdict"], [t["ref"] for t in outcome["trace"]]), ("pass", "supported", ["check.script@1"]))
        self.assertEqual(outcome["results"][0]["evidence"][0]["tier"], "standard")
        wrong = json.loads(json.dumps(self.CLAIM))
        wrong["data"]["data"]["claimed"] = 2000.0
        self.assertEqual(self.runner().run(wrong)["verdict"], "contradicted")

    def test_without_a_sandbox_the_script_checks_are_not_offered(self):
        library, tmp = library_with()
        outcome = core_for(None, library, tmp).checks.run(self.CLAIM)
        self.assertEqual((outcome["verdict"], outcome["trace"]), ("none", []))                                       # no script ever runs unprotected
        dead = S.SandboxRouter({"bubblewrap": S.BubblewrapSandbox(bwrap="/nonexistent/bwrap"), "podman": UnavailableBackend()})
        self.assertEqual(core_for(dead, library, tmp).checks.run(self.CLAIM)["verdict"], "none")

    def test_a_tainted_claim_needs_the_strong_wall_or_is_skipped(self):
        tainted = dict(self.CLAIM, tainted=True)
        self.assertEqual(self.runner().run(tainted)["verdict"], "none")                                              # podman is missing: skipped, not weakened
        self.assertEqual(self.runner(degrade=True).run(tainted)["results"][0]["evidence"][0]["degraded"], True)      # unless degrading is allowed, and then it is marked
        high = dict(self.CLAIM, stakes="high")
        self.assertEqual(self.runner().run(high)["verdict"], "none")

    @needs_podman
    def test_a_tainted_claim_goes_to_podman(self):
        outcome = self.runner({"bubblewrap": BWRAP, "podman": PODMAN}).run(dict(self.CLAIM, tainted=True))
        evidence = outcome["results"][0]["evidence"][0]
        self.assertEqual((outcome["verdict"], evidence["backend"], evidence["tier"]), ("supported", "podman", "strong"))

    @needs_podman
    def test_a_web_script_runs_through_the_broker_in_podman(self):
        library, tmp = library_with()
        broker, session, _ = TS.make_broker({"https://a.example/page": TS.FakeResponse(TS.BrokerTests.PAGE)})
        script = ("page = web.get('https://a.example/page')\nimport re\nnumbers = [int(n) for n in re.findall(r'\\d+', page['text'])]\n"
                  "result = {'holds': 330 in numbers, 'values': {'found': numbers, 'title': page['title']}, 'explanation': 'the page says 330'}\n")
        router = S.SandboxRouter({"bubblewrap": BWRAP, "podman": PODMAN})
        core = core_for(router, library, tmp, broker_factory=lambda: broker, tools={"web_search": Tool(lambda **k: None, None), "fetch_page": Tool(lambda **k: None, None)})
        claim = {"type": "computable_web", "text": "the page gives 330", "data": {"script": script}}
        self.assertEqual(core.checks.run(claim, include_web=False)["verdict"], "none")                               # web scripts only where the web is allowed
        outcome = core.checks.run(claim, include_web=True)
        evidence = outcome["results"][0]["evidence"][0]
        self.assertEqual((outcome["verdict"], evidence["backend"], evidence["tier"]), ("supported", "podman", "strong"))
        self.assertEqual(evidence["values"], {"found": [330], "title": "Doc"})
        self.assertEqual(session.calls, ["https://a.example/page"])
        self.assertEqual([entry["op"] for entry in evidence["web_log"]], ["get"])

    def test_web_scripts_are_skipped_when_only_the_standard_wall_exists(self):
        claim = {"type": "computable_web", "data": {"script": "result = 1"}}
        library, tmp = library_with()
        router = S.SandboxRouter({"bubblewrap": BWRAP, "podman": UnavailableBackend()})
        core = core_for(router, library, tmp, broker_factory=lambda: None)
        self.assertEqual(core.checks.run(claim, include_web=True)["verdict"], "none")


class FakeModel:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        self.calls.append((messages, schema, profile))
        return self.replies.pop(0)


SKILL = "---\nname: verify\npipeline: verify.computable\nmodel: {profile: light}\nmax_safety: {runs_code: true}\ntools: []\n---\n"


@needs_bwrap
class ComputablePipeline(unittest.TestCase):
    INPUT = {"claim": "1000 at 5 percent for 10 years grows to 1628.89", "data_description": "principal, rate (percent), years, claimed (the claimed result)",
             "data": {"principal": 1000, "rate": 5, "years": 10, "claimed": 1628.89}}

    def core(self, replies, skill=SKILL):
        library, tmp = library_with()
        model = FakeModel([json.dumps(r) if not isinstance(r, str) else r for r in replies])
        router = S.SandboxRouter({"bubblewrap": BWRAP, "podman": UnavailableBackend()})
        return core_for(router, library, tmp, {"verify": skill}, model=model), model

    def test_the_model_writes_the_check_and_the_sandbox_decides(self):
        core, model = self.core([{"script": COMPOUND, "approach": "recompute with decimals"}])
        self.assertEqual(core.check(), {})
        result = core.run("verify", self.INPUT)
        self.assertEqual((result.status, result.answer["status"]), ("done", "pass"))
        self.assertEqual(result.answer["evidence"][0]["values"]["computed"], 1628.89)
        prompt = model.calls[0][0][1]["content"]
        self.assertIn(self.INPUT["claim"], prompt)
        self.assertIn(S.SCRIPT_GUIDE, prompt)                                       # the model is told exactly what a script may use
        self.assertIn("`data` is a dict with the keys: principal (number), rate (number), years (number), claimed (number)", prompt)      # the shape comes from the real data
        self.assertIn(self.INPUT["data_description"], prompt)                       # the hint of the caller is kept
        self.assertNotIn("1628.89 is right", prompt)
        run = core.run_log.read()[0]
        self.assertEqual(run["uses"], ["check.script@1", "code.describe_data@1", "view.fix_check_script@1", "view.write_check_script@1"])
        self.assertEqual(run["pipeline_version"], 2)
        self.assertEqual(len(model.calls), 1)                                       # nothing to repair: one call of the model
        self.assertEqual(run["pipeline"], "verify.computable")

    def test_version_one_stays_available_for_comparisons(self):
        core, model = self.core([{"script": COMPOUND}])
        skill = core.skills.get("verify")
        skill["pipeline"] = "verify.computable@1"
        graph, uses, _ = core.graph(skill)
        self.assertNotIn("code.describe_data@1", uses)
        result = core.runner.run(skill, graph, self.INPUT)
        self.assertEqual(result.answer["status"], "pass")
        self.assertIn(self.INPUT["data_description"], model.calls[0][0][1]["content"])
        self.assertNotIn("`data` is a dict", model.calls[0][0][1]["content"])

    def test_the_repair_sees_the_real_shape_too(self):
        core, model = self.core([{"script": "result = {'holds': True, 'values': {'a': data['data']}}"}, {"script": COMPOUND}])
        result = core.run("verify", self.INPUT)
        self.assertEqual(result.answer["status"], "pass")
        repair_prompt = model.calls[1][0][1]["content"]
        self.assertIn("`data` is a dict with the keys: principal (number)", repair_prompt)
        self.assertIn("`data` has only the keys 'principal', 'rate', 'years', 'claimed'", repair_prompt)      # the KeyError names what exists

    def test_a_wrong_claim_is_contradicted(self):
        core, _ = self.core([{"script": COMPOUND}])
        result = core.run("verify", dict(self.INPUT, data=dict(self.INPUT["data"], claimed=1700.0)))
        self.assertEqual(result.answer["status"], "fail")

    def test_a_script_that_does_not_work_is_repaired_with_the_problem(self):
        broken = "result = {'holds': True, 'values': {'a': undefined_name}}"
        core, model = self.core([{"script": broken}, {"script": COMPOUND}])
        result = core.run("verify", self.INPUT)
        self.assertEqual((result.status, result.answer["status"]), ("done", "pass"))
        self.assertEqual(len(model.calls), 2)
        repair_prompt = model.calls[1][0][1]["content"]
        self.assertIn("undefined_name", repair_prompt)                                # the problem the sandbox reported ...
        self.assertIn(broken, repair_prompt)                                          # ... and the script that caused it
        self.assertIn(S.SCRIPT_GUIDE, repair_prompt)
        kinds = [(e["kind"], e["node"]) for e in result.events if e["node"] in ("fix", "rerun")]
        self.assertEqual(kinds, [("start", "fix"), ("done", "fix"), ("start", "rerun"), ("done", "rerun")])

    def test_repair_stops_after_two_attempts(self):
        broken = {"script": "result = {'holds': True}"}                               # never reports values
        core, model = self.core([broken, broken, broken])
        result = core.run("verify", self.INPUT)
        self.assertEqual((result.answer["status"], len(model.calls)), ("inconclusive", 3))     # the first script and two repairs
        self.assertIn("values", result.answer["detail"])

    def test_a_script_that_retypes_the_input_is_refused(self):
        retyped = "data = {'principal': 1000, 'rate': 5, 'years': 10, 'claimed': 1628.89}\nresult = {'holds': True, 'values': {'a': 1}}"
        core, model = self.core([{"script": retyped}, {"script": COMPOUND}])
        result = core.run("verify", self.INPUT)
        self.assertEqual(result.answer["status"], "pass")
        self.assertIn("must not be reassigned", model.calls[1][0][1]["content"])      # the model is told why the first script was refused

    def test_a_script_that_breaks_the_rules_gets_nowhere(self):
        core, _ = self.core([{"script": "import os\nresult = {'holds': True, 'values': {'a': os.listdir('/')}}"}] * 3)
        result = core.run("verify", self.INPUT)
        self.assertEqual((result.status, result.answer["status"]), ("done", "inconclusive"))
        self.assertIn("importing 'os'", result.answer["detail"])

    def test_the_skill_has_to_allow_running_code(self):
        core, _ = self.core([{"script": COMPOUND}], skill=SKILL.replace("max_safety: {runs_code: true}\n", ""))
        with self.assertRaises(PipelineError) as raised:
            core.run("verify", self.INPUT)
        self.assertIn("runs_code", str(raised.exception))

    def test_the_guide_in_the_prompt_node_is_the_sandbox_guide(self):
        library = Library(os.path.join(REPO, "library"))
        self.assertEqual(library.resolve("view.write_check_script@1", "node")["params"]["guide"]["default"], S.SCRIPT_GUIDE)


@needs_bwrap
class ScriptNodes(unittest.TestCase):
    def pipeline(self, nodes, entry_id="script.demo"):
        return {"id": entry_id, "version": 1, "title": "Script demo", "tags": ["demo"], "result": "out", "nodes": nodes}

    def test_a_stored_script_runs_in_the_sandbox(self):
        library, tmp = library_with([self.pipeline([{"id": "calc", "use": "script.compound_interest@1", "wire": {"principal": "$input.p", "rate": "$input.r", "years": "$input.y"}, "output": "out"}])])
        core = core_for(S.SandboxRouter({"bubblewrap": BWRAP, "podman": UnavailableBackend()}), library, tmp,
                        {"demo": "---\nname: demo\npipeline: script.demo\nmax_safety: {runs_code: true}\n---\n"})
        result = core.run("demo", {"p": 1000, "r": 5, "y": 10})
        self.assertEqual(result.status, "done")
        self.assertEqual((result.answer["status"], result.answer["result"]["value"], result.answer["backend"], result.answer["tier"]), ("ok", 1628.89, "bubblewrap", "standard"))
        events = [e for e in result.events if e["node"] == "calc"]
        self.assertEqual({e["library"] for e in events}, {"script.compound_interest@1"})

    def test_input_that_is_tainted_gets_the_strong_wall(self):
        library, tmp = library_with([self.pipeline([{"id": "calc", "use": "script.compound_interest@1", "wire": {"principal": "$input.p", "rate": "$input.r", "years": "$input.y"},
                                                     "tainted": True, "output": "out"}])])
        core = core_for(S.SandboxRouter({"bubblewrap": BWRAP, "podman": UnavailableBackend()}), library, tmp,
                        {"demo": "---\nname: demo\npipeline: script.demo\nmax_safety: {runs_code: true}\n---\n"})
        result = core.run("demo", {"p": 1000, "r": 5, "y": 10})
        self.assertEqual(result.status, "error")                                                                       # no strong backend: refused, never weakened
        self.assertIn("strong operation", result.error)

    def test_a_failing_script_is_an_error_of_the_node(self):
        broken = {"id": "script.broken", "version": 1, "kind": "script", "title": "Broken", "tags": [], "body": {"script": "result = 1 / 0"}, "safety": {"runs_code": True},
                  "inputs": {"schema": {"type": "object", "properties": {}}}, "status": "trusted"}
        library, tmp = library_with([self.pipeline([{"id": "calc", "use": "script.broken@1", "output": "out"}], "script.bad")], [broken])
        core = core_for(S.SandboxRouter({"bubblewrap": BWRAP}), library, tmp, {"bad": "---\nname: bad\npipeline: script.bad\nmax_safety: {runs_code: true}\n---\n"})
        result = core.run("bad", {})
        self.assertEqual(result.status, "error")
        self.assertIn("division by zero", result.error)

    def test_without_a_sandbox_a_script_node_cannot_run(self):
        library, tmp = library_with([self.pipeline([{"id": "calc", "use": "script.compound_interest@1", "wire": {"principal": 1, "rate": 1, "years": 1}, "output": "out"}])])
        core = core_for(None, library, tmp, {"demo": "---\nname: demo\npipeline: script.demo\nmax_safety: {runs_code: true}\n---\n"})
        result = core.run("demo", {})
        self.assertEqual(result.status, "error")
        self.assertIn("no sandbox", result.error)


if __name__ == "__main__":
    unittest.main()
