# Test requirements: G-V4.VIEW

**Test spec:** `test-spec.md` (scenarios approved, D-441)   **Status:** Draft (agent, 2026-11-22), for the owner's review one check at a time (unit kind by group)

<!-- Requirements on the checks, apart from the product requirements: under which conditions a verdict counts. Setup kind: the verdict depends on the setup; written out and reviewed in detail. Unit kind: exact expected values; grouped and signed off as a group. The repository has no shared test-requirement catalog (M43), so no item has a Source line. -->

## Groups
| Order | Group | What it covers | Test requirements |
|---|---|---|---|
| 1 | SD | Stores and data: the stores, the fixture graphs, the accounts the checks run on | TR-VIEW-001, TR-VIEW-002, TR-VIEW-003 |
| 2 | SI | Stand-ins: what the mocks, the fake DOM and the fault wrappers prove | TR-VIEW-004, TR-VIEW-005, TR-VIEW-006, TR-VIEW-007 |
| 3 | BR | Browser: Firefox, the test server, "settled", the request record, keyboard, colours | TR-VIEW-008, TR-VIEW-009, TR-VIEW-010, TR-VIEW-011, TR-VIEW-012, TR-VIEW-013 |
| 4 | DP | Dependencies on other goals and on installed material | TR-VIEW-014, TR-VIEW-015 |
| 5 | SM | Smoke checks on the owner's host | TR-VIEW-016, TR-VIEW-017 |
| 6 | EX | Exact values, signed off as a group | TR-VIEW-018, TR-VIEW-019, TR-VIEW-020 |
| 7 | CR | Ability to fail | TR-VIEW-021 |

### TR-VIEW-001 – Both stores, skips visible
- Applies to: TC-IF-104-17, TC-IF-104-18, TC-IF-104-19, TC-IF-104-20, TC-IF-104-21, TC-IF-104-22, TC-IF-104-23, TC-IF-104-24, TC-IF-104-25, TC-IF-104-26, TC-IF-104-27, TC-API-021
- Requirement: REQ-API-018
- Group: SD
- Kind: setup
- Text: The check shall run on a new file store in a temporary folder and on a throw-away PostgreSQL 16 database started by the test (`core_stores`, image `postgres:16` local, never pulled), and shall report a variant that cannot run as skipped with its reason, never as passed.
- Rationale: REQ-API-018 asks for the same answers on both stores; the PostgreSQL variant needs podman, the image and psycopg 3, which the venv `mia312` has and the system Python has not (CLAUDE.md); a hidden skip would read as success (as TR-CORE-003).
- Credibility aspect: measurement conditions
- Verified by: inspection of the test report (each case listed three times: mock, files, postgres)
- Status: Draft

### TR-VIEW-002 – The fixture graphs
- Applies to: TC-API-018, TC-API-020, TC-GA-017, TC-GA-018, TC-GA-019, TC-GA-020, TC-GA-021, TC-GA-022, TC-GA-023, TC-GA-024, TC-GA-025, TC-GA-026, TC-GA-027, TC-GA-028, TC-GA-029, TC-GA-030, TC-GA-033, TC-GA-034, TC-GA-035, TC-GA-036, TC-GA-037, TC-GA-038, TC-GA-039, SMOKE-VIEW-002
- Requirement: REQ-GA-019
- Group: SD
- Kind: setup
- Text: The checks shall take their graphs from `tests/fixtures/graph_view/`, made by the prototype's `make_sample_store.py` (R11, `prototype/g-v4`) and kept unchanged: cp2.multi (versions 1 to 4 by anna, ben, anna, ben, version n naming the tool tn, 3 steps, 2 connections), sample.code (7 steps, 6 connections, the hostile step), sample.broken (e2 to the missing var.gone), plus four added graphs: a context graph `ctx.small` (steps of types `concept` and `source`), a graph `swarm.one` of kind `swarm` with one untrusted step, a graph `chat` whose description is "Chat with the owner", and a chain `chain.fifty` of 50 steps and 49 connections; the JS checks read the same graphs as JSON.
- Rationale: the scenarios name these graphs and their counts; one source for the Python, the JS and the browser checks keeps their answers comparable, and the counts are the expected values of TC-GA-017 and TC-GA-022; the four added graphs are the cases R11 lacks (REQ-GA-020, 028, SMOKE-VIEW-002).
- Credibility aspect: reference accuracy
- Verified by: inspection of the fixture list against this text (IDs, versions, authors, counts)
- Status: Draft

### TR-VIEW-003 – Fresh stores and accounts
- Applies to: TC-API-018, TC-API-019, TC-API-020, TC-API-021, TC-API-022, TC-API-023, TC-API-024, TC-API-025, TC-GA-033, TC-GA-034, TC-GA-035, TC-GA-036, TC-GA-037, TC-GA-038, TC-GA-039
- Requirement: REQ-API-046
- Group: SD
- Kind: setup
- Text: Each check shall start on a store and an accounts store that no other check has written to, with `anna` made first (the owner) and `ben` made second, each with its own password; the Firefox checks log in as anna through `/api/login` once per check.
- Rationale: the owner is the first account (`accounts.owner_check`), so the order of making decides who may write; a store shared between checks would let an earlier save change a later count; one login per check is the case of NFR-12 ("one login is enough").
- Credibility aspect: measurement conditions
- Verified by: review of the test setup
- Status: Draft

### TR-VIEW-004 – What the JS mock proves
- Applies to: TC-GA-017, TC-GA-018, TC-GA-019, TC-GA-020, TC-GA-021, TC-GA-022, TC-GA-023, TC-GA-024, TC-GA-025, TC-GA-026, TC-GA-027, TC-GA-028, TC-GA-029, TC-GA-030
- Requirement: REQ-GA-019
- Group: SI
- Kind: setup
- Text: The node checks shall use the protected JS mock of IF-104 v2 only through its routes (no reach into its fields except `seed` and `unreachable`), shall count only while the JS contract suite passes on that mock, and shall use no value the mock and the real provider are known to treat differently (a place with a half, a rule other than `step_identity`, `connection_endpoints`, `cycle`, an exact time).
- Rationale: the node checks prove the page's logic over the answers the contract fixes; the mock's fidelity limits (its header: three rules, no record checks, a fixed toolbox, half-up rounding, a counter for time) must not decide a verdict; that the page works with the real provider is shown by the Firefox checks (D-440 (2)).
- Credibility aspect: stand-in fidelity
- Verified by: inspection of the node checks against the mock's fidelity list; the JS contract suite in the same run
- Status: Draft

### TR-VIEW-005 – What the fake DOM proves
- Applies to: TC-GA-017, TC-GA-019, TC-GA-020, TC-GA-021, TC-GA-022, TC-GA-023, TC-GA-024, TC-GA-025, TC-GA-026, TC-GA-027, TC-GA-028, TC-GA-029, TC-GA-030
- Requirement: REQ-GA-024
- Group: SI
- Kind: setup
- Text: The node checks shall assert on text, attributes and elements of the fake DOM (`tests/js/fake-dom.mjs`) and on the nodes, connections and options the page hands to the drawing library, never on places in pixels, sizes or colours; claims about pixels, colours, focus and requests are made only by the Firefox checks.
- Rationale: the fake DOM has no layout, no styles and no drawing; a node check that read a place would test the fake, not the page; vis-network draws what it is handed, so the handed data is the page's part of REQ-GA-024 to 027.
- Credibility aspect: stand-in fidelity
- Verified by: review of the node checks
- Status: Draft

### TR-VIEW-006 – Fault wrappers are shown to fire
- Applies to: TC-IF-104-26, TC-API-021, TC-API-023, TC-GA-020
- Requirement: REQ-API-040
- Group: SI
- Kind: setup
- Text: Each fault stand-in shall be shown to fire in the same check before its verdict counts: the unreachable store (every backend call raises `ConnectionError`), the failing record table (only writes to `graph_changes` raise; a write to `graphs` succeeds in the same save), the record the store refuses (a step of type `no_such_type` refused by IF-301 `check_record` with `unknown_type`), the unreachable JS mock.
- Rationale: a wrapper that never fires makes a refusal check pass for the wrong reason; TC-API-023 needs the version write to succeed and only the record write to fail, else it shows a refused save, not a version without its record.
- Credibility aspect: stand-in fidelity
- Verified by: an assertion in each check that the fault was raised at least once (a call counter of the wrapper)
- Status: Draft

### TR-VIEW-007 – The store setting is read as in production
- Applies to: TC-API-018, TC-API-019, SMOKE-VIEW-001
- Requirement: REQ-API-019
- Group: SI
- Kind: setup
- Text: The checks shall give the store setting the way the product reads it (D-440 (4)): the configuration key `store` (`files`, `database`, absent, or the wrong values `postgress`, `""`, `5`) and the address from `MIA_DATABASE_URL`, set in a copy of the configuration and an environment of the test; they shall not call the store choice with prepared objects.
- Rationale: REQ-API-019 and 020 are about the configuration as the owner writes it; a check that hands in a backend object would skip the part that can go wrong (the key, the default folder, the message).
- Credibility aspect: validity domain
- Verified by: review of the test setup
- Status: Draft

### TR-VIEW-008 – Firefox as the reference browser
- Applies to: TC-GA-033, TC-GA-034, TC-GA-035, TC-GA-036, TC-GA-037, TC-GA-038, TC-GA-039, SMOKE-VIEW-002
- Requirement: REQ-GA-012
- Group: BR
- Kind: setup
- Text: The checks shall drive the Firefox build installed by Playwright for Python at the version pinned in `requirements-browser.txt` (a release at least two weeks old at install, DEP-5, DEP-6), headless, viewport 1280 × 800 at device scale factor 1, locale `en-US`, colour scheme `light` unless the check sets `dark`, a new browser context per check, and a step timeout of 10 s; where Playwright or its Firefox is missing the checks skip with that reason, never pass.
- Rationale: the owner's choice of browser and size (D-430, REQ-GA-012 "1280 × 800"); one pinned build keeps pixel places and colours comparable between runs (REQ-GA-031); a new context per check has no storage, cookies or cache of an earlier check.
- Credibility aspect: measurement conditions
- Verified by: inspection of the test report (browser name and version printed once per run)
- Status: Draft

### TR-VIEW-009 – One origin with the real provider
- Applies to: TC-GA-033, TC-GA-034, TC-GA-035, TC-GA-036, TC-GA-037, TC-GA-038, TC-GA-039
- Requirement: REQ-GA-042
- Group: BR
- Kind: setup
- Text: The Firefox checks shall run against one local test server on `127.0.0.1` at a free port that serves `graph_app/` at `/graph/` and the real provider `graph_api_v2.create_app` with the account routes at `/api/`, on a throw-away file store seeded per TR-VIEW-002, with that origin as the only allowed origin.
- Rationale: D-440 (2); in production Caddy gives page and API one origin (DEP-9), and the session cookie and the "nothing from outside" check depend on it; the real provider removes the mock's fidelity limits from the browser verdicts.
- Credibility aspect: validity domain
- Verified by: inspection of the server helper
- Status: Draft

### TR-VIEW-010 – When the picture counts as settled
- Applies to: TC-GA-036, TC-GA-037, SMOKE-VIEW-002
- Requirement: REQ-GA-031
- Group: BR
- Kind: setup
- Text: A picture shall count as settled when the drawing library has reported that it stabilised (or physics is off), and the places shall then be read through the read-only test hook the page offers (named in `plan.md`) and rounded to whole pixels; a picture not settled within 10 s fails the check.
- Rationale: places read during the movement differ from run to run and would make REQ-GA-031 flaky or meaningless; rounding to whole pixels is the tolerance of the scenario; a bound on the wait keeps a never-settling picture from hanging the run.
- Credibility aspect: numerical settings
- Verified by: review; the check prints the time to settle
- Status: Draft

### TR-VIEW-011 – Every request is recorded
- Applies to: TC-GA-037, TC-GA-039
- Requirement: REQ-GA-043
- Group: BR
- Kind: setup
- Text: The checks shall record every request the page makes from the first navigation to the end of the check, through the browser's own request events (documents, scripts, styles, fonts, images, fetches and web sockets), with method and full address, and shall fail on any request to another origin or any request to `/api/v2` other than GET.
- Rationale: a record taken only from the page's own fetch calls would miss a font or script from outside (NFR-13) and a write sent by the drawing library; the browser's events see everything that leaves the page.
- Credibility aspect: measurement conditions
- Verified by: a planted request to `https://example.invalid/x.css` in a copy of the page fails TC-GA-039 (see TR-VIEW-021)
- Status: Draft

### TR-VIEW-012 – Keyboard only
- Applies to: TC-GA-038
- Requirement: REQ-GA-041
- Group: BR
- Kind: setup
- Text: The check shall use key presses only (Tab, Shift+Tab, arrow keys, Enter, Space, Escape) and no mouse or touch call, and shall assert after each step which element has the focus.
- Rationale: one mouse click hidden in the setup would let a page that cannot be reached by keyboard pass; asserting the focus shows each step was reached, not only the end state.
- Credibility aspect: validity domain
- Verified by: review of the check
- Status: Draft

### TR-VIEW-013 – Colours compared with the browser's token values
- Applies to: TC-GA-034
- Requirement: REQ-GA-016
- Group: BR
- Kind: setup
- Text: The check shall take the expected colours from the browser itself, as the computed value of a probe element styled with the token variable in the same page and theme, and compare them with the computed colour of the page background and a step label, as RGB values equal to the last digit.
- Rationale: hard-coded hex values in the test would copy the tokens and break with any change of `tokens.css`; the browser's own resolution of the variable is the reference the requirement means ("equal the token values of that theme").
- Credibility aspect: reference accuracy
- Verified by: the two themes give different values in the same run (the check can fail)
- Status: Draft

### TR-VIEW-014 – Checks that wait for RULES
- Applies to: TC-API-025, TC-IF-104-22, TC-IF-104-23
- Requirement: REQ-API-035
- Group: DP
- Kind: setup
- Text: TC-API-025 shall count only on code that holds IF-301 v4 (`graph_rule_set`, G-V4.GRAPHAPI.RULES merged into `goal/v4` and from there into this branch); until then it fails naming RULES; the real side of TC-IF-104-22 and 23 counts for the rule names only as far as CORE's rules name them.
- Rationale: REQ-API-031 and 035 ask for the IF-301 v4 rule report, which only RULES provides (handover, section 4); a pass on CORE's rules would not show HR-008.
- Credibility aspect: validity domain
- Verified by: inspection of the branch state in the verification report
- Status: Draft

### TR-VIEW-015 – Installed contract suites unchanged
- Applies to: TC-IF-104-17, TC-IF-104-18, TC-IF-104-19, TC-IF-104-20, TC-IF-104-21, TC-IF-104-22, TC-IF-104-23, TC-IF-104-24, TC-IF-104-25, TC-IF-104-26, TC-IF-104-27, TC-IF-302-13, TC-IF-302-14, TC-API-020
- Requirement: REQ-API-030
- Group: DP
- Kind: setup
- Text: The contract cases shall count only when run from suite files byte-identical to those installed by A-171, A-172 and A-174, and the IF-104 v1 suites (Python and JS) byte-identical to `goal/v4`, with the mock and the real variants all passing.
- Rationale: the suites are the frozen interface shared with EDIT, REPLAY and CONTEXT (D-368, D-425 A); REQ-API-030 keeps v1 unchanged beside v2.
- Credibility aspect: reviewer independence
- Verified by: `git diff --stat` of the suite files against the installing commits in the verification report
- Status: Draft

### TR-VIEW-016 – The image smoke check writes nothing
- Applies to: SMOKE-VIEW-001
- Requirement: REQ-OPR-011
- Group: SM
- Kind: setup
- Text: The smoke check shall build the release image from `deploy/` on the owner's host, start it with `store: database` and the owner's `MIA_DATABASE_URL` from `deploy/.env`, run only `import psycopg` in the container and `GET /api/v2/store` as the owner, and send no request that writes.
- Rationale: the check proves the image can open the owner's database (REQ-OPR-011); the live graphs are not test data (as TR-CORE-009).
- Credibility aspect: measurement conditions
- Verified by: inspection of the smoke script
- Status: Draft

### TR-VIEW-017 – The opening time is measured, not judged
- Applies to: SMOKE-VIEW-002
- Requirement: REQ-GA-031
- Group: SM
- Kind: setup
- Text: The measurement shall run on the owner's host with the installed release's graph app and API against a throw-away file store holding `chain.fifty` (TR-VIEW-002), in Firefox per TR-VIEW-008, five openings with a reload between them after one warm-up opening not counted, each timed from the choice in the list to "settled" (TR-VIEW-010), and report the median and the smallest and largest time in milliseconds without a pass or fail.
- Rationale: NFR-11 has no hard bound (D-425 E-H); the number is for the owner to read with VAL-VIEW-01; a warm-up keeps the first load of the vendored library out of the figure; the live store is not written.
- Credibility aspect: repetitions and seeds
- Verified by: the deployment record holds the five times, the median and the range
- Status: Draft

### TR-VIEW-018 – Exact values
- Applies to: TC-API-018, TC-API-019, TC-API-020, TC-API-021, TC-API-022, TC-API-023, TC-API-024, TC-API-025, TC-OPR-011, TC-GA-017, TC-GA-018, TC-GA-019, TC-GA-020, TC-GA-021, TC-GA-022, TC-GA-023, TC-GA-024, TC-GA-025, TC-GA-026, TC-GA-027, TC-GA-028, TC-GA-029, TC-GA-030, TC-GA-031, TC-GA-033, TC-GA-035, TC-GA-038, TC-GA-039, TC-IF-104-17, TC-IF-104-18, TC-IF-104-19, TC-IF-104-20, TC-IF-104-21, TC-IF-104-22, TC-IF-104-23, TC-IF-104-24, TC-IF-104-25, TC-IF-104-26, TC-IF-104-27, TC-IF-302-13, TC-IF-302-14
- Requirement: REQ-API-023
- Group: EX
- Kind: unit
- Text: The expected values of these checks shall be written as exact values: statuses, codes, IDs, versions, authors, counts, orders, words of the page and hashes, with no tolerance; places in pixels are compared rounded to whole pixels (TC-GA-036, TC-GA-037 only).
- Rationale: every outcome of the test spec is exact (its limit column); a tolerance would hide a defect.
- Credibility aspect: reference accuracy
- Verified by: known answer
- Sign-off: skimmed as a group
- Status: Draft

### TR-VIEW-019 – Times are not compared exactly
- Applies to: TC-GA-021, TC-GA-030, TC-IF-104-17, TC-IF-104-25
- Requirement: REQ-GA-017
- Group: EX
- Kind: unit
- Text: The checks shall compare a time only as the text the IF-104 v2 answer holds for that version (the page shows what it was given), and in the backend checks only for being present and not decreasing, never against a fixed clock value.
- Rationale: the time is the store's clock (the mock's is a counter); fixed values would make the checks flaky and say nothing about the requirement (as TR-CORE-008).
- Credibility aspect: measurement conditions
- Verified by: review
- Sign-off: skimmed as a group
- Status: Draft

### TR-VIEW-020 – What the file checks read
- Applies to: TC-GA-031, TC-GA-032, TC-OPR-011
- Requirement: REQ-GA-015
- Group: EX
- Kind: unit
- Text: TC-GA-031 shall hash the files as committed (bytes, no line-ending change); TC-GA-032 shall scan every `.css` of `graph_app/` except `tokens.css` and `vendor/`, plus `style` attributes and `<style>` blocks of its HTML, for `#` colours, `rgb(`, `rgba(`, `hsl(`, `hsla(`, the CSS named colours, `font-family` values and `px` values of `border-radius` and `box-shadow`, allowing them only inside a `var(--…)` use; TC-OPR-011 shall read the stage of `deploy/Containerfile` that the release image is built from.
- Rationale: these are the forms in which a style can bypass the tokens (REQ-GA-015) and a file can drift (REQ-GA-014); the list fixes what "outside the tokens" means so the scan is reproducible.
- Credibility aspect: validity domain
- Verified by: known answer (TR-VIEW-021's planted literal)
- Sign-off: skimmed as a group
- Status: Draft

### TR-VIEW-021 – Each new check is shown able to fail
- Applies to: TC-API-018, TC-API-019, TC-API-020, TC-API-021, TC-API-022, TC-API-023, TC-API-024, TC-API-025, TC-OPR-011, TC-GA-017, TC-GA-018, TC-GA-019, TC-GA-020, TC-GA-021, TC-GA-022, TC-GA-023, TC-GA-024, TC-GA-025, TC-GA-026, TC-GA-027, TC-GA-028, TC-GA-029, TC-GA-030, TC-GA-031, TC-GA-032, TC-GA-033, TC-GA-034, TC-GA-035, TC-GA-036, TC-GA-037, TC-GA-038, TC-GA-039
- Requirement: REQ-GA-043
- Group: CR
- Kind: setup
- Text: Each of these checks shall be shown able to fail once, by running it against a deliberate defect of the unit it checks, before its pass is trusted; the defects are listed per check in `plan.md` (for example: the store default changed to PostgreSQL, the record written twice, the origin check removed, a filter that ignores the description, a mark on every step, a link around the stored name, a random seed, a page that saves the arrangement on drop, a planted `color: #fff`, a planted request to `https://example.invalid/x.css`).
- Rationale: the page logic comes from the prototype (R6 keep+tests), and a check written against existing code tends to confirm it; the red state before the code is not enough where a stub could pass by accident (as TR-CORE-006).
- Credibility aspect: reviewer independence
- Verified by: mutation (each listed defect makes its check fail; recorded in the implementation log)
- Status: Draft
