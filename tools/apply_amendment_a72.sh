#!/usr/bin/env bash
# Amendment A-72 (N-1 integration step 1, 2026-11-01): the Voice playback N-1.3 is integrated. Its real provider of IF-112 is the VoicePlayer of
# templates/static/chat/sound.js behind a small adapter (tick, played) in a new protected helper; the contract suite of IF-112 runs it as its real side
# (5 tests that skipped), the step tests/integration/N-1/step_01 runs the scenario with it. Note: specs/mia/amendments/A-72/A-72-note.md
# Protected files that change:
#   tests/helpers/real/if_112_voice_player.mjs                   NEW: RealVoicePlayer (copied from specs/mia/contract-drafts/tests/helpers/real/)
# Made from the INSTALLED files at run time (shared with the later N-1 steps), each edit refused when its anchor is not found exactly once:
#   tests/helpers/integration.mjs                                READY gets N-1.3; realSubject('IF-112') gives RealVoicePlayer
#   tests/helpers/contract.mjs                                   the skip reason of IF-112 goes
#   tests/acceptance/contract/test_if_112_voice_player.test.mjs  make('real') builds RealVoicePlayer instead of null
# INSTALL IT ON THE LINE OF WORK goal/v1 (A-70 installed).
#   bash tools/apply_amendment_a72.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a72.sh --do      install, run the IF-112 suite and N-1 step_01; commit afterwards as "plan: A-72 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - tests/helpers/integration.mjs tests/helpers/contract.mjs tests/acceptance/contract/test_if_112_voice_player.test.mjs "$WORK" <<'PY'
import os
import re
import sys
integration, contract, suite, work = sys.argv[1:5]
read = lambda path: open(path, encoding="utf-8").read()


def write(name, text):
    open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def edit(text, old, new, where, what, done=None):
    """old -> new exactly once; a text that has the new part already (done) is left as it is."""
    if (done or new) in text:
        return text
    if text.count(old) != 1:
        sys.exit("%s: %s is not found exactly once; install A-72 by hand" % (where, what))
    return text.replace(old, new)


text = read(integration)
imp = "import { VoicePlayerMock } from './mocks/if_112_voice_player.mjs';\n"
text = edit(text, imp, imp + "import { RealVoicePlayer } from './real/if_112_voice_player.mjs';\n", integration, "the import line of the voice player mock",
            done="import { RealVoicePlayer }")
throw = "  throw new Error(`the real adapter of ${iface} is added by the integration step of its node`);\n"
text = edit(text, throw, "  if (iface === 'IF-112') return new RealVoicePlayer();     // A-72: the Voice playback N-1.3\n" + throw, integration, "the throw in realSubject",
            done="if (iface === 'IF-112') return new RealVoicePlayer();")
match = re.search(r"^export const READY = new Set\((\[[^\]]*\])?\);(.*)$", text, re.M)
if not match:
    sys.exit("%s: the READY line is not found in its usual form; install A-72 by hand" % integration)
nodes = re.findall(r"'([^']+)'", match.group(1) or "")
if "N-1.3" not in nodes:
    nodes.append("N-1.3")
comment = re.sub(r",? e\.g\. new Set\(\[[^\]]*\]\)", "", match.group(2))
if "A-72" not in comment:
    comment = comment.rstrip() + " (A-72: the Voice playback)"
text = text[:match.start()] + "export const READY = new Set([%s]);%s" % (", ".join("'%s'" % n for n in nodes), comment) + text[match.end():]
write("integration.mjs", text)

text = read(contract)
line = re.findall(r"^  'IF-112': .*\n", text, re.M)
if len(line) > 1:
    sys.exit("%s: more than one IF-112 line; install A-72 by hand" % contract)
write("contract.mjs", text.replace(line[0], "") if line else text)

text = read(suite)
old = "const make = (kind) => (kind === 'mock' ? new VoicePlayerMock() : null);\n"
new = ("import { RealVoicePlayer } from '../../helpers/real/if_112_voice_player.mjs';\n"
       "const make = (kind) => (kind === 'mock' ? new VoicePlayerMock() : new RealVoicePlayer());\n")
write("suite.mjs", edit(text, old, new, suite, "the make line"))
PY
[ "$do_it" = 1 ] && mkdir -p tests/helpers/real
copy $D/tests/helpers/real/if_112_voice_player.mjs tests/helpers/real/if_112_voice_player.mjs
copy "$WORK/integration.mjs" tests/helpers/integration.mjs
copy "$WORK/contract.mjs" tests/helpers/contract.mjs
copy "$WORK/suite.mjs" tests/acceptance/contract/test_if_112_voice_player.test.mjs
finish
echo
echo "== IF-112 suite and N-1 steps"
node --test tests/acceptance/contract/test_if_112_voice_player.test.mjs "tests/integration/N-1/step_0*/test_step.test.mjs" 2>&1 | grep -E "^not ok|^ok .*SKIP|^# (pass|fail|skipped)"
