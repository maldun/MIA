"""Write the review file for the open plausibility items: specs/mia/plausibility-review.md (the person fills in the decisions).

Usage: python3 -I tools/gen_plausibility_review.py <repository root>
Reads the items of specs/mia/plausibility-proposal.yaml that have `attention` and no `decision`, shows each with its text, criterion, the reason for the
flag, the facts the agent found and a suggestion. The person writes the decision on the line `Decision:`; tools/import_plausibility_review.py puts
the decisions back into the proposal. Decision words:
  plausible                                realistic as it stands (give the reason on the line `Basis:`)
  field                                    postponed to the field (phase 7, VAL-006), accepted risk
  probe: <what> | <who> | <when>           questionable, a probe is planned (a spike, a baseline run)
  risk: <reason> | <owner> | <follow-up>   questionable, the risk is accepted
  implausible                              change the requirement first"""
import pathlib
import re
import sys

import yaml

# title, ids, facts the agent found, suggestion
FAMILIES = [
    ("Judgement quality of the verify workflow", ["FR-9", "REQ-BE-049", "REQ-WFM-014"],
     "The suites verdicts, hard_checks and computable exist in eval/suites, with the baseline reports eval/baselines/verdicts-styles.md and computable-gemma4-12b.md. The criterion (fewer wrong claims than the single voice, no more true claims lost, on the holdout) is decided by eval_decide.py against the recorded baseline.",
     "probe: the first dev-split run of the styles against the baseline (task T-04 and the first Implement task of N-2.3); the holdout decides in Verify. If the criterion looks unreachable on the pinned model the agent stops and reports (agent-app rule)."),
    ("Stable verdicts", ["REQ-BE-050", "REQ-WFM-015"],
     "A limit of 0.90 as the lower bound of a 95 % interval needs enough repeats; the current stability is not measured in this plan.",
     "probe: measure the stability of today's verify on the dev suite with 3 repeats before the first Implement task of N-2.3."),
    ("Lookup with sources", ["FR-10", "REQ-BE-051", "REQ-WFM-016"],
     "The lookup exists today (suites research and web_checks). The criterion is a rate with a baseline (every answer has a source and a verbatim quote, or unknown).",
     "probe: baseline run of today's lookup (T-04). The same baseline serves VAL-001 in the field."),
    ("Review report (recall and precision)", ["FR-11", "REQ-BE-053", "REQ-WFM-018"],
     "The suites research, research_compound and review_toy exist; the review is the largest model-dependent workflow and runs in time slices.",
     "probe: baseline per tier from the existing research suites (recall and precision against the baseline). Alternatively `field` with an accepted risk, since the review is the second workflow (VAL-002)."),
    ("Method transfer", ["FR-13", "REQ-BE-057", "REQ-WFM-022"],
     "The known method must be in the top 3 on the retro-discovery cases of the owner (AC-26); the cases exist, the rate on the pinned model is not measured.",
     "risk or field: you decide whether method transfer is a first-release criterion. It is switched on only on request (`Where method transfer is switched on`)."),
    ("Structured memory", ["FR-14", "REQ-BE-024", "REQ-CHA-011"],
     "The criterion is relative: at least as good as today on the memory test set. The memory exists (extraction.py, content_store.py); a baseline report is eval/baselines/extraction-rules.md.",
     "plausible: a relative criterion against a recorded baseline can only fail if the new storage loses information; the test set decides in Verify."),
    ("Silent repair of behaviour violations", ["FR-15", "REQ-BE-027", "REQ-CHA-014"],
     "behaviour.py and the suite behaviour exist; the criterion keeps the recorded precision and recall of the detectors.",
     "plausible: a relative criterion against the recorded precision and recall (precedent in the code)."),
    ("Persona dialogues", ["FR-25", "REQ-BE-021", "REQ-CHA-008"],
     "Decided as at least 84 of 100 dialogues (D-52); today's MIA is estimated at about 0.90 but not measured on the same 100 dialogues. If it comes out clearly below 0.90 you are asked again.",
     "probe: the measurement of today's MIA on the 100 dialogues (task T-04, owner)."),
    ("Adaptation to negative votes", ["FR-29", "REQ-BE-030", "REQ-CHA-017"],
     "The statistical test at 0.5 % has a calculated false alarm of 0.0135 and a miss of 0.0102 at a true rate of 2 % (finding F-1, scripts/false_alarm.py). The mechanism is a counter and a chance, no model.",
     "plausible: calculated (the error rates are exact) and the mechanism is plain code."),
    ("Confidence by code, no invented source", ["NFR-4"],
     "Two parts: the confidence figures are computed by code (deterministic), and the criterion `0 invented references and 100 % of cited quotes found` is measured on the suites (evidence.py exists).",
     "plausible for the code part; the measured part is covered by the lookup and verify baselines above. One decision for both is fine."),
    ("Baselines and benchmark suites", ["REQ-EVL-005", "REQ-OPS-005", "REQ-EVL-009", "REQ-OPS-019"],
     "eval/suites has 10 suites and eval/baselines has 9 reports, but the baselines are `.md` reports; the form `eval/baselines/<suite>__<variant>__baseline.jsonl` that eval_decide.py reads is not there yet. Review has no suite named after the workflow.",
     "probe: record the baselines in the .jsonl form (a task of N-4.1, owner for the labels); plausible after that."),
    ("Security and accounts", ["FR-21", "NFR-3", "NFR-5", "NFR-6"],
     "Precedent in the code: sandbox.py, tls_proxy.py, source_trust.py, the web log, accounts over IF-101 with throttling (the 6th failed attempt in a minute is refused). Security is checked in Verify by tests and a review of the trust boundaries.",
     "plausible, with the note that the security review of the Verify phase is the real check; a security item should not be rated by a proposal alone."),
    ("VRoid model mapping", ["FR-24"],
     "ui/character and the character pack exist; the unmapped presets and gestures of a second model are reported by IF-111 (contract test with the models A and B).",
     "plausible: precedent in the code and the contract mock; the second model is a demonstration."),
    ("Assumption about the phones", ["ASM-N1-002"],
     "The 30 fps on any phone inside the network is measured on the phones you have at hand (HLS amendment 9). The requirement itself is postponed to the field (category `field`).",
     "field: the same decision as for the frame-rate requirements."),
]


def load(root):
    items = {}
    files = [root / "specs/mia/requirements.md"] + sorted((root / "specs/mia/nodes").rglob("requirements.md"))
    for path in files:
        for block in re.split(r"\n(?=### )", path.read_text(encoding="utf-8"))[1:]:
            rid = block.split("\n")[0][4:].split(" ")[0]
            field = lambda k: (re.search(r"- %s: (.*)" % k, block) or [0, ""])[1].strip()
            items[rid] = dict(text=field("Text"), ac=field("Acceptance criterion"), method=field("Verification method"), quality=field("Quality"))
    return items


def main(root):
    root = pathlib.Path(root)
    proposal = yaml.safe_load((root / "specs/mia/plausibility-proposal.yaml").read_text(encoding="utf-8"))["proposal"]
    open_ids = {k for k, v in proposal.items() if v.get("attention") and not v.get("decision")}
    items = load(root)
    listed = {i for _, ids, _, _ in FAMILIES for i in ids}
    assert listed == open_ids, ("not in a family:", sorted(open_ids - listed), "not open:", sorted(listed - open_ids))
    L = ["# Plausibility review: %d open items" % len(open_ids), "",
         "Write your decision on every line `Decision:` and, where it helps, the reason on `Basis:`. Decision words: `plausible` | `field` (postponed to the field, VAL-006) | "
         "`accept: <reason>` (questionable, the risk is accepted for now, you are the owner, follow-up VAL-006) | "
         "`probe: <what> | <who> | <when>` | `risk: <reason> | <owner> | <follow-up>` | `implausible`. The suggestion lines are only the agent's opinion. "
         "Then run `python3 -I tools/import_plausibility_review.py .` and after it `tools/apply_plausibility.py`.", "",
         "Context: a controlled environment with a few users (ASM-MU-001); performance and resource figures go to the field (VAL-006); the baseline of today's MIA is task T-04 (owner).", ""]
    n = 0
    for title, ids, facts, suggestion in FAMILIES:
        L += ["---", "", "## %s" % title, "", "**Facts found:** %s" % facts, "", "**Suggestion:** %s" % suggestion, ""]
        for rid in ids:
            n += 1
            it = items.get(rid, {})
            L += ["### %d. %s" % (n, rid), "", "- Text: %s" % (it.get("text") or proposal[rid]["text"])]
            if it.get("ac"):
                L.append("- Criterion: %s" % it["ac"])
            if it.get("quality"):
                L.append("- Quality line: %s" % it["quality"])
            L += ["- Verified by: %s" % (it.get("method") or "assumption"), "- Flagged because: %s" % ", ".join(proposal[rid]["attention"]), "- Decision: ", "- Basis: ", ""]
    pathlib.Path(root, "specs/mia/plausibility-review.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(n, "items in", len(FAMILIES), "families")


main(sys.argv[1] if len(sys.argv) > 1 else ".")
