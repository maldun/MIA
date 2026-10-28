"""
The review as a chat task (/review question [until YYYY-MM-DD], A-18, A-20): the glue between the chat and ReviewRun. Nothing here talks to a model or the internet itself; the skills, the
scholarly search, the full text and the question to the user are handed in, as in research_chat.py.

  C1  the review asks the user three kinds of question (the keywords before the search, the checkpoint before the full text or a used-up limit, new keywords) and waits for the reply;
      ask(text) gives the reply text, or None when the user stopped the run or did not answer in time: None is "no"
  C2  yes / no and a list are read by code (parse_reply); a model never reads the reply
  C3  the report is shown as markdown; the summary says that a person has to check it
  C4  the voice (owner 2026-10-28): each question is spoken before the review waits, and a short result at the end, from plain texts made here; the markdown report is never read out.
      speak(text) is optional and may fail: a voice that fails must not take the report away
"""
import re

try:
    from . import review_models, review_stages
    from .review_request import ReviewRequest, RequestError
except ImportError:
    import review_models
    import review_stages
    from review_request import ReviewRequest, RequestError

YES = {"yes", "y", "ok", "okay", "go", "continue", "sure", "ja", "all"}
NO = {"no", "n", "stop", "none", "nein", "cancel"}
MAX_ITEMS, MAX_ITEM_CHARS = 12, 60
_UNTIL = re.compile(r"\s+until\s+(\d{4}-\d{2}-\d{2})$", re.I)
_SPLIT = re.compile(r"[,;\n]")


def parse_request(text):
    """(question, until): "question until 2024-06-30" -> ("question", "2024-06-30"); no date -> (question, None)"""
    text = text.strip()
    found = _UNTIL.search(text)
    if found:
        return text[:found.start()].strip(), found.group(1)
    return text, None


def parse_reply(text):
    """{"answer": "yes" | "no" | "items", "items": [..]}: yes and no words, else a list split at commas, semicolons and line breaks"""
    word = (text or "").strip().lower().strip(".!?, ")
    if word in YES:
        return {"answer": "yes", "items": []}
    if word in NO:
        return {"answer": "no", "items": []}
    items = [i.strip().strip("\"'“”‘’ ").strip() for i in _SPLIT.split(text or "")]
    items = [i for i in items if i and len(i) <= MAX_ITEM_CHARS][:MAX_ITEMS]
    return {"answer": "items", "items": items}


# --- what the user reads --------------------------------------------------------------------------------------------------------------

def keywords_prompt(keywords, criteria):
    lines = ["I will search for these keywords:"] + ["- " + k for k in keywords]
    if criteria:
        lines += ["", "A work is ruled out by these criteria:"] + ["- %s: %s" % (c["code"], c["text"]) for c in criteria]
    lines += ["", "Reply **yes** to start, **no** to cancel, or send your own keywords separated by commas."]
    return "\n".join(lines)


def _flow_line(flow):
    return ("%d records found (%d duplicates), %d dropped before screening, %d screened: %d included, %d maybe, %d excluded at the abstract, %d excluded at the full text, %d not yet decided"
            % (flow["found"], flow["duplicates"], flow["dropped"], flow["screened"], flow["included"], flow["maybe"], flow["excluded_abstract"], flow["excluded_full"], flow["undecided"]))


def checkpoint_prompt(report):
    asking = report.get("asking") or "checkpoint"
    lines = [_flow_line(report["flow"])]
    if asking.startswith("limit:"):
        lines += ["", "The limit **%s** is used up. Continue with another slice?" % asking.split(":", 1)[1], "Reply **yes** or **no**; with **no** you get the report as it stands."]
    else:
        advice = report.get("recommendation") or {}
        if advice:
            lines += ["", "Recommendation: **%s** - %s" % (advice["action"], advice["why"])]
        lines += ["", "Read the full texts of the works that are not excluded (open access only)? Reply **yes** or **no**; with **no** you get the report as it stands."]
    return "\n".join(lines)


def terms_prompt(proposals, n):
    listed = ", ".join("%s (%d)" % (p["term"], p["works"]) for p in proposals)
    return ("These terms occur in at least %d of the screened works and are not in the keyword list: %s.\nSearch for them too? Reply **yes** (all), **no**, or the terms you want, separated by commas."
            % (n, listed))


def spoken_keywords(keywords, limit=8):
    return "I will search for these keywords: %s. Shall I start? Say yes, or send your own list." % ", ".join(keywords[:limit])


def spoken_checkpoint(report):
    asking = report.get("asking") or "checkpoint"
    if asking.startswith("limit:"):
        return "The limit %s is used up. Shall I continue?" % asking.split(":", 1)[1]
    flow, advice = report["flow"], report.get("recommendation") or {}
    said = "I screened %d works: %d included, %d maybe." % (flow["screened"], flow["included"], flow["maybe"])
    if advice:
        said += " I recommend to %s." % advice["action"]
    return said + " Shall I read the full texts?"


def spoken_terms(proposals, limit=8):
    return "These terms occur in several works: %s. Shall I search for them too?" % ", ".join(p["term"] for p in proposals[:limit])


def spoken_result(report):
    flow = report["flow"]
    counts = "I found %d works and included %d." % (flow["found"], flow["included"])
    summary = report.get("summary")
    if summary:
        return "The review is done. %s Coverage of your question is %s. The report is in the chat, please check the summary against the sources." % (counts, summary["figures"]["level"])
    return "I stopped the review. %s The report is in the chat as it stands." % counts


def format_report(report, question, until):
    out = ["## Literature review", "", "**Question:** %s" % question, "**Cut-off:** %s   **Ended by:** %s" % (until, report["ended_by"])]
    summary = report.get("summary")
    if summary:
        figures = summary["figures"]
        out += ["", "### Summary (a draft: a person has to check it against the sources)", "**Coverage of the question: %s.** %s" % (figures["level"], summary["coverage"])]
        out += ["", "**What was found**"] + (["- %s (%s)" % (p["point"], ", ".join(p["works"])) for p in summary["found"]] or ["- nothing that could be cited"])
        out += ["", "**Gaps**"] + (["- %s%s" % (g["gap"], " (%s)" % ", ".join(g["works"]) if g["works"] else "") for g in summary["gaps"]] or ["- none named"])
        if summary["dropped_points"]:
            out.append("(%d point(s) of the summary were removed because they cited no work of this review.)" % summary["dropped_points"])
    out += ["", "### How the works were selected", _flow_line(report["flow"]) + ".", "", "| Keyword | Origin | Hits |", "|---|---|---|"]
    out += ["| %s | %s | %d |" % (k["keyword"], k["origin"], k["hits"]) for k in report["keywords"]]
    if report["gaps"]:
        out.append("\nKeywords without an included work: %s." % ", ".join(report["gaps"]))
    works = report["works"]

    def block(title, rows):
        if rows:
            out.extend(["", "### " + title] + ["- **%s** (%s, relevance %d%s): %s" % (w["title"], w["doi"] or "no DOI", w["grade"], ", abstract only" if w["abstract_only"] else "",
                                                                                      " ".join(w["notes"]) or "no note") for w in rows])
    block("Included", [w for w in works if w["decision"] == "include"])
    block("Maybe", [w for w in works if w["decision"] == "maybe"])
    block("Excluded although closely related (relevance 2 or 3)", [w for w in works if w["decision"] == "exclude" and w["grade"] >= 2])
    if report["dropped"]:
        out += ["", "### Dropped before screening"] + ["- %s: %s" % (d["work"].get("title") or d["work"].get("doi"), d["reason"]) for d in report["dropped"]]
    return "\n".join(out)


# --- the task --------------------------------------------------------------------------------------------------------------------------

def run_review(text, run_skill, scholar, full_text_source, ask, on_event=None, should_stop=None, cfg=None, today=None, min_works=3, speak=None):
    """the review of `text` ("question [until YYYY-MM-DD]") as markdown. scholar.search(query, limit, until, since, check_retraction) is Scholar.search; full_text_source(work) is a
    FullTextSource; ask(text) -> the reply text or None; speak(text) says a short text aloud (None: silent). The model steps run through run_skill(name, inputs) (core.run); on_event gets {"kind": "step", "plain": text} per stage."""
    cfg = cfg or {}
    question, until = parse_request(text)
    try:
        request = ReviewRequest.from_config(question, cfg, until=until, today=today)
    except RequestError as exc:
        return "I cannot start the review: %s." % exc
    started = {"shown": False}

    def say(spoken):
        if speak is None:
            return
        try:
            speak(spoken)
        except Exception:                      # a voice that fails must not take the report away
            pass

    def progress(plain):
        if on_event is None:
            return
        if not started["shown"]:
            started["shown"] = True
            on_event({"kind": "run_start", "payload": {"show": True}})
        on_event({"kind": "step", "plain": plain})

    progress("choosing keywords")
    concepts, criteria = review_models.plan_keywords(run_skill, question)
    keywords = [k for words in concepts.values() for k in words]
    say(spoken_keywords(keywords))
    reply = parse_reply(ask(keywords_prompt(keywords, criteria)))
    if reply["answer"] == "no" or (reply["answer"] == "items" and not reply["items"]):
        return "The review was cancelled before the search."
    if reply["answer"] == "items":
        keywords = reply["items"]

    def search(keyword, query):
        progress("searching for %s" % keyword)
        found = scholar.search(query, limit=cfg.get("review_results_per_keyword", 10), until=request.until, since=request.since, check_retraction=True)
        return found["works"]

    def screen_abstract_noted(work):
        progress("reading the abstract: %s" % (work.get("title") or work.get("doi")))
        return abstract(work)

    def screen_full_noted(work, text_):
        progress("reading the full text: %s" % (work.get("title") or work.get("doi")))
        return full(work, text_)

    def agree(report):
        say(spoken_checkpoint(report))
        return parse_reply(ask(checkpoint_prompt(report)))["answer"] == "yes"

    def approve_terms(proposals):
        say(spoken_terms(proposals))
        reply_ = parse_reply(ask(terms_prompt(proposals, min_works)))
        if reply_["answer"] == "yes":
            return [p["term"] for p in proposals]
        wanted = {i.lower() for i in reply_["items"]}
        return [p["term"] for p in proposals if p["term"].lower() in wanted]

    abstract, full = review_models.make_screeners(run_skill, question, criteria)
    run = review_stages.ReviewRun(request, keywords, {c["code"] for c in criteria} or set(review_models.CODES), search=search, screen_abstract=screen_abstract_noted,
                                  screen_full=screen_full_noted, full_text=full_text_source, agree=agree, approve_terms=approve_terms, min_works=min_works,
                                  summarize=review_models.make_summarizer(run_skill, question), should_stop=should_stop)
    report = run.run()
    progress("writing the report")
    say(spoken_result(report))
    return format_report(report, question, request.until.isoformat())
