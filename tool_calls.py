"""
The one door to the tools (IF-402, part VerificationSuite of node N-2.4.2): everything a workflow step may do besides a model call.

  call(run, tool, args)   {"output", "trust"}; run = {"id", "limits": {tool: max calls}}
  used(run_id)            {tool: calls counted for the run}

The code checks come from checks.py and are offered to every workflow (REQ-TLS-001). Every call is counted against the limits of its run, and
every output carries its trust: `code` (computed by code), `web` (text from the web or a paper, untrusted data) or `model` (REQ-TLS-008).
The web, the scholarly sources, the trust table and the sandbox are handed in (web_tools.build_web_tools, scholar.build_scholar,
source_trust.TrustTable.for_url, sandbox.create_router), so the door itself touches no network. Without an isolating sandbox a script is refused before
anything runs, never run unprotected (REQ-TLS-005).
"""
import hashlib

try:
    from . import checks
    from .schema_check import check as check_schema
    from .web_tools import chunk_text
    from .evidence import passage_id
    from .sandbox import Operation
except ImportError:  # used as plain script / in tests
    import checks
    from schema_check import check as check_schema
    from web_tools import chunk_text
    from evidence import passage_id
    from sandbox import Operation

TRUST = {"number_check": "code", "quote_in_source": "code", "schema_check": "code", "run_script": "code",
         "web_search": "web", "fetch_passages": "web", "scholar_search": "web", "source_record": "web"}
TOOLS = tuple(TRUST)
EXTERNAL = ("web_search", "fetch_passages", "scholar_search", "source_record")


class ToolCallError(Exception):
    """IF-402 errors. code: unknown_tool | budget (detail: the tool) | source_error (detail: what the source said)."""

    def __init__(self, code, detail=None):
        super().__init__("%s%s" % (code, ": %s" % detail if detail is not None else ""))
        self.code, self.detail = code, detail


class ToolCalls:
    def __init__(self, web_search=None, fetch_page=None, scholar=None, trust=None, sandbox=None):
        self.web_search, self.fetch_page, self.scholar, self.trust = web_search, fetch_page, scholar, trust
        self.sandbox = sandbox
        self.script_check = checks.make_script_check(sandbox) if sandbox is not None else None
        self._used = {}

    def used(self, run_id):
        return dict(self._used.get(run_id, {}))

    def call(self, run, tool, args):
        if tool not in TRUST:
            raise ToolCallError("unknown_tool", tool)
        used = self._used.setdefault(run["id"], {})
        limit = (run.get("limits") or {}).get(tool)
        if limit is not None and used.get(tool, 0) >= limit:
            raise ToolCallError("budget", tool)
        # counted before it runs: a source that fails has still been asked (IF-402 errors)
        used[tool] = used.get(tool, 0) + 1
        try:
            output = getattr(self, "_" + tool)(**args)
        except ToolCallError:
            raise
        except Exception as exc:
            if tool not in EXTERNAL:
                raise
            raise ToolCallError("source_error", "%s: %s" % (type(exc).__name__, exc)) from exc
        return {"output": output, "trust": TRUST[tool]}

    # --- code checks (REQ-TLS-001) ---

    def _number_check(self, claim, evidence):
        found = checks.number_check(claim, "\n".join(evidence))
        # IF-402 knows three statuses: nothing to compare is not a verdict either way
        status = found["status"] if found["status"] in ("pass", "fail") else "inconclusive"
        return {"status": status, "detail": found["detail"]}

    def _quote_in_source(self, quote, source_text):
        # a near match is inconclusive in checks.py; for a quotation only the verbatim text counts
        return {"status": "pass" if checks.quote_in_source(quote, source_text)["status"] == "pass" else "fail"}

    def _schema_check(self, value, schema):
        problems = check_schema(value, schema)
        return {"status": "fail" if problems else "pass", "problems": problems}

    def _run_script(self, code, inputs):
        # asked before the check, with the operation the check will run: a removed sandbox must not reach any backend (REQ-TLS-005)
        if self.script_check is None or not self.sandbox.available_for(Operation("compute", "model")):
            return {"status": "unavailable", "stdout": ""}
        found = self.script_check(code, data=inputs)
        stdout = found["evidence"][0].get("stdout", "") if found["evidence"] else ""
        return {"status": "ok", "stdout": stdout, "result": found}

    # --- web and scholarly sources (untrusted data) ---

    def _web_search(self, query):
        found = self._need(self.web_search, "web search")(query)
        return [{"url": r["url"], "title": r.get("title", ""), "content": r.get("snippet", "")} for r in found["results"]]

    def _fetch_passages(self, url, question):
        page = self._need(self.fetch_page, "page fetch")(url)
        text = page["text"]
        passages = [{"id": passage_id(url, piece), "quote": piece} for piece in chunk_text(text)]
        return {"ref": url, "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], "passages": passages}

    def _scholar_search(self, query, until=None, since=None):
        found = self._need(self.scholar, "scholarly search").search(query, until=until, since=since)
        return {"works": found["works"], "errors": found["errors"], "dropped": found["dropped"]}

    def _source_record(self, ref):
        entry = self._need(self.trust, "trust table")(ref)
        return {"ref": ref, "class": entry["class"], "trust": entry["score"], "retraction": None}

    @staticmethod
    def _need(source, name):
        if source is None:
            raise ToolCallError("source_error", "no %s is configured" % name)
        return source
