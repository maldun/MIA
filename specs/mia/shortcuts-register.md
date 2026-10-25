# Path to product: shortcuts and exit criteria (MIA)

Blueprint M25. Draft of 2026-10-25 (amendment 5, proposed). Source of the entries: "Known shortcuts" in the HLS (section 2), the risk table and `KNOWN_RISKS.md`. Reviewed at each gate.

**Might become a product or enter a regulated use?** undecided, proposed answer **no** (a private assistant for a handful of trusted users; revisit if MIA is offered to people outside that circle). Open choice P-1.

## Shortcuts
| ID | Shortcut | Why taken | Risk if it stays | Resolved by (T-nn / TD-nn / DR-nnn) | Status |
|---|---|---|---|---|---|
| SC-01 | Persona is a shared parameter file outside git (`calibration.txt`) | prototype speed | persona changes are not versioned or reviewed | FR-25 (persona in the database) | open |
| SC-02 | Editor and chat use one shared token, no login | single user so far | anyone with the token can edit everything | FR-21 (accounts) | open |
| SC-03 | Tailscale access never tried against a real tailnet | no second device tried yet | NFR-6 unproven | owner test with a phone outside the network | open |
| SC-04 | Verification styles and research suites are starter-sized | cost of labelling | decisions come out NOT DECIDED or noise | suites with holdout (T-05..T-10 of `specs/number-gate`) | open |
| SC-05 | Evaluation labels set by the owner alone | one person available | label bias; no agreement figure beyond the audit (kappa 0.85 on 166 rows) | second labeller for the holdout, or accepted by the owner | open |
| SC-06 | SysML text was not parsed by a tool until the pilot parser check | no tool installed | model errors hidden | `tools/check_sysml.sh` (now available, run after every change) | open until all models pass |
| SC-07 | Users see and may edit everything, no roles (CON-6) | trusted circle | one wrong edit changes MIA for all | roles, only if the circle grows (quality.md step-up path) | accepted |
| SC-08 | MIA state is files and one SQLite index | built first | no sharing between apps | NFR-8, node N-3 (Database) | open |

## Exit criteria before leaving research use
- [ ] Every shortcut is resolved or explicitly accepted (owner, reason)
- [ ] Requirements are completed for the new use (quality model re-walked: `Safety` and `Security` no longer "basics only", `quality.md` step-up path done)
- [ ] Applicable standards and their owners identified: personal data of other users (GDPR) if the circle grows; none otherwise (to confirm, P-1)
- [ ] Responsible person signs off on every deferral that touches security, safety, legal or data protection
- [ ] Operation: runbook, monitoring and support owner in place (see O-1 in the HLS section 3.6)
- [ ] Licenses, bill of materials and disclosure of AI use are complete (`release_check.py`)
