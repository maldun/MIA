# Owner's manual checks (D-145, D-148), N-1.3 and N-4.2

Only the owner can do these: they need ears, a second device, a network outside the home, or a clean machine. Write the result after each check (ok / not ok + what you saw). The coding agent copies the results into the two verification reports and sets the statuses.

Work in the goal-v1 worktree unless a step says otherwise:

```bash
cd /home/maldun/prog/Python/MIA/.claude/worktrees/goal-v1
```

## A. N-1.3 Voice playback, by ear (the status waits for these)

**Start every stage from the goal-v1 worktree** (`cd /home/maldun/prog/Python/MIA/.claude/worktrees/goal-v1`): a stage serves the folder it is started from, and from the main folder that is master's old page (D-157; the likely cause of A4's first result). Start the test page once: `bash tools/start_testing.sh start chat-on-stub`, then open `http://127.0.0.1:8685/?character=0` (stop it afterwards with `bash tools/start_testing.sh stop chat-on-stub`).

**How voice reaches the stub (corrected 2026-10-31):** the stub has no voice synthesis, so "speak again" makes no sound there. A line arrives the way the speech process delivers it, by an upload. **Click once into the page first**: the click lets the browser play sound and makes this page the one that holds the voice. Then send a line from a terminal:

```bash
up() { curl -s -o /dev/null -w "%{http_code}\n" -F "file=@$1" http://127.0.0.1:8685/upload; }   # 200 = accepted
up /home/maldun/prog/Python/MIA/voice/expressions/happy_default.wav
```

| # | Check | Expected | Result |
|---|---|---|---|
| A1 | **Two tabs claim the voice.** Open tab A and tab B (or phone and computer). Click in A, `up …happy_default.wav`; click in B, `up …sad_default.wav`; close B, `up …surprised_default.wav`. | Only A plays the first line; only B plays the second and A is silent; after closing B, A plays the third. | ok (owner, 2026-10-31) |
| A2 | **Mute per device, autoplay hint.** Mute in A, `up` a line; reload A (click), `up` a line; unmute A, `up` a line. Then open a fresh private window without clicking, `up` a line, then click once. | Muted: no sound, the line is dropped; still muted after the reload; after unmute the line is heard. In the private window the sound hint appears; the click plays the held line. | ok (owner, 2026-10-31) |
| A3 | **Stop silences the voice.** Send a long line (`up …annoyed_default.wav` or `up …shocked_default.wav` from the v1-shocked worktree) and press Stop while it plays. | The voice stops at once on this device, the mouth stops. (Known, N3: Stop is shown only while an answer runs; a line still being made may come later.) | **not ok**: the line stops, then the voice starts again (the speech process keeps sending the answer's next sentences, N3); fix D-154 |
| A4 | **A broken line file.** Open DevTools (Console). `curl -s -o /dev/null -F "file=@/etc/hostname;filename=broken.wav" http://127.0.0.1:8685/upload`, then right after `up …happy_default.wav`. | Exactly one console warning `MIA voice: line skipped ...`; nothing on the page; the happy line plays. | **not ok**: the upload was accepted, but no console warning appeared; fix D-154 |

## B. N-4.2 Operation

| # | Check | How | Expected | Result |
|---|---|---|---|---|
| B1 | **Runbook walkthrough (TC-OPR-006).** | Follow `deploy/RUNBOOK.md` from the top on a clean machine or a clean user account (start, `deploy/up.sh character ZIP`, `deploy/up.sh exec ollama ollama list` or the host Ollama, backup, restore, retirement). | Every step works as written; note any step that is wrong or unclear. | |
| B2 | **Outside port scan (SMOKE-MIA-002).** | With the stack running and `MIA_BIND=0.0.0.0`: from another device in the LAN, `nmap -p- <host ip>`; from outside the home network (e.g. a phone without Wi-Fi) the same against your public address. | Inside the LAN only 8586 (https) answers; from outside nothing. | |
| B3 | **Backup and restore in a real stack (TC-OPR-005).** | `deploy/up.sh db`, chat a little, `deploy/up.sh backup /tmp/mia-test.tar.gz` (the archive holds `db.dump` and `data.tar`), stop and remove the stack's volumes, `deploy/up.sh db`, `deploy/up.sh restore /tmp/mia-test.tar.gz`. Once more: stop `db` and run the backup. | The same history and data after the restore. With `db` stopped: a clear error message, MIA is running again, no temp copy left in /tmp. | |
| B4 | **No paid API in use (TC-OPR-009).** | After a session with a web search: `python tools/check_free.py --log <the web logs in the data volume>`; read the lists `PAID_PACKAGES` and `PAID_HOSTS` at the top of `tools/check_free.py`. | The check passes; the two lists are what you want counted as paid (add or remove names). | |
| B5 | **A stack start with the complete config.** | Start the stack once (`deploy/up.sh`), then `podman logs mia_mia_1 | head -40`; after one literature review look into the data volume for `data/cache/scholar`. | No "lacks N option(s)" warning; the cache folder exists (older than 7 days is pruned once the pruning is merged). | |
| B6 | **Index digests (later, D-139 (6)).** | At the next pin update: replace the local digests in `deploy/compose.yaml` and `deploy/Containerfile` by the multi-platform index digests of the registry. | — | (later) |

## Afterwards

Tell the coding agent "checklist done" (or paste this table). Results that are "not ok" become findings with a test first.
