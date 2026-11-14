# Hand-over after Step 4 of G-V2.STORE (written 2026-11-07): what is left

Read `CLAUDE.md` first. Phase: Plan, subgoal **G-V2.STORE**, line of work `goal/v2.store`, worktree `.claude/worktrees/goal-v2-store`. The owner installs and merges.

## What is done (commit "test: acceptance tests and IF-301 v2 mock for G-V2.STORE (red)"; the tag `plan-baseline-it2-store` is **not set yet**: it comes after the owner has installed the tests)
All new files are **staged** in `specs/mia/goals/G-V2.STORE/red-tests/` (the deny rules keep the agent out of `tests/`); nothing under `tests/`, `contracts/`, `tests/smoke/`, `benchmarks/`, `eval/` was touched.

| Staged file (target under `tests/`) | What it is |
|---|---|
| `helpers/mocks/if_301_graph_tables_v2.py` | IF-301 v2 mock, complexity 1: the fixed list of types (`data`, `master`, `transform`) as JSON schemas, pure functions, node classes |
| `acceptance/contract/test_if_301_v2_graph_tables.py` | IF-301 v2 contract suite, TC-IF-301-05..19 (golden examples 1..10 of the A-90 text and more). Mock side: 15 pass. Real side: skipped, reason "N-3.2 not integrated yet"; `IF301_V2_REAL=1` runs it (24 failures by assertion at the moment) |
| `helpers/graph_store_standin.py` | storage stand-in = IF-102 mock + the four record tables + `check_record` guard; `if_102_suite_problems()` runs the IF-102 `_mock` cases against it (TR-GTB-002) |
| `acceptance/test_graph_records.py` | TC-GTB-006..021 (20 tests incl. the TR-GTB-002..005 setups), mirroring the scenarios step by step |

Also in the commit (not protected): stubs in `graph_tables.py` (`record_definitions`, `types`, `check_record`, `to_object`, `to_record`, `to_document`, `from_document`, wrong-but-valid values), `tools/install_red_tests_g_v2_store.sh`, `tools/apply_amendment_a90_if301.sh`, the staged v2 contract text `specs/mia/amendments/A-90/IF-301-graph-tables.md`.

State of the tests (overlay of the worktree with the staged files laid over `tests/`; the old v1 IF-301 suite and the v0 IF-203 suite pass unchanged, `tests/test_graph_tables.py` passes):
- Baseline before the work (`python -m unittest discover -s tests -q`, 2026-11-07): 1831 tests, 3 failures, 61 errors, 7 skipped, 1 expected failure. Not caused by this work.
- `test_graph_records.py`: 20 tests, 15 fail by assertion (the Given of each: `record_definitions()` of the stub is empty), 5 pass (IF-102 gate, validator pin 4.23.0, the two import inspections, "the round-trip check can fail").
- The same file with the Graph tables replaced by the v2 mock: 20 of 20 pass (so the tests are satisfiable and agree with the contract text). With a mock whose `check_record` accepts everything: 10 tests/cases fail (010, 011, 017, 019, 020, 021), so the refusal checks do bite.
- `trace_check`: with the staged tests the 15 "no mark.req marker" warnings of REQ-GTB-005..020 are gone; the 517 old errors are unchanged. `goal_check`: no finding. `req_graph`: no new finding.
- TC-GTB-012 and the "round-trip check can fail" test are green from the start (the Graph tables import nothing banned today; the point is the mutation check, TR-GTB-005 and TR-GTB-004).
- Timing: 500 node + 500 edge records, 6.4 ms on the mock (bound 500 ms, D-187); the real figure comes in Implement.

## What is left
1. **Owner: install the tests.** `bash tools/install_red_tests_g_v2_store.sh` (look), then `--do`. Run `python tests/acceptance/contract/test_if_301_v2_graph_tables.py` (mock green, real skipped) and `python tests/acceptance/test_graph_records.py` (fails by assertion). Then commit the installed files and tag that commit `plan-baseline-it2-store` (local, annotated, never pushed); a tag on the staged state would not protect the tests.
2. **Owner: approve the IF-301 v2 contract text** `specs/mia/amendments/A-90/IF-301-graph-tables.md`, above all its last section "Clarifications fixed by the v2 mock and suite", then `bash tools/apply_amendment_a90_if301.sh` (look) and `--do` (not run by this session). It changes only `contracts/IF-301-graph-tables.md`.
3. **Parent session (root files, not mine):** rows TC-IF-301-05..19 in `specs/mia/test-spec.md`; the owner's decision on `definitions()` (below) as a D-number (suggest D-189, in STORE's range) and a line in `specs/mia/amendments/A-90-draft-IF-301-v2.md` (its operations table still says `definitions()` returns six tables); TC-IF-301 rows are not in any `Applies to:` line (same old error as TC-IF-301-01..04).
4. **Step 5: `plan.md` of G-V2.STORE** (tasks for Implement). Suggested cut: T-01 `check_record` and the type list (schemas, `types`, `record_definitions`); T-02 `to_object`/`to_record` and the classes; T-03 `to_document`/`from_document`; T-04 the Storage layer (N-3.1) knows the four tables, calls `check_record` before a write and keeps versions from `record_definitions()`; T-05 stage 2: remove the skip of the real side of the v2 suite (the environment switch in `subject()`), run the IF-102 suite on the real storage, TC-GTB-015 with the real library.

## Decisions taken in this session (the owner's answer, 2026-11-07)
- **`definitions()` stays the two tables of v1; the four record tables come from a new `record_definitions()`.** Why: the v1 suite asserts exactly two tables against the real `graph_tables` and must pass unchanged (TR-GTB-006), and REQ-GTB-001 / TC-GTB-001 say exactly two; the approved A-90 text (six tables in `definitions()`) contradicted both. The staged contract text says so (decision 11).

## Interpretations the suite and the mock fix (the approved text was silent; all are in the staged contract text, section "Clarifications")
`types()` is a dict `{type ID: schema}`; node objects have `id` plus the field names of their type as attributes; an edge's `data` must be an object (`schema_break`, detail `data`); a context node's category is in `data["type"]` and `categories` makes a record a context record; `schema_break` detail is the dotted path (suite pins only top-level paths); a header with a member ID twice is `record_identity` (TC-GTB-017 only requires a refusal: the scenario says "an ID that already exists", I read it as a member ID twice in the header); the document form carries the other node fields flat and the edge JSON field under `data`, edges of a v1 document get `e1`, `e2`, ...
If the owner reads one of these differently, the mock, the suite and the text change together (amendment at the owner).

## Things to know for Implement and the owner
- **TC-GTB-015** hashes the v1 IF-301 suite (`1d9022ca...`) and the IF-203 v0 suite (`0eb58da6...`) as they are on master today. When the IF-203 v1 amendment (MODEL/TOOLBOX) changes `test_if_203_workflow_library.py`, that hash must be updated by an amendment, or the check keeps a copy of the v0 file; TR-GTB-006 says "the file as before A-90". Decide when IF-203 v1 is installed. Also, the scenario's "graphs held as records" is only checked through `from_document`/`to_document`; the real library storing records internally is wired in Implement (T-05), the protected suite files cannot be edited.
- TC-GTB-014: `TC_GTB_014_N=5000 python tests/acceptance/test_graph_records.py` raises N (default 1000, seeds 1..N).
- The tests import `graph_tables` and the mocks with the real `graph_rules` first on the path (the mocks have their own `graph_rules`); do not reorder the `sys.path` lines.
- IF-102 is unchanged; the stand-in subclasses the IF-102 mock and is checked against its `_mock` cases (11 cases) at the start of `test_graph_records.py`.
- Local model (`local-coder`) was not used: the files needed design decisions (the mock, the stand-in, the interpretations), which the skill keeps with the agent.
