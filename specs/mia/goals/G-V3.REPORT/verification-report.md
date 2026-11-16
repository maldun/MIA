# Verification report: G-V3.REPORT (a report at the end of every skill run)

**Goal:** G-V3.REPORT (subgoal of G-V3), supervised
**Branch:** goal/v3.report @ af366cd2 (checked out as verify/g-v3-report)   **Parent line of work:** goal/v3 (master merged in)   **Plan baseline:** plan-baseline-g-v3-report
**Date:** 2026-11-16/17   **Reviewers:** an independent AI reviewer (Sonnet 5.5, fresh context, never saw the implementation); a person has not yet read this report

## Verdict
**Verified with accepted deviations (proposal)**, on condition that the owner decides the findings below. Every in-scope check is green under its test requirements, the protected material is unchanged except the documented installs, and no failure is new against master. No finding is a security hole of the page. One finding (V-1, medium) is a real functional defect of REQ-WFM-139/140 and should be fixed (Phase 3, one regression test) or accepted by the owner before the merge; V-2 (medium) is a letter-of-the-requirement gap of REQ-WFM-141 outside the page.

## Automated checks (everything run by me, in this worktree, in the foreground, one run at a time)
| Check | Result |
|---|---|
| JS: `node --test "tests/js/*.test.mjs"` | tests 177, pass 177, fail 0 |
| Acceptance scripts, one by one (54 scripts, python of the mia312 venv) | 51 exit 0. Exit 1: `test_decide_guard` (ImportError: relative import, no result), `test_judge_calibration` (same ImportError), `test_skill_snapshots` (Ran 8, failures=8). The same three fail identically on master (checked, see below). `test_if_101_chat_api`: Ran 82, OK (skipped=2). `test_skill_run_report`: Ran 5, OK |
| Browser file `tests/acceptance/test_skill_run_view_browser.py`, alone | Ran 16 tests in 53.8s, OK (the four new checks TC-CLV-048, 050, 051, 052 included; the flaky shares check F-5 passed) |
| Unit suite, `unittest discover -s tests`, in pieces (the 10 min limit, and because the harness moves long foreground commands to the background): `test_[a-c]*` Ran 657, FAILED (failures=7, errors=1); `test_[d-m]*` Ran 489, FAILED (failures=4, expected failures=1); `test_[n-r]*` Ran 565, OK (skipped=2); `test_s[a-gi-z]*` Ran 419, OK (skipped=3); `test_sh*` Ran 20, OK; `test_[t-z]*` Ran 269, FAILED (failures=2, expected failures=1) | Sum 2419 tests, 13 failures + 1 error: test_control_entries (1 error, 3 failures), test_converted_tools (2), test_core_converted (2), test_harness_converted (4), test_task_files_browser (2). Nothing else. `test_shutdown*` (foreground): 20 OK |
| The same failures on master (clean extra worktree at master 440e599b, removed afterwards; same chunks) | `[a-c]` Ran 657, failures=7, errors=1; `[d-m]` Ran 489, failures=4; `[t-z]` Ran 269, failures=2 (the two test_task_files_browser tests); acceptance `test_skill_snapshots` failures=8, `test_decide_guard` and `test_judge_calibration` exit 1. Identical test names: **the brief's claim is confirmed, none of the 14 is ours** (the other chunks were not repeated on master, they pass here) |
| Protected material vs. baseline | see "Protected material" below: only A-155 and the browser payload |
| `trace_check.py --spec-dir specs/mia --tests-dir tests` | 587 `| ERROR |` rows, the same number on master. Nothing names an item of this goal as an error. One WARN names `REQ-CLV-049`: "verified by test, but no @pytest.mark.req marker found" (the marker is `mark.req("REQ-CLV-048", "REQ-CLV-049")` and `mark.req("REQ-CLV-052", "REQ-CLV-049")`, the script apparently reads only the first argument; the unit tests of the renderer are marked with the id in a title). Low, see V-9 |
| `goal_check.py --spec-dir specs/mia` | 2 errors (GL1 G-V2/G-V3 two open iteration goals; GL3 G-V2.TOOLBOX IF-302), 1 warning (GL11 G-V3.CHAT): identical on master; none names G-V3.REPORT |
| `tools/check_sysml_model.py` | OK (40 acceptance criteria) |
| `tools/check_sysml.sh` | 4 files, 0 with errors, 0 with warnings (71 s) |
| Architecture rules | `satisfy` links exist for REQ-WFM-139, 140, 141 (taskRuntime) and REQ-CLV-048 to 052 (frontEnd) in `specs/mia/architecture.sysml`; glossary has "Run report". `run_report.py` is a new module without its own part in the model (the plan allowed this: "only if a part changes"); see V-10 |
| Static and security: a linter, bandit or a dependency audit are not configured in the repo (CLAUDE.md: no lint, formatter or type checker); no dependency was added (`git diff --name-only` shows no requirements file); I read the code and probed it instead (below) | done by hand |
| Refactoring commits, agent configuration, release_check, deployable build, mutation tests | not applicable / not run: no `refactor:` commit in the range; no agent configuration file (`.claude`, skills) changed; Deploy is `empty` for this goal; no mutation test run (the log reports two mutants per task; I did not repeat them). Not run is not a pass |
| Hand check of `/lookup` against the running MIA (model server and SearXNG) | **not run, needs the owner** (services must not be started by me). It stays the Validate item of the goal |

Environment caveat: another session ran a full `unittest discover` in the main checkout at the same time during my first unit chunks (visible in the process list); my chunk a-c took 227 s instead of about 120 s. All chunks passed or failed exactly as on master, so I count the results, but they were not under quiet conditions.

## Protected material
`git diff plan-baseline-g-v3-report..HEAD -- tests/acceptance tests/helpers tests/smoke contracts benchmarks specs/mia/test-requirements.md` changes exactly three files:
- `tests/acceptance/contract/test_if_101_chat_api.py` (14 lines): TC-IF-101-30 and -35 and the docstring example of TC-IF-101-41 only = A-155 (`amendment-a155/note.md`, commit acd49fb3). Matches the note: the files list holds the skill's file and then the run report; no tolerance loosened (the assertions are as strict, `files == ["review-contract.md", record["report"]]`).
- `tests/helpers/mocks/if_101_chat_api.py`: every ended run gets a report file after `chat_done` (A-155; the mock follows the real service).
- `tests/acceptance/test_skill_run_view_browser.py`: four new tests (TC-CLV-048, 050, 051, 052 browser half) = the browser payload (`plan-step4b/protected.patch`), plus the new scenario names.
`tests/smoke`, `contracts`, `benchmarks`, `test-requirements.md`: no change. No `skip`/`xfail` was added in the acceptance tests of the range. Result: **no unexplained change**. Not protected but touched, and checked: `tests/browser/skill_run_view.py` (scenarios of the payload, see V-6), `tests/test_chat_tasks.py` and `tests/test_review_chain.py` (adapted to "one more file, the report": assertions kept, counts changed, legitimate), the stand-in server `ui/tools/skill_run_stub_server.py` (the two steps of the interface note).

## Verification matrix
Test requirements: TR-PANEL-001 fixed window sizes (browser driver `browser(size=(1440, 900))`, theme and size fixed; `--window-size` in the driver), 002 stand-in skill (the scripted skills and the stub server know nothing of the view), 003 fake storage (FakeSkillRunStorage, real FileStore in a temporary folder), 005 hostile strings (the five fixed strings are in the unit, acceptance and browser checks), 006 exact values (assertEqual on names, states, counts). All of them were applied as written in the checks I ran; the browser checks ran alone.

| Requirement | Method | Evidence (run by me) | TR met | Result | Plausible? |
|---|---|---|---|---|---|
| REQ-WFM-139 every run ends with a report | Test | TC-WFM-139: `test_skill_run_report.py` 3 tests OK (done, stopped, failed; scripted run without report and output says "no output"); unit `test_lookup_report`, `test_review_report`, `test_search_report` (the three real skills, scripted) OK in the unit chunks; my probe p2 (done, failed with own report, no output) | 002, 003, 005, 006 | **Pass with V-1**: a question with one very long word gets no report at all | yes (a test that fails if the report is missing was seen in the mutants of the log; I confirmed the first-line text by probe) |
| REQ-WFM-140 record names the report | Test | TC-WFM-140 (1 test), TC-IF-101-41, -42 real and mock variants in `test_if_101_chat_api.py` (82 OK), TC-IF-302-08 (`test_if_302_record_tables` 20 OK) | 002, 003, 006 | Pass (same V-1: field stays null) | yes |
| REQ-WFM-141 addresses and texts | Test (red team) | TC-WFM-141 (1 test, done and failed as sub-tests), `test_search_report`, `test_review_report` (hostile titles), `test_lookup_report`; probes p1, p3, p4 | 005 | **Pass for the listed strings; V-2** for `ftp:`, e-mail and `www.` auto-links in an outside Markdown reader | yes |
| REQ-WFM-137 (changed) report stored as data | Test | TC-WFM-137 `test_the_texts_of_a_run_are_stored_as_data` OK, but it has no report case; the report file is composed (state line, escaping), not stored "unchanged" | 003, 005 | **Partly: V-4** (the changed wording is not checked) | – |
| REQ-CLV-048 Report part | Test (browser) | TC-CLV-048 browser test OK (state in summary, rendered report, `/api/files/<name>` download byte for byte), `report-part.test.mjs` 3 OK | 001, 002, 006 | Pass | yes |
| REQ-CLV-049 links in the report | Test | `report-render.test.mjs` 7 OK, browser TC-CLV-048 and 052 (only the http address is a link, `_blank`, `noopener noreferrer`) | 005, 006 | Pass | yes |
| REQ-CLV-050 before the end | Test (browser) | TC-CLV-050 OK (waiting note, no link, then the report without a reload) | 001, 002 | Pass (but V-1: the sentence stays forever when no report could be stored) | yes |
| REQ-CLV-051 file gone | Test (browser) | TC-CLV-051 OK (removed note, no link, result and counts unchanged) | 001, 002 | Pass | yes |
| REQ-CLV-052 no active content | Test (browser red team + unit) | TC-CLV-052 browser OK (no script, img, link, iframe, style, form; no alert; no outside request), renderer unit tests OK; code read, see V-6 | 001, 005 | Pass | yes |
| REQ-CLV-043 (changed) | Test | TC-CLV-043 in the browser file OK (the other texts stay text nodes; I read `drawFull`: result, answers, material are `textContent`/text nodes, only `#srv-report-body` uses `innerHTML`) | 001, 005 | Pass | yes |
| IF-101 v18, IF-302 v12 | contract (mock and real) | `test_if_101_chat_api.py` 82 OK, `test_if_302_record_tables.py` 20 OK | – | Pass | yes |

In scope: 11 items (REQ-WFM-139, 140, 141, 137; REQ-CLV-048 to 052, 043; the two interfaces). 10 verified, 1 partly (REQ-WFM-137, V-4). All changed or new requirements stay Draft until the owner settles the findings.

## Goal acceptance (supervised goal: for information)
| Item | Result |
|---|---|
| Frozen requirements unchanged | none frozen (no siblings) |
| Protected checks identical to the baseline | yes, except A-155 and the browser payload |
| Nothing outside the goal's parts touched | the diff (49 files) is inside: runtime (`run_report.py`, `chat_service.py`, `skill_runs.py`, `skill_run_observer.py`, `extension_loader.py`), the three skills and their manifests, the front end, the stub server, docs. `research_chat.py`: the interim `files=` of 36cc3a9 replaced as planned |
| Stop conditions logged | the implementer stopped and asked for A-155 instead of editing protected files: yes |
| Exit criterion OC-1 to OC-4 | OC-1, OC-3, OC-4 checked by tests; OC-2 by TC-CLV-048/052; the hand check on the real model stays for Validate |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-WFM-139/140 "a run ends with a report" | a long single word in the argument makes the name invalid and the report is lost (V-1) | Phase 3 |
| specified, not done | REQ-WFM-141 "no link whose target does not start with http" | auto-links of `ftp://`, `a@b.example`, `www.` survive in the file for outside readers (V-2) | Phase 3 or accepted |
| specified, not checked | REQ-WFM-137 changed text | no check of the report as data (V-4) | Phase 2 |
| done, not specified | the state line wording (`# Done`, `# Stopped`, `# Failed: <reason>` up to 300 characters, the reason cut at 300 chars) | not in a requirement (the tests accept words only; the log names it) | Phase 2 amendment (small) |
| done, not specified | file name `<skill>-<date>-<first six words>.md`, a duplicate gets `-2`, `-3` by the files volume | not in a requirement | Phase 2 amendment or accept |
| done, not specified | the report is written only where a recorder and a volume exist; a volume error is logged and the run kept (no visible sentence) | not in a requirement; interacts with V-1 | Phase 2 |
| done, not specified | the fallback body has "## Result" and "## Figures" (counts and budget) | not in a requirement ("state, reason, result, figures" is in REQ-WFM-139's text, the layout is not) | accept |
| done, not specified | the Report part opens by itself once its report is loaded; a failed read keeps the part and asks again at the next change; the sentence "waiting" is shown whenever the record names no report, also for an ended run | open point 1 of A-154 covers opening; the rest is not stated (V-1 effect) | Phase 2 |
| done, not specified | the skill's own report is used also when the run fails or is stopped, with the state line on top | not stated | accept |
| done, not specified | `/search` hands its result text (escaped Markdown) as report, so it is not escaped again | not stated, consistent with REQ-WFM-141 | accept |

Human review: the specification side was reviewed by maldun (`plan-review.md`, D-341); code was read by me for every file named in the brief; items marked "Code review: needed": none found in the goal.

## Quality evidence per characteristic (M32)
Only the characteristics this goal touches: functional suitability (matrix above), security (the hostile checks, V-2, V-5, V-6 read), reliability (V-1 and the swallowed volume errors), interaction capability (Report part states; the waiting sentence, V-1). Others: not touched by this goal; `quality_check.py` was not run (no goal-level quality.md change).

## Findings
Severity: Blocker / High / Medium / Low / Info. Reproducers are in `/tmp/claude-1000/-home-maldun-prog-Python-MIA/5e26c798-8be5-4f43-bfc8-de08ec57aa3c/scratchpad/verify-probes/` (outside the repo; they use `python -I`, a probe of the real ChatService re-uses the acceptance test's `Setup`).

| ID | Severity | Where | Finding | Reproduce | Touches | Destination |
|---|---|---|---|---|---|---|
| V-1 | Medium | `run_report.report_name`, `chat_service._keep_report` (the exception is only logged), `skill-run-model.reportModel` | The file name is `<skill>-<date>-<first 6 words of the argument>.md` and each word is any length. The files volume accepts names of at most 120 characters (`file_store.NAME`). A `/lookup` or `/review` whose argument holds one long token (a long URL or identifier, about 100+ characters without a separator) gives a name of 190 to 220 characters, the put raises `invalid_file_name`, the run ends with no report and `report` null (a warning in the log only). That violates REQ-WFM-139 (every run, also stopped and failed) and REQ-WFM-140, and the Report part of a finished run then says "The report comes when the run ends" forever (REQ-CLV-050 is wrong for an ended run). The same happens when the volume is full or not writable. | `p1.py` (names of 221 and 190 characters are invalid); `p2.py` test_long_word: `/lookup` + 150 `a`: state done, `report` None, files [] | REQ-WFM-139, 140, CLV-050; TC-WFM-139 does not cover it | Phase 3: cut each word and the whole name to the allowed length (a regression test first) and give the page a sentence for "ended, no report"; or Phase 2 amendment that says what a run without a stored report shows |
| V-2 | Medium | `run_report.escape/link_addresses`, `research_chat._plain`, `review_chat._md` | Only http(s) addresses are written as `<...>` links, but the escape set leaves `@`, `:` and `/` alone. In a GFM reader (marked here, GitHub, most Markdown viewers) `ftp://x.example/a` becomes a link to `ftp://`, `a@b.example` a `mailto:` link and `www.w.example` a link (to http). So the downloaded file can hold a live non-http(s) link, contrary to REQ-WFM-141 ("no link whose target does not start with http:// or https://") and its acceptance criterion's spirit. In the MIA page this is harmless (`reportHref` unwraps these), so only the file opened outside MIA is affected. The `/search` list also prints the raw url line unescaped (`format_results`; the url is filtered to http(s) and without whitespace, so it is an http link only; control characters are not removed, which the page rejects) | `p3.mjs` (marked: `ftp:`, `mailto:` become links); `p1.py` (`www.evil.example and a@b.example` unchanged); `p4.py` (`_md` leaves the same) | REQ-WFM-141 (TC-WFM-141 checks only the fixed list, not these schemes) | Phase 3: escape `@` and the colon of a scheme (or write `ftp://` etc. as code), and add the cases to the red-team list; or accept for personal use (owner, memory: privacy-only findings low; this is untrusted web text, so it still counts) |
| V-3 | Low | `run_report.link_addresses` | An address that ends in `)` loses it (`https://a.example/p_(q)` becomes `<https://a.example/p_(q>` then `\)`), so Wikipedia-style addresses are cut and the link goes to a wrong page. The strip list `.,;:!?)]}'"` is applied without checking for balance. An address followed by `](javascript:alert(1))` is swallowed whole into one http link (safe, mangled). Only the fallback body (`link_addresses`) is affected; `/lookup` uses `_web_address` (no strip) | `p1.py` lines 2, 3 | REQ-WFM-141 (not wrong, only broken links) | Backlog / Phase 3 |
| V-4 | Low | `specs`: REQ-WFM-137 changed text, TC-WFM-137 | REQ-WFM-137 now says the report is stored "unchanged as text". The runtime puts its state line on top and composes/escapes the fallback body, so the stored file is not what the skill handed over. The requirement and the check do not say how these two fit (the check was not extended to the report) | read of `compose` (`'# Done\n\nOWN'` for own="OWN") and `test_skill_runs.py` line 167 | REQ-WFM-137, REQ-WFM-139 | Phase 2: word it as "the skill's own text is stored unchanged below the state line", add the report to TC-WFM-137 or name TC-WFM-139 |
| V-5 | Low | `chat_service._keep_report` | The report is stored after `chat_done` (A-155), so for a short moment the record has no report; a crash between the two leaves a finished run without a report (unspecified window). `_figures` raises if `budget` is not a dict, which would lose the report (caught and logged); the real recorder always gives a dict | `chat_service.py` lines around `_observer.end` | REQ-WFM-139 | Info, accept |
| V-6 | Low | `tests/browser/skill_run_view.py` (`report_hostile`) | After the payload was installed the implementer changed the hostile scenario (joined by blank lines instead of single line breaks, finding F-6 of the log) so that the http address becomes a link. The safety assertions are unchanged and the old form was safe too (a raw HTML block swallows the lines), but the file is part of the approved payload and was changed afterwards by the implementer; the single-newline variant (stricter for the sanitizer: raw HTML next to the link) is no longer run. I read `renderReport` (marked, then DOMPurify with its own call config: no `img`, `form`, `a` only `href`/`title`, `ALLOWED_URI_REGEXP` http(s) only, no hooks; then a detached `template`, links re-checked by `reportHref`, others unwrapped) and found no way for a tag, image or script to survive; the global hook of the chat renderer (target, rel, img rule) also runs on the report's sanitize but cannot add anything. Not exercised by me: a browser run with the single-newline text | read; browser file OK 16 | REQ-CLV-052, TR-PANEL-005 | Owner decides whether the variant joins the payload (Phase 2) |
| V-7 | Low | `skill-run.js drawReport` | Read for the points of the brief: the key is `run id|file name`, a stale answer is dropped by the key check, one request at a time (`loading`), a failed read (not 404) keeps the part and asks again with the next status; a 404 is final until the key changes (a file that comes back is not noticed). The part opens by itself only when the text arrives. No bug found; one small gap: after a run switch A to B and back to A with A's request still in flight, two requests may run (harmless) | read | REQ-CLV-048, 050, 051 | none |
| V-8 | Low | flaky check F-5 (dark theme shares, TC-CLV-046) | Passed in my single browser run; the log reports it failing in 2 of 4 runs. One run of mine cannot settle its failure rate | browser file run | TR-PANEL-001 | for the owner (G-V3.PANEL) |
| V-9 | Low | `trace_check.py` | WARN: REQ-CLV-049 "no @pytest.mark.req marker found" although two tests carry it (multi-id marker not read). Not a defect of the goal | `trace_check` output | traceability | Info |
| V-10 | Info | `architecture.sysml` | `run_report.py` and the need `run_report` are not parts of the model; requirement satisfy links exist | grep | M42 | accept |
| V-11 | Info | review `_md` | Minimal escape set (backslash and `[ ] < >`); a `|` or a line break in a keyword/origin breaks the keyword table row (known, noted in the log), a title with a line break can start a heading or a list in the file; none of these forms a link, image or tag | `p4.py` | REQ-WFM-141 (no link) | known limitation |

## Open deferrals
None of this goal. The TD records of the repo (TD-01, TD-03, TD-04 and others) are not listed in the node verification reports (trace_check WARNs, as on master).

## Accepted-deviation candidates
V-3, V-5, V-8, V-9, V-10, V-11, and (if the owner wants the Markdown file safe only inside MIA) V-2.

## Notes for Phase 7 (only people can judge)
- The owner looks at a real `/lookup` run: are the sources links, does the download open, is the state line wording ("# Done", "# Failed: <reason>") what is wanted, is the Report part's opening by itself right?
- A long question gives a long name in the files list (up to 120 characters).

## Not run
- `/lookup` against the running MIA (model server, SearXNG): needs the owner.
- Mutation tests, `release_check.py`, deployable build: not applicable to this goal or not run (see table).
- Browser run of the single-newline hostile variant (V-6): not run (the stub scenario is the implementer's; I did not edit it).
