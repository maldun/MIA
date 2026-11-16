# G-V3.CHAT fourth Verify run: report

Reviewer: fresh Verify-phase agent (no memory of earlier sessions), 2026-11-15, branch `goal/v3.chat`, HEAD `466ed94` (fixes of `9d8e475`), very narrow run (brief `verify-brief-run4.md`). The reviewer returned its report as text; the implementing session saved it here, condensed, with the column "Fixed in". It worked in `git archive` copies and changed nothing; it ran no model, no browser (DOMPurify not run; the vendored marked was run with node and its `href` values decoded as a browser does) and did not touch the holdout.

## Verdict of the reviewer: Not verified
F-19, F-21 and F-23 fixed as specified; F-20 and F-22 fixed for what they named, each fix left a neighbour open (F-29, F-28). Eight new findings, F-25 to F-32; F-25, F-26 and F-27 are bypasses of the invariants of REQ-CHA-066 and 064. F-12 and F-14 were not re-examined; none is accepted.

## Findings
| ID | Sev | Finding | Fixed in |
|---|---|---|---|
| F-25 | medium | a backslash escape builds a link the cut and the `html.unescape` check do not see: `[x](#run\=evil)`, `[x](<#run\=evil>)`, `[r]: #run\=evil` + `[x][r]`; marked renders `<a href="#run=evil">`, the click handler `a[href^="#run="]` opens run `evil`; also mixed with entities (`#r&#117;n\=e`) | `browser_view` (entities, backslash escapes of punctuation, tab and newline, lower case) decides; `neutralize_run_links` writes every `&` as `&amp;` and every `#` as the full-width sign when that view holds `#run=` |
| F-26 | medium | order strip, repair, cut: the cut joined a tag the strip had not seen as one: `<[x](#run=1)script>EVIL</[x](#run=1)script>` became `<script>EVIL</script>` and was spoken | `clean_model_text`: both cuts together up to 3 rounds, then `strip_markup` (ends with `escape_markup`) and `neutralize_run_links` last, so that nothing after it can build a link; used in `_turn_text` |
| F-27 | medium-low | a tag with a `<` in an attribute value (`<script a="<">alert(1)`, `<b title="<">x</b>`, `<svg onload="<">`) survived `TAG` | `escape_markup`: every `<` followed by a letter, `!` or `/` is written `&lt;` at the end of `strip_markup`, by construction (`5 < 6` stays) |
| F-28 | low-medium | `CODE_OPEN` with `re.I` matched `ſ`, `İ`, `ı` for s and i: `KeyError` in `CODE_CLOSE`, the wording of the step was lost (`<ſcript>x`) | `re.I | re.A` on `CODE_OPEN` and `CODE_CLOSE` |
| F-29 | low-medium | `CODE_OPEN` with the prefix `[ \t]*` was quadratic on blanks: 100 000 blanks 10.5 s, tabs 15.6 s | no prefix; the blanks in front of a removed element are cut with `rstrip` (linear) |
| F-30 | low | text ending in `<!--` or an open code fence swallowed the real link that code adds | the comment is escaped by `escape_markup`; an open fence is closed before the link |
| F-31 | low | `[x](#ru&#10;n=e)` and `&#9;`: the URL parser drops tab and newline, a click or a reload reads the hash `#run=e` | in `browser_view` (F-25) |
| F-32 | info | after 8 rounds all `<` were escaped (`5 < 6` too, at depth 8 exactly); the voice reads `&amp;` and `&lt;` where the net fires | only `<` before a letter, `!` or `/` is escaped, so `5 < 6` stays; a spoken `&lt;` remains possible in the rare case that the net fires |

## Status of F-19 to F-24
F-19 fixed for entity forms, gap F-25/F-31 closed now; F-20 closed (cut) and F-29 (the removal); F-21 closed; F-22 closed and F-28 closed; F-23 closed (script and style end tags); F-24 tests added (the gaps named by the mutants are covered by `FourthVerifyRun`).

## Mutants and gaps
Killed: `&amp;` rewrite removed, `html.unescape` check removed, bounds removed, the `&lt;` fallback removed, `CODE_CLOSE` back to `\s*`, `lower()` back, `CODE_OPEN` without `re.I`, the plain pass removed, cut before repair. Survivors named by the reviewer and now covered by tests: normal `&` unchanged (`Tom & Jerry`), `#RUN=` in a destination and as a rest, `CUT_ROUNDS` 1 (the joined link is cut whole), label bound (`"[a]["*30000` under 1 s), destination bound, nesting depth 7 to 10, `</style foo>`, comments and doctype, `escape_markup`.

## Checks (reviewer, clean copy of HEAD)
Full unit suite 2306 OK (4 skipped, 2 expected failures); integration check, acceptance tests (22), IF-201 contract (24), `test_chat_verify_fixes` (27) OK; SysML OK; `check_d_numbers` D-182 only; `trace_check` 538 as master, none for REQ-CHA-040 to 066 or TC-CHA-040 to 071; `req_plausibility` only REQ-RTB-009; `agent_check` and `goal_check` nothing for this goal; protected diff `dd9f8ac..HEAD` empty.

## Worst-case time (reviewer, 1 MB)
`cut_run_links` at most 0.28 s (6 rounds), `strip_markup` at most 0.17 s except blanks and tabs (F-29, fixed).

## What the owner must do
1. Decide how many more narrow checks (each of the four found real, ever smaller defects of the same family; this round moved the guarantees to the end of the functions by construction instead of per form) and whether F-12 and F-14 become accepted deviations.
2. Run the holdout (script prepared), label, decide REQ-CHA-049, 053, 054.
3. Push and merge; name the paths in the commands, no `git add -A`.
