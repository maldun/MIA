# A-157 – REQ-WFM-137 says what is stored for the report (approved 2026-11-17, Verify finding V-4)

Decision: owner by questionnaire, 2026-11-17 (D-342): reword the requirement and add a report case to TC-WFM-137.

- REQ-WFM-137 (Draft since A-154): "The Workflow management shall store the texts of a run (result, material, answers, reason) unchanged as text, and the run report as text with its state line on top and the text of the skill unchanged below it, and never execute or interpret any of them." The first wording of A-154 said `unchanged` for the whole report, but the runtime puts the state line on top (REQ-WFM-139).
- `architecture.sysml` and the history line of the requirement follow; the scenario of TC-WFM-137 in `test-spec.md` has the report case.
- Protected: the check itself, `test_a_report_with_hostile_text_is_stored_as_text_below_the_state_line` in `tests/acceptance/test_skill_run_report.py` (6 tests, all OK in the sandbox; the case describes behavior that exists, so it is green at once). To install (owner):
```
git apply specs/mia/goals/G-V3.REPORT/amendment-a157/protected.patch
git add tests/acceptance/test_skill_run_report.py
git commit -m "test: A-157 TC-WFM-137 report case (the report is stored as text below the state line)"
```

## Renumbered (2026-11-17)
This amendment was first called A-156. The G-V3.CHAT session used A-156 for "a skill run speaks once" (FB-09, `specs/mia/amendments/A-156-draft-skill-run-speaks-once.md`) at the same time, so this one is **A-157**. The check was installed on master as commit `69d8a76a` ("test: A-156 TC-WFM-137 report case ...") and its docstring in `tests/acceptance/test_skill_run_report.py` still says A-156; `docstring-rename.patch` in this folder changes that one word (protected file: the owner installs it; the commit message cannot be changed once pushed and stays as it is). `protected.patch` is the record of what was installed and is not applied again.
