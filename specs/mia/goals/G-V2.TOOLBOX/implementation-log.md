# Implementation log: G-V2.TOOLBOX

Line of work `goal/v2.toolbox`, supervised. Test runs here are feedback, not verification (Phase 4 verifies).

## T-01: Entries by ID, status fields, reason, newer versions
- Requirements: REQ-WFM-050, 051, 090, 092, 093. Files: `toolbox.py` (stub replaced).
- Tests reported green (own run, 2026-11-11): TC-WFM-050, 051, 090, 092, 093 in `tests/acceptance/test_toolbox.py`. TC-WFM-052 and 053 also pass as a side effect (status of the file dropped; code never run on import). The other 10 tests stay red until their tasks.
- Deviation (owner's answer, "minimal versions in T-01"): the T-01 tests call `export_transform`, `set_trust`, `set_lifecycle` and `run`, which the plan assigns to T-02 to T-04. T-01 has the plain happy path of these; the rules are left to their tasks: file check `invalid_file` (T-02), owner-only (T-03), evidence, retired, baseline, `offer` (T-04), shipped and `seed_shipped` (T-05). `run` runs the code text with `exec` only in `run`, and refuses untrusted transforms.
- Decision: the reason text for an imported transform is "It came from outside MIA and was not reviewed." (TC-WFM-090 fixes the two phrases, not the full sentence). `reason` is stored in the meta record on import and shown only while the transform is untrusted.
- Open for Phase 4: `import_transform` does `json.loads` and key access without a check until T-02; a bad file raises a plain exception today.
