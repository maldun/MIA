"""Read the decisions of specs/mia/plausibility-review.md into specs/mia/plausibility-decisions.yaml.

Usage: python3 -I tools/import_plausibility_review.py <repository root>
Lines left empty stay open. A word the script does not know is an error (nothing is written). tools/apply_plausibility.py merges the decisions into
the proposal, so regenerating the proposal never loses a decision."""
import pathlib
import re
import sys

import yaml

FIELD_RISK = {"reason": "performance and resource figures are validated in the field (phase 7, VAL-006) and tuned in later iterations", "owner": "{by}",
              "decided": "{date} by {by}", "follow_up": "VAL-006"}


def parts(text, n):
    got = [p.strip() for p in text.split("|")]
    return got + [""] * (n - len(got))


def main(root):
    root = pathlib.Path(root)
    text = (root / "specs/mia/plausibility-review.md").read_text(encoding="utf-8")
    out, problems = {}, []
    for block in re.split(r"\n(?=### \d+\. )", text)[1:]:
        rid = re.match(r"### \d+\. (\S+)", block).group(1)
        decision = (re.search(r"^- Decision:[ \t]*(.*)$", block, re.M) or [0, ""])[1].strip()
        basis = (re.search(r"^- Basis:[ \t]*(.*)$", block, re.M) or [0, ""])[1].strip()
        if not decision:
            continue
        word = decision.split(":")[0].strip().lower()
        item = {}
        if word == "plausible":
            item["decision"] = "plausible"
        elif word == "implausible":
            item["decision"] = "implausible"
        elif word == "field":
            item.update(decision="questionable", accepted_risk=dict(FIELD_RISK))
            basis = basis or "the figure or quality depends on real use; it is measured in the field and tuned in later iterations (owner decision)"
        elif word == "probe":
            what, who, when = parts(decision.split(":", 1)[1], 3)
            if not (what and who and when):
                problems.append("%s: probe needs what | who | when" % rid)
            item.update(decision="questionable", probe={"what": what, "who": who, "when": when})
        elif word == "risk":
            reason, owner, follow = parts(decision.split(":", 1)[1], 3)
            if not (reason and owner):
                problems.append("%s: risk needs reason | owner | follow-up" % rid)
            item.update(decision="questionable", accepted_risk={"reason": reason, "owner": owner, "decided": "{date} by {by}", "follow_up": follow or "VAL-006"})
        else:
            problems.append("%s: unknown decision word '%s'" % (rid, word))
            continue
        if len(basis) < 10:
            problems.append("%s: Basis needs at least 10 characters" % rid)
        item["basis"] = [basis]
        out[rid] = item
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    path = root / "specs/mia/plausibility-decisions.yaml"
    path.write_text("# Decisions of the person who rates, read from plausibility-review.md by tools/import_plausibility_review.py\n" + yaml.safe_dump({"decisions": out}, sort_keys=True, allow_unicode=True), encoding="utf-8")
    print(len(out), "decisions written")


main(sys.argv[1])
