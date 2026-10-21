"""
Scoring of literature reviews (ui/REQUIREMENTS_RESEARCH.md RV31 to RV33, RV37). A review pipeline gives

  {"sources":   [{"doi", "title", "date", "year"}, ...]       the works the report relies on
   "retrieved": [doi or title, ...]                            everything the run actually found (optional; without it invented references cannot be counted)
   "answers":   [{"id", "answer", "quotes": [{"source", "quote"}]}]   one answer to each conclusion question: supports | does_not_support | inconclusive | unknown
   "report": text}

The gold of a case (eval/suites/review*/cases.jsonl) says what a good review finds, in terms code can test:

  {"included":  [doi | {"doi", "title", "terms_differ"}]       the works of the reference review that fall into the allowed time
   "excluded":  [{"doi" | "title", "reason": retracted | after_cutoff | off_topic}]    works a review must not rely on
   "questions": [{"id", "question", "answer", "evidence": [{"source", "quote"}]}]}     the conclusions of the reference review as questions with a label

and the input says {"until": cut-off date, "key_terms": [...]}. What is measured and what is a hard failure:

  hard failures (the worst errors, each one makes the case fail):  a source published after the cut-off (or without a date), a source from the excluded list (a retracted paper,
      a paper after the cut-off, an off-topic one), a reference that the run never retrieved (invented), a quote that is not in the text of the source it cites
  quality (never a single figure): source recall and precision against the included works, recall of the works that do not share the question's terms (cross-field recall, H0 of the
      requirements), and the answers to the conclusion questions: correct, wrong or abstained (unknown); for a question without an answer in the literature "unknown" is the correct answer
  ok: no hard failure and every conclusion question correct
"""
import math

try:
    from . import checks, scholar
    from .metrics import wilson
except ImportError:  # used as plain script / in tests
    import checks
    import scholar
    from metrics import wilson

ANSWERS = ("supports", "does_not_support", "inconclusive", "unknown")
_SYNONYMS = {"supports": "supports", "support": "supports", "yes": "supports", "does_not_support": "does_not_support", "does not support": "does_not_support", "no": "does_not_support",
             "contradicts": "does_not_support", "inconclusive": "inconclusive", "mixed": "inconclusive", "unclear": "inconclusive", "unknown": "unknown", "none": "unknown", "": "unknown"}


def normalize_answer(answer):
    return _SYNONYMS.get(str(answer if answer is not None else "").strip().lower().replace("-", "_"), "unknown")


def _key(entry):
    """the name of a work for matching: its DOI, else its title"""
    if isinstance(entry, str):
        return scholar.clean_doi(entry) or entry
    return scholar.clean_doi(entry.get("doi")) or entry.get("title") or ""


def _same(a, b):
    """two works are the same: the same DOI, or (without a DOI on one side) the same title"""
    da = scholar.clean_doi(a.get("doi")) if isinstance(a, dict) else scholar.clean_doi(a)
    db = scholar.clean_doi(b.get("doi")) if isinstance(b, dict) else scholar.clean_doi(b)
    if da and db:
        return da == db
    ta = a.get("title") if isinstance(a, dict) else None
    tb = b.get("title") if isinstance(b, dict) else None
    return bool(ta and tb and scholar.same_title(ta, tb))


def _as_entry(item):
    return {"doi": item} if isinstance(item, str) else dict(item)


def _find(entry, others):
    return next((o for o in others if _same(entry, o)), None)


def score_review(result, gold, inputs=None, texts=None, world=None):
    """the score of one review against the gold of its case. texts: {doi: full text} or a function doi -> text, for the quote check (a world dict {doi: work} is turned into texts);
    world: {doi: work} to look up the date of a source that the result gives without one"""
    inputs = inputs or {}
    result = result if isinstance(result, dict) else {}
    included = [_as_entry(i) for i in gold.get("included", [])]
    excluded = [_as_entry(i) for i in gold.get("excluded", [])]
    listed = [_as_entry(s) for s in (result.get("sources") or []) if s and isinstance(s, (str, dict))]
    unique = []
    for s in listed:
        if not _find(s, unique):
            unique.append(s)
    until = inputs.get("until")
    out = {"hard_failures": []}

    # --- sources
    found = [i for i in included if _find(i, unique)]
    relevant = [s for s in unique if _find(s, included)]
    out["sources"] = {"listed": len(unique), "included": len(included), "found": len(found), "recall": len(found) / len(included) if included else None,
                      "precision": len(relevant) / len(unique) if unique else (None if not included else 0.0)}
    differ = [i for i in included if i.get("terms_differ")]
    out["cross_field_recall"] = (sum(1 for i in differ if _find(i, unique)) / len(differ)) if differ else None

    # --- the hard failures among the sources
    used_excluded = []
    for s in unique:
        hit = _find(s, excluded)
        if hit:
            used_excluded.append({"source": _key(s), "reason": hit.get("reason", "excluded")})
    out["excluded_used"] = used_excluded
    out["hard_failures"] += ["relies on %s (%s)" % (u["source"], u["reason"]) for u in used_excluded]
    late = []
    if until:
        for s in unique:
            known = dict(s)
            if not (known.get("date") or known.get("year")) and world and scholar.clean_doi(s.get("doi")) in world:
                known["date"] = world[scholar.clean_doi(s["doi"])].get("date")
            ok, reason = scholar.within(known, until)
            if not ok:
                late.append({"source": _key(s), "reason": reason})
    out["cutoff_violations"] = late
    out["hard_failures"] += ["time cut-off: %s: %s" % (v["source"], v["reason"]) for v in late if not any(v["source"] == u["source"] for u in used_excluded)]
    retrieved = result.get("retrieved")
    if retrieved is None:
        out["invented"] = None
    else:
        known = [_as_entry(r) for r in retrieved if isinstance(r, (str, dict))] if isinstance(retrieved, list) else []
        out["invented"] = [_key(s) for s in unique if not _find(s, known)]
        out["hard_failures"] += ["invented reference: %s" % k for k in out["invented"]]

    # --- the conclusion questions
    answers = {a.get("id"): a for a in (result.get("answers") or []) if isinstance(a, dict)}
    rows, quote_total, quote_found = [], 0, 0
    for q in gold.get("questions", []):
        given = answers.get(q["id"])
        said = normalize_answer(given.get("answer") if given else None)
        wanted = q["answer"]
        if said == "unknown" and wanted != "unknown":
            outcome = "abstained"
        else:
            outcome = "correct" if said == wanted else "wrong"
        anchored = []
        for quote in [q_ for q_ in ((given or {}).get("quotes") or []) if isinstance(q_, dict)]:
            text = _text_of(quote.get("source"), texts, world)
            if text is None:
                continue
            quote_total += 1
            good = checks.quote_in_source(quote.get("quote", ""), text)["status"] == "pass"
            quote_found += 1 if good else 0
            anchored.append(good)
            if not good:
                out["hard_failures"].append("quote not in %s: %s" % (quote.get("source"), str(quote.get("quote", ""))[:60]))
        rows.append({"id": q["id"], "gold": wanted, "given": said, "outcome": outcome, "anchored": anchored})
    correct = sum(1 for r in rows if r["outcome"] == "correct")
    wrong = sum(1 for r in rows if r["outcome"] == "wrong")
    out["questions"] = rows
    out["conclusion"] = {"total": len(rows), "correct": correct, "wrong": wrong, "abstained": len(rows) - correct - wrong,
                         "accuracy": correct / len(rows) if rows else None, "precision_when_answered": correct / (correct + wrong) if correct + wrong else None,
                         "interval": wilson(correct, len(rows)) if rows else None}
    out["anchored"] = {"quotes": quote_total, "found": quote_found, "share": quote_found / quote_total if quote_total else None}
    out["ok"] = not out["hard_failures"] and bool(rows) and correct == len(rows)
    out["status"] = "pass" if out["ok"] else "fail"
    return out


def _text_of(source, texts, world):
    """the text a quote must occur in: the full text of the cited work"""
    if source is None:
        return None
    doi = scholar.clean_doi(source) or source
    if callable(texts):
        return texts(doi)
    if isinstance(texts, dict) and doi in texts:
        return texts[doi]
    if world and doi in world:
        return work_text(world[doi])
    return None


def work_text(work):
    """title, abstract and every section of a work, as one text"""
    parts = [work.get("title", ""), work.get("abstract", "")] + [v for v in (work.get("sections") or {}).values()]
    return "\n".join(p for p in parts if p)


def summarize(scores):
    """the figures over several cases: pooled conclusion accuracy with its interval, mean source recall and precision, the hard failures by kind, and the abstentions"""
    total = sum(s["conclusion"]["total"] for s in scores)
    correct = sum(s["conclusion"]["correct"] for s in scores)
    wrong = sum(s["conclusion"]["wrong"] for s in scores)
    recalls = [s["sources"]["recall"] for s in scores if s["sources"]["recall"] is not None]
    precisions = [s["sources"]["precision"] for s in scores if s["sources"]["precision"] is not None]
    cross = [s["cross_field_recall"] for s in scores if s["cross_field_recall"] is not None]
    kinds = {"excluded": sum(len(s["excluded_used"]) for s in scores), "cutoff": sum(len(s["cutoff_violations"]) for s in scores),
             "invented": sum(len(s["invented"] or []) for s in scores), "unanchored": sum(s["anchored"]["quotes"] - s["anchored"]["found"] for s in scores)}
    mean = lambda xs: sum(xs) / len(xs) if xs else None            # noqa: E731
    return {"cases": len(scores), "passed": sum(1 for s in scores if s["ok"]), "questions": total, "correct": correct, "wrong": wrong, "abstained": total - correct - wrong,
            "accuracy": correct / total if total else None, "interval": wilson(correct, total) if total else None, "mean_recall": mean(recalls), "mean_precision": mean(precisions),
            "mean_cross_field_recall": mean(cross), "hard_failures": kinds}
