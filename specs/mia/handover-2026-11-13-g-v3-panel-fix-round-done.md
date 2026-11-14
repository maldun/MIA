# Hand-over (2026-11-13): G-V3.PANEL fix round T-11 done, second Verify run is next

For the session that continues **G-V3**. Start with `CLAUDE.md`, then this file. It replaces the PANEL part of `handover-2026-11-12-g-v3-panel-verify-chat-t03.md` (that file stays valid for the CHAT line). Nothing is pushed (push and merge are the owner's). The owner decides every approval by questionnaire (`AskUserQuestion`, recommended option first). Commit with `git add <paths>` and `git commit -m ... -- <paths>`, messages end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Python for every test: `/home/maldun/prog/Python/venvs/mia312/bin/python`. Work only in the worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v3` (branch `goal/v3`, HEAD `cdca767`, clean).

## State of G-V3.PANEL
First Verify run (2026-11-12) said **Not verified** (`goals/G-V3.PANEL/verification-report.md`, findings F-01 to F-12). Since `ad454f6` there are 25 commits (`git log --oneline ad454f6..HEAD`). Every finding has a destination now:

| Finding | Result | Where |
|---|---|---|
| F-01 lost answers (no lock) | fixed, `RLock` in `skill_runs.py`; test `tests/test_skill_runs_race.py` (0 of 30 answers kept before, 30 after) | `92075cb` |
| F-02 storage error in `_emit_status` | fixed; `tests/test_emit_status_storage_error.py` (fix written before the test, then reverted once to see it red) | `92075cb` |
| F-03 broken `%` in `#run=` | fixed, `runOfHash` moved to `skill-run-model.js`; JS test | `92075cb` |
| F-04 other account's run is a 404 | A-145: TC-IF-101-40, the IF-101 mock checks the account | payload `contract-change-5`, installed `876475e` |
| F-05 TC-CLV-036 measured the summary | A-146: browser driver measures `.srv-full-body`; the CSS mutant (limit 1.6 times) is now killed | `48b386a` (no payload: `tests/browser/` is not protected) |
| F-06 mutant gaps M02, M04, M11, M12, M20, M21, M22 | `tests/test_skill_run_gaps.py` (7 tests, each mutant killed by hand) | `a02fd5f` |
| F-07 model | A-147: skill-run files in `architecture.sysml`, `skillRunStore` is `built` with `skill_runs.py` and `skill_run_observer.py` | `9b644ec` |
| F-08 one history record deletes all runs of the author | A-144: deletes the run whose id is the id of the history record (owner confirmed: history id = run id); code `90823b9`, text in REQ-WFM-135, TC-WFM-135, sysml, `run-recorder-interface.md` (`e7014a6`), tests by payload `contract-change-5` | see left |
| F-09 manifest `phases` | fixed in `read_manifest`; test in `tests/test_extension_loader.py` | `92075cb` |
| F-10 run left `running` after a crash | owner: backlog; **TD-81** in `deferred.md`, signed off 2026-11-13, trigger Validate of G-V3 or 2026-12-31 | `aab21c4`, `e7780d0` |
| F-11 REQ-FE-032 without a check | A-148: REQ-FE-032 in Verifies of TC-CLV-030 (`req_graph` reads that column, not "Verified by") | `9fdbf69` |
| F-12 `Example:` line | fixed | `92075cb` |

Decisions: D-331 in `review-log.md` (owner 2026-11-13) with approval rows for REQ-WFM-135, TC-WFM-135, TC-CLV-030; A-144 to A-148 notes say "approved ... D-331"; `goals/G-V3.PANEL/owner-decisions-2026-11-13.md`.

**Renumbering against master (owner: master keeps its numbers).** G-V3's D-304 to D-309 are now **D-332 to D-337** and its amendment A-143 (elements in the run record, IF-302 v9, IF-101 v17) is now **A-149** (`amendments/A-149-note.md`), commit `2263233`; the protected files followed by payload `contract-change-6` (`c8fce44`). Installed payload copies (`payload/` folders, `contract-change-2/install.py`) were left as installed history and still say D-306 and A-143. `python3 -I tools/check_d_numbers.py` (new, `585f6c4`) lists the highest D-number per line of work, the next free number (**D-338**) and collisions; it still lists D-304 to D-309 because `goal/v3.chat` has the old numbers (see below), plus two old harmless ones (D-103, D-182).

**Payloads of this round (all installed by the owner):** `goals/G-V3/contract-change-5` (A-144 and A-145: TC-WFM-135, TC-IF-101-39 and -40, `delete_history(account, run_id)` in the real adapter and the IF-101 mock, the mock checks the account), `contract-change-6` (renumbering in `contracts/`, `plausibility.yaml`, one docstring), `contract-change-7` (Given/When/Then comments in TC-IF-101-39 and -40, `00cc992`). Built in sandbox copies; the protected files were never edited in the repository.

## Checks at HEAD (2026-11-13)
- Full unit suite alone: 2075 tests, one error, the known `test_tailscale`. **Never run two full suites at the same time**: they share the checkout and `test_checkout_untouched` then fails (it did, twice).
- JS 164 pass; contract suites IF-101 (78, 2 skips as before), IF-302, IF-102 green; browser suite 12 tests, three runs, no flip; restart test OK; PostgreSQL: `tools/contract_postgres.sh` 12 OK and `tests/test_storage_postgres.py` 26 OK.
- `check_sysml_model.py` no problems, `check_sysml.sh` 0 errors on 4 models; `req_graph` 26 errors (REQ-FE-032 gone); `test_doc_check` 2658 (tag 2659); `req_review status`: only TC-WFM-047 and TR-MODEL-003 changed (G-V2.MODEL's); `goal_check`: GL1 (D-271) and GL11 (G-V3.CHAT), known.
- `trace_check` **547 errors, tag 545**: both extras are TD-81 (`REQ-CLV-034 does not carry 'Relaxed: TD-81'` and `has no 'Target'`). The owner chose to **leave them** until a requirement change is approved. The proper fix is a `Relaxed:`/`Target:` pair on the requirement TD-81 names (REQ-CLV-038 was the recommended one, then TD-81's id list moves into its text).

## Next, in order
1. **Second Verify run:** paste `specs/mia/goals/G-V3.PANEL/verify-brief-run2.md` into a fresh reviewer agent (it names the changes since the first report, the regression places to inspect, the mutants to rerun, the facts above). The reviewer writes only `verification-report-run2.md` (finding ids from F-13). **Earlier fix rounds each brought one regression found by the next Verify run**: expect one here.
2. Fix round from run 2 if needed (test first, from the reviewer's probe). The first run's probe scripts are gone (their scratchpad is deleted); my F-01 and F-02 tests are reconstructions.
3. Owner accepts or rejects remaining low findings as deviations; verdict "Verified with accepted deviations" needs an approval row in `review-log.md`.
4. **Commit phase** (`commit-phase` skill): merge master into `goal/v3`, checks, merge request draft; the owner merges; status updates on a branch of their own.

## Open for the owner
- TD-81 link: add `Relaxed: TD-81` and `Target:` to a requirement (a requirement change) or accept the two `trace_check` errors.
- **CHAT line (`goal/v3.chat`, worktree `goal-v3-chat`)** is not renamed: its review-log rows and files still use D-304 to D-309 and A-143. Apply the same mapping there (script idea: the throwaway `renumber.py` used here maps D-304..309 to D-332..337 and A-143 to A-149 over tracked files, protected files by payload; it lives in the scratchpad of this session and is not kept; rebuild it from this paragraph). Also pending there: `contract-change-4` install (the real adapter of IF-201), then T-04 to T-06 (see the 2026-11-12 hand-over).
- The two branches merge into one line later: order and who resolves the generated `architecture.sysml` block; `CHANGELOG.md` `[Unreleased]` will collide with master's.
- VAL-012 / VAL-013 are Validate items; `deferred.md` TD-01 still names the superseded REQ-CLV-023.

## Pitfalls met in this stretch (keep)
- The permission classifier refuses a command that edits a protected file in place, even briefly. Build payloads from a sandbox copy (`rsync` the worktree without `.git` into the scratchpad, edit there, `git diff --no-index a b` with the `a/` `b/` prefixes fixed by `sed`, check with `git apply --check`, run the suites in the copy), and give the owner an `install.py` (copy from an earlier `contract-change-*`).
- `trace_check` and `req_graph` read the Verifies column of the test-spec, markers and TD blocks; they do not read "Verified by" lines.
- A background command whose first line fails can leave the rest not run: check that a commit really happened (`git log -1`) before relying on it.
- Doc check for new tests: docstring with an `Example:` line and Given/When/Then comments (T1 to T3).
- The review log: add a decision row after D-309's old place (now D-337) and approve changed items with `req_review.py mark --by maldun --result approved --note ... <ids>` only after the owner's answer.
