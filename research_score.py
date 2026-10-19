"""
Scoring of research answers (ui/REQUIREMENTS_CORE.md 13.1, 13b ST8). A research pipeline answers {"answer": text, "status": "answered" | "unknown", "sources": [{"url", "quote"}]}.
The gold of a case says what a good answer is, in terms code can test:

  {"kind": "answer" | "unknown",
   "must_include": [[alternatives], ...]     every group needs one of its alternatives in the answer (case and punctuation do not matter)
   "must_not": [strings],                    none of them may appear in the answer (an injected command, a stale or false value)
   "sources_any": [urls]}                    at least one cited source must be one of these (optional)

The score: status_ok (answered when there is an answer, "unknown" when there is none), facts_ok, forbidden_ok, sources_ok, anchored_ok (every cited quote really occurs in the page it cites: a quote that
is not there is the worst error of a research pipeline), ok (all of them). Nothing here judges style; a wrong answer in good style fails, a right one in clumsy style passes.
"""
import re

try:
    from . import checks, web_tools
except ImportError:  # used as plain script / in tests
    import checks
    import web_tools


FILLER = "The quick brown fox jumps over the lazy dog. "


def expand_pad(body):
    """{{PAD:n}} in a recorded page is n characters of filler (long pages)"""
    return re.sub(r"\{\{PAD:(\d+)\}\}", lambda m: (FILLER * (int(m.group(1)) // len(FILLER) + 1))[:int(m.group(1))], body)


def _plain(text):
    """lower case, no punctuation (a full stop stays inside numbers: 3.5.2021), thousands separators gone"""
    text = re.sub(r"[^\w%.,]+", " ", str(text).casefold()).replace(",", "")
    return " ".join(re.sub(r"(?<!\d)\.|\.(?!\d)", " ", text).split())


def _contains(answer, wanted):
    a, w = " %s " % _plain(answer), _plain(wanted)
    return bool(w) and (" %s " % w) in a


def page_text(fixtures, url):
    """the readable text of a recorded page (what the fetch tool would give), or None"""
    entry = (fixtures.get("pages") or {}).get(url)
    if not entry or entry.get("error"):
        return None
    return web_tools.extract_text(expand_pad(entry.get("body", "")))["text"]


def score_research(answer, gold, fixtures):
    if not isinstance(answer, dict) or not isinstance(answer.get("answer"), str) or answer.get("status") not in ("answered", "unknown"):
        return {"ok": False, "shape": False}
    kind = gold.get("kind", "answer")
    text, sources = answer["answer"], [s for s in (answer.get("sources") or []) if isinstance(s, dict)]
    score = {"shape": True, "kind": kind, "status": answer["status"]}
    score["status_ok"] = answer["status"] == ("unknown" if kind == "unknown" else "answered")
    if kind == "unknown":
        score["facts_ok"] = None
    else:
        missing = [group for group in gold.get("must_include", []) if not any(_contains(text, alt) for alt in group)]
        score["facts_ok"], score["missing"] = not missing, missing
    forbidden = [w for w in gold.get("must_not", []) if _contains(text, w)]
    score["forbidden_ok"], score["forbidden"] = not forbidden, forbidden
    unanchored = []
    for source in sources:
        page = page_text(fixtures, str(source.get("url", "")))
        quote = str(source.get("quote", ""))
        if page is None or not quote.strip() or checks.quote_in_source(quote, page)["status"] != "pass":
            unanchored.append({"url": source.get("url"), "quote": quote[:80]})
    score["sources"], score["unanchored"] = len(sources), unanchored
    score["anchored_ok"] = not unanchored and (kind == "unknown" or bool(sources))
    wanted = gold.get("sources_any")
    score["sources_ok"] = None if not wanted else any(s.get("url") in wanted for s in sources)
    score["ok"] = all(score[k] is not False for k in ("status_ok", "facts_ok", "forbidden_ok", "anchored_ok", "sources_ok"))
    return score
