"""
The model steps of the review workflow (A-18, REQ-WFM-028) as the functions ReviewRun wants. run_skill(name, inputs) runs a skill and gives its answer (a mapping), as in
memory_records.memory_hooks; nothing here talks to a model itself. The skills are review_keywords, review_abstract, review_section and review_full.

  M1  a section is cut to max_chars (about half of the context, RV2) and at most max_sections sections are read; the rest of the text is not sent to a model
  M2  the answers are returned as they are: values and quotes are checked by review_stages (check_judgement, check_full), not here
"""

CODES = ("off_topic", "outdated", "wrong_type", "language")


def criteria_text(criteria):
    return "\n".join("- %s: %s" % (c["code"], c["text"]) for c in criteria)


def plan_keywords(run_skill, question):
    """-> ({concept: [keyword]}, [{"code", "text"}]) from the skill review_keywords; criteria with a code outside CODES are dropped"""
    answer = run_skill("review_keywords", {"question": question})
    concepts = {c["name"]: list(c["keywords"]) for c in answer.get("concepts", [])}
    return concepts, [c for c in answer.get("criteria", []) if c.get("code") in CODES]


def make_screeners(run_skill, question, criteria, max_chars=6000, max_sections=12):
    """-> (screen_abstract(work), screen_full(work, text)) for ReviewRun"""
    listed = criteria_text(criteria)

    def screen_abstract(work):
        return run_skill("review_abstract", {"question": question, "criteria": listed, "title": work.get("title") or "", "date": work.get("date") or str(work.get("year") or ""),
                                              "abstract": work.get("abstract") or ""})

    def screen_full(work, text):
        sections, notes = [], []
        for part in text.get("sections", [])[:max_sections]:
            answer = run_skill("review_section", {"question": question, "section": part.get("name", ""), "text": part.get("text", "")[:max_chars]})
            sections.append(answer)
            notes.append("%s: grade %s, %s" % (part.get("name", ""), answer.get("grade"), answer.get("statement", "")))
        final = run_skill("review_full", {"question": question, "criteria": listed, "abstract_statement": work.get("abstract_statement", ""),
                                          "section_notes": "\n".join(notes) or "(no sections)", "conclusion": text.get("conclusion", "")[:max_chars]})
        return {**final, "sections": sections}

    return screen_abstract, screen_full
