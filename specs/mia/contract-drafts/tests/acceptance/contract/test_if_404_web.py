"""IF-404 web search and fetch (external; owned by the Tools and sandbox): the contract suite runs against the mock (stage 1) and the real web client
with SearXNG (stage 2, skipped until the stage-2 run supplies a scripted server). Protected after the Plan gate.
Run with: python tests/acceptance/contract/test_if_404_web.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider, subject_for  # noqa: E402
from markers import mark                                    # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from errors import ServiceError                             # noqa: E402
from if_404_web import WebMock                              # noqa: E402

IF = "IF-404"


def make(**options):
    return lambda kind: WebMock(**options) if kind == "mock" else subject_for(IF, kind)


def code_of(call):
    try:
        call()
    except ServiceError as err:
        return err.code, err.detail
    raise AssertionError("no ServiceError raised")


@contract
class WebContract(unittest.TestCase):
    @mark.req("IF-404", "REQ-BE-068")
    @each_provider(IF)
    def test_search_and_fetch(self, web):
        """TC-IF-404-01 golden 1: search returns findings with url, title and content; fetch returns text, a hash and the size."""
        hits = web.search("height of the tower")
        self.assertTrue(hits and {"url", "title", "content"} <= set(hits[0]))
        page = web.fetch(hits[0]["url"])
        self.assertEqual((page["text"], page["truncated"]), ("The tower is 330 m high.", False))
        self.assertEqual((len(page["hash"]), page["bytes"]), (64, len("The tower is 330 m high.")))

    @mark.req("IF-404", "REQ-BE-064")
    @each_provider(IF)
    def test_unsafe_addresses_are_refused_before_any_request(self, web):
        """TC-IF-404-02 golden 2 and 3: a private address, localhost, port 22 and a file scheme are unsafe_url and nothing is fetched."""
        for url in ("http://192.168.1.10/admin", "http://localhost/x", "https://example.org:22/x", "file:///etc/passwd", "http://10.0.0.5/"):
            self.assertEqual(code_of(lambda: web.fetch(url)), ("unsafe_url", None), url)
        self.assertEqual(web.log, [])

    @mark.req("IF-404")
    @each_provider(IF)
    def test_http_errors_and_unsupported_content(self, web):
        """TC-IF-404-03 golden 2: a 404 is http_status with 404; an image is unsupported_content."""
        self.assertEqual(code_of(lambda: web.fetch("https://example.org/missing")), ("http_status", 404))
        self.assertEqual(code_of(lambda: web.fetch("https://example.org/photo")), ("unsupported_content", None))

    @mark.req("IF-404", "REQ-BE-068")
    @each_provider(IF, make(search_down=True))
    def test_a_failing_search_service(self, web):
        """TC-IF-404-04 golden 2: a search service that fails is search_error, with no partial list."""
        self.assertEqual(code_of(lambda: web.search("q")), ("search_error", None))

    @mark.req("IF-404")
    @each_provider(IF, make(max_bytes=10, pages={"https://example.org/big": {"text": "x" * 50, "type": "text/plain", "status": 200}}))
    def test_a_large_page_is_truncated(self, web):
        """TC-IF-404-05 golden 3: a page over the limit comes back truncated with exactly the limit in bytes."""
        page = web.fetch("https://example.org/big")
        self.assertEqual((page["truncated"], page["bytes"], len(page["text"])), (True, 10, 10))


if __name__ == "__main__":
    unittest.main()
