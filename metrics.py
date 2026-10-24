"""
The numbers of the evaluation (ui/REQUIREMENTS_CORE.md 9, EL3 to EL5), without any dependency. A *record* is the result of one case in one run:

  {"case": id, "repeat": 0, "tags": [...], "status": "pass" | "fail" | "open" | "not_applicable" | "error:...", "expect": status or None, "truth": True | False | None,
   "seconds": float, "calls": int, "chars_in": int, "chars_out": int}

`truth` says whether the claim of the case is actually correct (what a verifier should find out); `expect` is the exact behaviour a regression test wants (for example that a near match
stays `open`). The metrics for verifiers follow the questions of the research notes: how often is a pass wrong (false pass), how often a fail (false fail), how much is decided at all
(coverage), and how sure can one be with so few cases (Wilson intervals; with 30 cases the intervals are wide, and that is part of the result).
"""
import hashlib
import math
import unicodedata
from collections import defaultdict

OPEN = "open"
ABSTAIN_STATUSES = ("open", "inconclusive", "not_applicable", "none")


def normalize_status(status):
    status = str(status)
    return OPEN if status in ("inconclusive", "none") else status


def decision(status):
    """pass | fail | abstain: what a verifier decided, whatever it called its doubts"""
    status = normalize_status(status)
    return status if status in ("pass", "fail") else "abstain"


def wilson(successes, total, z=1.96):
    """the 95 percent interval of a proportion (better than the plain formula for small numbers and for 0 % or 100 %)"""
    if total <= 0:
        return (0.0, 1.0)
    p = successes / total
    centre = p + z * z / (2 * total)
    spread = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
    denominator = 1 + z * z / total
    return (max(0.0, (centre - spread) / denominator), min(1.0, (centre + spread) / denominator))


def rate(successes, total):
    """{"k", "n", "rate", "low", "high"}; rate is None for n = 0"""
    low, high = wilson(successes, total)
    return {"k": successes, "n": total, "rate": successes / total if total else None, "low": low if total else None, "high": high if total else None}


def sign_test(only_a, only_b):
    """two-sided exact p value for 'a and b are equally good' from the cases in which only a was right (only_a) and only b was right (only_b)"""
    n = only_a + only_b
    if n == 0:
        return 1.0
    k = min(only_a, only_b)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def verification_metrics(records):
    """for the records that have a `truth`: confusion of decisions against truth and the rates that matter for a verifier"""
    labelled = [r for r in records if r.get("truth") is not None]
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "abstain_true": 0, "abstain_false": 0}
    for r in labelled:
        d = decision(r["status"])
        if d == "pass":
            counts["tp" if r["truth"] else "fp"] += 1
        elif d == "fail":
            counts["tn" if not r["truth"] else "fn"] += 1
        else:
            counts["abstain_true" if r["truth"] else "abstain_false"] += 1
    n = len(labelled)
    true_n = sum(1 for r in labelled if r["truth"])
    false_n = n - true_n
    decided = counts["tp"] + counts["fp"] + counts["tn"] + counts["fn"]
    correct = counts["tp"] + counts["tn"]
    return {
        "n": n, "true_claims": true_n, "false_claims": false_n, "counts": counts,
        "coverage": rate(decided, n),                                                    # share of claims on which a decision was made
        "accuracy_decided": rate(correct, decided),                                      # right among the decided
        "accuracy_overall": rate(correct, n),                                            # abstaining counts as not right
        "false_pass": rate(counts["fp"], false_n),                                       # a wrong claim that passed: the dangerous error
        "false_fail": rate(counts["fn"], true_n),                                        # a right claim that was refuted
        "precision_pass": rate(counts["tp"], counts["tp"] + counts["fp"]),
        "precision_fail": rate(counts["tn"], counts["tn"] + counts["fn"]),
        "abstain_rate": rate(n - decided, n),
        "errors": rate(sum(1 for r in labelled if str(r["status"]).startswith("error")), n),
    }


def match_metrics(records):
    """for the records that have an `expect`: how many behave exactly as expected"""
    expected = [r for r in records if r.get("expect") is not None]
    matched = [r for r in expected if normalize_status(r["status"]) == normalize_status(r["expect"])]
    return {"n": len(expected), "match": rate(len(matched), len(expected)), "mismatches": [r for r in expected if r not in matched]}


def is_right(record):
    """did the record do what the case asked: the expected status if there is one, else the right decision for the truth"""
    if record.get("expect") is not None:
        return normalize_status(record["status"]) == normalize_status(record["expect"])
    if record.get("truth") is not None:
        return decision(record["status"]) == ("pass" if record["truth"] else "fail")
    return None


def breakdown(records, by="tags"):
    """per tag: the number of records, how many were right, the interval"""
    groups = defaultdict(list)
    for r in records:
        for tag in (r.get(by) or ["(none)"]):
            groups[tag].append(r)
    table = {}
    for tag, items in groups.items():
        judged = [r for r in items if is_right(r) is not None]
        table[tag] = rate(sum(1 for r in judged if is_right(r)), len(judged))
    return dict(sorted(table.items()))


def extraction_metrics(records):
    """for the records that carry a `score` (extraction.score_extraction): micro precision and recall over all claims, F1, the cases that are perfect, and the problems counted by kind.
    Texts without any gold claim are 'empty' cases: a claim there is an invented claim."""
    scored = [r for r in records if isinstance(r.get("score"), dict) and "gold" in r["score"]]
    gold = sum(r["score"]["gold"] for r in scored)
    predicted = sum(r["score"]["predicted"] for r in scored)
    matched = sum(r["score"]["matched"] for r in scored)
    precision, recall = rate(matched, predicted), rate(matched, gold)
    p, q = precision["rate"], recall["rate"]
    empty = [r for r in scored if r["score"]["gold"] == 0]
    kinds = {k: sum(len(r["score"].get(k, [])) for r in scored) for k in ("missed", "wrong_data", "wrong_type", "spurious", "duplicates", "unanchored", "invalid")}
    return {"cases": len(scored), "gold": gold, "predicted": predicted, "matched": matched, "precision": precision, "recall": recall,
            "f1": None if not p or not q else 2 * p * q / (p + q), "perfect": rate(sum(1 for r in scored if r["score"]["ok"]), len(scored)),
            "empty_cases": len(empty), "empty_clean": rate(sum(1 for r in empty if r["score"]["predicted"] == 0), len(empty)),
            "unanchored": rate(kinds["unanchored"], predicted), "problems": kinds}


def rule_metrics(records):
    """for the records that carry a rule `score` ({"expected": [rules], "found": [rules], "repair_ok", "idempotent", ...}): per rule how often it fired rightly (tp), wrongly (fp) or not when it should (fn),
    the rate of false alarms on texts that are clean, and how good and how safe the repairs are"""
    scored = [r for r in records if isinstance(r.get("score"), dict) and "found" in r["score"]]
    table = {}
    for r in scored:
        expected, found = set(r["score"]["expected"]), set(r["score"]["found"])
        for rule in expected | found:
            row = table.setdefault(rule, {"tp": 0, "fp": 0, "fn": 0})
            row["tp" if rule in expected and rule in found else "fp" if rule in found else "fn"] += 1
    for row in table.values():
        row["precision"] = rate(row["tp"], row["tp"] + row["fp"])
        row["recall"] = rate(row["tp"], row["tp"] + row["fn"])
    clean = [r for r in scored if not r["score"]["expected"]]
    repairs = [r for r in scored if r["score"].get("repair_ok") is not None]
    return {"texts": len(scored), "rules": dict(sorted(table.items())), "clean_texts": len(clean), "clean_ok": rate(sum(1 for r in clean if not r["score"]["found"]), len(clean)),
            "repair_ok": rate(sum(1 for r in repairs if r["score"]["repair_ok"]), len(repairs)), "idempotent": rate(sum(1 for r in scored if r["score"].get("idempotent")), len(scored)),
            "remaining_ok": rate(sum(1 for r in scored if r["score"].get("remaining_ok")), len(scored))}


def plan_metrics(records):
    """for the records of a plan suite (score from plans.py): how often the plan is as it should be and, one by one, the properties that were tested (rates over the plans where the property applies)"""
    scored = [r for r in records if isinstance(r.get("score"), dict) and "n_ok" in r["score"]]
    table = {"plans": len(scored), "lookups_per_plan": sum(r["score"]["lookups"] for r in scored) / len(scored) if scored else 0.0, "ok": rate(sum(1 for r in scored if r["score"]["ok"]), len(scored))}
    for key in ("n_ok", "coverage_ok", "drift_ok", "redundancy_ok", "verbatim_ok", "structure_ok", "dependent_ok", "ops_ok", "calculation_ok"):
        applicable = [r for r in scored if r["score"].get(key) is not None]
        table[key] = rate(sum(1 for r in applicable if r["score"][key]), len(applicable))
    return table


def research_metrics(records):
    """for the records of a research suite (score from research_score.py): answers that are right (facts, sources, nothing forbidden), the rate of correct abstention on questions without an answer,
    questions that were answerable but refused, quotes that are not in their page, forbidden content (an injected command followed, a stale value) and the work done (searches and fetches per question)"""
    scored = [r for r in records if isinstance(r.get("score"), dict) and "status_ok" in r["score"]]
    answerable = [r for r in scored if r["score"]["kind"] == "answer"]
    unknown = [r for r in scored if r["score"]["kind"] == "unknown"]
    return {"questions": len(scored), "answerable": len(answerable), "unanswerable": len(unknown),
            "answers_right": rate(sum(1 for r in answerable if r["score"]["ok"]), len(answerable)),
            "facts_right": rate(sum(1 for r in answerable if r["score"]["facts_ok"]), len(answerable)),
            "abstained_right": rate(sum(1 for r in unknown if r["score"]["status_ok"]), len(unknown)),
            "refused_wrongly": rate(sum(1 for r in answerable if r["score"]["status"] == "unknown"), len(answerable)),
            "quote_not_in_page": rate(sum(1 for r in scored if r["score"]["unanchored"]), len(scored)),
            "forbidden": rate(sum(1 for r in scored if not r["score"]["forbidden_ok"]), len(scored)),
            "searches": sum(r["score"].get("searches", 0) for r in scored) / len(scored) if scored else 0.0,
            "fetches": sum(r["score"].get("fetches", 0) for r in scored) / len(scored) if scored else 0.0}


def cost(records):
    n = len(records)
    seconds = sum(r.get("seconds", 0.0) for r in records)
    return {"runs": n, "seconds": seconds, "seconds_per_run": seconds / n if n else 0.0, "calls": sum(r.get("calls", 0) for r in records),
            "chars_in": sum(r.get("chars_in", 0) for r in records), "chars_out": sum(r.get("chars_out", 0) for r in records)}


def stability(records):
    """with repeats: the share of cases whose repeats all ended in the same status (a model that gives different verdicts for the same claim is not a verifier)"""
    by_case = defaultdict(set)
    counts = defaultdict(int)
    for r in records:
        by_case[r["case"]].add(normalize_status(r["status"]))
        counts[r["case"]] += 1
    repeated = [c for c, n in counts.items() if n > 1]
    return rate(sum(1 for c in repeated if len(by_case[c]) == 1), len(repeated))


def compare(records_a, records_b):
    """paired comparison on the cases both ran: who was right where, the exact sign test, and the cases in which they differ"""
    def per_case(records):
        grouped = defaultdict(list)
        for r in records:
            verdict = is_right(r)
            if verdict is not None:
                grouped[r["case"]].append(verdict)
        return {case: sum(v) / len(v) for case, v in grouped.items()}      # with repeats: the share of right repeats
    a, b = per_case(records_a), per_case(records_b)
    shared = sorted(set(a) & set(b))
    only_a = [c for c in shared if a[c] > b[c]]
    only_b = [c for c in shared if b[c] > a[c]]
    return {"cases": len(shared), "a_right": sum(a[c] for c in shared), "b_right": sum(b[c] for c in shared), "only_a": only_a, "only_b": only_b,
            "p_value": sign_test(len(only_a), len(only_b)), "missing_in_a": sorted(set(b) - set(a)), "missing_in_b": sorted(set(a) - set(b))}


# --- stability of repeats with facts (Plan iteration 1, specs/number-gate: REQ-STAB-001, REQ-STAB-002, IF-004) ------------------------------------

def _plain(text):
    """lower case, no diacritics, single spaces: the form in which two facts are compared"""
    decomposed = unicodedata.normalize("NFKD", str(text))
    return " ".join("".join(c for c in decomposed if not unicodedata.combining(c)).casefold().split())


def _number(value):
    """the number of a fact as a float ('1,200' and 1200 are the same); text that is no number stays text"""
    try:
        return float(str(value).replace(",", "").replace(" ", ""))
    except ValueError:
        return _plain(value)


def _fact_key(fact):
    quote = hashlib.sha1(_plain(fact.get("quote", "")).encode("utf8")).hexdigest()
    return (_plain(fact.get("entity", "")), _number(fact.get("number", "")), _plain(fact.get("unit", "")), quote)


def same_facts(facts_a, facts_b):
    """True when both lists hold the same facts; a fact is {"entity", "number", "unit", "quote"}, compared by normalised parts; order and the wording of the answer are ignored"""
    return sorted(map(_fact_key, facts_a), key=repr) == sorted(map(_fact_key, facts_b), key=repr)


def case_is_stable(repeats):
    """True when all repeats of a case ({"status", "facts", ...}) have the same status and the same facts"""
    first = repeats[0]
    return all(normalize_status(r["status"]) == normalize_status(first["status"]) and same_facts(r.get("facts", []), first.get("facts", [])) for r in repeats[1:])


def repeat_lists(records):
    """{case id: [{"status", "facts"}, ...]} for the cases with at least two repeats"""
    grouped = defaultdict(list)
    for r in records:
        grouped[r["case"]].append({"status": r["status"], "facts": r.get("facts", [])})
    return {case: repeats for case, repeats in grouped.items() if len(repeats) > 1}


def stability_report(records):
    """{"n": cases with repeats, "share": share of stable cases, "low", "high": Wilson 95 % interval, "unstable": [case ids]}"""
    lists = repeat_lists(records)
    unstable = sorted(case for case, repeats in lists.items() if not case_is_stable(repeats))
    stable = len(lists) - len(unstable)
    low, high = wilson(stable, len(lists))
    return {"n": len(lists), "share": stable / len(lists) if lists else 0.0, "low": low, "high": high, "unstable": unstable}
