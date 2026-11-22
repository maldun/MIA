# Test requirements: G-V4.GRAPHAPI.RULES

**Test spec:** `test-spec.md`   **Status:** Draft (for the owner's review, Plan step 3)

<!-- Requirements on the checks, apart from the product requirements: under which conditions a measurement counts. Setup kind: the verdict depends on the setup; written out and reviewed in detail. Unit kind: exact expected values; grouped and signed off as a group. -->

## Groups
| Order | Group | What it covers | Test requirements |
|---|---|---|---|
| 1 | EX | Exact values: expected rule names, IDs, orders and counts, signed off as a group | TR-RULES-001 |
| 2 | DA | Data: the graphs, the corpus and the skills the checks run on | TR-RULES-002, TR-RULES-003, TR-RULES-004 |
| 3 | EP | Entry points and stand-ins: how the run, the save and the check route are driven, and what the mock proves | TR-RULES-005, TR-RULES-006, TR-RULES-007 |
| 4 | CR | Ability to fail and protected material: the checks can fail, the older suites are untouched | TR-RULES-008, TR-RULES-009 |

### TR-RULES-001 – Exact values
- Applies to: TC-GTB-037, TC-GTB-038, TC-GTB-039, TC-GTB-040, TC-GTB-041, TC-GTB-042, TC-GTB-043, TC-GTB-044, TC-WFM-179, TC-WFM-180, TC-WFM-181, TC-WFM-182, TC-WFM-183, TC-WFM-184, TC-RUN-037, TC-RUN-038, TC-RUN-039, TC-IF-301-27, TC-IF-301-28, TC-IF-301-29, TC-IF-301-30, TC-IF-301-31, TC-IF-301-32, TC-IF-301-33, TC-IF-301-34
- Requirement: REQ-GTB-037
- Group: EX
- Kind: unit
- Text: The expected values of these checks shall be written as exact values: rule names, parts in their order, sentences, statuses and counts, with no tolerance and no check by "contains".
- Rationale: every outcome is a name, an ID, an order or an equality (test spec, limit column); OC-1 is about the same order, so a check that ignores the order or allows extra items would hide the defect it is for.
- Credibility aspect: reference accuracy
- Verified by: known answer
- Sign-off: skimmed as a group
- Status: Draft

### TR-RULES-002 – Small graphs written out in the check
- Applies to: TC-GTB-038, TC-GTB-039, TC-GTB-040, TC-GTB-041, TC-GTB-042, TC-GTB-043, TC-GTB-046, TC-WFM-179, TC-WFM-180, TC-WFM-181, TC-WFM-183, TC-WFM-184, TC-RUN-036, TC-RUN-037, TC-RUN-038, TC-RUN-039
- Requirement: REQ-GTB-041
- Group: DA
- Kind: setup
- Text: Each graph of these checks shall be written out in the check itself with at most eight steps, and each broken graph shall have a sound twin that differs in one place and gives no item.
- Rationale: a reader sees at a glance which rule a graph breaks; the twin shows that the item comes from the one difference and not from something else in the graph (the prototype's rule 1 once refused a slash for no reason, finding 5).
- Credibility aspect: validity domain
- Verified by: inspection
- Status: Draft

### TR-RULES-003 – The corpus of the old refusals
- Applies to: TC-GTB-047
- Requirement: HR-005
- Group: DA
- Kind: setup
- Text: The check shall use every case of TC-GTB-002 and the generator of TC-GTB-003 with the seeds 1 to 1000 as they are at `goal/v4`, turn each document into the stored form with `from_document`, and fail on the first graph refused by the five older rules and accepted by the eight.
- Rationale: HR-005 fixes this corpus; the seed range is fixed in Plan and never changed to make the check pass; the one known exception (`max_seconds: 1.0`, valid under REQ-WFM-048) is named in the check, not filtered by a broad rule; the counts of newly refused graphs are printed for the record (prototype: 57, 42 and 15), not asserted, so a better rule does not fail the check.
- Credibility aspect: validity domain
- Verified by: known answer (the prototype's counts of `cp17_check.py`)
- Status: Draft

### TR-RULES-004 – The converted skills
- Applies to: TC-RUN-040, TC-GTB-043, TC-GTB-044, TC-RUN-037, TC-IF-301-28, TC-IF-301-33, SMOKE-RULES-001
- Requirement: HR-006
- Group: DA
- Kind: setup
- Text: The converted skill graphs shall be built at test time from `skills/*.md` and `library/` with `pipeline_graph.convert` and `bind_skill`, as the prototype's `converted()` does, and the check shall fail when fewer than 15 graphs are built.
- Rationale: DEP-2; built, not copied, so a change of a skill shows up in the check; the count guards against a silent loss of skills (a check over zero graphs passes); `chat` is the converted `chat` skill named in AC-018.
- Credibility aspect: reference accuracy
- Verified by: known answer (15 skills on 2026-11-22)
- Status: Draft

### TR-RULES-005 – No step ran, shown by markers that can fire
- Applies to: TC-RUN-036, TC-RUN-039, SMOKE-RULES-001
- Requirement: REQ-RUN-036
- Group: EP
- Kind: setup
- Text: "No step ran" shall be shown by a marker function per step that counts its calls, and in the same check a sound twin shall call each of its markers once.
- Rationale: a count of zero proves nothing if the markers cannot be called; the twin shows they can (as TC-RUN-017 shows the marker side effect).
- Credibility aspect: power and false-alarm rate
- Verified by: mutation (a runner that runs the first step before asking the run check must fail TC-RUN-036)
- Status: Draft

### TR-RULES-006 – Every entry point, five times
- Applies to: TC-GTB-046
- Requirement: HR-004
- Group: EP
- Kind: setup
- Text: The check shall send each graph through the rule report, the save on a fresh files store, the check route and the run, five times each in one process, and compare the items with the rule report item by item: rule, parts in order and sentence.
- Rationale: HR-004 fixes four entry points and five repeats; "kept" in HR-004 is the save of a working copy, the same call as the save (the page is a stand-in, D-416 (2)); a fresh store per save, so an earlier refusal cannot change a later one.
- Credibility aspect: validity domain
- Verified by: inspection
- Status: Draft

### TR-RULES-007 – What the stand-ins prove
- Applies to: TC-GTB-046, TC-IF-301-27, TC-IF-301-28, TC-IF-301-29, TC-IF-301-30, TC-IF-301-31, TC-IF-301-32, TC-IF-301-33, TC-IF-301-34
- Requirement: REQ-GTB-033
- Group: EP
- Kind: setup
- Text: The IF-301 v4 mock shall pass the same contract cases as the real module, and the check-route half of TC-GTB-046 shall count only as a wiring check until IF-104 v2 is real.
- Rationale: the consumers (save, runner, later EDIT and CONTEXT) test against the mock, so it must agree with the real side on every golden example; the IF-104 v2 mock answers with the rule report, so TC-GTB-046 shows the route passes the kind and the report through, not that a real route does (D-416 (2)); the real route is checked when IF-104 v2 is written or in EDIT.
- Credibility aspect: stand-in fidelity
- Verified by: contract suite on both sides
- Status: Draft

### TR-RULES-008 – Each check is shown able to fail
- Applies to: TC-GTB-037, TC-GTB-039, TC-GTB-042, TC-GTB-043, TC-GTB-046, TC-WFM-179, TC-WFM-180, TC-RUN-036, TC-RUN-037, TC-RUN-038, TC-RUN-039
- Requirement: REQ-GTB-034
- Group: CR
- Kind: setup
- Text: Each of these checks shall be shown able to fail by running it once against a deliberate defect of the unit it checks, before the check is trusted.
- Rationale: the code is adapted from the validated prototype, so a test written against it tends to confirm it; the defects: two rules swapped in the registry, the first broken rule only, the cycle asked while rule 3 is broken, the save path on `check_graph`, repeats removed from a refused run (seen on the scratch run of 2026-11-22), trust checked before the run check, prepare inputs not counted as given.
- Credibility aspect: reviewer independence
- Verified by: mutation
- Status: Draft

### TR-RULES-009 – The older suites stay untouched
- Applies to: TC-GTB-045
- Requirement: REQ-GTB-052
- Group: CR
- Kind: setup
- Text: The check shall run the contract suites of IF-301 v1 to v3, IF-102, IF-104 v1 and IF-203 from files that `git diff goal/v4` shows unchanged, and shall fail if any of those files differs.
- Rationale: Q-6 keeps the document form as it is; a suite that was edited to pass would hide a change of it; the protected suites change only through an amendment, and none is planned in RULES.
- Credibility aspect: reference accuracy
- Verified by: inspection (git diff)
- Status: Draft
