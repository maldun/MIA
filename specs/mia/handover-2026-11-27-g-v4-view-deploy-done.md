# Handover: G-V4.VIEW Deploy done (with the dark-mode fix); VIEW waits for Validate in G-V5 (2026-11-27)

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4`, branch `goal/v4` (tracks `origin/goal/v4`; only the owner pushes, `git push -4`). This file supersedes `handover-2026-11-25-g-v4-view-deploy-next.md`. VIEW has no more phase to run before Validate, which belongs to G-V5 (parked, D-386). The next session of this line picks another G-V4 subgoal (see "Next").

## Before the next session (the owner)
- [ ] `git push -4` in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4` (this handover; `8013b24a` and `cf3460a0` are pushed).
- [ ] REQ-GA-016 (`specs/mia/nodes/N-5-graph-app/requirements.md`): text changed by A-176, Status line still `Verified`: set to Draft in Emacs, review, approve again.

## What happened (2026-11-26 and 27)
| Step | Result | Record |
|---|---|---|
| Deploy | image `localhost/mia:g-v4-view` built from `goal/v4`; preflight OK (pins PASS); live stack restarted on it (`store: files`); a throw-away stack `mia-view` (8595/8596, fixture graphs in files and database) for the owner's look; SMOKE-VIEW-002 median 97 ms (88 to 122); SMOKE-VIEW-001 green (the owner's run, `store: database`); the owner's look done with files, database and an empty store; `mia-view` removed afterwards | `goals/G-V4.VIEW/deployment-record.md`, `goal.md` Deploy row |
| Finding "no dark mode" | the page followed only the system's scheme (light on the host). Fix branch: A-176 (REQ-GA-016 follows the main app's choice `mia.theme`, new protected check TC-GA-040), `graph_app/theme.js`; independent Verify (subagent): verified with deviations; A-177 (TC-GA-040 tightened, traced to TR-VIEW-002, 003, 008, 009, 013, 021); merged by the owner at `eebc315a`; redo: image `722a3cd0c480` on the live stack, the owner saw dark | D-503, D-504, `implementation-log.md` (last section), deployment record "Redo" |
| F-1 | `migrate files-to-db` stops with a traceback on the `presets` files of the live volume | handed to TRANSFER: `goals/G-V4.GRAPHSTORE.TRANSFER/note-f1-migrate-presets.md` |
| F-2 | `deploy/preflight.sh` checks the container-side `OLLAMA_URL` (`host.containers.internal`) from the host, so P1 fails although Ollama answers (works with `OLLAMA_URL=http://127.0.0.1:11434`) | open, no branch yet; a check first, then the script fix |

## State of the host
- Live stack `mia` runs from the `goal-v4` worktree (its git-ignored `deploy/.env` and `deploy/setup_cfg.local.json` are copies of the main checkout's), image `localhost/mia:g-v4-view` (`722a3cd0c480`), `store: files`, no graphs in the store (only 16 presets). **Every `deploy/up.sh` call needs `MIA_IMAGE=localhost/mia:g-v4-view`**: `localhost/mia:latest` is RUN's branch build (networkx, `9206eeb93719`), which RUN's image tests need.
- Rollback: `localhost/mia:g-v4-view-pre-theme` (`7c8618d359c0`, before the theme fix), `localhost/mia:v0.2.1`. Commands in the deployment record.
- **Never build an image in the `goal-v4` worktree while `deploy/.env` is there**: `.containerignore` does not exclude it (v0.2.1 F-1). Build from a worktree without `.env` whose tree equals the commit, or move `.env` out first.
- `localhost/mia-view-check:latest` (`d5d63bbf1de7`) holds the cached pip layer `tests/test_delivery_on_stack.py` needs for its offline build; keep it.
- Ollama container `ollama` running (0.40.5); podman after a reboot prints "Refreshing container ... file exists" errors on the first call and hangs inside the sandbox: run podman outside it.
- Choose the theme in the main app at `https://localhost:8586`, not at `http://localhost:8585`: the browser keeps it per address (D-504, `deploy/README.md`).

## Next
VIEW: Validate in G-V5 (VAL-VIEW-01, NFR-10, light and dark readability, the 220 px layers on large graphs). For G-V4 the open lines are (see `handover-2026-11-25-g-v4-run-t03-next.md` for RUN):
- `goal/v4.graphapi.run` (worktree `goal-v4-run`): T-03 next; its handover lists what waits for the owner (REQ-GTB-060, REQ-GTB-043, A-189 joint amendment).
- `goal/v4.graphstore.transfer` (worktree `goal-v4-transfer`): carries V-3 and now F-1; it should merge `goal/v4` to get the F-1 note and the VIEW merge.
- `explore/builder-workflow` (D-520 block).
- EDIT and CODE: the notes in `goals/G-V4.VIEW/merge-request.md` ("Notes for other subgoals"), TD-91 to TD-95 (deadline 2026-12-31).

## Next free numbers
VIEW's blocks: decisions D-505 (D-500 to D-519), amendments A-178 (A-171 to A-184). Checks TC-GA-041, TC-API-026, TC-OPR-012; TD-96; TR-VIEW-022; SMOKE-VIEW-003. Other lines: see their handovers (RUN: D-485, A-190).
