# Quality model: MIA

**Model:** ISO/IEC 25010:2023 (product quality), ISO/IEC 25019 (quality in use)   **Walked:** 2026-10-25 with the owner (decisions Q-1..Q-3)   **Status:** Approved by the owner 2026-10-25 (amendment 5, D-45); the walk of the characteristics against requirements is done in Plan

Q-1 (decided): ISO/IEC 25010:2023. A quality requirement (`Quality:` line) is written in Plan; this draft only says which HLS items carry each characteristic and where the owner has to say "not now".

## Context of use
- Users: the owner (develops, researches, administers) and a handful of trusted people with a local account (CON-6); no roles; skilled with a phone and a browser, not with the internals.
- Tasks: talk to the character, ask for sourced facts (lookup), later a literature review; edit workflows and the persona; give plus/minus feedback; the owner reads run logs and eval results.
- Environment: the owner's workstation (Fedora 43, Ryzen 9 5900X, RX 7800 XT 16 GB, podman); clients on phones and computers in the home network or the tailnet; local models only (MP-light for chat, MP-full for background work, which does not fit the GPU, D-40).
- Not covered: public internet exposure, more than a handful of users, paid APIs, languages other than English, safety-critical or regulated use, offline use of the chat page.

## Characteristics
| Characteristic | Requirements (IDs) or `not now` | Reason for `not now` | Step-up path (security, safety only) |
|---|---|---|---|
| Functional suitability | FR-1 as the model case; the other FR-n of HLS 3.1 by their acceptance criteria AC-1..AC-29 (test-spec.md); AC-2 (verification beats single voice on the holdout) |  |  |
| Performance efficiency | NFR-7 (first text in 10 s on MP-light, budgets per run, fps), NFR-2, CON-2 | | |
| Compatibility | FR-24 (VRoid .vrm models), CON-3 (technology); browsers and widths are under interaction capability, the model switch under flexibility; the interfaces between the nodes are under contract (`contracts/`, `decomposition.yaml`) |  |  |
| Interaction capability | NFR-1 (accessibility, devices, browsers, touch targets), FR-4 (transparency), FR-23 (mood in every situation) |  |  |
| Reliability | NFR-4 (honest confidence), FR-19 (orderly shutdown, backup and restore) | availability targets `not now` (Q-3): restart by hand after a crash |  |
| Security | NFR-3 (untrusted input stays data), NFR-5, NFR-6, FR-21, CON-4, CON-5; trust boundaries TB-user..TB-edit; threat model in Plan | | If MIA is ever exposed beyond trusted users: per-user permissions (CON-6 lifted), rate limits per account, audit log of edits, penetration test, update policy for the bill of materials |
| Maintainability | NFR-8 (database, backups, one door to the state), FR-20 (one development path), decomposition into nodes with contracts |  |  |
| Flexibility | FR-8 (model switch), FR-32 (variants) | NVIDIA and CPU-only modes exist but are not the target (3.4) |  |
| Safety | `not now` | decided by the owner (Q-2): no safety requirements at all; MIA controls nothing physical | If MIA acts on the world (calendar writes, e-mail, home control): redo as a safety analysis before the first such tool |

## Quality in use (judged in Validate, in the context above)
| Dimension | Measure | Target |
|---|---|---|
| Effectiveness | share of lookup answers whose verdicts and quotes the owner confirms in a sample; claims passed that are wrong (AC-2) | set in Plan from the T-06 baselines; not yet fixed |
| Efficiency | time to first text; queue wait with several users (NFR-7) | 10 s on MP-light; queue wait unmeasured (risk) |
| Satisfaction | plus/minus feedback per category (FR-27), the owner's weekly rating | to be fixed in Validate |
| Freedom from risk | no leak of private data in a query; no instruction from untrusted text obeyed (red-team cases) | 0 in the red-team suite |
| Context coverage | works on phone and desktop browsers; works inside the tailnet | NFR-1, NFR-6; Tailscale still untried |

## Decisions of the owner (2026-10-25)
- Q-1: ISO/IEC 25010:2023 is the quality model. Yes.
- Q-2: no safety requirements at all.
- Q-3: after a crash MIA is restarted by hand; no restart time is required.
