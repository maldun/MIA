#!/usr/bin/env bash
# Amendment A-62 (N-1.1 Verify, F4 of the verification report, owner decision D-163, 2026-10-31): IF-101 describes the whole wire the chat page uses,
# TC-CLV-021 takes its allow-list from the contract alone, and the duplicate id TC-IF-101-30 is resolved (A-54's rate-limit case becomes TC-IF-101-33).
# Protected files that change (all BUILT FROM THE INSTALLED FILES at run time; nothing is copied whole, so A-61 may come before or after):
#   contracts/IF-101-chat-api.md                        the title one version up (the NEXT version at install time: v14, or v15 after A-61); the REST
#                                                       addresses with their methods; `history` on the wire ({messages, older}, `before`); the operations
#                                                       `commands` and `backgrounds`; the events chat_status, chat_pipeline, audio_owner, audio_reload; the
#                                                       page's events audio_claim, audio_ended, character_ready; one row in the version history
#   tests/acceptance/contract/test_if_101_chat_api.py   A-54's case "the eleventh message ... rate limited": TC-IF-101-30 -> TC-IF-101-33 (30 stays the files case)
#   specs/mia/test-spec.md                              its row: TC-IF-101-30 -> TC-IF-101-33
# Not protected, changed with it (the allow-list follows the contract): tests/js/multiuser.test.mjs and tests/test_chat_views_browser.py, PENDING_A62 emptied.
# Note: specs/mia/amendments/A-62/A-62-note.md. If A-54 is installed again AFTER this one (it copies whole files), run this script with --do again.
# INSTALL IT ON THE LINE OF WORK goal/v1 after the merge of v1-n11b (the two test files above come with that branch).
#   bash tools/apply_amendment_a62.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a62.sh --do      install, run the IF-101 suite in the image and the JS tests; commit afterwards as "plan: A-62 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
python3 - contracts/IF-101-chat-api.md "$TMP/IF-101-chat-api.md" <<'PY'
import re
import sys
text = open(sys.argv[1], encoding="utf-8").read()
if "| A-62 |" not in text:
    lines = text.split("\n")
    title = re.fullmatch(r"(# IF-101 .*, v)(\d+)", lines[0])
    if not title:
        sys.exit("the title of IF-101 has no version where A-62 expects it: check contracts/IF-101-chat-api.md")
    v = int(title.group(2)) + 1
    lines[0] = "%s%d" % (title.group(1), v)

    def one(predicate, what):
        found = [i for i, line in enumerate(lines) if predicate(line)]
        if len(found) != 1:
            sys.exit("%s is not found exactly once in contracts/IF-101-chat-api.md; install A-62 by hand" % what)
        return found[0]

    rest = "The REST address of an operation is `/api/<operation>`; the socket events carry the same operations where noted."
    i = one(lambda line: rest in line, "the sentence on REST addresses")
    lines[i] = lines[i].replace(rest, rest + " **[v%d]** The table *REST addresses* gives the method and the address of every operation the page "
                                "calls; where it differs from `/api/<operation>`, the table holds." % v)

    i = one(lambda line: line.startswith("| `history(session, limit)`"), "the row of history")
    if not lines[i].endswith(" |"):
        sys.exit("the row of history does not end with ' |'; install A-62 by hand")
    lines[i] = lines[i][:-2] + ("; **[v%d]** on the wire `GET /api/chat/history?limit=<n>&before=<id>` answers `{\"messages\", \"older\"}`: the list, "
                                "and whether older messages exist; `before` (optional) is the id of the oldest message the page has, the answer then holds "
                                "the messages before it; the page asks with `limit` 50, the server gives at most 200 |" % v)
    lines[i + 1:i + 1] = [
        "| `commands(session)` (`/api/chat/commands`) **[v%d]** | | `{\"commands\": [{\"command\", \"description\", \"confirm\"}]}` | the slash commands of "
        "the palette: the fixed ones and one per task of the registry (REQ-WFM-029); `confirm` true = the page asks before it sends the command "
        "(REQ-RUN-002) |" % v,
        "| `backgrounds(session)` (`/character-backgrounds.json`) **[v%d]** | | `{\"files\": [name], \"default\"}` | the background pictures the "
        "character can show and the configured one; the character (IF-111) loads a picture from `/character-backgrounds/<name>` |" % v,
    ]

    events = one(lambda line: line.startswith("Events (server to every connected page)"), "the line 'Events (server to every connected page)'")
    lines[events:events] = [
        "REST addresses **[v%d]** (the session cookie on every call; a body is JSON):" % v,
        "| Address | Method | Operation | Input |",
        "|---|---|---|---|",
        "| `/api/login` | POST | `login` | `{user, password}` |",
        "| `/api/whoami` | GET | `whoami` | |",
        "| `/api/logout` | POST | `logout` | |",
        "| `/api/change_password` | POST | `change_password` | `{old, new}` |",
        "| `/api/chat/history` | GET | `history` | query `limit`, `before` |",
        "| `/api/chat/commands` | GET | `commands` | |",
        "| `/api/regenerate` | POST | `regenerate` | `{message_id}` |",
        "| `/api/speak_again` | POST | `speak_again` | `{message_id}` |",
        "| `/api/account` | GET | `account` | query `message_id` |",
        "| `/api/vote` | POST | `vote` | `{subject, category, value}` |",
        "| `/api/score` | GET | `score` | |",
        "| `/api/counters` | GET | `counters` | |",
        "| `/api/reset_counter` | POST | `reset_counter` | `{name}` |",
        "| `/api/items` | GET | `items` | query `kind` |",
        "| `/api/items` | POST | `save_item` | `{kind, id, text, source, due}` (`due` left out = no due time) |",
        "| `/api/items` | DELETE | `delete_item` | query `kind`, `id` |",
        "| `/api/trust` | GET | `trust` | |",
        "| `/api/trust` | POST | `set_trust` | `{source, value}` |",
        "| `/api/persona` | GET | `persona` | |",
        "| `/api/persona` | POST | `save_persona` | `{doc}` |",
        "| `/api/pause` | POST | `pause` | |",
        "| `/api/resume` | POST | `resume` | |",
        "| `/api/files` | GET | `files` | |",
        "| `/api/files/<name>` | GET | `file` | the name, URL-encoded |",
        "| `/character-backgrounds.json` | GET | `backgrounds` | |",
        "",
    ]

    events = one(lambda line: line.startswith("Events (server to every connected page)"), "the line 'Events (server to every connected page)'")
    end = events + 1
    while end < len(lines) and lines[end].startswith("|"):
        end += 1
    lines[end:end] = [
        "| `chat_status` **[v%d]** | `{busy, activity, model, profile, queue, mood}`: first after `connect`, then after every change |" % v,
        "| `chat_pipeline` **[v%d]** | `{id, event}`: one step of the pipeline that makes the answer `id`, for skills with a status block; the page "
        "shows the steps above the answer |" % v,
        "| `audio_owner` **[v%d]** | `{sid}`: the socket that plays the voice now; every other page stays silent (one page plays, REQ-VPB-002) |" % v,
        "| `audio_reload` **[v%d]** | `{url, serial, message}` to the playing page only: a voice line at `url` (`/audio/<file>`) with its serial "
        "number, in order (IF-112 on the page) |" % v,
        "",
        "Events (page to server) **[v%d]**:" % v,
        "| Event | Payload |",
        "|---|---|",
        "| `chat_send` | the operation `send` |",
        "| `chat_stop` | the operation `stop` |",
        "| `audio_claim` | `{initial}`: this page is seen or touched and wants to play the voice; ack `{owner}`; `initial` true on the first claim of a "
        "loaded page |",
        "| `audio_ended` | `{serial}`: the line with this serial number ended on this page |",
        "| `character_ready` | none: the character of this page loaded; the server answers with `expression` of the current face |",
    ]

    history = max(i for i, line in enumerate(lines) if re.match(r"\| v\d+ \| ", line))
    lines.insert(history + 1, "| v%d | 2026-10-31 | the whole wire of the chat page (D-163, F4 of the N-1.1 verification): the REST addresses with "
                 "their methods; `history` on the wire is `{messages, older}` with `before`; the operations `commands` (`/api/chat/commands`) and "
                 "`backgrounds` (`/character-backgrounds.json`); the events `chat_status`, `chat_pipeline`, `audio_owner`, `audio_reload`; the page's "
                 "events `audio_claim`, `audio_ended`, `character_ready` | A-62 |" % v)
    text = "\n".join(lines)
open(sys.argv[2], "w", encoding="utf-8").write(text)
PY
python3 - tests/acceptance/contract/test_if_101_chat_api.py "$TMP/test_if_101_chat_api.py" specs/mia/test-spec.md "$TMP/test-spec.md" <<'PY'
import sys
suite_in, suite_out, spec_in, spec_out = sys.argv[1:5]
pairs = ((suite_in, suite_out, '"""TC-IF-101-30 (v12, A-54):', '"""TC-IF-101-33 (v12, A-54):'),
         (spec_in, spec_out, "| TC-IF-101-30 | IF-101 | Contract | 1 (mock) and 2 (real) | v12 (A-54", "| TC-IF-101-33 | IF-101 | Contract | 1 (mock) and 2 (real) | v12 (A-54"))
for source, target, old, new in pairs:
    text = open(source, encoding="utf-8").read()
    if new not in text:
        if text.count(old) != 1:
            sys.exit("A-54's TC-IF-101-30 is not found exactly once in %s; renumber it by hand" % source)
        if "TC-IF-101-33" in text:
            sys.exit("TC-IF-101-33 is taken already in %s; pick the next free number by hand" % source)
        text = text.replace(old, new)
    open(target, "w", encoding="utf-8").write(text)
PY
python3 - tests/js/multiuser.test.mjs "$TMP/multiuser.test.mjs" tests/test_chat_views_browser.py "$TMP/test_chat_views_browser.py" <<'PY'
import re
import sys
done = "// A-62 installed: IF-101 names the whole wire"
for source, target, pattern, empty in ((sys.argv[1], sys.argv[2], r"const PENDING_A62 = new Set\(\[.*?\]\);", "const PENDING_A62 = new Set();      " + done),
                                       (sys.argv[3], sys.argv[4], r"PENDING_A62 = \{.*?\}\n", "PENDING_A62 = set()      # A-62 installed: IF-101 names the whole wire\n")):
    text = open(source, encoding="utf-8").read()
    if "A-62 installed" not in text:
        text, n = re.subn(pattern, lambda m: empty, text, count=1, flags=re.S)
        if n != 1:
            sys.exit("PENDING_A62 is not found in %s; empty it by hand" % source)
    open(target, "w", encoding="utf-8").write(text)
PY
copy "$TMP/IF-101-chat-api.md" contracts/IF-101-chat-api.md
copy "$TMP/test_if_101_chat_api.py" tests/acceptance/contract/test_if_101_chat_api.py
copy "$TMP/test-spec.md" specs/mia/test-spec.md
copy "$TMP/multiuser.test.mjs" tests/js/multiuser.test.mjs
copy "$TMP/test_chat_views_browser.py" tests/test_chat_views_browser.py
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py
node --test "tests/js/*.test.mjs" 2>&1 | grep -E '^# (pass|fail)|^not ok'
