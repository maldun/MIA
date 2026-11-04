"""Two hard checks for builder proposals (hard checks before model judgement). Plain Python, no dependency.
1. entity_in_source: the name of a proposed entity occurs in a passage it claims as source.
2. relation_in_source: both endpoints of a proposed relation occur together in one passage (loose: same chunk;
   strict: within `window` characters, i.e. about one sentence).
Normalisation is deliberately small: case, hyphens and punctuation, a trailing plural 's', a parenthetical suffix."""
import re


def norm(s: str) -> str:
    s = s.casefold().replace("-", " ").replace("_", " ")
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(s.split())


def _variants(name: str):
    out = {norm(name)}
    base = re.sub(r"\s*\(.*?\)\s*", " ", name).strip()  # "Large Language Models (LLMs)" -> "Large Language Models"
    paren = re.findall(r"\((.*?)\)", name)
    out.add(norm(base))
    out.update(norm(p) for p in paren)
    out |= {v[:-1] for v in list(out) if v.endswith("s") and len(v) > 4}
    return {v for v in out if v}


def _positions(name: str, text_norm: str):
    pos = []
    for v in _variants(name):
        forms = re.escape(v) + r"(?:e?s)?"  # the text may use the plural of the name
        if v.endswith("y"):
            forms += "|" + re.escape(v[:-1]) + "ies"
        for m in re.finditer(r"(?<!\w)(?:" + forms + r")(?!\w)", text_norm):
            pos.append(m.start())
    return pos


def entity_in_source(name: str, passages: list[str]) -> bool:
    return any(_positions(name, norm(p)) for p in passages)


def relation_in_source(a: str, b: str, passages: list[str], window: int | None = None) -> bool:
    for p in passages:
        t = norm(p)
        pa, pb = _positions(a, t), _positions(b, t)
        if not pa or not pb:
            continue
        if window is None or any(abs(x - y) <= window for x in pa for y in pb):
            return True
    return False
