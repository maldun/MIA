# Start of the Plan session for FB-01 (skills panel beside the chat), written 2026-10-30

For a **fresh session**. Skills: `dev-workflow`, `plan-phase`, `agent-app`, `agent-app-plan` (and `decomposition`: the change cuts across nodes). This is a feedback iteration: the existing node plans are **amended**, not rewritten.

**Precondition: the HLS gate.** Explore is done (commit `fcd2b20`, merged in `3c84bda`; decision D-114), but the owner has **not yet approved** iteration 1 of the HLS. Ask the gate question first (below); start Plan only after a yes, then set the status line of `high-level-spec.md` to *Approved (iteration 1)*.

## Start prompt (paste this)

> Plan phase for feedback item FB-01 (skills panel beside the chat). Load the skills `dev-workflow`, `plan-phase`, `agent-app`, `agent-app-plan` and `decomposition`. Read, in this order: `CLAUDE.md`, `specs/mia/handover-fb-01-plan.md` (this file), `specs/mia/feedback/FB-01.md`, `specs/mia/high-level-spec.md` section 8 and FR-34, FR-35, AC-30, the FB-01 rows of section 4 and section 7, `specs/mia/research-fb-01.md`, and the requirements, plans and test specs of the nodes listed under "Affected nodes". Work in a worktree branched from current master. First ask me the HLS gate question for iteration 1; continue only after my approval. Then draft the plan amendment (next free A-id) one node at a time, and stop for my approval of the requirements, the eval criterion and the red tests before anything is installed. Do not write production code. End with the merge commands.

## The HLS gate question (ask first)
Do you approve iteration 1 of the HLS: FR-34 (skills panel), FR-35 (skill turns in the chat), AC-30, boundary TB-result and the architecture of section 5.3? Points for the owner to check:
1. the **draft example cases** of section 4 (good, bad, unknown and attack for the summary and the status message) are the agent's; confirm or edit them, they become the first eval cases after labelling;
2. AC-30 is *proposed*;
3. the pin of `SkillDigestStep` (drafted MP-light; or the model selected for the chat?);
4. cost: each declared phase and each piece of a long result is one call on the one model server; only the skill's declaration limits the status messages.

## Decided (do not re-ask; HLS section 8, D-111, D-114)
1. Skills panel beside the chat on the same page, a tab on the phone; a **new part of the chat page**, not a tab of the modal workspace dialog (`templates/static/chat/workspace.js:6`).
2. The chat holds only the questions, the answers, status messages and the summary with a link; a failure is a short message with the reason and a link.
3. **The chat model** writes status messages and summary in MIA's persona like any chat turn; a long result is digested **in pieces** first (`SkillDigestStep`, then `ChatStep`). The summary is informative only; the full result in the panel is the reference. (This revised FB-01's "the skill writes its own summary".)
4. 1200 characters, **in the prompt only**; nothing cuts. The link is added by code.
5. Spoken like answers, with the same repair; questions, answers, summary and **the last status message of each run** are in the model history.
6. "Session" = the **shared chat history**: the panel lists the runs whose messages are in it, after reload and restart; deleting the history empties the panel, files and report records stay.
7. Status messages: a **new message per phase**, only for phases the skill **declares** worth telling; no time gap, no templates.
8. The same rule for every skill, also `/lookup` and `/search`.

## Open for Plan (propose an answer with each, ask the owner)
1. **Eval criterion for FR-35** (faithful to the result and in persona): suite, metric, bound, repeats, pin, decision rule, baseline (none exists: record one). A judge for "faithful" needs calibration against the owner's ratings (FR-17).
2. **THR entry for TB-result** (indirect injection through a skill result into the chat step and the history, LLM01 and LLM04 next to THR-006) and red-team cases as drafts in `specs/mia/eval-drafts/`. `agent_check.py` reports A10 for `SkillDigestStep` until then.
3. **Budgets:** seconds per call of `SkillDigestStep` (A9 reports `secondBudget = 0.0`), the size of a piece (share of `num_ctx` 8192, NFR-2: inputs within 50 %), the calls per run; whether status and summary turns queue behind user messages like chat answers (NFR-7).
4. **Contracts:** IF-101 (panel: run list, full result, final figures after reload; a marker for skill messages; where `task_status` is drawn), IF-201 (skill turns in the history: which roles, how the last status message replaces the earlier ones); manifest field for declared phases (REQ-WFM-039). Each is an amendment with mock and contract tests.
5. **Run record** (`skillRunStore`): a new table behind IF-102 or an extension of `reports`; it must be listable in order (storage has only `ids/get/history` today, `storage.py:84-98`) and tie runs to the chat history so a deletion empties the panel.
6. Which existing tests change: TC-CLV-023, TC-CLV-024, TC-WFM-031, TC-WFM-036, TC-IF-101-24, -25, `tests/js` of the card; protected ones only through the amendment.

## Affected nodes (requirements to change or add, `Parent` up to FR-34 / FR-35)
- N-1.1 chat and login views: REQ-CLV-023 (card into the panel; after reload, closes TD-01), REQ-CLV-024 (link target from the panel), new panel requirements; parent REQ-FE-014.
- N-2.3 workflow management: REQ-WFM-031, -036, -038, -039 (all still `Draft`).
- N-2.2 chat agent: REQ-CHA-008, -014 (persona and repair of skill turns), history (IF-201).
- N-2.5 voice synthesis: task text gets the repair of answers (`web_app.py:603-610` speaks it without).
- N-3 database: the run record.
- N-4 evaluation: the FR-35 suite and baseline.

## Where the code is
See `research-fb-01.md` (with `file:line`): `chat_service.py:542-567` (ask), `:607-711` (late result, card, files, failure), `task_monitor.py`, `templates/static/chat/task-card.js`, `app.js:203`, `extension_loader.py`, `extensions/review/review_chat.py:144,152,227-233,291`, `communicator.py:191-211`, `web_app.py:364,603-610`, `record_tables.py:11`.

## Another session is working in parallel (keep this in mind)
- A second chat is implementing **N-2.4.1 pipeline runner** (worktree `n241-t01`; commits `d416356` T-01, `9cfa556` A-31). It touches `run_workflow.py`, `tools/sync_workflows.py`, `tests/helpers/contract.py`, the N-2.4.1 implementation log, `review-log.md` and the amendments.
- **Ids collide.** That session took D-112 and D-113 while Explore of FB-01 also wrote D-112 (lost in the merge, re-added as D-114). Before you write a D-, A- or TC-id, read the newest ids **on master at that moment** (`git log -1 master`, `grep -o '^| D-[0-9]*' specs/mia/review-log.md | tail -1`, `ls specs/mia/amendments`), and re-check right before the merge. The next amendment is A-32 unless the other session has taken it.
- **Shared files:** `review-log.md`, `high-level-spec.md`, `architecture.sysml` (generated node block), `decomposition.yaml`, `tests/helpers/`. Append, never reorder; merge master into your branch before the hand-back and resolve conflicts by keeping both rows.
- Do not touch `run_workflow.py` or the N-2.4.1 folder; FR-35's skill turns go through the chat path (`skillTurnRelay`), not the runner. If a task needs the runner, stop and report.
- An old worktree `fb-01-skills-panel` (at `8c564f3`, no commits of its own) exists; it is not used, leave it.

## Rules that matter here
- The owner's per-machine settings are not in git (`deploy/setup_cfg.local.json`); no `git add -A` in the main checkout; end with the merge commands.
- Contract changes (IF-101, IF-201, IF-102) and changed protected tests are amendments, approved before install.
- Never edit `eval/suites/` or `eval/baselines/`; new cases are drafts in `specs/mia/eval-drafts/` until the owner labels them.
- Do not run the local coder model (`lc.py run`) while the owner hand-tests with Ollama.
- Checks before the gate: `python3 -I tools/check_sysml_model.py .`, `bash tools/check_sysml.sh` after a `.sysml` change, `trace_check.py`, `agent_check.py` (known before Plan: A9 and A10 on `SkillDigestStep`; FR-34, FR-35 not yet in a node `requirements.md`).
