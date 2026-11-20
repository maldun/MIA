# Brief for an agent: sign-off commands in `requirement-mode` (Emacs)

Written 2026-11-20 by the MIA session (Claude) for the owner, Stefan Reiterer, to hand to a fresh agent. Status: a request, not a decision. The owner decides every gate.

## Where to work
- Repository: `/home/maldun/prog/Lisp/requirement-mode`. Read first: `CLAUDE.md`, `specs/requirement-mode/handover.md`, `README.md`. Its workflow is the seven-phase workflow (skills in `~/.claude/skills`, the newer set).
- This is a new feature of an existing, verified product: start in **Explore** (`explore-phase`: a short top-level spec for the feature, an interview of the owner by questionnaire, one item per question), then Plan. Do not write code before the owner approves the plan. Stop-and-report rules of `CLAUDE.md` apply (new interface, protected files, `contracts/`).
- Hard rule that stays: the mode and every tool it offers to Claude never set a gate on their own authority (NFR-6). A sign-off command is for the **owner at the keyboard** and asks for a confirmation; it must not be reachable from the `requirement_*` tools of `requirement-claude.el`.

## The need (owner, 2026-11-20)
The owner asked: "can I sign it with the emacs mode?" Today he types the sign-off by hand. The mode opens the files and saves them byte for byte (checked), but it has **no command for a sign-off** that is not a requirement `Status:` bullet. Typing by hand is error-prone: a stray `:sadd:` ended up in a signed table row today, and a name was typed with a different date format (`20.11.2026`) than the ISO date of the conventions.

## What exists (checked 2026-11-20, Emacs 30.2 batch)
- Markdown files below `specs/` open in `requirement-mode`; saving writes Markdown back unchanged except the edit (test: replace `Validated by: –` and `Decided by: –` in copies of the two files below, save, `diff` shows only those lines).
- `requirement-set-status` (`C-c r s`, `requirement-status.el:199`) and `requirement-cycle-status` handle `- Status:` bullets of items with IDs; gate statuses (Approved, Verified, Validated) need a confirmation and leave `Approved confirmed in Emacs on <date>` in `- History:`; `requirement-check-gates` and `requirement-accept-gates` report and backfill those records.
- The dashboard section `To sign off` (`requirement-dashboard.el:119` and following) lists files with items waiting for a gate. It knows nothing of the elements below.

## What is missing: sign-off elements that are not requirement statuses
These are the forms the workflow checkers read (`~/.claude/skills/dev-workflow/scripts/spec_check.py`, `goal_check.py`, `binding_check.py`). Examples are from the MIA prototype of goal G-V4, branch `prototype/g-v4`, worktree `/home/maldun/prog/Python/MIA-prototype-g-v4`; look at the real files, do not edit them in this task.

| Element | Where (example) | Form today | Who must sign |
|---|---|---|---|
| Validation signature | `specs/mia/goals/G-V4/prototype/rounds/02/validation.md` | line `Validated by: –` (PT10 wants a person) | the owner |
| Carry-over decision | `.../rounds/02/prototype-report.md`, under the carry-over table | line `Decided by: –` (PT3 wants a person, the decision cells hold `adopt`, `adapt`, `discard` or `stand-in`) | the owner |
| Run authorization | `.../rounds/02/run.md` | field `**Authorized by:**` and `**Date:**` (PT9) | the owner |
| Reuse map review | `prototype/reuse-map.md` (Plan) | `Reviewed by:` and `Date:` (PT12) | the owner |
| Binding map | `binding-map.md` (Plan) | signed by a person (BD4) | the owner |
| Agreement of subgoals | goal records, table row such as `\| G-V4.VIEW \| [ ] Stefan Reiterer (owner) \| 2026-11-20 \|` | a box `[ ]` in a table cell, `[x]` when ticked | the named person |
| Approval boxes of a TLS or HLS | `top-level-spec.md`, status and sign-off sections | box `[ ]` | the owner |
| Unsupervised goal acceptance | goal record, `Accepted by:` | name | the named person |

## Wanted behaviour (to be confirmed with the owner in Explore; these are proposals)
1. One command, for example `requirement-sign` (`C-c r S`), that finds the sign-off element at point (or the next unsigned one in the file), shows what will be written, asks for a **yes** (the same confirmation function as the gates), and writes the signer's name and an **ISO date** (`2026-11-20`). The signer comes from a customizable variable (default `user-full-name`); it never writes `–`, never signs for another person, and refuses a row whose signer is named differently from the account unless the owner says so.
2. Forms: `Label: –` lines (any of the labels above), `[ ]` boxes in table cells and list items (to `[x]` with name and date where the cell has room), and `Reviewed by:` plus `Date:` pairs.
3. A record of the sign, like the gate records: a line in the file's own history where one exists (`signed in Emacs on <date>`), otherwise a short entry in a `*Requirement sign-off log*` buffer. The README is honest that such a record cannot prove who typed a line; keep that sentence true.
4. An already signed element is not overwritten silently; there is no "unsign" (a correction is a new, dated line by a person).
5. The dashboard section `To sign off` also lists files with unsigned sign-off elements (`–` after a sign-off label, `[ ]` in a sign-off table), next to the files with Draft or Implemented items.
6. Safe against the conversion layer: the byte-for-byte round trip of the Markdown file must hold after a sign (a test on a fixture, `tests/fixtures/`, kept as `*.fixture`).

## Open questions for the owner (ask them in the questionnaire, recommended option first)
- Which elements in the table above should the command handle in the first version (suggest: `Validated by`, `Decided by`, boxes, `Reviewed by` with `Date`)?
- Name and date: from `user-full-name` and the system date, or asked each time?
- May the command sign several elements of one file in one go, or one at a time (suggest: one at a time)?
- Where does the record go when the file has no `History:` (suggest: a log buffer plus an optional `Signed: <name>, <date>` line)?
- Does a sign-off of a goal's Agreement table (several people) belong here, or only the owner's own?

## Done means (proposal for the Plan)
- Requirements in `specs/requirement-mode/` in the form of that project (EARS, one "shall" each, grouped), a test per requirement in ERT with `:tags '(req:<ID>)`, the traceability check green, byte-compile with warnings as errors clean, checkdoc clean, no new dependency.
- A test that the claude tools cannot reach the command, and a test that the command asks before writing.
- A short README section "Sign a document" and an entry in the key table.

## Not in this task
Changing the workflow checkers or the skills (the scripts in `~/.claude/skills` define the forms above; if a form should change, report it to the owner). Editing any MIA spec file. Running Claude from within the sign command.
