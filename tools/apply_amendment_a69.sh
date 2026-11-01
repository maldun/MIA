#!/usr/bin/env bash
# Amendment A-69 (first Verify of N-2.2, N-2.3, N-2.5; owner decisions D-173, 2026-11-01): three deferrals are recorded (TD-09 history deletion, TD-10 persona
# check dialogues, TD-11 voice through IF-204), TD-03 and TD-04 are confirmed, and the three requirements carry the Relaxed/Target lines.
# Note: specs/mia/amendments/A-69/A-69-note.md
# Protected files that change (all made from the INSTALLED files at run time, each edit refused when its anchor is not found exactly once):
#   specs/mia/deferred.md                                                  new TD-09, TD-10, TD-11; the Decision line of TD-03 and TD-04 says confirmed
#   specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md     REQ-CHA-005 `Relaxed: TD-09`, REQ-CHA-008 `Relaxed: TD-10` and their Target lines
#   specs/mia/nodes/N-2-backend/nodes/N-2.5-voice-synthesis/requirements.md REQ-VOI-001 `Relaxed: TD-11` and its Target line
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a69.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a69.sh --do      install and run the trace check for the three TDs; commit afterwards as "plan: A-69 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
N22=specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md
N25=specs/mia/nodes/N-2-backend/nodes/N-2.5-voice-synthesis/requirements.md
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - specs/mia/deferred.md "$N22" "$N25" "$WORK" <<'PY'
import os
import re
import sys
deferred, n22, n25, work = sys.argv[1:5]
read = lambda path: open(path, encoding="utf-8").read()


def write(name, text):
    open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def once(text, old, new, where, what):
    """old -> new exactly once; a text that has the new part already is left as it is (the copy then reports unchanged)"""
    if new in text:
        return text
    if text.count(old) != 1:
        sys.exit("%s: %s is not found exactly once; install A-69 by hand" % (where, what))
    return text.replace(old, new)


text = read(deferred)
confirmed = "- Decision: D-173, 2026-11-01, Stefan Reiterer\n"
proposed = "- Decision: proposed 2026-10-29, to be confirmed by Stefan Reiterer\n"
for td in ("TD-03", "TD-04"):
    match = re.search(r"## %s .*?(?=\n## |\Z)" % td, text, re.S)
    if not match:
        sys.exit("%s: %s is missing" % (deferred, td))
    block = match.group(0)
    if confirmed in block:
        continue
    if block.count(proposed) != 1:
        sys.exit("%s: the Decision line of %s is not found exactly once" % (deferred, td))
    text = text.replace(block, block.replace(proposed, confirmed))
NEW = '''
## TD-09 – Deleting the chat history after a confirmation
- Kind: defer
- Requirement: REQ-CHA-005
- Interim criterion: the history is bounded and the oldest messages are dropped over the limit (`test_oldest_are_dropped_over_the_limit`); the only deletion is the token-guarded legacy route `POST /api/chat/clear`, which the page does not offer
- Target: a user deletes the history on the page after a confirmation dialog; the backend refuses a deletion without `confirm: true`; the IF-101 contract names the operation
- Reason: no page control and no confirmation parameter exist; privacy is not an issue for now (D-131); it needs an IF-101 amendment and a page change
- Effort: about half a day (backend flag, button and dialog, amendment, tests)
- Risk of the gap: a user cannot delete the history on his or her own. Mitigation: the operator deletes the `history` records
- Owner: Stefan Reiterer
- Trigger: the first request to delete a history, or 2026-12-31, whichever first
- Target check: specified only
- Sign-off: Stefan Reiterer, 2026-11-01
- Decision: D-173, 2026-11-01, Stefan Reiterer
- Status: open

## TD-10 – Persona check dialogues (AC-8)
- Kind: defer
- Requirement: REQ-CHA-008
- Interim criterion: the persona file is read at every call, the default address is "master", and the persona message is the system message of every call (`tests/test_persona_prompt.py`)
- Target: AC-8 is decided statistically: check dialogues against the baseline of today's MIA, with the rule fixed in Plan (D-52)
- Reason: it needs the labelled dialogues and a baseline run; the owner postponed it to after the field test (2026-10-26)
- Effort: about one day plus GPU time
- Risk of the gap: the persona can drift without a number. Mitigation: the owner's use
- Owner: Stefan Reiterer
- Trigger: the first iteration after the field test
- Target check: specified only
- Decision: D-173, 2026-11-01, Stefan Reiterer
- Status: open

## TD-11 – The voice goes through IF-204
- Kind: defer
- Requirement: REQ-VOI-001
- Interim criterion: the app speaks through `SpeechStreamer` and `Speaker.render_voice` with the `speech_text` filter; `SpeechService` passes the IF-204 contract suite and TC-VOI-001 to -003
- Target: the chat agent's audio goes through `SpeechService`, the `audio_chunk` event of an answer is built, and the skipped cases of IF-201 and IF-101 and the integration step 1 of N-2 run green
- Reason: the older route works on the host; changing it risks the working voice for no gain to the user now
- Effort: about one day
- Risk of the gap: two routes may diverge. Mitigation: both use `speech_text` and `render_voice`
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration, or 2026-12-31, whichever first
- Target check: skip: the IF-204 side of the chat is not wired (TD-11); the skipped cases carry deferred('TD-11') until green
- Decision: D-173, 2026-11-01, Stefan Reiterer
- Status: open
'''
if "## TD-09 " not in text:
    text = text.rstrip("\n") + "\n" + NEW
write("deferred.md", text)


def relax(path, name, req, td, target, hist):
    body = read(path)
    match = re.search(r"### %s .*?(?=\n### |\Z)" % req, body, re.S)
    if not match:
        sys.exit("%s: %s is missing" % (path, req))
    block = match.group(0)
    if "- Relaxed: %s\n" % td in block:
        write(name, body)
        return
    old = "- Status: Approved\n- History: –\n"
    if block.count(old) != 1:
        sys.exit("%s: the Status/History lines of %s are not found exactly once" % (path, req))
    new = "- Status: Approved\n- Relaxed: %s\n- Target: %s\n- History: A-69 (2026-11-01): Relaxed %s (%s)\n" % (td, target, td, hist)
    write(name, body.replace(block, block.replace(old, new)))


relax(n22, "n22.md", "REQ-CHA-005", "TD-09", "a user deletes the history on the page after a confirmation dialog, and the backend refuses a deletion without a confirmation", "D-173")
# a second requirement of the same file: edit the result of the first
first = read(os.path.join(work, "n22.md"))
open(os.path.join(work, "n22-in.md"), "w", encoding="utf-8").write(first)
relax(os.path.join(work, "n22-in.md"), "n22.md", "REQ-CHA-008", "TD-10", "AC-8 is decided: the check dialogues pass at the rate fixed in Plan against the recorded baseline", "D-173")
relax(n25, "n25.md", "REQ-VOI-001", "TD-11", "the chat agent's audio goes through the speech interface IF-204 and an audio_chunk event carries each sentence", "D-173")
PY
copy "$WORK/deferred.md" specs/mia/deferred.md
copy "$WORK/n22.md" "$N22"
copy "$WORK/n25.md" "$N25"
finish
echo
echo "== trace_check, errors naming the new deferrals (none expected)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E 'ERROR.*(TD-09|TD-10|TD-11)' || echo "none"
