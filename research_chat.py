"""
The /research command of the chat (ui/REQUIREMENTS_CORE.md 13.1): the question goes to the skill `research`, the answer comes back as a chat message with its sources, and the answer (without the
sources) can be spoken. The task is chosen by the user: nothing here starts a web search on its own.

  format_answer(answer)      the chat text: the answer, and below it the pages and the exact words that support it
  run_research(core, ...)    runs the skill, turns the failures a user can understand into messages, returns the text
  format_results / run_search  /search: the top results of the search tool as a chat message, no model, no answer
"""
import re

try:
    from .research import NO_ANSWER
except ImportError:  # used as plain script / in tests
    from research import NO_ANSWER

MAX_QUOTE = 220


def _short(quote):
    quote = " ".join(str(quote).split())
    return quote if len(quote) <= MAX_QUOTE else quote[:MAX_QUOTE].rsplit(" ", 1)[0] + " ..."


def format_answer(answer):
    """the text of the chat message for {answer, status, sources}"""
    if not isinstance(answer, dict) or not str(answer.get("answer", "")).strip():
        return NO_ANSWER
    text = str(answer["answer"]).strip()
    sources = answer.get("sources") if answer.get("status") == "answered" else None
    if not sources:
        return text
    lines = ["- %s: “%s”" % (source.get("url", ""), _short(source.get("quote", ""))) for source in sources if isinstance(source, dict)]
    return text + "\n\nSources:\n" + "\n".join(lines)


def spoken_text(answer):
    """what MIA says: the answer, not the list of sources"""
    return str(answer.get("answer", "")).strip() if isinstance(answer, dict) and answer.get("status") == "answered" else ""


def friendly_error(error):
    error = str(error or "the research failed")
    if "SearchError" in error or "no search backend" in error.lower():
        return "The web search is not reachable (%s). Is SearXNG running? (port 8590 by default; DuckDuckGo is the fallback)" % re.sub(r"^.*?SearchError:?\s*", "", error)[:300]
    if "budget" in error:
        return "The research needed more steps than the budget allows (%s)." % error
    return error


MAX_RESULTS = 5
MAX_SNIPPET = 200
_MARKDOWN = re.compile(r"([\\`*_{}\[\]()#+!|<>~])")


def _plain(text, limit):
    """text from the web as plain words: no markup can come through, no control characters, a limit"""
    text = " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", str(text)).split())
    text = text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + " ..."
    return _MARKDOWN.sub(r"\\\1", text)


def format_results(result, count=MAX_RESULTS):
    """the chat text for the answer of the search tool ({query, backend, results, errors, warnings}): numbered results with title, address and the start of the snippet"""
    results = result.get("results") if isinstance(result, dict) else None
    if not isinstance(results, list) or not results:
        return "No results for \u201c%s\u201d." % _plain(result.get("query", "") if isinstance(result, dict) else "", 120)
    lines = []
    for number, item in enumerate((r for r in results if isinstance(r, dict) and str(r.get("url", "")).startswith(("http://", "https://"))), 1):
        if number > count:
            break
        snippet = _plain(item.get("snippet", ""), MAX_SNIPPET)
        lines.append("%d. %s\n   %s%s" % (number, _plain(item.get("title", "") or item.get("url", ""), 120), re.sub(r"[\s<>]+", "", str(item["url"])), ("\n   " + snippet) if snippet else ""))
    if not lines:
        return "No usable results for \u201c%s\u201d." % _plain(result.get("query", ""), 120)
    note = "Results for \u201c%s\u201d (%s):" % (_plain(result.get("query", ""), 120), _plain(result.get("backend", "") or "search", 40))
    return note + "\n\n" + "\n\n".join(lines)


def run_search(web_search, query, count=MAX_RESULTS, should_stop=None):
    """/search: one call of the search tool (every query is written to the web log by the tool itself); a search that cannot be reached becomes a message a person can act on"""
    if should_stop is not None and should_stop():
        return ""
    try:
        result = web_search(query)
    except Exception as exc:
        raise RuntimeError(friendly_error("%s: %s" % (type(exc).__name__, exc)))
    return format_results(result, count)


def run_research(core, question, pipeline=None, on_event=None, should_stop=None, speak=None):
    result = core.run("research", {"question": question}, pipeline=pipeline, on_event=on_event, should_stop=should_stop)
    if result.status == "stopped":
        return ""
    if result.status != "done":
        raise RuntimeError(friendly_error(result.error))
    text = format_answer(result.answer)
    spoken = spoken_text(result.answer)
    if speak is not None and spoken:
        try:
            speak(spoken)
        except Exception:        # a voice that fails must not take the answer away
            pass
    return text
