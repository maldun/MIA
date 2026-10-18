"""
Verification styles (ui/REQUIREMENTS_CORE.md 12.1): the code part. The styles themselves are pipelines of the library (verify.single, verify.consistency, verify.jury, verify.cops, verify.trial) built from
a few model views (what each voice says) and the functions here (what is decided by counting, never by a model):

  tally(verdicts)   votes of {"verdict": "supported" | "refuted" | "unclear", "reason", "confidence"} (one object or a list) -> the result in the vocabulary of the hard checks:
                    {"status": "pass" | "fail" | "inconclusive", "verdict", "agreement", "counts", "reasons", "detail"}. Rules: the majority of the votes that take a side wins; a tie, no vote that takes a
                    side, or fewer than half of all votes for the winner is "unclear" (inconclusive): a split jury is not a verdict. "agreement" is the share of all votes for the winner.
  sequence(n)       [0, 1, ..., n-1] (to ask the same question several times in a map node)
  experts(experts)  the experts of a jury: the given list, or the default panel (voices that look at the claim from different sides)
"""
VERDICTS = ("supported", "refuted", "unclear")
STATUS = {"supported": "pass", "refuted": "fail", "unclear": "inconclusive"}

DEFAULT_EXPERTS = [
    {"name": "fact checker", "context": "You check statements against what is well documented. You only call a claim supported when you know it is documented, and refuted when you know of a documented contradiction."},
    {"name": "sceptic", "context": "You look for what could make the claim wrong: wrong numbers, wrong names, wrong dates, a popular myth that sounds right. You say unclear when you cannot rule such an error out."},
    {"name": "domain reader", "context": "You read the claim as a specialist of its subject would: you check whether the details fit together and whether the wording means what it seems to mean."},
]


def _as_list(votes):
    if isinstance(votes, dict):
        return [votes]
    return [v for v in (votes if isinstance(votes, (list, tuple)) else [])]


def tally(verdicts):
    votes = []
    for vote in _as_list(verdicts):
        word = str(vote.get("verdict", "")).strip().lower() if isinstance(vote, dict) else ""
        votes.append({"verdict": word if word in VERDICTS else "unclear", "reason": str(vote.get("reason", "")) if isinstance(vote, dict) else "",
                      "confidence": vote.get("confidence") if isinstance(vote, dict) else None})
    counts = {name: sum(1 for v in votes if v["verdict"] == name) for name in VERDICTS}
    total = len(votes)
    sides = {name: counts[name] for name in ("supported", "refuted")}
    best = max(sides.values()) if total else 0
    leaders = [name for name, n in sides.items() if n == best and n > 0]
    if total and len(leaders) == 1 and best * 2 >= total:
        verdict = leaders[0]
    else:
        verdict = "unclear"
    agreement = round(counts[verdict] / total, 3) if total else 0.0
    if not total:
        detail = "no votes"
    elif verdict == "unclear" and len(leaders) == 2:
        detail = "the votes are split (%d supported, %d refuted, %d unclear): no verdict" % (counts["supported"], counts["refuted"], counts["unclear"])
    elif verdict == "unclear":
        detail = "no side has the majority (%d supported, %d refuted, %d unclear)" % (counts["supported"], counts["refuted"], counts["unclear"])
    else:
        detail = "%d of %d votes %s" % (counts[verdict], total, verdict)
    return {"status": STATUS[verdict], "verdict": verdict, "agreement": agreement, "counts": counts, "reasons": [v["reason"] for v in votes if v["reason"]], "detail": detail}


def sequence(n):
    try:
        count = int(n)
    except (TypeError, ValueError):
        count = 0
    return list(range(max(0, min(count, 20))))


def experts(experts=None):
    given = [e for e in (experts if isinstance(experts, (list, tuple)) else []) if isinstance(e, dict) and e.get("context")]
    return [dict(e) for e in (given or DEFAULT_EXPERTS)]


FUNCTIONS = {"tally": tally, "sequence": sequence, "experts": experts}
