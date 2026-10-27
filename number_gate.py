"""
The code part of the verification gate verify.number_gate@1 (specs/number-gate: REQ-GATE-001 to REQ-GATE-006, IF-003). The gate is a library pipeline; the decisions that must
not depend on a model are made here, in plain functions:

  gate_prepare(given)        the route of a claim and the evidence cut to EVIDENCE_LIMIT characters: "abstain" (a number and no evidence: REQ-GATE-006), "single" (no
                             number: as the current release, REQ-GATE-004, or style single) or "cops" (the default for a claim with a number)
  run_number_check(c, e)     checks.number_check, logged as a check_run event when it ran (REQ-GATE-001)
  gate_evidence(plan, check) the evidence the judgement steps see: the line of the check result first, then the evidence (REQ-GATE-002, -003); used by verify.number_gate@1
                             and by the style single; gate_check_line gives the line alone, for the prompts of verify.number_gate@2 that keep it outside the evidence
  gate_record(...)           the result record of IF-003 from the tally of the judgement style
  gate_abstain(plan)         the same record when nobody was asked
  limits_of(...)             the limits of a result, made by code (REQ-WFM-023, NFR-4): a list of {code, text}; gate_record_limits and gate_abstain_limits are the records of
                             verify.number_gate@5, which carry them (the older versions keep their record)
"""
import re
import time

try:
    from . import checks
    from . import events as ev
except ImportError:  # used as plain script / in tests
    import checks
    import events as ev

EVIDENCE_LIMIT = 4000
STYLES = ("cops", "single")
EVENT_RESULT = {"pass": "pass", "fail": "fail", "inconclusive": "skipped"}       # the vocabulary of the check_run event
CALLS = {"abstain": 0, "single": 1, "cops": 3}


def gate_prepare(given):
    """given: the input of the run {claim, evidence, style (optional)}"""
    claim, evidence, style = str(given.get("claim", "")), str(given.get("evidence") or ""), given.get("style") or "cops"
    if style not in STYLES:
        raise ValueError("style must be one of %s, not %r" % (", ".join(STYLES), style))
    numbered = bool(re.search(r"\d", claim))
    if not numbered:
        route = "single"
    elif not evidence.strip():
        route = "abstain"
    else:
        route = style
    shown = defang(evidence)
    return {"route": route, "numbered": numbered, "evidence": shown[:EVIDENCE_LIMIT], "cut": len(shown) > EVIDENCE_LIMIT, "started": time.monotonic()}


def defang(evidence):
    """the prompts of verify.number_gate@2 quote the evidence between <<<EVIDENCE and EVIDENCE>>>; the evidence must not be able to close that block itself (THR-001)"""
    return evidence.replace("<<<", "<<").replace(">>>", ">>")


def run_number_check(claim, evidence):
    outcome = checks.number_check(claim, evidence)
    if outcome["status"] != checks.NOT_APPLICABLE:
        ev.emit("check_run", {"name": "number_check", "target": str(claim)[:380], "result": EVENT_RESULT[outcome["status"]], "detail": "%s: %s" % (outcome["status"], outcome["detail"])[:380]})
    return outcome


def check_line(check):
    """the line of a check result for the judge; none when the check did not apply"""
    if check["status"] == checks.NOT_APPLICABLE:
        return ""
    line = "Number check: %s - %s" % (check["status"], check["detail"])
    if check["status"] == checks.FAIL:
        line += ". Code found a contradiction between the claim and the evidence."
    return line


def gate_check_line(check):
    """the line of the check result as a value of its own, outside the evidence block (verify.number_gate@2)"""
    return check_line(check) or "not run (the claim has no number to compare)"


def gate_evidence(plan, check):
    line = check_line(check)
    return "%s\n\n---\n%s" % (line, plan["evidence"]) if line else plan["evidence"]


def _record(plan, tally, check_status):
    return dict(tally, calls=CALLS[plan["route"]], seconds=round(time.monotonic() - plan["started"], 3), facts=[], number_check=check_status)


def gate_record(plan, check, verdict):
    return _record(plan, verdict, check["status"])


def gate_abstain(plan):
    tally = {"status": "inconclusive", "verdict": "unclear", "agreement": 0.0, "counts": {"supported": 0, "refuted": 0, "unclear": 0},
             "reasons": ["a claim with a number and no evidence is not decided"], "detail": "no evidence: the gate does not guess"}
    return _record(plan, tally, checks.NOT_APPLICABLE)


def limits_of(plan, check_status, tally):
    """what a reader must know about a result (REQ-WFM-023): only what code can see here: the evidence came with the claim and was not checked against a source, how much of it
    was used, whether the number check could compare, and what stands behind the verdict. Sources, fetch failures and dates belong to the
    pipelines that retrieve sources."""
    if plan["route"] == "abstain":
        return [{"code": "no_evidence", "text": "no evidence given: no verdict"}]
    limits = [{"code": "evidence_unchecked", "text": "the evidence was given with the claim; it was not checked against a source"}]
    if plan.get("cut"):
        limits.append({"code": "evidence_cut", "text": "the evidence was cut to %d characters" % EVIDENCE_LIMIT})
    if not plan["numbered"]:
        limits.append({"code": "no_number_check", "text": "no number check: the claim has no number"})
    elif check_status == checks.INCONCLUSIVE:
        limits.append({"code": "number_check_inconclusive", "text": "the number check could not compare the numbers of the claim with the evidence"})
    # the tally holds one vote in both styles (the judge's ruling, or the single voice), so an "agreement" of 1.0 would suggest a confidence that nothing backs
    basis = {"cops": "the verdict is the ruling of one judge after the arguments for and against; no vote count stands behind it",
             "single": "the verdict is the answer of one model voice; no vote count stands behind it"}[plan["route"]]
    limits.append({"code": "confidence_basis", "text": basis + "; it is not calibrated"})
    limits.append({"code": "judged_by", "text": "judged by the %s style on one model" % plan["route"]})
    return limits


def gate_record_limits(plan, check, verdict):
    return dict(_record(plan, verdict, check["status"]), limits=limits_of(plan, check["status"], verdict))


def gate_abstain_limits(plan):
    record = gate_abstain(plan)
    return dict(record, limits=limits_of(plan, checks.NOT_APPLICABLE, record))


FUNCTIONS = {"gate_prepare": gate_prepare, "run_number_check": run_number_check, "gate_check_line": gate_check_line, "gate_evidence": gate_evidence, "gate_record": gate_record, "gate_abstain": gate_abstain,
             "gate_record_limits": gate_record_limits, "gate_abstain_limits": gate_abstain_limits}
