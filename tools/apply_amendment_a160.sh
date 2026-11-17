#!/usr/bin/env bash
# Amendment A-160 (G-V3.CHAT, owner maldun, plan gate 2026-11-18): the end message of a run is bounded, can be stopped and keeps the status line until it is ready; the review returns a short result.
# Source: specs/mia/amendments/A-160-draft-end-message-is-bounded-and-stoppable.md. Made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its
# anchor is not found exactly once, so a second --do changes nothing.
# Files that change:
#   specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md     REQ-CHA-069 clarified; REQ-CHA-073, 074, 075 new (Draft)
#   specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md   REQ-WFM-142 new (Draft)
#   specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/test-spec.md        TC-CHA-077 to 080 (table rows and scenarios)
#   specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/test-spec.md   TC-WFM-142
#   specs/mia/test-requirements.md   (protected) TC-CHA-077 to 080 and TC-WFM-142 join the "Applies to:" line of TR-CHAT-006 (owner's answer of the plan gate)
#   specs/mia/plausibility.yaml      the ratings (plausible, maldun, 2026-11-18) of REQ-CHA-073, 074, 075, REQ-WFM-142 and the new rating of REQ-CHA-069
#   specs/mia/review-log.md          two rows (the amendment, the plan gate); ids: the next free ones (A160_FIRST_ID=nnn overrides)
#   specs/mia/architecture.sysml     after --do: the model block of the node requirements is generated again (tools/gen_node_requirements_model.py)
# NOT changed here: tests/acceptance (TC-CHA-077 to 080 are written red in the next step, protected folder: patch plus apply script), the code, the status of the requirements (Draft until Commit).
#   bash tools/apply_amendment_a160.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a160.sh --do      install, generate the model, run the checks; commit afterwards with the paths named (never git add -A)
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
N22=specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent
N23=specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management
REQ22=$N22/requirements.md; REQ23=$N23/requirements.md; TS22=$N22/test-spec.md; TS23=$N23/test-spec.md
TR=specs/mia/test-requirements.md; PLAUS=specs/mia/plausibility.yaml; LOG=specs/mia/review-log.md
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$REQ22" "$REQ23" "$TS22" "$TS23" "$TR" "$PLAUS" "$LOG" "$WORK" "${A160_FIRST_ID:-}" <<'PY'
import os
import re
import sys

req22, req23, ts22, ts23, tr, plaus, log, work, first_id = sys.argv[1:10]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def die(message):
    sys.exit("REFUSED: " + message)


def edit(text, old, new, label):
    if text.count(old) != 1:
        die("%s: the anchor was found %d times (expected once); the installed file is not what this script was made for" % (label, text.count(old)))
    return text.replace(old, new)


def block(rid, title, subject, text, rationale, parent, group, criterion, check, history):
    return ("### %s – %s\n- Level: low   Subject: %s\n- Text: %s\n- Rationale: %s\n- Parent: %s\n- Group: %s\n- Priority: Must\n- Verification method: Test\n"
            "- Acceptance criterion: %s\n- Verified by: %s\n- Status: Draft\n- History: %s\n") % (rid, title, subject, text, rationale, parent, group, criterion, check, history)


# ------------------------------------------------------------------------------------------------------------------ requirements: chat agent
text = read(req22)
if "### REQ-CHA-073" not in text:
    old69 = text[text.index("### REQ-CHA-069 –"):text.index("### REQ-CHA-070 –")]
    new69 = old69
    new69 = edit(new69, "shall send the clearing of the status line of the run before it adds the end message, whether or not a line was shown.",
                 "shall send the clearing of the status line of the run when the text of the end message is ready and before it adds the end message, whether or not a line was shown; until then the line shows the phase the run was in.", "069 text")
    new69 = edit(new69, "no line follows it (exact)\n", "no line follows it; with a digest that takes a scripted time the line is not cleared before the digest has returned: line, digest call, clearing, message (exact)\n", "069 criterion")
    new69 = edit(new69, "- Verified by: TC-CHA-074\n", "- Verified by: TC-CHA-074, TC-CHA-080\n", "069 check")
    new69 = new69.rstrip("\n").rstrip() + "; A-160 (owner 2026-11-18, plan gate): the line stays until the text of the end message is ready (first real /review: the chat was blank for 16 minutes)\n\n"
    text = text.replace(old69, new69)
    anchor = "### REQ-CHA-072 –"
    start = text.index(anchor)
    rest = text[start:]
    nxt = re.search(r"\n### ", rest[5:])
    end = start + 5 + nxt.start() + 1 if nxt else len(text)
    new = "\n" if not text[:end].endswith("\n\n") else ""
    new += block("REQ-CHA-073", "Output of a digest call", "ConversationCore",
                 "The Chat agent shall ask the model server for at most 1024 tokens in each model call of SkillDigestStep.",
                 "refines REQ-BE-078 and REQ-CHA-050; owner 2026-11-18 (A-160): with an input of at most 4096 tokens a call stays inside num_ctx 8192, so the server never ends a text at the context limit; first real /review: a digest piece wrote about 1400 tokens and the end message was cut in the middle",
                 "REQ-BE-078", "ST", "AC-39: with a fake model that records the options of each call, a summary of a long result makes only calls with `num_predict` 1024 (exact)", "TC-CHA-077",
                 "A-160 (owner 2026-11-18, plan gate), new") + "\n"
    new += block("REQ-CHA-074", "A too long summary is asked again once", "ConversationCore",
                 "When the text of the last call of SkillDigestStep is longer than 1200 characters, the Chat agent shall ask the step once more to shorten that text to at most 1200 characters and pass on the text of the second call.",
                 "refines REQ-BE-078 and REQ-WFM-036; owner 2026-11-18 (A-160): REQ-CHA-052 only asks for 1200 characters and a 12B model does not always comply; the second call gets the short text and costs seconds; the code never cuts (REQ-CHA-063 unchanged)",
                 "REQ-BE-078", "ST", "AC-39: with scripted replies a first reply of 800 characters makes one call; a first reply of 3000 and a second of 900 characters makes two calls and the chat gets the 900 characters; a first reply of 3000 and a second of 2500 characters makes two calls (no third) and the chat gets the 2500 characters unchanged (exact)",
                 "TC-CHA-078", "A-160 (owner 2026-11-18, plan gate), new") + "\n"
    new += block("REQ-CHA-075", "Stop ends the end message", "ConversationCore",
                 "When the user stops while the end message of a run is made, the Chat agent shall make no further model call for it and end the run with the plain sentence of its outcome and the link to the run.",
                 "refines REQ-BE-078 and REQ-CHA-004; owner 2026-11-18 (A-160, decision A): Stop must work at every point of a run, also in the minutes after its skill returned; the result is stored, the user has the report in the Skill run view",
                 "REQ-BE-078", "ST", "AC-39: with a long result of ten pieces and a stop during the first piece call, no further model call is made, the end message is the plain sentence `The run is done.` with the link and the chat model history holds no digest text (exact)",
                 "TC-CHA-079", "A-160 (owner 2026-11-18, plan gate), new")
    text = text[:end] + new + ("\n" if not text[end:].startswith("\n") and text[end:] else "") + text[end:]
out("requirements-cha.md", text)

# ------------------------------------------------------------------------------------------------------------------ requirements: workflow management
text = read(req23)
if "### REQ-WFM-142" not in text:
    text = text.rstrip("\n") + "\n\n" + block(
        "REQ-WFM-142", "The result of the review is short", "TaskRuntime",
        "The Workflow management shall deliver the review with a result that holds the question, the cut-off, the way the run ended, the summary (coverage, what was found, gaps) and the flow count, and no list of works, while the full report stays unchanged in the run report, the record of the report and the files.",
        "refines REQ-BE-053, REQ-WFM-018 and REQ-WFM-139; owner 2026-11-18 (A-160, decision C): the end message is worded from the result (REQ-WFM-036); a result with every screened work made about 17 digest calls and a cut end message in the first real /review; the report is read in the Skill run view and the files as before",
        "REQ-BE-053", "RV",
        "AC-39: with a scripted review of 400 screened works the returned result holds the question, the summary and the flow line, none of the sections `Included`, `Maybe` and `Excluded although closely related`, and is shorter than 8000 characters; the run report and the `.md` file are the same texts as before (exact)",
        "TC-WFM-142", "A-160 (owner 2026-11-18, plan gate), new")
out("requirements-wfm.md", text)

# ------------------------------------------------------------------------------------------------------------------ test specs
text = read(ts22)
if "TC-CHA-077" not in text:
    row = "| TC-CHA-076 | REQ-CHA-072 |"
    line = [l for l in text.split("\n") if l.startswith(row)]
    if len(line) != 1:
        die("test-spec N-2.2: the row of TC-CHA-076 was not found once")
    rows = ("\n| TC-CHA-077 | REQ-CHA-073 | Component | 1 | unit test with a recording chat function that keeps the options of each call | AC-39: with a long result every call of the step carries the option num_predict 1024 | exact |"
            "\n| TC-CHA-078 | REQ-CHA-074 | Component | 1 | unit test with scripted replies of the fake model | AC-39: 800 characters give one call; 3000 then 900 give two calls and 900 reach the chat; 3000 then 2500 give two calls and 2500 reach the chat | exact |"
            "\n| TC-CHA-079 | REQ-CHA-075 | Component | 1 | unit test with the fake model server and a stop during the first piece call | AC-39: no further call after the stop; the end message is `The run is done.` with the link; the model history holds no digest text | exact |"
            "\n| TC-CHA-080 | REQ-CHA-069 | Component | 1 | unit test with a recording of the events and a scripted slow digest | AC-39: the order of the events is line, digest call, clearing, end message | exact |")
    text = text.replace(line[0], line[0] + rows)
    tail = "after the stop no line is sent again before the clearing (A-158, F-03, F-06)\n"
    scenarios = ("\n### TC-CHA-077 – Output of a digest call\n- Verifies: REQ-CHA-073\n- Given: the digest step on a recording chat function and a result of 20 000 tokens\n- When: the step writes the summary (pieces, digests, last call)\n- Then: every call carried the option `num_predict` 1024 (A-160)\n"
                 "\n### TC-CHA-078 – A too long summary is asked again once\n- Verifies: REQ-CHA-074\n- Given: the digest step on scripted replies; three runs: a first reply of 800 characters; 3000 then 900; 3000 then 2500\n- When: the step writes the summary\n- Then: one call, then two calls and the 900 characters, then two calls (no third) and the 2500 characters unchanged (A-160)\n"
                 "\n### TC-CHA-079 – Stop ends the end message\n- Verifies: REQ-CHA-075\n- Given: a run whose result is ten pieces long and a fake model server that stops the run during its first piece call\n- When: the end message is made\n- Then: no further model call is made, the end message is `The run is done.` with the link, and the history for the chat model holds no digest text (A-160, decision A)\n"
                 "\n### TC-CHA-080 – The line stays until the end message is ready\n- Verifies: REQ-CHA-069\n- Given: a run in its phase `collect` and a digest that takes a scripted time; a recording of the events\n- When: the run ends done\n- Then: the order is the line `collect`, the digest call, the clearing of the line, the end message; no clearing before the digest has returned (A-160)\n")
    i = text.index("### TC-CHA-076 –")
    j = text.index(tail, i) + len(tail)
    text = text[:j] + scenarios + text[j:]
out("test-spec-cha.md", text)

text = read(ts23)
if "TC-WFM-142" not in text:
    line = [l for l in text.split("\n") if l.startswith("| TC-WFM-141 | REQ-WFM-141 |")]
    if len(line) != 1:
        die("test-spec N-2.3: the row of TC-WFM-141 was not found once")
    text = text.replace(line[0], line[0] + "\n| TC-WFM-142 | REQ-WFM-142 | Component | 1 | unit test with the scripted review of 400 works, the fake storage and the fake files volume | AC-39: the result holds the question, the summary and the flow line, none of the work sections, under 8000 characters; the run report and the `.md` file are the full texts | exact |")
    scenario = ("### TC-WFM-142 – The result of the review is short\n- Verifies: REQ-WFM-142\n- Given: a scripted review that screens 400 works and includes 74 of them, the fake storage and the fake files volume\n"
                "- When: the run ends\n- Then: the result holds the question, the summary (coverage, found, gaps) and the flow line, none of the sections `Included`, `Maybe` and `Excluded although closely related`, and is shorter than 8000 characters; the run report and the `.md` file hold the full report as before (A-160, decision C)\n\n")
    text = edit(text, "## Scenarios (G-V2.TOOLBOX, checks TC-WFM-050", scenario + "## Scenarios (G-V2.TOOLBOX, checks TC-WFM-050", "test-spec N-2.3 anchor")
out("test-spec-wfm.md", text)

# ------------------------------------------------------------------------------------------------------------------ test requirements
text = read(tr)
if "TC-CHA-077" not in text:
    start = text.index("### TR-CHAT-006 –")
    lines = text[start:].split("\n")
    at = next(i for i, l in enumerate(lines) if l.startswith("- Applies to:"))
    if not lines[at].rstrip().endswith("TC-CHA-076"):
        die("TR-CHAT-006: the Applies to: line does not end with TC-CHA-076")
    lines[at] = lines[at].rstrip() + ", TC-CHA-077, TC-CHA-078, TC-CHA-079, TC-CHA-080, TC-WFM-142"
    text = text[:start] + "\n".join(lines)
out("test-requirements.md", text)

# ------------------------------------------------------------------------------------------------------------------ plausibility
text = read(plaus)
if "    REQ-CHA-073:" not in text:
    entry = """    %s:
      basis:
      - no number, measurement or model quality depends on it; the behaviour is fixed
        by an exact acceptance criterion on a scripted run, no real model (proposal
        of the agent, 2026-11-18, A-160; rated plausible by the owner in the plan gate
        questionnaire)
      hardware: HW-target
      rated: '2026-11-18'
      rated_by: maldun
      rating: plausible
"""
    text = edit(text, "    REQ-CHA-048:\n", "".join(entry % each for each in ("REQ-CHA-073", "REQ-CHA-074", "REQ-CHA-075", "REQ-WFM-142")) + "    REQ-CHA-048:\n", "plausibility anchor")
    start = text.index("    REQ-CHA-069:\n")
    end = text.index("\n    REQ-", start + 5) + 1
    entry69 = text[start:end]
    new69 = edit(entry69, "      hardware: HW-target\n", "      - clarified by A-160 (the line stays until the text of the end message is ready) and\n        rated again by the owner in the plan gate 2026-11-18\n      hardware: HW-target\n", "069 basis")
    new69 = edit(new69, "      rated: '2026-11-17'\n", "      rated: '2026-11-18'\n", "069 rated")
    text = text.replace(entry69, new69)
out("plausibility.yaml", text)

# ------------------------------------------------------------------------------------------------------------------ review log
text = read(log)
if "Amendment A-160: the end message of a run" not in text:
    numbers = [int(n) for n in re.findall(r"^\| D-(\d+) ", text, re.M)]
    start = int(first_id) if first_id else max(numbers) + 1
    taken = set(numbers)
    rows = [
        "**Amendment A-160: the end message of a run is bounded and stoppable, owner maldun, 2026-11-18 (first real /review).** Findings: the end message was 14 112 characters and cut at the context limit, in text and voice; the chat was blank and Stop had no effect for 16 minutes "
        "while the digest read the whole report in about 17 calls (slowed to half speed by another session's test on the same Ollama server, not a fault of the app); the end bubble sat below the command (fixed, `ba37465d`, TC-WFM-036). Decided: a digest call asks for at most 1024 tokens "
        "(REQ-CHA-073); a summary over 1200 characters is asked again once, the code never cuts (REQ-CHA-074); Stop during the end message gives the plain sentence `The run is done.` and no further call (REQ-CHA-075, decision A); the review returns a short result, the report stays in "
        "the file and the Skill run view (REQ-WFM-142, decision C); the status line stays until the text is ready (REQ-CHA-069 clarified); no time limit (decision B); the contract text is not reworded (IF-201 `done` and IF-101 `result` still say full result: a known gap).",
        "**A-160 plan gate, owner maldun, 2026-11-18 (questionnaire).** REQ-CHA-073, 074, 075, REQ-WFM-142 and REQ-CHA-069 (clarified) rated plausible one by one (`plausibility.yaml`); they stay Draft until the Commit phase; the Skill run view shows the short result in its result block "
        "and the report in its report part; the checks TC-CHA-077 to 080 and TC-WFM-142 join TR-CHAT-006. `/lookup` was seen in the app and works (the open point of D-346 for `/lookup` is closed).",
    ]
    ids, candidate = [], start
    while len(ids) < len(rows):
        if candidate not in taken:
            ids.append(candidate)
        candidate += 1
    if not text.endswith("\n"):
        text += "\n"
    text += "".join("| D-%d | %s |\n" % (n, row) for n, row in zip(ids, rows))
out("review-log.md", text)
PY
copy "$WORK/requirements-cha.md" "$REQ22"
copy "$WORK/requirements-wfm.md" "$REQ23"
copy "$WORK/test-spec-cha.md" "$TS22"
copy "$WORK/test-spec-wfm.md" "$TS23"
copy "$WORK/test-requirements.md" "$TR"
copy "$WORK/plausibility.yaml" "$PLAUS"
copy "$WORK/review-log.md" "$LOG"
finish
if [ "$do_it" = 1 ]; then
    echo "══ the model block and the checks"
    python3 -I tools/gen_node_requirements_model.py . | tail -2
    python3 -I tools/check_sysml_model.py . 2>&1 | tail -2
    "$PY" -c "import yaml; d=yaml.safe_load(open('$PLAUS')); i=d['plausibility']['items']; print('plausibility.yaml parses;', [k for k in ('REQ-CHA-069','REQ-CHA-073','REQ-CHA-074','REQ-CHA-075','REQ-WFM-142') if i.get(k,{}).get('rated')=='2026-11-18'])"
    "$PY" ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | tail -4
    echo "SysML syntax (15 s):"; bash tools/check_sysml.sh specs/mia/architecture.sysml 2>&1 | tail -2
    echo "then: git add tools/apply_amendment_a160.sh $REQ22 $REQ23 $TS22 $TS23 $TR $PLAUS $LOG specs/mia/architecture.sysml && git commit -m 'plan: A-160 requirements REQ-CHA-073 to 075, REQ-WFM-142, REQ-CHA-069 clarified, checks TC-CHA-077 to 080 and TC-WFM-142, plausibility, review log'"
fi
