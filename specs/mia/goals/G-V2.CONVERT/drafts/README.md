# Drafts of G-V2.CONVERT (2026-11-16): nothing here is applied

| File | For | Who applies it |
|---|---|---|
| `architecture-regenerated.patch` | `specs/mia/architecture.sysml`: the node-requirement block regenerated with `python3 -I tools/gen_node_requirements_model.py .` (REQ-RUN-030 to 035 added; REQ-CHA-064 to 066 and the old 82 % texts of REQ-WFM-110 and 113 brought up to date). Both model checks pass on the result. | `git apply specs/mia/goals/G-V2.CONVERT/drafts/architecture-regenerated.patch`, or run the generator again (same result) |
| `test-spec-scenarios-draft.md` | scenarios for TC-WFM-116 to 129, the five checks with a double id (proposed TC-WFM-139 to 143), TC-RUN-030 to 035 | the owner, after the decision on the double ids |
| `test-requirements-draft.md` | TR-CONVERT-008 and TR-MODEL-006 (protected file) | the owner |

After applying: `trace_check.py` should lose the 76 new errors named in the pre-merge report (the missing scenarios, test requirements and model entries).
