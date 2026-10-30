"""Mock of IF-404, web search and fetch (protected). Complexity 3: scripted pages and results, refusals, errors.
No real internet and no redirect chains."""
import hashlib
import re
from urllib.parse import urlparse

try:
    from .errors import ServiceError
except ImportError:
    from errors import ServiceError

PRIVATE = re.compile(r"^(localhost|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|169\.254\.|0\.0\.0\.0|\[?::1)")


class WebMock:
    def __init__(self, pages=None, results=None, search_down=False, max_bytes=2_000_000):
        self.pages = pages if pages is not None else {
            "https://example.org/tower": {"text": "The tower is 330 m high.", "type": "text/html", "status": 200},
            "https://example.org/missing": {"text": "", "type": "text/html", "status": 404},
            "https://example.org/photo": {"text": "", "type": "image/png", "status": 200},
        }
        self.results = results if results is not None else [{"url": "https://example.org/tower", "title": "Tower", "content": "The tower is 330 m high.", "backend": "searxng"}]
        self.search_down, self.max_bytes = search_down, max_bytes
        self.log = []

    def search(self, query):
        if self.search_down:
            raise ServiceError("search_error")
        self.log.append(("search", query))
        return [dict(r) for r in self.results]

    def fetch(self, url):
        parts = urlparse(url)
        port = parts.port or (443 if parts.scheme == "https" else 80)
        if parts.scheme not in ("http", "https") or port not in (80, 443, 8080, 8443) or PRIVATE.match(parts.hostname or ""):
            raise ServiceError("unsafe_url")
        self.log.append(("fetch", url))
        page = self.pages.get(url) or {"text": "", "type": "text/html", "status": 404}
        if page["status"] >= 400:
            raise ServiceError("http_status", detail=page["status"])
        if not page["type"].startswith("text/"):
            raise ServiceError("unsupported_content")
        data = page["text"].encode("utf-8")
        truncated = len(data) > self.max_bytes
        data = data[: self.max_bytes]
        return {"text": data.decode("utf-8", "ignore"), "hash": hashlib.sha256(data).hexdigest(), "bytes": len(data), "truncated": truncated}
