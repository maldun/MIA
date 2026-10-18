"""
Claims out of prose (ui/REQUIREMENTS_CORE.md 13.1, step 5): the stage that turns an answer or a document into the structured claims that the checks accept. This module holds the two things every
extractor needs, whatever it is made of:

  score_extraction(source, predicted, gold)   how good a list of claims is, against the claims a person found in the same text
  extract_claims_rules(text)                  a baseline extractor made of patterns, without a model

A claim is {"type", "text", "data"}. `text` is a **verbatim span of the source** (a sentence or part of it): that is what makes an invented claim detectable by code (the quote check of the library),
`type` is the claim type of the checks and `data` has the fields that type needs:

  numeric    {"expression": "12*1.5+3", "value": 21}                                    an arithmetic statement
  unit       {"value": 5, "from_unit": "km", "to_unit": "mi", "result_value": 3.1}      a conversion
  date       {"kind": "weekday", "date": "2000-01-01", "weekday": "Saturday"}           calendar facts (see checks.date_claim)
  fact       {"entities": ["Eiffel Tower"], "facts": ["330 metres"]}                    a statement about the world that the web can confirm
  quotation  {"quote": "...", "attributed_to": "Eiffel"}                                 somebody is quoted
  citation   {"url": "https://...", "quote": "..."}                                      a source is cited

Not claims: opinions, questions, advice, instructions, hedged statements ("might", "probably"), and statements that somebody else makes ("critics say ..."), unless the statement is a quotation.
"""
import json
import re

try:
    from . import checks
except ImportError:  # used as plain script / in tests
    import checks

CLAIM_TYPES = ("numeric", "unit", "date", "fact", "quotation", "citation", "computable")
REQUIRED_DATA = {"numeric": ("expression", "value"), "unit": ("value", "from_unit", "to_unit", "result_value"), "date": ("kind",), "fact": ("entities",),
                 "quotation": ("quote",), "citation": ("url",), "computable": ()}
HEDGES = re.compile(r"\b(might|may|could|probably|perhaps|maybe|possibly|likely|i think|i believe|seems?|appears?|supposedly|allegedly|should|would)\b|\?", re.I)


def validate_claim(claim):
    """problems of one extracted claim as a list of messages (empty = the claim has the shape the checks need)"""
    if not isinstance(claim, dict):
        return ["a claim must be an object"]
    problems = []
    if claim.get("type") not in CLAIM_TYPES:
        problems.append("type must be one of %s" % ", ".join(CLAIM_TYPES))
    if not isinstance(claim.get("text"), str) or not claim.get("text", "").strip():
        problems.append("text (a verbatim span of the source) is needed")
    data = claim.get("data")
    if not isinstance(data, dict):
        problems.append("data must be an object")
    else:
        for key in REQUIRED_DATA.get(claim.get("type"), ()):
            if key not in data or data[key] in (None, "", []):
                problems.append("data.%s is needed for a %s claim" % (key, claim.get("type")))
    return problems


EXTRACTION_GUIDE = """Find the checkable claims in the text. A claim is a statement that can be true or false and that a program or a source could check. Do not judge whether it is true: extract false claims too.
For each claim give: type, text (copy the sentence, or the part of it that holds the claim, EXACTLY as it appears in the text, character for character), data.
Types and their data:
- numeric: an arithmetic statement. data: {"expression": "12*1.5+3", "value": 21} (digits and + - * / ** and brackets; value is the claimed result)
- unit: a conversion between units. data: {"value": 5, "from_unit": "km", "to_unit": "mi", "result_value": 3.1}
- date: calendar facts. data: {"kind": "weekday", "date": "2000-01-01", "weekday": "Saturday"}. Other kinds: days_between (start, end, days), age (birth, on, years), leap_year (year, leap: true or false), add_days (start, days, result_date). Dates as YYYY-MM-DD.
- fact: a statement about the world with names and numbers or other specifics. data: {"entities": ["Eiffel Tower"], "facts": ["330 metres"]} (entities: the names; facts: the key numbers and specifics as written)
- quotation: somebody is quoted. data: {"quote": "the words", "attributed_to": "Name"}
- citation: a web address is given as a source. data: {"url": "https://...", "quote": "the quoted words, if any"}
Not claims: opinions, feelings, questions, advice, instructions, chat, hedged statements (might, probably, I think), what others only think or feel, and numbers that are no statements (phone numbers, page numbers, times, a year inside a name).
A sentence can hold several claims: give each its own entry with the same text. If there is nothing to check, return an empty list."""


# --- scoring ----------------------------------------------------------------------------------------------------------------------------------

def _norm(text):
    return re.sub(r"[^\w\s.]", " ", checks.normalize(str(text)).replace("'", "")).split()


def _norm_text(text):
    return " ".join(_norm(text))


def _overlap(a, b):
    """do two spans of text say the same thing: one contains the other (normalised) or most of their words are shared"""
    na, nb = _norm_text(a), _norm_text(b)
    if not na or not nb:
        return False
    if na in nb or nb in na:
        return True
    wa, wb = set(na.split()), set(nb.split())
    return len(wa & wb) / len(wa | wb) >= 0.6


def _number(value):
    try:
        return checks.parse_number(value)
    except (ValueError, TypeError):
        return None


def _same_value(predicted, wanted):
    a, b = _number(predicted), _number(wanted)
    if a is not None and b is not None and not isinstance(predicted, bool):
        return abs(a - b) <= 1e-9 * max(1.0, abs(b))
    return _norm_text(predicted) == _norm_text(wanted)


def _same_expression(predicted, wanted):
    """the same arithmetic: equal values (so 3 + 12 * 1.5 is 12 * 1.5 + 3), else the same text"""
    try:
        return abs(checks.evaluate_two_ways(str(predicted))[0] - checks.evaluate_two_ways(str(wanted))[0]) <= 1e-9 * max(1.0, abs(checks.evaluate_two_ways(str(wanted))[0]))
    except checks.ExpressionError:
        return _norm_text(predicted) == _norm_text(wanted)


def _same_unit(predicted, wanted):
    return checks._unit(predicted) == checks._unit(wanted)


def _same_date(predicted, wanted):
    try:
        return checks.parse_date(predicted) == checks.parse_date(wanted)
    except (ValueError, TypeError, AttributeError):
        return _norm_text(predicted) == _norm_text(wanted)


def _same_weekday(predicted, wanted):
    a, b = checks._WEEKDAYS.get(str(predicted).strip().lower().rstrip(".")), checks._WEEKDAYS.get(str(wanted).strip().lower().rstrip("."))
    return a is not None and a == b


def _contains_all(predicted, wanted):
    """every wanted item occurs in the predicted list (normalised, a longer text that contains the item is fine)"""
    items = [_norm_text(p) for p in (predicted if isinstance(predicted, list) else [predicted])]
    return all(any(_norm_text(w) in item or item in _norm_text(w) for item in items if item) for w in wanted)


FIELD_RULES = {"expression": _same_expression, "from_unit": _same_unit, "to_unit": _same_unit, "date": _same_date, "weekday": _same_weekday, "start": _same_date, "end": _same_date,
               "birth": _same_date, "on": _same_date, "a": _same_date, "b": _same_date, "result_date": _same_date,
               "entities": _contains_all, "facts": _contains_all, "quote": lambda p, w: _norm_text(w) in _norm_text(p) or _norm_text(p) in _norm_text(w),
               "attributed_to": lambda p, w: _norm_text(w) in _norm_text(p) or _norm_text(p) in _norm_text(w), "url": lambda p, w: str(p).strip().rstrip("/") == str(w).strip().rstrip("/")}


def data_differences(predicted_data, gold_data):
    """the keys of the gold data that the predicted data gets wrong or lacks (extra keys are fine)"""
    wrong = []
    for key, wanted in (gold_data or {}).items():
        if key not in (predicted_data or {}):
            wrong.append(key)
        elif not FIELD_RULES.get(key, _same_value)(predicted_data[key], wanted):
            wrong.append(key)
    return wrong


def score_extraction(source, predicted, gold):
    """compares extracted claims with the gold claims of a text. Every gold claim is matched, wrongly typed, has wrong data or is missed; every predicted claim is matched, spurious (no gold claim
    at that place), a duplicate, or unanchored (its text is not a verbatim span of the source). ok means a perfect extraction for this text."""
    predicted = [p for p in (predicted or []) if isinstance(p, dict)]
    gold = list(gold or [])
    used, matched, wrong_data, wrong_type, missed = set(), [], [], [], []
    for g in gold:
        near = [i for i, p in enumerate(predicted) if i not in used and _overlap(str(p.get("text", "")), g["anchor"])]
        same_type = [i for i in near if predicted[i].get("type") == g["type"]]
        good = [i for i in same_type if not data_differences(predicted[i].get("data"), g.get("data"))]
        if good:
            used.add(good[0])
            matched.append({"anchor": g["anchor"], "type": g["type"]})
        elif same_type:
            used.add(same_type[0])
            wrong_data.append({"anchor": g["anchor"], "type": g["type"], "keys": data_differences(predicted[same_type[0]].get("data"), g.get("data")), "got": predicted[same_type[0]].get("data")})
        elif near:
            used.add(near[0])
            wrong_type.append({"anchor": g["anchor"], "wanted": g["type"], "got": predicted[near[0]].get("type")})
        else:
            missed.append({"anchor": g["anchor"], "type": g["type"]})
    spurious, duplicates = [], []
    for i, p in enumerate(predicted):
        if i in used:
            continue
        if any(_overlap(str(p.get("text", "")), g["anchor"]) for g in gold):
            duplicates.append({"text": p.get("text"), "type": p.get("type")})
        else:
            spurious.append({"text": p.get("text"), "type": p.get("type")})
    unanchored = [{"text": p.get("text"), "type": p.get("type")} for p in predicted
                  if checks.quote_in_source(str(p.get("text", "")), source)["status"] != "pass"]
    invalid = [{"text": p.get("text"), "problems": validate_claim(p)} for p in predicted if validate_claim(p)]
    ok = not (wrong_data or wrong_type or missed or spurious or duplicates or unanchored or invalid)
    return {"gold": len(gold), "predicted": len(predicted), "matched": len(matched), "wrong_data": wrong_data, "wrong_type": wrong_type, "missed": missed, "spurious": spurious,
            "duplicates": duplicates, "unanchored": unanchored, "invalid": invalid, "ok": ok}


# --- a baseline without a model ------------------------------------------------------------------------------------------------------------------

_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z“\"(])")
_NUM = r"\d[\d,]*(?:\.\d+)?"
_UNIT_WORDS = "|".join(sorted({u for table in checks._UNITS.values() for u in table} | set(checks._ALIASES) | {"c", "f", "k"}, key=len, reverse=True))
_UNIT = re.compile(r"(?P<v>%s)\s*(?P<a>[\u00b0]?(?:%s))\b\s*(?:=|is|are|equals|converts to|corresponds to|is about|is roughly|is approximately|are about|are roughly|is equal to|\u2248)\s*"
                   r"(?:about |roughly |approximately |around )?(?P<r>%s)\s*(?P<b>[\u00b0]?(?:%s))\b" % (_NUM, _UNIT_WORDS, _NUM, _UNIT_WORDS), re.I)
_ARITH = re.compile(r"(?P<e>(?:%s\s*[-+*/x×÷^]\s*)+%s)\s*(?:=|equals|is)\s*(?P<v>%s)" % (_NUM, _NUM, _NUM), re.I)
_WORD_ARITH = re.compile(r"(?P<e>%s(?:\s+(?:plus|minus|times|multiplied by|divided by|over)\s+%s)+)\s+(?:is|equals)\s+(?P<v>%s)" % (_NUM, _NUM, _NUM), re.I)
_WEEKDAY = re.compile(r"(?P<d>(?:\d{4}-\d{2}-\d{2})|(?:[A-Z][a-z]+ \d{1,2}, \d{4})|(?:\d{1,2} [A-Z][a-z]+ \d{4}))\s+(?:was|is) a (?P<w>Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)")
_LEAP = re.compile(r"(?P<y>\d{4}) (?P<w>was|is) (?P<n>not )?a leap year")
_URL = re.compile(r"https?://[^\s)\]>,;\"']+[^\s)\]>,;.\"']")
_QUOTE = re.compile(r"[“\"]([^”\"]{12,})[”\"]")
_ATTRIBUTION = re.compile(r"(?:according to|by|said|says|wrote|writes|stated|states)\s+([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*)*)|([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*)*)\s+(?:said|says|wrote|writes|stated|states)")
_CAPITALISED = re.compile(r"\b([A-Z][\w'-]*(?:\s+(?:(?:of|the|de|von|van)\s+)?[A-Z][\w'-]*)*)")
_FACT_NUMBER = re.compile(r"\b(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?:\s+(?:percent|%|metres|meters|km|kilometres|kilometers|miles|feet|years|people|million|billion|tons|tonnes|kg|degrees))?", re.I)
_STOP_ENTITIES = {"The", "A", "An", "It", "This", "That", "These", "Those", "In", "On", "At", "He", "She", "They", "We", "I", "Its", "His", "Her", "Their", "And", "But", "So", "Today", "However"}


def _as_number(text):
    return float(text.replace(",", ""))


def extract_claims_rules(text):
    """a baseline: patterns for arithmetic, unit conversions, weekdays and leap years, quotations, citations (addresses), and a rough rule for facts (a sentence with a name and a number,
    without a hedge). It finds what has a clear form and misses what needs reading: the room that a model has to fill."""
    claims = []
    for sentence in _SENTENCE.split(str(text).strip()):
        sentence = sentence.strip()
        if not sentence:
            continue
        url = _URL.search(sentence)
        quote = _QUOTE.search(sentence)
        if url:
            data = {"url": url.group(0)}
            if quote:
                data["quote"] = quote.group(1)
            claims.append({"type": "citation", "text": sentence, "data": data})
            continue
        if quote and re.search(r"\b(said|says|wrote|writes|stated|states|according to)\b", sentence):
            who = _ATTRIBUTION.search(sentence)
            claims.append({"type": "quotation", "text": sentence, "data": {"quote": quote.group(1), "attributed_to": (who.group(1) or who.group(2)).strip() if who else ""}})
            continue
        if HEDGES.search(sentence):
            continue
        m = _ARITH.search(sentence) or _WORD_ARITH.search(sentence)
        if m:
            expression = m.group("e")
            for word, op in (("multiplied by", "*"), ("divided by", "/"), ("times", "*"), ("plus", "+"), ("minus", "-"), ("over", "/")):
                expression = re.sub(r"\s+%s\s+" % word, " %s " % op, expression)
            expression = expression.replace("x", "*").replace("×", "*").replace("÷", "/").replace("^", "**").replace(",", "")
            claims.append({"type": "numeric", "text": sentence, "data": {"expression": re.sub(r"\s+", "", expression), "value": _as_number(m.group("v"))}})
            continue
        m = _UNIT.search(sentence)
        if m:
            claims.append({"type": "unit", "text": sentence, "data": {"value": _as_number(m.group("v")), "from_unit": m.group("a").lstrip("°"), "to_unit": m.group("b").lstrip("°"),
                                                                        "result_value": _as_number(m.group("r"))}})
            continue
        m = _WEEKDAY.search(sentence)
        if m:
            claims.append({"type": "date", "text": sentence, "data": {"kind": "weekday", "date": m.group("d"), "weekday": m.group("w")}})
            continue
        m = _LEAP.search(sentence)
        if m:
            claims.append({"type": "date", "text": sentence, "data": {"kind": "leap_year", "year": int(m.group("y")), "leap": (m.group("w") is not None) and not m.group("n")}})
            continue
        entities = []
        for found in _CAPITALISED.findall(sentence):
            words = found.split()
            while words and words[0] in _STOP_ENTITIES:                    # "The Eiffel Tower" is "Eiffel Tower"
                words = words[1:]
            if words and " ".join(words) not in entities:
                entities.append(" ".join(words))
        numbers = [m.group(0).strip() for m in _FACT_NUMBER.finditer(sentence)]
        if entities and numbers and not re.search(r"\b(should|must|please|try|use|consider)\b", sentence, re.I):
            claims.append({"type": "fact", "text": sentence, "data": {"entities": entities[:4], "facts": numbers[:4]}})
    return {"claims": claims}


def anchor_claims(text, claims, snap=0.75):
    """what a model returned, made safe: claims with the wrong shape are dropped; a claim whose text is a verbatim span of the source stays; a claim whose text is a slightly different wording is snapped
    to the sentence of the source it is most like (ratio >= snap); anything else is dropped as invented. Duplicates go. Returns {"claims", "dropped": [{claim, reason}], "snapped": n}."""
    import difflib
    sentences = [s.strip() for s in _SENTENCE.split(str(text).strip()) if s.strip()]
    kept, dropped, snapped, seen = [], [], 0, set()
    for claim in (claims if isinstance(claims, list) else []):
        problems = validate_claim(claim)
        if problems:
            dropped.append({"claim": claim, "reason": "; ".join(problems)})
            continue
        claim = {"type": claim["type"], "text": claim["text"].strip(), "data": claim["data"]}
        if checks.quote_in_source(claim["text"], text)["status"] != "pass":
            wording = _norm_text(claim["text"])
            ratio, best = max(((difflib.SequenceMatcher(None, wording, _norm_text(s)).ratio(), s) for s in sentences), default=(0.0, ""))
            if ratio < snap:
                dropped.append({"claim": claim, "reason": "its text is not in the source (closest sentence %.0f%% alike)" % (100 * ratio)})
                continue
            claim["text"], snapped = best, snapped + 1
        key = json.dumps([claim["type"], claim["text"], claim["data"]], sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            kept.append(claim)
    return {"claims": kept, "dropped": dropped, "snapped": snapped}


FUNCTIONS = {"extract_claims_rules": extract_claims_rules, "anchor_claims": anchor_claims}
