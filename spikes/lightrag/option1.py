"""Throwaway spike C, option 1: own builder = one model step with a JSON schema, chunks cut at sentence borders,
every proposal carries the sentence that states it, proposals are checked against the WHOLE document.
Not an eval run. Standard library only (talks to Ollama over HTTP, like the model layer would).

usage: python3 -I option1.py OUTDIR DOC.txt...      (run only with the owner's OK: it uses the GPU)
writes OUTDIR/<doc>.json = {accepted: [...], refused: [{item, reason}], seconds, chunks}

Rules (candidate requirement text for Plan, not applied to FR-42):
  a proposal is refused when a name it uses does not occur in the source document, or when its quote is not
  a verbatim passage of the document, or when a relation's quote does not contain both of its ends."""
import json, re, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import entity_in_source, relation_in_source, norm

HOST, MODEL, CTX = "http://127.0.0.1:11434", "gemma4:12b-it-qat", 8192
MAX_CHARS = 3000  # about 750 tokens of text, leaves room for prompt and answer in 8192

SCHEMA = {"type": "object", "required": ["entities", "relations"], "properties": {
    "entities": {"type": "array", "items": {"type": "object", "required": ["name", "quote"], "properties": {
        "name": {"type": "string"}, "quote": {"type": "string"}}}},
    "relations": {"type": "array", "items": {"type": "object", "required": ["source", "relation", "target", "quote"],
        "properties": {"source": {"type": "string"}, "relation": {"type": "string"}, "target": {"type": "string"},
                       "quote": {"type": "string"}}}}}}

PROMPT = """Extract the important entities and the relations between them from the text.
Rules: use the names exactly as written in the text. Only state what the text says; do not infer.
Every entity and every relation needs a quote: one sentence copied word for word from the text that states it.
A relation's quote must contain both ends. Skip generic nouns and example details.

TEXT:
{text}"""


def split_sentences(text: str):
    # paragraph first, then sentence ends; abbreviations like "e.g." may split early, which is harmless here
    for para in re.split(r"\n\s*\n", text):
        para = " ".join(para.split())
        if para:
            yield from re.split(r"(?<=[.!?])\s+(?=[A-Z\"(\[])", para)


def chunk(text: str, max_chars: int = MAX_CHARS):
    """Chunks of whole sentences, never cut inside a word or sentence (a longer sentence is its own chunk)."""
    out, cur = [], ""
    for s in split_sentences(text):
        if cur and len(cur) + len(s) + 1 > max_chars:
            out.append(cur)
            cur = ""
        cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out


def validate(proposal: dict, doc_text: str):
    """Returns None when accepted, else the reason. Names are checked against the whole document."""
    quote = proposal.get("quote", "")
    if not quote or norm(quote) not in norm(doc_text):
        return "quote is not a passage of the document"
    ends = [proposal["name"]] if "name" in proposal else [proposal["source"], proposal["target"]]
    for e in ends:
        if not entity_in_source(e, [doc_text]):
            return f"name not in the document: {e}"
    if "name" in proposal:
        return None if entity_in_source(proposal["name"], [quote]) else "quote does not contain the name"
    if not relation_in_source(proposal["source"], proposal["target"], [quote]):
        return "quote does not contain both ends"
    return None


def ask(text: str) -> dict:
    body = {"model": MODEL, "stream": False, "think": False, "format": SCHEMA,
            "options": {"num_ctx": CTX, "temperature": 0},
            "messages": [{"role": "user", "content": PROMPT.format(text=text)}]}
    req = urllib.request.Request(f"{HOST}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(json.loads(r.read())["message"]["content"])


def build(doc_text: str, ask_fn=ask):
    accepted, refused, seen = [], [], set()
    chunks = chunk(doc_text)
    for c in chunks:
        try:
            got = ask_fn(c)
        except Exception as e:  # a failed chunk is recorded, not hidden
            refused.append(dict(item={"chunk": c[:80]}, reason=f"model step failed: {e!r}"[:200]))
            continue
        for kind, rows in (("entity", got.get("entities", [])), ("relation", got.get("relations", []))):
            for p in rows:
                key = (kind, norm(p.get("name", "")), norm(p.get("source", "")), norm(p.get("target", "")), norm(p.get("relation", "")))
                if key in seen:
                    continue
                seen.add(key)
                why = validate(p, doc_text)
                (refused if why else accepted).append(dict(item=dict(p, kind=kind), reason=why) if why else dict(p, kind=kind))
    return dict(accepted=accepted, refused=refused, chunks=len(chunks))


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
