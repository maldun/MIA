"""
The run report (REQ-WFM-139, 141; G-V3.REPORT T-01, A-154): the Markdown file that ends every skill run. The first line names the state (Done, Stopped, Failed; the reason of a failure on the
same line), then comes the text of the skill unchanged, or, where the skill handed over none, a short report of the run record: the result, or the sentence that the run gave no output, and the figures.
Everything that came from the web, a model or a user is escaped here, and a web address is a link only where it is an http or https address without spaces (the sources are web text, TB-web).
"""
import re

STATES = {"done": "Done", "stopped": "Stopped", "failed": "Failed"}
NO_OUTPUT = "The run gave no output."
MAX_REASON = 300
_SPECIAL = re.compile(r"([\\`*_\[\]()<>#|~!&])")                                  # what can start a link, an image, a tag, a heading or a table in a Markdown reader
_ADDRESS = re.compile(r"https?://[^\s<>]+", re.I)
_TRAILING = ".,;:!?)]}'\""                                                       # punctuation after an address that belongs to the sentence, not to the address


def escape(text):
    """the text with every character that a Markdown or HTML reader could take as markup written as a plain character"""
    return _SPECIAL.sub(r"\\\1", str(text))


def link_addresses(text):
    """escaped text in which every http or https address is a link `<address>`; any other address (javascript:, data:, file:, relative) stays escaped text"""
    text, parts, last = str(text), [], 0
    for match in _ADDRESS.finditer(text):
        address = match.group(0).rstrip(_TRAILING)
        end = match.start() + len(address)
        parts.append(escape(text[last:match.start()]))
        parts.append("<%s>" % address)
        last = end
    parts.append(escape(text[last:]))
    return "".join(parts)


def _one_line(text):
    return " ".join(str(text).split())[:MAX_REASON]


def first_line(state, reason=None):
    """`# Done`, `# Stopped` or `# Failed: <reason>`: the state of the run on one line"""
    line = "# " + STATES.get(state, escape(state))
    if reason and state != "done":
        line += ": " + escape(_one_line(reason))
    return line


def _figures(record):
    lines = ["- %s: %s" % (escape(name), escape(value)) for name, value in sorted((record.get("counts") or {}).items())]
    for name, figure in sorted((record.get("budget") or {}).items()):
        if isinstance(figure, dict) and "used" in figure:
            lines.append("- %s: %s%s" % (escape(name), escape(figure["used"]), " of %s" % escape(figure["limit"]) if "limit" in figure else ""))
    return lines


def compose(state, reason=None, own=None, result="", record=None):
    """the report text: the state line, a blank line, then the skill's own report unchanged, or the fallback of the run record (result or `no output`, then the figures)"""
    head = first_line(state, reason) + "\n\n"
    if own:
        return head + str(own)
    body = ["## Result", "", link_addresses(result) if str(result or "").strip() else NO_OUTPUT]
    figures = _figures(record or {})
    if figures:
        body += ["", "## Figures", ""] + figures
    return head + "\n".join(body) + "\n"


def report_name(skill, date, question):
    """`<skill>-<date>-<first words of the question>.md`: a name that the files volume takes (letters, digits, dot, dash, underscore)"""
    words = "-".join(re.findall(r"[a-z0-9]+", str(question or "").lower())[:6])
    return "-".join(part for part in (re.sub(r"[^A-Za-z0-9._-]", "", str(skill)), date, words or "report") if part) + ".md"
