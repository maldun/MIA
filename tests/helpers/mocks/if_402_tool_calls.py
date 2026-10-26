"""Mock of IF-402, the tool calls of the Tools and sandbox (protected). Complexity 3: counted calls against budgets, trust labels, scripted tools.
No real network and no real sandbox: pages, search results and works are scripted; the sandbox is a flag."""
import re

try:
    from .errors import ServiceError
except ImportError:
    from errors import ServiceError

TOOLS = ("number_check", "quote_in_source", "schema_check", "run_script", "web_search", "fetch_passages", "scholar_search", "source_record")
TRUST = {"number_check": "code", "quote_in_source": "code", "schema_check": "code", "run_script": "code",
         "web_search": "web", "fetch_passages": "web", "scholar_search": "web", "source_record": "web"}
NUMBER = re.compile(r"\d[\d,]*\.?\d*")


def _numbers(text):
    return [float(n.replace(",", "")) for n in NUMBER.findall(text) if n.replace(",", "").replace(".", "", 1).isdigit()]


class ToolCallsMock:
    def __init__(self, sandbox=True, results=None, pages=None, works=None, records=None):
        self.sandbox = sandbox
        self.results = results if results is not None else [{"url": "https://example.org/a", "title": "A", "content": "The tower is 330 m high."}]
        self.pages = pages if pages is not None else {"https://example.org/a": "The tower is 330 m high. It was finished in 1889."}
        self.works = works if works is not None else [{"doi": "10.1/x", "title": "On towers", "date": "2001"}]
        self.records = records if records is not None else {"https://example.org/a": {"ref": "https://example.org/a", "class": "web", "trust": 0.5, "retraction": None}}
        self._used = {}

    def call(self, run, tool, args):
        if tool not in TOOLS:
            raise ServiceError("unknown_tool")
        used = self._used.setdefault(run["id"], {})
        limit = run.get("limits", {}).get(tool)
        if limit is not None and used.get(tool, 0) >= limit:
            raise ServiceError("budget", detail=tool)
        used[tool] = used.get(tool, 0) + 1
        return {"output": getattr(self, "_" + tool)(**args), "trust": TRUST[tool]}

    def _number_check(self, claim, evidence):
        wanted = _numbers(claim)
        have = [n for line in evidence for n in _numbers(line)]
        if not wanted or not have:
            return {"status": "inconclusive", "detail": "no number to compare"}
        agree = any(abs(w - h) <= 0.005 * max(abs(w), abs(h)) for w in wanted for h in have)
        return {"status": "pass" if agree else "fail", "detail": "claim %s, evidence %s" % (wanted, have)}

    def _quote_in_source(self, quote, source_text):
        norm = lambda t: re.sub(r"\s+", " ", t).strip()
        return {"status": "pass" if norm(quote) and norm(quote) in norm(source_text) else "fail"}

    def _schema_check(self, value, schema):
        problems = [k for k in schema.get("required", []) if not isinstance(value, dict) or k not in value]
        return {"status": "fail" if problems else "pass", "problems": problems}

    def _run_script(self, code, inputs):
        if not self.sandbox:
            return {"status": "unavailable", "stdout": ""}
        return {"status": "ok", "stdout": "ran %d characters" % len(code)}

    def _web_search(self, query):
        return list(self.results)

    def _fetch_passages(self, url, question):
        if url not in self.pages:
            raise ServiceError("source_error", detail="not found")
        sentences = [s.strip() + "." for s in self.pages[url].split(".") if s.strip()]
        return {"ref": url, "hash": "h%d" % len(self.pages[url]), "passages": [{"id": "p%d" % i, "quote": s} for i, s in enumerate(sentences)]}

    def _scholar_search(self, query, until=None, since=None):
        return {"works": list(self.works), "errors": [], "dropped": []}

    def _source_record(self, ref):
        if ref not in self.records:
            raise ServiceError("source_error", detail="unknown source")
        return dict(self.records[ref])
