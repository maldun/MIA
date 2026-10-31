#!/usr/bin/env bash
# Amendment A-56 (N-2.2 T-01, 2026-10-31): the real `stop` in the IF-201 contract suite. chat_service.py now ends an answer that was stopped before the worker
# took it (REQ-CHA-004); in tests/helpers/contract.py _ChatTurnAdapter.stop and _ChatApiAdapter.stop call it instead of skipping, so TC-IF-201-04 and
# TC-IF-101-06 run on the real side (stage 2).
# The contract, the suite and the mocks are unchanged. Note: specs/mia/amendments/A-56/A-56-note.md
# Protected file that changes:
#   tests/helpers/contract.py   _ChatTurnAdapter.stop and its class docstring, _ChatApiAdapter.stop (no skip without a thread); made from the INSTALLED file at run time (shared by many amendments, so it cannot go stale)
# INSTALL IT ON THE LINE OF WORK goal/v1 after the merge of v1-n22 (the fix in chat_service.py must be there, or TC-IF-201-04 real is red).
#   bash tools/apply_amendment_a56.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a56.sh --do      install and run the IF-201 and IF-101 suites in the image; commit afterwards as "plan: A-56 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
HELPER=$(mktemp)
trap 'rm -f "$HELPER"' EXIT
python3 - tests/helpers/contract.py "$HELPER" <<'PY'
import sys
installed, out = sys.argv[1:3]
text = open(installed, encoding="utf-8").read()
stop_old = '''    def stop(self):
        raise unittest.SkipTest("IF-201 stop of an answer that has not started is not in the real chat agent yet (N-2.2 T-01)")
'''
stop_new = '''    def stop(self):
        return {"stopped": self._chat.stop()}
'''
api_old = '''        self._call("whoami", session)
        if not self._threaded:
            raise unittest.SkipTest("IF-101 stop of an answer that has not started is not in the real Backend yet (N-2.2 T-01)")
        return {"stopped": self._chat.stop()}
'''
api_new = '''        self._call("whoami", session)
        return {"stopped": self._chat.stop()}
'''
doc_old = '''What is not built yet (expression and audio_chunk of an answer: N-2.5; `stop` of an answer that has not started:
    N-2.2 T-01) skips the test.'''
doc_new = '''What is not built yet (expression and audio_chunk of an answer: N-2.5) skips
    the test; `stop` is real since A-56.'''
if stop_old not in text and api_old not in text:
    open(out, "w", encoding="utf-8").write(text)          # installed already: the copy below reports "unchanged"
    sys.exit(0)
for piece, name in ((stop_old, "_ChatTurnAdapter.stop"), (doc_old, "the docstring of _ChatTurnAdapter"), (api_old, "_ChatApiAdapter.stop")):
    if text.count(piece) != 1:
        sys.exit("tests/helpers/contract.py: %s is not found exactly once; install A-56 by hand" % name)
open(out, "w", encoding="utf-8").write(text.replace(stop_old, stop_new).replace(doc_old, doc_new).replace(api_old, api_new))
PY
copy "$HELPER" tests/helpers/contract.py
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_201_chat_turn.py tests/acceptance/contract/test_if_101_chat_api.py
