# G-V3.CHAT third Verify run: report

Reviewer: fresh Verify-phase agent (no memory of earlier sessions), 2026-11-15, branch `goal/v3.chat`, HEAD `dd9f8ac` (fixes `86c7d5f` and the owner's `cd06750`), very narrow run (brief `verify-brief-run3.md`). The reviewer returned its report as text; the implementing session saved it here, condensed, with the column "Fixed in". It worked in a copy of the worktree and changed nothing; no model was run, the holdout was not touched.

## Verdict of the reviewer: Not verified
F-15 to F-18 of the second report are fixed (F-15 for every literal `#run=` form, F-16 no cap, F-17 the file parses, F-18 tests). Six new findings, F-19 to F-24, none beyond low to medium; F-12 and F-14 are still candidates for accepted deviations (not re-examined, none accepted).

## Findings
| ID | Sev | Finding | Fixed in |
|---|---|---|---|
| F-19 | medium | REQ-CHA-066: an HTML character reference in a link destination (`[x](&#35;run=e)`, `&#x23;`, `&num;`, `#&#114;un=`, `#run&#61;`, a reference definition `[r]: &#35;run=e`) survives the cut; the page's renderer writes `href="&#35;run=e"`, the browser decodes it to `#run=e` and the click handler `a[href^="#run="]` opens an arbitrary run (decoding from the HTML rules, not confirmed in a browser) | `cut_run_links` fails closed: if the text decodes to `#run=` (`html.unescape`) every `&` is written `&amp;`, so the page shows the text and never builds the link; test `ThirdVerifyRun.test_a_link_with_an_encoded_destination_is_not_left_to_the_page` |
| F-20 | low-medium | the cut was quadratic: `\s*` in front (40 000 blanks 3.7 s), `[a` repeated 80 KB 1.4 s, a chain of joined links of depth d needs d+1 rounds (88 KB 9.5 s) | no `\s*`, bounded label and destination, at most 6 rounds; what is left is made plain by a single pass (the invariant never depended on more rounds); test of the three degenerate texts under 1 s |
| F-21 | low | `strip_markup` rounds bounded only by the nesting depth: `"<a"*d + "b" + ">"*d` took 2.9 s at 24 KB (about 1.4 h at 1 MB) | at most 8 rounds, then the remaining `<` are written `&lt;` (fails closed, shown as text); test: 8000 levels under 1 s and no tag |
| F-22 | low | `_without_code_elements` mixed the indexes of `text` and `text.lower()`; the dotted capital I (`"İ".lower()` has two characters) moved the cut: text after a script was lost or the content of a second script kept | the original text is searched with case-insensitive patterns, no lower-cased copy; test |
| F-23 | low | an end tag with attributes or a slash (`</script foo>`, `</script/>`) did not close the element, so the script content stayed (plain text) | `</script\b[^<>]*>` and `</style\b[^<>]*>`; test |
| F-24 | low | test gaps: the left-over rewrite of `#run=` (mutant N2) and M7 (cursor check) had no test of their own; nothing covered İ or `</script foo>` | tests above and `test_the_rest_of_a_cut_is_made_plain_even_when_no_link_form_matches` |
| obs | info | `<?php ...?>`, `</ b>`, `<!--` without `>` and `<\x00script>` survive `strip_markup`: not tags, DOMPurify removes them (not checked whether the page strips control characters) | – |

## Mutants
N2 (leftover rewrite removed) and M7 (cursor check removed) survived; N3, N4, N8 (single layers of the link pattern) survive alone because the rewrite makes any leftover inert, killed in combination; all others killed (persona read once, link not cut in failed or stopped, cut before repair only, two rounds, `on_phase` raising, `no_close` ignored, one pass, cap of 20, waiter reset, without `<`, `CODE_OPEN` case). `ask` checked with a log that fails once and a run without recorder.

## Checks (reviewer)
Full unit suite 2300 OK (4 skipped, 2 expected failures); integration check, acceptance tests (22), IF-201 contract (24), `test_chat_verify_fixes` (21) OK; SysML OK; `check_d_numbers` D-182 only; `trace_check` 538 as master and none for REQ-CHA-040 to 066 or TC-CHA-040 to 071; `req_plausibility` parses, only REQ-RTB-009; `agent_check` and `goal_check` nothing for this goal; protected diff `85f302d..HEAD`: only `cd06750`. REQ-CHA-063 has an acceptance test only (no unit test).

## What the owner must do
1. After a fourth check (or the owner's decision to rely on the fail-closed ends): accept F-12 and F-14 or have them fixed.
2. Run the holdout (script prepared), label, decide REQ-CHA-049, 053, 054.
3. Push and merge; name the paths in the commands, no `git add -A`.
