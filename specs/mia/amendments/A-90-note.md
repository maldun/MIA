# A-90: interfaces of the skill rework foundation (G-V2)

Status: **approved 2026-11-07** by the owner as written (D-188); not yet applied: the contract files and the protected contract suites change in Plan step 4, with the contract text reviewed by the owner first. Decisions behind it: D-186, D-187, interview rows 12, 22.

| Interface | Change |
|---|---|
| IF-301 graph tables, v1 to v2 | node and edge records with a fixed `type` and a JSON field (REQ-GTB-005 to -008); node kinds `data`, `transform`, `master` besides today's `process`; `validate` also reports unknown type IDs and schema breaks (REQ-GTB-009 to -011); the document form of v1 stays readable during the transition (REQ-GTB-015); two more versioned tables, `graphs` (header and pinned members, REQ-GTB-017, 019) and `skills` (REQ-GTB-018), added by D-264 |
| IF-203 workflow library, v0 to v1 | new kinds `skills`, `transforms`, `snapshots` besides `workflows`, `context_graphs`; `set_status` is split into trust (`set_trust`, owner only) and lifecycle (`set_lifecycle`, with named evidence) for transforms; the four workflow states stay (later amendment); snapshot operations `snapshot`, `list_snapshots`, `restore_snapshot` (owner only) |
| IF-202 run workflow | a run is refused with the name of an untrusted transform or a master node (REQ-RUN-017, -018) |
| IF-102 storage interface | no change expected; node and edge tables are new tables of IF-301 |

## Not changed here
Tests in `tests/acceptance/contract/` for IF-301 and IF-203 (protected): new versions of the suites are written in Step 4 outside the implementing session; the v1 and v0 suites keep passing on the document form (REQ-GTB-015).
