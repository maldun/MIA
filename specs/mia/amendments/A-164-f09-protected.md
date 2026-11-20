# A-164: plan documents of G-V2.CONVERT (F-09), for the owner

What is done on the branch `docs/f09-patches` (unprotected, committed): scenarios for TC-WFM-116 to 129 and TC-RUN-030 to 035 in the two `test-spec.md` files, and the five checks that had ids used twice (CONVERT's TC-WFM-130 to 134) renumbered in the tables to **TC-WFM-144 to 148** (PANEL keeps 130 to 134; 139 to 142 are G-V3's and 143 is reserved for F-05, so the drafts' proposal of 139 to 143 could not be used).

What is a **protected patch** for you: `specs/mia/amendments/A-164-f09-protected.patch` (checked with `git apply --check`), applied from the repository root with `git apply specs/mia/amendments/A-164-f09-protected.patch`:
- `tests/acceptance/test_skill_binding.py` and `tests/acceptance/test_pipeline_graph.py`: the markers TC-WFM-131 to 134 become 145 to 148 and TC-WFM-130 becomes 144 (docstring lines only, no code),
- `specs/mia/test-requirements.md`: TR-CONVERT-008 (component checks) and TR-MODEL-006 (stage checks) with their group rows.
Effect on `trace_check` (errors, main checkout today 598): test-spec edits alone 583, with the patch 559.

Not done, needs your decision:
- F-09(a): TR-CONVERT-006 says the fake model server passes the IF-103 contract suite; the replay helper is not a model server and the real half of the suite is skipped (6 of 12). Reword the TR or accept "in spirit".
- F-09(b): TR-CONVERT-001 to 008 and TR-MODEL-006 are Draft: set them after your review.
- F-09(c) rest: plausibility records for REQ-RUN-030 to 035 (`plausibility.yaml`, protected, your rating).
- F-09(e): TC-WFM-128 and `test_pipeline_graph.py` load `research.escalate@3`, the skill `research` runs `research.escalate@1`. Which one is right? Changing it moves a protected test; not touched.
