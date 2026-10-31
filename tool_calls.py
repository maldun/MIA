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
import inspect
import threading

try:
    from . import checks
    from .schema_check import check as check_schema
    from .research import collect_passages
    from .evidence import passage_id
    from .sandbox import Operation
    from .scholar import RETRACTED, WITHDRAWN, clean_doi, reference_of, retraction_state
except ImportError:  # used as plain script / in tests
    import checks
    from schema_check import check as check_schema
    from research import collect_passages
    from evidence import passage_id
    from sandbox import Operation
    from scholar import RETRACTED, WITHDRAWN, clean_doi, reference_of, retraction_state

TRUST = {"number_check": "code", "quote_in_source": "code", "schema_check": "code", "run_script": "code",
         "web_search": "web", "fetch_page": "web", "fetch_passages": "web", "scholar_search": "web", "source_record": "web"}
TOOLS = tuple(TRUST)
EXTERNAL = ("web_search", "fetch_page", "fetch_passages", "scholar_search", "source_record")


def build_tool_calls(web_tools, scholar, trust_table, sandbox):
    """the door as the app builds it: web_tools of web_tools.build_web_tools, scholar of scholar.build_scholar, trust_table of source_trust.build_trust,
    sandbox of sandbox.create_router. Every source is handed in, so the trust of works, the retraction check and the DOI lookup work in the app, not only
    in tests (REQ-TLS-003, Verify finding F2 of N-2.4.2)"""
    return ToolCalls(web_search=web_tools["web_search"][0], fetch_page=web_tools["fetch_page"][0], scholar=scholar, trust=trust_table.for_url,
                     sandbox=sandbox, work_trust=trust_table.for_work, retractions=scholar.verify_retraction,
                     work_lookup=scholar.crossref.lookup if scholar.crossref is not None else None)


class ToolCallError(Exception):
    """IF-402 errors. code: unknown_tool | budget (detail: the tool) | source_error (detail: what the source said) | bad_arguments (detail: why; nothing counted)."""

    def __init__(self, code, detail=None):
        super().__init__("%s%s" % (code, ": %s" % detail if detail is not None else ""))
        self.code, self.detail = code, detail


class ToolCalls:
    def __init__(self, web_search=None, fetch_page=None, scholar=None, trust=None, sandbox=None, work_trust=None, retractions=None, work_lookup=None):
        """work_trust(work, as_of): the trust entry of a work (source_trust.TrustTable.for_work); retractions(work, errors): asks for the notices of a work
        and merges them into it (scholar.Scholar.verify_retraction); without it only what the sources reported themselves counts; work_lookup(doi): the full
        record of one DOI or None (scholar.CrossrefClient.lookup)"""
        self.web_search, self.fetch_page, self.scholar, self.trust = web_search, fetch_page, scholar, trust
        self.work_trust, self.retractions, self.work_lookup = work_trust, retractions, work_lookup
        self.sandbox = sandbox
        self.script_check = checks.make_script_check(sandbox) if sandbox is not None else None
        self._used = {}
        self._lock = threading.Lock()        # the runner maps with threads: the check of the limit and the count are one step

    def used(self, run_id):
        return dict(self._used.get(run_id, {}))

    def call(self, run, tool, args):
        if tool not in TRUST:
            raise ToolCallError("unknown_tool", tool)
        method = getattr(self, "_" + tool)
        try:
            inspect.signature(method).bind(**args)
        except TypeError as exc:
            raise ToolCallError("bad_arguments", str(exc)) from exc
        with self._lock:
            used = self._used.setdefault(run["id"], {})
            limit = (run.get("limits") or {}).get(tool)
            if limit is not None and used.get(tool, 0) >= limit:
                raise ToolCallError("budget", tool)
            # counted before it runs: a source that fails has still been asked (IF-402 errors)
            used[tool] = used.get(tool, 0) + 1
        try:
            output = method(**args)
        except ToolCallError:
            raise
        except Exception as exc:
            if tool not in EXTERNAL:
                raise
            raise ToolCallError("source_error", "%s: %s" % (type(exc).__name__, exc)) from exc
        return {"output": output, "trust": TRUST[tool]}

    # --- code checks (REQ-TLS-001) ---

    def _number_check(self, claim, evidence):
        # one string is one passage: joined as a list it would be cut into single characters (N-1 of the N-2.4.2 re-verification)
        found = checks.number_check(claim, evidence if isinstance(evidence, str) else "\n".join(evidence))
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
        ran = found["evidence"][0].get("run_status") if found["evidence"] else None
        # ok only for a script that ran to its end; a sandbox that went away after the question above is unavailable (finding 6, D-132)
        status = {"ok": "ok", "unavailable": "unavailable"}.get(ran, "failed")
        return {"status": status, "stdout": stdout, "result": found}

    # --- web and scholarly sources (untrusted data) ---

    def _web_search(self, query):
        found = self._need(self.web_search, "web search")(query)
        return [{"url": r["url"], "title": r.get("title", ""), "content": r.get("snippet", "")} for r in found["results"]]

    def _fetch_page(self, url, max_chars=None):
        """the whole page as the fetcher gives it (title, text, clipped, the phrases that look like instructions): the page of the research pipelines (A-34)"""
        fetch = self._need(self.fetch_page, "page fetch")
        return fetch(url) if max_chars is None else fetch(url, max_chars=max_chars)

    def _fetch_passages(self, url, question):
        """the passages of the page that share most words with the question, best first (REQ-TLS-002): the selection of the lookup
        (research.collect_passages), so a workflow sees the same passages the lookup would quote from"""
        page = self._need(self.fetch_page, "page fetch")(url)
        text = page["text"]
        chosen = collect_passages(question, [dict(page, url=url, ref=url)])["passages"]
        passages = [{"id": passage_id(url, p["text"]), "quote": p["text"]} for p in chosen]
        return {"ref": url, "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], "passages": passages}

    def _scholar_search(self, query, until=None, since=None):
        """IF-405 records (REQ-TLS-003): origin (`sources`), trust class, the retraction state as of the cut-off; a work retracted or withdrawn by then
        is dropped and listed like a work after the cut-off"""
        found = self._need(self.scholar, "scholarly search").search(query, until=until, since=since)
        errors = dict(found["errors"])
        dropped = [{"ref": d["ref"], "title": d.get("title", ""), "reason": d.get("code") or d["reason"], "detail": d["reason"]} for d in found["dropped"]]
        works = []
        for work in found["works"]:
            if self.retractions is not None:
                self.retractions(work, errors)
            # notices after the cut-off do not count: a run as of a past day must not know them (scholar.use_as_of)
            state = retraction_state(work, as_of=until)
            if state["status"] in (RETRACTED, WITHDRAWN):
                dropped.append({"ref": reference_of(work), "title": work.get("title", ""), "reason": state["status"],
                                "detail": "; ".join(n.get("doi") or n["type"] for n in state["notices"])})
                continue
            works.append(dict(work, retraction=state, trust=self.work_trust(work, until) if self.work_trust is not None else None))
        return {"works": works, "errors": [{"source": s, "message": m} for s, m in errors.items()], "dropped": dropped}

    def _source_record(self, ref):
        """a web page by its address (trust by domain, no retraction), a work by its DOI ("doi:10.…" or "10.…"; REQ-TLS-003: trust class and retraction state)"""
        doi = clean_doi(ref[4:] if ref.lower().startswith("doi:") else ref) if ref.lower().startswith(("doi:", "10.")) else None
        if doi is None:
            entry = self._need(self.trust, "trust table")(ref)
            return {"ref": ref, "class": entry["class"], "trust": entry["score"], "retraction": None}
        work = self._need(self.work_lookup, "work lookup")(doi)
        if work is None:
            raise ToolCallError("source_error", "no record of %s" % doi)
        entry = self._need(self.work_trust, "trust table for works")(work, None)
        return {"ref": "doi:" + doi, "class": entry["class"], "trust": entry["score"], "retraction": retraction_state(work)}

    @staticmethod
    def _need(source, name):
        if source is None:
            raise ToolCallError("source_error", "no %s is configured" % name)
        return source
