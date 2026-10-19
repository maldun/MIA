"""
The code steps of the research pipelines (ui/REQUIREMENTS_CORE.md 13.1, 13b). The pipelines themselves are library entries; what is decided by code, not by a model, lives here:

  top_urls(hits, n)                                  the first n distinct addresses of a search result
  collect_passages(question, pages, ...)             the passages of the fetched pages that share most words with the question, numbered, within a character budget, rendered as untrusted web text
  check_plan(plan, question)                         normalize_plan plus the checks of 13b ST11: what asks for what the question states, what has little to do with the question, near-duplicates,
                                                     multi-step plans that lose the question, the question's own words for a single lookup, calculations flagged by wording; every change is reported
  check_typed_plan / typed_prepare / typed_lookup_record / typed_other / typed_summary   a typed plan (13b ST10) is checked, then run step by step: the next step with the results of the earlier ones
                                                     substituted (#2 becomes "Nordbau"), a lookup answered with a quote and a bare value, an operation done by code, blocked when a step it needs has no value
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
    from . import checks, plans, web_tools
except ImportError:  # used as plain script / in tests
    import checks
    import plans
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


def _plain_value(text):
    """a value as plain words for the comparison with a quote: lower case, no punctuation, no thousands separators"""
    return " ".join(re.sub(r"[^\w.]+", " ", re.sub(r"(?<=\d),(?=\d{3})", "", str(text)).casefold()).split())


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
    extra = {}
    if "value" in answer:                      # the bare value of a lookup (a name, a number, a date): only if it stands in a verified quote
        value = str(answer.get("value") or "").strip()
        extra["value"] = value if value and any(_plain_value(value) in _plain_value(k["quote"]) for k in kept) else None
    if status != "answered" or not text:
        return {"answer": text or NO_ANSWER, "status": "unknown", "sources": [], "dropped": dropped, "demoted": False, **({"value": None} if extra else {})}
    if not kept:
        return {"answer": NO_ANSWER, "status": "unknown", "sources": [], "dropped": dropped, "demoted": True, "draft": text, **({"value": None} if extra else {})}
    return {"answer": text, "status": "answered", "sources": kept, "dropped": dropped, "demoted": False, **extra}


MAX_SUBQUESTIONS = 4
_MONTHS = {name: number for number, names in enumerate((("january", "jan"), ("february", "feb"), ("march", "mar"), ("april", "apr"), ("may",), ("june", "jun"), ("july", "jul"), ("august", "aug"),
                                                         ("september", "sep", "sept"), ("october", "oct"), ("november", "nov"), ("december", "dec")), 1) for name in names}


def to_number(value):
    """the first number in a text (thousands separators allowed), or None"""
    match = re.search(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?", str(value))
    return float(match.group(0).replace(",", "")) if match else None


def to_date(value):
    """a date in a text as datetime.date (YYYY-MM-DD, 5 June 1998, June 5, 1998), or None"""
    text = str(value)
    try:
        match = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
        if match:
            return datetime.date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        match = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b", text)
        if match and match.group(2).lower() in _MONTHS:
            return datetime.date(int(match.group(3)), _MONTHS[match.group(2).lower()], int(match.group(1)))
        match = re.search(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", text)
        if match and match.group(1).lower() in _MONTHS:
            return datetime.date(int(match.group(3)), _MONTHS[match.group(1).lower()], int(match.group(2)))
    except ValueError:
        return None
    return None


def _as_year_or_date(value):
    day = to_date(value)
    if day:
        return day.isoformat()
    match = re.search(r"\b(\d{4})\b", str(value))
    return match.group(1) if match else None


def _number_text(number):
    return str(int(number)) if float(number).is_integer() else ("%g" % number)


def check_typed_plan(plan, question):
    """{"valid", "plan", "problems"}: a typed plan is run only if its structure is sound (plans.typed_problems) and the question is one for a plan (a comparison, a chain, two questions in one, or a
    calculation); a simple question takes the cheap way"""
    problems = plans.typed_problems(plan)
    if not problems and not any(isinstance(s, dict) and s.get("op") == "lookup" for s in plan["steps"]):
        problems.append("a plan needs at least one lookup")
    if not problems and len(plan["steps"]) > 8:
        problems.append("more than 8 steps")
    if not problems and not (_COMPOUND.search(str(question)) or _CALCULATION.search(str(question))):
        problems.append("a simple question needs no plan")
    return {"valid": not problems, "plan": plan if isinstance(plan, dict) else {}, "problems": problems}


def typed_start():
    return []


def _label(step, entity=None):
    return "%s of %s" % (step.get("attribute", ""), entity if entity is not None else step.get("entity", ""))


def typed_prepare(plan, values, question=""):
    """the next step to run: {"done": True}, or {"done": False, "kind": "lookup", "step", "question", "query", "label"} (a runnable lookup, its entity substituted), or {"done": False, "kind": "other", "step"}
    for an operation or a step that is blocked because a step it needs has no value"""
    finished = {v["id"]: v for v in values}
    for step in plan.get("steps", []):
        if step["id"] in finished:
            continue
        if step["op"] == "lookup":
            entity = step["entity"]
            if str(entity).startswith("#"):
                source = finished.get(int(str(entity)[1:]))
                if not source or not source.get("ok"):
                    return {"done": False, "kind": "other", "step": step, "blocked": True}
                entity = str(source["value"])
            return {"done": False, "kind": "lookup", "step": step, "label": _label(step, entity), "question": "What is the %s of %s?" % (step["attribute"], entity),
                    "query": "%s %s" % (step["attribute"], entity)}
        refs = [a for a in step.get("args", []) if str(a).startswith("#")]
        if any(not finished.get(int(str(r)[1:]), {}).get("ok") for r in refs):
            return {"done": False, "kind": "other", "step": step, "blocked": True}
        return {"done": False, "kind": "other", "step": step, "blocked": False}
    return {"done": True}


def typed_lookup_record(values, current, attempt):
    """the values so far plus the result of the lookup just run (ok only if the answer is supported by a quote and has a bare value that stands in the quote)"""
    attempt = attempt if isinstance(attempt, dict) else {}
    ok = attempt.get("status") == "answered" and bool(attempt.get("value"))
    step = current["step"]
    return list(values) + [{"id": step["id"], "kind": "lookup", "label": current["label"], "question": current["question"], "ok": ok, "value": attempt.get("value") if ok else None,
                            "result": {k: attempt.get(k) for k in ("answer", "status", "sources")}}]


def _operand(args, finished, index):
    a = args[index]
    return finished[int(a[1:])] if str(a).startswith("#") else {"value": a, "label": str(a), "ok": True}


def typed_other(values, current):
    """runs the operation of the step (difference, compare, weekday, days_between, years_between, add_days) with the values so far, or records that it is blocked"""
    step = current["step"]
    finished = {v["id"]: v for v in values}
    entry = {"id": step["id"], "kind": "op", "op": step["op"], "label": step["op"], "ok": False, "value": None, "text": "(blocked: a step it needs has no value)"}
    if not current.get("blocked"):
        args = step.get("args", [])
        first = _operand(args, finished, 0)
        second = _operand(args, finished, 1) if len(args) > 1 else None
        op = step["op"]
        if op in ("difference", "compare"):
            na, nb = to_number(first["value"]), to_number(second["value"])
            if na is None or nb is None:
                entry["text"] = "(the values %r and %r are not numbers)" % (first["value"], second["value"])
            elif op == "difference":
                unit = " %s" % step["unit"] if step.get("unit") else ""
                entry.update(ok=True, value=_number_text(abs(na - nb)), text="%s = %s, %s = %s: the difference is %s%s." % (first["label"], _number_text(na), second["label"], _number_text(nb),
                                                                                                                         _number_text(abs(na - nb)), unit))
            else:
                high, low = ((first, na), (second, nb)) if na >= nb else ((second, nb), (first, na))
                entry.update(ok=True, value=high[0]["label"], text="%s = %s, %s = %s: the larger value is %s, the smaller value is %s." % (first["label"], _number_text(na), second["label"], _number_text(nb),
                                                                                                                                       high[0]["label"], low[0]["label"]))
        else:
            request = {"op": op}
            if op == "weekday":
                request["a"] = to_date(first["value"]).isoformat() if to_date(first["value"]) else None
            elif op == "add_days":
                request.update(a=to_date(first["value"]).isoformat() if to_date(first["value"]) else None, n=to_number(second["value"]) if second else None)
                request["n"] = int(request["n"]) if request["n"] is not None else None
            elif op in ("days_between", "years_between"):
                request.update(a=_as_year_or_date(first["value"]), b=_as_year_or_date(second["value"]) if second else None)
            done = calculate(request) if request.get("a") else {"ok": False, "text": "(no usable date or year in %r)" % first["value"]}
            entry.update(ok=done["ok"], text="%s: %s" % (first["label"] if op == "weekday" else op, done["text"]), value=done["text"] if done["ok"] else None)
    return list(values) + [entry]


def typed_summary(plan, values, question=""):
    """{"facts" ..., "context", "passages", "answered", "open", "calculation"}: the lookups as numbered facts and the operations as one text, for the final answer"""
    lookups = [v for v in values if v["kind"] == "lookup"]
    table = facts_table([{"id": v["id"], "question": v["question"]} for v in lookups], [dict(v["result"], status="answered" if v["ok"] else "unknown") for v in lookups])
    operations = [v for v in values if v["kind"] == "op"]
    table["calculation"] = "\n".join("Step %d (%s): %s" % (v["id"], v["op"], v["text"]) for v in operations) or "(no calculation)"
    return table


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


_ASK_WORDS = {"which", "what", "where", "when", "who", "whom", "whose", "how", "does", "did", "there"}
_NAME_OF = re.compile(r"\bnames? of (?:the )?([A-Z][\w'-]*(?:\s+[A-Z][\w'-]*)*)\s*\??$")      # "the name of the Tarn Museum": a proper name that the question has already
_COMPOUND = re.compile(r"\b(?:or|than|both|each|between|compare|difference|older|younger|longer|shorter|bigger|larger|smaller|taller|earlier|later)\b"
                       r"|,\s*and\b|\band\s+(?:when|who|what|where|how|which|by how)\b|\bof the\b.*\bof the\b|\bthat (?!is\b|are\b)\w+|\b(?:where|whose)\s+(?!is\b|are\b)\w+"
                       r"|(?<=\w\s)\bwho\s+(?!is\b|are\b)\w+", re.I)
_CALCULATION = re.compile(r"\b(day of the week|what day|which day|weekday|how many (?:years|days|months|weeks)|(?:years?|days?|months?) (?:older|younger|earlier|later|between|passed|apart)|older|younger|difference|"
                          r"how much (?:more|less|longer|shorter|bigger|smaller|taller)|by how many)\b", re.I)
MIN_SHARED = 2             # a lookup must share this many content words with the question
MIN_COVERAGE = 0.6         # a plan of several lookups must keep this share of the question's content words
SIMILAR = 0.7              # lookups with this share of their words in common are the same lookup


def _stems(text):
    """the content words of a text, cut to four letters (works = work, founded = founding)"""
    return {w[:4] for w in re.findall(r"[^\W_]+", str(text).casefold()) if len(w) >= 3 and w not in _STOP_WORDS and w not in _ASK_WORDS}


def _same_lookup(a, b):
    """two lookups are the same when one has no word the other lacks, or when they share SIMILAR of their words"""
    return bool(a and b) and (a <= b or b <= a or len(a & b) / len(a | b) >= SIMILAR)


def check_plan(plan, question):
    """normalize_plan plus the checks of 13b ST11. Returns the plan with "checks": [{rule, detail}] (what was changed and why) and "fallback": True when the plan was replaced by the question itself."""
    base = normalize_plan(plan, question)
    subs, checks = list(base["subquestions"]), []
    wanted = _stems(question)
    calculation = base["needs_calculation"] or bool(_CALCULATION.search(str(question)))       # then the lookups are the facts the calculation needs, not the question itself
    if len(subs) > 1 and not _COMPOUND.search(str(question)) and not calculation:
        checks.append({"rule": "simple question", "detail": "the question has no sign of a comparison, a chain or two questions in one: the question itself is the only lookup (the planner wrote %d)" % len(subs)})
        subs = []
    if len(subs) > 1:
        kept = []
        for sub in subs:
            own = _stems(sub["question"])
            named = _NAME_OF.search(sub["question"].strip())
            if named and named.group(1).casefold() in str(question).casefold():
                checks.append({"rule": "nothing new", "detail": "dropped %r: it asks for the name of %s, which the question already names" % (sub["question"], named.group(1))})
            elif len(own & wanted) < MIN_SHARED:
                checks.append({"rule": "off topic", "detail": "dropped %r: it shares fewer than %d content words with the question" % (sub["question"], MIN_SHARED)})
            else:
                kept.append(sub)
        subs = kept
    merged = []
    for sub in subs:
        own = _stems(sub["question"])
        twin = next((m for m in merged if own and _same_lookup(own, _stems(m["question"]))), None)
        if twin is None:
            merged.append(sub)
        elif own > _stems(twin["question"]):                      # the later one says everything the earlier said and more: it replaces it
            checks.append({"rule": "redundant", "detail": "dropped %r: %r says the same and more" % (twin["question"], sub["question"])})
            merged[merged.index(twin)] = sub
        else:
            checks.append({"rule": "redundant", "detail": "dropped %r: the same lookup as %r" % (sub["question"], twin["question"])})
    subs = merged
    fallback = False
    if len(subs) > 1:
        covered = set().union(*(_stems(s["question"] + " " + s["query"]) for s in subs))
        share = len(covered & wanted) / len(wanted) if wanted else 1.0
        if share < MIN_COVERAGE:
            checks.append({"rule": "coverage", "detail": "the plan keeps only %.0f%% of the question's content words: the question itself is used" % (100 * share)})
            subs, fallback = [], True
    if not subs:
        subs, fallback = [{"id": 1, "question": str(question), "query": str(question)}], True
    if len(subs) == 1 and not calculation and (subs[0]["question"].strip() != str(question).strip() or subs[0]["query"].strip() != str(question).strip()):
        if not fallback:
            checks.append({"rule": "verbatim", "detail": "a single lookup keeps the question's own words (was %r)" % subs[0]["question"]})
        subs = [{"id": 1, "question": str(question), "query": str(question)}]
    for index, sub in enumerate(subs, 1):
        sub["id"] = index
    needs = base["needs_calculation"]
    if not needs and calculation:
        needs = True
        checks.append({"rule": "calculation", "detail": "the wording of the question asks for a calculation"})
    return {"subquestions": subs, "needs_calculation": needs, "single": len(subs) == 1, "checks": checks, "fallback": fallback}


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
             "calculate": calculate, "only_result": only_result, "check_plan": check_plan, "check_typed_plan": check_typed_plan,
             "typed_start": typed_start, "typed_prepare": typed_prepare, "typed_lookup_record": typed_lookup_record, "typed_other": typed_other, "typed_summary": typed_summary}
