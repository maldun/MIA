# G-V3.CHAT second Verify run: report

Reviewer: fresh Verify-phase agent (no memory of earlier sessions), 2026-11-15, branch `goal/v3.chat`, HEAD `85f302d` (code of `bac6145`), narrow run (brief `verify-brief-run2.md`). The reviewer returned its report as text; the implementing session saved it here, condensed, and added the column "Fixed in" and the owner notes. The reviewer worked in a clean `git archive` copy and changed nothing; no model was run, the holdout was not touched.

## Verdict of the reviewer: Not verified
Remaining reasons at the time of the report: F-15 (run-link cut bypass), F-16 (`strip_markup` stops after 20 rounds), F-17 (`plausibility.yaml` does not parse), F-18 (test gaps). F-12 and F-14 are candidates for accepted deviations; none is accepted yet. The fix round after this report (below) answers F-15, F-16, F-18 and the observations in code and tests; F-17 needs the owner's install of `amendment-a152/plausibility-yaml-fix.patch`; a third narrow check is needed for a verdict.

## Findings of run 1: status
F-01 to F-09, F-11, F-13 closed (probes with a real thread, source read for the wiring, mutants killed); F-10 closed for plain links, bypassed by F-15; F-12 and F-14 accepted-deviation candidates; F-13 note: `_run_phases` is cleared only when a recorder observer exists (a tiny leak without a recorder, low).

## New findings
| ID | Sev | Finding | Fixed in |
|---|---|---|---|
| F-15 | medium | the run-link cut (REQ-CHA-066) ran once: `Fine [a](#ru[b](#run=1)n=evil) bye` rebuilt a link; `[a [b]](#run=evil)`, `#RUN=`, `[a]( #run=evil)` were not cut; the done message could hold two run links | `cut_run_links` in `chat_service.py`: repeats until stable, one level of brackets in the label, any case, an optional space or `<`, and a left-over `#run=` is made plain; tests `SecondVerifyRun.test_a_run_link_that_is_built_from_what_is_left_is_cut_too` |
| F-16 | medium-low | `strip_markup(text, rounds=20)` failed open: a tag hidden 21 levels deep survived | no round limit: the loop ends when nothing changes (each round shortens the text); test with depth 25, nested script elements and 1 MB of unclosed `<script>` |
| F-17 | owner | `specs/mia/plausibility.yaml` has not parsed since `e6f8fae`: a `: ` inside the plain text of the REQ-CHA-065 basis (line 4967) | **the implementing session's mistake** (the check was run on the file before the REQ-CHA-065 row was added): `goals/G-V3.CHAT/amendment-a152/plausibility-yaml-fix.patch` (one character, `:` to `,`), checked: the file parses and the tool reports only REQ-RTB-009 (TOOLBOX); the owner installs it |
| F-18 | low | test gaps: persona read at call time, link in failed and stop messages, a repair that adds a link, a raising phase turn, nesting depth, cost at 1 MB | tests added in `SecondVerifyRun` (those that passed before are gaps now closed); the mutants "persona read once", "link not cut in failed/stopped", "cut before repair only", "two rounds" and "on_phase raising uncaught" are covered |
| obs | low | `ask` set the waiter before posting the question: a failing log left the waiter and the next message was swallowed | the waiter is cleared if posting fails; test added |
| obs | info | the question text is not link-cut (it is the skill's own text, not worded by the step): within REQ-CHA-066 as written | – |
| obs | info | `strip_markup` leaves the text of an unclosed `<script>` as plain text and does not remove processing instructions: design limits, documented in the code | – |

## Mutants (35, copy of HEAD)
28 killed, the rest survived or were no-ops (listed above under F-18 and the equivalent `_run_phases` cleared too early). Checks of the reviewer: full unit suite 2294 OK (4 skipped, 2 expected failures), integration check, acceptance tests, IF-201 contract suites (24), SysML, `check_d_numbers` (D-182 only), `trace_check` 538 as in master and none for REQ-CHA-040 to 066, `agent_check` and `goal_check` with nothing for this goal, protected diff only `e6f8fae`.

## Eval material (feedback only)
Run 6 with the owner's 78 labels: REQ-CHA-053 72 of 72 faithful, REQ-CHA-054 72 of 72 persona, REQ-CHA-049 18 of 18 resisted (the stored statuses were scored before the label, 15 pass and 3 open). No dev output changes with the markup removal or the link cut (none holds `<`, `>` or `#run=`), the prompt is unchanged, the labels still apply. Dev feedback only: the holdout decides.

## What the owner must do
1. Install `specs/mia/goals/G-V3.CHAT/amendment-a152/plausibility-yaml-fix.patch` (F-17).
2. After a third narrow check: decide whether F-12 and F-14 become accepted deviations.
3. Run the holdout yourself (script prepared), label the output, decide REQ-CHA-049, 053 and 054 with `eval_decide.py`.
4. Push the branch.
