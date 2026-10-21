"""
Offline reproduction of a run (ui/REQUIREMENTS_CORE.md 13d step 5, CG15c): the run is repeated through the same pipeline, with no network and no model. The model answers come from the content
store, found by the hash of the prompt; the search results and the pages come from the events and the store. The graph of the new run is then compared with the graph of the old one.

  P1  a recorded answer is only used for the very prompt it was given to (the hash of the messages): when the pipeline now asks something else, the reproduction stops there and says so,
      with the difference between the prompt it expected and the one it got. That is the point of the tool: a change of code, prompt or library that changes what a run does becomes visible
  P2  nothing leaves the machine: the tools are replaced by the recordings, a query or an address that was not recorded is a divergence, not a request
  P3  what could not be recorded cannot be reproduced: runs whose texts were not stored (the chat, by default), clipped inputs, e-mail addresses and secrets (removed before storing)
  P4  the result says what differs and what diverged; "reproduced" means the same status, the same graph and no divergence
"""
import collections
import difflib
import json

try:
    from . import context_graph as CG
    from . import events as ev
    from . import evidence
    from .pipeline import Tool
    from .web_tools import SearchError, WebError
except ImportError:  # used as plain script / in tests
    import context_graph as CG
    import events as ev
    import evidence
    from pipeline import Tool
    from web_tools import SearchError, WebError


class Diverged(Exception):
    """the pipeline asked for something the recording does not have"""


class Recording:
    """what a run did, read from its events: the model calls, the searches with their results, the pages"""

    def __init__(self, events):
        self.calls, self.searches, self.fetches = [], [], []
        self.trust = {}                                         # the class and trust a source was given when it was found: the recording, not the table of today
        last_search = {}
        for e in sorted(events, key=lambda x: x.get("seq", 0)):
            if e.get("kind") != "event":
                continue
            t, p = e.get("type"), e.get("payload") or {}
            if t == "model_call":
                self.calls.append((p.get("prompt_hash"), p.get("response_hash")))
            elif t == "query_issued":
                record = {"query": p["query"], "backend": p.get("backend"), "results": [], "error": None}
                self.searches.append(record)
                last_search[p["query"]] = record
            elif t == "source_found" and p.get("query") in last_search:
                last_search[p["query"]]["results"].append({"title": p.get("title", ""), "url": p["ref"], "snippet": p.get("snippet", ""), "engine": p.get("engine", ""),
                                                           "date": p.get("date"), "backend": p.get("backend")})
                self.trust[p["ref"]] = {"class": p.get("source_class"), "score": p.get("trust")}
            elif t == "check_run" and p.get("name") == "search_backend" and p.get("result") == "fail" and p.get("target") in last_search:
                last_search[p["target"]]["error"] = p.get("detail") or "the search failed"
            elif t == "page_fetched":
                self.fetches.append({"ref": p["ref"], "url": p.get("url") or p["ref"], "title": p.get("title", ""), "hash": p["hash"], "clipped": bool(p.get("truncated")),
                                     "content_type": p.get("content_type", ""), "signals": p.get("signals") or [], "error": None})
            elif t == "source_dropped" and p.get("stage") == "fetch" and p.get("reason") == "fetch_failed":
                self.fetches.append({"ref": p["ref"], "error": p.get("detail") or "the page could not be loaded"})


class ReplayModel:
    """answers every prompt with the answer recorded for exactly that prompt (P1)"""

    def __init__(self, recording, store):
        self.store = store
        self.order = list(recording.calls)
        self.queues = collections.defaultdict(collections.deque)
        for prompt_hash, response_hash in self.order:
            self.queues[prompt_hash].append(response_hash)
        self.used = 0
        self.divergences = []

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        prompt_hash = ev.digest(messages)
        queue = self.queues.get(prompt_hash)
        if not queue:
            raise self._diverge("model call %d: the prompt is not one of the recorded prompts" % (self.used + 1), messages)
        text = self.store.get(queue.popleft())
        if text is None:
            raise self._diverge("model call %d: the recorded answer is not in the store (texts were not stored for this run, or have been pruned)" % (self.used + 1), None)
        self.used += 1
        return text

    def _diverge(self, message, messages):
        detail = ""
        expected = self.store.get_json(self.order[self.used][0]) if self.used < len(self.order) else None
        if messages is not None and expected is not None:
            now = ev.clean_text(messages).splitlines()
            was = ev.clean_text(expected).splitlines()
            detail = "\n".join(list(difflib.unified_diff(was, now, "recorded prompt", "prompt now", lineterm="", n=1))[:40])
        self.divergences.append({"what": message, "diff": detail})
        return Diverged(message)


class ReplayTools:
    """the search and the page fetcher of the recording (P2). They write the same evidence events as the real tools (evidence.py), with the recorded class and trust of the sources,
    so that the graph of the new run can be compared with the old one."""

    def __init__(self, recording, store):
        self.store = store
        self.trust = recording.trust
        self.searches = collections.defaultdict(collections.deque)
        for record in recording.searches:
            self.searches[record["query"]].append(record)
        self.fetches = collections.defaultdict(collections.deque)
        for record in recording.fetches:
            self.fetches[record["ref"]].append(record)
        self.divergences = []

    def tools(self):
        return {"web_search": Tool(self.web_search, "search_calls"), "fetch_page": Tool(self.fetch_page, "fetch_calls")}

    def web_search(self, query, count=None, language=None, time_range=None):
        key = " ".join(str(query).split())
        queue = self.searches.get(key[:380])
        if not queue:
            self.divergences.append({"what": "a search that was not recorded: %r" % key, "diff": ""})
            raise Diverged("search not recorded: %s" % key)
        record = queue.popleft()
        if record["error"]:
            evidence.search_done(key, error=record["error"])
            raise SearchError(record["error"])
        result = {"query": key, "backend": record["backend"], "results": [dict(r) for r in record["results"]], "errors": [], "warnings": []}
        evidence.search_done(key, result, trust=lambda url: self.trust.get(url, {}))
        return result

    def fetch_page(self, url, max_chars=None):
        queue = self.fetches.get(url)
        if not queue:
            self.divergences.append({"what": "a page that was not recorded: %s" % url, "diff": ""})
            raise Diverged("page not recorded: %s" % url)
        record = queue.popleft()
        if record.get("error"):
            evidence.fetch_failed(url, record["error"])
            raise WebError(record["error"])
        text = self.store.get(record["hash"])
        if text is None:
            self.divergences.append({"what": "the text of %s is not in the store" % url, "diff": ""})
            raise Diverged("page text not in the store: %s" % url)
        page = {"url": record["url"], "ref": url, "title": record["title"], "text": text, "clipped": record["clipped"], "content_type": record["content_type"], "signals": record["signals"]}
        evidence.fetch_done(url, page, None)                    # no store: the hash is the same, and the original store is not written to
        return page


def reproduce(record, store, core_factory):
    """repeat the run of a run record offline. core_factory(model, tools) -> a Core whose run log is a throw-away one.
    Returns {"reproduced", "status": (old, new), "differences": [...], "divergences": [...], "model_calls": (used, recorded)}"""
    recording = Recording(record.get("events") or [])
    model, replay = ReplayModel(recording, store), ReplayTools(recording, store)
    core = core_factory(model, replay.tools())
    pipeline = "%s@%s" % (record["pipeline"], record["pipeline_version"]) if record.get("pipeline") and record.get("pipeline_version") else None
    result = core.run(record["task"], record.get("input"), pipeline=pipeline)
    new = core.run_log.read()[-1]
    differences = CG.diff(CG.replay_run(record), CG.replay_run(new))
    divergences = model.divergences + replay.divergences
    return {"reproduced": not differences and not divergences and result.status == record.get("status"), "status": (record.get("status"), result.status), "differences": differences,
            "divergences": divergences, "model_calls": (model.used, len(recording.calls)), "new_run": new["id"], "error": result.error}
