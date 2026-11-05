"""Throwaway spike (a) of the skill rework: verify.cops and verify.jury as DEBATES (several rounds) on the 12B.
Not an eval run; the claims are the spike's own (spike cases are not eval cases, truth set by the coding agent for
this spike only). Standard library only.
usage: python3 -I debate_spike.py OUTFILE.jsonl [REPEATS=3]
Variants: single (one call), cops (pro and con rebut each other, a judge may end after any round),
jury (3 experts vote, those who disagree see the others' reasons and may change; up to the round cap).
Caps (owner's numbers, configuration values): 3 rounds, 12 calls, 300 s per debate."""
import json, sys, time, urllib.request

HOST, MODEL, CTX = "http://127.0.0.1:11434", "gemma4:12b-it-qat", 8192
MAX_ROUNDS, MAX_CALLS, MAX_SECONDS = 3, 12, 300
VERDICTS = ["supported", "refuted", "unclear"]

CASES = [  # (id, claim, truth, kind)
    ("burj", "The Burj Khalifa is 928 metres tall.", "refuted", "near-miss number"),
    ("everest-wrong", "Mount Everest is 8,948 metres high.", "refuted", "near-miss number"),
    ("moon", "The Moon is about 284,000 km from the Earth.", "refuted", "near-miss number"),
    ("curie", "Marie Curie won her second Nobel Prize in 1905.", "refuted", "near-miss date"),
    ("everest-right", "Mount Everest is about 8,849 metres high.", "supported", "true number"),
    ("light", "The speed of light in vacuum is about 299,792 kilometres per second.", "supported", "true number"),
    ("chromosomes", "Humans normally have 23 pairs of chromosomes.", "supported", "true number"),
    ("lightning", "Lightning never strikes the same place twice.", "refuted", "myth"),
    ("cat", "My neighbour's cat was called Felix in 1999.", "unclear", "unverifiable"),
    ("mayor", "The mayor of Rivertown ate soup on 3 May 2021.", "unclear", "unverifiable"),
]
EXPERTS = ["a careful fact-checker", "a sceptic who looks for the exact figure, date or name that may be slightly off",
           "a subject expert who knows the topic well"]

VERDICT_SCHEMA = {"type": "object", "required": ["verdict", "reason"], "properties": {
    "verdict": {"type": "string", "enum": VERDICTS}, "reason": {"type": "string"}}}
ARGUE_SCHEMA = {"type": "object", "required": ["points"], "properties": {"points": {"type": "string"}}}
JUDGE_SCHEMA = {"type": "object", "required": ["verdict", "decided", "reason"], "properties": {
    "verdict": {"type": "string", "enum": VERDICTS}, "decided": {"type": "boolean"}, "reason": {"type": "string"}}}
RULE = ("Answer 'supported' only if the claim is true, 'refuted' if it is false or a detail (number, date, name) is off, "
        "and 'unclear' if it cannot be decided from general knowledge.")


class Budget:
    def __init__(self, max_calls=MAX_CALLS, max_seconds=MAX_SECONDS, clock=time.time):
        self.max_calls, self.max_seconds, self.clock = max_calls, max_seconds, clock
        self.calls, self.start = 0, clock()

    def spend(self):
        self.calls += 1

    def left(self, need=1):
        return self.calls + need <= self.max_calls and self.clock() - self.start < self.max_seconds


def ollama(prompt, schema, seed):
    body = {"model": MODEL, "stream": False, "think": False, "format": schema,
            "options": {"num_ctx": CTX, "temperature": 0.7, "seed": seed},
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(f"{HOST}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(json.loads(r.read())["message"]["content"])


def single(claim, ask, seed, budget):
    budget.spend()
    r = ask(f"Judge this claim.\nClaim: {claim}\n{RULE}", VERDICT_SCHEMA, seed)
    return dict(verdict=r["verdict"], rounds=1, stop="single", history=[r["verdict"]])


def cops(claim, ask, seed, budget, max_rounds=MAX_ROUNDS):
    pro = con = ""
    verdict, history, stop = "unclear", [], "cap"
    for rnd in range(1, max_rounds + 1):
        if not budget.left(3):
            stop = "budget"
            break
        side = lambda s, other: (f"Claim: {claim}\nArgue {s} the claim in at most four short points, using only what you know to be true."
                                 + (f"\nThe other side said:\n{other}\nAnswer its strongest point." if other else ""))
        for _ in range(3):
            budget.spend()
        new_pro = ask(side("FOR", con), ARGUE_SCHEMA, seed)["points"]
        new_con = ask(side("AGAINST", pro), ARGUE_SCHEMA, seed)["points"]
        pro, con = new_pro, new_con
        j = ask(f"Claim: {claim}\nCase for:\n{pro}\nCase against:\n{con}\n{RULE}\n"
                "Set decided=true only if another round of rebuttals could not change your verdict.", JUDGE_SCHEMA, seed)
        verdict = j["verdict"]
        history.append(verdict)
        if j["decided"]:
            stop = "judge"
            break
    return dict(verdict=verdict, rounds=len(history) or 0, stop=stop, history=history)


def jury(claim, ask, seed, budget, max_rounds=MAX_ROUNDS):
    votes, history, stop = {}, [], "cap"
    for rnd in range(1, max_rounds + 1):
        if not budget.left(len(EXPERTS)):
            stop = "budget"
            break
        new = {}
        for e in EXPERTS:
            budget.spend()
            others = "".join(f"- {o}: {v['verdict']}, {v['reason']}\n" for o, v in votes.items() if o != e)
            new[e] = ask(f"You are {e}. Claim: {claim}\n{RULE}"
                         + (f"\nThe other jurors said:\n{others}Keep or change your verdict." if others else ""),
                         VERDICT_SCHEMA, seed)
        votes = new
        tally = [v["verdict"] for v in votes.values()]
        history.append(tally)
        if len(set(tally)) == 1:
            stop = "agreement"
            break
    final = [v["verdict"] for v in votes.values()]
    best = max(VERDICTS, key=final.count) if final else "unclear"
    verdict = best if final.count(best) * 2 > len(final) else "unclear"  # a split jury is not a verdict
    return dict(verdict=verdict, rounds=len(history), stop=stop, history=history)


VARIANTS = {"single": single, "cops": cops, "jury": jury}


def main(argv):
    out, repeats = argv[1], int(argv[2]) if len(argv) > 2 else 3
    with open(out, "a") as f:
        for cid, claim, truth, kind in CASES:
            for name, fn in VARIANTS.items():
                for seed in range(1, repeats + 1):
                    b, t = Budget(), time.time()
                    try:
                        r = fn(claim, ollama, seed, b)
                    except Exception as e:
                        r = dict(verdict="error", rounds=0, stop=repr(e)[:120], history=[])
                    row = dict(case=cid, kind=kind, truth=truth, variant=name, seed=seed, calls=b.calls,
                               seconds=round(time.time() - t, 1), **r)
                    f.write(json.dumps(row) + "\n")
                    f.flush()
                    print(cid, name, seed, r["verdict"], r["rounds"], r["stop"], row["seconds"], flush=True)


if __name__ == "__main__":
    main(sys.argv)
