# Owner's manual checks (D-145, D-148), N-1.3 and N-4.2

Only the owner can do these: they need ears, a second device, a network outside the home, or a clean machine. Write the result after each check (ok / not ok + what you saw). The coding agent copies the results into the two verification reports and sets the statuses.

Work in the goal-v1 worktree unless a step says otherwise:

```bash
cd /home/maldun/prog/Python/MIA/.claude/worktrees/goal-v1
```

## A. N-1.3 Voice playback, by ear (the status waits for these)

Start the test page once: `bash tools/start_testing.sh start chat-on-stub`, then open `http://127.0.0.1:8685/?character=0` (stop it afterwards with `bash tools/start_testing.sh stop chat-on-stub`).

| # | Check | Expected | Result |
|---|---|---|---|
| A1 | **Two tabs claim the voice.** Open tab A and tab B (or phone and computer). Click in A, ask something; then click in B, ask; then close B and ask again. | Only A speaks; then only B speaks and A is silent; after closing B, A speaks the next line. | |
| A2 | **Mute per device, autoplay hint.** Mute in A, ask; reload A, ask; let B (with the voice) play; unmute A. Then open a fresh private window and ask. | Muted: no sound, no new line starts, the mouth stops after the current line; still muted after reload; B plays; after unmute the next line is heard. In the private window the sound hint appears; one click plays the held line and the next ones in order. | |
| A3 | **Stop silences the voice.** During a long spoken answer press Stop. | The voice stops at once on this device, the mouth stops. (Known and recorded, N3: a line still being made may come a moment later; when the text is already complete there is no Stop button.) | |
| A4 | **A missing line file.** Right after a line is announced, delete its `line-*.wav` under the stub's audio folder (or let the stub announce a wrong url). Watch the DevTools console and the next line. | Exactly one console warning `MIA voice: line skipped ...`; nothing on the page; the following line plays. | |

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
