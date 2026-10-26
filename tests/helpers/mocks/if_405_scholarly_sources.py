"""Mock of IF-405, scholarly sources (protected). Complexity 3: scripted works, the strict date cut-off, a failing source.
It does not reproduce the five real APIs or the file cache."""
import calendar

WORKS = [
    {"doi": "10.1/a", "title": "Exact day", "date": "2001-11-22", "sources": ["openalex"]},
    {"doi": "10.1/b", "title": "Month only", "date": "2001-11", "sources": ["crossref"]},
    {"doi": "10.1/c", "title": "Year only", "date": "2001", "sources": ["openalex"]},
    {"doi": "10.1/d", "title": "No date", "date": None, "sources": ["pubmed"]},
    {"doi": "10.1/a", "title": "Exact day", "date": "2001-11-22", "sources": ["crossref"]},       # the same work from a second source
]


def latest_day(date):
    """The latest day a date could mean: '2001' -> 2001-12-31, '2001-11' -> 2001-11-30."""
    parts = [int(p) for p in date.split("-")]
    if len(parts) == 1:
        return "%04d-12-31" % parts[0]
    if len(parts) == 2:
        return "%04d-%02d-%02d" % (parts[0], parts[1], calendar.monthrange(parts[0], parts[1])[1])
    return "%04d-%02d-%02d" % tuple(parts)


class ScholarMock:
    def __init__(self, works=None, failing=()):
        self.works = works if works is not None else WORKS
        self.failing = set(failing)

    def search(self, query, until=None, since=None):
        errors = [{"source": s, "message": "rate limited"} for s in sorted(self.failing)]
        merged, dropped = {}, []
        for work in self.works:
            sources = [s for s in work.get("sources", []) if s not in self.failing]
            if not sources:
                continue
            if work["doi"] in merged:
                merged[work["doi"]]["sources"] = sorted(set(merged[work["doi"]]["sources"]) | set(sources))
                continue
            merged[work["doi"]] = dict(work, sources=sorted(sources))
        works = []
        for work in merged.values():
            if until or since:
                if not work.get("date"):
                    dropped.append({"ref": work["doi"], "reason": "no_date"})
                    continue
                if until and latest_day(work["date"]) > until:
                    dropped.append({"ref": work["doi"], "reason": "after_cutoff"})
                    continue
                if since and latest_day(work["date"]) < since:
                    dropped.append({"ref": work["doi"], "reason": "before_since"})
                    continue
            works.append(work)
        return {"works": works, "errors": errors, "dropped": dropped}
