#!/usr/bin/env bash
# Amendment A-158, second part (G-V3.CHAT, owner maldun, plan gate questionnaire 2026-11-17). Run after tools/apply_amendment_a158.sh.
# What changes (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found exactly once):
#   specs/mia/plausibility.yaml   the 8 ratings (plausible) of REQ-CHA-068 to 072 and REQ-CLV-053 to 055, rated_by maldun, 2026-11-17: the owner's answers of the questionnaire
#   specs/mia/review-log.md       four rows appended: A-156, A-158, the plan gate (ratings, F-04 "not now", the mock decision), the approver of the protected patches (F-07) and the open point of gate 4.
#                                 Ids: the next free ones after the highest D-number of the log (A158_FIRST_ID=nnn overrides); the parent's range decides, check before the merge with origin/goal/v3.report
#   contracts/IF-201-chat-turn.md, tests/helpers/mocks/if_201_chat_turn.py, tests/acceptance/contract/test_if_201_chat_turn.py   (protected)
#                                 the mock follows the real service: a question after the end of its run is a message and gets no line `waiting for your answer`; TC-IF-201-16
# NOT changed here: the status of the 8 requirements (Draft -> Verified happens at the Commit phase).
#   bash tools/apply_amendment_a158b.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a158b.sh --do      install and run the checks; commit afterwards with the paths named (never git add -A)
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
PLAUS=${A158_PLAUS:-specs/mia/plausibility.yaml}
LOG=${A158_LOG:-specs/mia/review-log.md}
C201=${A158_IF201:-contracts/IF-201-chat-turn.md}
MOCK=${A158_MOCK:-tests/helpers/mocks/if_201_chat_turn.py}
SUITE=${A158_SUITE:-tests/acceptance/contract/test_if_201_chat_turn.py}
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$PLAUS" "$LOG" "$C201" "$MOCK" "$SUITE" "$WORK" "${A158_FIRST_ID:-}" <<'PY'
import os
import re
import sys

plaus, log, c201, mock, suite, work, first_id = sys.argv[1:8]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def die(message):
    sys.exit("REFUSED: " + message)


def edit(text, old, new, label):
    if text.count(old) != 1:
        die("%s: the anchor was found %d times (expected once); the installed file is not what this script was made for" % (label, text.count(old)))
    return text.replace(old, new)


# ----------------------------------------------------------------------------------------------------------------------- plausibility.yaml
text = read(plaus)
if "    REQ-CHA-068:" not in text:
    items = ["REQ-CHA-068", "REQ-CHA-069", "REQ-CHA-070", "REQ-CHA-071", "REQ-CHA-072", "REQ-CLV-053", "REQ-CLV-054", "REQ-CLV-055"]
    entry = """    %s:
      basis:
      - no number, measurement or model quality depends on it; the behaviour is fixed
        by an exact acceptance criterion on a scripted run, no real model (proposal
        of the agent, 2026-11-17, A-158; rated plausible by the owner in the plan gate
        questionnaire)
      hardware: HW-target
      rated: '2026-11-17'
      rated_by: maldun
      rating: plausible
"""
    text = edit(text, "    REQ-CHA-048:\n", "".join(entry % each for each in items) + "    REQ-CHA-048:\n", "plausibility anchor")
out("plausibility.yaml", text)

# ----------------------------------------------------------------------------------------------------------------------- review log
text = read(log)
if "Amendment A-158: the chat shows a skill run like a chatbot" not in text:
    numbers = [int(n) for n in re.findall(r"^\| D-(\d+) ", text, re.M)]
    start = int(first_id) if first_id else max(numbers) + 1
    taken = set(numbers)
    rows = [
        "**Amendment A-156 (FB-09): a skill run speaks once, owner maldun, 2026-11-16.** Phase messages are not chat messages (they stay in the run status and the Skill run view); a status is noted once; the end message of the "
        "persona is the one spoken text of the run (REQ-CHA-067, REQ-CHA-041 changed); the skill gives no voice of its own for a task with end messages. Applied 2026-11-16 (`440e599b`), code `7bdd9419`, acceptance 23 of 23 green; "
        "the owner saw it in the app and judged it much better. Number collision: the G-V3.REPORT amendment is renumbered A-157 on `origin/goal/v3.report`.",
        "**Amendment A-158: the chat shows a skill run like a chatbot, owner maldun, 2026-11-17 (questionnaires).** Open point of A-156 answered: the status card is superseded by the Skill run view; the chat tells what to answer, "
        "what currently happens and the summary. Decided: one live status line, always last, updated in place; **transient** (not in the log, history or speech); a run without phases shows a generic `working` line "
        "(REQ-CHA-055 only says \"to the chat log\"); fixed wording from the manifest's phase names, no model call; interface change approved (event `chat_run_status`, IF-101 v19; IF-201 v4 turn kinds `start` and `answered`); "
        "the `/review` question is spoken (A-156 open point 2: yes). New REQ-CHA-068 to 072, REQ-CLV-053 to 055, TC-CHA-073 to 076, TC-CLV-053; tasks T-07 to T-09; contract text installed with `d962ed27`.",
        "**A-158 plan gate and Verify answers, owner maldun, 2026-11-17 (questionnaire).** The 8 requirements REQ-CHA-068 to 072 and REQ-CLV-053 to 055 are rated plausible one by one (`plausibility.yaml`); they move from Draft "
        "to Verified at the Commit phase. Decided: F-04 of the Verify report (the line is lost on a page reload; the run strip of the Skill run view shows the state) is accepted as \"not now\"; the IF-201 mock follows the real "
        "service: a question after the end of its run is a message and gets no waiting line (contract text, mock and TC-IF-201-16, `tools/apply_amendment_a158b.sh`).",
        "**A-158 protected patches and open point, owner maldun, 2026-11-17.** Finding F-07 of the Verify report: the patches of the protected files of A-156 and A-158 were applied and committed by the owner (`7a750eea`, "
        "`907ef3fa`, `aa2150b5`, `be60bf2a`, `97122a8a`, `599d6590`; the contract text with `d962ed27`). Open point (gate 4): no real `/lookup` or `/review` run has been looked at in the app yet, only the scripted stub run; "
        "the 8 requirements are rated on the scripted checks.",
    ]
    ids = []
    candidate = start
    while len(ids) < len(rows):
        if candidate not in taken:
            ids.append(candidate)
        candidate += 1
    if not text.endswith("\n"):
        text += "\n"
    text += "".join("| D-%d | %s |\n" % (n, row) for n, row in zip(ids, rows))
out("review-log.md", text)

# ----------------------------------------------------------------------------------------------------------------------- contract, mock, suite
text = read(c201)
if "unless its run has ended" not in text:
    text = edit(text, "A `question` is followed by the line `waiting for your answer` (REQ-CHA-070);",
                "A `question` is followed by the line `waiting for your answer` (REQ-CHA-070), unless its run has ended (a late question is a message and leaves no line);", "IF-201 question")
    text = edit(text, "the contract suite gets TC-IF-201-13 to -15 and TC-IF-201-09, -10, -12 follow A-156", "the contract suite gets TC-IF-201-13 to -16 and TC-IF-201-09, -10, -12 follow A-156", "IF-201 history")
out("IF-201-chat-turn.md", text)

text = read(mock)
if "_ended" not in text:
    text = edit(text, "        self._lines = {}  ", "        self._ended = set()                                                   # v4 (A-158): the runs that ended; a late question of one gets no line\n        self._lines = {}  ", "mock init")
    text = edit(text, "            self._lines.pop(run, None)\n            self._line(run, None)", "            self._lines.pop(run, None)\n            self._ended.add(run)\n            self._line(run, None)", "mock end")
    text = edit(text, "        if kind == \"question\":\n            self._line(run, self.WAITING)                                    # REQ-CHA-070; the mock knows no ended run, so it always sends it",
                "        if kind == \"question\" and run not in self._ended:\n            self._line(run, self.WAITING)                                    # REQ-CHA-070; a question after the end of its run leaves no line, as in the real service", "mock question")
out("if_201_chat_turn.py", text)

text = read(suite)
if "TC-IF-201-16" not in text:
    new_test = '''

    @mark.req("IF-201", "REQ-CHA-070")
    @each_provider(IF, make(phases=("screening",)))
    def test_a_late_question_of_an_ended_run_gets_no_line(self, chat):
        """TC-IF-201-16 (v4): a question that arrives after the end of its run is a message and gets no line `waiting for your answer`.
        Example: screening, done, then the question "Which period?" -> the message, no line after it."""
        # Given: a run that has ended, and a subscriber
        seen = []
        chat.subscribe(seen.append)
        chat.skill_turn("anna", "r1", "phase", "screening")
        chat.skill_turn("anna", "r1", "done", "All done.")
        chat.settle()
        first = len(seen)
        # When: a question of that run arrives late
        ack = chat.skill_turn("anna", "r1", "question", "Which period?")
        # Then: it is a message and no line follows it
        chat.settle()
        self.assertTrue(ack["id"])
        self.assertEqual([e["event"] for e in seen[first:] if e["event"] in ("chat_message", "chat_run_status")], ["chat_message"])
'''
    text = edit(text, '\n\nif __name__ == "__main__":', new_test + '\n\nif __name__ == "__main__":', "suite end")
out("test_if_201_chat_turn.py", text)
PY
copy "$WORK/plausibility.yaml" "$PLAUS"
copy "$WORK/review-log.md" "$LOG"
copy "$WORK/IF-201-chat-turn.md" "$C201"
copy "$WORK/if_201_chat_turn.py" "$MOCK"
copy "$WORK/test_if_201_chat_turn.py" "$SUITE"
finish
if [ "$do_it" = 1 ]; then
    echo "══ checks"
    "$PY" -c "import yaml,sys; d=yaml.safe_load(open('$PLAUS')); i=d['plausibility']['items']; print('plausibility.yaml parses;', sum(1 for k in i if k in ('REQ-CHA-068','REQ-CHA-069','REQ-CHA-070','REQ-CHA-071','REQ-CHA-072','REQ-CLV-053','REQ-CLV-054','REQ-CLV-055')), 'of 8 A-158 items present')"
    "$PY" "$SUITE" 2>&1 | tail -3
    echo "then: git add tools/apply_amendment_a158b.sh $PLAUS $LOG $C201 $MOCK $SUITE && git commit -m 'plan: A-158 plausibility of the 8 requirements, review log, mock follows the real service (TC-IF-201-16)'"
fi
