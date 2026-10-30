"""
TC-TLS-002 (REQ-TLS-002): the lookup tools of the door (tool_calls.py) on the real web tools: findings with title, address and short text, the passages
of a page that answer the question first, verbatim and with their source; an answer that quotes a passage keeps its source, one that does not is unknown
(research.anchor_answer, the rule of the lookup). The HTTP session and the name resolver are fakes.
Run with: python tests/test_tool_calls_lookup.py
"""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                   # noqa: E402
from research import anchor_answer                         # noqa: E402
from tool_calls import ToolCalls                           # noqa: E402
from web_tools import build_web_tools                      # noqa: E402

SEARXNG = "http://localhost:8590/search"
PAGE = "https://example.org/tower"
RUN = {"id": "r1", "limits": {}}
HEIGHT = "The tower is 330 m high including its antennas."
TEXT = "The tower was built for a world fair. " * 45 + HEIGHT + " " + "Millions of visitors climb the stairs every year. " * 15


class FakeResponse:
    def __init__(self, status=200, body="", headers=None, json_data=None):
        self.status_code, self._body = status, body.encode("utf-8")
        self.headers = headers if headers is not None else {"Content-Type": "text/plain; charset=utf-8"}
        self.encoding, self._json, self.text, self.raw = "utf-8", json_data, body, None

    def iter_content(self, chunk_size=1):
        for i in range(0, len(self._body), chunk_size):
            yield self._body[i:i + chunk_size]

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json

    def close(self):
        pass


class FakeSession:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, **kwargs):
        self.calls.append(("get", url, kwargs))
        return self.routes[url]


def door():
    found = {"results": [{"url": PAGE, "title": "The tower", "content": "x" * 1000, "engine": "x"}]}
    session = FakeSession({SEARXNG: FakeResponse(json_data=found), PAGE: FakeResponse(body=TEXT)})
    tools, _, _ = build_web_tools({"search_backends": ["searxng"]}, tempfile.mkdtemp(), session=session, resolver=lambda host: ["93.184.216.34"])
    return ToolCalls(web_search=tools["web_search"][0], fetch_page=tools["fetch_page"][0])


def as_lookup_passages(output):
    """the passages of the door as the lookup numbers them for the model: n from 1, the text and the address of the page"""
    return [{"n": i + 1, "url": output["ref"], "text": p["quote"]} for i, p in enumerate(output["passages"])]


class LookupToolTests(unittest.TestCase):

    @mark.req("REQ-TLS-002")
    def test_findings_have_title_address_and_short_text(self):
        """TC-TLS-002: findings have title, address, and short text.

        Example: web_search -> finding with url, title, and content.
        """
        # Given: a door with a fake session
        out = door().call(RUN, "web_search", {"query": "height of the tower"})
        # When: extracting the first finding
        finding = out["output"][0]
        # Then: verify the expected fields
        self.assertEqual((finding["url"], finding["title"], out["trust"]), (PAGE, "The tower", "web"))
        self.assertTrue(0 < len(finding["content"]) <= 400)

    @mark.req("REQ-TLS-002")
    def test_the_passage_that_answers_the_question_comes_first(self):
        """TC-TLS-002: the passage that answers the question comes first.

        Example: fetch_passages -> first passage contains the height.
        """
        # Given: a door with a fake session
        out = door().call(RUN, "fetch_passages", {"url": PAGE, "question": "How high is the tower?"})["output"]
        # When: checking the passage list
        self.assertTrue(1 <= len(out["passages"]) <= 2)
        # Then: the first passage contains the height
        self.assertIn(HEIGHT, out["passages"][0]["quote"])

    @mark.req("REQ-TLS-002")
    def test_passages_are_verbatim_and_keep_their_source(self):
        """TC-TLS-002: passages are verbatim and keep their source.

        Example: two consecutive fetch_passages calls return the same passage IDs.
        """
        # Given: a door with a fake session
        tools = door()
        # When: calling fetch_passages twice
        first = tools.call(RUN, "fetch_passages", {"url": PAGE, "question": "How high is the tower?"})["output"]
        again = tools.call(RUN, "fetch_passages", {"url": PAGE, "question": "How high is the tower?"})["output"]
        # Then: the ref, verbatim quotes, and passage ids match
        self.assertEqual(first["ref"], PAGE)
        self.assertTrue(all(p["quote"] in TEXT for p in first["passages"]))
        self.assertEqual([p["id"] for p in first["passages"]], [p["id"] for p in again["passages"]])

    @mark.req("REQ-TLS-002")
    def test_an_answer_that_quotes_a_passage_keeps_its_source(self):
        """TC-TLS-002: an answer that quotes a passage keeps its source.

        Example: anchor_answer with a verbatim quote returns the source.
        """
        # Given: a door with a fake session
        out = door().call(RUN, "fetch_passages", {"url": PAGE, "question": "How high is the tower?"})["output"]
        answer = {"status": "answered", "answer": "The tower is 330 m high.", "sources": [{"n": 1, "quote": HEIGHT}]}
        # When: anchoring the answer
        result = anchor_answer(answer, as_lookup_passages(out))
        # Then: the status and sources match
        self.assertEqual((result["status"], result["sources"]), ("answered", [{"url": PAGE, "quote": HEIGHT}]))

    @mark.req("REQ-TLS-002")
    def test_an_answer_without_a_verbatim_quote_is_unknown(self):
        """TC-TLS-002: an answer without a verbatim quote is unknown.

        Example: anchor_answer with a non-matching quote returns unknown.
        """
        # Given: a door with a fake session
        out = door().call(RUN, "fetch_passages", {"url": PAGE, "question": "How high is the tower?"})["output"]
        answer = {"status": "answered", "answer": "The tower is 330 m high.", "sources": [{"n": 1, "quote": "The tower measures 330 metres."}]}
        # When: anchoring the answer
        result = anchor_answer(answer, as_lookup_passages(out))
        # Then: the status is unknown and demoted is true
        self.assertEqual((result["status"], result["sources"], result["demoted"]), ("unknown", [], True))


if __name__ == "__main__":
    unittest.main()
