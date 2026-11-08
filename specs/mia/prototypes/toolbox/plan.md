# Plan: G-V2.TOOLBOX (toolbox and trust) -- DRAFT from the prototype

Status: Prototype (draft, not reviewed, not applied to `specs/mia/goals/G-V2.TOOLBOX/`). Written 2026-11-08 from the template of `specs/mia/goals/G-V2.MODEL/plan.md`, the owner's decisions D1-D5 and the carry-over table in `prototype-report.md`.

**Goal:** specs/mia/goals/G-V2.TOOLBOX/goal.md   **Requirements:** REQ-WFM-050..056, 067, 068, 070 in `nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md`, plus three new ones below (IDs are reserved per session, `goals/G-V2/parallel-work.md`; here REQ-WFM-090..C)   **Test spec:** `test-spec.md` of N-2.3, scenarios at the end   **Acceptance:** AC-32a..c (proposed in `proposed-spec-changes.md`)

Line of work `goal/v2.toolbox`; supervised. Pure logic: no model step, no prompt, no eval suite, no eval budget. Red tests are written first in a session of their own (Step 4) and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `contracts/`, `benchmarks/`, `eval/suites/` or `eval/baselines/`.

## What the toolbox does (the plan in one paragraph)
One entry per transform ID (latest version). Each entry has a trust status (untrusted or trusted) that decides whether it may run, and a lifecycle (draft, tested, retired) that records its performance. Outside transforms are stored untrusted and nothing of them runs on import; only the owner marks one trusted. Retired entries are not offered for new graphs but can run as the baseline of a check. MIA's shipped nodes are in the same toolbox, trusted, and not exportable.

## New requirements (proposed, from the owner's decisions)
| Id | Text (EARS) | Decision | Check |
|---|---|---|---|
| REQ-WFM-090 | When someone looks up an untrusted transform, the Workflow management shall show the reason it is untrusted. | OC-1, carry-over 3 | the look-up of an imported transform names "imported from outside MIA" (exact) |
| REQ-WFM-091 | Where the owner allowed it when retiring an untrusted transform, the Workflow management shall run it as the baseline of a check; it shall refuse the allowance from any other account. | D3 | non-owner refused, state stays; retired untrusted without allowance is refused as baseline; with allowance runs (exact); still never in a graph |
| REQ-WFM-092 | When a transform arrives with the ID of an entry and a higher version, the Workflow management shall replace its code and keep its trust status and lifecycle; with an equal or lower version it shall refuse. | D1, D5 | version 2 runs after version 1 was trusted, version 1 again is refused (exact) |
| REQ-WFM-093 | When the code of a trusted transform is replaced by a newer version, the Workflow management shall record an event with the ID, the old and the new version and the author. | D5 risk, owner 2026-11-08 | one event per replace of a trusted transform, none for an untrusted one (exact) |

Changes to existing requirements: REQ-WFM-054 (any logged-in account may set a transform back to untrusted, only trusting is owner-only), REQ-WFM-050 (one entry per ID, see REQ-WFM-092), 055 (export refused for a shipped node), 056 (shipped flag; one entry per ID, the highest non-retired version), 068 (refers to REQ-WFM-091). Details in `proposed-spec-changes.md`.

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
| T-04 Lifecycle, retired, baseline | REQ-WFM-067, 068, 070, REQ-WFM-091 | TC-WFM-067, 068, 070, 091 | T-01 |
| T-05 Seed with the shipped nodes | REQ-WFM-056 | TC-WFM-056 | T-01 |
| T-06 The `transforms` part of IF-203 v1 in the library | REQ-WFM-050, 051, 054, 067 on the real library (TR-TOOLBOX-001) | the tests of T-01..T-05 against the IF-203 v1 contract suite for `transforms`, no skip; the v0 suite still passes | T-01..T-05; G-V2.STORE merged |

## Tasks

### T-01: Entries by ID, status fields, reason, newer versions
- Implements: REQ-WFM-050, REQ-WFM-051, REQ-WFM-090, REQ-WFM-092
- Tests to turn green: TC-WFM-050, TC-WFM-051, and the cases for REQ-WFM-090 and REQ-WFM-092 (written in Step 4)
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
- Notes: import stores untrusted whatever the file's `status` says (prototype `test_oc1`). A file that fails the schema check is refused with the first message. Export of a shipped node is refused (no code text).

### T-03: Only the owner trusts
- Implements: REQ-WFM-054
- Tests to turn green: TC-WFM-054
- Touches: `toolbox.py`
- Must not touch: protected material, account code (`accounts.py`)
- Depends on: T-01
- Done when: the owner's account changes the status, any other is refused, the refusal names the reason and the status stays
- Notes: exception to CON-6 (A-89). Setting a transform back to untrusted is allowed for every logged-in account (owner 2026-11-08); the change is in the text of REQ-WFM-054.

### T-04: Lifecycle, retired, baseline
- Implements: REQ-WFM-067, REQ-WFM-068, REQ-WFM-070, REQ-WFM-091
- Tests to turn green: TC-WFM-067, 068, 070, 091
- Touches: `toolbox.py`
- Must not touch: protected material, the equivalence check (CONVERT, REQ-WFM-069)
- Depends on: T-01
- Done when: the listed tests are green
- Notes: a change to `tested` names its evidence (a check or run); `offer()` leaves retired entries out; a retired entry runs as baseline only with `as_baseline=True`, and an untrusted one only with the owner's allowance (REQ-WFM-091). A skill record that is retired is CONVERT's part; here only transforms.

### T-05: Seed with the shipped nodes
- Implements: REQ-WFM-056
- Tests to turn green: TC-WFM-056
- Touches: `toolbox.py`; reads `library/nodes/*/*.json` only
- Must not touch: protected material, `library/nodes` itself
- Depends on: T-01
- Done when: after a first start every shipped node is in the toolbox as trusted, flagged shipped, one entry per ID
- Notes: 73 IDs today, 89 files (some IDs have several versions, for example `code.gate_abstain`): the highest non-retired version is seeded. The prototype has no code text for them: how a shipped node is run stays with the old runner (finding 2 of the report).

### T-06: The `transforms` part of IF-203 v1 in the library
- Implements: REQ-WFM-050, 051, 054, 067 on the real library (TR-TOOLBOX-001, proposed)
- Tests to turn green: the tests of T-01..T-05 run against the IF-203 v1 contract suite for the kind `transforms`, with no skip; the IF-203 v0 suite keeps passing
- Touches: the new table of transform meta in IF-302 (amendment A-110, proposed; its contract suite is written in Step 4); `workflow_library.py` (adds `transforms` to `KINDS`, `set_trust`, `set_lifecycle`; `set_status` stays for workflows); the wiring in `toolbox.py` to the library
- Must not touch: protected material, STORE's files, the snapshot operations and the kinds `skills` and `snapshots` (CONVERT), the four workflow states
- Depends on: T-01..T-05; G-V2.STORE merged (IF-301 v2)
- Done when: the mock passes the IF-203 v1 contract suite for `transforms`, or the difference is reported as a finding; the listed tests are green against the real library; the v0 suite is unchanged
- Notes: a transform is a versioned record (ID, version, schemas, code text); trust and lifecycle live in a separate meta record per ID in a new table of IF-302 (owner 2026-11-08), as `TableMeta` does for workflows in `workflow_meta`, so saving a new version leaves them as they are (this is REQ-WFM-092 / D5). MODEL and CONVERT also extend this file: each goal adds its own methods and kinds in its own block, merge order STORE, MODEL, TOOLBOX, CONVERT, later goals rebase (owner 2026-11-08); TOOLBOX touches only the block of the kind `transforms`, `set_trust` and `set_lifecycle`. If the mock fails the suite, stop and report.

## Order and checks
T-01 first; T-02 to T-05 are independent of each other; T-06 waits for STORE. After each task: `python tests/test_<name>.py` for its tests, then the stage 1 and 2 steps of `stages.yaml`. Merge order of the subgoals: STORE, MODEL, TOOLBOX, CONVERT.

## Size check (splitting)
10 requirements of the goal plus three new, six tasks of one session each, all inside N-2.3. No split is suggested; the goal record's "keep together" stands.

## Decided by the owner (2026-11-08, questionnaire on the open points)
| Point | Decision |
|---|---|
| Meta record of transforms (4b) | a new table in IF-302: amendment A-110 (TOOLBOX range A-110..119, proposed), contract suite written in Step 4 |
| Untrust (6) | any logged-in account may set trusted back to untrusted; only trusting is owner-only (REQ-WFM-054 text) |
| Version change of a trusted transform (1) | an event is recorded: REQ-WFM-093 |
| `goals/G-V2.TOOLBOX/goal.md` | amend Parts and Scope now (see next steps) |
| Shared `workflow_library.py` (3b) | separate methods in its own block, merge in order |
| IDs (8) | REQ-WFM-090..093, TC-WFM-090..093, TR-TOOLBOX-001.., A-110 and D-220.. from the TOOLBOX block of `parallel-work.md`; nothing written to shared files |

## Next steps that follow from it (not done)
1. In the worktree of `goal/v2.toolbox` (does not exist yet): amend `goals/G-V2.TOOLBOX/goal.md`, Parts row "IF-203 v1 library (kind `transforms`)" to real (TOOLBOX adds it), Dependencies note, scope rows for REQ-WFM-090..093 and the amended REQ-WFM-054; that file is TOOLBOX's own (parallel-work.md).
2. Parent session, not this one: `goals/G-V2/goal.md` line 115 ("all three extend it") and `high-level-spec.md` (FR-38, AC-32a..c); `requirements.md` is parent-only.
3. Write A-110 (IF-302 table for transform meta) and the IF-203 v1 contract suite for `transforms` in Step 4 outside the implementing session.

## Risks and open points
1. D5 (trust carries over to a newer version): new code runs without a new decision; the version change is logged (REQ-WFM-093), the risk stays.
2. SC-09 / TD-24: trusted code runs unsandboxed in the MIA process; stays open.
3. Resolved: TOOLBOX adds the `transforms` part of IF-203 v1 (option A); the shared file follows the rule above.
4. The IF-203 v1 contract suite for kind `transforms` is not written; the Step 4 session writes it.
4b. Resolved: new table in IF-302 (A-110, proposed).
5. Shipped nodes carry no code text: running them is not part of this goal.
6. Resolved: any logged-in account may untrust.
7. REQ-WFM-054 History still says "A-89 not yet approved": check whether A-90 superseded it.
8. Resolved: IDs from the TOOLBOX block; the final TC list is written in Step 4.
