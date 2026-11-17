#!/usr/bin/env bash
# Amendment A-158 (G-V3.CHAT, approved by the owner 2026-11-17): the contract text for the status line of a skill run. Source: specs/mia/goals/G-V3.CHAT/amendment-a158/IF-101-change.md
# Files that change (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found exactly once, so a second
# --do changes nothing):
#   contracts/IF-101-chat-api.md      v18 -> v19: the event `chat_run_status` {run, text} in the events table, version history
#   contracts/IF-201-chat-turn.md     v3 -> v4: the turn kinds `start` and `answered`, the status line, the event in `subscribe`; also what A-156 changed in v3's text: a `phase` is no message
#   tests/helpers/mocks/if_201_chat_turn.py   the mock follows (kinds, line state, event, order)                                   (protected)
#   tests/acceptance/contract/test_if_201_chat_turn.py   TC-IF-201-13 to -15 are new; TC-IF-201-09, -10, -12 follow A-156 (they are red since A-156: they expect a message per declared phase)   (protected)
# NOT changed here (separate steps): the review log row (D-nnn), TR-CHAT-010's "Applies to:" line, the status of the 8 Draft requirements.
#   bash tools/apply_amendment_a158.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a158.sh --do      install and run the checks; commit afterwards with the paths named (never git add -A)
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
C101=${A158_IF101:-contracts/IF-101-chat-api.md}
C201=${A158_IF201:-contracts/IF-201-chat-turn.md}
MOCK=${A158_MOCK:-tests/helpers/mocks/if_201_chat_turn.py}
SUITE=${A158_SUITE:-tests/acceptance/contract/test_if_201_chat_turn.py}
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$C101" "$C201" "$MOCK" "$SUITE" "$WORK" <<'PY'
import os
import sys

c101, c201, mock, suite, work = sys.argv[1:6]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def die(message):
    sys.exit("REFUSED: " + message)


def edit(text, old, new, label):
    """one exact replacement; refused when the anchor is not found exactly once"""
    if text.count(old) != 1:
        die("%s: the anchor was found %d times (expected once); the installed file is not what this script was made for" % (label, text.count(old)))
    return text.replace(old, new)


def after_line(text, prefix, line, label):
    """insert `line` after the one line that starts with `prefix`"""
    lines = text.split("\n")
    hits = [i for i, each in enumerate(lines) if each.startswith(prefix)]
    if len(hits) != 1:
        die("%s: %d lines start with %r (expected one)" % (label, len(hits), prefix))
    lines.insert(hits[0] + 1, line)
    return "\n".join(lines)


# ----------------------------------------------------------------------------------------------------------------------------- IF-101 v19
text = read(c101)
if "chat_run_status" not in text:
    text = edit(text, "# IF-101 – Chat, expression, audio and REST API, v18", "# IF-101 – Chat, expression, audio and REST API, v19", "IF-101 title")
    text = after_line(text, "| `skill_run_changed` **[v16]**",
                      "| `chat_run_status` **[v19]** | `{run, text}`: the status line of a skill run. `run` is the run id; `text` is the phase name of the manifest, `working` or `waiting for your answer`, or `null`, "
                      "which clears the line and comes before the end message of the run. It is no chat message: no id, not in the log or the history, not spoken. A page that does not know "
                      "the event ignores it. After a reload the line is not restored; the run strip of the Skill run view shows the state (REQ-CHA-068 to 071, REQ-CLV-038) |", "IF-101 events")
    text = after_line(text, "| v18 |",
                      "| v19 | 2026-11-17 | the event `chat_run_status` `{run, text}`: the status line of a skill run, phase name, `working`, `waiting for your answer`, or `null` to clear; no message, "
                      "not stored, not spoken (REQ-CHA-068 to 071; owner 2026-11-17) | A-158 |", "IF-101 history")
out("IF-101-chat-api.md", text)

# ----------------------------------------------------------------------------------------------------------------------------- IF-201 v4
text = read(c201)
if "chat_run_status" not in text:
    text = edit(text, "# IF-201 – Chat turn service, v3", "# IF-201 – Chat turn service, v4", "IF-201 title")
    text = edit(text, "`kind` `question` (payload: the question text), `phase` (the phase name; only phases the manifest declares worth telling), `done`",
                "`kind` `question` (payload: the question text), `phase` (the phase name; only phases the manifest declares count), **[v4]** `start` (payload ignored), `answered` (payload: the answer text), `done`",
                "IF-201 kinds")
    text = edit(text, "or `{\"id\": null}` when the turn adds no message (an undeclared phase)", "or `{\"id\": null}` when the turn adds no message (**[v4]** every `phase`, `start` and `answered`)", "IF-201 id")
    text = edit(text, "`counters_changed` **[v2]**;", "`counters_changed` **[v2]**, `chat_run_status` **[v4]**;", "IF-201 subscribe")
    rows = text.split("\n")
    hits = [i for i, each in enumerate(rows) if each.startswith("| `skill_turn(account, run, kind, payload)` **[v3]**")]
    if len(hits) != 1 or not rows[hits[0]].endswith(" |"):
        die("IF-201 skill_turn row: not found once or not a table row")
    rows[hits[0]] = rows[hits[0]][:-2] + (
        " **[v4, A-156, A-158]** A `phase`, `start` or `answered` turn is no message: it feeds the status line of the run, the event `chat_run_status` `{run, text}` of IF-101 v19 "
        "(no record, not in `history`, not spoken, REQ-CHA-068). A declared `phase` that changed gives the line with its name (a repeat or an undeclared phase gives none); `start` gives `working` "
        "for a run without declared phases and nothing for a run with phases; `answered` gives the line of the current phase again, or `working`. A `question` is followed by the line "
        "`waiting for your answer` (REQ-CHA-070); `done`, `failed` and `stopped` send the clearing line (`text: null`) before the end message, which is then the last event of the run (REQ-CHA-069); "
        "a failing line never stops the run (REQ-CHA-071). The status messages per phase of v3 are gone (A-156, REQ-CHA-041) |")
    text = "\n".join(rows)
    text = after_line(text, "| v3 |",
                      "| v4 | 2026-11-17 | the turn kinds `start` and `answered` of `skill_turn`, the event `chat_run_status` (IF-101 v19) for the status line of a run; a `phase` adds no message any more (A-156: a skill run speaks once, "
                      "its status is the line and the Skill run view); the contract suite gets TC-IF-201-13 to -15 and TC-IF-201-09, -10, -12 follow A-156 (owner 2026-11-17) | A-158 |", "IF-201 history")
out("IF-201-chat-turn.md", text)

# ----------------------------------------------------------------------------------------------------------------------------- the mock
text = read(mock)
if "chat_run_status" not in text:
    text = edit(text, "        self._callbacks = []\n", "        self._callbacks = []\n        self._lines = {}                                                      # v4 (A-158): the status line of each run\n", "mock init")
    start = text.find("    # v3 (amendment A-142): the turns of a skill run")
    end = text.find("    def advance_time")
    if start < 0 or end < start or text.count("    def advance_time") != 1:
        die("mock: the skill_turn block was not found")
    block = '''    # v3 (amendment A-142), v4 (A-158): the turns of a skill run; the mock words them by rule, the real step words them in persona (REQ-CHA-054).
    # A phase, start or answered turn is no message: it gives the status line, the event chat_run_status (no record, no history, no speech; REQ-CHA-068).
    KINDS = ("question", "phase", "start", "answered", "done", "failed", "stopped")
    WORKING, WAITING = "working", "waiting for your answer"

    def _line(self, run, text):
        self._api._broadcast("chat_run_status", {"run": run, "text": text})

    def skill_turn(self, account, run, kind, payload):
        if kind not in self.KINDS:
            raise ServiceError("invalid_kind")
        if kind in ("phase", "start", "answered"):
            if kind == "phase":
                if payload not in self._phases or self._lines.get(run) == payload:
                    return {"id": None}                                      # undeclared or repeated: no line
                self._lines[run] = payload
            elif kind == "start":
                if self._phases:
                    return {"id": None}                                      # the first declared phase gives the first line
                self._lines[run] = self.WORKING
            else:
                self._lines.setdefault(run, self.WORKING)
            self._line(run, self._lines[run])
            self._forward()
            return {"id": None}
        link = " [Open in the Skill run view](#run=%s)" % run                # added by code (REQ-CHA-056)
        if kind == "question":
            text = payload
        elif kind == "done":
            text = payload[:1200] + link                                     # the real summary is worded by the digest step; the full result never goes into the chat
        elif kind == "failed":
            text = "%s%s" % (payload, link)
        else:
            text = "The run was stopped (%s).%s" % (payload, link)
        if kind in ("done", "failed", "stopped"):
            self._lines.pop(run, None)
            self._line(run, None)                                            # the line goes before the end message (REQ-CHA-069)
        record = self._api._record("assistant", "MIA", text)
        record["skill_run"], record["kind"] = run, kind
        self._api._broadcast("chat_message", record)
        for index, sentence in enumerate(s for s in text.replace("?", "?|").replace(".", ".|").replace("!", "!|").split("|") if s.strip()):
            self._api._broadcast("audio_chunk", {"id": record["id"], "index": index, "sentence": sentence.strip()})      # spoken with the repair of REQ-CHA-014 (REQ-CHA-047)
        if kind == "question":
            self._line(run, self.WAITING)                                    # REQ-CHA-070; the mock knows no ended run, so it always sends it
        self._forward()
        return {"id": record["id"]}

'''
    text = text[:start] + block + text[end:]
out("if_201_chat_turn.py", text)

# ----------------------------------------------------------------------------------------------------------------------------- the contract suite
text = read(suite)
if "TC-IF-201-13" not in text:
    text = edit(text, '"""IF-201 v3 (A-142): the turns of a skill run in the chat (G-V3.CHAT)."""', '"""IF-201 v3 (A-142) and v4 (A-158): the turns of a skill run in the chat and its status line (G-V3.CHAT)."""', "suite class")
    # TC-IF-201-09: a phase is no message since A-156
    text = edit(text, "with kind question, phase, done, failed or stopped adds one message", "with kind question, done, failed or stopped adds one message", "TC-09 doc")
    text = edit(text, 'turns = [("question", "Which period?"), ("phase", "screening"), ("done", full),', 'turns = [("question", "Which period?"), ("done", full),', "TC-09 turns")
    text = edit(text, "for i in ids[2:]:", "for i in ids[1:]:", "TC-09 end messages")
    text = edit(text, 'self.assertIn("the scholarly service is down", by_id[ids[3]]["text"])', 'self.assertIn("the scholarly service is down", by_id[ids[2]]["text"])', "TC-09 failed")
    text = edit(text, 'self.assertLess(len(by_id[ids[2]]["text"]), len(full))', 'self.assertLess(len(by_id[ids[1]]["text"]), len(full))', "TC-09 summary")
    text = edit(text, "for i in ids[:2]:\n            self.assertNotIn", "for i in ids[:1]:\n            self.assertNotIn", "TC-09 question")
    # TC-IF-201-10: no phase adds a message, a declared one gives the line
    text = edit(text, "TC-IF-201-10 (v3): a phase that the manifest of the skill does not declare gives `{\"id\": None}` and adds no message and no event; a declared phase gives a message.",
                "TC-IF-201-10 (v3, v4): a phase that the manifest of the skill does not declare gives `{\"id\": None}` and adds no message and no event; a declared phase gives `{\"id\": None}` too and adds no message, only the status line (TC-IF-201-13).", "TC-10 doc")
    text = edit(text, '''        # Then: the first adds no message and no event, the second adds one message
        chat.settle()
        self.assertEqual((len(chat.history()), seen), (before, []))
        ack = chat.skill_turn("anna", "r1", "phase", "screening")
        self.assertTrue(ack["id"])
        self.assertEqual(len(chat.history()), before + 1)''', '''        # Then: the first adds no message and no event, the second adds no message either (A-156) but the event of the status line
        chat.settle()
        self.assertEqual((len(chat.history()), seen), (before, []))
        self.assertEqual(chat.skill_turn("anna", "r1", "phase", "screening"), {"id": None})
        chat.settle()
        self.assertEqual(len(chat.history()), before)
        self.assertEqual([e["event"] for e in seen if e["event"] in ("chat_message", "chat_run_status")], ["chat_run_status"])''', "TC-10 body")
    # TC-IF-201-12: only messages are spoken
    text = edit(text, 'for kind, payload in (("question", "Which period?"), ("phase", "screening"), ("done", "All done."))]', 'for kind, payload in (("question", "Which period?"), ("done", "All done."))]', "TC-12 turns")
    text = edit(text, "# When: a question, a phase and a summary are added, and an undeclared phase", "# When: a question and a summary are added, and a declared and an undeclared phase", "TC-12 when")
    text = edit(text, '        self.assertIsNone(chat.skill_turn("anna", "r1", "phase", "indexing")["id"])\n',
                '        self.assertIsNone(chat.skill_turn("anna", "r1", "phase", "screening")["id"])\n        self.assertIsNone(chat.skill_turn("anna", "r1", "phase", "indexing")["id"])\n', "TC-12 phases")
    new_tests = '''

    @mark.req("IF-201", "REQ-CHA-068", "REQ-CHA-071")
    @each_provider(IF, make(phases=("screening", "reading")))
    def test_the_status_line_follows_the_declared_phases_and_is_no_message(self, chat):
        """TC-IF-201-13 (v4): the events chat_run_status `{run, text}` carry the declared phases in order; a repeated phase and an undeclared one give none; `start` of a run with phases gives none; no turn adds a message, a history record or speech.
        Example: start, screening, screening, indexing, reading -> the lines screening, reading."""
        # Given: a skill that declares screening and reading, and a subscriber
        seen = []
        chat.subscribe(seen.append)
        before = len(chat.history())
        # When: the run starts and enters its phases, one of them twice, and an undeclared one
        for kind, payload in (("start", ""), ("phase", "screening"), ("phase", "screening"), ("phase", "indexing"), ("phase", "reading")):
            self.assertEqual(chat.skill_turn("anna", "r1", kind, payload), {"id": None})
        # Then: the lines are the two declared phases in order, and nothing else was added
        chat.settle()
        self.assertEqual([e["payload"] for e in seen if e["event"] == "chat_run_status"], [{"run": "r1", "text": "screening"}, {"run": "r1", "text": "reading"}])
        self.assertEqual(len(chat.history()), before)
        self.assertEqual([e for e in seen if e["event"] in ("chat_message", "audio_chunk")], [])

    @mark.req("IF-201", "REQ-CHA-068", "REQ-CHA-070")
    @each_provider(IF, make(phases=()))
    def test_a_run_without_phases_shows_working_and_a_question_shows_that_it_waits(self, chat):
        """TC-IF-201-14 (v4): `start` of a run without declared phases gives the line `working`; a question is followed by the line `waiting for your answer`; `answered` gives the line `working` again; the line never comes before its question.
        Example: start, question "Which period?", answered "2020" -> working, message, waiting for your answer, working."""
        # Given: a skill without declared phases and a subscriber
        seen = []
        chat.subscribe(seen.append)
        # When: the run starts, asks a question and gets the answer
        chat.skill_turn("anna", "r1", "start", "")
        chat.skill_turn("anna", "r1", "question", "Which period?")
        chat.skill_turn("anna", "r1", "answered", "2020")
        # Then: the lines and the question message come in this order (other events, such as the voice, do not count)
        chat.settle()
        order = [(e["event"], e["payload"]["text"] if e["event"] == "chat_run_status" else e["payload"]["kind"]) for e in seen if e["event"] in ("chat_run_status", "chat_message")]
        self.assertEqual(order, [("chat_run_status", "working"), ("chat_message", "question"), ("chat_run_status", "waiting for your answer"), ("chat_run_status", "working")])

    @mark.req("IF-201", "REQ-CHA-069")
    @each_provider(IF, make(phases=("screening",)))
    def test_the_line_is_cleared_before_the_end_message(self, chat):
        """TC-IF-201-15 (v4): for done, failed and stopped the clearing line `{run, text: null}` comes before the end message, and no line of that run follows it.
        Example: screening, then done -> the lines screening, null, then the message of kind done, nothing after."""
        # Given: a skill that declares screening and a subscriber
        seen = []
        chat.subscribe(seen.append)
        for kind, payload in (("done", "All done."), ("failed", "the service is down"), ("stopped", "stopped by the user")):
            with self.subTest(kind=kind):
                # When: a run is in its phase and then ends
                first = len(seen)
                chat.skill_turn("anna", "r-" + kind, "phase", "screening")
                chat.skill_turn("anna", "r-" + kind, kind, payload)
                chat.settle()
                # Then: the clearing line comes before the end message and nothing of the run's line follows
                order = [(e["event"], e["payload"]["text"] if e["event"] == "chat_run_status" else e["payload"]["kind"]) for e in seen[first:] if e["event"] in ("chat_run_status", "chat_message")]
                self.assertEqual(order, [("chat_run_status", "screening"), ("chat_run_status", None), ("chat_message", kind)])
'''
    text = edit(text, '\n\nif __name__ == "__main__":', new_tests + '\n\nif __name__ == "__main__":', "suite end")
out("test_if_201_chat_turn.py", text)
PY
copy "$WORK/IF-101-chat-api.md" "$C101"
copy "$WORK/IF-201-chat-turn.md" "$C201"
copy "$WORK/if_201_chat_turn.py" "$MOCK"
copy "$WORK/test_if_201_chat_turn.py" "$SUITE"
finish
if [ "$do_it" = 1 ]; then
    echo "══ checks"
    "$PY" "$SUITE" 2>&1 | tail -4
    "$PY" tests/acceptance/contract/test_if_101_chat_api.py 2>&1 | tail -3
    "$PY" tests/acceptance/test_chat_skill_turns.py 2>&1 | tail -3
    "$PY" tests/test_chat_views_browser.py 2>&1 | tail -3
    node --test "tests/js/multiuser.test.mjs" 2>&1 | grep -E "^# (pass|fail)"
    echo "then: git add $C101 $C201 $MOCK $SUITE && git commit -m 'contracts: A-158 installed (IF-101 v19, IF-201 v4, mock, TC-IF-201-13..15; TC-IF-201-09,-10,-12 follow A-156)'"
fi
