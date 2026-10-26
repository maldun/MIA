"""Draft of the plausibility record (L2b) for the plan gate: the agent proposes, a person rates.

Usage: python3 -I tools/gen_plausibility_draft.py <repository root>
Writes specs/mia/plausibility-proposal.yaml: every requirement and assumption with a proposed rating and the reason. Items that depend on a
number, a measurement, a model or hardware are flagged `attention`; the person decides those one by one (rating, basis, probe or accepted risk).
The others carry a proposal that the person can accept as a whole with tools/apply_plausibility.py. Nothing here is a rating.

Decisions of the owner are recorded as categories (below): `multi-user` (accepted), `field` (performance and resource figures validated in the field,
an accepted risk with follow-up VAL-006). `deterministic` is the agent's own proposal and the person may veto it. The names `{by}` in an accepted risk
are replaced by apply_plausibility.py with the person who rates."""
import pathlib
import re
import sys

BOUND = re.compile(r"\d")
WORDS = re.compile(r"at least|at most|within|no more than|median|per cent|%|fps|seconds|\bs\b|GB|ms\b|rate|recall|precision|kappa|interval", re.I)
MODEL = re.compile(r"pinned model|eval suite|holdout|dev split|LLM judge|\bGPU\b|VRAM|phone|baseline", re.I)
IDS = re.compile(r"\b(?:AC|IF|REQ|FR|NFR|CON|TC|ASM)-[A-Z0-9-]+|\btest_\w+\.\w+|\b\w+\.(?:py|mjs|md)\b|(?:3\.1[1-9]|4\.6\.1)")

# Owner decision 2026-10-26: a controlled environment, a few trusted users who rarely work at the same time.
MULTI_USER = {"REQ-API-002", "REQ-BE-007", "REQ-DB-006", "REQ-SLY-006", "REQ-BE-003", "REQ-CHA-003", "REQ-BE-072", "REQ-RUN-010", "REQ-WFX-021",
              "REQ-CHV-005", "REQ-CLV-009", "REQ-FE-015"}
# Owner decision 2026-10-26: performance and resource figures are validated in the field (phase 7) and tuned in later iterations.
FIELD = {"NFR-7", "REQ-CHV-010", "REQ-FE-025", "REQ-BE-069", "REQ-RUN-007", "REQ-WFX-018", "REQ-EVL-007", "REQ-OPS-017", "NFR-2", "REQ-BE-062", "REQ-RUN-005",
         "REQ-WFX-012", "REQ-BE-063", "REQ-RUN-006", "REQ-WFX-013", "CON-2", "FR-33", "REQ-BE-042", "REQ-WFM-009", "REQ-BE-071", "REQ-RUN-009", "REQ-WFX-020",
         "REQ-BE-054", "REQ-WFM-019", "FR-8", "REQ-BE-044", "REQ-RUN-002", "REQ-WFX-003"}
# The agent's own proposal (the person may veto): flagged only by a number or a quality line; the check is deterministic code, a fixed fixture or an
# inspection, and the part exists in the code base or is a plain table.
DETERMINISTIC = {"REQ-API-009", "REQ-BE-014", "REQ-BE-028", "REQ-CHA-015", "REQ-DB-012", "REQ-RTB-003", "REQ-DB-014", "REQ-RTB-005", "REQ-BE-032", "REQ-CHA-019",
                 "FR-28", "REQ-FE-003", "REQ-CLV-003", "REQ-FE-004", "REQ-CLV-004", "REQ-BE-060", "REQ-LOG-004", "REQ-WFX-010", "REQ-BE-047", "REQ-WFM-012",
                 "REQ-TLS-006", "REQ-WFX-016", "REQ-BE-067", "REQ-WFM-024", "REQ-EVL-004", "REQ-OPS-004", "REQ-EVL-001", "REQ-OPS-001", "IF-104",
                 "REQ-TLS-002", "REQ-WFX-006", "REQ-BE-039", "REQ-WFM-006", "FR-19", "FR-23", "FR-32", "FR-4", "NFR-1", "NFR-8", "REQ-FE-024", "REQ-CLV-016",
                 "REQ-FE-007", "REQ-CLV-007", "REQ-FE-009", "REQ-CHV-003", "FR-1", "FR-26", "FR-20"}
# Assumptions that could be checked on the host or are decisions of the plan.
ASM_OK = {"ASM-N3-002": "hashlib.scrypt exists in the standard library (checked on the host 2026-10-26)",
          "ASM-N3-004": "graphlib is in the standard library (checked on the host 2026-10-26)",
          "ASM-N3-001": "podman 5.7.1 is installed on the host (checked 2026-10-26); the tests skip, never weaken, where it is not",
          "ASM-N4-002": "podman 5.7.1 is installed on the host (checked 2026-10-26); the tests skip, never weaken, where it is not",
          "ASM-N1-001": "Chromium runs headless through flatpak on the host (ui/tools/browser_check.py uses it today)",
          "ASM-N5-001": "Chromium runs headless through flatpak on the host (ui/tools/browser_check.py uses it today)",
          "ASM-N3-003": "psycopg 3 approved by the owner (D-54)",
          "ASM-N3-005": "a design decision of the plan, fixed in contracts/IF-302-record-tables.md",
          "ASM-N2-001": "a design decision of the plan: the fake model server of pipeline.py exists and its tests run without a model",
          "ASM-N2-002": "a design decision of the plan: the mock of IF-102 exists (contract-drafts)",
          "ASM-N5-002": "decided by the owner on 2026-10-25 (the Graph app is an add-on)",
          "ASM-N4-001": "the scripts eval_decide.py and agent_check.py exist in the agent-app skill (checked 2026-10-26)",
          "ASM-N4-003": "deploy/compose.yaml runs the model server and the search service today"}


def reqs_of(root):
    files = [root / "specs/mia/requirements.md"] + sorted((root / "specs/mia/nodes").rglob("requirements.md"))
    out = {}
    for path in files:
        for block in re.split(r"\n(?=### )", path.read_text(encoding="utf-8"))[1:]:
            head = block.split("\n")[0]
            rid = head[4:].split(" ")[0]
            if not re.match(r"(REQ|NFR|FR|CON|IF)-", rid):
                continue
            field = lambda k: (re.search(r"- %s: (.*)" % k, block) or [0, ""])[1].strip()
            out[rid] = dict(text=field("Text"), ac=field("Acceptance criterion"), method=field("Verification method"), quality=field("Quality"))
    return out


def asms_of(root):
    found = {}
    for path in sorted((root / "specs/mia").rglob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            for asm in re.findall(r"\bASM-[A-Z0-9]+(?:-[A-Z0-9]+)?\b", line):
                if line.lstrip("- ").startswith(asm) or ("- %s:" % asm) in line:
                    found.setdefault(asm, line.strip().lstrip("- ")[:240])
    return found


def flags(r):
    why = []
    if "Measurement" in r["method"]:
        why.append("decided by a measurement")
    if r["quality"]:
        why.append("quality requirement with a target")
    crit = r["text"] + " " + r["ac"]
    if BOUND.search(IDS.sub("", r["ac"])) and WORDS.search(IDS.sub("", crit)):
        why.append("numeric bound in the criterion")
    if MODEL.search(IDS.sub("", crit)):
        why.append("depends on the model, a GPU or a phone")
    return why


MULTI_BASIS = "controlled environment with a few users who rarely work at the same time (owner decision 2026-10-26, ASM-MU-001); the queue and the live update are the same code for one user"
FIELD_RISK = ("{reason: \"performance and resource figures are validated in the field (phase 7, VAL-006) and tuned in later iterations\", owner: \"{by}\", "
              "decided: \"2026-10-26 by {by}\", follow_up: \"VAL-006\"}")


def main(root):
    root = pathlib.Path(root)
    reqs, asms = reqs_of(root), asms_of(root)
    lines = ["# Proposal for the plausibility record (L2b). Generated by tools/gen_plausibility_draft.py; NOT a rating.",
             "# A person decides. Items with `attention` and no `decision` are open: set `decision` (plausible | questionable | implausible) and `basis`,",
             "# and for questionable also `probe` (what, who, when) or `accepted_risk` (reason, owner, decided, follow_up). Then run tools/apply_plausibility.py.",
             "# Categories: multi-user and field carry the owner's decision of 2026-10-26; deterministic is the agent's proposal (veto by deleting the line).",
             "proposal:"]
    open_count = 0
    for rid, r in sorted(reqs.items()):
        why = flags(r)
        lines += ["  %s:" % rid, "    text: %s" % repr(r["text"][:160])]
        if rid in MULTI_USER:
            lines += ["    proposed: plausible", "    category: multi-user", "    decision: plausible", "    basis: [%r]" % MULTI_BASIS]
        elif rid in FIELD:
            lines += ["    proposed: questionable", "    category: field", "    attention: %s" % (why or ["performance or resource figure"]), "    decision: questionable",
                      "    basis: [\"the figure depends on the real model, hardware and use; it is measured in the field and tuned in later iterations (owner decision 2026-10-26)\"]",
                      "    accepted_risk: %s" % FIELD_RISK]
        elif rid in DETERMINISTIC:
            lines += ["    proposed: plausible", "    category: deterministic",
                      "    basis: \"flagged by a number or a quality line only; the check is deterministic code, a fixed fixture or an inspection, and the part exists in the code base or is a plain table (agent proposal)\""]
        elif why:
            open_count += 1
            lines += ["    proposed: questionable", "    attention: %s" % why, "    decision:                     # plausible | questionable | implausible",
                      "    basis: []                     # references or sourced text (10 characters or more)"]
        else:
            lines += ["    proposed: plausible",
                      "    basis: \"no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)\""]
    for asm, text in sorted(asms.items()):
        if asm == "ASM-MU-001":                      # decided by the owner, written out below
            continue
        lines += ["  %s:" % asm, "    text: %s" % repr(text)]
        if asm in ASM_OK:
            lines += ["    proposed: plausible", "    category: assumption", "    basis: [%r]" % ASM_OK[asm]]
        else:
            open_count += 1
            lines += ["    proposed: questionable", "    attention: [\"assumption: checked in validation\"]", "    decision:", "    basis: []"]
    lines += ["  ASM-MU-001:", "    text: 'The MIA system is used in a controlled environment by a few trusted users who rarely work at the same time (owner, 2026-10-26).'",
              "    proposed: questionable", "    category: assumption", "    attention: [\"assumption: checked in the field (VAL-003, VAL-004)\"]", "    decision: questionable",
              "    basis: [\"decided by the owner on 2026-10-26; checked in the field with the first users\"]",
              "    accepted_risk: {reason: \"the number of simultaneous users is a fact about use; the field shows it\", owner: \"{by}\", decided: \"2026-10-26 by {by}\", follow_up: \"VAL-003\"}"]
    (root / "specs/mia/plausibility-proposal.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("%d requirements, %d assumptions, %d open for a decision" % (len(reqs), len(asms) + 1, open_count))


main(sys.argv[1])
