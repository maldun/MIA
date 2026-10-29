"""
The full text of a work for the review (RV34, REQ-WFM-028): the open access link of the work, the text of the page or of the PDF, cut by code into sections that fit a model (RV2).
Open access only: a work without a link, or one that cannot be read, stays at abstract level and the reason is kept in `notes`.

  F1  a heading is a whole line of at most 60 characters, optionally numbered ("1.", "2 ", "II."), that is one of the usual section names; a sentence with such a word is not one
  F2  the text before the first heading is the section "Start"; References, Bibliography and Acknowledgements and everything after them are dropped
  F3  a section longer than max_chars is cut at blank lines into parts "Name (1)", "Name (2)" (one paragraph longer than max_chars is cut hard); without any heading the parts are "Part n"
  F4  the conclusion is the section Conclusion(s), else the last section, else ""
  F5  a PDF is converted only by pdf_text.pdf_to_text (inside the wall, W1 to W3); without the wall the work stays at abstract level
  F6  the page is untrusted (TB-paper): phrases that look like instructions are listed in `signals`; the model prompts delimit the text as data
"""
import importlib
import re

HEADINGS = {"abstract", "introduction", "background", "related work", "methods", "method", "materials and methods", "methodology", "results", "discussion", "results and discussion",
            "conclusion", "conclusions", "limitations", "summary"}
STOPS = {"references", "bibliography", "acknowledgements", "acknowledgments"}
_NUMBER = re.compile(r"^(?:\d+(?:\.\d+)*\.?|[IVX]+\.)\s+")
_PARAGRAPHS = re.compile(r"\n\s*\n")
PDF_TYPE = "application/pdf"
MAX_PDF_BYTES = 20 * 1024 * 1024


def _heading(line):
    line = line.strip()
    if not line or len(line) > 60:
        return None
    name = _NUMBER.sub("", line).strip().rstrip(":")
    return name if name.lower() in HEADINGS | STOPS else None


def _parts(name, text, max_chars, numbered=False):
    """[(name, text)]: the text cut at blank lines into parts of at most max_chars"""
    pieces = []
    for paragraph in (p.strip() for p in _PARAGRAPHS.split(text)):
        while len(paragraph) > max_chars:
            pieces.append(paragraph[:max_chars])
            paragraph = paragraph[max_chars:].strip()
        if paragraph:
            pieces.append(paragraph)
    parts = []
    for piece in pieces:
        if parts and len(parts[-1]) + 2 + len(piece) <= max_chars:
            parts[-1] += "\n\n" + piece
        else:
            parts.append(piece)
    if numbered:
        return [("%s %d" % (name, i), part) for i, part in enumerate(parts, 1)]
    if len(parts) == 1:
        return [(name, parts[0])]
    return [("%s (%d)" % (name, i), part) for i, part in enumerate(parts, 1)]


def cut_sections(text, max_chars=6000):
    """{"sections": [{"name", "text"}], "conclusion": text}"""
    raw, name, lines, headed = [], "Start", [], False
    for line in text.splitlines():
        heading = _heading(line)
        if heading is None:
            lines.append(line)
            continue
        raw.append((name, "\n".join(lines).strip()))
        if heading.lower() in STOPS:
            lines, name = [], None
            break
        name, lines, headed = heading, [], True
    if name is not None:
        raw.append((name, "\n".join(lines).strip()))
    raw = [(n, t) for n, t in raw if t]
    if not raw:
        return {"sections": [], "conclusion": ""}
    if not headed:
        sections = _parts("Part", "\n\n".join(t for _, t in raw), max_chars, numbered=True)
    else:
        sections = [part for n, t in raw for part in _parts(n, t, max_chars)]
    conclusion = next((t for n, t in raw if n.lower().startswith("conclusion")), sections[-1][1])
    return {"sections": [{"name": n, "text": t} for n, t in sections], "conclusion": conclusion[:max_chars]}



def _core(name):
    """a module of the core, loaded when it is needed: as a part of the package (python -m MIA) by its place, as a script (the tests) by its name"""
    if __package__:
        try:
            return importlib.import_module("..." + name, package=__package__)
        except (ImportError, ValueError):             # ValueError: as a script (extensions.review.fulltext) there is no package above
            pass
    return importlib.import_module(name)

class FullTextSource:
    """full_text(work) for ReviewRun: the cut text of the open access link of the work, or None (the reason is in notes[id]). get(url, accept, max_bytes) is WebClient.get;
    pdf_to_text(bytes) is pdf_text.pdf_to_text; extract_text (gives {"title", "text"}) and injection_signals are those of web_tools (the defaults are loaded only when needed)"""

    def __init__(self, get, pdf_to_text=None, extract_text=None, injection_signals=None, max_chars=6000):
        self.get, self.max_chars, self.notes = get, max_chars, {}
        self._pdf, self._extract, self._signals = pdf_to_text, extract_text, injection_signals

    def _note(self, work, why):
        self.notes[work.get("doi") or work.get("title") or ""] = why

    def __call__(self, work):
        url = work.get("oa_url")
        if not url:
            return self._note(work, "no open access link")
        web_tools = _core("web_tools")
        ALLOWED_TYPES = web_tools.ALLOWED_TYPES
        if self._extract is None:
            self._extract, self._signals = web_tools.extract_text, web_tools.injection_signals
        try:
            page = self.get(url, accept=tuple(ALLOWED_TYPES) + (PDF_TYPE,), max_bytes=MAX_PDF_BYTES)
            if page["content_type"] == PDF_TYPE:
                if self._pdf is None:
                    self._pdf = _core("pdf_text").pdf_to_text
                text = self._pdf(page["body"])["text"]
            else:
                text = self._extract(page["text"])["text"]
        except Exception as exc:                  # WebError, PdfError, PdfUnavailable: the work stays at abstract level
            return self._note(work, "%s: %s" % (type(exc).__name__, exc))
        cut = cut_sections(text, self.max_chars)
        if not cut["sections"]:
            return self._note(work, "the page has no text")
        cut["source"] = page["url"]
        cut["truncated"] = page["truncated"]
        cut["signals"] = self._signals(text) if self._signals else []
        return cut
