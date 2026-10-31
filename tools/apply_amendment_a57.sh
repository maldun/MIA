#!/usr/bin/env bash
# Amendment A-57 (N-2.2 T-06, D-156, 2026-10-31): IF-101 records that a minus vote is followed by `expression {name: "shocked"}` (REQ-CHV-006); the mock sends it.
# Protected files that change (both BUILT FROM THE INSTALLED FILES at run time, so A-54 may come before or after; see the note):
#   contracts/IF-101-chat-api.md              the title one version up, one sentence at the end of the vote row, one row in the version history
#   tests/helpers/mocks/if_101_chat_api.py    vote: a minus also broadcasts expression {name: "shocked"} after the score event
# Note: specs/mia/amendments/A-57/A-57-note.md. If A-54 is installed AFTER this one, run this script with --do again (A-54 copies whole files).
# INSTALL IT ON THE LINE OF WORK goal/v1 after the merge of v1-n22.
#   bash tools/apply_amendment_a57.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a57.sh --do      install and run the IF-101 suite in the image; commit afterwards as "plan: A-57 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
CONTRACT=$(mktemp)
MOCK=$(mktemp)
trap 'rm -f "$CONTRACT" "$MOCK"' EXIT
python3 - contracts/IF-101-chat-api.md "$CONTRACT" tests/helpers/mocks/if_101_chat_api.py "$MOCK" <<'PY'
import re
import sys
contract_in, contract_out, mock_in, mock_out = sys.argv[1:5]
MARK = 'a minus (value -1) is followed by the event `expression {name: "shocked"}`'

text = open(contract_in, encoding="utf-8").read()
if MARK not in text:
    title = re.search(r"^(# IF-101 .*, v)(\d+)$", text, re.M)
    vote = [line for line in text.splitlines() if line.startswith("| `vote(session, subject, category, value)`")]
    if title is None or len(vote) != 1 or not vote[0].endswith(" |"):
        sys.exit("contracts/IF-101-chat-api.md: the title or the vote row is not found exactly once; install A-57 by hand")
    version = int(title.group(2)) + 1
    rows = [line for line in text.splitlines() if re.match(r"\| v%d \| " % (version - 1), line)]
    if len(rows) != 1:
        sys.exit("contracts/IF-101-chat-api.md: the version row v%d is not found exactly once; install A-57 by hand" % (version - 1))
    sentence = ('; **[v%d]** %s to every connected page, with the shocked line on the audio route; the face of the current mood follows '
                'after the line (REQ-CHV-006, D-143, D-156)' % (version, MARK))
    text = text.replace(title.group(0), title.group(1) + str(version), 1)
    text = text.replace(vote[0], vote[0][:-2] + sentence + " |", 1)
    text = text.replace(rows[0], rows[0] + "\n| v%d | 2026-10-31 | `vote`: a minus is followed by the event `expression {name: \"shocked\"}` and the shocked line, "
                        "then the face of the mood (REQ-CHV-006, D-156) | A-57 |" % version, 1)
open(contract_out, "w", encoding="utf-8").write(text)

mock = open(mock_in, encoding="utf-8").read()
anchor = '        self._broadcast("score", score)\n        return {"stored": True, "score": score}\n'
if '"expression", {"name": "shocked"}' not in mock:
    if mock.count(anchor) != 1:
        sys.exit("tests/helpers/mocks/if_101_chat_api.py: the end of vote is not found exactly once; install A-57 by hand")
    mock = mock.replace(anchor, '        self._broadcast("score", score)\n'
                                '        if value == -1:\n'
                                '            self._broadcast("expression", {"name": "shocked"})      # A-57: a minus hurts her (REQ-CHV-006, D-156)\n'
                                '        return {"stored": True, "score": score}\n')
open(mock_out, "w", encoding="utf-8").write(mock)
PY
copy "$CONTRACT" contracts/IF-101-chat-api.md
copy "$MOCK" tests/helpers/mocks/if_101_chat_api.py
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py
