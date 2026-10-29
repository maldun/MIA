"""
The LaTeX file of a review report (REQ-WFM-038), made by code from the report record, English headings. Every screened work is in it with its decision, grade and reason, not only the
works the chat message shows. No LaTeX run, no package beyond the standard article class (the user compiles it where LaTeX is installed).
"""
_SPECIAL = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "#": r"\#", "$": r"\$", "%": r"\%", "&": r"\&", "_": r"\_"}


def tex_escape(text):
    return "".join(_SPECIAL.get(ch, ch) for ch in str(text))


def _items(lines):
    return ["\\begin{itemize}"] + ["\\item " + line for line in lines] + ["\\end{itemize}"] if lines else []


def _work_line(w):
    label = "\\textbf{%s} (%s, relevance %d%s%s)" % (tex_escape(w["title"]), tex_escape(w["doi"] or "no DOI"), w["grade"], ", abstract only" if w["abstract_only"] else "",
                                                    ", reason: " + tex_escape(w["reason"]) if w.get("reason") else "")
    return label + (": " + tex_escape(" ".join(w["notes"])) if w.get("notes") else "")


def report_tex(report, question, until):
    flow = report["flow"]
    out = ["\\documentclass{article}", "\\usepackage[utf8]{inputenc}", "\\usepackage[T1]{fontenc}", "\\begin{document}", "",
           "\\section*{Literature review}", "\\textbf{Question:} %s\\\\" % tex_escape(question), "\\textbf{Cut-off:} %s \\quad \\textbf{Ended by:} %s" % (tex_escape(until), tex_escape(report["ended_by"]))]
    summary = report.get("summary")
    if summary:
        out += ["", "\\section*{Summary (a draft: a person has to check it against the sources)}",
                "\\textbf{Coverage of the question: %s.} %s" % (tex_escape(summary["figures"]["level"]), tex_escape(summary["coverage"])), "", "\\textbf{What was found}"]
        out += _items(["%s (%s)" % (tex_escape(p["point"]), tex_escape(", ".join(p["works"]))) for p in summary["found"]] or ["nothing that could be cited"])
        out += ["", "\\textbf{Gaps}"] + _items([tex_escape(g["gap"]) for g in summary["gaps"]] or ["none named"])
    out += ["", "\\section*{How the works were selected}",
            "%d found, %d duplicates, %d dropped before the screening, %d screened: %d included, %d maybe, %d excluded." % (
                flow["found"], flow["duplicates"], flow["dropped"], flow["screened"], flow["included"], flow["maybe"], flow["excluded_abstract"] + flow["excluded_full"]), "",
            "\\begin{tabular}{llr}", "Keyword & Origin & Hits \\\\ \\hline"]
    out += ["%s & %s & %d \\\\" % (tex_escape(k["keyword"]), tex_escape(k["origin"]), k["hits"]) for k in report["keywords"]]
    out += ["\\end{tabular}"]
    if report["gaps"]:
        out += ["", "Keywords without an included work: %s." % tex_escape(", ".join(report["gaps"]))]
    works = report["works"]
    for title, rows in (("Included", [w for w in works if w["decision"] == "include"]), ("Maybe", [w for w in works if w["decision"] == "maybe"]),
                        ("Excluded", [w for w in works if w["decision"] == "exclude"])):
        if rows:
            out += ["", "\\section*{%s}" % title] + _items([_work_line(w) for w in rows])
    if report["dropped"]:
        out += ["", "\\section*{Dropped before screening}"] + _items(["%s: %s" % (tex_escape(d["work"].get("title") or d["work"].get("doi")), tex_escape(d["reason"])) for d in report["dropped"]])
    out += ["", "\\end{document}", ""]
    return "\n".join(out)
