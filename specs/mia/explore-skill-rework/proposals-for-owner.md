# Proposals for the owner (agent's draft, 2026-11-05, nothing applied)

Three open items of the Explore hand-over. Each is a proposal to correct, strike or confirm; `quality.md`, the HLS and the interview log are unchanged until you answer.

## 1. Example case "review report" (HLS section 5, the empty row)
Tier 1 of the review ladder: a small question, a short report. Proposed row, in the style of the table:

| Kind | Example input | What a right result looks like | Note |
|---|---|---|---|
| good: review report (tier 1) | "Does spaced repetition improve vocabulary retention?" with a small recorded set of 12 abstracts: 7 on topic, 3 off topic, 2 retracted | the 7 are kept, the 3 dropped with a reason, the 2 retracted are listed as excluded for retraction; every finding has a verbatim anchor from a kept source; conflicts between sources are shown, not averaged; one gap named; an answerability figure with its parts; ends with a named end ("all sub-questions answered" or "budget used") | suite for the review skill, labelled by a person |
| bad: review report | the same input | a finding without an anchor or with an anchor not in the source; a retracted paper used; a conflict smoothed into one claim; a missing gap; the end is "the model felt done" | |
| unknown is right: review report | a question the 12 abstracts do not address | "not answerable from these sources", the gap and next keywords; no finding | |

Questions: is a recorded set of 12 abstracts the right size for "small"? Is "retracted papers excluded" a case you want in tier 1, or only later?

## 2. Quality targets for the rework (rows for `quality.md`, "Quality in use" and "Characteristics")
Targets are proposals; numbers marked * are guesses until spike (a) and Validation.

| Characteristic | Proposed requirement or target |
|---|---|
| Functional suitability | context-graph builder: at least 68 % of marked items right and at most 5 % invented (your bar, spike C); after the quote rule, 0 accepted proposals whose name is not in the source document; skill conversion (FR-45): same outcomes on its suite as before |
| Performance efficiency | builder: at most 50 items and 5 minutes per document (configuration values); debate: 3 rounds, 12 calls, 5 minutes (configuration values, to be checked by spike (a)); context-graph share of a step's context at most 20 %, about 1 500 tokens |
| Interaction capability | FR-46: the chat holds only spoken text; a skill result in the chat is a short spoken summary with a link; every answer to a skill's question has a confirmation in the subwindow |
| Reliability | FR-47: a snapshot of the skill set can be restored and the former state is kept as a snapshot; a new version of a context graph marks dependent testbenches stale and none is silently reused |
| Security | no proposal is readable by a step before it is confirmed (TB-context); an imported transform is stored untrusted and never run until the owner marks it (while `sandbox_backend: none` this is one person's decision, see conflict 3) |
| Maintainability | a skill, a context graph and a transform are separate records with IDs and versions; N-6 runs in its own container |

Quality in use, effectiveness: share of builder proposals the owner confirms in a sample of each new document type (target 68 % right, 5 % invented as the starting point; fixed in Validation). Satisfaction and efficiency stay as in `quality.md`.

## 3. Conflicts for Plan (to be decided there; stated here so nothing is lost)
1. **Owner-only editing against CON-6 and FR-22.** CON-6 and FR-22 let every logged-in user edit every node and edge; FR-38 and the iteration-2 trust rule make "trusted" one person's mark. Proposal: everyone edits data nodes and graphs, only the owner marks a transform trusted; Plan states this as an exception to CON-6 and amends FR-22.
2. **FR-40 against IF-301 and IF-203.** Separate node and edge records change the interfaces of the storage layer and the workflow library and their protected contract suites. Proposal: Plan amends the interfaces and keeps the document form readable during the transition (as the HLS risk table already says); a contract suite change goes through a plan amendment, not through Implement.
3. **Trust rule while `sandbox_backend: none` (TD-24).** An imported transform that is marked trusted runs in the MIA process with MIA's permissions. Proposal: stored-but-not-runnable by default (as in the risk table), one entry in `shortcuts-register.md` for the interim rule, and the review process or a sandbox backend as the condition for lifting it.
