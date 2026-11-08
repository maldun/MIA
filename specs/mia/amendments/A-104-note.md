# A-104: what a level is, and task T-13 (G-V2.STORE, F-23, F-24, F-25)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a104.sh` is not yet run with `--do` in the repository.

## Findings (sixth Verify run, `3bbd725`) and the owner's decisions (2026-11-08)
| Finding | Decision |
|---|---|
| **F-23** (low, spec gap): a scalar counts as a level in the protected mock (since A-98) and in the real graph code, but the Storage layer counted containers only, so a scalar in the 200th object was stored for `workflows` and refused for graph tables | **clarify the wording, a scalar counts everywhere** (this note; the code follows in T-13) |
| **F-24** (low, Python callers only): the Graph tables do not treat tuples as containers (`check_record` accepts a record that contains itself through a tuple; `to_object` hangs on a DAG of tuples, raises `RecursionError` on a tuple nested 5000 deep) | **fix now**, T-13 |
| **F-25** (low): a legal 200-level document is refused as `nested too deep` when `put` is called from about 600 frames of caller stack; `get` at 600 frames raises a raw `RecursionError` | **fix now**, T-13 |

## What A-104 contains
| Part | Content |
|---|---|
| **REQ-GTB-027** (N-3.2) | the acceptance criterion says what a level is: a deepest value (object, list or scalar) at level 200 is accepted, at level 201 refused; the record is level 1 and every value below it one level deeper than its parent. The requirement text does not change |
| **REQ-SLY-013** (N-3.1) | the same wording in its acceptance criterion |
| **IF-301 v2** | one bullet "What a level is", which also says that the Storage layer counts the same way and that a tuple counts like a list |
| **plan.md** | task T-13, counts (thirteen tasks), order, decision 11 |
| Generated | `architecture.sysml` requirement block regenerated after `--do` |
No protected test, mock or helper changes: the real graph code and the mock already agree with the wording (probe by the drafter: an empty object, an empty list and a scalar at level 200 are accepted, at level 201 refused).

## What T-13 will do (code, not in this script)
- F-23: the Storage walk counts a scalar as a level, so documents behave the same for graph tables and other tables; boundary tests with an empty object, an empty list and a scalar at level 200 and 201 (kills the surviving mutant G6).
- F-24: `_too_deep`, `_non_finite_path` and the copy in `to_object` treat a tuple like a list; tests for a tuple cycle, a tuple DAG and a deeply nested tuple, each within one second.
- F-25: `put` and `get` of a 200-level document work from a call stack 700 frames deep; if the experiment shows that the backends' own serialisation is the limit, T-13 stops and reports (the backends are outside its bounds).

## Points for the owner
1. The wording change reopens the review of REQ-GTB-027 and REQ-SLY-013 (acceptance criteria changed). After the install they come back in `req_review.py`; I mark them once you say so.
2. **One behaviour change in the Storage layer comes with T-13:** a legal document of a non-graph table whose scalar sits in the 200th object (level 201) is stored today and will be refused. None of the 1357 JSON/YAML files in the repository is near it (deepest 18 levels).
3. Install A-104 when T-13 is next; T-13 depends on it. The goal row stays "done" until T-13 is open; I set it to "in progress" and re-mark it when you tell me A-104 is installed.

## Checked by the drafter (scratch copy; nothing installed in the repository)
- `--do` twice: the second run changes nothing (checksums identical); `check_sysml` 0 errors; `goal_check` no findings; `trace_check` 520 (unchanged).

## Install
```
bash tools/apply_amendment_a104.sh --report     # look only
bash tools/apply_amendment_a104.sh --do         # then commit "plan: A-104 installed"
```
