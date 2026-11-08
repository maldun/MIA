# A-143: wire TD-62 (the tailscale unit test on a host with Tailscale) into the checks (drafted 2026-11-08)

Status: **approved as proposed (option A) and applied, owner 2026-11-08: sign-off maldun, marker as unittest `expectedFailure` (comment carries `mark.deferred("TD-62")` for `trace_check.py`), expected failure only when the host has `tailscale` in `/usr/bin:/bin`.** Result: `python tests/test_tailscale.py` 17 tests OK, 1 expected failure (32 s, the timeout); `trace_check.py` 544 errors (545 before), none names TD-62. Decision id: see `review-log.md` (D-289 recorded the deferral itself). Plan step only; no production code changes. Parent decision: D-289 (owner Stefan Reiterer, 2026-11-08: the tailscale test is deferred to a later goal).

## Problem
D-289 added `TD-62` to `deferred.md`. `trace_check.py` now reports four errors that name it (549 errors instead of 545 on master before; none of them concerns TD-11):

| Error | Meaning |
|---|---|
| `NFR-6 does not carry 'Relaxed: TD-62'` | the requirement the record points to has no link back |
| `NFR-6 has no 'Target'` | the full level is not visible in the requirement |
| `open, but no test with @pytest.mark.deferred('TD-62')` | the target check is named in the record but carries no marker |
| `touches security ... needs 'Sign-off: <person, date>'` | the checker treats Tailscale (network exposure) as a security topic |

Cause of the red test itself: `tests/test_tailscale.py::ScriptTest::test_without_tailscale_it_says_how_to_install` (line 181) sets `PATH=/usr/bin:/bin` to hide the fake `tailscale`; on this host `/usr/bin/tailscale` exists, so `remote.sh up` (line 15 finds it, line 21 runs `tailscale serve`) calls the real binary and the test times out after 30 s.

## Precedent
`TD-26` (same requirement, NFR-6) has the same three of the four errors today and sits in the old M41 backlog (D-270). Adding TD-62 the same way keeps the pattern; it does not fix the backlog.

## Proposal (three small changes, all in protected or approved material, hence this amendment)

1. **`NFR-6`** (file where NFR-6 lives: `specs/mia/high-level-spec.md` / the node requirements that carry it; the exact line is to be found with `grep -rn "NFR-6" specs/mia`): add `- Relaxed: TD-62` next to the existing `Relaxed: TD-26` line (if any) and extend its `Target:` text by one clause: "the unit test without Tailscale gives the same result on every host (TD-62)". No change of the requirement's text or status.
2. **`tests/test_tailscale.py`**, test at line 181: add `@pytest.mark.deferred("TD-62")` as a strict xfail on a host that has Tailscale (a skip with a reason would hide the fault on hosts without it). `tests/` is not protected, so this needs no amendment by itself; it is listed here so the three parts land in one commit. Requires `pytest` to be importable in the file or a `unittest.expectedFailure` equivalent: **check which one `tests/` uses for other deferred markers before writing** (the grep for `deferred('TD` found none in `tests/` today, so the convention is open: question 2).
3. **`deferred.md` TD-62**: add `- Sign-off: <person>, <date>` (question 1). Nothing else in the record changes.

The later fix (Target of TD-62) is not part of this amendment: the test needs a `PATH` that has `bash`, `python3` and the coreutils but no `tailscale`, for example a temp directory with symlinks to those tools, or `remote.sh` honouring a `TAILSCALE_BIN` variable. The second option changes `remote.sh`, so it is a Phase 3 task with its own review.

## Expected result
- `trace_check.py`: the four TD-62 errors go; 545 errors remain (the old backlog, TD-26 pattern included); the warnings "open deferral not listed in verification-report.md" stay until a goal's report lists it.
- `python tests/test_tailscale.py` on this host: the one test reports an expected failure instead of a 30 s timeout; on a host without Tailscale it behaves as the marker says (see question 2).
- The stage `unit` of the ladder turns green on this host for this test only.

## Alternatives
- **A (proposed):** the three changes above.
- **B:** only the sign-off and `Relaxed`/`Target` lines, no marker: keeps the test red and the stage red; `trace_check` still reports the missing marker.
- **C:** fix the test now (Phase 3, test first). The owner deferred this on 2026-11-08, so it is not proposed here.

## Questions for the owner
1. **Sign-off for TD-62:** who and which date goes into `Sign-off:`? (The checker wants a named responsible person; the proposal is `Stefan Reiterer, 2026-11-08`, the owner of the record.)
2. **Marker form:** strict xfail with `pytest.mark.deferred` (needs pytest in that file, which runs as a plain `unittest` script today) or `unittest.expectedFailure` plus a comment `# deferred: TD-62` that `trace_check.py` may not recognise? A short check of the script decides this before approval; the proposal is whichever the script accepts.
3. **Hosts without Tailscale:** an expected failure there would turn into an "unexpected success" error. The proposal is a condition: expected failure only when `shutil.which("tailscale")` finds the binary; otherwise the test runs normally.

## Steps after approval
1. Owner answers 1 to 3 (and approves or chooses B).
2. Phase 2 edits (me): NFR-6 lines, `deferred.md` sign-off, the marker in `tests/test_tailscale.py`, one commit `docs: A-143 ... (NFR-6)`.
3. Checks: `python tests/test_tailscale.py`, `trace_check.py` (expect the four errors gone), `git diff --stat` shows no other file.
4. Review-log record with the next free decision id.
