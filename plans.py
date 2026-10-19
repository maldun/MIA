"""
Plans of research questions (ui/REQUIREMENTS_CORE.md 13b ST10 to ST13): the two forms of a plan, the checks of a typed plan, and the scoring of a plan against what a good plan for the question must have.

A free plan (research.decompose):   {"subquestions": [{"id", "question", "query"}], "needs_calculation": bool, "single": bool}
A typed plan (ST10):                {"steps": [{"id", "op", "attribute", "entity"} | {"id", "op", "args": [..]}], "answer": "#n"}
                                    ops: lookup (attribute of an entity or of the result #n of an earlier step) and, done by code, difference, compare, weekday, days_between, years_between, add_days

The gold of a case (what code can test about a plan):
  {"lookups": [min, max],              how many lookups a good plan has
   "cover": [[alternatives], ...],     every group needs one of its alternatives somewhere in the plan (the words of the question that must not get lost)
   "must_not": [phrases],              none of them may be asked (a known drift: "the name of the Tarn Museum")
   "verbatim": true,                   a single free lookup keeps the question's own words
   "dependent": true,                  a lookup needs the result of another (typed plans can say so)
   "ops": ["difference", ...]}         operations the answer needs (typed plans; for free plans only whether a calculation is needed is checked)
"""
import re

OPS = {"lookup": 0, "difference": 2, "compare": 2, "weekday": 1, "days_between": 2, "years_between": 2, "add_days": 2}
CODE_OPS = tuple(op for op in OPS if op != "lookup")
_STOP = {"the", "and", "for", "are", "was", "were", "how", "what", "when", "who", "does", "did", "has", "have", "with", "from", "that", "this", "which", "into", "than", "then", "its", "his", "her",
         "can", "you", "your", "our", "not", "but", "any", "all", "one", "of", "is", "in", "on", "at", "a", "an", "to", "by", "or"}


def _words(text):
    return {w for w in re.findall(r"[^\W_]+", str(text).casefold()) if w not in _STOP and len(w) > 1}


def _plain(text):
    return " ".join(re.findall(r"[^\W_]+", str(text).casefold()))


def is_typed(plan):
    return isinstance(plan, dict) and isinstance(plan.get("steps"), list)


def plan_items(plan):
    """[{"id", "kind": lookup | op, "text", "refs": [#n], "op"}] of a free or a typed plan; [] for anything else"""
    items = []
    if is_typed(plan):
        for step in plan["steps"]:
            if not isinstance(step, dict):
                continue
            op = step.get("op")
            if op == "lookup":
                entity = str(step.get("entity", ""))
                items.append({"id": step.get("id"), "kind": "lookup", "op": op, "text": "%s of %s" % (step.get("attribute", ""), entity), "refs": [entity] if entity.startswith("#") else []})
            else:
                args = [str(a) for a in step.get("args", [])] if isinstance(step.get("args"), list) else []
                items.append({"id": step.get("id"), "kind": "op", "op": op, "text": "%s %s" % (op, " ".join(args)), "refs": [a for a in args if a.startswith("#")]})
    elif isinstance(plan, dict) and isinstance(plan.get("subquestions"), list):
        for sub in plan["subquestions"]:
            if isinstance(sub, dict):
                items.append({"id": sub.get("id"), "kind": "lookup", "op": "lookup", "text": "%s %s" % (sub.get("question", ""), sub.get("query", "")), "question": str(sub.get("question", "")), "refs": []})
    return items


def typed_problems(plan):
    """problems of the structure of a typed plan (empty list = sound)"""
    if not is_typed(plan):
        return ["not a typed plan"]
    problems, seen, used = [], [], set()
    steps = plan["steps"]
    if not steps:
        return ["no steps"]
    for position, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            problems.append("step %d is not an object" % position)
            continue
        if step.get("id") != position:
            problems.append("step %d has id %r (ids must run 1, 2, 3 ...)" % (position, step.get("id")))
        op = step.get("op")
        if op not in OPS:
            problems.append("step %d: unknown operation %r" % (position, op))
            continue
        refs = []
        if op == "lookup":
            for key in ("attribute", "entity"):
                if not str(step.get(key, "")).strip():
                    problems.append("step %d: a lookup needs an %s" % (position, key))
            if str(step.get("entity", "")).startswith("#"):
                refs.append(step["entity"])
        else:
            args = step.get("args")
            if not isinstance(args, list) or len(args) != OPS[op]:
                problems.append("step %d: %s needs %d arguments" % (position, op, OPS[op]))
            else:
                refs.extend(str(a) for a in args if str(a).startswith("#"))
        for ref in refs:
            match = re.fullmatch(r"#(\d+)", ref)
            if not match or int(match.group(1)) not in seen:
                problems.append("step %d: %r refers to a step that does not come before" % (position, ref))
            else:
                used.add(int(match.group(1)))
        seen.append(position)
    answer = plan.get("answer")
    match = re.fullmatch(r"#(\d+)", str(answer))
    if not match or int(match.group(1)) not in seen:
        problems.append("the answer must be the result of a step (#n)")
    else:
        used.add(int(match.group(1)))
        # every step must lead to the answer: walk back from it
        reached, todo = set(), [int(match.group(1))]
        while todo:
            n = todo.pop()
            if n in reached or not 1 <= n <= len(steps) or not isinstance(steps[n - 1], dict):
                continue
            reached.add(n)
            step = steps[n - 1]
            for ref in ([step.get("entity")] if step.get("op") == "lookup" else step.get("args") or []):
                m = re.fullmatch(r"#(\d+)", str(ref))
                if m:
                    todo.append(int(m.group(1)))
        for n in seen:
            if n not in reached:
                problems.append("step %d is not used by the answer" % n)
    return problems


def _redundant(items):
    lookups = [i for i in items if i["kind"] == "lookup"]
    for index, a in enumerate(lookups):
        for b in lookups[index + 1:]:
            wa, wb = _words(a["text"]), _words(b["text"])
            if wa and wb and len(wa & wb) / len(wa | wb) >= 0.8:
                return [a["text"], b["text"]]
    return None


def score_plan(plan, gold, question):
    items = plan_items(plan)
    if not items:
        return {"ok": False, "shape": False}
    typed = is_typed(plan)
    lookups = [i for i in items if i["kind"] == "lookup"]
    text = _plain(" ".join(i["text"] for i in items))
    low, high = gold.get("lookups", [1, 4])
    missing = [group for group in gold.get("cover", []) if not any(_plain(alt) in text for alt in group)]
    drift = [phrase for phrase in gold.get("must_not", []) if _plain(phrase) in text]
    duplicate = _redundant(items)
    score = {"shape": True, "typed": typed, "lookups": len(lookups), "n_ok": low <= len(lookups) <= high, "coverage_ok": not missing, "missing": missing, "drift_ok": not drift, "drift": drift,
             "redundancy_ok": duplicate is None, "duplicate": duplicate}
    score["verbatim_ok"] = (_plain(items[0]["question"]) == _plain(question)) if gold.get("verbatim") and not typed and len(lookups) == 1 else None
    if typed:
        problems = typed_problems(plan)
        score["structure_ok"], score["problems"] = not problems, problems
        score["dependent_ok"] = any(i["refs"] for i in lookups) if gold.get("dependent") else None
        wanted = set(gold.get("ops", []))
        score["ops_ok"] = wanted <= {i["op"] for i in items if i["kind"] == "op"} if wanted else None
        score["calculation_ok"] = None
    else:
        score["structure_ok"] = score["dependent_ok"] = score["ops_ok"] = None
        score["calculation_ok"] = bool(plan.get("needs_calculation")) == any(op in CODE_OPS for op in gold.get("ops", [])) if "ops" in gold else None
    checks = ("n_ok", "coverage_ok", "drift_ok", "redundancy_ok", "verbatim_ok", "structure_ok", "dependent_ok", "ops_ok", "calculation_ok")
    score["ok"] = all(score[k] is not False for k in checks)
    return score
