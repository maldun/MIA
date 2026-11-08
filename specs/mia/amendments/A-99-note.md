# A-99: plausibility records for REQ-GTB-023..027 (G-V2.STORE)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a99.sh` is not yet run with `--do` in the repository.

## Owner's ratings (2026-11-08)
| Requirement | Rating | Basis in short |
|---|---|---|
| REQ-GTB-023 context tables (versioned, never deleted) | plausible | no number; acceptance criterion, golden 17, mock, TC-GTB-024; realised in T-08 |
| REQ-GTB-024 shape of context records | plausible | no number; golden 17, mock, TC-GTB-025; realised in T-08 |
| REQ-GTB-025 ends of a context edge | plausible | no number; golden 18, mock, TC-GTB-026; realised in T-08 |
| REQ-GTB-026 members of a context header | plausible | no number; golden 19, mock, TC-GTB-027; realised in T-08 |
| REQ-GTB-027 input that cannot be checked (limit 200 levels) | first "questionable, needs a probe", then **plausible after the probe** | probe below |

## The probe for REQ-GTB-027 (run by the drafter, 2026-11-08)
193 JSON, JSONL and YAML files under `library/`, `skills/` and `eval/` were read and the nesting depth of every document measured (the record would be level 1). Deepest documents: `library/pipelines/research.escalate/3.json` 19 levels (a whole pipeline; a single node record is shallower), `research.typed/1.json` 17, `research.escalate/2.json` and `/1.json` 13, `research.decompose/2.json` and `/1.json` 11. The limit of 200 is about ten times the deepest real document and far below the recursion limit of about 1000. Limit of the probe: current files only, not future user workflows; the owner rated plausible with this result.

## What the script does
Inserts five records in sorted place in `specs/mia/plausibility.yaml` (`rated_by: maldun`, `rated: '2026-11-08'`, `hardware: HW-target`, a basis text each). Nothing else changes. A record that is there already is skipped.

## Why the script now refuses broken YAML
My A-97 text for REQ-WFM-068 had "…no number: a retired…". YAML reads a colon followed by a space as a key, so `req_plausibility` crashed (fixed in commit `e691dee`), and my scratch checks had counted that crash as "0 errors". A-99 therefore (a) parses the result and refuses when a basis is not text, (b) keeps the checker's output and prints its exit code, the number of tracebacks and every error line. It caught the same mistake in my first draft of the REQ-GTB-027 basis.

## Checked by the drafter (scratch copy)
- `--do` twice: the second run changes nothing (checksum identical); 35 lines added; 520 items, keys sorted, one rater (`maldun`).
- `req_plausibility` over all requirements: exit 0, 0 tracebacks, **no error** (before: the five missing records).
- T-09 was running in the same worktree at that time; the scratch copy was taken from the committed state.

## Install
```
bash tools/apply_amendment_a99.sh --report     # look only
bash tools/apply_amendment_a99.sh --do         # then commit "plan: A-99 installed"
```
