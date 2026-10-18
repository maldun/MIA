"""
The web broker for sandboxed scripts (ui/REQUIREMENTS_CORE.md 11, 12.2): a sandbox has no network at all, not even a loopback to this machine, so a script cannot run curl or open a
socket. What it gets instead is a capability: a request line on its standard output, answered on its standard input by this process (sandbox.py reads the lines), for two questions:
GET a page and search. No socket, no mounted file, and so nothing for SELinux or the namespaces to get in the way of.
The answers come from MIA's own web tools (web_tools.py), so a script is held to exactly the rules of every other web access: public addresses only, checked at every redirect and
for the connected address, size and type limits, no cookies, no POST, untrusted text with the instruction signals reported, every request in the web log. On top come budgets per script
(calls and bytes). The script never sees an address, a header or a socket; this also means the DNS name is resolved and connected by the broker, not by the script.
"""
import json
import time

try:
    from . import web_tools
except ImportError:  # used as plain script / in tests
    import web_tools

DEFAULT_LIMITS = {"get": 5, "search": 3, "bytes": 400_000}


def web_handlers(search, client, max_chars=60000):
    """the two operations on top of MIA's web tools: search(query, count) -> dict (web_tools.Search.search) and client.get(url) (web_tools.WebClient.get)"""
    def get(url, mode="text"):
        page = client.get(url)
        if mode == "raw" or page["content_type"] not in ("text/html", "application/xhtml+xml", ""):
            title, text = "", page["text"].strip()
        else:
            extracted = web_tools.extract_text(page["text"])
            title, text = extracted["title"], extracted["text"]
        clipped = len(text) > max_chars or page["truncated"]
        text = text[:max_chars]
        return {"url": page["url"], "status": page["status"], "content_type": page["content_type"], "title": title, "text": text, "clipped": clipped,
                "signals": web_tools.injection_signals(text)}

    def do_search(query, count=8):
        found = search.search(query, count)
        return {"backend": found["backend"], "results": found["results"], "errors": found["errors"]}

    return {"get": get, "search": do_search}


class WebBroker:
    """usage: with WebBroker(handlers) as broker: sandbox.run(code, broker=broker). The sandbox calls handle() for every request line its script writes."""

    def __init__(self, handlers, limits=None):
        self.handlers = handlers
        self.limits = {**DEFAULT_LIMITS, **(limits or {})}
        self.calls = {"get": 0, "search": 0}
        self.bytes = 0
        self.log = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def handle(self, request):
        """the answer (a dict) to one request (a dict from the script); never raises"""
        try:
            return self._answer(request)
        except Exception as exc:                        # the broker must never die because of a script
            return {"error": "the broker failed: %s" % type(exc).__name__}

    def handle_line(self, raw):
        """the answer for a request line as the sandbox sent it (bytes)"""
        try:
            request = json.loads(raw.decode("utf-8"))
            if not isinstance(request, dict) or "op" not in request:
                raise ValueError
        except (ValueError, UnicodeDecodeError):
            return {"error": "unreadable request"}
        return self.handle(request)

    def _answer(self, request):
        operation = request.get("op")
        if operation not in self.handlers:
            return {"error": "unknown operation '%s'" % str(operation)[:30]}
        if self.calls[operation] >= self.limits.get(operation, 0):
            self.log.append({"op": operation, "refused": "budget"})
            return {"error": "budget: at most %d %s call(s) per script" % (self.limits.get(operation, 0), operation)}
        if self.bytes >= self.limits["bytes"]:
            return {"error": "budget: the script has received enough data (%d bytes)" % self.limits["bytes"]}
        self.calls[operation] += 1
        started = time.time()
        argument = request.get("url") if operation == "get" else request.get("query")
        try:
            if operation == "get":
                answer = self.handlers["get"](str(argument), "raw" if request.get("mode") == "raw" else "text")
            else:
                answer = self.handlers["search"](str(argument), max(1, min(int(request.get("count", 8)), 20)))
        except web_tools.WebError as exc:
            self.log.append({"op": operation, "arg": argument, "error": str(exc), "ms": int((time.time() - started) * 1000)})
            return {"error": "%s: %s" % (type(exc).__name__, exc)}
        except Exception as exc:
            self.log.append({"op": operation, "arg": argument, "error": type(exc).__name__})
            return {"error": "failed: %s" % type(exc).__name__}
        size = len(json.dumps(answer, ensure_ascii=False).encode("utf-8"))
        room = self.limits["bytes"] - self.bytes
        if size > room and isinstance(answer.get("text"), str):
            answer["text"] = answer["text"][:max(0, len(answer["text"]) - (size - room))]
            answer["clipped"] = True
        self.bytes += min(size, room)
        self.log.append({"op": operation, "arg": argument, "ms": int((time.time() - started) * 1000), "bytes": size})
        return answer
