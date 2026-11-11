"""Throwaway spike C, option 1b (draft, NOT run on a model): option 1 plus two stricter rules for ENTITIES, the weak spot of
the owner's marks (12 of 15 invented items and 18 of 116 bad entities, relations 6 of 79).
  rule 1: the quote of an entity is ONE whole sentence of the document (not a fragment, not two sentences) and contains the name.
  rule 2: an entity has a description, and every content word of it occurs in its quote (the description only restates the quote).
Both are hard checks without a model call. Relations are checked as in option1.py. Standard library only.

usage: python3 -I option1b.py OUTDIR DOC.txt...      (uses the GPU: run only with the owner's OK)
Throwaway, not an eval run; the thresholds are guesses until `measure_grounding.py` and a run on the marked documents show them."""
import re, sys, json, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import norm
import option1
from option1 import split_sentences, chunk, ask as _ask_unused  # noqa: F401  (same chunker and model call shape)

STOP = set("""the a an and or of in on at to for with by from as is are was were be been being this that these those it its their
his her which who whom whose what when where how than then also such can may might will would should could not no into over under
about between among each other more most some any all both only very has have had do does did""".split())

SCHEMA = {"type": "object", "required": ["entities", "relations"], "properties": {
    "entities": {"type": "array", "items": {"type": "object", "required": ["name", "description", "quote"], "properties": {
        "name": {"type": "string"}, "description": {"type": "string"}, "quote": {"type": "string"}}}},
    "relations": option1.SCHEMA["properties"]["relations"]}}

PROMPT = """Extract the important entities and the relations between them from the text.
Rules: use the names exactly as written in the text. Only state what the text says; do not infer.
Every entity needs a quote (ONE whole sentence copied word for word from the text that names it) and a description
that only restates that sentence, using words of the sentence. Every relation needs a quote with both ends.
Skip generic nouns and example details.

TEXT:
{text}"""


def words(s: str):
    """Content words, case-folded, a trailing plural 's' dropped; short words and stop words do not count."""
    return {w[:-1] if w.endswith("s") and len(w) > 4 else w for w in norm(s).split() if len(w) > 3 and w not in STOP}


def ungrounded(description: str, quote: str):
    return sorted(words(description) - words(quote))


def one_whole_sentence(quote: str, doc_text: str) -> bool:
    return norm(quote) in {norm(s) for s in split_sentences(doc_text)}


def validate(proposal: dict, doc_text: str, max_ungrounded: int = 0):
    """None when accepted, else the reason. Entities: option 1 rules + rule 1 + rule 2; relations: option 1 rules."""
    why = option1.validate(proposal, doc_text)
    if why or "name" not in proposal:
        return why
    if not one_whole_sentence(proposal["quote"], doc_text):
        return "quote is not one whole sentence of the document"
    extra = ungrounded(proposal.get("description", ""), proposal["quote"])
    if not proposal.get("description", "").strip():
        return "entity has no description"
    if len(extra) > max_ungrounded:
        return f"description uses words that are not in the quote: {', '.join(extra[:5])}"
    return None


def build(doc_text: str, ask_fn=None, max_ungrounded: int = 0):
    ask_fn = ask_fn or ask
    accepted, refused, seen = [], [], set()
    chunks = chunk(doc_text)
    for c in chunks:
        try:
            got = ask_fn(c)
        except Exception as e:
            refused.append(dict(item={"chunk": c[:80]}, reason=f"model step failed: {e!r}"[:200]))
            continue
        for kind, rows in (("entity", got.get("entities", [])), ("relation", got.get("relations", []))):
            for p in rows:
                key = (kind, norm(p.get("name", "")), norm(p.get("source", "")), norm(p.get("target", "")), norm(p.get("relation", "")))
                if key in seen:
                    continue
                seen.add(key)
                if kind == "entity":
                    p["ungrounded"] = len(ungrounded(p.get("description", ""), p.get("quote", "")))  # kept so other limits can be read off the run
                why = validate(p, doc_text, max_ungrounded)
                (refused if why else accepted).append(dict(item=dict(p, kind=kind), reason=why) if why else dict(p, kind=kind))
    return dict(accepted=accepted, refused=refused, chunks=len(chunks))


def ask(text: str) -> dict:
    import urllib.request
    body = {"model": option1.MODEL, "stream": False, "think": False, "format": SCHEMA,
            "options": {"num_ctx": option1.CTX, "temperature": 0},
            "messages": [{"role": "user", "content": PROMPT.format(text=text)}]}
    req = urllib.request.Request(f"{option1.HOST}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(json.loads(r.read())["message"]["content"])


def main(argv):
    out = Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for f in map(Path, argv[2:]):
        t = time.time()
        res = build(f.read_text())
        res["seconds"] = round(time.time() - t, 1)
        (out / f"{f.stem}.json").write_text(json.dumps(res, indent=1))
        print(f.stem, res["chunks"], "chunks", len(res["accepted"]), "accepted", len(res["refused"]), "refused", res["seconds"], "s", flush=True)


if __name__ == "__main__":
    main(sys.argv)
