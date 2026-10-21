"""
The source trust table (ui/REQUIREMENTS_RESEARCH.md RV14, RV15): how much we trust a kind of source before reading it.

  T1  the numbers are our judgement, shown as such with their reason and the date they were set; they are a prior, never a proof (the quote check of extraction decides
      what a source really says)
  T2  the table is data: library/source_trust.json is the default, the file of the option source_trust_file (default data/source_trust.json) overrides it entry by entry
  T3  a retracted or withdrawn work is not usable (score 0); an expression of concern lowers the score; a correction is a flag; an unconfirmed hint (OpenAlex's flag,
      a title that begins with RETRACTED) is a flag that asks for a check, not a verdict
  T4  citation counts are not part of the prior (they come with the weights of a finding later, and they are as of today, see scholar.use_as_of)
  T5  a record that is only a notice about another work (a retraction notice, an erratum) is not usable as evidence
"""
import json
import os
import re
from urllib.parse import urlparse

from scholar import CONCERN, CORRECTION, RETRACTED, WITHDRAWN, forms, retraction_state

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILE = os.path.join(HERE, "library", "source_trust.json")

JOURNAL_TYPES = {"journal-article", "article", "journal", "journal-issue", "review", "letter", "editorial"}
CONFERENCE_TYPES = {"proceedings-article", "conference-paper", "proceedings", "conference"}
PREPRINT_TYPES = {"posted-content", "preprint", "repository"}
BOOK_TYPES = {"book", "book-chapter", "monograph", "edited-book", "reference-book", "book-section", "book-part"}
THESIS_TYPES = {"dissertation", "thesis"}
REPORT_TYPES = {"report", "report-series", "report-component", "standard", "dataset"}


def _read(path):
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)


def is_notice(work):
    """a retraction notice, withdrawal or erratum is a record about another work: PubMed marks them, Crossref titles begin with the kind"""
    types = {t.lower() for t in work.get("pub_types", [])}
    if types & {"retraction of publication", "published erratum", "expression of concern"}:
        return True
    return bool(re.match(r"^\s*(retraction|withdrawal|expression of concern|erratum|correction)\b\s*[-:\u2013\u2014]", str(work.get("title", "")), re.I))


class TrustTable:
    def __init__(self, data):
        self.data = data
        self.classes = data.get("classes", {})
        self.domains = data.get("domains", {})
        self.suffixes = data.get("suffixes", {})
        self.venues = {}
        for name, entry in data.get("venues", {}).items():
            for form in forms(name):
                self.venues[form] = (name, entry)

    @classmethod
    def load(cls, default_path=DEFAULT_FILE, user_path=None):
        data = _read(default_path)
        if user_path and os.path.exists(user_path):
            try:
                user = _read(user_path)
            except (OSError, ValueError):
                user = {}
            for section in ("classes", "domains", "suffixes", "venues"):
                data.setdefault(section, {}).update(user.get(section, {}))
        return cls(data)

    def prior(self, kind):
        entry = self.classes.get(kind) or self.classes.get("unknown") or {"prior": 0.3, "reason": "no table"}
        return float(entry["prior"]), entry.get("reason", "")

    def classify(self, work):
        """the class of a scholarly record: its type, then the signs a type does not give (a preprint server, a PubMed publication type)"""
        kind = str(work.get("work_type") or "").lower()
        types = {t.lower() for t in work.get("pub_types", [])}
        venue = str(work.get("venue") or "")
        if "preprint" in types or kind in PREPRINT_TYPES or work.get("sources") == ["arxiv"] or venue.lower() in ("arxiv", "biorxiv", "medrxiv", "ssrn"):
            return "preprint"
        if kind in CONFERENCE_TYPES:
            return "conference"
        if kind in BOOK_TYPES:
            return "book"
        if kind in THESIS_TYPES:
            return "thesis"
        if kind in REPORT_TYPES:
            return "report"
        if kind in JOURNAL_TYPES or "journal article" in types:
            return "journal"
        return "unknown"

    def for_work(self, work, as_of=None):
        """{"class", "score", "usable", "flags", "reason"} for a scholarly record"""
        kind = self.classify(work)
        score, reason = self.prior(kind)
        reasons = ["%s: %s" % (kind, reason)]
        venue = None
        for form in forms(work.get("venue", "")):
            if form in self.venues:
                venue = self.venues[form]
                break
        if venue:
            score += float(venue[1].get("adjust", 0.0))
            reasons.append("venue %s: %s" % (venue[0], venue[1].get("reason", "")))
        state = retraction_state(work, as_of)
        flags, usable = [], True
        if state["status"] in (RETRACTED, WITHDRAWN):
            score, usable = 0.0, False
            flags.append(state["status"])
        elif state["status"] == CONCERN:
            score -= 0.2
            flags.append("expression of concern")
        elif state["status"] == CORRECTION:
            flags.append("has a correction")
        if is_notice(work):
            usable = False
            flags.append("is a notice about another work, not evidence itself")
        if state["unconfirmed"]:
            flags.append("unconfirmed retraction hint: " + "; ".join(state["hints"]))
        return {"class": kind, "score": round(max(0.0, min(1.0, score)), 3), "usable": usable, "flags": flags, "reason": "; ".join(reasons)}

    def for_url(self, url):
        """a web page: the entry of its domain (the longest matching one), else of its suffix, else unknown"""
        host = (urlparse(url).hostname or "").lower().rstrip(".")
        best = None
        for domain, entry in self.domains.items():
            if host == domain or host.endswith("." + domain):
                if best is None or len(domain) > len(best[0]):
                    best = (domain, entry)
        if best is None:
            for suffix, entry in self.suffixes.items():
                if host.endswith(suffix) and (best is None or len(suffix) > len(best[0])):
                    best = (suffix, entry)
        kind = best[1]["class"] if best else "unknown"
        score, reason = self.prior(kind)
        return {"class": kind, "score": round(score, 3), "usable": True, "flags": [], "matched": best[0] if best else None,
                "reason": "%s: %s%s" % (kind, reason, (" (%s)" % best[1].get("reason", "")) if best else "")}


def build_trust(cfg):
    path = (cfg or {}).get("source_trust_file")
    if path and not os.path.isabs(path):
        path = os.path.join(HERE, path)
    return TrustTable.load(DEFAULT_FILE, path)
