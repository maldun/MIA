"""
The code steps of the research pipelines (ui/REQUIREMENTS_CORE.md 13.1, 13b). The pipelines themselves are library entries; what is decided by code, not by a model, lives here:

  top_urls(hits, n)                                  the first n distinct addresses of a search result
  collect_passages(question, pages, ...)             the passages of the fetched pages that share most words with the question, numbered, within a character budget, rendered as untrusted web text
  anchor_answer(answer, passages)                    what a model answered, made safe: a source stays only if its quote really occurs in the passage it cites; an answer without a single
                                                     verified source is demoted to "unknown" (a research pipeline never states what it cannot quote)
"""
import re

try:
    from . import checks, web_tools
except ImportError:  # used as plain script / in tests
    import checks
    import web_tools

_STOP_WORDS = {"the", "and", "for", "are", "was", "were", "how", "what", "when", "who", "does", "did", "has", "have", "with", "from", "that", "this", "which", "into", "than", "then", "its", "his", "her",
               "can", "you", "your", "our", "not", "but", "any", "all", "one", "day", "many", "much", "long", "often"}
NO_ANSWER = "I could not find an answer that the pages I read support with a quote."


def _words(text):
    return {w for w in re.findall(r"[^\W_]{3,}", str(text).casefold()) if w not in _STOP_WORDS}


def top_urls(hits, n=3):
    results = hits.get("results") if isinstance(hits, dict) else hits
    urls, seen = [], set()
    for item in results if isinstance(results, list) else []:
        url = item.get("url") if isinstance(item, dict) else None
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            continue
        key = web_tools.normalize_url(url)
        if key not in seen:
            seen.add(key)
            urls.append(url)
        if len(urls) >= max(0, int(n)):
            break
    return urls


def collect_passages(question, pages, per_page=2, size=900, budget=6000):
    """{"passages": [{n, url, title, text, score}], "context": text for the model, "signals": phrases that look like instructions, "pages": number of pages used}"""
    wanted = _words(question)
    candidates, signals, used = [], set(), 0
    for page in pages if isinstance(pages, list) else []:
        if not isinstance(page, dict) or not page.get("text"):
            continue
        used += 1
        signals.update(page.get("signals") or [])
        scored = [(len(wanted & _words(chunk)), -index, chunk) for index, chunk in enumerate(web_tools.chunk_text(page["text"], size=size, overlap=100))]
        for score, index, chunk in sorted(scored, reverse=True)[:max(1, int(per_page))]:
            candidates.append((score, -index, page.get("url", ""), page.get("title", ""), chunk))
    passages, total = [], 0
    for score, _, url, title, chunk in sorted(candidates, key=lambda c: (-c[0], c[1])):
        if total + len(chunk) > budget and passages:
            continue
        passages.append({"n": len(passages) + 1, "url": url, "title": title, "text": chunk, "score": score})
        total += len(chunk)
    context = "\n\n".join("[%d] %s (%s)\n%s" % (p["n"], p["title"] or "page", p["url"], web_tools.untrusted(p["text"], p["url"])) for p in passages)
    return {"passages": passages, "context": context or "(no pages could be read)", "signals": sorted(signals), "pages": used}


def anchor_answer(answer, passages):
    """{"answer", "status": answered | unknown, "sources": [{url, quote}], "dropped": [...], "demoted": bool, "draft": the model's answer when it was demoted}"""
    by_number = {p.get("n"): p for p in passages if isinstance(p, dict)} if isinstance(passages, list) else {}
    if not isinstance(answer, dict):
        return {"answer": NO_ANSWER, "status": "unknown", "sources": [], "dropped": [], "demoted": False}
    kept, dropped = [], []
    for source in answer.get("sources") if isinstance(answer.get("sources"), list) else []:
        if not isinstance(source, dict):
            continue
        passage, quote = by_number.get(source.get("n")), str(source.get("quote", "")).strip()
        if passage and quote and checks.quote_in_source(quote, passage["text"])["status"] == "pass":
            entry = {"url": passage["url"], "quote": quote}
            if entry not in kept:
                kept.append(entry)
        else:
            dropped.append({"n": source.get("n"), "quote": quote[:120], "reason": "no such passage" if not passage else "the quote is not in the passage"})
    text, status = str(answer.get("answer", "")).strip(), answer.get("status")
    if status != "answered" or not text:
        return {"answer": text or NO_ANSWER, "status": "unknown", "sources": [], "dropped": dropped, "demoted": False}
    if not kept:
        return {"answer": NO_ANSWER, "status": "unknown", "sources": [], "dropped": dropped, "demoted": True, "draft": text}
    return {"answer": text, "status": "answered", "sources": kept, "dropped": dropped, "demoted": False}


FUNCTIONS = {"top_urls": top_urls, "collect_passages": collect_passages, "anchor_answer": anchor_answer}
