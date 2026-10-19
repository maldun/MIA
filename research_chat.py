"""
The /research command of the chat (ui/REQUIREMENTS_CORE.md 13.1): the question goes to the skill `research`, the answer comes back as a chat message with its sources, and the answer (without the
sources) can be spoken. The task is chosen by the user: nothing here starts a web search on its own.

  format_answer(answer)      the chat text: the answer, and below it the pages and the exact words that support it
  run_research(core, ...)    runs the skill, turns the failures a user can understand into messages, returns the text
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
