#!/usr/bin/env bash
# A-160: two protected acceptance tests follow the code (found when the code of A-160 went green). Idempotent; shows the diff.
#  - TC-WFM-142 (tests/acceptance/test_end_message.py): the scripted user answers "yes", "yes" (keywords, full texts), so that the review reaches its summary; with "no" the run ends without a summary and the
#    check of the summary cannot pass (a mistake of the red test).
#  - TC-CHA-063 (tests/acceptance/test_chat_skill_turns.py): REQ-CHA-074 asks a summary of 3000 characters once more, so the fake model answers the shortening call with the same 3000 characters; what the
#    check shows (the code never cuts) is unchanged.
set -e
cd "$(git rev-parse --show-toplevel)"
P=specs/mia/goals/G-V3.CHAT/amendment-a160/protected-adjust-tests.patch
if git apply --check -R "$P" 2>/dev/null; then echo "already applied"; exit 0; fi
git apply "$P"; git diff -- tests/acceptance/test_end_message.py tests/acceptance/test_chat_skill_turns.py
echo "then: git add tests/acceptance/test_end_message.py tests/acceptance/test_chat_skill_turns.py && git commit -m 'plan: A-160 two protected checks follow the code (TC-WFM-142 scripted answers, TC-CHA-063 second reply)'"
