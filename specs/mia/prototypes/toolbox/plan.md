# Plan: G-V2.TOOLBOX (toolbox and trust) -- DRAFT from the prototype

Status: Prototype (draft, not reviewed). Written 2026-11-08 from the template of `specs/mia/goals/G-V2.MODEL/plan.md`, the owner's decisions D1-D5 and the carry-over table in `prototype-report.md`. Updated 2026-11-08 after Plan step 3: the requirements, checks and test requirements named here are in commit `308c67f` of the line of work `goal/v2.toolbox` (all Draft); this file is the draft of `goals/G-V2.TOOLBOX/plan.md` (Step 5) and is not applied there.

**Goal:** specs/mia/goals/G-V2.TOOLBOX/goal.md   **Requirements:** REQ-WFM-050..056, 067, 068, 070 in `nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md`, plus REQ-WFM-090..095 (new, IDs from the TOOLBOX block of `goals/G-V2/parallel-work.md`)   **Test spec:** `test-spec.md` of N-2.3, TC-WFM-050..056, 067, 068, 070, 090..095 with scenarios at the end   **Test requirements:** TR-TOOLBOX-001..006 in `specs/mia/test-requirements.md`   **Acceptance:** AC-32 (AC-32a..c proposed in `proposed-spec-changes.md`, not yet in the HLS)

Line of work `goal/v2.toolbox`; supervised. Pure logic: no model step, no prompt, no eval suite, no eval budget. Red tests are written first in a session of their own (Step 4) and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `contracts/`, `benchmarks/`, `eval/suites/` or `eval/baselines/`.

## What the toolbox does (the plan in one paragraph)
One entry per transform ID (latest version). Each entry has a trust status (untrusted or trusted) that decides whether it may run, and a lifecycle (draft, tested, retired) that records its performance. Outside transforms are stored untrusted and nothing of them runs on import; only the owner marks one trusted. Retired entries are not offered for new graphs but can run as the baseline of a check. MIA's shipped nodes are in the same toolbox, trusted, and not exportable.

## New and changed requirements (written in Plan step 3, Draft)
| Id | Text (EARS) | Decision | Check |
|---|---|---|---|
| REQ-WFM-090 | When someone looks up an untrusted transform, the Workflow management shall show the reason it is untrusted. | OC-1 | TC-WFM-090 |
| REQ-WFM-091 | Where the owner allowed it when retiring an untrusted transform, the Workflow management shall run it as the baseline of a check. | D3 | TC-WFM-091 |
| REQ-WFM-092 | When a transform arrives with the ID of an entry and a higher version, the Workflow management shall replace the code of the entry and keep its trust status and lifecycle. | D1, D5 | TC-WFM-092 |
| REQ-WFM-093 | When the code of a trusted transform is replaced by a newer version, the Workflow management shall record an event with the ID, the old and the new version and the author. | D5 risk | TC-WFM-093 |
| REQ-WFM-094 | If an export is asked for a shipped transform, then the Workflow management shall refuse it. | D2 | TC-WFM-094 |
| REQ-WFM-095 | If an account other than the owner asks to allow an untrusted retired transform as a baseline, then the Workflow management shall refuse the allowance. | D3 | TC-WFM-095 |

Changed: REQ-WFM-050 (criterion: an equal or lower version is refused, a higher one is REQ-WFM-092), 054 (criterion: any account sets trusted back to untrusted), 056 (text and criterion: marked shipped, one entry per ID, the highest version that is not retired), 068 (criterion: a retired trusted transform; an untrusted one only under REQ-WFM-091). REQ-WFM-055 is unchanged: the refusal of the export of a shipped transform is REQ-WFM-094.

## Interface (stand-ins for the red tests)
- `Toolbox(library)`: `import_transform(text)`, `export_transform(id)`, `look_up(id)`, `offer()`, `set_trust(id, value, account)`, `set_lifecycle(id, value, account, evidence=None, allow_baseline=False)`, `run(id, args, as_baseline=False)`, `seed_shipped(nodes_dir)`. Signatures follow `toolbox.py` of the prototype; the prototype is the model, the code is rewritten.
- `library`: the IF-203 v1 library with the new kind `transforms`. Decided by the owner 2026-11-08 (option A): TOOLBOX itself adds the `transforms` part to `workflow_library.py` (kind, `set_trust`, `set_lifecycle`); MODEL and CONVERT add their own parts. Until T-06 the toolbox works against a mock of that part. Who is the owner comes in as a lookup the test supplies (stand-in for IF-101 accounts).
- `GraphRunner(trust)` of MODEL asks `Toolbox.look_up(id)["trust"]`; TOOLBOX does not call MODEL.

## Task list
| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-01 Entries by ID, status fields, reason, newer versions | REQ-WFM-050, 051, 090, 092, 093 | TC-WFM-050, 051, 090, 092, 093 | red tests installed |
| T-02 Import and export of the exchange file | REQ-WFM-052, 053, 055 | TC-WFM-052, 053, 055 | T-01 |
| T-03 Only the owner trusts | REQ-WFM-054 | TC-WFM-054 | T-01 |
| T-04 Lifecycle, retired, baseline | REQ-WFM-067, 068, 070, 091, 095 | TC-WFM-067, 068, 070, 091, 095 | T-01 |
| T-05 Seed with the shipped nodes, no export of them | REQ-WFM-056, 094 | TC-WFM-056, 094 | T-01, T-02 |
| T-06 The `transforms` part of IF-203 v1 in the library | REQ-WFM-050, 051, 054, 067 on the real library (TR-TOOLBOX-001) | the tests of T-01..T-05 against the IF-203 v1 contract suite for `transforms`, no skip; the v0 suite still passes | T-01..T-05; G-V2.STORE merged |

## Tasks

### T-01: Entries by ID, status fields, reason, newer versions
- Implements: REQ-WFM-050, REQ-WFM-051, REQ-WFM-090, REQ-WFM-092, REQ-WFM-093
- Tests to turn green: TC-WFM-050, TC-WFM-051, TC-WFM-090, TC-WFM-092, TC-WFM-093
- Touches: a new module `toolbox.py` in N-2.3 (name proposed)
- Must not touch: protected material, `workflow_library.py` and `library.py` (the old library keeps its workflow statuses), `graph_run.py` (MODEL), `graph_tables.py` (STORE)
- Depends on: red tests installed
- Done when: the listed tests are green, all other tests unchanged
- Notes: the version replace of a trusted transform writes an event (REQ-WFM-093) through IF-401, with a stand-in in the tests. Trust values are exactly `untrusted` and `trusted`; any other value is refused (051). The toolbox does not use the four workflow statuses of `workflow_library.py` (draft, tested, trusted, retired) for transforms: trust and lifecycle are two fields.

### T-02: Import and export of the exchange file
- Implements: REQ-WFM-052, REQ-WFM-053, REQ-WFM-055
- Tests to turn green: TC-WFM-052, TC-WFM-053, TC-WFM-055
- Touches: `toolbox.py`; uses `jsonschema` (already pinned, `requirements.txt:19`)
- Must not touch: protected material, anything that can compile or run the code text on import
- Depends on: T-01
- Done when: the listed tests are green; the marker file of TC-WFM-053 never appears on import
- Notes: import stores untrusted whatever the file's `status` says (prototype `test_oc1`). A file that fails the schema check is refused with the first message. Export of a shipped node is REQ-WFM-094, in T-05.

### T-03: Only the owner trusts
- Implements: REQ-WFM-054
- Tests to turn green: TC-WFM-054
- Touches: `toolbox.py`
- Must not touch: protected material, account code (`accounts.py`)
- Depends on: T-01
- Done when: the owner's account changes the status, any other is refused, the refusal names the reason and the status stays
- Notes: exception to CON-6 (A-89). Setting a transform back to untrusted is allowed for every logged-in account (owner 2026-11-08); the change is in the text of REQ-WFM-054.

### T-04: Lifecycle, retired, baseline
- Implements: REQ-WFM-067, REQ-WFM-068, REQ-WFM-070, REQ-WFM-091, REQ-WFM-095
- Tests to turn green: TC-WFM-067, TC-WFM-068, TC-WFM-070, TC-WFM-091, TC-WFM-095
- Touches: `toolbox.py`
- Must not touch: protected material, the equivalence check (CONVERT, REQ-WFM-069)
- Depends on: T-01
- Done when: the listed tests are green
- Notes: a change to `tested` names its evidence (a check or run); `offer()` leaves retired entries out; a retired entry runs as baseline only with `as_baseline=True`, and an untrusted one only with the owner's allowance (REQ-WFM-091), which only the owner can set (REQ-WFM-095). A skill record that is retired is CONVERT's part; here only transforms.

### T-05: Seed with the shipped nodes
- Implements: REQ-WFM-056, REQ-WFM-094
- Tests to turn green: TC-WFM-056, TC-WFM-094
- Touches: `toolbox.py`; reads `library/nodes/*/*.json` only
- Must not touch: protected material, `library/nodes` itself
- Depends on: T-01, T-02 (the export it refuses)
- Done when: after a first start every shipped node is in the toolbox once, trusted and marked shipped, with its highest version that is not retired; its export is refused
- Notes: 73 IDs today, 89 files (some IDs have several versions, for example `code.gate_abstain`): the highest non-retired version is seeded. The prototype has no code text for them: how a shipped node is run stays with the old runner (finding 2 of the report).

### T-06: The `transforms` part of IF-203 v1 in the library
- Implements: REQ-WFM-050, 051, 054, 067 on the real library (TR-TOOLBOX-001)
- Tests to turn green: the tests of T-01..T-05 run against the IF-203 v1 contract suite for the kind `transforms`, with no skip; the IF-203 v0 suite keeps passing
- Touches: the new table of transform meta in IF-302 (amendment A-110, proposed; its contract suite is written in Step 4); `workflow_library.py` (adds `transforms` to `KINDS`, `set_trust`, `set_lifecycle`; `set_status` stays for workflows); the wiring in `toolbox.py` to the library
- Must not touch: protected material, STORE's files, the snapshot operations and the kinds `skills` and `snapshots` (CONVERT), the four workflow states
- Depends on: T-01..T-05; G-V2.STORE merged (IF-301 v2)
- Done when: the mock passes the IF-203 v1 contract suite for `transforms`, or the difference is reported as a finding; the listed tests are green against the real library; the v0 suite is unchanged
- Notes: a transform is a versioned record (ID, version, schemas, code text); trust and lifecycle live in a separate meta record per ID in a new table of IF-302 (owner 2026-11-08), as `TableMeta` does for workflows in `workflow_meta`, so saving a new version leaves them as they are (this is REQ-WFM-092 / D5); the event of REQ-WFM-093 is not part of the library but of the toolbox. MODEL and CONVERT also extend this file: each goal adds its own methods and kinds in its own block, merge order STORE, MODEL, TOOLBOX, CONVERT, later goals rebase (owner 2026-11-08); TOOLBOX touches only the block of the kind `transforms`, `set_trust` and `set_lifecycle`. If the mock fails the suite, stop and report.

## Order and checks
T-01 first; T-02 to T-05 are independent of each other; T-06 waits for STORE. After each task: `python tests/test_<name>.py` for its tests, then the stage 1 and 2 steps of `stages.yaml`. Merge order of the subgoals: STORE, MODEL, TOOLBOX, CONVERT.

## Size check (splitting)
16 requirements of the goal (the 10 of the first scope plus REQ-WFM-090..095) and IF-203, six tasks of one session each, all inside N-2.3. No split is suggested; the goal record's "keep together" stands.

## Decided by the owner (2026-11-08, questionnaire on the open points)
| Point | Decision |
|---|---|
| Meta record of transforms (4b) | a new table in IF-302: amendment A-110 (TOOLBOX range A-110..119, proposed), contract suite written in Step 4 |
| Untrust (6) | any logged-in account may set trusted back to untrusted; only trusting is owner-only (REQ-WFM-054 text) |
| Version change of a trusted transform (1) | an event is recorded: REQ-WFM-093 |
| `goals/G-V2.TOOLBOX/goal.md` | amend Parts and Scope now (see next steps) |
| Shared `workflow_library.py` (3b) | separate methods in its own block, merge in order |
| IDs (8) | REQ-WFM-090..095, TC-WFM-090..095, TR-TOOLBOX-001..006, A-110 and D-220.. from the TOOLBOX block of `parallel-work.md` |

## Done in Plan step 3 and what is still open
Done on `goal/v2.toolbox` (commit `308c67f`, Draft): requirements REQ-WFM-090..095 and the changed criteria, 16 checks with scenarios in `test-spec.md`, TR-TOOLBOX-001..006, the regenerated requirement block of `architecture.sysml` (`check_sysml.sh`: 0 errors), the amended `goal.md` (commit `4768d5d`). Checks: `req_lint` no error on these IDs, `trace_check` six errors fewer, `goal_check` two errors, `req_graph` none on them.
Open:
1. Plausibility: REQ-WFM-090..095 only have proposals in `plausibility-proposal.yaml`; a person rates them (`req_plausibility.py` reports six errors until then).
2. Parent session: `goals/G-V2/goal.md` (IF-302 in scope, line 115 "all three extend it": the one remaining GL3 error), `high-level-spec.md` (FR-38 text, AC-32a..c), root `requirements.md`.
3. Step 4, outside the implementing session: A-110 (IF-302 table for transform meta), the IF-203 v1 contract suite for `transforms`, the red tests, the fixed copy of three shipped nodes (TR-TOOLBOX-004).
4. Review in batches (`req_review.py`): the requirements group by group, then the checks; REQ-WFM-092 and 093 are single requirements with several "and" in the lint (INFO), the owner may ask to split.
5. Draft `proposed-spec-changes.md` is older than step 3: the requirement text there is superseded by `requirements.md`.

## Risks and open points
1. D5 (trust carries over to a newer version): new code runs without a new decision; the version change is logged (REQ-WFM-093), the risk stays.
2. SC-09 / TD-24: trusted code runs unsandboxed in the MIA process; stays open.
3. Resolved: TOOLBOX adds the `transforms` part of IF-203 v1 (option A); the shared file follows the rule above (T-06 notes).
4. The IF-203 v1 contract suite for kind `transforms` is not written; the Step 4 session writes it.
4b. Resolved: new table in IF-302 (A-110, proposed).
5. Shipped nodes carry no code text: running them is not part of this goal.
6. Resolved: any logged-in account may untrust.
7. REQ-WFM-054 History still says "A-89 not yet approved" (kept in the requirements file): check whether A-90 superseded it; not checked.
8. Resolved: IDs from the TOOLBOX block.
