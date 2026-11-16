# Proposal (2026-11-17, agent; the owner decides): the browser tests must not read the checkout's `setup_cfg.json`

## Finding
`tests/test_character_requests.py` (3 of 4 red) and `tests/test_page_requests.py` (2 of 6 red) fail in the main checkout and pass in a clean worktree. Cause, by bisection and a direct check: `accounts_enabled: true` in the git-ignored `setup_cfg.json` of the main checkout.
- `test_character_requests`: original file 3 failures; same file with only `accounts_enabled` set to `false`: 4 of 4 green (no other stage running in both runs).
- `test_page_requests`: with `accounts_enabled` false 6 of 6 green; with the original file 2 red.
- The other four keys that stayed in the bisection (`review_budget`, `structured_memory`, `max_conversations`, `calibration_file`) each pass alone.
- Likely reason (not read in the code): with accounts on the page shows the login first, so the character iframe gets no address and is not hidden. The stage `chat-on-stub` mounts the checkout (`tools/start_testing.sh`), so it reads the checkout's own `setup_cfg.json`.

## Why it matters
The result of a stage 2 test depends on the owner's personal settings, so a green or red run says nothing about the code. A worktree has a generated default file and passes; the main checkout fails. The same tests are named in the verification matrices, and a red run in the main checkout has already cost a long search.

## Proposal (not done; the owner picks)
1. **The stage gets its own config** (recommended): `tools/start_testing.sh start chat-on-stub` starts the stub server with a config of its own (defaults, accounts off), not the checkout's `setup_cfg.json`. One place, no test changes. Needs a look at how the stub server finds its config (`MIA_TESTING_DIR` is the state folder; not checked whether it covers the config).
2. The two tests fail with a clear message ("accounts_enabled is on in setup_cfg.json") or skip, instead of failing in the browser. Small test change, hides nothing, but does not make the tests independent.
3. Leave as is and document: switch `accounts_enabled` off before a stage 2 run. Cheapest, and it stays a trap.

`tests/test_character_requests.py` and `tests/test_page_requests.py` are not in a protected folder; `tools/start_testing.sh` is a tool of the repo. Whether either change needs an amendment is the owner's call (I called it "protected" earlier in the session; that was wrong for these two files).

## Not covered
Other modules that start a stage were not run with accounts off (`test_task_files_browser` fails the same way on a clean master worktree and has not been looked at). Two further local leftovers also made tests red in the main checkout and were moved out of the repo, not deleted: `templates/static/answer.html` (`test_chat_page`) and `templates/node_modules/` (`test_system_inspection`). `test_make_voice_lines` cannot pass in a folder named `MIA` (by design of the test).
