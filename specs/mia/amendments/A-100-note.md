# A-100: the Storage layer refuses documents that are too deep or contain themselves (G-V2.STORE, F-19 and F-20)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a100.sh` is not yet run with `--do` in the repository.

## Findings (fifth Verify run, `5d2724b`)
- **F-19 (medium, a defect introduced by T-10):** `storage._unstorable` is iterative but has no cycle guard. `Storage.put` of a Python object that contains itself never returns (reproduced by the drafter: a graph node value that is a list containing itself, and a `workflows` document with a dict containing itself, both ran into a 5 s alarm). Before T-10 the same input raised a `RecursionError`. Only Python callers can build such a document; JSON has no cycles.
- **F-20 (low, a gap in the spec):** for tables that are not graph tables the depth limit is the recursion limit of the interpreter: 300 levels stored, 496 the last stored, 497 the first refused as `nested too deep`; the same 480-level document is refused when `put` runs 100 frames deeper. Graph tables have the 200-level rule (REQ-GTB-027).
- F-21 (low): four lines of `test_a_local_reference_still_works` without Given/When/Then comments; fixed in T-11, no amendment needed.

## Owner's decision (2026-11-08)
Add one Storage requirement with one limit for all tables, and fix F-19 together with it.

## What A-100 contains
| Part | Content |
|---|---|
| **REQ-SLY-013** (N-3.1, Draft, Parent REQ-SLY-004) | "If a document that is put is nested deeper than 200 levels, then the Storage layer shall refuse it as invalid." The document is level 1; graph tables name `schema_break`/`data` (as REQ-GTB-027), other tables `schema`/`nested too deep`; file backend and PostgreSQL. Check TC-SLY-012 |
| **REQ-SLY-014** (N-3.1, Draft, Parent REQ-SLY-004) | "If a document that is put contains itself, then the Storage layer shall refuse it as invalid within one second." Check TC-SLY-013 (time limit 1 s, also a dict that contains itself twice) |
| **test-spec.md of N-3.1** | two rows and two scenarios |
| **plan.md** | task T-11 (storage.py, tests in `tests/test_storage.py`, `tests/test_storage_postgres.py`, the comment lines of F-21), counts (eleven tasks), order, decision 9 |
| Generated | `architecture.sysml` requirement block regenerated after `--do` |
No protected file changes: the Storage checks live in `tests/test_storage.py`, which is unprotected.

## Points for the owner
1. **The limit is 200 levels for every table, with the document as level 1.** The deepest real document in `library/`, `skills/` and `eval/` has 19 levels. A legal document nested 201 to about 496 levels that is stored today (non-graph tables) will be refused. Say if you want another number.
2. **The read side is not part of this.** `Storage.get` of a stored document nested about 480 levels can raise a `RecursionError` on a deep call stack (older than T-10). With the 200-level limit on write no new such document can be stored; documents stored before are not touched.
3. **Plausibility ratings of REQ-SLY-013 and REQ-SLY-014 are needed** (A-101, after your ratings; `plausibility.yaml` is protected and a person rates).
4. **Two more trace errors of a known kind:** `trace_check` shows 519 errors after `--do` instead of 517. The two new ones are "no test requirement applies" for TC-SLY-012 and TC-SLY-013, the same error that the baseline already has for all eleven existing TC-SLY checks (N-3.1 has no test-requirements file). Two warnings "no @pytest.mark.req marker" go away when T-11 writes the tests.

## Checked by the drafter (scratch copy; nothing installed in the repository)
- `--do` twice: the second run changes nothing (checksums of `specs/`, `contracts/`, `tests/` identical); 435 node requirements; `check_sysml` 0 errors; `goal_check` no findings.
- trace_check as described in point 4.

## Install (after the look-only review; T-11 follows in a fresh Implement session)
```
bash tools/apply_amendment_a100.sh --report     # look only
bash tools/apply_amendment_a100.sh --do         # then commit "plan: A-100 installed"
```
