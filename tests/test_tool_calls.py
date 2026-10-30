"""
TC-TLS-001 (REQ-TLS-001) and TC-TLS-008 (REQ-TLS-008): the one door to the tools (IF-402, tool_calls.py) offers the code checks to every workflow,
counts every call against the limits of its run and labels every output with its trust. The web, the scholarly sources and the sandbox are fakes.
Run with: python tests/test_tool_calls.py
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                  # noqa: E402
from tool_calls import ToolCalls, ToolCallError, TOOLS   # noqa: E402

PAGE = "The tower is 330 m high. It was finished in 1889."


def fake_search(query):
    return {"query": query, "results": [{"title": "A", "url": "https://example.org/a", "snippet": "The tower is 330 m high."}]}


def fake_fetch(url):
    if url != "https://example.org/a":
        raise OSError("not found")
    return {"ref": url, "url": url, "title": "A", "text": PAGE}


class FakeScholar:
    def search(self, query, until=None, since=None):
        return {"works": [{"doi": "10.1/x", "title": "On towers", "date": "2001"}], "errors": {}, "dropped": []}


def fake_trust(url):
    return {"class": "web", "score": 0.5}


def tools():
    return ToolCalls(web_search=fake_search, fetch_page=fake_fetch, scholar=FakeScholar(), trust=fake_trust)


def error_of(call):
    try:
        call()
    except ToolCallError as err:
        return err.code, err.detail
    return None


class ToolCallsTests(unittest.TestCase):

    @mark.req("REQ-TLS-001")
    def test_the_three_code_checks_are_offered_with_trust_code(self):
        """TC-TLS-001: the three code checks are offered with trust code.

        Example: number_check, quote_in_source, schema_check -> (status, trust) = ("fail", "code"), ("pass", "code"), ("pass", "code")
        """
        # Given: t = tools() and run = {"id": "r1", "limits": {}}
        t = tools()
        run = {"id": "r1", "limits": {}}
        # When: calling number_check, quote_in_source, and schema_check
        out1 = t.call(run, "number_check", {"claim": "The tower is 1,200 m high", "evidence": ["The tower is 1,020 m high"]})
        out2 = t.call(run, "quote_in_source", {"quote": "finished in 1889", "source_text": PAGE})
        out3 = t.call(run, "schema_check", {"value": {"verdict": "supported", "reason": "r"}, "schema": {"required": ["verdict", "reason"]}})
        # Then: assertEqual of (output["status"], trust) for each
        self.assertEqual((out1["output"]["status"], out1["trust"]), ("fail", "code"))
        self.assertEqual((out2["output"]["status"], out2["trust"]), ("pass", "code"))
        self.assertEqual((out3["output"]["status"], out3["trust"]), ("pass", "code"))
        self.assertTrue(all(name in TOOLS for name in ("number_check", "quote_in_source", "schema_check")))

    @mark.req("REQ-TLS-001")
    def test_a_quote_that_is_not_verbatim_fails(self):
        """TC-TLS-001: a quote that is not verbatim fails.

        Example: quote_in_source with {"quote": "finished in 1890", "source_text": PAGE} -> assertEqual(out["output"]["status"], "fail")
        """
        # Given: t = tools() and run = {"id": "r1", "limits": {}}
        t = tools()
        run = {"id": "r1", "limits": {}}
        # When: calling quote_in_source with a non-verbatim quote
        out = t.call(run, "quote_in_source", {"quote": "finished in 1890", "source_text": PAGE})
        # Then: assertEqual(out["output"]["status"], "fail")
        self.assertEqual(out["output"]["status"], "fail")

    @mark.req("REQ-TLS-001")
    def test_a_number_check_without_a_number_in_the_evidence_is_inconclusive(self):
        """TC-TLS-001: a number_check without a number in the evidence is inconclusive.

        Example: number_check {"claim": "It is 1,200 m", "evidence": ["no figures here"]} -> status "inconclusive"; number_check {"claim": "It is 1,200 m", "evidence": []} -> status "inconclusive"
        """
        # Given: t = tools() and run = {"id": "r1", "limits": {}}
        t = tools()
        run = {"id": "r1", "limits": {}}
        # When: calling number_check with no numbers in evidence
        out1 = t.call(run, "number_check", {"claim": "It is 1,200 m", "evidence": ["no figures here"]})
        out2 = t.call(run, "number_check", {"claim": "It is 1,200 m", "evidence": []})
        # Then: both should have status "inconclusive"
        self.assertEqual(out1["output"]["status"], "inconclusive")
        self.assertEqual(out2["output"]["status"], "inconclusive")

    @mark.req("REQ-TLS-001")
    def test_a_schema_check_names_the_missing_key(self):
        """TC-TLS-001: a schema_check names the missing key.

        Example: schema_check {"value": {"verdict": "supported"}, "schema": {"required": ["verdict", "reason"]}} -> assertEqual(out["output"]["status"], "fail"); assertEqual(len(out["output"]["problems"]), 1); assertIn("reason", out["output"]["problems"][0])
        """
        # Given: t = tools() and run = {"id": "r1", "limits": {}}
        t = tools()
        run = {"id": "r1", "limits": {}}
        # When: calling schema_check with a missing required key
        out = t.call(run, "schema_check", {"value": {"verdict": "supported"}, "schema": {"required": ["verdict", "reason"]}})
        # Then: status "fail", one problem, and the missing key named
        self.assertEqual(out["output"]["status"], "fail")
        self.assertEqual(len(out["output"]["problems"]), 1)
        self.assertIn("reason", out["output"]["problems"][0])

    @mark.req("REQ-TLS-008")
    def test_a_call_over_the_limit_is_refused_naming_the_tool(self):
        """TC-TLS-008: a call over the limit is refused naming the tool.

        Example: run = {"id": "r1", "limits": {"web_search": 1}}; one web_search {"query": "q"} succeeds; the second gives assertEqual(error_of(lambda: t.call(run, "web_search", {"query": "q"})), ("budget", "web_search")); then assertEqual(t.used("r1"), {"web_search": 1})
        """
        # Given: t = tools() and run = {"id": "r1", "limits": {"web_search": 1}}
        t = tools()
        run = {"id": "r1", "limits": {"web_search": 1}}
        # When: the first web_search succeeds
        t.call(run, "web_search", {"query": "q"})
        # Then: the second web_search is refused with a budget error
        self.assertEqual(error_of(lambda: t.call(run, "web_search", {"query": "q"}))[0], "budget")
        self.assertEqual(error_of(lambda: t.call(run, "web_search", {"query": "q"}))[1], "web_search")
        self.assertEqual(t.used("r1"), {"web_search": 1})

    @mark.req("REQ-TLS-008")
    def test_limits_are_per_run_and_per_tool(self):
        """TC-TLS-008: limits are per run and per tool.

        Example: After the limit of run r1 is used up as in 5, fetch_passages {"url": "https://example.org/a", "question": "height"} in run r1 works (assertTrue on its output["passages"]), and web_search in run {"id": "r2", "limits": {"web_search": 1}} works; assertEqual(t.used("r2"), {"web_search": 1})
        """
        # Given: t = tools() and two runs with separate budgets
        t = tools()
        run1 = {"id": "r1", "limits": {"web_search": 1}}
        run2 = {"id": "r2", "limits": {"web_search": 1}}
        # When: web_search is used on run1
        t.call(run1, "web_search", {"query": "q"})
        # Then: fetch_passages still works on run1, and web_search works on run2
        out1 = t.call(run1, "fetch_passages", {"url": "https://example.org/a", "question": "height"})
        self.assertTrue(out1["output"]["passages"])
        out2 = t.call(run2, "web_search", {"query": "q"})
        self.assertEqual(t.used("r2"), {"web_search": 1})

    @mark.req("REQ-TLS-008")
    def test_an_unknown_tool_is_refused_and_not_counted(self):
        """TC-TLS-008: an unknown tool is refused and not counted.

        Example: assertEqual(error_of(lambda: t.call(run, "nonsense", {}))[0], "unknown_tool") and assertEqual(t.used("r1"), {})
        """
        # Given: t = tools() and run = {"id": "r1", "limits": {}}
        t = tools()
        run = {"id": "r1", "limits": {}}
        # When: calling an unknown tool
        error = error_of(lambda: t.call(run, "nonsense", {}))
        # Then: error code is unknown_tool and budget is not decremented
        self.assertEqual(error[0], "unknown_tool")
        self.assertEqual(t.used("r1"), {})

    @mark.req("REQ-TLS-008")
    def test_a_failing_source_is_counted(self):
        """TC-TLS-008: a failing source is counted.

        Example: fetch_passages {"url": "https://example.org/missing", "question": "q"} -> error_of(...)[0] == "source_error"; then assertEqual(t.used("r1"), {"fetch_passages": 1})
        """
        # Given: t = tools() and run = {"id": "r1", "limits": {}}
        t = tools()
        run = {"id": "r1", "limits": {}}
        # When: a fetch_passages call fails with a source_error
        error = error_of(lambda: t.call(run, "fetch_passages", {"url": "https://example.org/missing", "question": "q"}))
        # Then: the call is still counted against the budget
        self.assertEqual(error[0], "source_error")
        self.assertEqual(t.used("r1"), {"fetch_passages": 1})

    @mark.req("REQ-TLS-008")
    def test_every_output_carries_its_trust_label(self):
        """TC-TLS-008: every output carries its trust label.

        Example: In run {"id": "r1", "limits": {}}: web_search, fetch_passages (url https://example.org/a), scholar_search {"query": "q"} each have trust "web"; run_script {"code": "print(1)", "inputs": {}} has trust "code" and output equal to {"status": "unavailable", "stdout": ""}
        """
        # Given: t = tools() and run = {"id": "r1", "limits": {}}
        t = tools()
        run = {"id": "r1", "limits": {}}
        # When: calling the four tools
        out1 = t.call(run, "web_search", {"query": "q"})
        out2 = t.call(run, "fetch_passages", {"url": "https://example.org/a", "question": "height"})
        out3 = t.call(run, "scholar_search", {"query": "q"})
        out4 = t.call(run, "run_script", {"code": "print(1)", "inputs": {}})
        # Then: each output has the correct trust label
        self.assertEqual(out1["trust"], "web")
        self.assertEqual(out2["trust"], "web")
        self.assertEqual(out3["trust"], "web")
        self.assertEqual(out4["trust"], "code")
        self.assertEqual(out4["output"], {"status": "unavailable", "stdout": ""})

    @mark.req("REQ-TLS-008")
    def test_fetched_passages_keep_their_source(self):
        """TC-TLS-008: fetched_passages keep their source.

        Example: fetch_passages {"url": "https://example.org/a", "question": "height"} -> output["ref"] == "https://example.org/a"; every passage has keys "id" and "quote"; assertTrue(all(p["quote"] in PAGE for p in output["passages"]))
        """
        # Given: t = tools() and run = {"id": "r1", "limits": {}}
        t = tools()
        run = {"id": "r1", "limits": {}}
        # When: calling fetch_passages
        out = t.call(run, "fetch_passages", {"url": "https://example.org/a", "question": "height"})
        # Then: ref matches the url, and each passage is a valid quote from the page
        self.assertEqual(out["output"]["ref"], "https://example.org/a")
        for passage in out["output"]["passages"]:
            self.assertIn("id", passage)
            self.assertIn("quote", passage)
            self.assertIn(passage["quote"], PAGE)


if __name__ == "__main__":
    unittest.main()
