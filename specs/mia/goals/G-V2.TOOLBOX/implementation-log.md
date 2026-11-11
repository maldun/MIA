# Implementation log: G-V2.TOOLBOX

Line of work `goal/v2.toolbox`, supervised. Test runs here are feedback, not verification (Phase 4 verifies).

## T-01: Entries by ID, status fields, reason, newer versions
- Requirements: REQ-WFM-050, 051, 090, 092, 093. Files: `toolbox.py` (stub replaced).
- Tests reported green (own run, 2026-11-11): TC-WFM-050, 051, 090, 092, 093 in `tests/acceptance/test_toolbox.py`. TC-WFM-052 and 053 also pass as a side effect (status of the file dropped; code never run on import). The other 10 tests stay red until their tasks.
- Deviation (owner's answer, "minimal versions in T-01"): the T-01 tests call `export_transform`, `set_trust`, `set_lifecycle` and `run`, which the plan assigns to T-02 to T-04. T-01 has the plain happy path of these; the rules are left to their tasks: file check `invalid_file` (T-02), owner-only (T-03), evidence, retired, baseline, `offer` (T-04), shipped and `seed_shipped` (T-05). `run` runs the code text with `exec` only in `run`, and refuses untrusted transforms.
- Decision: the reason text for an imported transform is "It came from outside MIA and was not reviewed." (TC-WFM-090 fixes the two phrases, not the full sentence). `reason` is stored in the meta record on import and shown only while the transform is untrusted.
- Open for Phase 4: `import_transform` does `json.loads` and key access without a check until T-02; a bad file raises a plain exception today.

## T-02: Import and export of the exchange file
- Requirements: REQ-WFM-052, 053, 055. Files: `toolbox.py`, new unit test `tests/test_toolbox.py`.
- Tests reported green (own run, 2026-11-11): TC-WFM-052, 053, 055. T-01 tests still green; contract mock suite green. Full unit suite not re-run (last full run at T-01: 2202 OK).
- Finding (closes the open point of T-01): a malformed file raised a plain exception. Test first: `tests/test_toolbox.py` (not JSON, list, version 0, version `true`, `inputs` a text, empty id), then the schema check `EXCHANGE_SCHEMA` with `jsonschema` (already pinned); the first problem is the reason, nothing is stored.
- Deviation: TC-WFM-055 asserts `offer() == ["t.one"]`, so `offer` lists all IDs now; T-04 leaves retired ones out.
- Code text is still never compiled on import (TC-WFM-053 green).

## T-03: Only the owner trusts
- Requirement: REQ-WFM-054. File: `toolbox.py` (`set_trust`: `owner_only` for trusted by a non-owner; setting untrusted is open to every account).
- Test reported green (own run, 2026-11-11): TC-WFM-054; TC-WFM-050..053, 055, 090, 092, 093 still green. No new unit test: the acceptance test checks the refusal with its accepted twins (owner trusts, any account untrusts); no edge case beyond it.
- The refusal leaves the status as it was (checked in TC-WFM-054). The same rule for `allow_baseline` is REQ-WFM-095, T-04.
- Process note: in T-02 the unit test `tests/test_toolbox.py` was written together with the code, not seen red first; it covers the malformed-file cases, which the schema check handles.

## T-04: Lifecycle, retired, baseline
- Requirements: REQ-WFM-067, 068, 070, 091, 095. Files: `toolbox.py` (`set_lifecycle`, `offer`, `run`), `tests/test_toolbox.py`.
- Tests reported green (own run, 2026-11-11): TC-WFM-067, 068, 070, 091, 095; all earlier toolbox tests still green; contract mock suite green. Only TC-WFM-056 (two variants) and 094 stay red (T-05).
- Decisions: `set_lifecycle` writes lifecycle, evidence and the allowance in one `set_meta` call (one new version of the meta record); `allow_baseline=False` means "not given", it never clears an allowance. The allowance counts only while the transform is retired and only as baseline (REQ-WFM-091); a refused change leaves everything as it was (unit test `BaselineChecks`, the edge case beyond the acceptance tests).
- Library calls: the toolbox now uses `set_meta`, `get_meta`, `get_lifecycle` of IF-203 v1 (A-111) next to `set_trust`; `set_lifecycle` of the library is not used.
