"""Generate the model block of the node requirements (task T-14) and put it at the end of specs/mia/architecture.sysml.

Usage: python3 -I tools/gen_node_requirements_model.py <repository root>
For every REQ-id of specs/mia/nodes/**/requirements.md: a `requirement def` with the requirement text as doc and its way of verification, a usage,
`satisfy` and `allocate` to the part of its subject, and a `dependency` to its parent. The block lies between two marker lines and is rewritten
on every run; nothing in it is edited by hand (change the requirement files and run this again). The interface ids (IF-...) are already in the model."""
import pathlib
import re
import sys

BEGIN = "// BEGIN GENERATED: node requirements (tools/gen_node_requirements_model.py, task T-14) - do not edit by hand"
END = "// END GENERATED: node requirements"
PART = {"MiaSystem": "mia", "WebFrontEnd": "mia.frontEnd", "WebApplication": "mia.webApp", "GraphApp": "mia.graphApp", "ConversationCore": "mia.conversation",
        "TaskRuntime": "mia.taskRuntime", "VerificationSuite": "mia.verifier", "VoiceSubsystem": "mia.voice", "Observability": "mia.observability",
        "Evaluation": "mia.evaluation", "Persistence": "mia.persistence", "OperationLayer": "mia.operation"}
HOW = {"test": "test", "measurement": "measurement", "inspection": "inspection", "demonstration": "demonstration"}


def usage(rid):
    return re.sub(r"[^a-z0-9]", "", rid.lower()) if re.match(r"(FR|NFR|CON|IF)-\d+$", rid) else "r_" + re.sub(r"[^a-z0-9]", "_", rid.lower())


def camel(title, rid):
    words = re.findall(r"[A-Za-z0-9]+", title)
    name = "".join(w[:1].upper() + w[1:] for w in words)[:60] or "Requirement"
    return re.sub(r"^(\d)", r"R\1", name) + "_" + rid.split("-")[1].title() + rid.split("-")[-1]


def read(root):
    out = []
    for path in sorted((root / "specs/mia/nodes").rglob("requirements.md")):
        for block in re.split(r"\n(?=### )", path.read_text(encoding="utf-8"))[1:]:
            head = block.split("\n")[0]
            if not head.startswith("### REQ-"):
                continue
            field = lambda k: (re.search(r"- %s: (.*)" % k, block) or [0, ""])[1].strip()
            methods = [HOW[m.strip().lower()] for m in field("Verification method").split(",") if m.strip().lower() in HOW] or ["test"]
            subject = re.search(r"Subject: (\w+)", block)
            out.append(dict(id=head[4:].split(" ")[0], title=head.split(" – ", 1)[1], text=field("Text"), parent=[p.strip() for p in field("Parent").split(",") if p.strip()],
                            methods=methods, subject=subject.group(1) if subject else "MiaSystem"))
    return out


def block(reqs, known):
    ids = {r["id"] for r in reqs}
    L = [BEGIN, "package MIA_NodeRequirements {", "    private import MIA_Common::*;", "    private import MIA_Architecture::*;", "    private import MIA_Requirements::*;", ""]
    names = set()
    for r in reqs:
        name = camel(r["title"], r["id"])
        while name in names:
            name += "x"
        names.add(name)
        r["def"] = name
        how = ", ".join("HowVerified::" + m for m in r["methods"])
        text = re.sub(r"\s+", " ", r["text"]).replace("*/", "* /")
        L += ["    requirement def <'%s'> %s {" % (r["id"], name), "        subject s : %s;" % r["subject"], "        doc /* %s */" % text,
              "        @Trace { :>> verifiedBy = (%s); }" % how, "    }"]
    L.append("")
    for r in reqs:
        L.append("    requirement %s : %s;" % (usage(r["id"]), r["def"]))
    L.append("")
    for r in reqs:
        L.append("    satisfy %s by %s;" % (usage(r["id"]), PART[r["subject"]]))
    for r in reqs:
        if PART[r["subject"]] != "mia":
            L.append("    allocate %s to %s;" % (usage(r["id"]), PART[r["subject"]]))
    L.append("")
    for r in reqs:
        for parent in r["parent"]:
            if parent in ids or parent in known:
                L.append("    dependency from %s to %s;" % (usage(r["id"]), usage(parent)))
    L += ["}", END]
    return "\n".join(L) + "\n"


def main(root):
    root = pathlib.Path(root)
    path = root / "specs/mia/architecture.sysml"
    text = path.read_text(encoding="utf-8")
    if BEGIN in text:
        text = text[:text.index(BEGIN)].rstrip("\n") + "\n"
    known = set(re.findall(r"requirement def <'([A-Z]+-\d+)'>", text))
    reqs = read(root)
    path.write_text(text + "\n" + block(reqs, known), encoding="utf-8")
    print(len(reqs), "node requirements written")


main(sys.argv[1])
