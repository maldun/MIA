# Requirements: Workflow management (N-2.3, low level)

**Parent:** `specs/mia/nodes/N-2-backend/requirements.md` (N-2)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The library of workflows and skills as versioned data, the graph rules, specification and benchmark records, context graphs, schedule and estimate, character variants. Provides IF-203; consumes IF-202 (measured costs) and IF-102. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-WFM-001 – Skills as tasks
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall perform each kind of work as a task defined by a skill file and a pipeline selectable by every user.
- Rationale: refines REQ-BE-033
- Parent: REQ-BE-033
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: the selectable list shows each skill; a selected skill runs its pipeline
- Verified by: TC-WFM-001
- Status: Verified
- History: –

### REQ-WFM-002 – Versioned workflow library
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall keep every pipeline and workflow as validated data in a library with the lifecycle draft, tested, trusted and retired and store every edit as a new immutable version with author and time.
- Rationale: refines REQ-BE-035
- Parent: REQ-BE-035
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10, AC-16: an edit creates version n+1 and leaves version n unchanged (exact)
- Verified by: TC-WFM-002
- Status: Verified
- History: –

### REQ-WFM-003 – No cycles
- Level: low   Subject: TaskRuntime
- Text: When a workflow is saved and before it runs, the Workflow management shall check by an algorithm that its graph has no cycle and name a cycle that it finds.
- Rationale: refines REQ-BE-036
- Parent: REQ-BE-036
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-27: a workflow with a cycle is refused with the cycle named; property test on generated graphs: every accepted graph has a topological order
- Verified by: TC-WFM-003
- Status: Verified
- History: –

### REQ-WFM-004 – Graph rules
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall refuse a workflow with two adjacent data nodes or a session node without a maximum number of cycles or a maximum time.
- Rationale: refines REQ-BE-037
- Parent: REQ-BE-037
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-27: each of the three violations is refused with the rule named (exact)
- Verified by: TC-WFM-004
- Status: Verified
- History: –

### REQ-WFM-005 – Model proposals stay drafts
- Level: low   Subject: TaskRuntime
- Text: When a model proposes a library entry, the Workflow management shall keep it as a draft until a user approves it, shown as a diff and tried on the test set.
- Rationale: refines REQ-BE-038
- Parent: REQ-BE-038
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-10: a proposed entry has status draft and cannot be run as trusted
- Verified by: TC-WFM-005
- Status: Verified
- History: –

### REQ-WFM-006 – Specification before trust
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall keep a workflow without specification and benchmark in draft status and refuse to promote it.
- Rationale: refines REQ-BE-039
- Parent: REQ-BE-039
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10: promotion of a workflow lacking its specification or its benchmark is refused (exact)
- Verified by: TC-WFM-006
- Status: Verified
- History: v1 reworded, A-16 (owner 2026-10-27: the context graph and the baseline of the benchmark are checked on the shipped workflows by inspection, TC-MIA-009, TC-MIA-010; the gate of the library checks specification and benchmark, as IF-203 says)

### REQ-WFM-007 – Time from idea to promotion
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall record the time from the idea of a skill to its promotion.
- Rationale: refines REQ-BE-040
- Parent: REQ-BE-040
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-9: the record has two time stamps for each promoted skill
- Verified by: TC-WFM-007
- Status: Verified
- History: –

### REQ-WFM-008 – Context graphs
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall keep one context graph per workflow and one for the chat and give each step the view that fits its token budget.
- Rationale: refines REQ-BE-041
- Parent: REQ-BE-041
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-10: the view of a step stays within its budget in tokens (exact on the recorded lookup run)
- Verified by: TC-WFM-008
- Status: Verified
- History: –

### REQ-WFM-009 – Workflow schedule and estimate
- Level: low   Subject: TaskRuntime
- Text: When a workflow is about to run, the Workflow management shall compute its order, critical path and an estimate of time, calls and tokens from its graph and the measured costs, and refuse a run whose estimate exceeds its budget.
- Rationale: refines REQ-BE-042
- Parent: REQ-BE-042
- Priority: Should
- Verification method: Test, Measurement
- Acceptance criterion: AC-28: on the recorded lookup runs the estimate is within the factor set in Plan of the measured time
- Verified by: TC-WFM-009
- Status: Verified
- History: –

### REQ-WFM-010 – Character variant per workflow
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall let a workflow name a character variant and send it to the frontend while the workflow runs.
- Rationale: refines REQ-BE-043
- Parent: REQ-BE-043
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-17: a run with a variant sends the variant name; a run without sends none
- Verified by: TC-WFM-010
- Status: Verified
- History: –

### REQ-WFM-011 – Code checks first
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow verify as a library entry whose model steps come after every code check that exists for the claim.
- Rationale: refines REQ-BE-046
- Parent: REQ-BE-046
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2: in the run log the code checks precede the first model call of each claim
- Verified by: TC-WFM-011
- Status: Verified
- History: –

### REQ-WFM-012 – Unclear without evidence
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow verify so that a claim with a number and no evidence gets the verdict unclear without a model call.
- Rationale: refines REQ-BE-047
- Parent: REQ-BE-047
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2: for 10 claims with a number and no evidence there are 0 model calls and the verdict is unclear (exact)
- Verified by: TC-WFM-012
- Status: Verified
- History: –

### REQ-WFM-013 – A failed check informs the judge
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow verify so that a failed code check reaches the judgement step as a contradiction found by code.
- Rationale: refines REQ-BE-048
- Parent: REQ-BE-048
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2: the judge input contains the check line (exact); the verdict is the judge's
- Verified by: TC-WFM-013
- Status: Verified
- History: –

### REQ-WFM-014 – Judgement quality
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow verify so that on the holdout it passes fewer wrong claims than the single voice and loses no more true claims among those with evidence.
- Rationale: refines REQ-BE-049
- Parent: REQ-BE-049
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-2: decided with the rule of the agent-app workflow against the baseline
- Verified by: TC-WFM-014
- Status: Verified
- History: –

### REQ-WFM-015 – Stable verdicts
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflows verify and lookup so that a repeated run on the same input and the same sources gives the same verdicts and the same set of facts.
- Rationale: refines REQ-BE-050
- Parent: REQ-BE-050
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-2: stability limit 0.90 (lower bound of the 95 % interval, at least) on the dev suites (REQ-VER-005, REQ-VER-006)
- Verified by: TC-WFM-015
- Status: Verified
- History: –

### REQ-WFM-016 – Lookup with sources
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow lookup as a library entry that answers a factual question with the sources and verbatim quotes that back it, or with unknown when nothing backs an answer.
- Rationale: refines REQ-BE-051
- Parent: REQ-BE-051
- Priority: Must
- Verification method: Test, Measurement
- Acceptance criterion: AC-2: every answer of the lookup suite carries a source and a quote or the verdict unknown
- Verified by: TC-WFM-016
- Status: Verified
- History: –

### REQ-WFM-017 – Search command
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the search command as a library entry that lists the findings of the metasearch (title, address, short text) without composing or verifying an answer.
- Rationale: refines REQ-BE-052
- Parent: REQ-BE-052
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-23: /search returns the list and starts no pipeline
- Verified by: TC-WFM-017
- Status: Verified
- History: –

### REQ-WFM-018 – Review report
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow review (keywords, search per keyword, collection, screening, review of each work, report) as a library entry that produces a report with the keywords and the query of each search, a flow count (found, duplicates, dropped before screening, excluded at the abstract and at the full text with reasons, included), for each work its keywords, decision, grade and notes with verbatim anchors, and the open gaps (keywords without an included work).
- Rationale: refines REQ-BE-053
- Parent: REQ-BE-053
- Priority: Should
- Verification method: Measurement
- Acceptance criterion: AC-3: per tier source recall and precision against the baseline
- Verified by: TC-WFM-018
- Status: Verified
- History: A-18 reworded (narrow variant: a literature review in fixed stages, flow count as in PRISMA 2020; was: findings per sub-question, conflicts)

### REQ-WFM-019 – Review in stages, run mode and slices
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow review so that it works in stages, gives an intermediate report with a recommendation after the stage of the abstract screening and goes on to the full-text stage only when the requesting user agrees; in the mode run (default, REQ-WFM-034) it asks no question at a used-up limit but at a hard cap, where the user decides to continue, to summarize or to stop, in the mode slice (option `slice`) it also works in time slices, gives an intermediate report at the end of each slice and continues only when the user agrees.
- Rationale: refines REQ-BE-054
- Parent: REQ-BE-054
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-3: after the abstract screening the run waits for agreement in both modes; in slice mode it waits for agreement after the first slice (60 s); in run mode no question comes at a used-up limit below the cap (exact)
- Verified by: TC-WFM-019
- Status: Verified
- Quality: functional suitability measure: share of review runs that end with a named end reason (complete, user, stopped, or the cap that ended it); target: 100 %; context: the owner's local model, runs of minutes to hours
- History: A-18 reworded (checkpoint before the full-text stage); A-23 reworded (run mode, slice as option); A-27 reworded (the question at a hard cap)

### REQ-WFM-020 – Review stops by a code check
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow review so that it ends when a code check finds every collected work decided and no approved keyword left to search, or a budget is used up.
- Rationale: refines REQ-BE-055
- Parent: REQ-BE-055
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-3: with a fake model that always says done, the run still continues until the code check holds
- Verified by: TC-WFM-020
- Status: Verified
- History: A-18 reworded (was: every sub-question answered)

### REQ-WFM-021 – Source records and cut-off
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflows lookup and review so that they record where a source comes from and how far it is trusted, keep the users' edits of that trust and honour a time cut-off strictly.
- Rationale: refines REQ-BE-056
- Parent: REQ-BE-056
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: 0 violations of the cut-off; retracted works are dropped and listed (exact)
- Verified by: TC-WFM-021
- Status: Verified
- History: –

### REQ-WFM-022 – Method transfer
- Level: low   Subject: TaskRuntime
- Text: Where method transfer is switched on, the Workflow management shall deliver the example workflow method_transfer as a library entry that offers few ranked candidate methods marked as hypotheses unless an executable test on a toy instance passed.
- Rationale: refines REQ-BE-057
- Parent: REQ-BE-057
- Priority: Could
- Verification method: Measurement
- Acceptance criterion: AC-26: the known method is in the top 3 on the retro-discovery cases
- Verified by: TC-WFM-022
- Status: Approved
- History: –

### REQ-WFM-023 – Confidence by code
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflows so that confidence figures are computed by tool calls of code from anchored evidence and the limits are reported with every result.
- Rationale: refines REQ-BE-066
- Parent: REQ-BE-066
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: each result shows its limits
- Verified by: TC-WFM-023
- Status: Verified
- History: v1 interpreted, A-17 (owner 2026-10-27): "limits" are what a reader must know about a result: the limits of the evidence (no source retrieved, sources not reachable, no reputable source, evidence cut, quotes removed) and the basis of its confidence figure; each is a {code, text} made by code. The number gate verify.number_gate@5 reports the ones it can see (evidence given with the claim, cut, number check not applicable or inconclusive, what stands behind the verdict); the source-related ones belong to lookup and the research pipelines

### REQ-WFM-024 – No invented source
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflows so that no source appears in an answer that a tool did not retrieve.
- Rationale: refines REQ-BE-067
- Parent: REQ-BE-067
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-3: 0 invented references and 100 % of cited quotes found in their source
- Verified by: TC-WFM-024
- Status: Verified
- History: –

### REQ-WFM-025 – State only through the storage interface
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall keep and read workflows and context graphs only through the storage interface IF-102.
- Rationale: refines REQ-BE-074
- Parent: REQ-BE-074
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-15: no database driver is imported outside the storage client
- Verified by: TC-WFM-025
- Status: Verified
- History: –

### REQ-WFM-026 – Workflow and graph API
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall list, read, save as a new version, show the history and diff of, and restore workflows and context graphs through IF-203, and refuse an invalid graph with the broken rule named.
- Rationale: refines REQ-BE-076
- Parent: REQ-BE-076
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-16: with the fake storage each of the six operations works; an invalid graph is refused with the rule named (exact)
- Verified by: TC-WFM-026
- Status: Verified
- History: –

## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-203 – Workflow library
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall provide the API and accounts, the Chat agent and the Workflow execution with the library interface IF-203 as specified in contracts/IF-203-workflow-library.md (list, read, save as a new version, history, diff, restore, the lifecycle status, and the estimate of a run).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-BE-035, REQ-BE-076
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10, AC-16, AC-28: the contract suite test_if_203_workflow_library.py passes against the mock (stage 1) and the Workflow management (stage 2)
- Verified by: TC-IF-203-01..04
- Frozen: G-V2
- Status: Verified
- History: v0, amendment 5/7 (2026-10-25)

### REQ-WFM-027 – Keyword extension with approval
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall, in the example workflow review, count by code the terms that occur in the screened works and are not in the keyword set, propose every term that occurs in at least N works (N = 3, to be optimised) and extend the search with it only after the requesting user approves.
- Rationale: refines REQ-BE-053; the search follows the vocabulary of the field and not only the words of the question
- Parent: REQ-BE-053
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-3: a term below N works is never proposed; a proposed term is searched only after approval; without approval the keyword set is unchanged (exact)
- Verified by: TC-WFM-027
- Status: Draft
- History: A-18 new

### REQ-WFM-028 – Staged screening with decision and grade
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall, in the example workflow review, screen each work in two stages, the abstract against the research question and the written inclusion and exclusion criteria, then each section of the open full text and its fit with the conclusion, so that each stage gives two independent judgements, the relevance of the work to the research question as a grade 0 to 3 and the eligibility as include, maybe or exclude with a reason code of a criterion, each with a short statement and a verbatim quote, code combines the stage grades by a fixed rule, no rule derives the eligibility from the grade, and a work without open full text keeps its abstract judgements marked as abstract only.
- Rationale: refines REQ-BE-053; screening with criteria and reasons is the practice of systematic reviews (PRISMA 2020), the four-point graded relevance scale is the one of information retrieval evaluation (Järvelin and Kekäläinen 2002); the two judgements have different purposes (a historic work can be highly relevant and still be excluded as outdated)
- Parent: REQ-BE-053
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-3: every statement quotes its source (checked by code); the combined grade follows the rule on scripted stage results; a grade 3 work can be excluded and a grade 0 work cannot be included by the grade alone; a work without full text is marked abstract only (exact)
- Verified by: TC-WFM-028
- Status: Draft
- History: A-18 new

### REQ-WFM-029 – Skill id is the command
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall give every skill one unique id that is at the same time the name of its command in the chat, the name of its skill file and the id of its library entry, shall refuse a second skill with an id that is already in use, and shall build the list of commands from the library and not from a list in the code.
- Rationale: refines REQ-BE-033; with many skills (lookup, search, review, ...) a command that is not the id of a skill is a second name to keep in step (owner 2026-10-29)
- Parent: REQ-BE-033
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: the list of commands shows each skill under its id; a second skill with the same id is refused with the id named; a new skill file appears in the list without a change of code (exact)
- Verified by: TC-WFM-029
- Status: Draft
- History: A-23 new

### REQ-WFM-030 – Options of a skill
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall let every skill declare its options (name, type, default, a short text), accept them in the chat as `/<id> options <name>[=<value>] ... -- <argument>`, list them with their defaults for `/<id> options` alone, apply the defaults of the configuration key `skill_options` for the skills named there, and refuse an unknown option or a value of the wrong type with the options of the skill named.
- Rationale: refines REQ-BE-033; options belong to the skill, not to the chat (owner 2026-10-29: `/review options slice`, the same pattern for every later skill)
- Parent: REQ-BE-033
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: `/review options slice -- q` runs with slice and the argument q; `/review options` lists the options and defaults; an unknown option is refused and nothing runs; a configured default applies and is overridden by the call (exact)
- Verified by: TC-WFM-030
- Status: Draft
- History: A-23 new

### REQ-WFM-031 – Task monitor
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall let every task report its state while it runs, the phase, budget figures (used and limit) for time, tokens, model calls, API requests and the budgets of its own, and counts of its own, and shall show them on one status card per task that is updated in place at most twice per second and stays with the final figures after the task has ended.
- Rationale: refines REQ-BE-033; a long task shows numbers and not only a sign of life (owner 2026-10-29); the card renders any budget and count the task reports, so every later task has the same monitor
- Parent: REQ-BE-033
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: a task that reports gets a card with exactly the figures it reported; two reports within half a second give one update; the final figures stay on the card; a task that reports nothing gets the card with the time only (exact)
- Verified by: TC-WFM-031
- Status: Draft
- Quality: performance efficiency measure: status updates of one task per second; target: at most 2; context: a task that reports after every step, for example one screening step per work
- History: A-23 new

### REQ-WFM-032 – Figures of the review
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall report for the example workflow review at least the sources on the list, the sources processed and the sources still to process, the sources included, maybe and excluded, the sources dropped before the screening, and the limits for time, tokens, model calls, API requests, sources screened and sources read with what is used of each.
- Rationale: refines REQ-BE-053; the figures of the owner's hand review 2026-10-29
- Parent: REQ-BE-054
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: on a scripted run after every step on the list = processed + still to process; included + maybe + excluded = processed; every limit shows used and limit (exact)
- Verified by: TC-WFM-032
- Status: Draft
- Relaxed: TD-03
- Target: the tokens used are the counts reported by the model server, not an estimate
- History: A-23 new

### REQ-WFM-033 – Pause and resume
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall let the requesting user pause a running task and resume it, a paused task shall not start a new step and shall not use time of its budget, and stop shall end a paused task.
- Rationale: refines REQ-BE-033; a run without questions must still be controllable (owner 2026-10-29)
- Parent: REQ-BE-033
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: after pause no step starts and the used time stays constant for 5 s; after resume the task goes on from the same step; stop ends a paused task with the report as it stands (exact)
- Verified by: TC-WFM-033
- Status: Draft
- Quality: reliability measure: seconds of the time budget used while a task is paused; target: 0, and stop ends a paused task every time; context: a long run that the owner pauses and resumes
- History: A-23 new

### REQ-WFM-034 – Run mode, hard caps and slicing
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run a task with a budget in the mode run by default, without a question at a used-up limit and bounded by hard caps, a time cap of 30 minutes of work time (the time of a pause and the time the user needs to answer a question do not count; configurable) and, for each count, the limit times a configurable factor (default 10); at a hard cap it shall ask the user whether to continue for another cap, to summarize what has been read, or to stop with the result as it stands, and a missing answer summarizes; in the mode slice, set by the option `slice` or by the class of the model, it works with the limits as slices and a question at each of them.
- Rationale: refines REQ-BE-054; local models cost no money, so asking at every limit is tedious; paid models need the slices (owner 2026-10-29)
- Parent: REQ-BE-054
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: in run mode no question is asked below the cap; the time cap is 1800 s of work time and a waiting for the user does not use any of it; at the cap the question names the cap and the three answers; continue adds one more cap, summarize ends the search and writes the summary of what is read, stop gives the report without a summary, no answer summarizes; in slice mode the question comes at each limit as before (exact)
- Verified by: TC-WFM-034
- Status: Draft
- History: A-23 new; A-27 reworded (time cap 30 minutes of work time, question at the cap; owner's hand test 2026-10-29)

### REQ-WFM-035 – Class of the model
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall keep for each model whether it is local or paid, ask the user once whether a model is paid when the model has not been used before and is not clearly local, never ask again for a model that is known, change the class only on the user's command `/model paid <name>` or `/model local <name>`, and give a warning at the start of a task with a paid model and use the mode slice by default for it.
- Rationale: refines REQ-BE-054; commercial models must not run without slices unawares (owner 2026-10-29)
- Parent: REQ-BE-054
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: a new model is asked once, the second use is not asked; a paid model gives the warning and slice; `/model local <name>` changes the stored class; the asking and the change are shown in the chat (exact)
- Verified by: TC-WFM-035
- Status: Draft
- Quality: flexibility measure: questions about the class of one model; target: 1 for each model, ever (a known model is never asked again); context: switching between local models and an occasional paid one
- History: A-23 new

### REQ-WFM-036 – Result at the end of the chat
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall, for a task that asks questions while it runs, publish the result as a new message at the end of the chat when it is ready, show the progress only on the status card, and, when the task fails, publish a result that says what failed instead of an empty message.
- Rationale: refines REQ-BE-033; the result must not sit in a message far above the questions and answers that came later (owner 2026-10-29)
- Parent: REQ-BE-033
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: on a review with two questions the result message has a later position in the history than the last question and its answer, and no message of the task exists before the result except the questions; a task that fails leaves a result that contains the reason (exact)
- Verified by: TC-WFM-036
- Status: Draft
- History: A-23 new; A-27 reworded (a failure is a visible result)

### REQ-WFM-037 – Files in a volume
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall let a task store generated files in a dedicated volume (a folder that the configuration can move to another volume, by default on the disk of MIA) with a limit for one file and a limit for the whole volume from the configuration, refuse and say so when a limit would be crossed, never delete a file by itself, list the files of the volume for every signed-in user with a download, and add the files of a task to its result as download links.
- Rationale: refines REQ-BE-033; generated files (report, later more) need a place that is not a button on one message (owner 2026-10-29: a files area, deleted by the user in the volume)
- Parent: REQ-BE-033
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: a stored file is listed with name, size, time and task and is downloaded byte for byte; the result of the task ends with a link for each file it stored; a name with a path or a type that is not allowed is refused; a file over the limit is not written and the task says so; a file deleted in the volume is gone from the list (exact)
- Verified by: TC-WFM-037
- Status: Draft
- Quality: security measure: files outside the files volume that a task can write or read through the interface; target: 0 (a name with a path or a type that is not allowed is refused); context: the files list for the trusted users
- History: A-23 new; A-27 reworded (links in the result; owner's hand test 2026-10-29)

### REQ-WFM-038 – Report as a record
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall store the finished report of the example workflow review as a record in the database through the storage interface IF-102 with the question, the skill id and version, the account, the model pin and the structured report (flow figures, works with decisions, grades and notes, keywords, limits and the end reason), and shall render the files of the report (markdown and LaTeX, English headings) from this record.
- Rationale: refines REQ-BE-053; a record can be used for further reference and for benchmarks, the files are a view of it (owner 2026-10-29)
- Parent: REQ-BE-053
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: the record read back has the same figures and works as the report; the markdown and the LaTeX file made from it contain every work with its decision; the LaTeX special characters are escaped (exact)
- Verified by: TC-WFM-038
- Status: Draft
- History: A-23 new

### REQ-WFM-039 – Skills are self-contained extensions
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall load each skill that runs as a task from a folder of its own (a manifest with the id, the text, the options and what the task needs from the core, the skill files and the code of the skill), so that a new skill needs no change of the chat service, the web application or the page, except a skill that adds an output view of its own, which belongs to the core.
- Rationale: refines REQ-BE-033; lookup and review are the models (owner 2026-10-29: skills are extensions, only a substantial addition such as a new output window goes into the core)
- Parent: REQ-BE-033
- Priority: Should
- Verification method: Test, Inspection
- Acceptance criterion: AC-23: a folder added to the extensions folder appears in the list of commands, its options are parsed and its task runs; no file of the core names the id of a skill (inspection, exact)
- Verified by: TC-WFM-039
- Status: Draft
- Quality: maintainability measure: files of the core that name the id of a skill in code; target: 0; context: adding a skill
- Relaxed: TD-04
- Target: the code of a skill lies in its folder; what several skills share is a library of the core with its own name
- History: A-24 new

## Iteration 2 (goal G-V2, skill rework: foundation)

## Groups
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 1 | SK | Skill record: the skill as one versioned record (FR-36) | REQ-WFM-040, REQ-WFM-041, REQ-WFM-042 |
| 2 | GM | Graph model: data, transform and master nodes and their rules (FR-37) | REQ-WFM-043, REQ-WFM-044, REQ-WFM-045, REQ-WFM-046, REQ-WFM-047, REQ-WFM-048, REQ-WFM-049 |
| 3 | TB | Toolbox and trust: transforms by ID, status, import and export (FR-38) | REQ-WFM-050, REQ-WFM-051, REQ-WFM-052, REQ-WFM-053, REQ-WFM-054, REQ-WFM-055, REQ-WFM-056, REQ-WFM-067 |
| 4 | CV | Conversion: moving today's skills onto the records, one by one (FR-45) | REQ-WFM-057, REQ-WFM-058, REQ-WFM-059, REQ-WFM-060, REQ-WFM-068, REQ-WFM-069, REQ-WFM-070, REQ-WFM-110, REQ-WFM-111, REQ-WFM-112, REQ-WFM-113, REQ-WFM-114, REQ-WFM-115 |
| 5 | SN | Snapshots: the skill set kept and restored (FR-47) | REQ-WFM-061, REQ-WFM-062, REQ-WFM-063, REQ-WFM-064, REQ-WFM-065, REQ-WFM-066 |

### REQ-WFM-040 – Skill record
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall store each skill as one versioned record of an ID, a command, a workflow graph ID and a context graph ID.
- Rationale: refines FR-36
- Parent: FR-36
- Group: SK
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a skill record is stored, read back and equal to the stored one (exact); an edit is a new version
- Verified by: TC-WFM-040
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-041 – Skill taken from its record
- Level: low   Subject: TaskRuntime
- Text: While a skill has a skill record, the Workflow management shall take its command, workflow graph and context graph from that record and not from its skill file, extension manifest or pipeline reference.
- Rationale: refines FR-36; the old form is replaced one skill at a time (FR-45)
- Parent: FR-36
- Group: SK
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: with the old skill file of a converted skill removed, the skill is listed and runs unchanged (exact)
- Verified by: TC-WFM-041
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-042 – Command used once
- Level: low   Subject: TaskRuntime
- Text: If a skill record names a command that another skill already uses, then the Workflow management shall refuse the record and name that skill.
- Rationale: refines FR-36; two skills with one command would make the chat command ambiguous (REQ-WFM-029) Suggestion of the agent, not in the HLS text; the owner decides at review.
- Parent: FR-36
- Group: SK
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-31: a second record with the command of the first is refused with the first skill's ID (exact)
- Verified by: TC-WFM-042
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-043 – Three node types
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall accept a workflow graph only if every node is a data node, a transform node or a master node.
- Rationale: refines FR-37
- Parent: FR-37
- Group: GM
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a graph with a node of another type is refused naming the node (exact)
- Verified by: TC-WFM-043
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-044 – Graph description
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall keep with each workflow graph an ID, the ID of its context graph, the ID of its testbench and a description.
- Rationale: refines FR-37; the testbench ID may be empty until the testbench exists (FR-44, a later goal)
- Parent: FR-37
- Group: GM
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: the four fields are read back as stored; an empty testbench ID is accepted
- Verified by: TC-WFM-044
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-045 – Data and transform alternate
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall refuse a workflow graph that has an edge between two data nodes or between two nodes that are not data nodes.
- Rationale: refines FR-37; the owner's note: between all nodes there is a transform, a nil transform if need be; this is rules R2 and R3 of FR-7 with the new node types
- Parent: FR-37
- Group: GM
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: an edge data-data and an edge transform-master are refused naming the edge (exact)
- Verified by: TC-WFM-045
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-046 – One writer per data node
- Level: low   Subject: TaskRuntime
- Text: If a data node is written by more than one transform or master node, then the Workflow management shall refuse the workflow graph and name the data node.
- Rationale: refines FR-37; several transforms may read a data node
- Parent: FR-37
- Group: GM
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: two writers of one data node are refused with its ID; two readers are accepted (exact)
- Verified by: TC-WFM-046
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-047 – No cycle
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall refuse a workflow graph that has a cycle and name the cycle.
- Rationale: refines FR-37 and REQ-WFM-003; the rule stays as in FR-7
- Parent: FR-37
- Group: GM
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a graph with a cycle is refused with the cycle as ids, first id repeated at the end (exact); every accepted graph has a topological order (property test)
- Verified by: TC-WFM-047
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-048 – Master node stops
- Level: low   Subject: TaskRuntime
- Text: If a master node has neither a maximum number of cycles nor a maximum time, then the Workflow management shall refuse the workflow graph and name the node.
- Rationale: refines FR-37; rule R4 of FR-7 for master nodes
- Parent: FR-37
- Group: GM
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a master node without a stopping criterion is refused; with max_cycles 1 it is accepted (exact)
- Verified by: TC-WFM-048
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-049 – Parameters of a data node
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall let each data node hold its parameters, such as a folder to store into, in a field apart from its value.
- Rationale: refines FR-37; the owner's note: output nodes can hold parameters like a folder, so there should be a dedicated field Suggestion of the agent, not in the HLS text; the owner decides at review.
- Parent: FR-37
- Group: GM
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-31: a data node with parameters is stored and read back with the parameters apart from the value (exact)
- Verified by: TC-WFM-049
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-050 – Transforms by ID
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall keep every transform in a toolbox under an ID that is unique in the toolbox.
- Rationale: refines FR-38
- Parent: FR-38
- Group: TB
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-32: a second transform with an existing ID is refused (exact)
- Verified by: TC-WFM-050
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-051 – Trust status of a transform
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall give every transform in the toolbox the trust status untrusted or trusted.
- Rationale: refines FR-38; trust is about security (may it run at all); performance is the separate lifecycle of REQ-WFM-067 (owner 2026-11-07)
- Parent: FR-38
- Group: TB
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-32: a transform has one of the two trust statuses; any other value is refused (exact)
- Verified by: TC-WFM-051
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-052 – Imported means untrusted
- Level: low   Subject: TaskRuntime
- Text: When a transform is imported from outside MIA, the Workflow management shall store it with the status untrusted.
- Rationale: refines FR-38; SC-09
- Parent: FR-38
- Group: TB
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-32: a transform imported with the field status set to trusted is stored untrusted (exact)
- Verified by: TC-WFM-052
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-053 – Import runs no code
- Level: low   Subject: TaskRuntime
- Text: When a transform is imported, the Workflow management shall not run any code of the transform.
- Rationale: refines FR-38; TB-exchange
- Parent: FR-38
- Group: TB
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-32: the marker side effect in the imported transform does not happen on import (exact)
- Verified by: TC-WFM-053
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-054 – Only the owner trusts
- Level: low   Subject: TaskRuntime
- Text: If an account other than the owner asks to set the status of a transform to trusted, then the Workflow management shall refuse the change.
- Rationale: refines FR-38; exception to CON-6 (A-89, owner 2026-11-05): everyone edits data nodes and graphs, only the owner marks a transform trusted
- Parent: FR-38
- Group: TB
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-32: the owner's account changes the status, any other account is refused and the status stays (exact)
- Verified by: TC-WFM-054
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-055 – Exchange form
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall export a transform as one JSON file that holds its ID, version, input and output schemas and its code as text, and import the same file.
- Rationale: refines FR-38 ('a form that can be stored and exchanged outside MIA'); the file format is the agent's proposal, the sandbox for the code text is TD-24 Suggestion of the agent, not in the HLS text; the owner decides at review.
- Parent: FR-38
- Group: TB
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-32: export then import into an empty toolbox gives a transform with the same ID, version and schemas (exact)
- Verified by: TC-WFM-055
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-056 – Shipped transforms
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall seed the toolbox with the transforms that MIA ships, each with the status trusted.
- Rationale: refines FR-38 and FR-45; the nodes of `library/nodes` are MIA's own code and the converted skills need them to run Suggestion of the agent, not in the HLS text; the owner decides at review.
- Parent: FR-38
- Group: TB
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-32: after a first start every shipped node is in the toolbox as trusted (exact)
- Verified by: TC-WFM-056
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-057 – Old runner until proven
- Level: low   Subject: TaskRuntime
- Text: While the converted version of a skill has not passed its equivalence check, the Workflow management shall run the skill from its old skill file and pipeline.
- Rationale: refines FR-45 and AC-34: a skill with a failing run stays on the old runner
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-34: a skill marked unconverted runs on the old runner; its converted version is not used (exact)
- Verified by: TC-WFM-057
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-058 – Same model calls
- Level: low   Subject: TaskRuntime
- Text: When a converted skill runs on scripted model replies, the Workflow management shall make the same model calls as the old runner, in the same order with the same prompts and options.
- Rationale: refines FR-45; a deterministic first check before the eval run, so a changed prompt or step order is caught without a model. Suggestion of the agent, not in the HLS text; the owner decides at review.
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-34: per skill, the list of model calls of the old and the converted run on scripted replies is equal (exact, a diff is shown)
- Verified by: TC-WFM-058
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-059 – Same outcomes on the suite
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall mark the converted version of a skill as accepted only if the criterion of that skill's equivalence requirement passed on the dev split with the pin MP-light.
- Rationale: refines FR-45 and AC-34; the numbers sit in the per-skill requirements REQ-WFM-110 to 115 (split per skill on the owner's decision of 2026-11-07, because one criterion line holds one suite); starting values by educated guess (owner 2026-11-07), configuration (REQ-WFM-069), a run uses one fixed version of them
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-34: on scripted run files, a skill whose criterion passes is accepted; a skill whose criterion fails or is not decided stays unconverted (exact)
- Verified by: TC-WFM-059
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new; Plan step 3 (2026-11-07): the Eval criterion line did not parse (agent_check A2), so the criteria moved to REQ-WFM-110 to 114 and the text became the acceptance rule (owner: split per skill); approved text of the review of 2026-11-07 superseded, back to review

### REQ-WFM-060 – Record of the check
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall record for each skill the suite, run, pins and verdict of its equivalence check, or the reason it is not converted.
- Rationale: refines FR-45 ('or stays on the old runner for a named reason', exit criterion of G-V2). Suggestion of the agent, not in the HLS text; the owner decides at review.
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-34: the record of each existing skill names the form it runs on and either a verdict with suite, run and pins or a reason (inspection)
- Verified by: TC-WFM-060
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-061 – Take a snapshot
- Level: low   Subject: TaskRuntime
- Text: When the owner asks for a snapshot with a name, the Workflow management shall store the skills, workflow graphs, context graphs, transforms with trust status and lifecycle, and their model pins.
- Rationale: refines FR-47; debate definitions are added when they exist (goal D)
- Parent: FR-47
- Group: SN
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-40: a snapshot holds every item named, each with its version, trust status and lifecycle (exact)
- Verified by: TC-WFM-061
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-062 – List snapshots
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall list the snapshots with name, time and author.
- Rationale: refines FR-47
- Parent: FR-47
- Group: SN
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-40: two snapshots are listed with the three fields (exact)
- Verified by: TC-WFM-062
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new; Plan step 3 (2026-11-07): Should raised to Must (owner: a restore asks for a name, and the snapshots of REQ-WFM-063 would be invisible without a list)

### REQ-WFM-063 – Restore keeps the former state
- Level: low   Subject: TaskRuntime
- Text: When the owner restores a snapshot, the Workflow management shall first store the current state as a snapshot of its own.
- Rationale: refines FR-47; Q-5 reliability
- Parent: FR-47
- Group: SN
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-40: after a restore of snapshot "a" a new snapshot named "before restore of a" with the state before it and the owner as author exists and can be restored (exact)
- Verified by: TC-WFM-063
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new; Plan step 3 (2026-11-07): name and author of the automatic snapshot added to the criterion (owner); text unchanged

### REQ-WFM-064 – Restore gives version and statuses
- Level: low   Subject: TaskRuntime
- Text: When the owner restores a snapshot, the Workflow management shall give every item in the snapshot the version, trust status and lifecycle it had in the snapshot.
- Rationale: refines FR-47
- Parent: FR-47
- Group: SN
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-40: a skill, a workflow graph, a context graph and a transform status are changed, then restored, and equal the stored ones; a transform untrusted in the snapshot is untrusted (exact)
- Verified by: TC-WFM-064
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-065 – Restore deletes nothing
- Level: low   Subject: TaskRuntime
- Text: When the owner restores a snapshot, the Workflow management shall delete no version of any item.
- Rationale: refines FR-47 and FR-40
- Parent: FR-47
- Group: SN
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-40: the list of versions before the restore is a prefix of the list after it (exact)
- Verified by: TC-WFM-065
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-WFM-066 – Snapshots only by the owner
- Level: low   Subject: TaskRuntime
- Text: If an account other than the owner account, the account that creates accounts, asks to take or restore a snapshot, then the Workflow management shall refuse the request.
- Rationale: refines FR-47 ('let the owner'); consistent with owner-only editing of skills (interview 11). Suggestion of the agent, not in the HLS text; the owner decides at review.
- Parent: FR-47
- Group: SN
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-40: a non-owner account is refused for both, the state stays (exact)
- Verified by: TC-WFM-066
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new; Plan step 3 (2026-11-07): "owner" defined in the text as the account that creates accounts (owner, D-260 B; TC-MIA-014)

### REQ-WFM-067 – Lifecycle of a transform
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall give every transform in the toolbox the lifecycle draft, tested or retired, apart from its trust status.
- Rationale: refines FR-38 (owner 2026-11-07: trusted/untrusted is about security, tested/retired about performance); a change to tested names the evidence (a check or run) that justifies it; the automatic gate by a testbench is FR-44 in goal D, until then the owner sets it
- Parent: FR-38
- Group: TB
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-32: a transform has one lifecycle value and one trust status independently of each other; any other lifecycle value is refused; a change to tested without a named evidence is refused (exact)
- Verified by: TC-WFM-067
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new, owner answer of 2026-11-07

### REQ-WFM-068 – A retired item stays usable as baseline
- Level: low   Subject: TaskRuntime
- Text: While a transform or a skill is retired, the Workflow management shall keep it runnable by a check as a baseline.
- Rationale: refines FR-38 and FR-45 (owner 2026-11-07: a retired skill may serve as baseline, for example the old form of a converted skill)
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-34: a retired transform runs when a check names it (exact)
- Verified by: TC-WFM-068
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new, owner answer of 2026-11-07

### REQ-WFM-069 – Settings of the equivalence check are configuration
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall read the margin, repeats and rule of the equivalence check from a versioned configuration record with defaults, and record the version used with every result.
- Rationale: refines FR-45 (owner 2026-11-07: start with educated guesses, adjustable and continuously improved by running and re-evaluating); M19 stays: a run uses one fixed version, a change is a new version that applies to later runs only and is never applied to a result already seen
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-34: a change of the margin creates settings version n+1, a new result names n+1 and an earlier result still names n (exact)
- Verified by: TC-WFM-069
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new, owner answer of 2026-11-07

### REQ-WFM-070 – A retired item is not offered
- Level: low   Subject: TaskRuntime
- Text: While a transform or a skill is retired, the Workflow management shall not offer it for a new graph or a new run.
- Rationale: refines FR-38 and FR-45; keeps the baseline from being used by accident
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-34: a retired transform is absent from the list for a new graph and a retired skill from the command list (exact)
- Verified by: TC-WFM-070
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new, owner answer of 2026-11-07

### REQ-WFM-110 – Same outcomes: research
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run the converted skill research so that it behaves as expected in at least 82 % of the dev cases of EV-research.
- Rationale: refines FR-45 and AC-34; v0.1.0 baseline 0.92 (research-escalate.md, 20 questions, 3 repeats) minus the margin 0.10, a starting guess under D-187 (REQ-WFM-069); the secondary suite EV-research_compound is run and reported, not decided
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-34: the share of right cases of the converted skill on the dev split of EV-research is at least 0.82 (3 repeats folded by majority, MP-light), decided by the rule, not by eye
- Eval criterion: suite=EV-research; select=; metric=right; min=0.82; n=20; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0050; split=dev
- Verified by: TC-WFM-110, EV-research
- Status: Draft
- History: G-V2 Plan step 3 (2026-11-07), new, split from REQ-WFM-059 (owner)

### REQ-WFM-111 – Same outcomes: plan_question
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run the converted skill plan_question so that it behaves as expected in at least 54 % of the dev cases of EV-plans.
- Rationale: refines FR-45 and AC-34; v0.1.0 baseline 0.64 (research-planners.md, 36 plans, 3 repeats, plan.free@1) minus the margin 0.10, a starting guess under D-187 (REQ-WFM-069); the baseline is low on purpose: the skill runs plan.free@1 today, the checked planner is a later change
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-34: the share of right cases of the converted skill on the dev split of EV-plans is at least 0.54 (3 repeats folded by majority, MP-light), decided by the rule, not by eye
- Eval criterion: suite=EV-plans; select=; metric=right; min=0.54; n=36; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0122; split=dev
- Verified by: TC-WFM-111, EV-plans
- Status: Draft
- History: G-V2 Plan step 3 (2026-11-07), new, split from REQ-WFM-059 (owner)

### REQ-WFM-112 – Same outcomes: verify_claim
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run the converted skill verify_claim so that it behaves as expected in at least 83 % of the dev cases of EV-verdicts.
- Rationale: refines FR-45 and AC-34; v0.1.0 baseline 0.93 (verdicts-single.md, 50 claims, 1 run, verify.single@1) minus the margin 0.10, a starting guess under D-187 (REQ-WFM-069); the baseline has one repeat; it is re-recorded at 3 repeats before any converted run; the suites EV-verdicts_injection and EV-verdicts_wikidata are run and reported, not decided
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-34: the share of right cases of the converted skill on the dev split of EV-verdicts is at least 0.83 (3 repeats folded by majority, MP-light), decided by the rule, not by eye
- Eval criterion: suite=EV-verdicts; select=; metric=right; min=0.83; n=50; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0001; split=dev
- Verified by: TC-WFM-112, EV-verdicts
- Status: Draft
- History: G-V2 Plan step 3 (2026-11-07), new, split from REQ-WFM-059 (owner)

### REQ-WFM-113 – Same outcomes: verify_computable
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run the converted skill verify_computable so that it behaves as expected in at least 82 % of the dev cases of EV-computable.
- Rationale: refines FR-45 and AC-34; v0.1.0 baseline 0.92 (computable-gemma4-12b.md, 39 cases, 1 run, verify.computable@2) minus the margin 0.10, a starting guess under D-187 (REQ-WFM-069); the baseline has one repeat; it is re-recorded at 3 repeats before any converted run
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-34: the share of right cases of the converted skill on the dev split of EV-computable is at least 0.82 (3 repeats folded by majority, MP-light), decided by the rule, not by eye
- Eval criterion: suite=EV-computable; select=; metric=right; min=0.82; n=39; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0001; split=dev
- Verified by: TC-WFM-113, EV-computable
- Status: Draft
- History: G-V2 Plan step 3 (2026-11-07), new, split from REQ-WFM-059 (owner)

### REQ-WFM-114 – Same outcomes: extract_claims
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run the converted skill extract_claims so that it behaves as expected in at least 59 % of the dev cases of EV-extraction.
- Rationale: refines FR-45 and AC-34; v0.1.0 baseline 0.69 (extraction-llm-light.md, 51 texts, 1 run, extract.llm@1) minus the margin 0.10, a starting guess under D-187 (REQ-WFM-069); the baseline has one repeat; it is re-recorded at 3 repeats before any converted run
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-34: the share of right cases of the converted skill on the dev split of EV-extraction is at least 0.59 (3 repeats folded by majority, MP-light), decided by the rule, not by eye
- Eval criterion: suite=EV-extraction; select=; metric=right; min=0.59; n=51; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0064; split=dev
- Verified by: TC-WFM-114, EV-extraction
- Status: Draft
- History: G-V2 Plan step 3 (2026-11-07), new, split from REQ-WFM-059 (owner)

### REQ-WFM-115 – Same outputs: extract_claims_rules
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall run the converted skill extract_claims_rules so that it gives the same output as the old runner on every dev case of EV-extraction.
- Rationale: refines FR-45 and AC-34; the skill is rule-based, no model: the same input gives the same output, so equality is checked instead of a rate (Suggestion of the agent, the owner decides at review)
- Parent: FR-45
- Group: CV
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-34: the 51 outputs of the converted and the old run on the dev cases of EV-extraction are equal (exact, a diff is shown)
- Verified by: TC-WFM-115
- Status: Draft
- History: G-V2 Plan step 3 (2026-11-07), new, split from REQ-WFM-059 (owner)
