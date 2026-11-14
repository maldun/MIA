# A-93: a node has only the fields of its type (G-V2.STORE, REQ-GTB-022)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a93.sh` is not yet run with `--do` in the repository (run twice in scratch copies, see "Checked by the drafter").

## Finding
Verify finding F-01 (`goals/G-V2.STORE/verification-report.md`, "Owner decisions", 2026-11-07): `Storage.put` accepts `{"type": "data", "foo": 1}` (the schemas of `data`, `transform` and `master` allow extra fields), then `graph_tables.to_object` does `DataNode(id, **data)` and raises `TypeError`; a key `id` inside `data` raises "multiple values for argument 'id'". The mock accepts the same record and silently drops the field. So write, read, mock and REQ-GTB-014 ("rebuilt equals stored") disagree.

## Decision (taken 2026-11-07; the owner delegated it to the reviewer and may overrule)
Refuse extras. The three schemas get `additionalProperties: false`; a node with an extra field, or with a key `id` inside `data`, is `schema_break` naming that field, on write (`check_record`, so also `Storage.put`) and on read (`to_object` calls `check_record` first and never raises). Context-graph nodes are not affected (their schema comes from the caller's `categories`).

## What the amendment contains
| Part | Content |
|---|---|
| **REQ-GTB-022** (new, Draft, TY, Must, Parent FR-40) | "If a node is written or read with a field in its JSON field that its type's schema does not list, then the Graph tables shall refuse the node as `schema_break` naming that field." AC-31 exact, verified by TC-GTB-023 |
| **IF-301 v2** (`contracts/IF-301-graph-tables.md`) | fixed-types text (closed for the fields of a type, workflow nodes only, `types()` carries the setting), golden 16, decision 13, a clarification line, version-history row (v2 is not merged: it stays v2) |
| **Mock** | `TYPE_SCHEMAS` of `data`, `master`, `transform` get `additionalProperties: False`. `_broken_path` also changes (needed, otherwise the detail would not name the field): an additional field is named by its own key, the first in sorted order when several |
| **TC-IF-301-21** (contract suite, mock and real) | one node per type with `foo`, a key `id` in `data`: `check_record` and `to_object` both give `schema_break` naming it; the twins give `None`; a missing key is named before an extra field; every schema of `types()` has `additionalProperties` false; a context-graph node keeps its fields |
| **TC-GTB-023** (Storage side: new `tests/acceptance/test_graph_node_fields.py`, staged in `amendments/A-93/`) | through the storage stand-in: the write is refused (`invalid`, `schema_break`, field), nothing is stored, the same record put past the check is refused on `to_object`; the twins are accepted. Chosen over extending TC-GTB-010/011 so no approved check changes. Scenario, row in `test-spec.md`; TR-GTB-001 applies to it (as for TC-GTB-022) |
| **T-07** in `plan.md` | schemas and `_broken_path` in `graph_tables.py` only, new failing unit tests first in `tests/test_graph_record_checks.py`; depends on T-06 and the install; table row, task text, order, size check (18 requirements, seven tasks), decision 6 |
| Generated | `architecture.sysml` requirement block regenerated after `--do` |

## Points for the owner
1. **Order of several breaks (decision 13).** A record with a missing key and an extra field needs one rule or the mock and the real code could name different fields. Chosen: the first path in text order, a missing key at the path of its object, an extra field at its own path (so a missing `toolbox_id` is named before an extra `foo`). Fixed by TC-IF-301-21. Say if you want another rule.
2. **Only the top level of the JSON field is closed.** `stop`, `parameters`, `task` and the member lists keep accepting extra keys (`task` is open by decision 6). Not asked for; a later amendment if wanted.
3. **Consequence for CONVERT (not checked here):** `from_document` puts the other fields of a v1 node flat into `data`; a converted node with a field outside its type is now refused when written. The contract already says a converted record is not checked (a `process` node has no `toolbox_id`), so nothing in G-V2.STORE changes, but the conversion goal has to map or drop such fields. I did not look at which fields real v1 workflows carry.
4. **Reviews come back.** The review log has A-92 approvals for TR-GTB-001 and `goal.md`; both change again, and REQ-GTB-022, TC-GTB-023 are new. `plausibility.yaml` is protected and untouched: REQ-GTB-022 needs a rating (one rule, no number; the reference is the 10-line change measured in scratch, below).
5. F-05 (`plausibility.yaml` differs from the tag) is not touched by A-93 or A-94.

## Checked by the drafter (scratch copies of the worktree; nothing installed in the repository)
- `--do` run twice: the second run changes nothing (checksums of `specs/`, `contracts/`, `tests/` identical). From the repository state with the A-92 doubles still in, and after A-94, with identical results in both orders.
- After `--do`: `check_sysml` 0 errors; `trace_check` 517 errors = the known baseline, none for REQ-GTB-022, TC-GTB-023, TC-IF-301-21; `req_lint` no warning for REQ-GTB-022 (33 words).
- Red for the right reason before T-07: `TC-IF-301-21_real` ("None != schema_break foo"), TC-GTB-023 ("StorageError not raised"); `TC-IF-301-21_mock` and all other suites green.
- Satisfiable: a throwaway patch of `graph_tables.py` in the scratch copy (three schemas plus `_broken_path`, about 10 lines) turns the contract suite (34 cases), TC-GTB-023, `test_graph_records.py` (with TC-GTB-014 at N = 1000), `test_graph_record_identity.py`, `test_graph_record_checks.py`, `test_graph_tables.py`, `test_storage.py`, `test_graph_record_objects.py` and `test_graph_document_form.py` all green. That patch is not in the repository; T-07 writes the real one, test first. `test_storage_postgres.py` was not run (needs a throwaway postgres:16).

## Install (after the look-only review)
```
bash tools/apply_amendment_a93.sh --report     # look only
bash tools/apply_amendment_a93.sh --do         # install; then commit "plan: A-93 installed"
```
Then T-07 in a fresh Implement session.
