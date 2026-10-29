"""Builds eval/suites/review/ (draft): four real reference cases from published reviews. Quotes are checked verbatim against the text of the review; labels are drafts (confirmed: false)."""
import json
import os
import re
import sys
import unicodedata

REPO = "/home/maldun/prog/Python/MIA/.claude/worktrees/chat-c1"
sys.path.insert(0, REPO)
from extensions.review import review_case as RC                                      # noqa: E402
import scholar                                                # noqa: E402

TMP = "/home/maldun/.claude/jobs/e483ef54/tmp/"
P = TMP + "papers/"
OUT = REPO + "/eval/suites/review/"


def norm(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"-\s*\n\s*(?=[a-z])", "", text)                  # hyphenation at a line end
    return re.sub(r"\s+", " ", text)


def read(name):
    return open(P + "review_%s.txt" % name, encoding="utf-8").read()


def questions(text, items, source):
    body = norm(text)
    out = []
    for n, (question, answer, quote) in enumerate(items, 1):
        q = norm(quote)
        assert q in body, "quote not found: %r" % quote
        out.append({"id": "q%d" % n, "question": question, "answer": answer, "evidence": [{"source": source, "quote": q}], "confirmed": False})
    return out


cfg = {"scholar_backends": ["openalex", "crossref"], "scholar_cache_dir": TMP + "scholar_cache"}
sch, http = scholar.build_scholar(cfg)
clients = [c for c in sch.clients if c.name in ("openalex", "crossref")]


def resolve_refs(refs, review_year, label):
    """resolved entries: the DOI printed in the reference list is taken as it is; the rest is searched (R1); a match later than the review is refused (another edition)"""
    included, later = [], []
    for n, ref in enumerate(refs, 1):
        entry = {"id": ref["key"], "title": ref["title"], "authors": ref["authors"]}
        if ref.get("doi"):
            item = dict(entry, resolved=True, doi=ref["doi"], year=ref.get("year"), matched_title=ref["title"], matched_by="reference list")
        else:
            item = RC.resolve(entry, clients)
            if item["resolved"] and item.get("year") and item["year"] > review_year:
                later.append(item["title"])
                item = dict(entry, resolved=False, year=ref.get("year"))
            elif not item["resolved"]:
                item["year"] = ref.get("year")
        print("%s %3d/%d %-4s %s" % (label, n, len(refs), "ok" if item["resolved"] else "NO", ref["title"][:60]), flush=True)
        included.append(item)
    return included, later


def case(case_id, tags, question, until, key_terms, review, included, qs, note):
    c = RC.draft_case(case_id, tags, question, until, key_terms, included, qs, review, notes=note)
    return c


cases = []

# 1. DevOps: Rütz, search April 2019, paper August 2019
text = read("devops")
included = json.load(open(TMP + "ruetz_included.json", encoding="utf-8"))
src = "Rütz 2019, DevOps: A systematic literature review"
qs = questions(text, [
    ("Does the literature concentrate on tools, practices and the lack of standards rather than on what DevOps is?", "supports", "the literature concentrates on tools, practices and the lack of standards"),
    ("Does the literature provide an adequate framework or process to adapt DevOps to an existing IT environment in enterprises?", "does_not_support", "the literature doesn’t provide an adequate framework or process to adapt DevOps to an existing IT environment in enterprises"),
    ("Is there a homogeneous definition of DevOps in the literature?", "does_not_support", "there isn’t a homogeneous definition in the literature"),
    ("Is there a unique standard or framework for DevOps?", "does_not_support", "DevOps constitute a general approach for software development without a unique standard or framework"),
    ("Are cloud computing and artificial intelligence in combination with DevOps described in detail?", "does_not_support", "cloud computing and artificial intelligence in combination with DevOps are not described in a detailed way"),
    ("Does the literature give recommendations on how to deal with the different views of development and operation teams?", "does_not_support", "The literature doesn’t provide recommendations or a model how to deal with the different views of development and operation teams"),
    ("Is the number of publications on DevOps increasing?", "supports", "The increasing number of publications underlines the importance of DevOps"),
    ("Do nearly all definitions of DevOps have the connection of development and operations teams in common?", "supports", "nearly all definitions have the connection aspect of both teams in common"),
], src)
cases.append(case("devops-ruetz-2019", ["devops", "real", "systematic_review"], "What does the literature say about DevOps: definition, enablers, challenges and open questions?", "2019-04-30", ["DevOps"],
                  {"title": "DevOps: A systematic literature review", "authors": "Martin Rütz", "published": "2019-08", "search_date": "2019-04", "kind": "systematic review (seminar paper)"},
                  [i for i in included], qs, "Rütz, Fachhochschule Wedel, August 2019. Search in April 2019 (string DevOps, IEEE Xplore, ACM, EBSCO), 58 selected works of Table 2. The cut-off is the search date, not the date of the paper."))

# 2. Applied mathematics: Argoul, lecture notes dated 27 July 2012
text = read("argoul")
refs = RC.parse_references(text[text.rindex("\nBibliography\n"):])
body = text[text.index("Introduction - Definitions\nThe term"):text.rindex("\nBibliography\n")]
cited = RC.cited_keys(body, {r["key"] for r in refs})
used = [r for r in refs if r["key"] in cited]
print("argoul: refs", len(refs), "cited", len(used))
inc, later = resolve_refs(used, 2012, "argoul")
src = "Argoul 2012, Overview of Inverse Problems"
qs = questions(text, [
    ("Is there a standard approach to inverse problems?", "does_not_support", "there exists no “standard”approach to inverse problems"),
    ("Are inverse problems characteristically ill posed in the sense of Hadamard?", "supports", "One characteristic of inverse problems is being ill posed or incorrectly posed, in the sense of Hadamard"),
    ("Is Tikhonov regularization the most well-known regularization method?", "supports", "Tikhonov’s regularization (the most well-known method"),
    ("Did the work of Backus and Gilbert constitute the first systematic exploration of the mathematical structure of inverse problems?", "supports", "constitutes the first systematic exploration of the mathematical structure of inverse problems"),
    ("Is the direct problem usually simpler to solve than the inverse problem?", "supports", "is often simpler and more easily mastered than that of an inverse problem"),
    ("Can classical methods always find a global optimum in the absence of regularity hypotheses?", "does_not_support", "In the absence of regularity hypotheses, it becomes difficult to find via classical methods a global optimum"),
    ("Can the methods for inverse problems be classified into functional analysis, regularization of ill-posed problems and stochastic or Bayesian inversion?", "supports", "the methods of investigating inverse problems can be classified into three main categories"),
], src)
cases.append(case("inverse-argoul-2012", ["applied_mathematics", "real", "lecture_notes", "tier1"], "What are inverse problems and which approaches exist to solve them?", "2012-07-27",
                  ["inverse problem", "ill-posed", "regularization"],
                  {"title": "Overview of Inverse Problems", "authors": "Pierre Argoul", "published": "2012-07-27", "kind": "lecture notes (narrative overview, 9 pages)"},
                  inc, qs, "Lecture notes, Ecole Nationale des Ponts et Chaussées, dated 27 July 2012 (HAL cel-00781172). Not a systematic review: the included works are the references cited in the text. Matches later than 2012 were refused: %d." % len(later)))

# 3. Applied mathematics: Nayak, overview chapters 1 to 5 of the dissertation
text = read("nayak")
refs = RC.parse_references(text[text.rindex("\nLIST OF REFERENCES\n"):])
chapters = text[text.index("CHAPTER 1\n\nIntroduction"):text.index("CHAPTER 6\n\nThe Inverse Problem of Numerical Differentiation")]
cited = RC.cited_keys(chapters, {r["key"] for r in refs})
used = [r for r in refs if r["key"] in cited]
print("nayak: refs", len(refs), "cited in chapters 1-5", len(used))
inc, later = resolve_refs(used, 2019, "nayak")
src = "Nayak 2019, Inverse Problems, Regularization and Its Applications, chapters 1 to 5"
qs = questions(chapters, [
    ("Is the choice of the regularization parameter a non-trivial task?", "supports", "to compute an optimum value of the regularization parameter and this is not a trivial task"),
    ("Does the simple Landweber iteration converge arbitrarily slowly?", "supports", "this simpler iterative method comes at the cost of (arbitrarily) slow convergence rate"),
    ("Is numerical differentiation an ill-posed problem?", "supports", "(numerical) differentiation is an ill-posed problem"),
    ("Are the vast majority of inverse problems ill-posed?", "supports", "A common property of a vast majority of inverse problems is their ill-posedness"),
    ("Is some information lost in numerical differentiation even for the optimal step size?", "supports", "there is an intrinsic loss of information that cannot be retrieved"),
    ("Was it realized only in the second half of the last century that a huge number of problems in science and technology are ill-posed?", "supports", "Only in the second half of the last century it was realized that a huge number of problems arising in science and technology are ill-posed"),
], src)
cases.append(case("inverse-nayak-overview-2019", ["applied_mathematics", "real", "thesis_overview", "tier1"], "What are inverse problems, why are they ill-posed, and how are they regularized?", "2019-12-31",
                  ["inverse problem", "ill-posed", "regularization", "Tikhonov", "Landweber"],
                  {"title": "Inverse Problems, Regularization and Its Applications (chapters 1 to 5: overview)", "authors": "Abinash Nayak", "published": "2019", "kind": "overview chapters of a PhD dissertation (UAB)"},
                  inc, qs, "Only the overview chapters 1 to 5 are the reference; the new method of the later chapters is not part of the case. Included works: references cited in chapters 1 to 5. Matches later than 2019 were refused: %d." % len(later)))

# 4. Co-simulation: Gomes et al., ACM Computing Surveys, May 2018
text = read("gomes")
refs = RC.parse_references(text[text.rindex("\nREFERENCES\n"):])
print("gomes: refs", len(refs))
inc, later = resolve_refs(refs, 2018, "gomes")
src = "Gomes et al. 2018, Co-Simulation: A Survey"
qs = questions(text, [
    ("Is there research on approaches that are both discrete-event and continuous-time based and that use the extra features of the simulation units?", "does_not_support", "there is a lack of research into approaches that are both DE and CT based, and that leverage the extra features from the SUs"),
    ("Is there research on modular, stable and accurate coupling of simulators in dynamic structure scenarios?", "does_not_support", "there is lack of research into modular, stable, and accurate coupling of simulators in dynamic structure scenarios"),
    ("Do the large majority of reported co-simulation applications couple just two simulators of two different domains in an ad-hoc way?", "supports", "the large majority of these applications represent ad-hoc couplings between two simulators of two different domains"),
    ("Do many discrete-event and continuous-time based approaches support IP protection?", "does_not_support", "the number of DE- and CT-based approaches that provide some support for it is small"),
    ("Is there only one approach that is both continuous-time and discrete-event based for any number of simulation units?", "supports", "there is only one approach [108] that is both CT and DE based, up to any number of SUs"),
    ("Is semantic adaptation one of the challenges of co-simulation?", "supports", "we highlight semantic adaptation, modular coupling, stability and accuracy, and finding a standard for hybrid co-simulation"),
], src)
cases.append(case("cosim-gomes-2018", ["co_simulation", "real", "survey", "tier2"], "What are the state of the art techniques, tools and open challenges of co-simulation?", "2018-05-31",
                  ["co-simulation", "cosimulation", "coupled simulation"],
                  {"title": "Co-Simulation: A Survey", "authors": "Cláudio Gomes, Casper Thule, David Broman, Peter Gorm Larsen, Hans Vangheluwe", "published": "2018-05", "kind": "survey with a taxonomy and a classification of 84 papers from 2011 to 2016 (ACM Computing Surveys 51(3))"},
                  inc, qs, "Included works: the whole reference list (158 entries, 95 with the DOI printed in the list); the 84 classified papers are not marked in the list. Matches later than 2018 were refused: %d." % len(later)))

os.makedirs(OUT, exist_ok=True)
with open(REPO + "/tools/review_suite.json", encoding="utf-8") as src_fp, open(OUT + "suite.json", "w", encoding="utf-8") as dst_fp:
    dst_fp.write(src_fp.read())                                                                    # the suite exists only together with its cases
with open(OUT + "cases.jsonl", "w", encoding="utf-8") as fp:
    for c in cases:
        fp.write(json.dumps(c, ensure_ascii=False) + "\n")
for c in cases:
    inc = c["gold"]["included"]
    print(c["id"], "included", len(inc), "with doi", sum(1 for i in inc if i.get("doi")), "questions", len(c["gold"]["questions"]))
print("requests:", http.requests_made)
