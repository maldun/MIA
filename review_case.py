"""
Building a reference case from a published review (ui/REQUIREMENTS_RESEARCH.md 2c1): the included works of the review are taken from its text, resolved to DOIs through the scholarly APIs, and kept
as title-only entries when they cannot be resolved. The conclusions are NOT guessed: questions and labels are written by a person (draft questions may be proposed, they carry `confirmed: false`).

  parse_matrix(text)          the rows "NNN._Title    Authors   ..." of a literature matrix (as in a review that lists its selected works in a table)
  resolve(entry, clients)     DOI, year and date of one entry by title and first author (OpenAlex, then Crossref); unresolved entries stay as they are
  build_included(...)         all entries, with a report of how many were resolved and which were not, and which lie after the cut-off (an anomaly in the reference review)
  draft_case(...)             the case as eval/suites/review*/cases.jsonl wants it

  R1  a resolution is accepted only with a similar title AND (a matching author, or a long distinctive title); a generic title such as "DevOps" without a matching author is not accepted
  R2  nothing is invented: an entry that cannot be resolved keeps its title and authors and gets no DOI, and the report says so
"""
import re

try:
    from . import scholar
    from .web_tools import WebError
except ImportError:  # used as plain script / in tests
    import scholar
    from web_tools import WebError

ROW = re.compile(r"^(\d{3})\._(.+?)\s{2,}(\S.*?)(?:\s{2,}\S.*)?$")
_TITLE_STOP = {"a", "an", "the", "of", "in", "on", "for", "and", "to", "with", "from", "by", "is", "as", "at", "or", "what", "how"}


def parse_matrix(text):
    """[{"id", "title", "authors"}] from the rows of a literature matrix; the artefacts of file names in titles (underscores, hyphens) are left to the matching"""
    rows = []
    for line in str(text).splitlines():
        m = ROW.match(line.rstrip("\n"))
        if m:
            rows.append({"id": m.group(1), "title": " ".join(m.group(2).replace("_", " ").split()), "authors": m.group(3).strip()})
    return rows


def _words(title):
    forms = sorted(scholar.forms(title))
    return {w for w in (forms[0].split() if forms else []) if w not in _TITLE_STOP}


def title_similarity(a, b):
    """the share of the words that two titles have in common (0 to 1), plurals and umlauts ignored"""
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def author_tokens(authors):
    """the name words of an author string or list, lower case: 'Banica, Logica', 'Georges Bou Ghantous;Asif Gill', ['A. Wahaballa']"""
    text = " ".join(authors) if isinstance(authors, (list, tuple)) else str(authors or "")
    folded = sorted(scholar.forms(text))
    return {w for w in (folded[0].split() if folded else []) if len(w) >= 3}


def authors_match(listed, found):
    """some name word of the listed authors is a name word of the found authors (family names are what the two sources share)"""
    return bool(author_tokens(listed) & author_tokens(found))


def accept(entry, candidate, threshold=0.75):
    """R1: is the candidate work the entry? Returns the similarity or None"""
    sim = title_similarity(entry["title"], candidate["title"])
    match = authors_match(entry.get("authors"), candidate.get("authors"))
    long_title = len(_words(entry["title"])) >= 4
    if sim >= 0.95 and (match or long_title):
        return sim
    if sim >= threshold and match:
        return sim
    return None


def resolve(entry, clients, until=None, limit=5):
    """the entry with doi, year, date, matched_by and similarity when it could be resolved, else with resolved False. clients: scholar clients (searched in order)."""
    out = dict(entry, resolved=False)
    for client in clients:
        try:
            found = client.search(entry["title"], limit=limit, until=until)
        except WebError:
            continue
        best = None
        for work in found:
            sim = accept(entry, work)
            if sim is not None and (best is None or sim > best[0]):
                best = (sim, work)
        if best:
            sim, work = best
            out.update({"resolved": True, "doi": work.get("doi"), "year": work.get("year"), "date": work.get("date"), "matched_title": work["title"], "matched_by": client.name,
                        "similarity": round(sim, 2), "work_type": work.get("work_type"), "oa_url": work.get("oa_url")})
            return out
    return out


def build_included(entries, clients, until=None, progress=None):
    """(included, report): the resolved entries first-class (doi), the others as title-only; report: counts, the unresolved titles, the duplicates, the entries after the cut-off"""
    included, seen = [], []
    for n, entry in enumerate(entries, 1):
        item = resolve(entry, clients, until=None)
        if progress:
            progress(n, len(entries), item)
        included.append(item)
    unresolved = [i for i in included if not i["resolved"]]
    late = []
    if until:
        late = [i for i in included if i["resolved"] and not scholar.within({"date": i.get("date"), "year": i.get("year")}, until)[0]]
    dois = [i["doi"] for i in included if i.get("doi")]
    duplicates = sorted({d for d in dois if dois.count(d) > 1})
    report = {"entries": len(included), "resolved": len(included) - len(unresolved), "unresolved": [i["title"] for i in unresolved], "duplicates": duplicates,
              "after_cutoff": [{"title": i["title"], "date": i.get("date")} for i in late], "similarity_below_1": sum(1 for i in included if i.get("resolved") and i.get("similarity", 1) < 1)}
    return included, report


REF_START = re.compile(r"^\[([^\]\s]{1,12})\]\s*(.*)$")
_NOISE = re.compile(r"^(ACM Computing Surveys, Vol\..*|\d+:\d+|[A-Z]\. [A-Z][a-z]+ et al\.|\d{1,3})$")
_AUTHOR = r"(?:[A-Z][a-zà-ÿ]*\.\s?)+(?:[\w’'-]+\s?)+"
_YEAR = re.compile(r"\b(1[5-9]\d\d|20[0-3]\d)\b")
_DOI = re.compile(r"10\.\d{4,9}/\S+")


def parse_references(text):
    """[{"key", "raw", "authors", "title", "year", "doi"}] from a reference list whose entries start with [key]; the heuristics (authors, quoted title or the part after the authors,
    first year, the DOI printed in the entry) are for matching only: R1 makes a wrong guess an unresolved entry, never a wrong one. The text of one reference list, not a whole paper."""
    entries, current = [], None
    for line in str(text).splitlines():
        line = line.strip()
        m = REF_START.match(line)
        if m:
            current = {"key": m.group(1), "lines": [m.group(2)]}
            entries.append(current)
        elif current is not None and line and not _NOISE.match(line):
            current["lines"].append(line)
    out = []
    for entry in entries:
        raw = " ".join(l for l in entry["lines"] if l)
        raw = re.sub(r"(?<=\w)- (?=[a-z])", "", raw)                                                    # hyphenation at a line end
        doi = None
        marker = re.search(r"DOI:|doi\.org/|https?://\s*dx\.", raw)
        body = raw[:marker.start()] if marker else raw
        if marker:
            tail = re.sub(r"\s+", "", raw[marker.start():])
            m = _DOI.search(tail)
            doi = scholar.clean_doi(m.group(0).rstrip(".,;")) if m else None
        names, title, year = "", "", None
        named = re.match(r"^(.+?)\.\s+((?:1[5-9]|20)\d\d)[a-z]?\.\s+(.+)$", body)                 # "Authors. 2011. Title. Venue ..."
        if named:
            names, year = named.group(1).strip(), int(named.group(2))
            title = re.split(r"\.\s|\.$", named.group(3), maxsplit=1)[0].strip(" ,.")
        else:                                                                                      # "A. B. Name and C. Name, “Title,” venue, 1999." or "A. Name. Title. Venue 1999."
            authors = re.match(r"^(?:(?:[A-Z]\.\s?)+[\w’'-]+(?:\s*,\s*and\s+|\s+and\s+|\s*,\s*|\s*;\s*)?)+", body)
            names = authors.group(0).strip(" ,;.") if authors else ""
            rest = body[authors.end():] if authors else body
            quoted = re.search(r"[“\"]([^”\"]{8,})[”\"]", rest)
            title = quoted.group(1).strip(" ,.") if quoted else re.split(r"\.\s|,\s+vol\.|,\s+volume|\.$", rest.lstrip(" .,"), maxsplit=1)[0].strip(" ,.")
            years = _YEAR.findall(body)
            year = int(years[-1]) if years else None
        out.append({"key": entry["key"], "raw": raw, "authors": names, "title": title, "year": year, "doi": doi})
    return out


def cited_keys(text, known):
    """which of the reference keys (a set) are cited in the text as [k], [k1, k2], [k1][k2]; intervals such as [0, 1] are not citations"""
    cited = set()
    for body in re.findall(r"\[([^\[\]]{1,60})\]", str(text)):
        keys = [k for k in re.split(r"[,;\s]+|and|or|–", body) if k]
        if not keys or "0" in keys:
            continue
        cited |= {k for k in keys if k in known}
    return cited


def published_by(item, until):
    """True when the work is dated within the review's time (strict: no date at all is not within; a bare year counts to its last day)"""
    return scholar.within({"date": item.get("date"), "year": item.get("year")}, until)[0] if until else True


def gold_entry(item):
    """the compact form of an included work in a case file"""
    entry = {"title": item.get("matched_title") or item["title"], "authors": item.get("authors")}
    for key in ("doi", "year", "date"):
        if item.get(key):
            entry[key] = item[key]
    if not item.get("resolved"):
        entry["title"] = item["title"]
        entry["unresolved"] = True
    return entry


def draft_case(case_id, tags, question, until, key_terms, included, questions, review, excluded=None, notes=""):
    """a case for cases.jsonl. questions: [{"id", "question", "answer", "evidence": [{"source": "the review", "quote"}], "confirmed": bool}]"""
    return {"id": case_id, "tags": list(tags), "input": {"question": question, "until": until, "key_terms": list(key_terms)},
            "gold": {"review": review, "included": [gold_entry(i) for i in included], "excluded": list(excluded or []), "questions": list(questions)}, "expect": "pass", **({"note": notes} if notes else {})}
