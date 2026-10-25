"""IF-402 tool calls (Pipeline runner to Tools and sandbox): the contract suite runs against the mock (stage 1) and the real Tools and sandbox
(stage 2, skipped until N-2.4.2 is integrated). Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_402_tool_calls.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider, subject_for  # noqa: E402
from markers import mark                                    # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from errors import ServiceError                             # noqa: E402
from if_402_tool_calls import ToolCallsMock                 # noqa: E402

IF = "IF-402"


def make(**options):
    return lambda kind: ToolCallsMock(**options) if kind == "mock" else subject_for(IF, kind)


def code_of(call):
    try:
        call()
    except ServiceError as err:
        return err.code, err.detail
    raise AssertionError("no ServiceError raised")


@contract
class ToolCallsContract(unittest.TestCase):
    @mark.req("IF-402", "REQ-BE-046")
    @each_provider(IF)
    def test_the_number_check_compares_by_code(self, tools):
        """TC-IF-402-01 golden 1: 1,200 m against 1,020 m fails, 1,200 against 1,200 passes, no number in the evidence is inconclusive; all with trust code."""
        run = {"id": "r1", "limits": {}}
        fail = tools.call(run, "number_check", {"claim": "The tower is 1,200 m high", "evidence": ["The tower is 1,020 m high"]})
        self.assertEqual((fail["output"]["status"], fail["trust"]), ("fail", "code"))
        self.assertEqual(tools.call(run, "number_check", {"claim": "It is 1,200 m", "evidence": ["about 1,200 m"]})["output"]["status"], "pass")
        self.assertEqual(tools.call(run, "number_check", {"claim": "It is 1,200 m", "evidence": ["no figures here"]})["output"]["status"], "inconclusive")

    @mark.req("IF-402", "REQ-BE-067")
    @each_provider(IF)
    def test_a_quote_must_occur_verbatim_and_passages_keep_their_source(self, tools):
        """TC-IF-402-02 golden 3: a quote that is not verbatim fails; fetched passages carry the source reference and the web trust label."""
        run = {"id": "r1", "limits": {}}
        text = "The tower is 330 m high.  It was finished in 1889."
        self.assertEqual(tools.call(run, "quote_in_source", {"quote": "finished in 1889", "source_text": text})["output"]["status"], "pass")
        self.assertEqual(tools.call(run, "quote_in_source", {"quote": "finished in 1890", "source_text": text})["output"]["status"], "fail")
        out = tools.call(run, "fetch_passages", {"url": "https://example.org/a", "question": "height"})
        self.assertEqual((out["trust"], out["output"]["ref"]), ("web", "https://example.org/a"))
        self.assertTrue(out["output"]["passages"])
        self.assertTrue(all(p["quote"] in "The tower is 330 m high. It was finished in 1889." for p in out["output"]["passages"]))

    @mark.req("IF-402", "REQ-BE-070", "REQ-BE-064")
    @each_provider(IF)
    def test_budgets_per_tool_and_run(self, tools):
        """TC-IF-402-03 golden 2: with a limit of 1 the second web_search of the run is 'budget' naming the tool; another run and another tool are not affected."""
        run = {"id": "r1", "limits": {"web_search": 1}}
        tools.call(run, "web_search", {"query": "q"})
        self.assertEqual(code_of(lambda: tools.call(run, "web_search", {"query": "q"})), ("budget", "web_search"))
        self.assertTrue(tools.call(run, "fetch_passages", {"url": "https://example.org/a", "question": "q"}))
        self.assertTrue(tools.call({"id": "r2", "limits": {"web_search": 1}}, "web_search", {"query": "q"}))
        self.assertEqual(code_of(lambda: tools.call(run, "nonsense", {}))[0], "unknown_tool")

    @mark.req("IF-402", "REQ-BE-065")
    @each_provider(IF, make(sandbox=False))
    def test_no_sandbox_means_no_script(self, tools):
        """TC-IF-402-04 golden 2: without a sandbox run_script is 'unavailable' and nothing runs."""
        out = tools.call({"id": "r1", "limits": {}}, "run_script", {"code": "print(1)", "inputs": {}})
        self.assertEqual((out["output"]["status"], out["output"]["stdout"]), ("unavailable", ""))

    @mark.req("IF-402", "REQ-BE-064")
    @each_provider(IF)
    def test_every_output_carries_a_trust_label_and_a_schema_check_names_problems(self, tools):
        """TC-IF-402-05: checks are 'code', web and scholarly tools are 'web'; schema_check names the missing keys."""
        run = {"id": "r1", "limits": {}}
        self.assertEqual(tools.call(run, "web_search", {"query": "q"})["trust"], "web")
        self.assertEqual(tools.call(run, "scholar_search", {"query": "q"})["trust"], "web")
        check = tools.call(run, "schema_check", {"value": {"verdict": "supported"}, "schema": {"required": ["verdict", "reason"]}})
        self.assertEqual((check["trust"], check["output"]["status"], check["output"]["problems"]), ("code", "fail", ["reason"]))


if __name__ == "__main__":
    unittest.main()
