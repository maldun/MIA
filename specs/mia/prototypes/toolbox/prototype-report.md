# Prototype report: toolbox (G-V2.TOOLBOX)

Status: Prototype (isolated, never merged; branch `prototype/toolbox`, folder `specs/mia/prototypes/toolbox/`). Its checks are the agent's own, not protected, never eval cases.

## Question
Do OC-1, OC-2, OC-3 of `specs/mia/goals/G-V2.TOOLBOX/goal.md` hold with a plain design: trust and lifecycle as two fields, owner-only trust, import that never runs code, retired items hidden but usable as baseline?

## What was built
- `toolbox.py` (one file, in memory): seed from `library/nodes` (REQ-WFM-056), import and export as one JSON file checked with the pinned `jsonschema` (REQ-WFM-055), `look_up`, `offer`, `set_trust`, `set_lifecycle`, `run`.
- `check_toolbox.py`: 7 checks, all pass with `/home/maldun/prog/Python/venvs/mia312/bin/python -I check_toolbox.py`. Marker file proves that import and untrusted runs execute no code.
- Reused: `library/nodes/*/*.json`, `jsonschema`. Not reused: `workflow_library.py` (its `set_status` is one mixed field for workflows, not transforms), `graph_run.py` (stub of MODEL).

## Check against the outcomes
| Outcome | Prototype | Check |
|---|---|---|
| OC-1 outside step untrusted, with reason, only owner can trust | yes, even when the file claims `trusted` | test_oc1 |
| OC-2 owner trusts, others refused with a reason | yes, status stays | test_oc2 |
| OC-3 retired: not offered, still a baseline | yes | test_oc3 |
| REQ-WFM-050, 051, 052, 053, 054, 055, 056, 067, 068, 070 | each shown once; none verified | see tests |

## Decisions (owner, 2026-11-08)
See `proposed-spec-changes.md`: D1 id only latest version, D2 same toolbox flagged shipped, D3 retired baseline with owner flag, D4 SC-09 stays as risk, D5 trust carries over. Prototype updated, 11 checks pass (adds the event on replace, REQ-WFM-093, and any-account untrust).

## Findings
1. A shipped node ID has several versions (e.g. `code.gate_abstain`: 2 files). REQ-WFM-050 says "ID unique in the toolbox" and REQ-WFM-055 carries a version. Open: is the toolbox key `id` or `id@version`? Prototype seeds the highest non-retired version per ID.
2. Shipped nodes are records without code text; export of them is refused. REQ-WFM-055 assumes code as text. Open: do shipped nodes belong in the same toolbox as exchangeable transforms?
3. "Trusted" gates running only through `run`; nothing stops another module from calling the code. The refusal point has to be named in Plan (MODEL refuses before any node runs, REQ-RUN-017).
4. Running a trusted imported transform is `exec` in the MIA process (SC-09, TD-24). The prototype makes the risk visible, it does not reduce it.
5. A retired and untrusted transform cannot be a baseline (run needs trust). Plausible, but REQ-WFM-068 does not say it.
6. Trust is set back to untrusted by anyone (prototype choice, not in a requirement).

## Assumptions
ASM-proto-1: one owner account identified by name; accounts come from IF-101. ASM-proto-2: evidence for `tested` is free text here, in Plan it is a named check or run.

## Carry-over (filled in by the owner, 2026-11-08)
| Item | Decision | Note |
|---|---|---|
| trust and lifecycle as two fields | adopt | REQ-WFM-051, 067 as they are |
| import stores untrusted whatever the file says | adopt | test_oc1 is the model for the acceptance test |
| `look_up` shows the reason | adopt | needs a new requirement, none exists today |
| seed from `library/nodes`, one entry per ID, shipped flag | adopt | version rule goes into REQ-WFM-056 |
| code in the MIA process (`exec`) | stand-in | until the sandbox goal (TD-24); SC-09 stays open |
| owner's allow-as-baseline flag | adopt | new requirement under REQ-WFM-068, own refusal test |
| newer version keeps trust and lifecycle (D5) | adopt as decided | known risk, see `proposed-spec-changes.md` |
| prototype checks and jsonschema file check | adapt | checks are the model for Plan's scenarios, code is rewritten; jsonschema check adopted |

Next: the proposed spec changes (`proposed-spec-changes.md`) go to Plan review; the TLS notes this prototype under risks and open questions.
