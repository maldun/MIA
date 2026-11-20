# A-165 draft: deferred entry TD-89 (research.escalate version in TC-WFM-128)

Owner decision of 2026-11-20 (D-356). `specs/mia/deferred.md` is protected: the owner appends the block below after TD-88 with `bash tools/apply_deferred_td89.sh --do`. The Sign-off line is yours to tick: nothing is signed here.

---

## TD-89 – The converter check of research runs on research.escalate@3, the skill runs research.escalate@1 (DRAFT)
- Kind: defer
- Requirement: REQ-WFM-058, REQ-WFM-110 (check TC-WFM-128 and the protected test `tests/acceptance/test_pipeline_graph.py`, `test_research_escalate_keeps_its_calls_as_transforms_and_wraps_every_map_and_loop`, which load `research.escalate@3`; the skill `research`, version 3, names `pipeline: research.escalate@1`; finding F-09(e) of the Verify of G-V2.CONVERT, noted again in the Verify of G-V2)
- Interim criterion: the equivalence of the converted skill is decided on the pipeline that runs: TC-WFM-110 runs the skill through `Core.run` on the graph path, so the rate of `research` (0.95, 57 of 60 on the dev run of 2026-11-16, criterion 0.85) is measured on `research.escalate@1`; TC-WFM-128 checks only that the converter turns the version-3 pipeline into a valid graph with its maps, branch and loop
- Target: decide which version is the right one for the skill (move the skill to `@3`, or move the check to `@1`); then the check, its scenario and the protected test name the same version as the skill file and the acceptance record; if `@1` and `@3` differ in graph shape, a check on `@1` too
- Reason: the owner decided on 2026-11-20 (D-356) to leave it as it is and to take it up in the sub goal that improves the skills; changing it moves a protected test and may change what the skill does
- Effort: about 1 hour to compare the three pipeline versions and one protected patch, more if the skill moves to `@3` (it then needs a new acceptance run and record)
- Risk of the gap: a change that breaks the conversion of `research.escalate@1` only (its map or loop shape) is not caught by TC-WFM-128; the equivalence run TC-WFM-110 would show it as a worse rate
- Owner: Stefan Reiterer
- Trigger: the start of the sub goal "improve the skills", or the next edit of `library/pipelines/research.escalate/**` or of `skills/research.md`, whichever first
- Target check: specified only
- Decision: D-356, 2026-11-20
- Sign-off: pending
- Status: open
