"""
Scholarly sources for the literature review (ui/REQUIREMENTS_RESEARCH.md, phase 1): search in OpenAlex, Crossref, PubMed, arXiv and (with a key) Semantic Scholar,
one record format for all of them, de-duplication, the date cut-off (RV32) and the retraction status (RV15). No model is involved.

A work is a plain dict (see new_work): doi, title, abstract, date (as the source gives it: "2001-11-22", "2001-11" or "2001"), year, venue, authors, cited_by,
work_type, oa_url, sources (which APIs know it), ids, pub_types and retraction ({"status", "notices", "hints"}).

Rules:
  S1  the API hosts are fixed in this file (https, public); a politeness interval per host, one retry after 429/503 with the server's wait (capped), nothing else
      is retried; an e-mail address for the "polite pool" of OpenAlex and Crossref is only sent if "scholar_email" is configured (it is not by default)
  S2  every request goes into the web log (X4 of web_tools), answers of the last days come from a small file cache
  S3  XML is parsed without entities, DTDs and network access
  S4  the date cut-off is strict: a work counts as published up to a date only if the LATEST day its date could mean is not after the cut-off; a work without a
      date is dropped when a cut-off is given. Citation counts and retraction notices are as of today: for a cut-off in the past they are not as of the cut-off
      (use_as_of() says which parts of a record may be used then)
  S5  one failing source never stops the others; the answer lists the errors and what was dropped, with reasons
"""
import datetime
import hashlib
import json
import os
import re
import time
import unicodedata
from urllib.parse import quote, urlencode

import requests
from lxml import etree

try:
    from .web_tools import WebError, WebLog
except ImportError:  # used as plain script / in tests
    from web_tools import WebError, WebLog

USER_AGENT = "MIA-research/1.0"
OPENALEX = "https://api.openalex.org/works"
CROSSREF = "https://api.crossref.org/works"
PUBMED_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
ARXIV = "https://export.arxiv.org/api/query"
SEMANTIC_SCHOLAR = "https://api.semanticscholar.org/graph/v1/paper/search"
BACKENDS = ("openalex", "crossref", "pubmed", "arxiv", "semanticscholar")
DEFAULT_BACKENDS = ("openalex", "crossref", "pubmed", "arxiv")

RETRACTED, CORRECTION, CONCERN, WITHDRAWN, NONE, UNKNOWN = "retracted", "correction", "concern", "withdrawn", "none", "unknown"
MAX_ABSTRACT = 6000


class ScholarError(WebError):
    pass


# --- spelling, transliteration, dates (RV43a, RV32) ---------------------------------------------------------------------------------

_UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue"})


def _strip_marks(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def _plain(text):
    return re.sub(r"[^0-9a-z]+", " ", text).strip()


_IRREGULAR = {"bases": "basis", "analyses": "analysis", "hypotheses": "hypothesis", "theses": "thesis", "matrices": "matrix", "indices": "index",
              "vertices": "vertex", "criteria": "criterion", "phenomena": "phenomenon", "axes": "axis", "diagnoses": "diagnosis", "syntheses": "synthesis"}


def _singular(word):
    if word in _IRREGULAR:
        return _IRREGULAR[word]
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def forms(text):
    """the spellings a text can be matched under (RV43a): umlauts as ae/oe/ue (Groebner) or as plain letters (Grobner), case, hyphens and punctuation ignored,
    plural ignored. A set of strings with single spaces."""
    base = unicodedata.normalize("NFC", str(text or "")).casefold()
    result = set()
    for variant in (_strip_marks(base.translate(_UMLAUTS)), _strip_marks(base)):
        result.add(" ".join(_singular(w) for w in _plain(variant).split()))
    return {r for r in result if r}


def contains_term(text, term):
    """does the text contain the term as words, under any spelling of forms()? Hyphenated and joined count as the same: non-smooth, nonsmooth, non smooth"""
    text_forms, term_forms = forms(text), forms(term)
    for t in term_forms:
        joined = t.replace(" ", "")
        for x in text_forms:
            if (" " + t + " ") in (" " + x + " "):
                return True
            words = x.split()
            if len(joined) >= 6 and (joined in words or any("".join(words[i:i + n]) == joined for n in (2, 3) for i in range(len(words) - n + 1))):
                return True
    return False


def same_title(a, b):
    fa, fb = forms(a), forms(b)
    return bool(fa & fb) and min(len(x) for x in fa | fb) >= 12


def parse_date(text):
    """(year, month or None, day or None) from "2001-11-22", "2001-11", "2001", "1989 Feb", "2001/11/22"; None if there is no year"""
    if text is None:
        return None
    match = re.match(r"^\s*(\d{4})(?:[-/ ]+(\d{1,2}|[A-Za-z]{3,9}))?(?:[-/ ]+(\d{1,2}))?", str(text))
    if not match:
        return None
    year, month, day = int(match.group(1)), match.group(2), match.group(3)
    if month is not None and not month.isdigit():
        names = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        month = names.index(month[:3].lower()) + 1 if month[:3].lower() in names else None
    elif month is not None:
        month = int(month)
        month = month if 1 <= month <= 12 else None
    if month is None:
        return (year, None, None)
    day = int(day) if day and day.isdigit() and 1 <= int(day) <= 31 else None
    return (year, month, day)


def _last_day_of_month(year, month):
    return (datetime.date(year + (month == 12), month % 12 + 1, 1) - datetime.timedelta(days=1)).day


def latest_day(date):
    """the latest day a (partial) date can mean, as datetime.date; None if no year"""
    parts = parse_date(date)
    if not parts:
        return None
    year, month, day = parts
    if month is None:
        return datetime.date(year, 12, 31)
    day = min(day or 31, _last_day_of_month(year, month))
    return datetime.date(year, month, day)


def earliest_day(date):
    parts = parse_date(date)
    if not parts:
        return None
    year, month, day = parts
    return datetime.date(year, month or 1, min(day or 1, _last_day_of_month(year, month or 1)))


def as_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    parts = parse_date(value)
    if not parts:
        raise ValueError("not a date: %r" % (value,))
    return earliest_day(value) if parts[1] else datetime.date(parts[0], 12, 31)


def within(work, until=None, since=None):
    """(ok, reason). until: strict (S4); since: a work whose date could still be on or after it passes"""
    until, since = as_date(until), as_date(since)
    if until is None and since is None:
        return True, ""
    date = work.get("date") or (str(work["year"]) if work.get("year") else None)
    if until is not None:
        latest = latest_day(date)
        if latest is None:
            return False, "no publication date, so it cannot be shown to be before %s" % until
        if latest > until:
            return False, "published %s, after the cut-off %s" % (date, until)
    if since is not None:
        latest = latest_day(date)
        if latest is not None and latest < since:
            return False, "published %s, before %s" % (date, since)
    return True, ""


def use_as_of(until, today=None):
    """what of a record may be used for a cut-off: citation counts and retraction notices are as of today, so they must not steer a run that pretends to be in the past"""
    until, today = as_date(until), as_date(today) or datetime.date.today()
    current = until is None or until >= today
    return {"citations": current, "retraction_notices": current, "note": "" if current else "counts and notices are as of today, not as of %s" % until}


# --- the record ---------------------------------------------------------------------------------------------------------------------

def new_work(source, **fields):
    work = {"doi": None, "title": "", "abstract": "", "date": None, "year": None, "venue": "", "authors": [], "cited_by": None, "work_type": "", "oa_url": None,
            "sources": [source], "ids": {}, "pub_types": [], "url": None, "retraction": {"status": UNKNOWN, "notices": [], "hints": []}}
    work.update(fields)
    work["doi"] = clean_doi(work["doi"])
    work["title"] = " ".join(str(work["title"] or "").split())
    work["abstract"] = (work["abstract"] or "")[:MAX_ABSTRACT]
    if work["year"] is None and work["date"]:
        parts = parse_date(work["date"])
        work["year"] = parts[0] if parts else None
    return work


def clean_doi(doi):
    if not doi:
        return None
    doi = str(doi).strip()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", doi, flags=re.I)
    return doi.lower() or None


def reference_of(work):
    """a stable name of a work: the DOI, else the id of the first source that has one"""
    if work.get("doi"):
        return "doi:" + work["doi"]
    for name in ("pmid", "arxiv", "openalex", "s2"):
        if work["ids"].get(name):
            return "%s:%s" % (name, work["ids"][name])
    return "title:" + (sorted(forms(work.get("title", "")))[0][:60] if forms(work.get("title", "")) else "")


def same_work(a, b):
    """DOI, PubMed id, arXiv id or OpenAlex id in common; else the same normalised title with a year at most one apart"""
    if a.get("doi") and a.get("doi") == b.get("doi"):
        return True
    for name in ("pmid", "arxiv", "openalex", "s2"):
        if a["ids"].get(name) and a["ids"].get(name) == b["ids"].get(name):
            return True
    if same_title(a.get("title", ""), b.get("title", "")):
        ya, yb = a.get("year"), b.get("year")
        return ya is None or yb is None or abs(ya - yb) <= 1
    return False


def merge_works(a, b):
    """one record from two: empty fields are filled, the longer abstract and the larger citation count win, sources and notices are united"""
    merged = json.loads(json.dumps(a))
    for key in ("doi", "title", "venue", "work_type", "oa_url", "url"):
        if not merged.get(key) and b.get(key):
            merged[key] = b[key]
    if len(b.get("abstract", "")) > len(merged.get("abstract", "")):
        merged["abstract"] = b["abstract"]
    if not merged.get("date") or (b.get("date") and len(b["date"]) > len(merged["date"] or "") and str(b["date"]).startswith(str(merged.get("year") or ""))):
        merged["date"] = b.get("date") or merged.get("date")
    merged["year"] = merged.get("year") or b.get("year")
    if not merged.get("authors"):
        merged["authors"] = list(b.get("authors", []))
    counts = [c for c in (merged.get("cited_by"), b.get("cited_by")) if c is not None]
    merged["cited_by"] = max(counts) if counts else None
    merged["sources"] = list(dict.fromkeys(merged["sources"] + b.get("sources", [])))
    merged["ids"] = {**b.get("ids", {}), **merged["ids"]}
    merged["pub_types"] = list(dict.fromkeys(merged["pub_types"] + b.get("pub_types", [])))
    merged["retraction"] = merge_retraction(merged["retraction"], b.get("retraction"))
    return merged


def dedupe(works):
    """(unique works, number merged)"""
    unique, merged = [], 0
    for work in works:
        for i, other in enumerate(unique):
            if same_work(other, work):
                unique[i] = merge_works(other, work)
                merged += 1
                break
        else:
            unique.append(work)
    return unique, merged


# --- retraction status (RV15) -------------------------------------------------------------------------------------------------------

_ORDER = [RETRACTED, WITHDRAWN, CONCERN, CORRECTION, NONE, UNKNOWN]


def merge_retraction(a, b):
    """the strongest status wins (retracted before concern before correction before none before unknown); notices and hints are united"""
    a = a or {"status": UNKNOWN, "notices": [], "hints": []}
    b = b or {"status": UNKNOWN, "notices": [], "hints": []}
    notices = a["notices"] + [n for n in b["notices"] if n not in a["notices"]]
    hints = a["hints"] + [h for h in b["hints"] if h not in a["hints"]]
    status = min(a["status"], b["status"], key=lambda s: _ORDER.index(s) if s in _ORDER else len(_ORDER))
    return {"status": status, "notices": notices, "hints": hints}


def retraction_state(work, as_of=None):
    """{"status", "notices", "hints", "unconfirmed"} using only the notices dated up to as_of (None: all; a notice without a date counts). "none" means a source
    that gives the status itself (PubMed, Crossref's full record) found nothing; "unknown" that nobody was asked. A hint of one source (OpenAlex's flag, a title
    that begins with RETRACTED) without a notice is reported as unconfirmed, not as a fact."""
    info = work.get("retraction") or {"status": UNKNOWN, "notices": [], "hints": []}
    limit = as_date(as_of)
    notices = [n for n in info.get("notices", []) if limit is None or not n.get("date") or latest_day(n["date"]) <= limit]
    status = next((kind for kind in (RETRACTED, WITHDRAWN, CONCERN, CORRECTION) if any(n["type"] == kind for n in notices)), None)
    if status is None:
        status = NONE if (info.get("notices") or info.get("status") == NONE) else UNKNOWN
    hints = info.get("hints", [])
    return {"status": status, "notices": notices, "hints": hints, "unconfirmed": bool(hints) and status in (NONE, UNKNOWN)}


def retraction_from_crossref(message):
    """Crossref's work record: updated-by lists the notices (retraction, correction, expression of concern; source: Retraction Watch or the publisher)"""
    notices = []
    for entry in message.get("updated-by") or []:
        kind = str(entry.get("type", "")).lower()
        kind = {"retraction": RETRACTED, "withdrawal": WITHDRAWN, "expression_of_concern": CONCERN, "expression-of-concern": CONCERN,
                "correction": CORRECTION, "erratum": CORRECTION}.get(kind, kind)
        date = None
        parts = (entry.get("updated") or {}).get("date-parts")
        if parts and parts[0]:
            date = "-".join("%02d" % p if i else str(p) for i, p in enumerate(parts[0]))
        notices.append({"type": kind, "doi": clean_doi(entry.get("DOI")), "date": date, "source": entry.get("source") or "crossref", "label": entry.get("label")})
    hints = []
    titles = message.get("title") or []
    if titles and re.match(r"^\s*\W*(retracted|withdrawn)\b", titles[0], re.I):
        hints.append("title begins with %s" % titles[0].split(":")[0].strip().upper())
    status = RETRACTED if any(n["type"] == RETRACTED for n in notices) else (NONE if not notices and not hints else UNKNOWN)
    return {"status": status, "notices": notices, "hints": hints}


# --- HTTP with politeness, retry and cache (S1, S2) ------------------------------------------------------------------------------------

class ResponseCache:
    def __init__(self, folder, days=7, clock=time.time):
        self.folder, self.seconds, self._clock = folder, days * 86400, clock

    def _path(self, key):
        return os.path.join(self.folder, hashlib.sha256(key.encode("utf-8")).hexdigest()[:40] + ".json")

    def get(self, key):
        if not self.folder:
            return None
        try:
            with open(self._path(key), encoding="utf-8") as fp:
                entry = json.load(fp)
            if self._clock() - entry["at"] <= self.seconds:
                return entry["body"]
        except (OSError, ValueError, KeyError):
            pass
        return None

    def put(self, key, body):
        if not self.folder:
            return
        try:
            os.makedirs(self.folder, exist_ok=True)
            with open(self._path(key), "w", encoding="utf-8") as fp:
                json.dump({"at": self._clock(), "key": key, "body": body}, fp)
        except OSError:
            pass


class ApiHttp:
    """GET with a politeness interval per host, one retry after 429/503, a cache and the web log"""

    def __init__(self, session=None, log=None, cache=None, timeout=20, timeouts=None, min_intervals=None, sleep=time.sleep, clock=time.monotonic, max_wait=30, retries=1, email=None):
        self.session = session or requests.Session()
        self.log = log or WebLog(None)
        self.cache = cache
        self.timeout, self.timeouts = timeout, timeouts or {}
        self.min_intervals = min_intervals or {}
        self._sleep, self._clock, self.max_wait, self.retries = sleep, clock, max_wait, retries
        self._last = {}
        self.email = email
        self.requests_made = 0

    def _wait_turn(self, host):
        gap = self.min_intervals.get(host, 0.0)
        last = self._last.get(host)
        if gap and last is not None and self._clock() - last < gap:
            self._sleep(gap - (self._clock() - last))
        self._last[host] = self._clock()

    def get(self, url, params=None, headers=None):
        """the body as text; raises ScholarError"""
        full = url + ("?" + urlencode(params, quote_via=quote) if params else "")
        cached = self.cache.get(full) if self.cache else None
        if cached is not None:
            self.log.record("scholar", url=full, cached=True)
            return cached
        host = url.split("/")[2]
        head = {"User-Agent": USER_AGENT + (" (mailto:%s)" % self.email if self.email else ""), "Accept": "application/json, application/atom+xml, application/xml;q=0.9"}
        head.update(headers or {})
        started = time.time()
        for attempt in range(self.retries + 1):
            self._wait_turn(host)
            try:
                response = self.session.get(url, params=params, headers=head, timeout=self.timeouts.get(host, self.timeout))
            except requests.RequestException as exc:
                self.log.record("scholar", url=full, error=str(exc), ms=int((time.time() - started) * 1000))
                raise ScholarError("%s cannot be reached (%s)" % (host, exc))
            self.requests_made += 1
            if response.status_code in (429, 503) and attempt < self.retries:
                wait = min(_retry_after(response), self.max_wait)
                self.log.record("scholar", url=full, status=response.status_code, retry_in=wait)
                self._sleep(wait)
                continue
            break
        self.log.record("scholar", url=full, status=response.status_code, ms=int((time.time() - started) * 1000))
        if response.status_code == 429:
            raise ScholarError("%s is limiting requests (429): wait, or use an API key where the service offers one" % host)
        if response.status_code != 200:
            raise ScholarError("%s answered %d" % (host, response.status_code))
        body = response.text
        if self.cache:
            self.cache.put(full, body)
        return body


def _retry_after(response):
    try:
        return max(0.0, float((response.headers or {}).get("Retry-After", 2)))
    except (TypeError, ValueError):
        return 2.0


def _json(body, host):
    try:
        return json.loads(body)
    except ValueError:
        raise ScholarError("%s did not answer with JSON" % host)


def _xml(body, host):
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False, recover=False)
    try:
        return etree.fromstring(body.encode("utf-8") if isinstance(body, str) else body, parser)
    except etree.XMLSyntaxError as exc:
        raise ScholarError("%s did not answer with valid XML (%s)" % (host, exc))


def _text(node):
    return " ".join("".join(node.itertext()).split()) if node is not None else ""


# --- the sources ------------------------------------------------------------------------------------------------------------------------

def reconstruct_abstract(index):
    """OpenAlex gives abstracts as an inverted index {word: [positions]}"""
    if not index:
        return ""
    slots = {}
    for word, positions in index.items():
        for p in positions:
            slots[p] = word
    return " ".join(slots[p] for p in sorted(slots))


def parse_openalex(data):
    works = []
    for r in data.get("results", []):
        source = ((r.get("primary_location") or {}).get("source") or {})
        oa = r.get("open_access") or {}
        work = new_work("openalex", doi=r.get("doi"), title=r.get("title") or r.get("display_name") or "", abstract=reconstruct_abstract(r.get("abstract_inverted_index")),
                        date=r.get("publication_date"), year=r.get("publication_year"), venue=source.get("display_name") or "",
                        authors=[(a.get("author") or {}).get("display_name") for a in r.get("authorships", []) if (a.get("author") or {}).get("display_name")],
                        cited_by=r.get("cited_by_count"), work_type=r.get("type") or "", oa_url=oa.get("oa_url") or (r.get("primary_location") or {}).get("pdf_url"),
                        url=r.get("doi") or r.get("id"), ids={"openalex": str(r.get("id", "")).rsplit("/", 1)[-1] or None})
        if r.get("is_retracted") is True:
            work["retraction"] = {"status": UNKNOWN, "notices": [], "hints": ["OpenAlex flags it as retracted (the flag is not reliable, see RESEARCH_FINDINGS F12)"]}
        works.append(work)
    return works


def _crossref_date(item):
    for key in ("issued", "published", "published-print", "published-online", "created"):
        parts = ((item.get(key) or {}).get("date-parts") or [[None]])[0]
        if parts and parts[0]:
            return "-".join(("%d" if i == 0 else "%02d") % p for i, p in enumerate(parts))
    return None


def _strip_jats(text):
    return " ".join(re.sub(r"<[^>]+>", " ", text or "").split())


def parse_crossref(data):
    message = data.get("message", data)
    items = message.get("items") if "items" in message else [message]
    works = []
    for item in items:
        titles = item.get("title") or [""]
        authors = [" ".join(x for x in (a.get("given"), a.get("family")) if x) or a.get("name", "") for a in item.get("author", [])]
        work = new_work("crossref", doi=item.get("DOI"), title=titles[0], abstract=_strip_jats(item.get("abstract")), date=_crossref_date(item),
                        venue=(item.get("container-title") or [""])[0], authors=[a for a in authors if a], cited_by=item.get("is-referenced-by-count"),
                        work_type=item.get("type") or "", url=item.get("URL"))
        if "updated-by" in item:
            work["retraction"] = retraction_from_crossref(item)
        elif re.match(r"^\s*\W*(retracted|withdrawn)\b", titles[0], re.I):
            work["retraction"]["hints"].append("title begins with RETRACTED")
        works.append(work)
    return works


def _pubmed_date(article):
    pub = article.find(".//Article/Journal/JournalIssue/PubDate")
    if pub is None:
        return None
    year, month, day = (pub.findtext(t) for t in ("Year", "Month", "Day"))
    if year:
        return "-".join(x for x in (year, month, day) if x) if month else year
    medline = pub.findtext("MedlineDate") or ""
    match = re.match(r"(\d{4})", medline)
    return match.group(1) if match else None


def parse_pubmed(root):
    works = []
    for article in root.iter("PubmedArticle"):
        pmid = article.findtext(".//MedlineCitation/PMID")
        ids = {a.get("IdType"): "".join(a.itertext()).strip() for a in article.iterfind(".//PubmedData/ArticleIdList/ArticleId")}
        abstract = " ".join((("%s: " % t.get("Label")) if t.get("Label") else "") + _text(t) for t in article.iterfind(".//Article/Abstract/AbstractText"))
        authors = []
        for author in article.iterfind(".//Article/AuthorList/Author"):
            name = " ".join(x for x in (author.findtext("ForeName"), author.findtext("LastName")) if x) or author.findtext("CollectiveName") or ""
            if name:
                authors.append(name)
        pub_types = [_text(t) for t in article.iterfind(".//Article/PublicationTypeList/PublicationType")]
        work = new_work("pubmed", doi=ids.get("doi"), title=_text(article.find(".//Article/ArticleTitle")), abstract=abstract, date=_pubmed_date(article),
                        venue=_text(article.find(".//Article/Journal/Title")), authors=authors, work_type="journal-article", pub_types=pub_types,
                        url="https://pubmed.ncbi.nlm.nih.gov/%s/" % pmid if pmid else None, ids={"pmid": pmid, "pmc": ids.get("pmc")})
        notices, hints = [], []
        if "Retracted Publication" in pub_types:
            notices.append({"type": RETRACTED, "doi": None, "date": None, "source": "pubmed", "label": "Retracted Publication"})
        for comment in article.iterfind(".//MedlineCitation/CommentsCorrectionsList/CommentsCorrections"):
            kind = {"RetractionIn": RETRACTED, "ExpressionOfConcernIn": CONCERN, "ErratumIn": CORRECTION}.get(comment.get("RefType"))
            if kind:
                notices.append({"type": kind, "doi": None, "date": None, "source": "pubmed", "label": comment.get("RefType")})
        if notices:
            work["retraction"] = {"status": RETRACTED if any(n["type"] == RETRACTED for n in notices) else UNKNOWN, "notices": notices, "hints": hints}
        else:
            work["retraction"] = {"status": NONE, "notices": [], "hints": []}
        if "Preprint" in pub_types:
            work["work_type"] = "preprint"
        works.append(work)
    return works


ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def parse_arxiv(root):
    works = []
    for entry in root.iterfind("a:entry", ATOM):
        link = (entry.findtext("a:id", namespaces=ATOM) or "").strip()
        arxiv_id = re.sub(r"v\d+$", "", link.split("/abs/")[-1]) if "/abs/" in link else None
        pdf = next((l.get("href") for l in entry.iterfind("a:link", ATOM) if l.get("title") == "pdf"), None)
        comment = _text(entry.find("arxiv:comment", ATOM))
        summary = _text(entry.find("a:summary", ATOM))
        work = new_work("arxiv", doi=_text(entry.find("arxiv:doi", ATOM)) or None, title=_text(entry.find("a:title", ATOM)), abstract=summary,
                        date=(entry.findtext("a:published", namespaces=ATOM) or "")[:10] or None, venue=_text(entry.find("arxiv:journal_ref", ATOM)) or "arXiv",
                        authors=[_text(a.find("a:name", ATOM)) for a in entry.iterfind("a:author", ATOM)], work_type="preprint", oa_url=pdf, url=link or None,
                        ids={"arxiv": arxiv_id})
        if re.search(r"\bwithdrawn\b", comment + " " + summary[:200], re.I):
            work["retraction"] = {"status": UNKNOWN, "notices": [], "hints": ["arXiv comment or abstract says the paper was withdrawn"]}
        works.append(work)
    return works


def parse_semantic_scholar(data):
    works = []
    for p in data.get("data", []):
        ext = p.get("externalIds") or {}
        works.append(new_work("semanticscholar", doi=ext.get("DOI"), title=p.get("title") or "", abstract=p.get("abstract") or "", date=p.get("publicationDate"),
                              year=p.get("year"), venue=p.get("venue") or "", authors=[a.get("name") for a in p.get("authors", []) if a.get("name")],
                              cited_by=p.get("citationCount"), work_type=(p.get("publicationTypes") or [""])[0].lower() if p.get("publicationTypes") else "",
                              pub_types=p.get("publicationTypes") or [], oa_url=(p.get("openAccessPdf") or {}).get("url"),
                              url="https://www.semanticscholar.org/paper/%s" % p.get("paperId") if p.get("paperId") else None,
                              ids={"s2": p.get("paperId"), "pmid": ext.get("PubMed"), "arxiv": ext.get("ArXiv")}))
    return works


class OpenAlexClient:
    name = "openalex"
    SELECT = "id,doi,title,publication_date,publication_year,cited_by_count,type,is_retracted,primary_location,open_access,authorships,abstract_inverted_index"

    def __init__(self, http, email=None):
        self.http, self.email = http, email

    def search(self, query, limit=10, until=None, since=None):
        flt = []
        if until:
            flt.append("to_publication_date:%s" % as_date(until).isoformat())
        if since:
            flt.append("from_publication_date:%s" % as_date(since).isoformat())
        params = {"search": query, "per-page": min(max(limit, 1), 50), "select": self.SELECT}
        if flt:
            params["filter"] = ",".join(flt)
        if self.email:
            params["mailto"] = self.email
        return parse_openalex(_json(self.http.get(OPENALEX, params), "api.openalex.org"))[:limit]


class CrossrefClient:
    name = "crossref"
    SELECT = "DOI,title,issued,published,container-title,is-referenced-by-count,type,abstract,author,URL,updated-by"

    def __init__(self, http, email=None):
        self.http, self.email = http, email

    def search(self, query, limit=10, until=None, since=None):
        flt = []
        if until:
            flt.append("until-pub-date:%s" % as_date(until).isoformat())
        if since:
            flt.append("from-pub-date:%s" % as_date(since).isoformat())
        params = {"query": query, "rows": min(max(limit, 1), 50), "select": self.SELECT}
        if flt:
            params["filter"] = ",".join(flt)
        if self.email:
            params["mailto"] = self.email
        return parse_crossref(_json(self.http.get(CROSSREF, params), "api.crossref.org"))[:limit]

    def lookup(self, doi):
        """the full record of one DOI (with the notices that update it); None if Crossref does not know it"""
        try:
            body = self.http.get("%s/%s" % (CROSSREF, quote(clean_doi(doi), safe="/()")), {"mailto": self.email} if self.email else None)
        except ScholarError as exc:
            if "answered 404" in str(exc):
                return None
            raise
        works = parse_crossref(_json(body, "api.crossref.org"))
        if not works:
            return None
        record = works[0]
        if record["retraction"]["status"] == UNKNOWN and not record["retraction"]["notices"] and not record["retraction"]["hints"]:
            record["retraction"]["status"] = NONE            # the full record lists every notice Crossref knows; none listed
        return record


class PubMedClient:
    name = "pubmed"

    def __init__(self, http, email=None, api_key=None):
        self.http, self.email, self.api_key = http, email, api_key

    def _common(self):
        extra = {"tool": "MIA-research"}
        if self.email:
            extra["email"] = self.email
        if self.api_key:
            extra["api_key"] = self.api_key
        return extra

    def search(self, query, limit=10, until=None, since=None):
        params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": min(max(limit, 1), 50), "sort": "relevance", **self._common()}
        if until or since:
            params.update({"datetype": "pdat", "mindate": (as_date(since) or datetime.date(1000, 1, 1)).strftime("%Y/%m/%d"),
                           "maxdate": (as_date(until) or datetime.date.today()).strftime("%Y/%m/%d")})
        ids = _json(self.http.get(PUBMED_SEARCH, params), "eutils.ncbi.nlm.nih.gov").get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        body = self.http.get(PUBMED_FETCH, {"db": "pubmed", "id": ",".join(ids), "retmode": "xml", **self._common()})
        return parse_pubmed(_xml(body, "eutils.ncbi.nlm.nih.gov"))[:limit]


class ArxivClient:
    name = "arxiv"

    def __init__(self, http):
        self.http = http

    def search(self, query, limit=10, until=None, since=None):
        words = [w for w in re.findall(r"[\w'-]+", query) if len(w) > 2][:8]
        text = " AND ".join("all:%s" % w for w in words) or "all:%s" % query.strip()
        if until or since:
            low = (as_date(since) or datetime.date(1991, 1, 1)).strftime("%Y%m%d") + "0000"
            high = (as_date(until) or datetime.date.today()).strftime("%Y%m%d") + "2359"
            text += " AND submittedDate:[%s TO %s]" % (low, high)
        body = self.http.get(ARXIV, {"search_query": text, "max_results": min(max(limit, 1), 50), "sortBy": "relevance"})
        return parse_arxiv(_xml(body, "export.arxiv.org"))[:limit]


class SemanticScholarClient:
    name = "semanticscholar"
    FIELDS = "title,abstract,year,venue,citationCount,externalIds,openAccessPdf,publicationDate,publicationTypes,authors"

    def __init__(self, http, api_key=None):
        self.http, self.api_key = http, api_key

    def search(self, query, limit=10, until=None, since=None):
        params = {"query": query, "limit": min(max(limit, 1), 100), "fields": self.FIELDS}
        if until or since:
            params["publicationDateOrYear"] = "%s:%s" % ((as_date(since).isoformat() if since else ""), (as_date(until).isoformat() if until else ""))
        headers = {"x-api-key": self.api_key} if self.api_key else None
        return parse_semantic_scholar(_json(self.http.get(SEMANTIC_SCHOLAR, params, headers), "api.semanticscholar.org"))[:limit]


# --- all together -----------------------------------------------------------------------------------------------------------------------

class Scholar:
    def __init__(self, clients, crossref=None, max_per_source=10):
        self.clients = list(clients)
        self.crossref = crossref or next((c for c in self.clients if isinstance(c, CrossrefClient)), None)
        self.max_per_source = max_per_source

    def search(self, query, limit=None, until=None, since=None, check_retraction=False):
        """{"works": [...], "errors": {source: message}, "counts": {source: n}, "dropped": [{"ref", "title", "reason"}], "merged": n}"""
        limit = limit or self.max_per_source
        found, errors, counts = [], {}, {}
        for client in self.clients:
            try:
                works = client.search(query, limit=limit, until=until, since=since)
            except WebError as exc:
                errors[client.name] = str(exc)
                continue
            counts[client.name] = len(works)
            found.extend(works)
        kept, dropped = [], []
        for work in found:
            ok, reason = within(work, until, since)
            (kept if ok else dropped).append(work if ok else {"ref": reference_of(work), "title": work["title"], "reason": reason})
        unique, merged = dedupe(kept)
        if check_retraction:
            for work in unique:
                self.verify_retraction(work, errors)
        return {"works": unique, "errors": errors, "counts": counts, "dropped": dropped, "merged": merged}

    def verify_retraction(self, work, errors=None):
        """ask Crossref for the notices of the DOI and merge them into the record (a record from a source that gives the status itself, PubMed, is merged too)"""
        if not self.crossref or not work.get("doi"):
            return work
        try:
            record = self.crossref.lookup(work["doi"])
        except WebError as exc:
            if errors is not None:
                errors["crossref-retraction"] = str(exc)
            return work
        if record is not None:
            work["retraction"] = merge_retraction(work["retraction"], record["retraction"])
            if "crossref" not in work["sources"]:
                work["sources"].append("crossref")
        return work


def build_scholar(cfg, runs_dir=None, session=None, sleep=time.sleep, clock=time.monotonic):
    """the Scholar of the configuration: scholar_backends, scholar_email (empty: none is sent), semantic_scholar_key, scholar_cache_dir, scholar_cache_days"""
    cfg = cfg or {}
    email = cfg.get("scholar_email") or None
    cache_dir = cfg.get("scholar_cache_dir")
    if cache_dir and not os.path.isabs(cache_dir):
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), cache_dir)
    http = ApiHttp(session=session, log=WebLog(runs_dir), cache=ResponseCache(cache_dir, cfg.get("scholar_cache_days", 7)) if cache_dir else None,
                   timeouts={"export.arxiv.org": 45}, min_intervals={"api.openalex.org": 0.2, "api.crossref.org": 0.3, "eutils.ncbi.nlm.nih.gov": 0.4, "export.arxiv.org": 3.0, "api.semanticscholar.org": 1.1},
                   sleep=sleep, clock=clock, email=email)
    names = [n for n in cfg.get("scholar_backends", DEFAULT_BACKENDS) if n in BACKENDS]
    clients = []
    for name in names:
        if name == "openalex":
            clients.append(OpenAlexClient(http, email))
        elif name == "crossref":
            clients.append(CrossrefClient(http, email))
        elif name == "pubmed":
            clients.append(PubMedClient(http, email))
        elif name == "arxiv":
            clients.append(ArxivClient(http))
        elif name == "semanticscholar":
            clients.append(SemanticScholarClient(http, cfg.get("semantic_scholar_key") or None))
    crossref = next((c for c in clients if isinstance(c, CrossrefClient)), None) or CrossrefClient(http, email)
    return Scholar(clients, crossref=crossref, max_per_source=cfg.get("scholar_results", 10)), http
