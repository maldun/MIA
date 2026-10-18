"""
Behaviour rules (ui/REQUIREMENTS_CORE.md 13a, BF1 to BF3): unwanted behaviour is detected by code, recorded as a signal in the run log, and repaired silently where a repair is certain, instead of
scolding the model in the conversation (the old "penalties" were messages that became part of its memory).

The first rules come from the very first message that MIA was given (communicator.EMOTION_QUESTION), because her voice reads the text aloud:
  speech.no_bold              no **bold** markup: emphasis cannot be spoken
  speech.no_emphasis          no *emphasis* with single asterisks (asterisks are for short actions like *smiles*, not for emphasis)
  speech.times_not_asterisk   multiplication is written as the word "times": 2 * 3 would be read as markup
  speech.sparing_actions      at most MAX_ACTIONS actions in asterisks per message
  speech.no_stage_directions  talk, do not describe what you do: no "I smile and say" and no (smiles) in brackets

A rule has a detector (text -> violations with the span of each), a severity, a description of the wanted behaviour and, where the repair is deterministic, a repair. Code spans (`...`) and fenced
code blocks are never touched. check_text() finds violations, repair_text() repairs what can be repaired and says what remains (for example a narrated action needs the model: a retry that names the rule),
record_signals() writes one line per violation to the run log. The library describes every rule as a node (library/nodes/rule.*) so that a skill can list the rules it is held to.
"""
import re

MAX_ACTIONS = 2

ACTION_STEMS = ("smil", "laugh", "wave", "nod", "sigh", "giggl", "blush", "tilt", "wink", "shrug", "grin", "bow", "clap", "point", "look", "think", "ponder", "scratch", "chuckl", "blink", "gasp",
                "cough", "clear", "lean", "hug", "tap", "fidget", "paus", "hum", "whisper", "stretch", "yawn", "danc", "spin", "jump", "rais", "shak", "cross", "fold", "adjust", "tuck", "pout",
                "sniff", "frown", "stare", "glanc", "smirk", "snicker", "wiggl", "hop", "turn", "step", "sit", "stand", "twirl", "salut", "curtsy", "facepalm", "cheer", "beam", "squint")
_ACTIONS = "|".join(ACTION_STEMS)

_CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)
_BOLD = re.compile(r"(?<![\w*])\*\*(?=\S)(.+?)(?<=\S)\*\*(?![\w*])", re.S)       # not x**2 + y**2 (a power); __bold__ is not handled: it cannot be told from __init__
_SINGLE = re.compile(r"(?<![\w*])\*(?!\*)(?=\S)([^*\n]{1,60}?)(?<=\S)\*(?![\w*])")
_TIMES = re.compile(r"(?<=\d)[ \t]*(?<![*])\*(?![*])[ \t]*(?=\d)")
_NARRATION = re.compile(r"(?:(?<=[.!?])[ \t]+|(?<=\n)[ \t]*|^[ \t]*)(I (?:smile|wave|nod|laugh|giggle|blush|sigh|shrug|grin|wink|bow|clap|chuckle|blink|gasp|cough|clear my throat|tilt my head|lean in|"
                        r"take a (?:deep )?breath|give you a (?:wink|smile|hug))\b)")
_BRACKETED = re.compile(r"[ \t]*[(\[](?:smil|laugh|wav|nod|sigh|giggl|blush|wink|grin|shrug|chuckl|clears? throat|tilts? head|paus|whisper|gasp|hugs?|bow|clap|smirk)[^)\]\n]{0,40}[)\]]", re.I)


# --- helpers --------------------------------------------------------------------------------------------------------------------------------------

def _masked(text):
    """the text with code spans blanked out (same length), so that detectors never look inside code"""
    return _CODE.sub(lambda m: " " * len(m.group(0)), text)


def _outside_code(text, function):
    """applies `function` to every stretch of the text that is not code"""
    out, last = [], 0
    for m in _CODE.finditer(text):
        out.append(function(text[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(function(text[last:]))
    return "".join(out)


def _is_action(content):
    first = content.strip().split()[0].lower() if content.strip() else ""
    return any(first.startswith(stem) for stem in ACTION_STEMS) and re.match(r"^[a-z']+$", first) is not None


def _spans(text):
    """the single-asterisk spans of the text with their kind: [(start, end, content, is_action)]"""
    return [(m.start(), m.end(), m.group(1), _is_action(m.group(1))) for m in _SINGLE.finditer(_masked(text))]


def _keep_edges(original, repaired):
    """a repair that cuts out a stretch must not leave a stray space or line break at an end where the original had none"""
    if original[:1] and not original[:1].isspace():
        repaired = repaired.lstrip()
    if original[-1:] and not original[-1:].isspace():
        repaired = repaired.rstrip()
    return repaired


def _tidy(text):
    """after something was cut out: no space before punctuation, no double spaces, no space at the end of a line"""
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"[ \t]+([.,;:!?])", r"\1", text)
    return re.sub(r"[ \t]+\n", "\n", text).strip(" \t") if "\n" not in text else re.sub(r"[ \t]+\n", "\n", text)


# --- the detectors ---------------------------------------------------------------------------------------------------------------------------------

def detect_bold(text):
    return [{"start": m.start(), "end": m.end(), "match": m.group(0), "detail": "bold markup cannot be spoken: just say it"} for m in _BOLD.finditer(_masked(text))]


def detect_emphasis(text):
    return [{"start": s, "end": e, "match": text[s:e], "detail": "emphasis with asterisks cannot be spoken; use plain words (asterisks are only for short actions)"}
            for s, e, content, action in _spans(text) if not action]


def detect_times(text):
    return [{"start": m.start(), "end": m.end(), "match": text[m.start():m.end()], "detail": 'write "times" instead of the asterisk'} for m in _TIMES.finditer(_masked(text))]


def detect_actions(text):
    actions = [(s, e) for s, e, content, action in _spans(text) if action]
    return [{"start": s, "end": e, "match": text[s:e], "detail": "more than %d actions in one message: use them sparingly" % MAX_ACTIONS} for s, e in actions[MAX_ACTIONS:]]


def detect_stage_directions(text):
    masked = _masked(text)
    looking = re.sub(r"\*+", lambda m: " " * len(m.group(0)), masked)             # markup does not hide the start of a sentence: **Wow!** I smile.
    found = [{"start": m.start(1), "end": m.end(1), "match": m.group(1), "detail": "do not describe what you do in the text: talk"} for m in _NARRATION.finditer(looking)]
    found += [{"start": m.start(), "end": m.end(), "match": m.group(0).strip(), "detail": "a stage direction in brackets is not spoken text"} for m in _BRACKETED.finditer(masked)]
    return sorted(found, key=lambda v: v["start"])


# --- the repairs (only where the result is certain) ---------------------------------------------------------------------------------------

def repair_bold(text):
    return _outside_code(text, lambda part: _BOLD.sub(lambda m: m.group(1), part))


def repair_emphasis(text):
    def fix(part):
        return _SINGLE.sub(lambda m: m.group(0) if _is_action(m.group(1)) else m.group(1), part)
    return _outside_code(text, fix)


def repair_times(text):
    return _outside_code(text, lambda part: _TIMES.sub(" times ", part))


def repair_actions(text):
    """keeps the first MAX_ACTIONS actions and removes the others"""
    spans = [(s, e) for s, e, content, action in _spans(text) if action][MAX_ACTIONS:]
    original = text
    for s, e in reversed(spans):
        text = _tidy(text[:s].rstrip(" \t") + " " + text[e:].lstrip(" \t")) if text[:s].strip() else text[e:].lstrip(" \t")
    return _keep_edges(original, text)


def repair_stage_directions(text):
    """removes directions in brackets; a narrated action ('I smile and say') cannot be repaired by code and stays"""
    return _keep_edges(text, _outside_code(text, lambda part: _tidy(_BRACKETED.sub("", part))))


class Rule:
    def __init__(self, name, title, severity, wanted, detect, repair=None, bad=(), good=()):
        self.name, self.title, self.severity, self.wanted, self.detect, self.repair = name, title, severity, wanted, detect, repair
        self.bad, self.good = list(bad), list(good)


RULES = {r.name: r for r in (
    Rule("speech.no_bold", "No bold markup in speech", "warn", "Say what is important in plain words; bold cannot be spoken.", detect_bold, repair_bold,
         ["This is **really** important.", "**Note:** it closes at five."], ["This is really important.", "Note: it closes at five."]),
    Rule("speech.no_emphasis", "No emphasis with asterisks", "warn", "Asterisks are only for short actions such as *smiles*; never for emphasis.", detect_emphasis, repair_emphasis,
         ["That is *very* kind of you."], ["That is very kind of you.", "*smiles* That is kind of you."]),
    Rule("speech.times_not_asterisk", 'Say "times", do not write an asterisk', "warn", 'Write the word "times" for multiplication: 2 times 3, not 2*3.', detect_times, repair_times,
         ["2*3 is 6", "12 * 1.5 + 3"], ["2 times 3 is 6", "12 times 1.5 plus 3"]),
    Rule("speech.sparing_actions", "Few actions in asterisks", "info", "At most %d actions like *waves* in one message." % MAX_ACTIONS, detect_actions, repair_actions,
         ["*smiles* Hi! *waves* Look, *nods* really, *giggles* ok."], ["*smiles* Hi! *waves* Look, really, ok."]),
    Rule("speech.no_stage_directions", "Talk, do not narrate", "warn", "Do not describe what you are doing in the text: say the words, and use an *action* if it must be shown.", detect_stage_directions,
         repair_stage_directions, ["I smile and say hello.", "Hello! (smiles)"], ["Hello!", "*smiles* Hello!"]),
)}
# the order in which repairs are applied: what removes text first, then markup
REPAIR_ORDER = ("speech.no_stage_directions", "speech.no_bold", "speech.times_not_asterisk", "speech.no_emphasis", "speech.sparing_actions")


# --- using the rules ------------------------------------------------------------------------------------------------------------------------------

def _selected(rules):
    names = list(RULES) if rules is None else [r for r in rules if r in RULES]
    return [RULES[n] for n in names]


def check_text(text, rules=None):
    """{"violations": [{rule, severity, start, end, match, detail}], "rules": [names that fired]} for the (default all) rules"""
    text = text if isinstance(text, str) else ""
    violations = []
    for rule in _selected(rules):
        for found in rule.detect(text):
            violations.append(dict(found, rule=rule.name, severity=rule.severity))
    violations.sort(key=lambda v: (v["start"], v["rule"]))
    return {"violations": violations, "rules": sorted({v["rule"] for v in violations})}


def repair_text(text, rules=None, max_rounds=4):
    """{"text", "changed", "fixed": [rules whose violations were repaired], "remaining": [rules that still fire after the repairs]}: silent repair of what code can repair with certainty"""
    text = text if isinstance(text, str) else ""
    wanted = {r.name for r in _selected(rules)}
    before = check_text(text, wanted)["rules"]
    current = text
    for _ in range(max_rounds):
        changed = False
        for name in REPAIR_ORDER:
            rule = RULES[name]
            if name in wanted and rule.repair and rule.detect(current):
                repaired = rule.repair(current)
                if repaired != current:
                    current, changed = repaired, True
        if not changed:
            break
    after = check_text(current, wanted)["rules"]
    return {"text": current, "changed": current != text, "fixed": [r for r in before if r not in after], "remaining": after}


def record_signals(run_log, run_id, text, node=None, rules=None):
    """one line in the run log per violation (a penalty signal with the rule, the span and what to do); returns the violations. Never raises: logging must not break an answer"""
    try:
        found = check_text(text, rules)["violations"]
        for v in found:
            run_log.add_signal(run_id, v["rule"], "penalty", node=node, detail=v["detail"], span=[v["start"], v["end"]], text=v["match"][:80], severity=v["severity"])
        return found
    except Exception:
        return []


def describe():
    """the rules as data (the library nodes rule.* are made from this and a test keeps them equal)"""
    return [{"name": r.name, "title": r.title, "severity": r.severity, "wanted": r.wanted, "repairable": r.repair is not None, "bad": r.bad, "good": r.good} for r in RULES.values()]


def apply_rules(text, rules=None, repair=True):
    """for pipelines: {"text": the text (repaired when asked), "violations": [...], "remaining": [...], "fixed": [...]}"""
    found = check_text(text, rules)
    if not repair:
        return {"text": text, "violations": found["violations"], "remaining": found["rules"], "fixed": []}
    fixed = repair_text(text, rules)
    return {"text": fixed["text"], "violations": found["violations"], "remaining": fixed["remaining"], "fixed": fixed["fixed"]}


FUNCTIONS = {"apply_rules": apply_rules}
