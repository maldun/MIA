# Validation plan: v0.2.1 (G-V2 and G-V3) – DRAFT of 2026-11-20, not run

Prepared by the coding agent for the owner. People judge; the agent prepares and analyses the run logs locally (run logs are confidential: nothing goes to a remote model or service). Skills: `validate-phase`, `agent-app-validate`. Template of the result: `validate-phase/assets/validation-report.md` plus `agent-app-validate/assets/validation-report-agent.md`.

## Frozen version
v0.2.1, image `439429d0b8d5`, commit 6f44b59c, MP-light `gemma4:12b-it-qat` digest 38044be4f923, `num_ctx` 8192. No pulls, no skill or prompt edits on the target; a fix is a patch version. Source: `specs/mia/deployment/deployment-record.md`.

Known gaps of the target (from the record): no character page, no voice, sandbox off (`script` check off), five acceptance records copied by hand into the data volume. Five skills run on the graph path (research, plan_question, verify_claim, extract_claims, verify_computable); lookup, review, search and the rest on the old runner. No call through the UI has yet shown the graph path running: do that first (VAL-007).

## Validators and data
- Validator: the owner (VAL-007, 009, 012, 013 name the owner); trusted users only where a criterion names them.
- Personal data: the run log holds the conversations. Before use: informed consent of every user, retention and deletion date **<<owner sets>>**, examples in reports pseudonymised.
- Feedback channel: plus/minus votes, free note, an FB file per understood finding (`specs/mia/feedback/`, next free id FB-10).

## Validation criteria in scope
| ID | Settles | Session (one week of daily use unless stated) | Evidence | Rating by |
|---|---|---|---|---|
| VAL-007 | G-V2 exit: converted skills and snapshots as good as before | use the six converted and nine interface skills as usual; take a snapshot, change a skill, restore it; `tools/run_explain.py problems`; time one skill on both runners (V2-4) | number of skills found worse, restores that did not give the former state, the two timings | owner |
| VAL-009 | G-V2.MODEL OC-1 to OC-3 | owner is shown the lookup record with both graphs, names command, steps and knowledge; three rule-breaking descriptions with their refusals | time, remarks, per refusal: message enough to fix? | owner |
| VAL-012 | G-V3 OC-1 to OC-6; settles the **Provisional strip height** of REQ-CLV-041 (16 %, 140 of 900 px) | lookup, search and review on desktop and phone; count each time the chat had to be read, Full run opened, or the page scrolled | counts; strip height kept or changed by the owner | owner |
| VAL-013 | G-V3.CHAT TR-CHAT-001 (production temperature vs temperature 0) | owner marks 20 sampled summaries and status messages (sampled by `run_explain.py list`, not chosen) faithful / in persona | shares with interval, compared with the holdout result (digest version 7); wrong ones become cases | owner |
| FB-08 | sources as links | already re-validated by the owner 2026-11-20 | – | closed |
| VAL-006 | speed and weight (field items) | medians from the run log: first text, calls of the first try, context share, model switch | medians; a missed target starts the next iteration | owner |

Not in scope this round: VAL-001, 003, 004, 005 (G-V1 material, never run; D-185); say in the report whether to run them now.

## Provisional and assumptions
- **Provisional:** REQ-CLV-041 strip height (VAL-012). The 3 s of REQ-VPB-006 is in the A-132 validation report, not this release; no voice on the target, so not checkable. `grep` finds no other `Provisional:` in the scope of G-V2 or G-V3.
- **Assumptions:** ASM-MU-001 (few trusted users, rarely at once): check the run log for two messages waiting together. Model capability and VRAM on the host: `ollama ps` (8.0 GB of 16 loaded), run log seconds per run. Falsified ones become findings.
- **Eval thresholds** are not settled here (M19).

## Open items inherited (not verdicts)
V2-4 (converted runs 2 to 10 times faster, cause unproven: time one skill on both runners), V3-6 (calls and seconds of the end message not measured: read from the run log), F-04 (status line not restored after reload, accepted D-344), V2-6 (no red-team case for THR-011), TD-82 to TD-85, TD-86 to TD-90 (unsigned drafts). Deferral triggers: review each on the day of the report.

## Tasks for the owner (goals, not clicks)
1. Run `/lookup` and `/search` as in daily work; judge from the view alone whether the run is done and what it found.
2. Run a skill from the graph path through the UI (e.g. research); compare with the old runner once.
3. Take a snapshot, change a skill, restore; see whether the former state is back.
4. Do the same on the phone for one day.
5. Exploratory: what is missing, what would you use this for?

## Agent analysis planned (after the week)
`tools/run_explain.py list | problems | cost`: runs per skill, failures, abstentions, budget ends, seconds and tokens against budgets, search queries sent out (read them). Cluster bad runs by failure mode and check each against the suites; uncovered clusters are drafted as cases with `failure-to-case.md` into `specs/mia/eval-drafts/` for the owner to label. No LLM judge is used, so no calibration.

## Quality in use (`quality.md`) – not covered
Public exposure, more than a handful of users, other languages, voice, character page, sandboxed `script` check, the Graph editor (FR-43).
