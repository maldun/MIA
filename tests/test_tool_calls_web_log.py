"""
TC-TLS-007 (REQ-TLS-007): only the query leaves the host, and the web log lists every request that left. The door (tool_calls.py) is wired to the real
web tools of web_tools.build_web_tools; the HTTP session and the name resolver are fakes, so nothing leaves this machine.
Run with: python tests/test_tool_calls_web_log.py
"""

import glob
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                   # noqa: E402
from tool_calls import ToolCalls, ToolCallError            # noqa: E402
from web_tools import build_web_tools                      # noqa: E402

SEARXNG = "http://localhost:8590/search"
DDG = "https://html.duckduckgo.com/html/"
PAGE = "https://example.org/a"
OLD = "https://example.org/old"
QUERY = "height of the tower"
RUN = {"id": "r1", "limits": {}}
with open(os.path.join(HERE, "fixtures", "ddg_results.html"), encoding="utf-8") as _fp:
    DDG_HTML = _fp.read()


class FakeResponse:
    def __init__(self, status=200, body="", headers=None, json_data=None):
        self.status_code, self._body = status, body.encode("utf-8")
        self.headers = headers if headers is not None else {"Content-Type": "text/html; charset=utf-8"}
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
    """answers from `routes` (url -> FakeResponse) and records every request that would have left the host"""

    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, **kwargs):
        self.calls.append(("get", url, kwargs))
        return self.routes[url]

    def post(self, url, **kwargs):
        self.calls.append(("post", url, kwargs))
        return self.routes[url]


def searxng_answer():
    return FakeResponse(json_data={"results": [{"url": PAGE, "title": "A", "content": "The tower is 330 m high.", "engine": "x"}]})


def routes(**extra):
    found = {SEARXNG: searxng_answer(), PAGE: FakeResponse(body="<p>The tower is 330 m high.</p>")}
    found.update(extra)
    return found


class WebLogTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def door(self, session, backends=("searxng",)):
        tools, _, _ = build_web_tools({"search_backends": list(backends)}, self.folder, session=session, resolver=lambda host: ["93.184.216.34"])
        return ToolCalls(web_search=tools["web_search"][0], fetch_page=tools["fetch_page"][0])

    def log(self):
        lines = []
        for path in sorted(glob.glob(os.path.join(self.folder, "web-*.jsonl"))):
            with open(path, encoding="utf-8") as fp:
                lines += [json.loads(line) for line in fp if line.strip()]
        return lines


    @mark.req("REQ-TLS-007")
    def test_a_search_sends_only_the_query(self):
        """TC-TLS-007: a search sends only the query.

        Example: web_search {"query": "height of the tower"} -> only the query is sent in the request params.
        """
        # Given: a fake session with the default routes
        session = FakeSession(routes())
        # When: calling web_search with the query
        self.door(session).call(RUN, "web_search", {"query": QUERY})
        # Then: assert that only the GET request to SEARXNG was made, with the correct parameters and headers
        self.assertEqual([(m, u) for m, u, _ in session.calls], [("get", SEARXNG)])
        self.assertEqual(session.calls[0][2]["params"], {"q": QUERY, "format": "json", "safesearch": 1})
        self.assertEqual(set(session.calls[0][2]["headers"]), {"User-Agent"})


    @mark.req("REQ-TLS-007")
    def test_a_search_is_in_the_web_log(self):
        """TC-TLS-007: a search is in the web log.

        Example: web_search {"query": "height of the tower"} -> a search record with the query and backend in the log.
        """
        # Given: a fake session with the default routes
        session = FakeSession(routes())
        # When: calling web_search with the query
        self.door(session).call(RUN, "web_search", {"query": QUERY})
        # Then: assert that the search is in the web log
        self.assertEqual([(r["kind"], r["query"], r["backend"]) for r in self.log()], [("search", QUERY, "searxng")])


    @mark.req("REQ-TLS-007")
    def test_a_fetch_is_in_the_web_log(self):
        """TC-TLS-007: a fetch is in the web log.

        Example: fetch_passages {"url": "https://example.org/a", "question": "height"} -> a fetch record with the url in the log.
        """
        # Given: a fake session with the default routes
        session = FakeSession(routes())
        # When: calling fetch_passages with the page and question
        self.door(session).call(RUN, "fetch_passages", {"url": PAGE, "question": "height"})
        # Then: assert that the fetch is in the web log
        self.assertEqual([u for _, u, _ in session.calls], [PAGE])
        self.assertEqual([(r["kind"], r["url"]) for r in self.log()], [("fetch", PAGE)])


    @mark.req("REQ-TLS-007")
    def test_every_address_of_a_redirect_is_in_the_web_log(self):
        """TC-TLS-007: every address of a redirect is in the web log.

        Example: fetch_passages with a redirect from OLD to PAGE -> both URLs in the web log.
        """
        # Given: a fake session with a redirect from OLD to PAGE
        session = FakeSession(routes(**{OLD: FakeResponse(status=301, headers={"Location": PAGE})}))
        # When: calling fetch_passages with the old url
        self.door(session).call(RUN, "fetch_passages", {"url": OLD, "question": "height"})
        # Then: both the old and new urls are in the web log
        self.assertEqual([u for _, u, _ in session.calls], [OLD, PAGE])
        logged = json.dumps(self.log())
        self.assertIn(OLD, logged)
        self.assertIn(PAGE, logged)


    @mark.req("REQ-TLS-007")
    def test_a_refused_address_sends_nothing_but_is_logged(self):
        """TC-TLS-007: a refused address sends nothing but is logged.

        Example: fetch_passages with a non-existent url -> ToolCallError with code source_error, no network call, but still logged as a fetch with an error.
        """
        # Given: a fake session with the default routes
        session = FakeSession(routes())
        # When: calling fetch_passages with a non-existent url
        with self.assertRaises(ToolCallError) as caught:
            self.door(session).call(RUN, "fetch_passages", {"url": "http://192.168.1.10/admin", "question": "q"})
        # Then: the error code is source_error, no network call was made, but the fetch is still logged with an error flag
        self.assertEqual(caught.exception.code, "source_error")
        self.assertEqual(session.calls, [])
        self.assertEqual([(r["kind"], "error" in r) for r in self.log()], [("fetch", True)])


    @mark.req("REQ-TLS-007")
    def test_a_failing_backend_and_its_fallback_are_both_logged(self):
        """TC-TLS-007: a failing backend and its fallback are both logged.

        Example: web_search with a failing searxng backend and a working duckduckgo fallback -> both search entries in the web log.
        """
        # Given: a fake session with a failing searxng and a working duckduckgo
        session = FakeSession(routes(**{SEARXNG: FakeResponse(status=500), DDG: FakeResponse(body=DDG_HTML)}))
        # When: calling web_search with both backends
        self.door(session, backends=("searxng", "duckduckgo")).call(RUN, "web_search", {"query": QUERY})
        # Then: both the failed searxng and the successful duckduckgo searches are in the web log
        self.assertEqual([(m, u) for m, u, _ in session.calls], [("get", SEARXNG), ("post", DDG)])
        self.assertEqual(session.calls[1][2]["data"], {"q": QUERY})
        self.assertEqual([(r["kind"], r["backend"]) for r in self.log()], [("search", "searxng"), ("search", "duckduckgo")])




if __name__ == "__main__":
    unittest.main()
