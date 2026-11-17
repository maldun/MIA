# Prototype report A-158 (2026-11-17, agent): the live status line, running on the stub page

**What runs:** `ui/tools/chat_stub_server.py` with the real `ChatService` (T-07) and the page code (`chat-model.js`, `chat.js`, `messages.css`, T-08 first cut). Say `run` in the stub chat: a scripted run goes through `start`, `collect`, `rank`, a question that waits 4 s, `answered`, `report`, `done`.
**Start it:** `bash tools/start_testing.sh start chat-on-stub` (then open `http://127.0.0.1:8685/?character=0`; without podman: `/home/maldun/prog/Python/venvs/mia312/bin/python ui/tools/chat_stub_server.py`).

## Evidence measured (event order seen by a Socket.IO client, seconds from the send)
| t | event |
|---|---|
| 0.0 | user message `run` |
| 0.5 | line `collect` (a run with phases gives no line at `start`) |
| 2.5 | line `rank` |
| 4.5 | question message, then the line `waiting for your answer` |
| 8.5 | line `rank` again (after the answer) |
| 9.0 | line `report` |
| 11.0 | clearing (`text: null`), then the end message `done` |

No `chat_run_status` is in the log, the history or the speech (TC-CHA-073, green). Tests: `test_chat_skill_turns.py` 25 of 26 (the 26th is the over-specified assertion of TC-CHA-075, patch `protected-fix-tc-cha-075.patch` waits for the owner), `run-line.test.mjs` green.

## What to look at (for the person who rates)
1. The line stays last while new messages arrive (say another message during the run), is replaced in place, and disappears when the summary comes.
2. The link `Skill run view` on the line opens the run view.
3. Wording and look of the line (italic, muted). The texts `working` and `waiting for your answer` are English only so far (i18n of these two is open).
4. Plausibility of the six requirements REQ-CHA-068 to 071, REQ-CLV-053, 054: they are met by this prototype except the browser check of the DOM order (not run headless by me: no browser available in this session).

## Known gaps
- `TC-CLV-021` (every socket event of the page is named in IF-101) is red until the contract text of `IF-101-change.md` is applied.
- The three older red JS tests (TC-CLV-049 twice, TC-CLV-052) were red before this work.
- A reload drops the line (decided: transient).
