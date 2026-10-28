"""
The review workflow as a literature review (specs/mia/eval-drafts/review-design.md, amendment A-18, REQ-WFM-018 to -021, -027, -028). Nothing here calls a model or the
internet: the search, the screening steps and the full text are functions that are handed in.

  Q1  one query per keyword and one combined Boolean string (OR within a concept, AND between concepts)
  C1  collect(): de-duplicate, remember which keywords found a work, drop what lies after the cut-off or is retracted and say why (PRISMA identification)
  J1  every screening judgement has two independent parts: a relevance grade 0 to 3 and an eligibility include / maybe / exclude with the reason code of a criterion;
      code never derives one from the other. The quote must occur in the source, else the judgement stays but is downgraded to "maybe" and marked unverified
  J2  combine(): sections whose quote is not in their text do not count; the full-text decision replaces the abstract decision; the grade is the highest of abstract and section grades when the sections fit the conclusion,
      else the lowest; without open full text the abstract judgements stand and are marked abstract only
  K1  propose_terms() counts by code; a term is searched only after approve(); a term that was proposed once is not proposed again
  S1  the summary: figures and the coverage level are made by code (coverage_figures); a model writes what was found and the gaps, every point cites works of the report, a point
      that cites none of them is dropped (check_summary); the summary always says that a person has to check it
  R1  ReviewRun: search per keyword, collect, abstract screening, a checkpoint (the user must agree before the full text is read), full-text screening, keyword extension;
      it ends when every collected work is decided and no approved keyword is left, or a limit is used up and the user does not continue. What a model says ("done") is ignored
"""
import re

try:
    from . import scholar
    from . import checks
    from .review_request import recommend
except ImportError:
    import scholar
    import checks
    from review_request import recommend

GRADES = (0, 1, 2, 3)
DECISIONS = ("include", "maybe", "exclude")
UNVERIFIED = "unverified_quote"
STOP_WORDS = frozenset("""this that with from have been were which their these those there about into than then also such more most other some only over under between
    using used uses based both each within without while where when what will would could should does being after before during through however thus""".split())


class StageError(ValueError):
    pass


# --- queries ------------------------------------------------------------------------------------------------------------------------

def build_queries(concepts):
    """concepts: {concept: [keyword, ...]} -> {"per_keyword": {keyword: query}, "combined": text}"""
    per_keyword, groups = {}, []
    for words in concepts.values():
        for word in words:
            per_keyword[word] = '"%s"' % word
        groups.append("(" + " OR ".join('"%s"' % w for w in words) + ")")
    return {"per_keyword": per_keyword, "combined": " AND ".join(groups)}


# --- collecting ---------------------------------------------------------------------------------------------------------------------

def work_id(work):
    return work.get("doi") or work.get("title") or ""


def _drop_code(reason):
    if "after the cut-off" in reason:
        return "after_cutoff"
    if "no publication date" in reason:
        return "no_date"
    return "before_since"


def collect(found, until=None, since=None):
    """found: {keyword: [work]} -> kept works (with `keywords`), dropped [{"work", "code", "reason"}], duplicates, by_keyword {keyword: [id]}"""
    records = [w for works in found.values() for w in works]
    unique, merged = scholar.dedupe(records)
    kept, dropped = [], []
    for work in unique:
        ok, reason = scholar.within(work, until, since)
        if not ok:
            dropped.append({"work": work, "code": _drop_code(reason), "reason": reason})
        elif scholar.retraction_state(work, as_of=until)["status"] in (scholar.RETRACTED, scholar.WITHDRAWN):
            dropped.append({"work": work, "code": "retracted", "reason": "retracted or withdrawn"})
        else:
            kept.append(work)
    for work in kept + [d["work"] for d in dropped]:
        work["keywords"] = [k for k, works in found.items() if any(scholar.same_work(work, w) for w in works)]
    by_keyword = {k: [work_id(w) for w in kept if k in w["keywords"]] for k in found}
    return {"kept": kept, "dropped": dropped, "duplicates": merged, "by_keyword": by_keyword, "found": len(records)}


# --- judgements ---------------------------------------------------------------------------------------------------------------------

def _check_parts(grade, decision, reason, criteria):
    if isinstance(grade, bool) or grade not in GRADES:
        raise StageError("the grade must be 0, 1, 2 or 3, not %r" % (grade,))
    if decision not in DECISIONS:
        raise StageError("the decision must be one of %s, not %r" % (", ".join(DECISIONS), decision))
    if (decision == "exclude" or reason) and reason not in criteria:
        raise StageError("the reason %r is not a criterion (%s)" % (reason, ", ".join(sorted(criteria))))


def _verify(judgement, source):
    quote = judgement.get("quote")
    if checks.quote_in_source(quote, source)["status"] == checks.PASS:
        return judgement
    return {**judgement, "verified": False, "decision": "maybe", "reason": UNVERIFIED}


def check_judgement(judgement, source, criteria):
    """the judgement of one abstract: values checked (StageError), the quote looked up in the source text"""
    _check_parts(judgement.get("grade"), judgement.get("decision"), judgement.get("reason", ""), criteria)
    return _verify({**judgement, "verified": True}, source)


def check_full(full, text, criteria):
    """the judgement of the full text: {"sections": [{"grade"}], "fits": bool, "decision", "reason", "quote", "statement"}; the quote is looked up in all sections"""
    sections = full.get("sections") or []
    for section in sections:
        _check_parts(section.get("grade"), "maybe", "", criteria)
    _check_parts(0, full.get("decision"), full.get("reason", ""), criteria)
    parts = text.get("sections", [])
    for i, section in enumerate(sections):                  # a section whose quote is not in its text stays in the record but does not count for the grade
        if section.get("quote") and i < len(parts):
            section["verified"] = checks.quote_in_source(section["quote"], parts[i].get("text", ""))["status"] == checks.PASS
    source = "\n".join([s.get("text", "") for s in parts] + [text.get("conclusion", "")])
    return _verify({**full, "verified": True}, source)


def combine(abstract, full=None):
    """J2: the final grade, decision and reason of a work; `abstract_only` when there is no full-text judgement"""
    if not full:
        return {"grade": abstract["grade"], "decision": abstract["decision"], "reason": abstract.get("reason", ""), "abstract_only": True}
    grades = [s["grade"] for s in full.get("sections", []) if s.get("verified", True)]
    if grades:
        section_grade = sum(grades) // len(grades)
        grade = max(abstract["grade"], section_grade) if full.get("fits") else min(abstract["grade"], section_grade)
    else:
        grade = abstract["grade"]
    return {"grade": grade, "decision": full["decision"], "reason": full.get("reason", ""), "abstract_only": False}


# --- keywords -----------------------------------------------------------------------------------------------------------------------

def _words(text):
    return re.findall(r"[a-z][a-z-]{3,}", str(text).lower())


def propose_terms(texts, keywords, n=3):
    """K1: words and two-word phrases that occur in at least n of the texts and have no word of a keyword -> [{"term", "works"}], the most frequent first"""
    taken = {w for k in keywords for w in _words(k)}
    counts = {}
    for text in texts:
        words = [w if w not in STOP_WORDS else None for w in _words(text)]
        terms = {w for w in words if w}
        terms |= {a + " " + b for a, b in zip(words, words[1:]) if a and b}
        for term in terms:
            if not taken & set(term.split()):
                counts[term] = counts.get(term, 0) + 1
    return [{"term": t, "works": c} for t, c in sorted(counts.items(), key=lambda x: (-x[1], x[0])) if c >= n]


class KeywordPool:
    """the keyword set of a run: the start keywords, the terms the user approved, and what has been searched. A term is never searched before approve()."""

    def __init__(self, keywords):
        self._keywords = list(keywords)
        self.origin = {k: "question" for k in keywords}
        self._searched, self._pending, self._seen = set(), [], set(keywords)

    def keywords(self):
        return list(self._keywords)

    def to_search(self):
        return [k for k in self._keywords if k not in self._searched]

    def mark_searched(self, keyword):
        self._searched.add(keyword)

    def propose(self, candidates):
        """the candidates not proposed before (and not a keyword); they wait for approval"""
        new = [c for c in candidates if c["term"] not in self._seen]
        self._seen.update(c["term"] for c in new)
        self._pending.extend(new)
        return new

    def approve(self, term):
        if term not in [p["term"] for p in self._pending]:
            raise StageError("%r was never proposed" % term)
        self._pending = [p for p in self._pending if p["term"] != term]
        self._keywords.append(term)
        self.origin[term] = "extension"


# --- the summary --------------------------------------------------------------------------------------------------------------------

# starting values of the coverage level, not validated: a person reads the summary anyway
THIN_BELOW = 3             # fewer included works than this: thin
GOOD_INCLUDED = 8          # at least this many included works, ...
GOOD_STRONG = 4            # ... of which at least this many with grade 2 or 3, ...
GOOD_KEYWORD_SHARE = 2 / 3  # ... and at least this share of the keywords with an included work


def coverage_figures(report):
    """counts and the level (none | thin | moderate | good) from the works of a report"""
    works = report["works"]
    included = [w for w in works if w["decision"] == "include"]
    strong = [w for w in included if w["grade"] >= 2]
    keywords = [k["keyword"] for k in report["keywords"]]
    with_includes = [k for k in keywords if any(k in w["keywords"] for w in included)]
    if not included:
        level = "none"
    elif len(included) < THIN_BELOW or not strong:
        level = "thin"
    elif len(included) >= GOOD_INCLUDED and len(strong) >= GOOD_STRONG and len(with_includes) >= GOOD_KEYWORD_SHARE * len(keywords):
        level = "good"
    else:
        level = "moderate"
    return {"included": len(included), "maybe": sum(1 for w in works if w["decision"] == "maybe"), "excluded": sum(1 for w in works if w["decision"] == "exclude"),
            "grade3": sum(1 for w in included if w["grade"] == 3), "grade2": sum(1 for w in included if w["grade"] == 2),
            "abstract_only": sum(1 for w in works if w["abstract_only"]), "keywords": len(keywords), "keywords_with_includes": len(with_includes), "level": level}


def check_summary(summary, report):
    """the summary of a model against the report: cited ids that are not works of the report are removed, a point left without a work is dropped"""
    known = {w["doi"] or w["title"] for w in report["works"]}
    dropped, found = 0, []
    for point in summary.get("found", []):
        cited = [i for i in point.get("works", []) if i in known]
        if cited:
            found.append({**point, "works": cited})
        else:
            dropped += 1
    gaps = [{**g, "works": [i for i in g.get("works", []) if i in known]} for g in summary.get("gaps", [])]
    return {"found": found, "coverage": summary.get("coverage", ""), "gaps": gaps, "dropped_points": dropped, "figures": coverage_figures(report),
            "needs_check": True}


# --- the run ------------------------------------------------------------------------------------------------------------------------

class ReviewRun:
    def __init__(self, request, keywords, criteria, search, screen_abstract, screen_full, full_text, agree, approve_terms, min_works=3, summarize=None):
        self.request, self.criteria = request, set(criteria)
        self.budget = request.budget
        self.pool = KeywordPool(keywords)
        self.search, self.screen_abstract, self.screen_full, self.full_text = search, screen_abstract, screen_full, full_text
        self.agree, self.approve_terms, self.min_works, self.summarize = agree, approve_terms, min_works, summarize
        self.found, self.hits, self.queries = {}, {}, {}
        self.judged, self.ended_by, self.recommendation = {}, "complete", None
        self.collected = {"kept": [], "dropped": [], "duplicates": 0, "by_keyword": {}, "found": 0}

    def _go(self, name=None):
        """true if the next step may run; at a used-up limit (the end of a slice included) the user is asked, and only agreement renews the limits"""
        while True:
            hit = self.budget.exhausted()
            if hit is None and (name is None or self.budget.spend(name)):
                return True
            hit = hit or name
            if not self.agree(self.report()):
                self.ended_by = "budget:" + hit
                return False
            self.budget.continue_run()

    def _search_new(self):
        for keyword in self.pool.to_search():
            if not self._go("api_requests"):
                return False
            query = build_queries({"k": [keyword]})["per_keyword"][keyword]
            self.queries[keyword] = query
            self.found[keyword] = list(self.search(keyword, query))
            self.hits[keyword] = len(self.found[keyword])
            self.pool.mark_searched(keyword)
        self.collected = collect(self.found, self.request.until, self.request.since)
        return True

    def _screen_abstracts(self):
        for work in self.collected["kept"]:
            wid = work_id(work)
            if wid in self.judged:
                continue
            if not self._go("screen"):
                return False
            judgement = check_judgement(self.screen_abstract(work), work.get("abstract", ""), self.criteria)
            self.judged[wid] = {"abstract": judgement, "full": None}
        return True

    def _screen_full_texts(self):
        for work in self.collected["kept"]:
            entry = self.judged.get(work_id(work))
            if not entry or entry["full"] or entry["abstract"]["decision"] == "exclude":
                continue
            text = self.full_text(work)
            if not text:
                continue
            if not self._go("read"):
                return False
            entry["full"] = check_full(self.screen_full(work, text), text, self.criteria)
        return True

    def run(self):
        self.budget.start()
        while True:
            if not self._search_new() or not self._screen_abstracts():
                break
            self.recommendation = recommend({"new_sources": len(self.judged)}, open_items=self.undecided())
            if not self.agree(self.report()):                  # B2: the full text only on agreement
                self.ended_by = "user"
                break
            if not self._screen_full_texts():
                break
            texts = [w.get("abstract", "") for w in self.collected["kept"]]
            fresh = self.pool.propose(propose_terms(texts, self.pool.keywords(), self.min_works))
            if not fresh:
                break
            for term in self.approve_terms(fresh) or []:
                self.pool.approve(term)
            if not self.pool.to_search():
                break
        report = self.report()
        if self.summarize and self.ended_by != "user":
            report["summary"] = check_summary(self.summarize(report), report)
        return report

    def undecided(self):
        return sum(1 for w in self.collected["kept"] if work_id(w) not in self.judged)

    def report(self):
        works, flow = [], {"found": self.collected["found"], "duplicates": self.collected["duplicates"], "dropped": len(self.collected["dropped"]),
                           "screened": len(self.judged), "excluded_abstract": 0, "excluded_full": 0, "included": 0, "maybe": 0, "undecided": self.undecided()}
        for work in self.collected["kept"]:
            entry = self.judged.get(work_id(work))
            if not entry:
                continue
            final = combine(entry["abstract"], entry["full"])
            if final["decision"] == "exclude":
                flow["excluded_abstract" if final["abstract_only"] else "excluded_full"] += 1
            else:
                flow["included" if final["decision"] == "include" else "maybe"] += 1
            notes = [e["statement"] + " [" + e["quote"] + "]" for e in (entry["abstract"], entry["full"]) if e and e.get("statement")]
            works.append({"doi": work.get("doi"), "title": work.get("title"), "keywords": work.get("keywords", []), **final, "notes": notes,
                          "verified": entry["abstract"]["verified"] and (entry["full"] or {"verified": True})["verified"]})
        included = {k for w in works if w["decision"] == "include" for k in w["keywords"]}
        keywords = [{"keyword": k, "query": self.queries.get(k), "origin": self.pool.origin[k], "hits": self.hits.get(k, 0)} for k in self.pool.keywords() if k in self.hits]
        return {"keywords": keywords, "flow": flow, "works": works, "dropped": self.collected["dropped"], "by_keyword": self.collected["by_keyword"],
                "gaps": [k["keyword"] for k in keywords if k["keyword"] not in included], "ended_by": self.ended_by, "recommendation": self.recommendation,
                "limits": self.budget.state()}
