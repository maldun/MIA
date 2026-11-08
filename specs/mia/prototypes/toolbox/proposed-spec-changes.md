# Proposed spec changes for the toolbox (DRAFT, Status: Prototype, nothing applied)

Decisions of the owner, 2026-11-08 (questionnaire after the prototype):
D1 key = ID only, latest version (a newer version replaces the code) / D2 shipped nodes in the same toolbox, flagged shipped / D3 a retired untrusted transform may run as a baseline, once the owner has allowed it when retiring / D4 SC-09 stays, stated as a risk / D5 trust carries over to a newer version.

## AC-32 split (high-level-spec.md section 3, replaces the one row)
| ID | Outcome | Serves |
|---|---|---|
| AC-32a | Given a step that arrives from outside MIA, when someone looks it up, then it is shown as untrusted with the reason, it has not run, and a workflow that uses it does not run and says why. | FR-38, OC-1 |
| AC-32b | Given such a step, when the owner marks it trusted it is shown as trusted and runs; when anyone else tries, the change is refused with the reason and the status stays. | FR-38, OC-2 |
| AC-32c | Given a retired step, when someone looks for a step for a new workflow it is not offered; a check that names it as baseline still runs it, if it is trusted or the owner allowed it when retiring. | FR-38, OC-3 |

## FR-38 text (HLS line 87, aligned with requirements.md)
"MIA shall collect transforms in a toolbox, one entry per ID, and keep them in a form that can be stored and exchanged outside MIA. Each has a trust status (untrusted or trusted) that decides whether it runs, and a lifecycle (draft, tested, retired) that records its performance. An imported transform is untrusted until the owner marks it trusted; a node whose transform is not trusted does not run. A review process for exchanged transforms is a later goal."

## Requirement changes (N-2.3 requirements.md)
| Requirement | Change |
|---|---|
| REQ-WFM-050 | "unique ID"; a transform with the ID of an entry and a higher version replaces its code, one with an equal or lower version is refused |
| REQ-WFM-056 | add: shipped nodes are flagged shipped and cannot be exported (no code text) |
| REQ-WFM-055 | add: "export refused for a shipped node" |
| REQ-WFM-068 | add: "an untrusted retired transform runs as a baseline only if the owner allowed it when retiring it" |
| NEW (after 054) | "When a transform is replaced by a newer version, its trust status and lifecycle stay." (D5) |

## Risks for the gate
- D5 weakens OC-1/OC-2: after the owner trusts version 1, version 2 with different code runs without a new decision. Prototype test `test_newer_version_keeps_trust_older_is_refused` shows it. Consider logging version changes of trusted transforms.
- D4 / SC-09: trusted foreign code runs in the MIA process.
- D3: the baseline flag is a second owner-only act, needs its own refusal test.
