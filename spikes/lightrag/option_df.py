"""Throwaway spike for NFR-23 sample A: definitions and stated facts (FR-98, FR-99), built like option 1 (same chunks,
same model call, a quote per proposal, checks against the WHOLE document). Not an eval run; plan:
specs/mia/goals/G-V4.BUILDER/nfr23-sample-plan.md. Standard library only.

usage: MIA_SPIKE_MODEL=<model> python3 -I option_df.py OUTDIR DOC.txt...   (run only with the owner's OK: it uses the GPU)
writes OUTDIR/<doc>.json = {model, accepted: [...], refused: [{item, reason}], seconds, chunks}

Checks (FR-99 as reviewed, D-382): the quote is a passage of the document word for word (after checks.norm); a
definition's term occurs in the document and in its quote. A fact has no name to check."""
import json, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import entity_in_source, norm
import option1

SCHEMA = {"type": "object", "required": ["definitions", "facts"], "properties": {
    "definitions": {"type": "array", "items": {"type": "object", "required": ["term", "definition", "quote"], "properties": {
        "term": {"type": "string"}, "definition": {"type": "string"}, "quote": {"type": "string"}}}},
    "facts": {"type": "array", "items": {"type": "object", "required": ["statement", "quote"], "properties": {
        "statement": {"type": "string"}, "quote": {"type": "string"}}}}}}

PROMPT = """Extract the definitions and the stated facts from the text.
A definition says what a term means. A stated fact is something the text states as true: a number, a date, a cause,
a result or a property of a named thing.
Rules: use terms exactly as written in the text. Only state what the text says; do not infer and do not add knowledge.
Write each definition and each fact as one short sentence that restates its quote.
Every definition and every fact needs a quote: one sentence copied word for word from the text that states it.
A definition's quote must contain its term. Skip examples, questions and opinions.

TEXT:
{text}"""


def validate(proposal: dict, doc_text: str):
    """Returns None when accepted, else the reason."""
    quote = proposal.get("quote", "")
    if not quote or norm(quote) not in norm(doc_text):
        return "quote is not a passage of the document"
    if "term" in proposal:
        if not entity_in_source(proposal["term"], [doc_text]):
            return f"term not in the document: {proposal['term']}"
        if not entity_in_source(proposal["term"], [quote]):
            return "quote does not contain the term"
    return None


def ask(text: str) -> dict:
    body = {"model": option1.MODEL, "stream": False, "think": False, "format": SCHEMA,
            "options": {"num_ctx": option1.CTX, "temperature": 0},
            "messages": [{"role": "user", "content": PROMPT.format(text=text)}]}
    req = urllib.request.Request(f"{option1.HOST}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(json.loads(r.read())["message"]["content"])


def build(doc_text: str, ask_fn=ask):
    accepted, refused, seen = [], [], set()
    chunks = option1.chunk(doc_text)
    for c in chunks:
        try:
            got = ask_fn(c)
        except Exception as e:  # a failed chunk is recorded, not hidden
            refused.append(dict(item={"chunk": c[:80]}, reason=f"model step failed: {e!r}"[:200]))
            continue
        for kind, rows in (("definition", got.get("definitions", [])), ("fact", got.get("facts", []))):
            for p in rows:
                key = (kind, norm(p.get("term", "")), norm(p.get("statement", "")), norm(p.get("quote", "")))
                if key in seen:
                    continue
                seen.add(key)
                why = validate(p, doc_text)
                (refused if why else accepted).append(dict(item=dict(p, kind=kind), reason=why) if why else dict(p, kind=kind))
    return dict(accepted=accepted, refused=refused, chunks=len(chunks))


if __name__ == "__main__":
    option1.main(sys.argv, build_fn=build)
