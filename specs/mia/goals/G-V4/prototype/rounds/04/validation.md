# Prototype validation: G-V4, round 04 (G-V4.GRAPHAPI.RULES)

<!-- Written for the owner after CP19, filled during and after the session. The owner, not the agent, judges. One row per outcome of the scope and one per open decision. -->

Validated by: maldun
Date: 22.11.2026 · Prototype state: branch prototype/g-v4 · Where it ran: here

## Outcomes
| Item | What the user tried (Given / When from the outcome) | What was observed | Result (met / partly / not met / not tried) | Finding |
|---|---|---|---|---|
| FR-63 (OC-1) | Given the worktree, run `./proto.sh proto_checks/cp19_check.py`: read the lines "OC-1": two graphs that each break three rules give the same list (rule, parts, order) when saved, through the check route, when kept and before a run, five times in a row. Then `./proto.sh proto_checks/cp17_check.py`: the registry lines and the table "old case / old rule / new rules" | run by the owner 2026-11-22 (statement: "I have signed it, it worked"); cp19: 14 pass, the OC-1 lines as described | met | – |
| FR-63 (AC-017, by hand) | Given `./proto.sh proto_checks/make_sample_store.py /tmp/gs4 --broken` and `./proto.sh graph_proto_app.py --store files:/tmp/gs4` (log in as the owner): in the editor of `cp2.multi` connect `var.out` back to `step.write` and add a second connection into one data step; both rules are named in the fixed order, the cycle last; `Keep the change` is refused with the same rules | tried by the owner 2026-11-22 (statement: "I have signed it, it worked"): worked | met | – |
| FR-64 (OC-2) | Given `./proto.sh proto_checks/cp19_check.py`: the lines "OC-2" and "FR-64": refused runs name every broken rule, then the input nobody supplies; no step ran; a context graph is refused as `kind_cannot_run`, an unknown kind as `unknown_kind`; the 15 converted skills are ready once their inputs are given | run by the owner 2026-11-22 (statement: "I have signed it, it worked"); cp19: 14 pass, the OC-2 and FR-64 lines as described; the FINDING line is finding 10 of the report (Q-7) | met | – |
| FR-64 (AC-018, by hand) | Given the same page: "Try a run (stand-in steps)" on `sample.broken` (the connection `e2` named), on `chat@1` without values (`input.text` of `step.converse` named), with `{"input.text": "hello"}` (it runs), and on a working copy with a cycle (the cycle named) | tried by the owner 2026-11-22 (statement: "I have signed it, it worked"): worked | met | – |
| all other outcomes of rounds 01 to 03 | not in this round's scope; every check of those rounds was re-run after this round's changes (`cp1` to `cp15`, 60 page tests): all pass | re-run by the agent 2026-11-22: all pass; signed by the owner with the sheet | met | – |

## Decisions for the owner (from CP17 to CP19; the numbers are in `prototype-report.md`)
| ID | Question | Agent's proposal | Owner's decision |
|---|---|---|---|
| Q-1 (ASM-3) | Rule 7 "session setting and stop limit": a data step holding `stop` or `session`, more than one settings connection into one step, a loop-controlling step without a valid stop limit. No stored graph breaks it; 7 steps take settings by connection | confirm the definition | confirmed – Stefan Reiterer, by answer in the session 2026-11-22 (D-415) |
| Q-2 | Candidate rule "a processing step needs a tool": in the form "names a tool" no stored graph breaks it; in the form "names a tool the toolbox knows" the check needs the toolbox (not a pure check any more) | drop it from RULES (eight rules as FR-63 says); the known-tool form belongs to G-V4.GRAPHAPI.CODE (trust per step) | dropped from RULES; known tool to CODE – Stefan Reiterer, by answer in the session 2026-11-22 (D-415) |
| Q-3 | Context graphs: the context rule set uses the same definitions (rules 1, 3, 4); rule 4 then also refuses two identical connections with different IDs (3 of 500 generated context graphs), which CORE accepts today | take rule 4 in full for context graphs | rule 4 in full – Stefan Reiterer, by answer in the session 2026-11-22 (D-415) |
| Q-4 | Rule 1 of CP8 refused a slash in a step name; CORE allows it (REQ-GTB-029: the graph ID ends at the first slash). The prototype now follows CORE | allow the slash (as CORE) | allowed, as CORE – Stefan Reiterer, by answer in the session 2026-11-22 (D-415) |
| Q-5 | The cycle is not asked while a step name is broken or a connection has a missing end (an order needs known steps), so such a graph names the cycle only after the fix | keep it so | kept so – Stefan Reiterer, by answer in the session 2026-11-22 (D-415) |
| Q-6 | The document form (`workflows` table, IF-301 `validate`, used by IF-102, IF-104 v1, IF-203 and their suites) keeps the five older rule names and the first broken rule only | leave the document form as it is in RULES; it goes away with G-V4.MIGRATION; RULES covers every check of the stored graph form | left as it is; MIGRATION retires it – Stefan Reiterer, by answer in the session 2026-11-22 (D-415) |
| Q-7 | A graph of an unknown kind: the save path and the Storage layer refuse it as `schema_break` / `kind` (REQ-WFM-154, V-2), the check and the run as `unknown_kind` (D-404) | the check and the run say `unknown_kind`; the save keeps `schema_break` / `kind` (CORE, verified); the read-only listing of D-404 is planned where a store from a newer version can be met (TRANSFER or MIGRATION) | two names, listing later – Stefan Reiterer, by answer in the session 2026-11-22 (D-415) |

## Beyond the outcomes
-

## What this changes
| Finding | Goes to | Change |
|---|---|---|
| – | – | – |

Hand-over to Plan: the requirements of the subgoal are written with these results as evidence.
