"""
The library entry of the review workflow (REQ-WFM-018, A-18, A-20): a draft record in the workflow library that says which stages the review has and what runs each of them. The
entry describes the process (data and process nodes, no cycle: the keyword extension that feeds a new round is named in its note); what runs is review_chat.run_review. It stays a draft
until its specification and benchmark are attached (the gate of the library, REQ-WFM-006).
"""
REVIEW_ID = "review"

STAGES = (
    ("question", "data", "the research question, optionally with a cut-off (/review question until DATE)"),
    ("keywords", "process", "skill review_keywords@2: concepts, keywords and the written criteria; the user may replace the keywords (review_chat.keywords_prompt)"),
    ("keyword_set", "data", "the keywords the user agreed to"),
    ("search", "process", "scholar.Scholar.search once per keyword (OpenAlex, Crossref, PubMed, arXiv), cut-off and retraction check"),
    ("records", "data", "the records found, per keyword"),
    ("collect", "process", "review_stages.collect: de-duplicate, keywords per work, drop what is after the cut-off or retracted and say why"),
    ("works", "data", "the collected works and the drop list"),
    ("abstract_screening", "process", "skill review_abstract@1 per work: relevance grade 0 to 3 and eligibility include/maybe/exclude with a reason code, quote checked by code"),
    ("abstract_judgements", "data", "two judgements per work"),
    ("checkpoint", "process", "the user decides whether the full texts are read (review_chat.checkpoint_prompt, REQ-WFM-019); also asked when a limit is used up"),
    ("approved", "data", "the works whose full text may be read"),
    ("full_text_screening", "process", "fulltext.FullTextSource (open access only, PDF inside the wall), skills review_section@1 per section and review_full@2 for the decision"),
    ("full_judgements", "data", "section grades, fit with the conclusion, final eligibility"),
    ("keyword_extension", "process", "review_stages.propose_terms: terms in at least 3 screened works are proposed; only approved terms are searched, in a new round of search to full text screening (REQ-WFM-027)"),
    ("extended_keywords", "data", "the approved new keywords"),
    ("summary", "process", "skill review_summary@1: what was found, coverage, gaps; figures and level by code, cited works checked by code; a person has to check it"),
    ("report", "data", "the report: keywords and queries, flow count, notes per work, dropped works, summary (review_chat.format_report)"),
)


def review_workflow():
    nodes = [{"id": i, "kind": kind, "note": note} for i, kind, note in STAGES]
    edges = [{"from": a[0], "to": b[0]} for a, b in zip(STAGES, STAGES[1:])]
    return {"nodes": nodes, "edges": edges, "implemented_by": "review_chat.run_review", "title": "Literature review"}


def ensure_review_workflow(library, author="library"):
    """saves the draft once; True if it was saved now"""
    if REVIEW_ID in library.list_ids("workflows"):
        return False
    library.save("workflows", REVIEW_ID, review_workflow(), author)
    return True
