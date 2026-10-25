# Quality model: MIA

**Model:** ISO/IEC 25010:2023 (product quality), ISO/IEC 25019 (quality in use)   **Walked:** not yet (drafted 2026-10-25 from the approved HLS; the walk with the owner is open)   **Status:** Draft (amendment 5, proposed)

Open choice Q-1: the quality model. The draft assumes ISO/IEC 25010:2023, as the `quality.md` template does. A quality requirement (`Quality:` line) is written in Plan; this draft only says which HLS items carry each characteristic and where the owner has to say "not now".

## Context of use
- Users: the owner (develops, researches, administers) and a handful of trusted people with a local account (CON-6); no roles; skilled with a phone and a browser, not with the internals.
- Tasks: talk to the character, ask for sourced facts (lookup), later a literature review; edit workflows and the persona; give plus/minus feedback; the owner reads run logs and eval results.
- Environment: the owner's workstation (Fedora 43, Ryzen 9 5900X, RX 7800 XT 16 GB, podman); clients on phones and computers in the home network or the tailnet; local models only (MP-light for chat, MP-full for background work, which does not fit the GPU, D-40).
- Not covered: public internet exposure, more than a handful of users, paid APIs, languages other than English, safety-critical or regulated use, offline use of the chat page.

## Characteristics
| Characteristic | Requirements (IDs) or `not now` | Reason for `not now` | Step-up path (security, safety only) |
|---|---|---|---|
| Functional suitability | FR-1..FR-20; AC-2 (verification beats single voice on the holdout); NFR-4 (no invented sources) | | |
| Performance efficiency | NFR-7 (first text in 10 s on MP-light, budgets per run, fps), NFR-2, CON-2 | | |
| Compatibility | NFR-1 (browsers, widths), CON-3, FR-8 (model server); the interface between the three top nodes (decomposition, IF-101..IF-103) | | |
| Interaction capability | NFR-1 (accessibility, touch targets), FR-4 (transparency), FR-23 (mood in every situation) | | |
| Reliability | NFR-4 (honest confidence), NFR-8 (database, backups), FR-19 | availability targets (uptime) `not now`: one owner's workstation, restart is acceptable | |
| Security | NFR-3 (untrusted input stays data), NFR-5, NFR-6, FR-21, CON-4, CON-5; trust boundaries TB-user..TB-edit; threat model in Plan | | If MIA is ever exposed beyond trusted users: per-user permissions (CON-6 lifted), rate limits per account, audit log of edits, penetration test, update policy for the bill of materials |
| Maintainability | NFR-8, FR-20 (one development path), decomposition into nodes with contracts | | |
| Flexibility | FR-24 (character exchange), FR-8 (model switch), FR-32 (variants); portability to NVIDIA or CPU-only `not now` | NVIDIA and CPU-only modes exist but are not the target (3.4) | |
| Safety | `not now` | MIA controls nothing physical; the character gives no medical, legal or financial advice beyond what a sourced lookup returns (to confirm, Q-2) | If MIA acts on the world (calendar writes, e-mail, home control): redo as a safety analysis before the first such tool |

## Quality in use (judged in Validate, in the context above)
| Dimension | Measure | Target |
|---|---|---|
| Effectiveness | share of lookup answers whose verdicts and quotes the owner confirms in a sample; claims passed that are wrong (AC-2) | set in Plan from the T-06 baselines; not yet fixed |
| Efficiency | time to first text; queue wait with several users (NFR-7) | 10 s on MP-light; queue wait unmeasured (risk) |
| Satisfaction | plus/minus feedback per category (FR-27), the owner's weekly rating | to be fixed in Validate |
| Freedom from risk | no leak of private data in a query; no instruction from untrusted text obeyed (red-team cases) | 0 in the red-team suite |
| Context coverage | works on phone and desktop browsers; works inside the tailnet | NFR-1, NFR-6; Tailscale still untried |

## Open choices for the owner
- Q-1: ISO/IEC 25010:2023 as the quality model (alternative: a short own list).
- Q-2: Safety is `not now` for the reason above; confirm, or name the advice domains the character must refuse.
- Q-3: Reliability: is a stated restart time after a crash wanted (for example back up in 5 minutes), or is "restart by hand" enough?
