# Handover: G-V4, CORE implemented; next Verify (2026-11-22)

Written for the next session. Read this first, then `CLAUDE.md` of the repository and the skills `dev-workflow`, `verify-phase` and `agent-app` (CORE has no model step, prompt or eval suite, so `agent-app-verify` adds nothing beyond the base checks). The owner is Stefan Reiterer (maldun). He decides every gate; never treat an agent report or silence as approval. The previous handover is `handover-2026-11-21-g-v4-core-plan-done.md`.

**Verify is independent.** You are a fresh reviewer: verify against the plan package and the specification, not against the implementation log. The log's results are the implementer's own runs (feedback, not verification); re-run everything yourself.

## 1. Where we are
Goal **G-V4** (graph rework), subgoal **G-V4.GRAPHSTORE.CORE**: Plan done (approved 2026-11-21), **Implement done** (2026-11-22, `goal.md` Phases table), **Verify next**. The other subgoals (RULES, TRANSFER, RUN, VIEW, EDIT, REPLAY, CODE, MIGRATION, CONTEXT, BUILDER) are not started (D-401: Plan subgoal by subgoal).

| Item | State |
|---|---|
| Tasks | T-01, T-01b (new, A-168), T-02, T-03, T-04, T-05: committed |
| Amendments during Implement | A-168 (D-412; count corrected), A-169 (D-413): approved, installed |
| Round 03 sign-off | still open: `Validated by:` in `rounds/03/validation.md`, `Decided by:` in `rounds/03/prototype-report.md` (prototype worktree); the owner's |

## 2. Where everything is
- Worktree `/home/maldun/prog/Python/MIA-goal-v4`, branch `goal/v4` (not pushed; no upstream). Start of Implement: `a16465e4`. Red-test tag: `plan-baseline-g-v4-core`.
- Commits of Implement, oldest first: `f2531cc8` T-01, `cf95f544` A-168 plan, `f65548ba` A-168 staging, `3f699b70` T-01b, `dbab43a2` A-168 count, `c50e6bee` A-168 installed (protected tests), `ea6fad71` T-02, `677f8ce4` A-169, `5a2a5f47` T-03, `4147b044` T-04, `b9f50875` T-05 (log only) + Implement done. Review the code diff with `git diff a16465e4..b9f50875 -- graph_tables.py graph_model.py tests/`.
- CORE folder `specs/mia/goals/G-V4.GRAPHSTORE.CORE/`: `goal.md`, `high-level-spec.md`, `requirements.md` (22 requirements, 2 assumptions), `test-spec.md`, `test-requirements.md`, `plan.md` (with the A-168 and A-169 sections), `binding-map.md`, `review-log.md`, `implementation-log.md` (with a "Hand-over to Verify" section), `red-tests/`.
- Amendment notes: `specs/mia/amendments/A-167-note.md`, `A-168-note.md` (with the drafts in `A-168/` and `tools/apply_amendment_a168.sh`). A-169 is a plan-only change (section in `plan.md`, D-413 in `specs/mia/review-log.md`).
- Product code changed: `graph_tables.py` (scoped IDs, `unscoped_id`), `graph_model.py` (save path, read path, versions, step history, context kind). No other product file.
- Tests added (unprotected): `tests/test_graph_tables.py` (class `ScopedIds`), `tests/test_graph_model_save.py`, `tests/test_graph_model_read.py`, `tests/test_graph_model_context.py`. Test data rewritten to scoped IDs (T-01b): `tests/test_storage.py`, `test_storage_postgres.py`, `test_storage_copy_semantics.py`, `test_graph_record_objects.py`, `test_skill_record_storage.py`.
- Protected files changed in Implement, only through A-168 (installed by the owner's script): `tests/acceptance/test_graph_context_tables.py`, `test_graph_document_size.py`, `test_graph_node_fields.py`, `test_graph_record_identity.py`. Check them against `specs/mia/amendments/A-168/tests/acceptance/` and every other protected file against `plan-baseline-g-v4-core`.
- Prototype worktree `/home/maldun/prog/Python/MIA-prototype-g-v4` (`prototype/g-v4`): reference code of reuse map R1. Main checkout `/home/maldun/prog/Python/MIA`: unrelated untracked files; do not touch. `specs/mia/amendments/A-167/A-167.diff` is an untracked view file; never commit it.

## 3. Decisions since the last handover (full text in `specs/mia/review-log.md`)
- **D-412 (A-168)** T-01 stays; new task T-01b before T-02 (scoped IDs in the unprotected unit tests); four protected scripts get scoped IDs through `tools/apply_amendment_a168.sh`; "all other tests unchanged" becomes a named regression set per task. Count corrected afterwards: seven `graph_model` checks per backend of `test_skill_record_storage.py` were red until T-02/T-03.
- **D-413 (A-169)** TC-WFM-165, 166, 168, 169 read back through `read_graph`/`graph_versions` and save context graphs: their workflow halves moved from T-02 to T-03, their context halves to T-04. No requirement, check or protected file changed.

## 4. For Verify
- The plan's checks: the CORE scripts `tests/acceptance/test_core_scoped_ids.py`, `test_core_save.py`, `test_core_context_and_history.py`, `test_core_both_stores.py`, the IF-301 suites `tests/acceptance/contract/test_if_301_graph_tables.py` and `test_if_301_v2_graph_tables.py`, and `tests/smoke/smoke_core_graphs.py` (SMOKE-CORE-001). Test requirements TR-CORE-001..009 say how each must run (fault injection at every write position, both backends, fresh store per check, exact values, times present and not decreasing).
- The regression set of `plan.md` (A-168): the unit suite and every acceptance script green. `unittest discover -s tests` does not reach `tests/acceptance/` (no `__init__.py`): run each acceptance script as a script.
- Open questions the implementer left for you (implementation log, hand-over section):
  1. An explicit `"kind": None` is refused as an unknown kind; REQ-WFM-153 says only "no kind".
  2. REQ-WFM-145's clause "only the versions the headers pin" (left open in the binding map, D-411 (2)): a unit test claims to witness it; TC-WFM-163 does not.
  3. The versions of an unknown graph raise the Storage layer's `not_found`; no requirement says what should happen.
- Known, not CORE's: `tests/acceptance/test_decide_guard.py` and `test_judge_calibration.py` give no unittest result (also on `a16465e4`, G-V3.REPORT F-3).
- Unspecified behaviour you find goes back as an amendment (plan-phase), not a code fix in Verify.

## 5. Tools and checks
- Test venv `/home/maldun/prog/Python/venvs/mia312/bin/python` (psycopg 3). A full unit run takes about 8 minutes; the acceptance scripts about as long.
- PostgreSQL halves start their own `postgres:16` container per process (named `mia-core-test-<pid>`; the IF-102 and storage tests use their own names), image local, never pulled. For SMOKE-CORE-001 without the owner's server, start a throw-away container (`podman run -d --rm --name mia-core-smoke-<pid> -e POSTGRES_PASSWORD=... --tmpfs /var/lib/postgresql/data -p 127.0.0.1::5432 docker.io/library/postgres:16`), pass `--server postgresql://postgres:<pw>@127.0.0.1:<port>/postgres`, and remove that container by its name. **Never** remove other containers: the owner's `mia_*`, `ollama`, `mia-searxng` run on this host. The smoke run on the owner's own server belongs to Deploy.
- `trace_check.py` and `binding_check.py` do not see a subgoal's parent records: run them on a temporary folder with symlinks (the CORE `*.md` files + `specs/mia/architecture.sysml`). Measured this way on 2026-11-22: 30 errors, 630 warnings; the same 30 errors on `a16465e4` (they come from other features' tests: number gate, eval harness, stability, TD-16/22/62). The previous handover reported 0 errors for this check; that could not be reproduced on `a16465e4` either.
- `test_doc_check.py --tests-dir <folder>`: copy the files to check into a folder of their own; on the five T-01b files it reports 33 errors before and after (old tests without `Example:` lines).
- Scratch worktrees for experiments: `git worktree add --detach <job tmp>/<name> HEAD`, remove with `git worktree remove --force` afterwards.
- Next free numbers (check master and the other branches first): D-414, A-170, TC-GTB-037, TC-WFM-179, REQ-WFM-162, REQ-GTB-033, AC-CORE-23, TC-IF-301-27.

## 6. Working rules (the owner's preferences)
- Decisions as a questionnaire (AskUserQuestion), recommended option first; reviews by thematic group (D-407), close look where users feel it (GUI), backend conventions little.
- Never sign for the owner: `[ ]` boxes, `Validated by`, `Decided by`, `Reviewed by`, `Verified by` stay empty until he ticks or says so; record how he said it.
- Name files by full path; privacy is no concern (personal use), untrusted web text still is.
- Commits end with the Co-Authored-By line of the session; name paths in every `git add`; never commit another session's changes; protected files change only through the owner's amendment scripts (writing staging copies under `specs/mia/amendments/A-nnn/` needs his approval when prompted).
- Leave files alone while the owner may have them open in Emacs.
