# Start of the Explore session for FB-01 (skills panel beside the chat), written 2026-10-30

For a **fresh session**. Skills: `dev-workflow`, `explore-phase`, `agent-app`, `agent-app-explore`. This is a feedback iteration: the existing HLS is **updated**, not rewritten.

## Start prompt (paste this)

> Explore phase for feedback item FB-01 (skills panel beside the chat). Load the skills `dev-workflow`, `explore-phase`, `agent-app` and `agent-app-explore`. Read, in this order: `CLAUDE.md`, `specs/mia/feedback/FB-01.md` (observation and the owner's decisions), `specs/mia/handover-fb-01-explore.md` (this file: scope, what is decided, what is open, where the code is), `specs/mia/high-level-spec.md` sections 3, 5, 6 and 8, and the requirements named under "Affects" in FB-01. Work in a worktree branched from current master. Do read-only research of the existing code first, then interview me only on the open points listed in the hand-over (do not re-ask the decided ones). Output: the HLS update (section 8 with FB-01, the changed or new high-level requirements with `Parent: FB-01`, the HLS-level architecture in `specs/mia/architecture.sysml` with `@ChangeSource { feedbackId = "FB-01"; iteration = 1; }`), and a short `specs/mia/research-fb-01.md`. Do not write detailed requirements, tests or code: that is the Plan phase. End with the merge commands and the HLS gate question.

## Decided by the owner (do not re-ask)
1. A **Skills panel beside the chat** on the same page: a tab like Files (a tab on the phone). It holds the status cards, progress, pause / resume / stop, the full result and the report link of every skill.
2. **In the chat only:** the questions a skill asks while it runs, a **short status line** of what happens now (with a bit of MIA's personality), and at the end a **summary with a link** to the full result. A failure is a short message with the reason and a link (REQ-WFM-036 keeps that rule).
3. **The skill writes its own summary** as part of its result (modularity, REQ-WFM-039, rule "skills are self-contained extensions"). The core does not summarize.
4. **Summary size:** at most **1200 characters**.
5. **MIA speaks** the questions and the summary (voice, repaired text as for answers) and **knows** them: questions, the user's answers and the summary are in the history the chat model sees.
6. The panel keeps a **history within a session**: running and finished skills stay listed after a reload.

## Open, for the interview (propose an answer with each question)
1. "Session" in decision 6: the login session, the chat session, or a time window? What the `reports` table (REQ-WFM-038) already gives.
2. The status line: who words it. Options to weigh: the skill reports a plain phase and the core adds MIA's personality from templates (persona, mood, `library/voice_lines.json`, no model call); or a model call (tokens on the 12B model, needs an eval case and a budget). Rule of the project: modular skills, core free of skill names (`tests/test_core_names_no_skill.py`).
3. The status line: one line updated in place or a new message per phase; how often at most; is it spoken (could get noisy).
4. Is the status line in the history the model sees (decision 5 covers questions and summary only)?
5. What the summary contract between a skill and the core looks like (a field of the result in the extension manifest or the result record), and what happens when a skill returns more than 1200 characters (cut, refuse, or fail visibly).
6. What happens to the old behaviour of REQ-WFM-036 and REQ-CLV-023 (card in the chat) for skills that do not ask questions (`/lookup`, `/search`): do they also move to the panel?

## Where the code is today (start of the read-only research)
- Card and monitor: `templates/static/chat/task-card.js`, `task-card-model.js`, `task_monitor.py` (`tests/test_task_monitor.py`, `tests/test_chat_tasks.py`), event `task_status` of IF-101.
- Skills as extensions: `extensions/<id>/manifest.json` + `entry.py`, `extension_loader.py`; the review in `extensions/review/`.
- Result and report: REQ-WFM-036, REQ-WFM-038 (table `reports`), files volume `data/files` and the Files tab (REQ-WFM-037, REQ-CLV-024).
- Speech: `SpeechStreamer(repair, settle)` (`tests/test_speech_repair.py`); persona `persona.py` (`data/persona.json`); voice lines `voice_lines.py`.
- Chat history and model view: `ChatService`, `Communicator.persona_message()`, `chat_log.py` (the chat log is still a file).
- Requirements: N-1.1 `specs/mia/nodes/N-1-web-frontend/nodes/N-1.1-chat-and-login-views/requirements.md` (REQ-CLV-023, -024), N-2.3 `specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md` (REQ-WFM-029 to -039, still `Draft`).
- Decisions: `specs/mia/review-log.md` D-106 (hand test of `/review`), D-111 (FB-01).

## Rules that matter here
- The owner's per-machine settings are not in git (`deploy/setup_cfg.local.json`); no `git add -A` in the main checkout; end with the merge commands.
- Contract changes (IF-101, IF-201) are amendments in Plan, not in Explore.
- Do not run the local coder model (`lc.py run`) while the owner hand-tests with Ollama.
