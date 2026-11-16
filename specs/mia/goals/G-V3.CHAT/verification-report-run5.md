# G-V3.CHAT fifth Verify run: report

Reviewer: fresh Verify-phase agent (no memory of earlier sessions), 2026-11-15, branch `goal/v3.chat`, HEAD `1cd6630` (= `a1b522e` + brief), very narrow run (brief `verify-brief-run5.md`): the new construction of the cleaning of the text of the digest step. The reviewer returned its report as text; the implementing session saved it here, condensed, with the column "Fixed in". It changed nothing; it ran no model and no browser (no DOM library in the repo or on the machine, so DOMPurify was **not run**; the vendored marked was run with node), and did not touch the holdout.

## Verdict of the reviewer: Not verified
Three remaining defects: F-33 (an exception, claim (d) refuted), F-34 (the fix of F-30 does not work: an open fence, indented code or a table row swallows the real link), F-35 (`<?` stays markup). Claims (a) (no `<` before a letter, `!` or `/`) and (c) (cost) hold; claim (b) holds for run links, refuted for the link staying a link. F-12 and F-14 are acceptable as accepted deviations; they are not a reason for the verdict. REQ-CHA-049, 053 and 054 are decided only by the owner's holdout run.

## Findings
| ID | Sev | Finding | Fixed in |
|---|---|---|---|
| F-33 | high | `html.unescape` calls `int()`, which raises `ValueError` for a reference with more than 4300 digits (`&#` + 5000 digits): `clean_model_text` raised in `_turn_text`; for an end message the call is outside any guard, so no message, no `chat_done`, no voice, the observer stays open, `_message_id` stays set (the model text is the only input needed) | `browser_view` catches the error and fails closed (the text is made plain); `_turn_text` falls back to a plain sentence if the cleaning fails for any reason; tests: the cleaning returns text for every text, a run with such a summary ends with its message and is closed |
| F-34 | medium | the closing fence was written on the same line as the link (` ``` [Open ...]`), not a closing fence: an open fence (also `~~~`, four backticks, with an info string, in a quote or a list), an indented code line and a table row swallowed the link | no code fence can open (runs of three or more backticks or tildes are escaped with backslashes in end messages); a blank line separates the link from an indented code line or a table row (otherwise the protected tests' form ` [Open ...]` stays); test |
| F-35 | medium | `escape_markup` left `<?` as markup (a bogus comment in the browser, a raw block in marked that swallows the link) | `<` before `?` is escaped too; test |
| F-36 | info | the run id was put into the link unencoded (an id with a space or a parenthesis breaks the link; real ids are `<digits>-<hex>`) | `quote(run, safe="")`; test |
| F-37 | low | survivors of non-equivalent mutants: the last `strip_markup` and the order of `neutralize_run_links` in `clean_model_text`; `</b` without `>`; a carriage return in a destination | tests (`FifthVerifyRun`) |
| F-38 | info | the voice may read `&lt;` or `&amp;` aloud when a net fired | unchanged (rare) |

## Status of F-25 to F-32
F-25, F-26, F-27, F-28, F-29, F-31, F-32 fixed (fuzz over 250 000 inputs, whole-path outputs, marked hrefs of 80 000 outputs decoded: no `#run=` fragment but the real link); F-30 partly (the comment is fixed, the fence was not: F-34, F-35).

## Worst-case time
100 KB: at most 0.25 s (`[a][` repeated in `cut_run_links` and `clean_model_text`), 1 MB: 2.45 s; 10 MB: plain 0.2 s, worst shapes 7 to 24 s, memory about 74 to 150 MB; all linear.

## Checks (reviewer)
Full unit suite 2316 OK (4 skipped, 2 expected failures); integration check, acceptance tests (22), IF-201 contract suite (24); `check_sysml_model`, `check_sysml`; `check_d_numbers` D-182 only; `trace_check` 538 as master and none for REQ-CHA-040 to 066 or TC-CHA-040 to 071; `req_plausibility` only REQ-RTB-009; protected diff `466ed94..HEAD` empty.

## What the owner must do
1. Install the F-12 and F-14 patches (`amendment-a153`) and the choice about further Verify rounds: this round answers F-33 to F-37; a sixth narrow run would check them.
2. Run DOMPurify on the real page once (the reviewer could not): look at one done message ending in an open fence and one with `<?`.
3. Run the holdout (script prepared), label, decide REQ-CHA-049, 053, 054. Push and merge, naming the paths.
