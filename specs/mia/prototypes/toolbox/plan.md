# Plan: G-V2.TOOLBOX (toolbox and trust) -- DRAFT from the prototype

Status: Prototype (draft, not reviewed, not applied to `specs/mia/goals/G-V2.TOOLBOX/`). Written 2026-11-08 from the template of `specs/mia/goals/G-V2.MODEL/plan.md`, the owner's decisions D1-D5 and the carry-over table in `prototype-report.md`.

**Goal:** specs/mia/goals/G-V2.TOOLBOX/goal.md   **Requirements:** REQ-WFM-050..056, 067, 068, 070 in `nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md`, plus three new ones below (IDs are reserved per session, `goals/G-V2/parallel-work.md`; here NEW-A..C)   **Test spec:** `test-spec.md` of N-2.3, scenarios at the end   **Acceptance:** AC-32a..c (proposed in `proposed-spec-changes.md`)

Line of work `goal/v2.toolbox`; supervised. Pure logic: no model step, no prompt, no eval suite, no eval budget. Red tests are written first in a session of their own (Step 4) and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `contracts/`, `benchmarks/`, `eval/suites/` or `eval/baselines/`.

## What the toolbox does (the plan in one paragraph)
One entry per transform ID (latest version). Each entry has a trust status (untrusted or trusted) that decides whether it may run, and a lifecycle (draft, tested, retired) that records its performance. Outside transforms are stored untrusted and nothing of them runs on import; only the owner marks one trusted. Retired entries are not offered for new graphs but can run as the baseline of a check. MIA's shipped nodes are in the same toolbox, trusted, and not exportable.

## New requirements (proposed, from the owner's decisions)
| Id | Text (EARS) | Decision | Check |
|---|---|---|---|
| NEW-A | When someone looks up an untrusted transform, the Workflow management shall show the reason it is untrusted. | OC-1, carry-over 3 | the look-up of an imported transform names "imported from outside MIA" (exact) |
| NEW-B | Where the owner allowed it when retiring an untrusted transform, the Workflow management shall run it as the baseline of a check; it shall refuse the allowance from any other account. | D3 | non-owner refused, state stays; retired untrusted without allowance is refused as baseline; with allowance runs (exact); still never in a graph |
| NEW-C | When a transform arrives with the ID of an entry and a higher version, the Workflow management shall replace its code and keep its trust status and lifecycle; with an equal or lower version it shall refuse. | D1, D5 | version 2 runs after version 1 was trusted, version 1 again is refused (exact) |

Changes to existing requirements: REQ-WFM-050 (one entry per ID, see NEW-C), 055 (export refused for a shipped node), 056 (shipped flag; one entry per ID, the highest non-retired version), 068 (refers to NEW-B). Details in `proposed-spec-changes.md`.

## Interface (stand-ins for the red tests)
- `Toolbox(library)`: `import_transform(text)`, `export_transform(id)`, `look_up(id)`, `offer()`, `set_trust(id, value, account)`, `set_lifecycle(id, value, account, evidence=None, allow_baseline=False)`, `run(id, args, as_baseline=False)`, `seed_shipped(nodes_dir)`. Signatures follow `toolbox.py` of the prototype; the prototype is the model, the code is rewritten.
- `library`: the IF-203 v1 library with the new kind `transforms`. Decided by the owner 2026-11-08 (option A): TOOLBOX itself adds the `transforms` part to `workflow_library.py` (kind, `set_trust`, `set_lifecycle`); MODEL and CONVERT add their own parts. Until T-06 the toolbox works against a mock of that part. Who is the owner comes in as a lookup the test supplies (stand-in for IF-101 accounts).
- `GraphRunner(trust)` of MODEL asks `Toolbox.look_up(id)["trust"]`; TOOLBOX does not call MODEL.

## Task list
| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-01 Entries by ID, status fields, reason, newer versions | REQ-WFM-050, 051, NEW-A, NEW-C | TC-WFM-050, 051 and the new TCs | red tests installed |
| T-02 Import and export of the exchange file | REQ-WFM-052, 053, 055 | TC-WFM-052, 053, 055 | T-01 |
| T-03 Only the owner trusts | REQ-WFM-054 | TC-WFM-054 | T-01 |
| T-04 Lifecycle, retired, baseline | REQ-WFM-067, 068, 070, NEW-B | TC-WFM-067, 068, 070 and the new TC | T-01 |
| T-05 Seed with the shipped nodes | REQ-WFM-056 | TC-WFM-056 | T-01 |
| T-06 The `transforms` part of IF-203 v1 in the library | REQ-WFM-050, 051, 054, 067 on the real library (TR-TOOLBOX-001) | the tests of T-01..T-05 against the IF-203 v1 contract suite for `transforms`, no skip; the v0 suite still passes | T-01..T-05; G-V2.STORE merged |

## Tasks

### T-01: Entries by ID, status fields, reason, newer versions
- Implements: REQ-WFM-050, REQ-WFM-051, NEW-A, NEW-C
- Tests to turn green: TC-WFM-050, TC-WFM-051, and the cases for NEW-A and NEW-C (written in Step 4)
- Touches: a new module `toolbox.py` in N-2.3 (name proposed)
- Must not touch: protected material, `workflow_library.py` and `library.py` (the old library keeps its workflow statuses), `graph_run.py` (MODEL), `graph_tables.py` (STORE)
- Depends on: red tests installed
- Done when: the listed tests are green, all other tests unchanged
- Notes: trust values are exactly `untrusted` and `trusted`; any other value is refused (051). The toolbox does not use the four workflow statuses of `workflow_library.py` (draft, tested, trusted, retired) for transforms: trust and lifecycle are two fields.

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
- Notes: exception to CON-6 (A-89). Setting a transform back to untrusted is allowed for everyone (prototype choice, not in a requirement: confirm in review).

### T-04: Lifecycle, retired, baseline
- Implements: REQ-WFM-067, REQ-WFM-068, REQ-WFM-070, NEW-B
- Tests to turn green: TC-WFM-067, TC-WFM-068, TC-WFM-070, and the case for NEW-B
- Touches: `toolbox.py`
- Must not touch: protected material, the equivalence check (CONVERT, REQ-WFM-069)
- Depends on: T-01
- Done when: the listed tests are green
- Notes: a change to `tested` names its evidence (a check or run); `offer()` leaves retired entries out; a retired entry runs as baseline only with `as_baseline=True`, and an untrusted one only with the owner's allowance (NEW-B). A skill record that is retired is CONVERT's part; here only transforms.

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
- Touches: `workflow_library.py` (adds `transforms` to `KINDS`, `set_trust`, `set_lifecycle`; `set_status` stays for workflows); the wiring in `toolbox.py` to the library
- Must not touch: protected material, STORE's files, the snapshot operations and the kinds `skills` and `snapshots` (CONVERT), the four workflow states
- Depends on: T-01..T-05; G-V2.STORE merged (IF-301 v2)
- Done when: the mock passes the IF-203 v1 contract suite for `transforms`, or the difference is reported as a finding; the listed tests are green against the real library; the v0 suite is unchanged
- Notes: a transform is a versioned record (ID, version, schemas, code text); trust and lifecycle live in a separate meta record per ID, as `TableMeta` does for workflows, so saving a new version leaves them as they are (this is NEW-C / D5). MODEL and CONVERT also extend this file: keep the edits to separate methods and tell the owner which lines are shared (`parallel-work.md`). If the mock fails the suite, stop and report.

## Order and checks
T-01 first; T-02 to T-05 are independent of each other; T-06 waits for STORE. After each task: `python tests/test_<name>.py` for its tests, then the stage 1 and 2 steps of `stages.yaml`. Merge order of the subgoals: STORE, MODEL, TOOLBOX, CONVERT.

## Size check (splitting)
10 requirements of the goal plus three new, six tasks of one session each, all inside N-2.3. No split is suggested; the goal record's "keep together" stands.

## Risks and open points
1. D5 (trust carries over to a newer version): new code runs without a new decision; consider logging version changes of trusted transforms (prototype report, risks).
2. SC-09 / TD-24: trusted code runs unsandboxed in the MIA process; stays open.
3. Resolved by the owner 2026-11-08 (option A): TOOLBOX adds the `transforms` part of IF-203 v1 itself. Open: the file `workflow_library.py` is also extended by MODEL and CONVERT, so the order of merges and shared lines need the rules of `parallel-work.md`.
4. The IF-203 v1 contract suite for kind `transforms` is not written; the Step 4 session writes it.
4b. Does the meta record of transforms need a new table in IF-302, or can it share `workflow_meta`? Not checked; the Step 4 session or the owner decides.
5. Shipped nodes carry no code text: running them is not part of this goal.
6. Anyone may set a transform back to untrusted (T-03 notes): confirm.
7. REQ-WFM-054 History still says "A-89 not yet approved": check whether A-90 superseded it.
8. Test requirement IDs (TR-TOOLBOX-nnn) and TC IDs for NEW-A..C are not reserved yet.
