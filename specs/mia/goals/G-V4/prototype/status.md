# Prototype status: G-V4 (living prototype)

Single source for what the demonstrator can show (`dev-workflow/references/prototyping.md`). Updated with every checkpoint and at merges.

Demonstrator deployed at: not yet (worktree `../MIA-prototype-g-v4`, branch `prototype/g-v4`; round 01 ran from `serve.py files 8765`) · Last updated: set at the first checkpoint, 2026-11-20

| Part / feature | Requirement IDs | State (mock / working / real / not yet / retired) | Made real by task | Commit | Date | Notes |
|---|---|---|---|---|---|---|
| viewer page: list, drawing, left panel, settings menu, physics, rounded edges (round 01) | FR-48, FR-49, FR-51, FR-52, FR-53 | working | – | – | 2026-11-20 | built in round 01 from the stored record form; no login, no history, no editing; reuse decision: see reuse-map.md (not yet written) |
| graph routes for the stored form (round 01) | FR-48 | working | – | – | 2026-11-20 | two routes; to be replaced by the prototype of IF-104 v2 in CP5 |
| scoped record IDs | FR-60 | not yet | – | – | – | CP1 |
| atomic save, versions, authors | FR-57, NFR-16 | not yet | – | – | – | CP1 |
| same behaviour in files and database | FR-58 | not yet | – | – | – | CP2 |
| whole-store move | FR-59 | not yet | – | – | – | CP2 |
| sync live store to copy | FR-93, NFR-15 | not yet | – | – | – | CP3 |
| eight rules and the check route | FR-63, FR-64 | not yet | – | – | – | CP4 |
| graph backend with login, list, versions, history (IF-104 v2 draft) | FR-48, FR-55, NFR-12 | not yet | – | – | – | CP5 |
| kinds and trust marks, read-only fields, text-only display | FR-50, FR-51, FR-54 | not yet | – | – | – | CP6 |
| shared arrangement, history list with stepping | FR-52, FR-55 | not yet | – | – | – | CP7 |
| editor: change, rule feedback, keep, restore, undo | FR-68, FR-69, FR-70, FR-71, FR-72, FR-73, FR-91, FR-92, FR-95, NFR-19 | not yet | – | – | – | CP8, CP9 |
| arrangement saving, copy a step | FR-74, FR-94 | not yet | – | – | – | CP10 |
| edit log | FR-76, FR-77, FR-80, FR-81 | not yet | – | – | – | CP11 |
| playback and comparison | FR-78, FR-79, NFR-20 | not yet | – | – | – | CP12 |

States: `mock` = looks right or stands in, behavior faked; `working` = functional prototype code built by the agent, not verified; `real` = made or adopted by a normal task (tests first, verified); `not yet` = nothing to show; `retired` = removed or archived at the MVP.
