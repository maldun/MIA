# Plausibility review: 37 open items

Write your decision on every line `Decision:` and, where it helps, the reason on `Basis:`. Decision words: `plausible` | `field` (postponed to the field, VAL-006) | `accept: <reason>` (questionable, the risk is accepted for now, you are the owner, follow-up VAL-006) | `probe: <what> | <who> | <when>` | `risk: <reason> | <owner> | <follow-up>` | `implausible`. The suggestion lines are only the agent's opinion. Then run `python3 -I tools/import_plausibility_review.py .` and after it `tools/apply_plausibility.py`.

Context: a controlled environment with a few users (ASM-MU-001); performance and resource figures go to the field (VAL-006); the baseline of today's MIA is task T-04 (owner).

---

## Judgement quality of the verify workflow

**Facts found:** The suites verdicts, hard_checks and computable exist in eval/suites, with the baseline reports eval/baselines/verdicts-styles.md and computable-gemma4-12b.md. The criterion (fewer wrong claims than the single voice, no more true claims lost, on the holdout) is decided by eval_decide.py against the recorded baseline.

**Suggestion:** probe: the first dev-split run of the styles against the baseline (task T-04 and the first Implement task of N-2.3); the holdout decides in Verify. If the criterion looks unreachable on the pinned model the agent stops and reports (agent-app rule).

### 1. FR-9

- Text: The MIA system shall check a claim by code where a code check exists, use model judgement only for the claims the hard checks leave open, accept "unknown" as an answer, and let a failed hard check inform the judge; a claim with a number and no evidence shall get the verdict unclear without a model call (amendment 4).
- Criterion: AC-2: on the holdout the chosen gate passes fewer wrong claims than the single voice and loses no more true claims among those with evidence (agent-app decision rule); repeated runs give the same verdicts (REQ-VER-005, REQ-VER-006)
- Verified by: Test, Measurement
- Flagged because: decided by a measurement, depends on the model, a GPU or a phone
- Decision: field
- Basis: hard to check outside field tests

### 2. REQ-BE-049

- Text: The Backend shall run the chosen judgement style so that on the holdout it passes fewer wrong claims than the single voice and loses no more true claims among those with evidence.
- Criterion: AC-2: decided with the rule of the agent-app workflow against the baseline
- Verified by: Measurement
- Flagged because: decided by a measurement, depends on the model, a GPU or a phone
- Decision: field
- Basis: hard to check outside field tests

### 3. REQ-WFM-014

- Text: The Workflow management shall deliver the example workflow verify so that on the holdout it passes fewer wrong claims than the single voice and loses no more true claims among those with evidence.
- Criterion: AC-2: decided with the rule of the agent-app workflow against the baseline
- Verified by: Measurement
- Flagged because: decided by a measurement, depends on the model, a GPU or a phone
- Decision: field
- Basis: hard to check outside field tests also should used at small scale

---

## Stable verdicts

**Facts found:** A limit of 0.90 as the lower bound of a 95 % interval needs enough repeats; the current stability is not measured in this plan.

**Suggestion:** probe: measure the stability of today's verify on the dev suite with 3 repeats before the first Implement task of N-2.3.

### 4. REQ-BE-050

- Text: When a verification is repeated on the same input and the same sources, the Backend shall give the same verdicts and the same set of facts.
- Criterion: AC-2: stability limit 0.90 (lower bound of the 95 % interval, at least) on the dev suites (REQ-VER-005, REQ-VER-006)
- Verified by: Measurement
- Flagged because: decided by a measurement, numeric bound in the criterion
- Decision: field
- Basis: hard to check outside field tests also should used at small scale

### 5. REQ-WFM-015

- Text: The Workflow management shall deliver the example workflows verify and lookup so that a repeated run on the same input and the same sources gives the same verdicts and the same set of facts.
- Criterion: AC-2: stability limit 0.90 (lower bound of the 95 % interval, at least) on the dev suites (REQ-VER-005, REQ-VER-006)
- Verified by: Measurement
- Flagged because: decided by a measurement, numeric bound in the criterion
- Decision: plausible
- Basis: 2 sigma is reasonable for this use case. 

---

## Lookup with sources

**Facts found:** The lookup exists today (suites research and web_checks). The criterion is a rate with a baseline (every answer has a source and a verbatim quote, or unknown).

**Suggestion:** probe: baseline run of today's lookup (T-04). The same baseline serves VAL-001 in the field.

### 6. FR-10

- Text: When a user asks a factual question, the MIA system shall answer with the sources and verbatim quotes that back it, or with "unknown" when nothing backs an answer.
- Criterion: AC-2, AC-23: every answer carries sources and verbatim quotes or the answer unknown; `/search` lists findings without composing an answer; a repeated lookup on the same sources gives the same facts
- Verified by: Test, Measurement
- Flagged because: decided by a measurement
- Decision: plausible
- Basis: It is the safe variant to avoid wrong judgement

### 7. REQ-BE-051

- Text: When a user asks a factual question, the Backend shall answer with the sources and verbatim quotes that back it, or with unknown when nothing backs an answer.
- Criterion: AC-2: every answer of the lookup suite carries a source and a quote or the verdict unknown
- Verified by: Test, Measurement
- Flagged because: decided by a measurement
- Decision: plausible
- Basis: There should be no more cases left

### 8. REQ-WFM-016

- Text: The Workflow management shall deliver the example workflow lookup as a library entry that answers a factual question with the sources and verbatim quotes that back it, or with unknown when nothing backs an answer.
- Criterion: AC-2: every answer of the lookup suite carries a source and a quote or the verdict unknown
- Verified by: Test, Measurement
- Flagged because: decided by a measurement
- Decision: plausible
- Basis: There should be no more cases left

---

## Review report (recall and precision)

**Facts found:** The suites research, research_compound and review_toy exist; the review is the largest model-dependent workflow and runs in time slices.

**Suggestion:** probe: baseline per tier from the existing research suites (recall and precision against the baseline). Alternatively `field` with an accepted risk, since the review is the second workflow (VAL-002).

### 9. FR-11

- Text: When a user gives a research question with a cut-off date and a budget, the MIA system shall produce a structured report of kept and dropped sources, findings per sub-question with verbatim anchors, conflicts and open gaps, and continue past an intermediate report only when the requesting user agrees.
- Criterion: AC-3: per tier source recall and precision against a baseline; 0 violations of the cut-off; 0 invented references; 100 % of quotes anchored
- Verified by: Measurement, Test
- Flagged because: decided by a measurement, numeric bound in the criterion, depends on the model, a GPU or a phone
- Decision: accept: criteria may be adjusted later if it is not working
- Basis: hard to check outside field tests also should used at small scale

### 10. REQ-BE-053

- Text: When a user gives a research question, a cut-off date and a budget, the Backend shall produce a report of kept and dropped sources with reasons, findings per sub-question with verbatim anchors, conflicts and open gaps.
- Criterion: AC-3: per tier source recall and precision against the baseline
- Verified by: Measurement
- Flagged because: decided by a measurement, depends on the model, a GPU or a phone
- Decision: accept: criteria may be adjusted later if it is not working
- Basis: hard to check outside field tests also should used at small scale also small scale us with little users

### 11. REQ-WFM-018

- Text: The Workflow management shall deliver the example workflow review as a library entry that produces a report of kept and dropped sources with reasons, findings per sub-question with verbatim anchors, conflicts and open gaps.
- Criterion: AC-3: per tier source recall and precision against the baseline
- Verified by: Measurement
- Flagged because: decided by a measurement, depends on the model, a GPU or a phone
- Decision: accept: criteria may be adjusted later if it is not working
- Basis: hard to check outside field tests also should used at small scale also small scale us with little users


---

## Method transfer

**Facts found:** The known method must be in the top 3 on the retro-discovery cases of the owner (AC-26); the cases exist, the rate on the pinned model is not measured.

**Suggestion:** risk or field: you decide whether method transfer is a first-release criterion. It is switched on only on request (`Where method transfer is switched on`).

### 12. FR-13

- Text: Where method transfer is switched on, the MIA system shall offer few ranked candidate methods from other fields, marked as hypotheses unless an executable test on a toy instance passed.
- Criterion: AC-26 (later, optional): the scout proposes the known method in its top 3 on the retro-discovery cases and marks a candidate verified only when an executable test passed
- Verified by: Measurement
- Flagged because: decided by a measurement
- Decision: accept: criteria may be adjusted later if it is not working
- Basis: hard to check outside field tests also should used at small scale also small scale us with little users


### 13. REQ-BE-057

- Text: Where method transfer is switched on, the Backend shall offer few ranked candidate methods marked as hypotheses unless an executable test on a toy instance passed.
- Criterion: AC-26: the known method is in the top 3 on the retro-discovery cases
- Verified by: Measurement
- Flagged because: decided by a measurement
- Decision: accept: criteria may be adjusted later if it is not working
- Basis: hard to check outside field tests also should used at small scale also small scale us with little users


### 14. REQ-WFM-022

- Text: Where method transfer is switched on, the Workflow management shall deliver the example workflow method_transfer as a library entry that offers few ranked candidate methods marked as hypotheses unless an executable test on a toy instance passed.
- Criterion: AC-26: the known method is in the top 3 on the retro-discovery cases
- Verified by: Measurement
- Flagged because: decided by a measurement
- Decision: accept: criteria may be adjusted later if it is not working
- Basis: hard to check outside field tests also should used at small scale also small scale us with little users


---

## Structured memory

**Facts found:** The criterion is relative: at least as good as today on the memory test set. The memory exists (extraction.py, content_store.py); a baseline report is eval/baselines/extraction-rules.md.

**Suggestion:** plausible: a relative criterion against a recorded baseline can only fail if the new storage loses information; the test set decides in Verify.

### 15. FR-14

- Text: The MIA system shall keep structured facts, preferences and commitments linked to their source, retrieve what is relevant within the token budget, let every user inspect, correct and delete any record, and never store a fact about a user that came from web or file text.
- Criterion: AC-24 (later): the memory test set is passed at least as well as today's summary-based dreaming at equal or lower token cost; every record shows its source and can be corrected and deleted by a user
- Verified by: Measurement, Test
- Flagged because: decided by a measurement
- Decision: plausible
- Basis: Not critical can adjusted later

### 16. REQ-BE-024

- Text: The Backend shall keep structured facts, preferences and commitments linked to their source and retrieve what is relevant within the token budget.
- Criterion: AC-24: the memory test set is passed at least as well as today's dreaming at equal or lower token cost
- Verified by: Measurement
- Flagged because: decided by a measurement
- Decision: plausible
- Basis: Not critical can adjusted later

### 17. REQ-CHA-011

- Text: The Chat agent shall keep structured facts, preferences and commitments linked to their source and retrieve what is relevant within the token budget.
- Criterion: AC-24: the memory test set is passed at least as well as today's dreaming at equal or lower token cost
- Verified by: Measurement
- Flagged because: decided by a measurement
- Decision: plausible
- Basis: Not critical can adjusted later

---

## Silent repair of behaviour violations

**Facts found:** behaviour.py and the suite behaviour exist; the criterion keeps the recorded precision and recall of the detectors.

**Suggestion:** plausible: a relative criterion against the recorded precision and recall (precedent in the code).

### 18. FR-15

- Text: If a behaviour rule is violated, then the MIA system shall repair the answer silently, record the violation as a signal and keep the correction out of the conversation memory.
- Criterion: AC-25: the speech-rule detectors keep their recorded precision and recall on the behaviour suite; a violation is repaired silently and never enters the memory as a scolding
- Verified by: Test, Measurement
- Flagged because: decided by a measurement
- Decision: plausible
- Basis: Not critical can adjusted later

### 19. REQ-BE-027

- Text: If a defined behaviour rule is violated, then the Backend shall repair the answer silently, record the violation as a signal and keep the correction out of the conversation memory.
- Criterion: AC-25: the detectors keep their recorded precision and recall on the behaviour suite
- Verified by: Test, Measurement
- Flagged because: decided by a measurement
- Decision: plausible
- Basis: Not critical can adjusted later

### 20. REQ-CHA-014

- Text: If a defined behaviour rule is violated, then the Chat agent shall repair the answer silently, record the violation as a signal and keep the correction out of the conversation memory.
- Criterion: AC-25: the detectors keep their recorded precision and recall on the behaviour suite
- Verified by: Test, Measurement
- Flagged because: decided by a measurement
- Decision: plausible
- Basis: Not critical can adjusted later

---

## Persona dialogues

**Facts found:** Decided as at least 84 of 100 dialogues (D-52); today's MIA is estimated at about 0.90 but not measured on the same 100 dialogues. If it comes out clearly below 0.90 you are asked again.

**Suggestion:** probe: the measurement of today's MIA on the 100 dialogues (task T-04, owner).

### 21. FR-25

- Text: The MIA system shall behave as the persona file specifies, using its names, pronouns and form of address, and use one shared persona file as the baseline for all users.
- Criterion: AC-8: check dialogues made from `calibration.txt` pass at a rate fixed in Plan against the recorded baseline, decided statistically; every user is addressed as master unless the file says otherwise
- Verified by: Measurement
- Flagged because: decided by a measurement, depends on the model, a GPU or a phone
- Decision: plausible
- Basis: Not critical can adjusted later. Only for personal use so hardware constraints are ok

### 22. REQ-BE-021

- Text: The Backend shall behave as the shared persona file specifies, with its names, pronouns and form of address, and address every user as master unless the file says otherwise.
- Criterion: AC-8: check dialogues pass at a rate fixed in Plan against the recorded baseline, decided statistically
- Verified by: Measurement
- Flagged because: decided by a measurement, depends on the model, a GPU or a phone
- Decision: plausible
- Basis: Not critical can adjusted later. Only for personal use so hardware constraints are ok

### 23. REQ-CHA-008

- Text: The Chat agent shall behave as the shared persona file specifies, with its names, pronouns and form of address, and address every user as master unless the file says otherwise.
- Criterion: AC-8: check dialogues pass at a rate fixed in Plan against the recorded baseline, decided statistically
- Verified by: Measurement
- Flagged because: decided by a measurement, depends on the model, a GPU or a phone
- Decision: plausible
- Basis: Not critical can adjusted later. Only for personal use so hardware constraints are ok

---

## Adaptation to negative votes

**Facts found:** The statistical test at 0.5 % has a calculated false alarm of 0.0135 and a miss of 0.0102 at a true rate of 2 % (finding F-1, scripts/false_alarm.py). The mechanism is a counter and a chance, no model.

**Suggestion:** plausible: calculated (the error rates are exact) and the mechanism is plain code.

### 24. FR-29

- Text: When a behaviour has received at least 5 net negative votes, the MIA system shall show it with a chance of at most 1 % per opportunity, and never apply this rule to facts or safety checks.
- Criterion: AC-11: after 5 net negative votes a test of 1000 opportunities shows the behaviour at most 10 times; a positive vote raises the rate again; votes on facts never change a fact
- Verified by: Test, Measurement
- Flagged because: decided by a measurement, numeric bound in the criterion
- Decision: field
- Basis: hard to tell without field test

### 25. REQ-BE-030

- Text: When a behaviour has received at least 5 net negative votes, the Backend shall show it with a chance of at most 1 % per opportunity and raise the chance again after positive votes.
- Criterion: AC-11: in 1000 opportunities after 5 net negative votes the behaviour appears at most 10 times
- Verified by: Test, Measurement
- Flagged because: decided by a measurement, numeric bound in the criterion
- Decision: field
- Basis: hard to tell without a field test

### 26. REQ-CHA-017

- Text: When a behaviour has received at least 5 net negative votes, the Chat agent shall show it with a chance of at most 1 % per opportunity and raise the chance again after positive votes.
- Criterion: AC-11: in 1000 opportunities after 5 net negative votes the behaviour appears at most 10 times
- Verified by: Test, Measurement
- Flagged because: decided by a measurement, numeric bound in the criterion
- Decision: field
- Basis: hard to tell without a field test

---

## Confidence by code, no invented source

**Facts found:** Two parts: the confidence figures are computed by code (deterministic), and the criterion `0 invented references and 100 % of cited quotes found` is measured on the suites (evidence.py exists).

**Suggestion:** plausible for the code part; the measured part is covered by the lookup and verify baselines above. One decision for both is fine.

### 27. NFR-4

- Text: The MIA system shall compute confidence figures by code from anchored evidence, show no source she did not retrieve, and report the limits with every result.
- Criterion: AC-3: 0 invented references and 100 % of cited quotes found in their source; confidence figures computed by code
- Quality line: reliability measure: invented references; cited quotes not found in their source; target: 0; 0 (100 % found); context: lookup and review results
- Verified by: Test, Measurement
- Flagged because: decided by a measurement, quality requirement with a target, numeric bound in the criterion
- Decision: plausible
- Basis: should be precise.

---

## Baselines and benchmark suites

**Facts found:** eval/suites has 10 suites and eval/baselines has 9 reports, but the baselines are `.md` reports; the form `eval/baselines/<suite>__<variant>__baseline.jsonl` that eval_decide.py reads is not there yet. Review has no suite named after the workflow.

**Suggestion:** probe: record the baselines in the .jsonl form (a task of N-4.1, owner for the labels); plausible after that.

### 28. REQ-EVL-005

- Text: The Evaluation shall keep a recorded baseline for every shipped workflow.
- Criterion: AC-10: each shipped workflow has a baseline file
- Verified by: Inspection
- Flagged because: depends on the model, a GPU or a phone
- Decision: plausible
- Basis: there should be a starting point and improve over time

### 29. REQ-OPS-005

- Text: The Evaluation and operation node shall keep a recorded baseline for every shipped workflow.
- Criterion: AC-10: each shipped workflow has a baseline file
- Verified by: Inspection
- Flagged because: depends on the model, a GPU or a phone
- Decision: plausible
- Basis: there should be a starting point and improve over time


### 30. REQ-EVL-009

- Text: The Evaluation shall hold the suites, baselines and eval criteria of the example workflows lookup, verify and review as the benchmark that decides their criteria.
- Criterion: AC-2, AC-3: each example workflow has a suite with a holdout and a recorded baseline; the criteria are decided with the rule of the agent-app workflow
- Verified by: Inspection, Measurement
- Flagged because: decided by a measurement, depends on the model, a GPU or a phone
- Decision: plausible
- Basis: there should be a starting point and improve over time. PErsonal use so hardware is known


### 31. REQ-OPS-019

- Text: The Evaluation and operation node shall hold the suites, baselines and eval criteria of the example workflows lookup, verify and review as the benchmark that decides their criteria.
- Criterion: AC-2, AC-3: each example workflow has a suite with a holdout and a recorded baseline; the criteria are decided with the rule of the agent-app workflow
- Verified by: Inspection, Measurement
- Flagged because: decided by a measurement, depends on the model, a GPU or a phone
- Decision: plausible
- Basis: there should be a starting point and improve over time. PErsonal use so hardware is known

---

## Security and accounts

**Facts found:** Precedent in the code: sandbox.py, tls_proxy.py, source_trust.py, the web log, accounts over IF-101 with throttling (the 6th failed attempt in a minute is refused). Security is checked in Verify by tests and a review of the trust boundaries.

**Suggestion:** plausible, with the note that the security review of the Verify phase is the real check; a security item should not be rated by a proposal alone.

### 32. FR-21

- Text: The MIA system shall let only the owner create accounts, let every user log in with a local account and password, and attribute every action that changes shared data to the account.
- Criterion: AC-14: only the owner creates accounts; at most 5 failed logins per minute per account are accepted; passwords are stored only as salted slow hashes and never logged; a user changes their own password
- Quality line: security measure: failed logins accepted per minute and account; plain passwords stored; target: at most 5; none; context: trusted users, home network and tailnet
- Verified by: Test, Inspection
- Flagged because: quality requirement with a target, numeric bound in the criterion
- Decision: plausible
- Basis: there should be a starting point and improve over time. PErsonal use so hardware is known

### 33. NFR-3

- Text: The MIA system shall treat text from the web, papers, PDFs and users as data and never as instruction, and run model-written scripts and hostile documents only in an isolating sandbox, refusing the operation when no sandbox is present.
- Criterion: AC-6: with the sandbox removed script checks report unavailable and nothing runs; injected instructions in pages and papers change no verdict and start no tool
- Quality line: security measure: injected instructions that change a verdict or start a tool; target: 0; context: red-team cases, sandbox present and removed
- Verified by: Test
- Flagged because: quality requirement with a target
- Decision: plausible
- Basis: there should be a starting point and improve over time. PErsonal use so hardware is known

### 34. NFR-5

- Text: The MIA system shall keep conversations, memory, logs, accounts and models on the host, send only the text of a web or scholarly query and, if configured, an e-mail address off it, and load nothing from the internet into the page.
- Criterion: AC-5: a browser test records every request the page makes and finds none outside the host; the web log lists every query that left the machine; the login page says that nothing is private between users
- Quality line: security measure: requests that leave the host other than the text of a web or scholarly query; target: 0; context: browser sessions of the chat and the graph app
- Verified by: Test, Inspection
- Flagged because: quality requirement with a target
- Decision: plausible
- Basis: there should be a starting point and improve over time. PErsonal use so hardware is known

### 35. NFR-6

- Text: The MIA system shall be reachable from other devices only over HTTPS inside the home network or the tailnet, authenticate every request by an account, check origins and limit message rates per user.
- Criterion: AC-14: other devices reach MIA only over HTTPS inside the home network or the tailnet; every request needs a login; origins are checked; message rates are limited per user; passwords go over plain HTTP only to `localhost`
- Quality line: security measure: unauthenticated requests served; plain-HTTP passwords accepted from LAN addresses; target: 0; 0; context: home network and tailnet
- Verified by: Test, Inspection
- Flagged because: quality requirement with a target
- Decision: plausible
- Basis: there should be a starting point and improve over time. PErsonal use so hardware is known

---

## VRoid model mapping

**Facts found:** ui/character and the character pack exist; the unmapped presets and gestures of a second model are reported by IF-111 (contract test with the models A and B).

**Suggestion:** plausible: precedent in the code and the contract mock; the second model is a demonstration.

### 36. FR-24

- Text: When a user selects another VRoid model, the MIA system shall map the expressions and gestures defined for one model to the shape keys of the other or report them as missing.
- Criterion: AC-17: a second `.vrm` model loads and reports which presets and gestures it cannot map
- Quality line: compatibility measure: presets and gestures of a second .vrm model that are mapped or listed as missing; target: 100 % mapped or listed, none dropped silently; context: VRoid models
- Verified by: Demonstration, Test
- Flagged because: quality requirement with a target
- Decision: plausible
- Basis: Model should not deviate too much

---

## Assumption about the phones

**Facts found:** The 30 fps on any phone inside the network is measured on the phones you have at hand (HLS amendment 9). The requirement itself is postponed to the field (category `field`).

**Suggestion:** field: the same decision as for the frame-rate requirements.

### 37. ASM-N1-002

- Text: ASM-N1-002: the phone figure (30 fps on any phone inside the network) is measured on the phones the owner has at hand; no particular device is named (HLS amendment 9).
- Verified by: assumption
- Flagged because: assumption: checked in validation
- Decision: plausible
- Basis: personal use only small user group

