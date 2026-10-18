"""
Tests for the library of nodes and pipelines: entry validation, loading and the rules for files, expansion into runner graphs (wiring, parameters, safety), version
resolution, status decisions, the SQLite index, selection with reasons, statistics from real runs, cases, drafts, and the Core on top of it.
Run with the MIA virtualenv: python tests/test_library.py
"""
import copy
import json
import os
import sqlite3
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import library as L                                   # noqa: E402
from core import Core                                 # noqa: E402
from pipeline import PipelineError, Tool              # noqa: E402

SHIPPED = os.path.join(REPO, "library")


def node(entry_id="check.quote", version=1, kind="code", **changes):
    entry = {"id": entry_id, "version": version, "kind": kind, "title": "Quote check", "description": "d", "tags": ["check", "exact"],
             "applies_to": {"claim_types": ["quotation"], "tasks": ["research"]},
             "inputs": {"schema": {"type": "object", "required": ["quote", "page"], "properties": {"quote": {"type": "string"}, "page": {"type": "string"}}}},
             "params": {"strict": {"default": True}},
             "body": {"function": "quote_in_source"}, "cost": {"seconds": 0.01}, "safety": {"reads_web": False, "runs_code": False}, "status": "trusted",
             "origin": {"by": "manual"}}
    if kind == "model":
        entry["body"] = {"template": "Is {{claim}} supported by {{passage}}?", "schema": {"type": "object", "required": ["verdict"]}}
        entry["inputs"] = {"schema": {"type": "object", "required": ["claim", "passage"], "properties": {"claim": {"type": "string"}, "passage": {"type": "string"}}}}
        entry["params"] = {}
    if kind == "tool":
        entry["body"] = {"tool": "web_search"}
        entry["safety"] = {"reads_web": True, "runs_code": False}
        entry["needs"] = {"tools": ["web_search"]}
        entry["inputs"] = {"schema": {"type": "object", "required": ["query"], "properties": {"query": {"type": "string"}}}}
        entry["params"] = {}
    entry.update(changes)
    return entry


def pipeline(entry_id="verify.quote", version=1, nodes=None, **changes):
    entry = {"id": entry_id, "version": version, "title": "Verify a quote", "description": "d", "goal": "g", "tags": ["verify"],
             "applies_to": {"claim_types": ["quotation"]}, "cost_class": "cheap", "result": "verdict",
             "nodes": nodes if nodes is not None else [{"id": "q", "use": "check.quote@1", "wire": {"quote": "$input.quote", "page": "$input.page"}, "output": "verdict"}],
             "status": "trusted", "origin": {"by": "manual"}}
    entry.update(changes)
    return entry


def write(root, entry_type, entry, name=None):
    path = os.path.join(root, entry_type + "s", entry["id"], name or "%d.json" % entry["version"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(entry, fp)
    return path


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.shipped = os.path.join(self.tmp.name, "library")
        self.user = os.path.join(self.tmp.name, "user")
        self.index = os.path.join(self.tmp.name, "library.sqlite")

    def tearDown(self):
        self.tmp.cleanup()

    def lib(self, user=True, index=True):
        return L.Library(self.shipped, self.user if user else None, self.index if index else None)


class ValidationTests(unittest.TestCase):
    def test_good_entries_pass(self):
        for kind in ("code", "model", "tool"):
            self.assertEqual(L.validate_node(node(kind=kind)), [], kind)
        self.assertEqual(L.validate_pipeline_entry(pipeline()), [])

    def test_node_problems(self):
        cases = [({"id": "Bad Id"}, "'id'"), ({"version": 0}, "'version'"), ({"version": True}, "'version'"), ({"title": " "}, "'title'"),
                 ({"kind": "wat"}, "'kind'"), ({"body": {}}, "body.function"), ({"body": "x"}, "'body'"), ({"tags": "x"}, "'tags'"),
                 ({"applies_to": {"tasks": "research"}}, "'applies_to'"), ({"status": "great"}, "'status'"), ({"safety": {"reads_web": "yes"}}, "'safety'"),
                 ({"safety": {"flies": True}}, "'safety'"), ({"typo_field": 1}, "unknown field 'typo_field'"), ({"params": {"a": 1}}, "'params'"),
                 ({"cost": {"seconds": "slow"}}, "'cost'"), ({"kind": "script", "body": {"script": "print(1)"}}, "runs_code")]
        for changes, expected in cases:
            self.assertIn(expected, "; ".join(L.validate_node(node(**changes))), changes)
        self.assertTrue(L.validate_node("text"))
        model = node(kind="model")
        model["body"]["template"] = 5
        self.assertIn("body.template", "; ".join(L.validate_node(model)))

    def test_pipeline_problems(self):
        for changes, expected in (({"nodes": []}, "'nodes'"), ({"result": ""}, "'result'"), ({"cost_class": "huge"}, "'cost_class'"), ({"id": "X"}, "'id'")):
            self.assertIn(expected, "; ".join(L.validate_pipeline_entry(pipeline(**changes))), changes)

    def test_refs(self):
        self.assertEqual(L.split_ref("check.x@2"), ("check.x", 2))
        self.assertEqual(L.split_ref("check.x"), ("check.x", None))
        for bad in ("Check", "check.x@", "check.x@a", "", "a b"):
            with self.assertRaises(L.LibraryError):
                L.split_ref(bad)


class ShippedTests(unittest.TestCase):
    def test_the_shipped_library_is_valid_and_complete(self):
        lib = L.Library(SHIPPED)
        self.assertEqual(lib.errors, {})
        self.assertEqual(lib.warnings, [])
        self.assertEqual({e["id"] for e in lib.entries("pipeline")}, {"chat", "summarize", "verify.computable"})
        self.assertGreaterEqual({e["id"] for e in lib.entries("node")}, {"code.converse", "view.summarize", "tool.web_search", "tool.fetch_page", "code.chunk_text",
                                                                          "code.untrusted_wrap", "check.injection_signals"})
        graph, uses, safety = lib.expand(lib.resolve("summarize"))
        self.assertEqual((uses, safety), (["view.summarize@1"], {"reads_web": False, "runs_code": False}))
        model = graph["nodes"][0]
        self.assertEqual((model["kind"], model["library"]), ("model", "view.summarize@1"))
        self.assertIn("{{sentences}}", model["template"])
        self.assertEqual(model["schema_def"]["required"], ["summary", "key_points"])
        self.assertEqual(model["inputs"], {"text": "$input.text", "sentences": "$input.sentences"})
        self.assertEqual(model["plain"], "summarizing the text in {{input.sentences}} sentences")

    def test_web_nodes_declare_their_safety(self):
        lib = L.Library(SHIPPED)
        for ref in ("tool.web_search", "tool.fetch_page"):
            self.assertTrue(lib.resolve(ref, "node")["safety"]["reads_web"])
        self.assertFalse(lib.resolve("code.chunk_text", "node")["safety"]["reads_web"])


class LoadingTests(Base):
    def test_files_must_match_their_entry(self):
        write(self.shipped, "node", node())
        write(self.shipped, "node", node("check.other"), name="7.json")                 # file name does not match the version
        broken = os.path.join(self.shipped, "nodes", "check.broken")
        os.makedirs(broken)
        with open(os.path.join(broken, "1.json"), "w") as fp:
            fp.write("{not json")
        write(self.shipped, "node", node("check.bad", kind="wat"))
        lib = self.lib()
        self.assertEqual([e["id"] for e in lib.entries("node")], ["check.quote"])         # the broken ones do not stop the rest
        messages = " | ".join(lib.errors.values())
        for part in ("must be check.other/1.json", "cannot be read", "'kind'"):
            self.assertIn(part, messages)

    def test_a_version_cannot_exist_twice(self):
        write(self.shipped, "node", node())
        write(self.user, "node", node(title="Changed under the same version"))
        lib = self.lib()
        self.assertEqual(lib.resolve("check.quote@1", "node")["title"], "Quote check")
        self.assertIn("exists already", list(lib.errors.values())[0])

    def test_pipelines_with_broken_references_are_reported_and_skipped(self):
        write(self.shipped, "node", node())
        write(self.shipped, "pipeline", pipeline())
        write(self.shipped, "pipeline", pipeline("verify.missing", nodes=[{"id": "q", "use": "check.nothing@1"}]))
        lib = self.lib()
        self.assertEqual([e["id"] for e in lib.entries("pipeline")], ["verify.quote"])
        self.assertIn("check.nothing@1", " ".join(lib.errors.values()))

    def test_user_entries_are_loaded_next_to_the_shipped_ones(self):
        write(self.shipped, "node", node())
        write(self.user, "node", node("check.mine"))
        self.assertEqual([e["id"] for e in self.lib().entries("node")], ["check.mine", "check.quote"])
        self.assertEqual(self.lib().resolve("check.mine", "node")["_source"], "user")


class ExpansionTests(Base):
    def expand(self, nodes, extra_nodes=()):
        write(self.shipped, "node", node())
        write(self.shipped, "node", node("view.entail", kind="model"))
        write(self.shipped, "node", node("tool.web_search", kind="tool"))
        for entry in extra_nodes:
            write(self.shipped, "node", entry)
        write(self.shipped, "pipeline", pipeline(nodes=nodes))
        lib = self.lib()
        if lib.errors:
            raise L.LibraryError(" ".join(lib.errors.values()))
        return lib.expand(lib.resolve("verify.quote"))

    def test_wiring_parameters_and_kinds(self):
        graph, uses, safety = self.expand([
            {"id": "q", "use": "check.quote@1", "wire": {"quote": "$input.q", "page": "$p"}, "params": {"strict": False}, "output": "v", "plain": "checking {{input.q}}"},
            {"id": "e", "use": "view.entail@1", "wire": {"claim": "$c", "passage": "$p"}, "output": "verdict", "on_error": "skip"},
            {"id": "s", "use": "tool.web_search@1", "wire": {"query": "$input.q"}, "output": "found"}])
        q, e, s = graph["nodes"]
        self.assertEqual((q["kind"], q["function"], q["args"], q["plain"]), ("code", "quote_in_source", {"strict": False, "quote": "$input.q", "page": "$p"}, "checking {{input.q}}"))
        self.assertEqual((e["kind"], e["template"], e["inputs"], e["on_error"]), ("model", "Is {{claim}} supported by {{passage}}?", {"claim": "$c", "passage": "$p"}, "skip"))
        self.assertEqual((s["kind"], s["tool"], s["args"]), ("tool", "web_search", {"query": "$input.q"}))
        self.assertEqual(uses, ["check.quote@1", "tool.web_search@1", "view.entail@1"])
        self.assertEqual(safety, {"reads_web": True, "runs_code": False})                 # the maximum of the nodes
        self.assertEqual((graph["name"], graph["version"], graph["result"]), ("verify.quote", 1, "verdict"))
        self.assertEqual(q["library"], "check.quote@1")

    def test_default_parameters_apply_when_not_set(self):
        graph = self.expand([{"id": "q", "use": "check.quote@1", "wire": {"quote": "$a", "page": "$b"}, "output": "v"}])[0]
        self.assertEqual(graph["nodes"][0]["args"]["strict"], True)
        self.assertEqual(graph["nodes"][0]["plain"], "Quote check")                         # the title when no description is given

    def test_references_inside_maps_branches_and_loops(self):
        graph, uses, _ = self.expand([{"id": "m", "kind": "map", "over": "$claims", "as": "claim", "collect": "v", "output": "verdict",
                                       "body": [{"id": "q", "use": "check.quote@1", "wire": {"quote": "$claim", "page": "$p"}, "output": "v"}]},
                                      {"id": "b", "kind": "branch", "if": {"ref": "x", "op": "true"},
                                       "then": [{"id": "q2", "use": "check.quote@1", "wire": {"quote": "$a", "page": "$p"}}]}])
        self.assertEqual(graph["nodes"][0]["body"][0]["library"], "check.quote@1")
        self.assertEqual(graph["nodes"][1]["then"][0]["function"], "quote_in_source")
        self.assertEqual(uses, ["check.quote@1"])

    def test_mistakes_are_named(self):
        bad = [([{"id": "q", "use": "check.quote", "wire": {"quote": "$a", "page": "$b"}}], "pin the version"),
               ([{"id": "q", "use": "check.quote@9", "wire": {}}], "no node 'check.quote@9'"),
               ([{"id": "q", "use": "check.quote@1", "wire": {"quote": "$a", "page": "$b", "colour": "$c"}}], "no input 'colour'"),
               ([{"id": "q", "use": "check.quote@1", "wire": {"quote": "$a"}}], "required input 'page'"),
               ([{"id": "q", "use": "check.quote@1", "wire": {"quote": "$a", "page": "$b"}, "params": {"loud": 1}}], "no parameter 'loud'"),
               ([{"id": "q", "use": "check.quote@1", "wire": {"quote": "$a", "page": "$b", "strict": True}}], "no input 'strict'"),
               ([{"id": "q", "use": "check.quote@1", "wire": {"quote": "$a", "page": "$b"}, "shout": 1}], "unknown field 'shout'"),
               ([{"id": "bad id!", "use": "check.quote@1", "wire": {"quote": "$a", "page": "$b"}}], "needs an id")]
        for nodes, expected in bad:
            with self.assertRaises(L.LibraryError, msg=expected) as raised:
                self.expand(nodes)
            self.assertIn(expected, str(raised.exception))

    def test_script_nodes_expand_into_sandbox_operations(self):
        script = node("script.calc", kind="script", body={"script": "result = data['x'] * 2", "limits": {"timeout": 3}}, safety={"runs_code": True},
                      inputs={"schema": {"type": "object", "required": ["x"], "properties": {"x": {"type": "number"}}}}, params={})
        graph, uses, safety = self.expand([{"id": "s", "use": "script.calc@1", "wire": {"x": "$input.x"}, "output": "out"},
                                           {"id": "t", "use": "script.calc@1", "wire": {"x": "$input.x"}, "tainted": True, "stakes": "high", "output": "out2"}], extra_nodes=[script])
        first, second = graph["nodes"]
        self.assertEqual((first["kind"], first["script"], first["data"], first["limits"], first["web"]), ("script", "result = data['x'] * 2", {"x": "$input.x"}, {"timeout": 3}, False))
        self.assertEqual(first["operation"], {"kind": "compute", "origin": "library", "tainted": False, "stakes": "normal"})      # a trusted, pinned script
        self.assertEqual(second["operation"], {"kind": "compute", "origin": "library", "tainted": True, "stakes": "high"})        # the pipeline says what its input is
        self.assertEqual(safety, {"reads_web": False, "runs_code": True})
        draft = node("script.draft", kind="script", status="draft", body={"script": "result = 1"}, safety={"runs_code": True},
                     inputs={"schema": {"type": "object", "properties": {}}}, params={})
        graph = self.expand([{"id": "d", "use": "script.draft@1"}], extra_nodes=[draft])[0]
        self.assertEqual(graph["nodes"][0]["operation"]["origin"], "model")                                                       # a draft is not trusted like a library script

    def test_script_nodes_with_web_access_must_say_so(self):
        web = node("script.web", kind="script", body={"script": "result = 1", "web": True}, safety={"runs_code": True})
        self.assertIn("reads_web", "; ".join(L.validate_node(web)))
        web["safety"] = {"runs_code": True, "reads_web": True}
        self.assertEqual(L.validate_node(web), [])


class ResolveAndStatusTests(Base):
    def test_resolution_prefers_the_highest_usable_version(self):
        write(self.shipped, "node", node(version=1, status="trusted"))
        write(self.shipped, "node", node(version=2, status="tested"))
        write(self.shipped, "node", node(version=3, status="draft"))
        lib = self.lib()
        self.assertEqual(lib.resolve("check.quote", "node")["version"], 2)               # the draft is not used unless asked for
        self.assertEqual(lib.resolve("check.quote", "node", allow_draft=True)["version"], 3)
        self.assertEqual(lib.resolve("check.quote@3", "node")["status"], "draft")        # an exact reference may name a draft
        self.assertEqual(lib.versions("check.quote", "node"), [1, 2, 3])

    def test_retired_and_missing_entries(self):
        write(self.shipped, "node", node(version=1, status="retired"))
        write(self.shipped, "node", node("check.drafty", status="draft"))
        lib = self.lib()
        for ref, text in (("check.quote", "no usable"), ("check.quote@1", "retired"), ("check.nothing", "no usable"), ("check.nothing@1", "no node"),
                          ("check.drafty", "only drafts")):
            with self.assertRaises(L.LibraryError, msg=ref) as raised:
                lib.resolve(ref, "node")
            self.assertIn(text, str(raised.exception))

    def test_status_decisions_live_outside_the_immutable_files(self):
        path = write(self.shipped, "node", node(status="draft"))
        before = open(path).read()
        lib = self.lib()
        lib.set_status("check.quote@1", "tested", note="passed 30 cases")
        self.assertEqual(lib.resolve("check.quote", "node")["status"], "tested")
        self.assertEqual(open(path).read(), before)                                       # the shipped file did not change
        decision = json.load(open(os.path.join(self.user, "status.json")))["check.quote@1"]
        self.assertEqual((decision["status"], decision["note"], decision["by"]), ("tested", "passed 30 cases", "user"))
        self.assertEqual(self.lib().resolve("check.quote", "node")["status"], "tested")   # survives a restart
        self.lib().set_status("check.quote@1", "retired")
        with self.assertRaises(L.LibraryError):
            self.lib().resolve("check.quote@1", "node")
        for ref, status in (("check.quote", "tested"), ("check.nothing@1", "tested"), ("check.quote@1", "awesome")):
            with self.assertRaises(L.LibraryError, msg=ref):
                lib.set_status(ref, status)

    def test_a_broken_status_file_is_ignored_with_a_warning(self):
        write(self.shipped, "node", node(status="draft"))
        os.makedirs(self.user)
        with open(os.path.join(self.user, "status.json"), "w") as fp:
            fp.write("{broken")
        lib = self.lib()
        self.assertEqual(lib.resolve("check.quote@1", "node")["status"], "draft")
        self.assertIn("status decisions", lib.warnings[0])


class IndexTests(Base):
    def test_index_content_and_dependencies(self):
        write(self.shipped, "node", node())
        write(self.shipped, "pipeline", pipeline())
        lib = self.lib()
        self.assertEqual(lib.used_by("check.quote@1"), ["verify.quote@1"])
        with sqlite3.connect(self.index) as db:
            rows = {r[0]: r for r in db.execute("SELECT ref, type, kind, status, tags FROM entries")}
        self.assertEqual(rows["check.quote@1"][1:4], ("node", "code", "trusted"))
        self.assertEqual(rows["verify.quote@1"][1], "pipeline")
        self.assertEqual(json.loads(rows["check.quote@1"][4]), ["check", "exact"])

    def test_the_index_is_rebuilt_from_the_files(self):
        write(self.shipped, "node", node())
        self.lib()
        os.remove(self.index)
        lib = self.lib()
        self.assertEqual(lib.used_by("check.quote@1"), [])
        with sqlite3.connect(self.index) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM entries").fetchone()[0], 1)

    def test_a_changed_version_is_noticed(self):
        path = write(self.shipped, "node", node())
        self.lib()
        entry = node(description="quietly changed")
        with open(path, "w") as fp:
            json.dump(entry, fp)
        warnings = self.lib().warnings
        self.assertEqual(len(warnings), 1)
        self.assertIn("immutable", warnings[0])


class SelectionTests(Base):
    def setUp(self):
        super().setUp()
        write(self.shipped, "node", node("check.quote"))
        write(self.shipped, "node", node("check.web", kind="tool", title="Web confirm", tags=["check", "web"], applies_to={"claim_types": ["fact"]}, cost={"seconds": 20}))
        write(self.shipped, "node", node("check.draftcheck", status="draft"))
        write(self.shipped, "node", node("check.general", title="General", applies_to={}, status="tested", cost={"seconds": 30, "tokens": 2000}))
        write(self.shipped, "node", node("check.sandboxed", title="Script", needs={"sandbox": True}, safety={"runs_code": True, "reads_web": False}))

    def refs(self, result):
        return [c["ref"] for c in result["selected"]]

    def test_hard_filters_with_reasons(self):
        lib = self.lib()
        result = lib.select("node", tags=["check"], applies_to={"claim_type": "quotation"})
        dropped = {d["ref"]: d["reason"] for d in result["dropped"]}
        self.assertIn("check.quote@1", self.refs(result))
        self.assertIn("check.general@1", self.refs(result))                                 # declares nothing: applies to everything
        self.assertEqual(dropped["check.draftcheck@1"], "status is draft")
        result = lib.select("node", applies_to={"claims": "x"})
        self.assertIn("check.quote@1", self.refs(result))                                  # unknown keys do not exclude
        result = lib.select("node", tags=["web"], applies_to={"claim_types": "fact"})
        self.assertEqual(self.refs(result), ["check.web@1"])
        dropped = {d["ref"]: d["reason"] for d in lib.select("node", tags=["check"], applies_to={"claim_types": "fact"})["dropped"]}
        self.assertIn("does not apply to claim_types=fact", dropped["check.quote@1"])
        self.assertIn("lacks tag", {d["ref"]: d["reason"] for d in lib.select("node", tags=["nope"])["dropped"]}["check.quote@1"])

    def test_budget_tools_sandbox_and_safety(self):
        lib = self.lib()
        dropped = lambda **kw: {d["ref"]: d["reason"] for d in lib.select("node", **kw)["dropped"]}   # noqa: E731
        self.assertIn("more than 10.0 s", dropped(max_seconds=10)["check.web@1"])
        self.assertIn("more than 1000", dropped(max_tokens=1000)["check.general@1"])
        self.assertIn("needs the tool web_search", dropped(tools=["fetch_page"])["check.web@1"])
        self.assertIn("sandbox", dropped(sandbox=False)["check.sandboxed@1"])
        self.assertNotIn("check.sandboxed@1", dropped(sandbox=True))
        self.assertEqual(dropped(allow_web=False)["check.web@1"], "reads the web")
        self.assertEqual(dropped(allow_code=False)["check.sandboxed@1"], "runs code")
        self.assertEqual(dropped(statuses=("trusted",))["check.general@1"], "status is tested")

    def test_ranking_prefers_specific_trusted_and_proven_entries(self):
        lib = self.lib()
        result = lib.select("node", tags=["check"], applies_to={"claim_types": "quotation", "tasks": "research"})
        self.assertEqual(self.refs(result)[0], "check.quote@1")                              # declares both keys and is trusted
        why = result["selected"][0]["why"]
        self.assertIn("declares claim_types, tasks", why)
        self.assertIn("trusted", why)
        self.assertIn("no measurements yet", why)

    def test_measured_results_change_the_ranking(self):
        write(self.shipped, "node", node("check.quote2", title="Other quote check"))
        lib = self.lib()
        base = self.refs(lib.select("node", tags=["check"], applies_to={"claim_types": "quotation"}))
        self.assertEqual(base[:2], ["check.quote2@1", "check.quote@1"] if base[0] == "check.quote2@1" else ["check.quote@1", "check.quote2@1"])
        runs = []
        for ref, ok in (("check.quote@1", False), ("check.quote2@1", True)):
            for _ in range(4):
                runs.append({"task": "research", "pipeline": None, "events": [{"kind": "start", "node": "n", "library": ref, "at": 0.0, "item": None},
                                                                               {"kind": "done" if ok else "error", "node": "n", "library": ref, "at": 0.5, "item": None}]})
        lib.recompute_stats(runs)
        self.assertEqual(lib.stats("check.quote2@1"), {"runs": 4, "ok": 4, "errors": 0, "seconds": 0.5})
        self.assertEqual(lib.stats("check.quote@1", "research")["errors"], 4)
        self.assertIsNone(lib.stats("check.quote@1", "chat"))
        result = lib.select("node", tags=["check"], applies_to={"claim_types": "quotation"}, task="research")
        self.assertEqual(self.refs(result)[0], "check.quote2@1")
        self.assertIn("4 of 4 runs ok", " ".join(result["selected"][0]["why"]))

    def test_few_runs_are_not_trusted(self):
        lib = self.lib()
        lib.recompute_stats([{"task": "t", "pipeline": None, "events": [{"kind": "start", "node": "n", "library": "check.quote@1", "at": 0, "item": None},
                                                                         {"kind": "done", "node": "n", "library": "check.quote@1", "at": 1, "item": None}]}])
        why = lib.select("node", tags=["check"], applies_to={"claim_types": "quotation"})["selected"][0]["why"]
        self.assertIn("no measurements yet", why)

    def test_search_and_diff(self):
        lib = self.lib()
        self.assertEqual([e["id"] for e in lib.search("web confirm", "node")], ["check.web"])
        self.assertEqual([e["id"] for e in lib.search(None, "node", tags=["web"])], ["check.web"])
        self.assertEqual([e["id"] for e in lib.search(None, "node", kind="tool")], ["check.web"])
        write(self.shipped, "node", node("check.quote", version=2, title="Quote check, normalised"))
        lib = self.lib()
        diff = lib.diff("check.quote@1", "check.quote@2")
        self.assertIn('- "title": "Quote check",', diff)
        self.assertIn("normalised", diff)
        with self.assertRaises(L.LibraryError):
            lib.diff("check.quote@1", "check.quote@9")


class CasesAndDraftsTests(Base):
    def test_cases_are_found_by_common_tags(self):
        lib = self.lib()
        a = lib.add_case("research", "The tower is 330 m high", ["numeric", "fact"], ["check.units@1"], "supported", {"user": "ok"})
        lib.add_case("research", "Paris is in France", ["fact"], [], "supported")
        lib.add_case("research", "unrelated", ["story"], [])
        found = lib.similar_cases(["numeric", "fact"])
        self.assertEqual([c["text"] for c in found], ["The tower is 330 m high", "Paris is in France"])
        self.assertEqual((found[0]["id"], found[0]["common"], found[0]["applied"], found[0]["outcome"]), (a, 2, ["check.units@1"], {"user": "ok"}))
        self.assertEqual(lib.similar_cases(["story"], task="research")[0]["text"], "unrelated")
        self.assertEqual(lib.similar_cases(["nothing"]), [])

    def test_drafts_are_new_versions_in_the_user_folder(self):
        write(self.shipped, "node", node())
        lib = self.lib()
        new = node(version=2, status="trusted", title="Better quote check")
        ref = lib.add_draft("node", new, by="gemma4")
        self.assertEqual(ref, "check.quote@2")
        entry = lib.resolve("check.quote@2", "node")
        self.assertEqual((entry["status"], entry["origin"]["by"], entry["_source"]), ("draft", "gemma4", "user"))     # never trusted on arrival
        self.assertEqual(lib.resolve("check.quote", "node")["version"], 1)                                          # and not used by default
        with self.assertRaises(L.LibraryError) as raised:
            lib.add_draft("node", node(version=2))
        self.assertIn("immutable", str(raised.exception))
        with self.assertRaises(L.LibraryError):
            lib.add_draft("node", node("check.bad", kind="wat"))
        broken_pipeline = pipeline("verify.broken", nodes=[{"id": "q", "use": "check.nothing@1"}])
        with self.assertRaises(L.LibraryError) as raised:
            lib.add_draft("pipeline", broken_pipeline)
        self.assertIn("check.nothing@1", str(raised.exception))
        self.assertFalse(os.path.exists(os.path.join(self.user, "pipelines", "verify.broken")) and os.listdir(os.path.join(self.user, "pipelines", "verify.broken")))
        self.assertEqual(lib.errors, {})


class FakeModel:
    def __init__(self):
        self.calls = []

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        self.calls.append((messages, schema, profile))
        return json.dumps({"summary": "short", "key_points": ["a"]})


class CoreTests(Base):
    def core(self, library, skills, **kwargs):
        os.makedirs(os.path.join(self.tmp.name, "skills"), exist_ok=True)
        for name, text in skills.items():
            with open(os.path.join(self.tmp.name, "skills", name + ".md"), "w") as fp:
                fp.write(text)
        return Core(os.path.join(self.tmp.name, "skills"), library, os.path.join(self.tmp.name, "runs"), **kwargs)

    def test_summarize_runs_from_the_library_and_logs_what_it_used(self):
        skills = {"summarize": open(os.path.join(REPO, "skills", "summarize.md")).read()}
        library = L.Library(SHIPPED, self.user, self.index)
        model = FakeModel()
        core = self.core(library, skills, model=model)
        self.assertEqual(core.check(), {})
        result = core.run("summarize", {"text": "A long text.", "sentences": 2})
        self.assertEqual((result.status, result.answer), ("done", {"summary": "short", "key_points": ["a"]}))
        messages, schema, profile = model.calls[0]
        self.assertIn("at most 2 sentences", messages[1]["content"])
        self.assertIn("A long text.", messages[1]["content"])
        self.assertEqual((messages[0]["role"], profile, schema["required"]), ("system", "light", ["summary", "key_points"]))
        run = core.run_log.read()[0]
        self.assertEqual((run["pipeline"], run["pipeline_version"], run["uses"]), ("summarize", 1, ["view.summarize@1"]))
        self.assertEqual({e["library"] for e in run["events"] if e["kind"] == "start"}, {"view.summarize@1"})

    def test_statistics_come_from_real_runs(self):
        library = L.Library(SHIPPED, self.user, self.index)
        core = self.core(library, {"summarize": open(os.path.join(REPO, "skills", "summarize.md")).read()}, model=FakeModel())
        for _ in range(4):
            core.run("summarize", {"text": "x", "sentences": 1})
        library.recompute_stats(core.run_log.read())
        self.assertEqual(library.stats("summarize@1")["runs"], 4)
        self.assertEqual(library.stats("view.summarize@1", "summarize")["ok"], 4)
        self.assertIn("4 of 4 runs ok", " ".join(library.select("pipeline", tags=["summarize"], task="summarize")["selected"][0]["why"]))

    def test_the_skill_must_allow_what_the_pipeline_needs(self):
        write(self.user, "node", node("tool.web_search", kind="tool"))
        write(self.user, "pipeline", pipeline("research.test", nodes=[{"id": "s", "use": "tool.web_search@1", "wire": {"query": "$input.text"}, "output": "verdict"}]))
        library = L.Library(SHIPPED, self.user, self.index)
        skill = "---\nname: research_test\npipeline: research.test\ntools: [web_search]\n%s---\n"
        core = self.core(library, {"closed": skill.replace("name: research_test", "name: closed") % "", "open": skill.replace("name: research_test", "name: open") % "max_safety: {reads_web: true}\n"},
                         tools={"web_search": Tool(lambda query: {"results": [query]}, "search_calls")})
        with self.assertRaises(PipelineError) as raised:
            core.run("closed", {"text": "q"})
        self.assertIn("reads_web", str(raised.exception))
        self.assertIn("closed", core.check())
        result = core.run("open", {"text": "q"})
        self.assertEqual((result.status, result.answer), ("done", {"results": ["q"]}))
        self.assertNotIn("open", core.check())

    def test_a_missing_pipeline_is_a_clear_error(self):
        core = self.core(L.Library(SHIPPED), {"ghost": "---\nname: ghost\npipeline: nothing\n---\n"})
        with self.assertRaises(PipelineError) as raised:
            core.run("ghost", {})
        self.assertIn("no usable pipeline 'nothing'", str(raised.exception))

    def test_the_library_is_available_to_planning_steps(self):
        core = self.core(L.Library(SHIPPED, self.user, self.index), {})
        found = core._select("pipeline", tags=["summarize"])
        self.assertEqual([c["ref"] for c in found["selected"]], ["summarize@1"])
        described = core._describe("view.summarize@1", "node")
        self.assertEqual(described["kind"], "model")
        self.assertFalse(any(k.startswith("_") for k in described))
        self.assertEqual(set(core.runner.tools) & {"library_select", "library_describe"}, {"library_select", "library_describe"})


if __name__ == "__main__":
    unittest.main()
