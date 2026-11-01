#!/usr/bin/env bash
# Amendment A-61 (N-3.3 Verify, owner decisions D-161: F3, F5, F8; D-162: the IF-101 mock): IF-302 v6, a document that is not a mapping is rule `schema`
# in every table, and a vote value is an integer (a boolean or a float such as 1.0 is rule `schema`, detail `value`); the IF-302 mock does both, as the
# Record tables do; the IF-101 mock refuses a vote of 1.0 as the chat service does.
# Protected files that change:
#   contracts/IF-302-record-tables.md                          v6: the two `schema` cases, golden example 4, the version line ("draft v0" dropped from the header)
#   tests/helpers/mocks/if_302_record_tables.py                a non-mapping is `schema` in every table; a bool or float vote value is `schema`
#   tests/acceptance/contract/test_if_302_record_tables.py     TC-IF-302-07 (golden 4)
#   contracts/IF-101-chat-api.md                               one version up: the vote value is the integer 1 or -1 (1.0 or true is 422 invalid_vote, rule value)
#   tests/helpers/mocks/if_101_chat_api.py                     vote: `type(value) is not int` instead of `isinstance(value, bool)`
#   tests/acceptance/contract/test_if_101_chat_api.py          TC-IF-101-32 (mock and real)
#   specs/mia/test-spec.md                                     the rows TC-IF-302-04..07 after TC-IF-302-03 (F8) and TC-IF-101-32 after the last TC-IF-101 row
# The four IF-101 and test-spec changes are BUILT FROM THE INSTALLED FILES at run time (A-54 and A-57 change IF-101 first; if A-54, which copies whole
# files, is installed after this one, run this script with --do again). The IF-302 files are N-3.3's own and are copied whole.
# Also (node file, made from the installed file): the node requirements.md of N-3.3, IF-302 `Verified by: TC-IF-302-01..07` and its History.
# The real sides are green once branch v1-n33b is merged: record_tables.py and chat_service.py refuse a float or bool vote value (F3/F5 fix).
# The vote categories for N-2.2 are not here: they go through IF-102 (D-162, A-59).
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1), after A-54 and A-57 and the merge of v1-n33b.
#   bash tools/apply_amendment_a61.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a61.sh --do      install, run the IF-302 suite and the IF-101 suite in the image; commit afterwards as "plan: A-61 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-61
D=specs/mia/contract-drafts
NODE=specs/mia/nodes/N-3-database/nodes/N-3.3-memories-history-feedback/requirements.md
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
python3 - specs/mia/test-spec.md "$TMP/test-spec.md" <<'PY'
import sys
after = "| TC-IF-302-03 | IF-302 | Contract | 1 (mock) and 2 (real) | a memory record needs a source (rule schema, detail source); text with newlines, quotes and non-ASCII characters is valid; a foreign table is a ValueError. | exact |"
rows = [
    "| TC-IF-302-04 | IF-302 | Contract | 1 (mock) and 2 (real) | v2: a memory record's kind (fact, preference, commitment) and status (active, replaced) are checked when present, subject and updated are free; a record of v1 stays valid; the source stays required. | exact |",
    "| TC-IF-302-05 | IF-302 | Contract | 1 (mock) and 2 (real) | v3: the status of workflow_meta is required and one of draft, tested, trusted, retired; specification and benchmark are free. | exact |",
    "| TC-IF-302-06 | IF-302 | Contract | 1 (mock) and 2 (real) | v4, v5: a reports record needs task, skill, skill_version, question, account, model_pin and report; a missing field is rule schema with that field as detail; the table is versioned and not deletable. | exact |",
    "| TC-IF-302-07 | IF-302 | Contract | 1 (mock) and 2 (real) | golden 4 (v6, A-61): a document that is not a mapping is rule schema in every table; a vote value 1.0, -1.0, True or False is rule schema, detail value. | exact |",
]
row_101 = "| TC-IF-101-32 | IF-101 | Contract | 1 (mock) and 2 (real) | A-61 (D-162): a vote value 1.0, -1.0 or True is 422 invalid_vote with the rule value and is not stored. | exact |"
text = open(sys.argv[1], encoding="utf-8").read()
if after not in text:
    sys.exit("the row of TC-IF-302-03 is not where A-61 expects it: check specs/mia/test-spec.md")
missing = [row for row in rows if row not in text]
if missing and len(missing) != len(rows):
    sys.exit("some rows TC-IF-302-04..07 are there and some not: check specs/mia/test-spec.md")
if missing:
    text = text.replace(after, "\n".join([after] + rows))
if row_101 not in text:
    lines = text.split("\n")
    last = max(i for i, line in enumerate(lines) if line.startswith("| TC-IF-101-"))
    lines.insert(last + 1, row_101)
    text = "\n".join(lines)
open(sys.argv[2], "w", encoding="utf-8").write(text)
PY
python3 - "$NODE" "$TMP/requirements.md" <<'PY'
import sys
old_by, new_by = "- Verified by: TC-IF-302-01..03\n", "- Verified by: TC-IF-302-01..07\n"
old_hist = "- History: v0, amendment 5/7 (2026-10-25)\n"
new_hist = "- History: v0, amendment 5/7 (2026-10-25); 2026-10-31 A-61 (D-161): IF-302 v6; Verified by names TC-IF-302-01..07 (it said 01..03)\n"
text = open(sys.argv[1], encoding="utf-8").read()
if new_by not in text:
    if text.count(old_by) != 1 or text.count(old_hist) != 1:
        sys.exit("the IF-302 entry of the N-3.3 requirements is not what A-61 expects: check " + sys.argv[1])
    text = text.replace(old_by, new_by).replace(old_hist, new_hist)
open(sys.argv[2], "w", encoding="utf-8").write(text)
PY
python3 - contracts/IF-101-chat-api.md "$TMP/IF-101-chat-api.md" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
if "| A-61 |" not in text:
    lines = text.split("\n")
    title = re.fullmatch(r"(# IF-101 .*, v)(\d+)", lines[0])
    if not title:
        sys.exit("the title of IF-101 has no version where A-61 expects it: check contracts/IF-101-chat-api.md")
    version = int(title.group(2)) + 1
    lines[0] = "%s%d" % (title.group(1), version)
    vote = [i for i, line in enumerate(lines) if line.startswith("| `vote(session, subject, category, value)`")]
    old = "`422 invalid_vote` with rule `category` or `value`"
    if len(vote) != 1 or lines[vote[0]].count(old) != 1:
        sys.exit("the vote row of IF-101 is not what A-61 expects: check contracts/IF-101-chat-api.md")
    lines[vote[0]] = lines[vote[0]].replace(old, old + " (**[v%d]** `value` is the integer 1 or -1: `1.0` or `true` is rule `value`)" % version)
    history = max(i for i, line in enumerate(lines) if re.match(r"\| v\d+ \| ", line))
    lines.insert(history + 1, "| v%d | 2026-10-31 | `vote`: the value is the integer 1 or -1; `1.0` or `true` is `422 invalid_vote`, rule `value`, as the chat service and the Record tables (IF-302 v6) refuse it; the mock follows (D-162) | A-61 |" % version)
    text = "\n".join(lines)
open(sys.argv[2], "w", encoding="utf-8").write(text)
PY
python3 - tests/helpers/mocks/if_101_chat_api.py "$TMP/if_101_chat_api.py" <<'PY'
import sys
old = "if category not in CATEGORIES or value not in (1, -1) or isinstance(value, bool):"
new = "if category not in CATEGORIES or value not in (1, -1) or type(value) is not int:      # A-61: a bool or a float equal to 1 is no vote value"
text = open(sys.argv[1], encoding="utf-8").read()
if new not in text:
    if text.count(old) != 1:
        sys.exit("the vote check of the IF-101 mock is not what A-61 expects: check tests/helpers/mocks/if_101_chat_api.py")
    text = text.replace(old, new)
open(sys.argv[2], "w", encoding="utf-8").write(text)
PY
python3 - tests/acceptance/contract/test_if_101_chat_api.py "$TMP/test_if_101_chat_api.py" <<'PY'
import sys
case = '''
    @mark.req("IF-101", "REQ-CHA-015")
    @each_provider(IF)
    def test_a_vote_value_that_is_no_integer_is_refused(self, api):
        """TC-IF-101-32 (A-61, D-162): a vote value 1.0, -1.0 or True is 422 invalid_vote with the rule value and is not stored."""
        anna = api.login("anna", "pw-anna")
        for value in (1.0, -1.0, True):
            err = error_of(lambda: api.vote(anna, "service", "service", value))
            self.assertEqual((err.status, err.code, err.rule), (422, "invalid_vote", "value"), value)
        self.assertEqual(api.score(anna)["votes"], 0)

'''
end = '\nif __name__ == "__main__":'
text = open(sys.argv[1], encoding="utf-8").read()
if "TC-IF-101-32" not in text:
    if text.count(end) != 1:
        sys.exit("the end of the IF-101 suite is not what A-61 expects: check tests/acceptance/contract/test_if_101_chat_api.py")
    text = text.replace(end, case + end)
open(sys.argv[2], "w", encoding="utf-8").write(text)
PY
copy $A/IF-302-record-tables.md contracts/IF-302-record-tables.md
copy $D/tests/helpers/mocks/if_302_record_tables.py tests/helpers/mocks/if_302_record_tables.py
copy $D/tests/acceptance/contract/test_if_302_record_tables.py tests/acceptance/contract/test_if_302_record_tables.py
copy "$TMP/IF-101-chat-api.md" contracts/IF-101-chat-api.md
copy "$TMP/if_101_chat_api.py" tests/helpers/mocks/if_101_chat_api.py
copy "$TMP/test_if_101_chat_api.py" tests/acceptance/contract/test_if_101_chat_api.py
copy "$TMP/test-spec.md" specs/mia/test-spec.md
copy "$TMP/requirements.md" "$NODE"
finish
echo
python3 tests/acceptance/contract/test_if_302_record_tables.py
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py
