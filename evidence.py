"""
The evidence events of a research or lookup run (ui/REQUIREMENTS_CORE.md 13d, step 4): what was searched, found, dropped, fetched, quoted, claimed and checked, written as
typed events (events.py) by the tools and code steps themselves. This module only builds the payloads and emits them.

  E1  every helper does nothing outside a run (events.emit is a no-op without an active stream), so tools and code steps work the same with and without logging
  E2  logging must never break a run: an unexpected error in a helper is swallowed (an event that does not fit its schema is already handled by the stream: strict mode
      raises in tests, normal mode writes a log_error event)
  E3  names are stable across the steps: a web source is named by the address it was found under (ref), a passage by the hash of its source and text, a claim by the hash
      of its text, so that the events of different steps meet in the same graph node (context_graph.py)
  E4  the sub-question a step works on is the index of the map element it runs in (1-based): in the lookup pipelines the node "lookups" maps over the sub-questions
"""
import functools

try:
    from . import events as ev
except ImportError:  # used as plain script / in tests
    import events as ev

CLAIM_MAX = 7000


def _safe(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if not ev.active():
            return None
        try:
            return function(*args, **kwargs)
        except ev.EventError:
            raise
        except Exception:
            return None
    return wrapper


def subtask():
    """E4: the 1-based index of the map element the active node works on, or None"""
    item = ev.current_item()
    return item + 1 if isinstance(item, int) and not isinstance(item, bool) else None


def passage_id(ref, text):
    return "p" + ev.digest("%s\n%s" % (ref, text))[2:12]


def claim_id(text):
    return "c" + ev.digest(text)[2:12]


def _cut(text, limit):
    text = str(text or "")
    return text if len(text) <= limit else text[:limit - 1] + "…"


def _with(payload, **optional):
    payload.update({k: v for k, v in optional.items() if v is not None})
    return payload


# --- search and fetch ---------------------------------------------------------------------------------------------------------------------

@_safe
def search_done(query, result=None, error=None, trust=None):
    """query_issued, then source_found for every result (rank 1, 2, ...); a failed search is a check_run that failed"""
    backend = (result or {}).get("backend") or "none"
    ev.emit("query_issued", _with({"query": _cut(query, 380), "backend": backend}, subtask=subtask()))
    if error is not None:
        ev.emit("check_run", {"name": "search_backend", "target": _cut(query, 380), "result": "fail", "detail": _cut(error, 380)})
        return
    for rank, hit in enumerate((result or {}).get("results") or [], 1):
        known = trust(hit["url"]) if trust else {}
        ev.emit("source_found", _with({"ref": _cut(hit["url"], 1000), "title": _cut(hit.get("title") or hit["url"], 380), "backend": hit.get("backend") or backend, "rank": rank,
                                       "query": _cut(query, 380), "source_class": known.get("class"), "trust": known.get("score")}, date=hit.get("date")))


@_safe
def fetch_done(ref, page, store=None):
    """page_fetched (the text goes to the store, the event carries its hash) and a check_run for the phrases that look like instructions"""
    text = page.get("text") or ""
    hash_ = store.put(text) if store is not None else ev.digest(text)
    ev.emit("page_fetched", {"ref": _cut(ref, 1000), "hash": hash_, "bytes": len(text.encode("utf-8", "replace")), "truncated": bool(page.get("clipped")), "status": 200})
    signals = page.get("signals") or []
    ev.emit("check_run", _with({"name": "injection_signals", "target": _cut(ref, 380), "result": "fail" if signals else "pass"}, detail=_cut("; ".join(signals), 380) if signals else None))


@_safe
def fetch_failed(ref, error):
    ev.emit("source_dropped", {"ref": _cut(ref, 1000), "stage": "fetch", "reason": "fetch_failed", "detail": _cut(error, 380)})


@_safe
def urls_dropped(pairs):
    """the results that were not chosen to be read, with the reason: [(url, "duplicate" | "not_selected")]; duplicate = read already or listed twice, not_selected = further down than the
    number to read"""
    for url, reason in pairs:
        ev.emit("source_dropped", {"ref": _cut(url, 1000), "stage": "pick", "reason": reason})


# --- passages, claims, checks -------------------------------------------------------------------------------------------------------------

@_safe
def passages_collected(passages, pages, anchored):
    """passage_extracted for every passage handed to the model; anchored(quote, page text) -> bool says whether it occurs in its page"""
    texts = {}
    for page in pages if isinstance(pages, list) else []:
        if isinstance(page, dict):
            texts[page.get("url")] = page.get("text") or ""
    for p in passages:
        ref = p.get("ref") or p.get("url") or ""
        source_text = texts.get(p.get("url"), "")
        start = source_text.find(p["text"])
        payload = {"id": passage_id(ref, p["text"]), "source": _cut(ref, 1000), "quote": _cut(p["text"], 7900), "anchor_ok": bool(anchored(p["text"], source_text)), "by": "collect_passages"}
        if start >= 0:
            payload.update(start=start, end=start + len(p["text"]))
        ev.emit("passage_extracted", _with(payload, subtask=subtask()))


@_safe
def answer_checked(answer, outcome, passages):
    """the quote check of an answer (anchor_answer): a check_run per cited quote, the claim, its verdict by the rule (style "anchor", no figure of confidence) and, for an answer, the
    sentence of the draft. answer: what the model gave; outcome: what anchor_answer made of it; passages: the numbered passages the model saw."""
    by_number = {p.get("n"): p for p in passages if isinstance(p, dict)} if isinstance(passages, list) else {}
    cited = []
    for source in (answer.get("sources") if isinstance(answer, dict) and isinstance(answer.get("sources"), list) else []):
        passage = by_number.get(source.get("n")) if isinstance(source, dict) else None
        if passage:
            cited.append((source, passage_id(passage.get("ref") or passage.get("url"), passage["text"])))
    kept_quotes = {k["quote"] for k in outcome.get("sources", [])}
    for source, pid in cited:
        ok = str(source.get("quote", "")).strip() in kept_quotes
        ev.emit("check_run", _with({"name": "quote_in_source", "target": pid, "result": "pass" if ok else "fail"}, detail=None if ok else "the quote is not in the passage"))
    for entry in outcome.get("dropped", []):
        if entry.get("reason") == "no such passage":
            ev.emit("check_run", {"name": "quote_in_source", "target": "", "result": "fail", "detail": "no such passage: %s" % entry.get("n")})
    answered = outcome.get("status") == "answered"
    if answered:
        text = outcome.get("answer")
    elif outcome.get("demoted"):
        text = outcome.get("draft")                           # the model answered, but no quote held: its draft is a claim that was not found in the pages
    else:
        return                                                # the model itself said "unknown": nothing was claimed
    text = str(text or "").strip()
    if not text:
        return
    cid = claim_id(text)
    ev.emit("claim_made", _with({"id": cid, "text": _cut(text, CLAIM_MAX), "passages": [pid for _, pid in cited][:200], "by": "model"}, subtask=subtask()))
    kept_ids = [pid for source, pid in cited if str(source.get("quote", "")).strip() in kept_quotes]
    ev.emit("claim_verified", _with({"claim": cid, "verdict": "supported" if answered else "not_found", "style": "anchor",
                                     "judge": {"actor": "rule:anchor_answer", "model": None}, "confidence": None}, passage=kept_ids[0] if kept_ids else None))
    if answered:
        ev.emit("draft_sentence", {"text": _cut(text, CLAIM_MAX), "claims": [cid]})


# --- plans, facts, calculations -----------------------------------------------------------------------------------------------------------

@_safe
def plan_checked(origin, plan, checks, goals=None, subtasks=None):
    """plan_made: checks = [(name, passed, detail)]"""
    ev.emit("plan_made", _with({"origin": origin, "plan": plan, "checks": [_with({"name": _cut(n, 120), "result": "pass" if ok else "fail"}, detail=_cut(d, 380) if d else None) for n, ok, d in checks][:100]},
                               goals=goals, subtasks=subtasks))


@_safe
def fact_passages(facts):
    """the verified quotes behind the facts of a final answer are passages of their own (a sub-passage of what was read): source = the address, anchor_ok because they passed the check"""
    for f in facts:
        ev.emit("passage_extracted", _with({"id": passage_id(f["url"], f["quote"]), "source": _cut(f["url"], 1000), "quote": _cut(f["quote"], 7900), "anchor_ok": True, "by": "facts_table"},
                                           subtask=f.get("sub")))


@_safe
def facts_open(open_slots):
    """slot_opened for every sub-question that no verified quote answered: [(sub id, question)]"""
    for sub_id, question in open_slots:
        ev.emit("slot_opened", {"subtask": str(sub_id), "target": _cut(question, 380), "why": "no answer with a verified quote in the pages read"})


@_safe
def calculation_done(request, outcome):
    ev.emit("check_run", _with({"name": "calculate", "target": _cut((request or {}).get("op") if isinstance(request, dict) else "", 380), "result": "pass" if outcome.get("ok") else "fail"},
                               detail=_cut(outcome.get("text"), 380)))
