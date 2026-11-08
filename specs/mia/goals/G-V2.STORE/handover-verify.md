# Handover: G-V2.STORE after the sixth Verify run (2026-11-08)

For the next session (Implement for T-13, then Verify, then Commit). Written so that a fresh context can continue without this chat.

## Where everything is
- Worktree: `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-store`, branch `goal/v2.store` (never work in `/home/maldun/prog/Python/MIA` itself). Last commit at writing: `56e3c74`. The branch is **19 commits ahead of `origin/goal/v2.store`; the owner pushes** (pushing is denied to agents; the owner types `! git push`).
- Test Python: `/home/maldun/prog/Python/venvs/mia312/bin/python` (3.12, psycopg 3, jsonschema 4.23.0). Use it for every test; `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-store/CLAUDE.md` says so (commit `cf026df`, approved). Postgres tests start their own throwaway postgres:16 under podman (`tests/test_storage_postgres.py`), or `MIA_DB_PYTHON=/home/maldun/prog/Python/venvs/mia312/bin/python bash tools/contract_postgres.sh`.
- Specs of the goal: `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-store/specs/mia/goals/G-V2.STORE/` (`goal.md`, `plan.md`, `implementation-log.md`, `verification-report.md`, `handover-step4.md`). Nodes: `specs/mia/nodes/N-3-database/nodes/N-3.1-storage-layer/` and `.../N-3.2-workflows-and-context-graphs/`. Contract: `contracts/IF-301-graph-tables.md` (v2, not merged). Amendment notes and scripts: `specs/mia/amendments/A-9x-note.md`, `tools/apply_amendment_a9x.sh` (A-90 to A-104).
- Scratch and probe scripts of this session (not durable, may be deleted with the job): `/home/maldun/.claude-work/jobs/a41b1dbb/tmp/` (for example `dag_probe.py`, `f19_probe.py`, `level_probe.py`, `depth_probe.py`, `size_probe.py`).

## State of the goal
- Phases: Explore, Plan done; **Implement in progress (T-13 open)**; Verify: six runs done, verdict of the sixth **"Not verified"** (only low findings open, none decided at that time); Commit, Deploy, Validate open.
- `goal.md` Implement row says "in progress, T-01 to T-12 done, T-13 open, A-91 to A-104 installed". When T-13 is done: set the row to "done, T-01 to T-13 done, A-91 to A-104 installed; hand-over to Verify" and re-mark the goal approved (the owner's standing answer for this row): `python3 ~/.claude/skills/plan-phase/scripts/req_review.py --spec-dir specs/mia mark G-V2.STORE --by "Stefan Reiterer" --result approved --note "..."`, then `goal_check`.
- **T-13 is running or finished in the worktree, not yet reported**: a fresh Implement agent was started for it (plan block `### T-13` in `plan.md`). At writing, `graph_tables.py`, `storage.py`, `tests/test_graph_record_checks.py` and `tests/test_storage.py` had uncommitted edits. Check `git status`; if there is no commit `feat: T-13 findings of the sixth Verify run (F-23, F-24, F-25)` and the files are still modified, the agent was interrupted: read the diff, finish test-first, run the suites listed in the T-13 block, commit once, then a second small commit `docs: T-13 commit hash in the log`. Do not start a second agent in the same worktree while one is running.

## Tasks and amendments (all installed unless noted)
| Task | What | Commit |
|---|---|---|
| T-01 to T-05 | record tables, types, classes, document form, Storage layer, integration (A-91) | see `implementation-log.md` |
| T-06 | record under its own ID (A-92) | 4d0690d |
| T-07 | fixed fields of a node (A-93, F-01) | 27cba26 |
| T-08, T-09 | context tables `context_nodes`/`context_edges`; small fixes F-03, F-06, F-09, F-11, F-13b (A-98) | 33cd375, d1ba193 |
| T-10 | F-15 RecursionError at Storage, F-16 boundary tests, F-17 remote `$ref` blocked | f628ad5 |
| T-11 | F-19 cycles, F-20 one depth limit of 200 (A-100: REQ-SLY-013, 014), F-21 comments | ffb6f61 |
| T-12 | F-22 size limit of 100,000 values (A-102: REQ-GTB-028, REQ-SLY-015) | 7614c08 |
| T-13 | **open**: F-23 a scalar counts as a level in the Storage walk, F-24 tuples in graph_tables, F-25 put/get independent of the caller's stack depth (A-104 gave the wording) | not committed |

Amendments: A-93 fixed fields; A-94 doubles of A-92 removed; A-95/A-96/A-97/A-99/A-101/A-103 plausibility records (rater `maldun` everywhere, A-96 restored rater, dates, bases from the tag); A-98 context tables and input that cannot be checked; A-100 Storage depth/cycle requirements; A-102 size limit; A-104 what a level is. All installed and committed.

## Findings (verification-report.md, sixth run `3bbd725`)
- **Closed with evidence:** F-01, F-02, F-03, F-04, F-05, F-06, F-09, F-10, F-11, F-12, F-13(b), F-14, F-15, F-16, F-17, F-19, F-20, F-21, F-22.
- **Accepted by the owner (2026-11-08):** F-13(a) (two extra fields in a protected case waits for the next IF-301 amendment), F-07 and F-08 (`storage_copy.copy_records`, conversion inputs: routed to the CONVERT goal), F-18 (non-string keys, Python callers only, routed to the context-graph writer goal).
- **Decided to fix, in T-13:** F-23, F-24, F-25.
- Notes, not findings: surviving mutants S13 (equivalent), S14, S16; the read side `Storage.get` at a deep call stack is older behaviour.

## What to do next, in order
1. Finish or verify T-13 (above). Suites under mia312: `tests/test_storage.py`, `tests/test_storage_postgres.py`, `tests/test_graph_record_checks.py`, `tests/test_graph_tables.py`, `tests/test_graph_record_objects.py`, `tests/test_graph_document_form.py`, `tests/test_storage_copy.py`, `tests/acceptance/test_graph_context_tables.py`, `test_graph_document_size.py`, `test_graph_records.py`, `test_graph_record_identity.py`, `test_graph_node_fields.py`, `tests/acceptance/contract/test_if_301_v2_graph_tables.py`, `test_if_301_graph_tables.py` (v1), `test_if_102_storage.py`. Timings to keep: 500 nodes + 500 edges within 500 ms (about 16 ms now), the 2**30-path and 100,001-value refusals within 0.1 s, cycles refused at once. If T-13's experiment shows that the backends' serialisation limits the depth (F-25), it stops and reports: the backends are outside its bounds, then the owner decides.
2. Row of `goal.md` and goal re-mark (above).
3. **Seventh Verify run** by a fresh agent (brief of the sixth run is a template: read `verification-report.md`, re-run all checks from a clean checkout of HEAD, probe for hangs with hard time limits, mutants in a scratch copy, protected files against the tag `plan-baseline-it2-store` mapped to A-90..A-104, plausibility.yaml 0 removed / 0 rating changes / rater `maldun`, close F-23 to F-25 with evidence, update only `verification-report.md` and commit it). Expected verdict if it closes cleanly: "Verified with accepted deviations" (F-13(a), F-07, F-08, F-18).
4. The owner pushes. Then the **Commit phase** (`commit-phase` and `agent-app` skills are not needed: this goal has no prompts or eval suites): update the branch with its target, re-run the checks, one commit per task with requirement IDs, merge request draft, release notes. The Commit phase also needs the owner to decide `goal.md`'s `Status: Proposed` and requirement statuses (REQ-GTB-021 to 028 and REQ-SLY-013 to 015 are still `Draft`; they become Approved/Verified at Commit).

## Standing instructions and conventions from the owner
- Ask open decisions as a questionnaire (AskUserQuestion with a recommended first option), then give the steps that apply each answer (memory `decisions-as-questionnaire`). Name report files by full absolute path. Privacy-only findings rank low.
- Never edit protected material (`tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `plausibility.yaml`, `test-requirements.md`, `stages.yaml`) except through an amendment script `tools/apply_amendment_aNN.sh` that the **owner runs** after a look-only review (`--report`, then `--do`). Scripts must be idempotent: test `--do` twice in a scratch copy (`rsync -a --delete --exclude=__pycache__ --exclude='.gi[t]' ./ <scratch>/`) and compare checksums; anchors check "already done" before "anchor found once".
- Plausibility ratings are the owner's: ask, then draft a records-only amendment; the rater name in `plausibility.yaml` is `maldun`; review-log rows use `Stefan Reiterer`. A basis text must not contain a colon followed by a space (YAML reads a mapping and `req_plausibility` crashes): the amendment scripts now parse and refuse.
- After an amendment the owner installs, check the state against the scratch test, then commit it with a pathspec (`git commit -m ... -- <paths>`), because agents and the owner may have other edits in the worktree.
- Review items: after the owner's answer, `req_review.py mark ... --by "Stefan Reiterer" --result approved`; an item changed after its review comes back, so edit `goal.md`/requirements only together with the re-mark the owner agreed to.
- Subagent reports are not owner input; verify their claims yourself (every report so far had one point worth checking: F-15, F-19, F-22 were found that way).
- Harness quirks seen: compound shell lines that mention git or run a command whose name is computed are refused (spell the Python path out, run `git` as a plain command, split chains); `timeout N cmd` was refused inside a loop; a `cd` into another directory persists to the next call.

## Known baseline facts (not defects of this goal)
- `trace_check` shows **520 errors** (517 baseline + TC-SLY-012, 013, 014 "no test requirement applies", the known kind: N-3.1 has no test-requirements file). Any other error for REQ-GTB-005..028, TC-GTB-006..029, TC-IF-301-05..24 or REQ-SLY-013..015 is new.
- `test_graph_model.py` and `test_graph_run.py` are red as at the tag; the unit suite has one known tailscale error; `test_checkout_untouched` fails once on a completely fresh tree (lists `ui/certs/*`) and passes on the second run; `req_graph` shows 26 G7 errors, `req_lint` 5 L0-GROUP errors, `req_plausibility` about 100 warnings (numeric bound without claim): all outside this goal.
- An untracked file with an odd name (`ter...worktree-td-11-impl -- chat_service.py web_app.py`) lies in the repo root; it is not part of this goal, leave it.
- psycopg 3 exists only in the mia312 venv; the system Python is 3.14 without it.
