"""
The code steps of the research pipelines (ui/REQUIREMENTS_CORE.md 13.1, 13b). The pipelines themselves are library entries; what is decided by code, not by a model, lives here:

  top_urls(hits, n)                                  the first n distinct addresses of a search result
  collect_passages(question, pages, ...)             the passages of the fetched pages that share most words with the question, numbered, within a character budget, rendered as untrusted web text
  normalize_plan(plan, question)                     the plan of a model made safe: one to four sub-questions with a query each (the question itself when the plan is empty), and whether it is a single lookup
  facts_table(subquestions, results)                 the verified answers of the sub-questions as numbered facts for the final answer (and as passages to anchor it again)
  calculate(request)                                 the calculation a model asked for, done by code: weekday, years_between, days_between, add_days (dates as YYYY-MM-DD, years as YYYY)
  only_result(results)                               the first result of a list (a single lookup needs no composing)
  anchor_answer(answer, passages)                    what a model answered, made safe: a source stays only if its quote really occurs in the passage it cites; an answer without a single
                                                     verified source is demoted to "unknown" (a research pipeline never states what it cannot quote)
"""
import datetime
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


def top_urls(hits, n=3, exclude=None):
    results = hits.get("results") if isinstance(hits, dict) else hits
    urls, seen = [], {web_tools.normalize_url(u) for u in exclude if isinstance(u, str)} if isinstance(exclude, list) else set()
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


MAX_SUBQUESTIONS = 4


def normalize_plan(plan, question):
    """{"subquestions": [{id, question, query}], "needs_calculation": bool, "single": bool}"""
    items = plan.get("subquestions") if isinstance(plan, dict) else None
    subs, seen = [], set()
    for item in items if isinstance(items, list) else []:
        text = str(item.get("question", "")).strip() if isinstance(item, dict) else ""
        if len(text) < 3 or text.casefold() in seen:
            continue
        seen.add(text.casefold())
        subs.append({"id": len(subs) + 1, "question": text, "query": " ".join(str(item.get("query", "")).split()) or text})
        if len(subs) >= MAX_SUBQUESTIONS:
            break
    if not subs:
        subs = [{"id": 1, "question": str(question), "query": str(question)}]
    needs = bool(plan.get("needs_calculation")) if isinstance(plan, dict) else False
    return {"subquestions": subs, "needs_calculation": needs, "single": len(subs) == 1}


def only_result(results):
    return results[0] if isinstance(results, list) and results else {"answer": NO_ANSWER, "status": "unknown", "sources": []}


def facts_table(subquestions, results):
    """{"facts": [{n, sub, question, answer, url, quote}], "passages": [{n, url, text}], "context": text, "answered": int, "open": [questions]}"""
    facts, lines, open_questions = [], [], []
    for index, sub in enumerate(subquestions if isinstance(subquestions, list) else []):
        result = results[index] if isinstance(results, list) and index < len(results) and isinstance(results[index], dict) else {}
        if result.get("status") != "answered" or not result.get("sources"):
            open_questions.append(sub.get("question"))
            lines.append("Sub-question %s: %s\n  No answer was found in the pages read." % (sub.get("id"), sub.get("question")))
            continue
        lines.append("Sub-question %s: %s\n  Answer: %s" % (sub.get("id"), sub.get("question"), result.get("answer")))
        for source in result["sources"]:
            n = len(facts) + 1
            facts.append({"n": n, "sub": sub.get("id"), "question": sub.get("question"), "answer": result.get("answer"), "url": source["url"], "quote": source["quote"]})
            lines.append("  [%d] quote from %s: \"%s\"" % (n, source["url"], source["quote"]))
    return {"facts": facts, "passages": [{"n": f["n"], "url": f["url"], "text": f["quote"]} for f in facts], "context": "\n".join(lines) or "(nothing was found)",
            "answered": len({f["sub"] for f in facts}), "open": open_questions}


def _date(value):
    text = str(value).strip()
    if re.fullmatch(r"\d{4}", text):
        return int(text), None
    try:
        day = datetime.date.fromisoformat(text)
    except ValueError:
        return None, None
    return day.year, day


def calculate(request):
    """{"ok", "text"}: the calculation a model asked for, {"op": weekday | years_between | days_between | add_days | none, "a", "b", "n"}"""
    if not isinstance(request, dict) or request.get("op") in (None, "", "none"):
        return {"ok": True, "text": "(no calculation)"}
    op = request["op"]
    (year_a, day_a), (year_b, day_b) = _date(request.get("a")), _date(request.get("b"))
    if op == "weekday":
        if day_a is None:
            return {"ok": False, "text": "(the weekday needs a full date YYYY-MM-DD)"}
        return {"ok": True, "text": "%s was a %s." % (day_a.isoformat(), day_a.strftime("%A"))}
    if op == "years_between":
        if year_a is None or year_b is None:
            return {"ok": False, "text": "(the years could not be read)"}
        text = "%d - %d = %d calendar years between %s and %s." % (max(year_a, year_b), min(year_a, year_b), abs(year_b - year_a), request.get("a"), request.get("b"))
        if day_a and day_b:
            early, late = sorted((day_a, day_b))
            full = late.year - early.year - ((late.month, late.day) < (early.month, early.day))
            text += " Full years elapsed between the two dates: %d." % full
        return {"ok": True, "text": text + (" The earlier one is %s." % request.get("a") if year_a < year_b else " The earlier one is %s." % request.get("b") if year_b < year_a else "")}
    if op == "days_between":
        if day_a is None or day_b is None:
            return {"ok": False, "text": "(days between need two full dates)"}
        return {"ok": True, "text": "%d days between %s and %s." % (abs((day_b - day_a).days), day_a.isoformat(), day_b.isoformat())}
    if op == "add_days":
        try:
            moved = day_a + datetime.timedelta(days=int(request.get("n")))
        except (TypeError, ValueError, AttributeError, OverflowError):
            return {"ok": False, "text": "(a full date and a number of days are needed)"}
        return {"ok": True, "text": "%s plus %s days is %s." % (day_a.isoformat(), request.get("n"), moved.isoformat())}
    return {"ok": False, "text": "(unknown calculation %s)" % op}


FUNCTIONS = {"top_urls": top_urls, "collect_passages": collect_passages, "anchor_answer": anchor_answer, "normalize_plan": normalize_plan, "facts_table": facts_table,
             "calculate": calculate, "only_result": only_result}
