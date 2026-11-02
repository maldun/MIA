# VAL-003 check sheet: does the character feel in character and pleasant?

Prepared by the coding agent for the owner (2026-11-02). Criterion (`validation-plan.md`): *each user chats for a week; evidence = the weekly overall score (FR-27), a short rating per user after the week (1 to 5 and a free line), the score trend, the ratings and quotes.* Quality in use: **satisfaction**. People judge; the agent only extracts and counts. No LLM judge. Persona check dialogues (AC-8) are not part of this (TD-10).

## Owner fixes before day 1 (not after the data)
- [ ] **What counts as pass / partial / fail?** The plan and `quality.md` give no number for VAL-003 ("to be fixed in Validate"). Write it here first, for example the median rating and the direction of the weekly score. Rule: _______________________
- [ ] Start date ________  end date (7 days later) ________  retention and deletion date of the logs ________
- [ ] Version is frozen: image `8217ecd0ccf8` (v0.1.0), no pulls, no prompt or skill edits during the week.
- [ ] Each user has an account, has read what is stored (messages, votes, run logs; read only by the owner; owner's host only) and agreed. Users are named **U1, U2, ...** in everything written down.

## What the user is told (goals, not clicks)
1. Chat with MIA in your daily life for a week, on the device you like, as much or as little as you want. Talk about real things, also small talk.
2. Give a **plus or minus** when an answer felt right or wrong, in whatever category the page offers. Give it when you feel it, not for the sheet. (In this release votes cover answers; votes on reactions and behaviours are not built, FB-05.)
3. Do not try to break her. If something feels off, say so in the note field below.
4. At the end, fill in the last page. There are no right answers.

## Daily note (one line per day, optional; the user keeps it)
| Day | Used? (how long, which device) | One line: what stood out, good or odd |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
| 6 | | |
| 7 | | |

## First session (owner or a helper present; observe, do not help)
Think-aloud once, 15 minutes. Write down: time to first text, what the user did next, errors shown, requests for help, quotes. Exploratory part at the end: "What is missing? What would you use her for?" No leading questions ("Isn't she cute?").

## End of the week (per user, 5 minutes)
- User: U__    Days used: __    Device(s): ________
- **Overall rating, 1 to 5:** 1 = I would switch her off, 3 = fine, nothing special, 5 = I look forward to talking to her.   ☐1 ☐2 ☐3 ☐4 ☐5
- **One line why:** ________________________________________
- A moment she felt like a character or a person: ________________________________________
- A moment she broke it or annoyed you: ________________________________________
- Would you keep using her? For what? ________________________________________

## What the agent extracts (locally, after the week, nothing leaves the machine)
- Weekly overall score per user and its trend, and plus/minus counts per category, from the votes of the deployed stack (the series per ISO week of IF-101; the counters view on the page is not built yet, so this is read from the votes table).
- Number of chat days and messages per user, queue waits, errors, from the run log and `tools/run_explain.py` pointed at the stack's `mia-data` (the default reads the old host runs).
- The ratings, the free lines and the daily notes, pseudonymised, with counts per theme and one quote each.
- Reported **descriptively** (counts, medians, quotes), no p-values. The agent proposes a rating against the owner's rule above; the owner decides.

## Not covered by this sheet
Persona statistics against the old MIA (AC-8, TD-10); more than a handful of users; other languages; voice quality in detail (the voice is part of the impression but not rated separately); the phone over the tailnet (VAL-004, TD-26).
