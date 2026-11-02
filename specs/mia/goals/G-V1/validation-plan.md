# Validation plan: G-V1 (DRAFT of 2026-11-01; **not run**: G-V1 closed without validation, D-185; this material is kept for the next goal)

Prepared by the coding agent for the owner. People judge; the agent prepares sessions and analyses the run logs locally (run logs are confidential: nothing goes to a remote model or service). Phase 7 skills: `validate-phase`, `agent-app-validate`. Exit criterion of G-V1: **VAL-001 and VAL-003 to VAL-006** (VAL-002 moved to the next goal, D-134). Template of the result: `validate-phase/assets/validation-report.md` plus `agent-app-validate/assets/validation-report-agent.md`.

## Frozen version
The deployed version of `deployment-record.md`. No pulls, no skill or prompt edits on the target during validation; a fix is a patch version.

## Validators and data
- Validators: the owner and the handful of trusted users with an account (CON-6); not the builders of a single feature.
- Personal data: the run log holds the conversations of the users. Before the first use: **informed consent** of every user (what is stored: messages, votes, run logs; who reads them: the owner; where: the owner's host only), collect only what the criteria need, **retention and deletion date** <<owner sets, e.g. the end of validation + 30 days>>; examples in reports are pseudonymised.
- Feedback channel: the plus/minus votes in the chat (FR-27, answers only in this release, REQ-CLV-010 partly), a free note to the owner, and an FB file in `specs/mia/feedback/` per understood finding (template `validate-phase/assets/feedback-item.md`; FB-01 to FB-06 exist).

## Validation criteria
| ID | Criterion | Sessions and tasks | Evidence | Rating by |
|---|---|---|---|---|
| VAL-001 | the owner can trust the facts in a lookup answer | **scope (owner, 2026-11-02): `/lookup` answers only; the owner seeds the log himself by using `/lookup` in daily work; the sample is drawn after at least 20 such answers exist from the deployed v0.1.0 (the runs before 2026-11-02 and the smoke runs do not count); fewer than 20 after the validation week is itself a finding** — the owner takes 20 answers of the lookup from real use (sampled from `tools/run_explain.py list`, not chosen by the owner) and confirms or rejects the verdict against the sources | the confirmed share with its interval; rejected ones become eval cases (`agent-app-validate/assets/failure-to-case.md`, drafts in `specs/mia/eval-drafts/`, labelled by the owner) | owner |
| VAL-003 | the character feels in character and pleasant | each user chats for a week; the weekly overall score (FR-27), a short rating per user after one week (1 to 5 and a free line), the check dialogues are deferred (TD-10, AC-8) | the score trend over the week, the ratings, quotes | users and owner |
| VAL-004 | MIA is usable on a phone inside the tailnet | each user uses the chat on their phone for one week and reports problems; `ui/CHECKLIST_CHAT_PHONE.md` once at the start; SMOKE-MIA-002 at deployment (**not run yet, TD-26, D-184: run it before this check starts**) | list of problems with counts, one quote each | users |
| VAL-005 | the platform is a blueprint: a person adds a new example workflow by the documented path without changing platform code | a dry run with a new small workflow by the documented skill path (`tests/acceptance/test_skill_path_doc.py` names the document); time recorded | the time, the steps that needed platform code (none expected) | owner |
| VAL-006 | MIA is fast and light enough in daily use | over one week: first text time, queue wait, frame rate on the phones in use, model calls of the first try, context share, model switch time, from the run log and the measurement tools (BM-MIA-001, -002 are deferred, TD-16: they are measured here first, descriptively) | medians per measure; a figure that misses its target starts the next iteration | owner and users |

Open numbers decided earlier (test-spec "Open numbers"): first text within 10 s on MP-light (NFR-7), 30 fps on the phone and the desktop, queue of 5 waiting messages and 2 per user, a change visible on a second device within 5 s.

## Tasks for the users (goals, not click instructions)
1. Ask MIA a question whose answer is on the web and judge whether you would act on it (lookup, sources and quotes).
2. Ask something MIA cannot know and see what it does ("unknown" is the right answer).
3. Chat with a second user at the same time; stop an answer; reload the page.
4. Give plus and minus on answers; change a setting that everyone sees (expression, persona) and watch it appear on the other device.
5. Use it on the phone away from the desk for a day.
6. Exploratory: what is missing, what would you use this for?

Observation protocol (owner or a helper, not helping): time to first text, what the user did next, errors shown, requests for help, quotes. Think-aloud for the first session only.

## Provisional requirements and assumptions
- **Provisional requirements in scope:** none found (`grep -rn "Provisional" specs/mia/requirements.md specs/mia/nodes` finds no `Provisional:` line). The goal check passes with no open provisional requirement.
- **Assumption ASM-MU-001** (a few trusted users who rarely work at the same time; queue of 5 and 2 per user): confirmed or falsified by the run log (how often two messages wait together) and by the users' reports.
- Model capability, latency and VRAM on the real host: from the run log and `ollama ps`; falsified assumptions become feedback items.

## Quality in use (`specs/mia/quality.md`)
Effectiveness (VAL-001), efficiency (VAL-006), satisfaction (VAL-003), freedom from risk (no private data in a query: read the web log, `tools/check_free.py`; the red-team suite is not part of the validation), context coverage (phone and desktop, the tailnet). **Not covered** (context of use): public exposure, more than a handful of users, paid APIs, languages other than English, safety-critical use, offline use of the chat page, the Graph app.

## Run-log analysis (after the week, local)
- `python tools/run_explain.py list` (runs per task, failures, abstentions, budget ends), `problems RUN` for the failing ones, `cost RUN` (calls, seconds, tokens), `explain RUN` for the 20 sampled lookups.
- The web log (`data/runs/web-YYYY-MM.jsonl`): every query that left the machine; no paid host (`python tools/check_free.py`).
- Cluster the bad runs by failure mode (wrong number, wrong source, ignored evidence, followed an instruction in a page, over-cautious "unknown", format drift, too slow); compare with the categories of the suites; clusters no suite covers are the most valuable findings. People interpret the clusters.
- **No LLM judge** is used in G-V1 (`specs/mia/eval-spec.md`, "LLM judge": the truth is a gold answer set by people), so there is no judge calibration to do.
- Numeric agreement is not claimed anywhere in this validation; small user numbers are reported descriptively (counts, medians, quotes), without p-values.

## Open deferrals to review in this phase
For each TD-01 to TD-04, TD-06 to TD-22: does the interim criterion still serve the purpose after a week of use? Decide per record: keep the trigger, schedule, extend with a reason, or drop with a reason. TD-12 to TD-20 are the nine stage 4 checks; the findings of VAL-001 and VAL-006 are the first real data for TC-MIA-002 and TC-MIA-019.

## Triage and decision
Every finding gets a type, priority and destination (`validate-phase`, "Triage"): bad output with a covered category → Implement (case first); an uncovered category → Plan (new cases); unsafe tool use → Plan, threat model, high; an assumption falsified → Plan or Deploy; usable but not trusted → Explore. Then the team decides: next iteration (a new goal, scoped again; FB-01 to FB-06 and the Graph app redesign are the known input), accept as is, or stop. FB items close only after re-validation in a deployed version and, for bad outputs, after their case is in a suite.

## What the agent does and does not
Prepares the sessions and this plan, extracts and clusters the run log locally, drafts failure cases and FB files, and writes the draft of `validation-report.md`. It does not rate a criterion as passed on its own, does not label truth, does not settle a provisional or a threshold, and does not tune anything on the target.
