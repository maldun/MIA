# A-102: a size limit for documents and records (G-V2.STORE, F-22)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a102.sh` is not yet run with `--do` in the repository.

## Finding (found by the T-11 agent, reproduced by the drafter)
A Python-built document that shares sub-objects (31 levels, the same child twice per level, 2**30 paths, no cycle) makes `graph_tables.check_record` run for minutes. Cause: the real `_too_deep` walks level by level and builds the whole list of each level, which doubles per level. Through `Storage.put` the same input reaches `check_record` (after Storage's own linear walk). Only Python callers can build it: `json.loads` creates distinct objects. Even with a fixed checker the backend would have to serialise the expanded document.

## Owner's decision (2026-11-08)
Add a size limit (A-102 and T-12), not only a checker fix.

## What A-102 contains
| Part | Content |
|---|---|
| **REQ-GTB-028** (N-3.2, Draft, TY, Parent FR-40) | "If a record has more than 100,000 values, counting a value once for every path that reaches it, then the Graph tables shall refuse it as `schema_break` naming `data`." Check TC-GTB-029 |
| **REQ-SLY-015** (N-3.1, Draft, Parent REQ-SLY-004) | the same for the Storage layer: refused as invalid (graph tables `schema_break`/`data`, other tables `schema`/`too large`), the 2**30-path document within one second. Check TC-SLY-014 (in `tests/test_storage.py`, T-12) |
| **IF-301 v2** | size bullet in the section "Context graph tables", golden 21, decision 16, version row (v2 is not merged: stays v2) |
| **Checks** | TC-GTB-029 (new `tests/acceptance/test_graph_document_size.py`, staged in `amendments/A-102/`), TC-IF-301-24 in the contract suite (mock and real), TR-GTB-001 applies to TC-GTB-029 |
| **Protected files changed** | the mock (`MAX_VALUES`, the walk counts values and stops at 100,001) and the contract suite (case TC-IF-301-24, `import threading`) |
| **plan.md** | task T-12 (storage.py, graph_tables.py `_too_deep`, tests in `tests/test_storage.py`), counts, order, decision 10 |
| Generated | `architecture.sysml` requirement block regenerated after `--do` |

## The number: 100,000 values
Probe of 202 JSON and YAML files in `library/`, `skills/`, `eval/`, `specs/` and `tests/`: the largest stored document is `library/pipelines/research.escalate/3.json` with 529 values (the larger files are spec files, not stored documents). 100,000 is about 190 times that; the check costs a few milliseconds at the limit. The count includes the record or document, every object, list and scalar; a value reached by two paths counts twice. Say if you want another number.

## Points for the owner
1. **Install only when T-12 is next:** the real side of TC-IF-301-24 and TC-GTB-029 are red until T-12 (as for A-98).
2. **A long text is one value.** A memory with a megabyte of text counts as one value, so the limit does not restrict text size; only the number of values.
3. **A document of exactly 100,000 values is allowed;** the boundary is exact on both sides in the checks (99,995 numbers in a data node value are 100,000 values, 99,996 are 100,001).
4. REQ-GTB-028 and REQ-SLY-015 need review and plausibility ratings (A-103, after your ratings).
5. `trace_check` shows 520 errors after `--do` (519 before): the new one is TC-SLY-014 "no test requirement applies", the same known error as for the other TC-SLY checks (N-3.1 has no test-requirements file).

## Checked by the drafter (scratch copy; nothing installed in the repository)
- `--do` twice: the second run changes nothing (checksums identical); 437 node requirements; `check_sysml` 0 errors; `goal_check` no findings; trace 520 as in point 5.
- `_mock` side of the contract suite and the old checks green; TC-GTB-029 red before T-12 (the record over the limit is accepted and the 2**30-path record gets no answer within 5 s).
- Satisfiable on the graph side: a throwaway fix of `_too_deep` in the scratch copy (one function) turns TC-GTB-029, the whole v2 contract suite (mock and real), `test_graph_context_tables.py`, `test_graph_records.py` and `test_graph_record_checks.py` green. The Storage side (REQ-SLY-015) is T-12.

## Install (after the look-only review; T-12 follows in a fresh Implement session)
```
bash tools/apply_amendment_a102.sh --report     # look only
bash tools/apply_amendment_a102.sh --do         # then commit "plan: A-102 installed"
```
