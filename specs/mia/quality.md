# Quality model: MIA

**Model:** ISO/IEC 25010:2023 (product quality), ISO/IEC 25019 (quality in use)   **Walked:** 2026-10-25 with the owner (decisions Q-1..Q-3)   **Status:** Approved by the owner 2026-10-25, the rows of the usability work added 2026-10-29 (A-26, to be approved) (amendment 5, D-45); the walk of the characteristics against requirements is done in Plan

Q-1 (decided): ISO/IEC 25010:2023. A quality requirement (`Quality:` line) is written in Plan; this draft only says which HLS items carry each characteristic and where the owner has to say "not now".

## Context of use
- Users: the owner (develops, researches, administers) and a handful of trusted people with a local account (CON-6); no roles; skilled with a phone and a browser, not with the internals.
- Tasks: talk to the character, ask for sourced facts (lookup), later a literature review; edit workflows and the persona; give plus/minus feedback; the owner reads run logs and eval results.
- Environment: the owner's workstation (Fedora 43, Ryzen 9 5900X, RX 7800 XT 16 GB, podman); clients on phones and computers in the home network or the tailnet; local models only (MP-light for chat, MP-full for background work, which does not fit the GPU, D-40).
- Not covered: public internet exposure, more than a handful of users, paid APIs, languages other than English, safety-critical or regulated use, offline use of the chat page.

## Characteristics
| Characteristic | Requirements (IDs) or `not now` | Reason for `not now` | Step-up path (security, safety only) |
|---|---|---|---|
| Functional suitability | FR-1 as the model case; the other FR-n of HLS 3.1 by their acceptance criteria AC-1..AC-29 (test-spec.md); AC-2 (verification beats single voice on the holdout); REQ-WFM-019 (a review ends with a named end); also WFM-030, -032, -036, -038 by their acceptance criteria |  |  |
| Performance efficiency | NFR-7 (first text in 10 s on MP-light, budgets per run, fps), NFR-2, CON-2; REQ-WFM-031 (status updates at most twice per second); also WFM-032, -034: numbers instead of a sign of life, hard caps instead of a question at every limit | | |
| Compatibility | FR-24 (VRoid .vrm models), CON-3 (technology); browsers and widths are under interaction capability, the model switch under flexibility; the interfaces between the nodes are under contract (`contracts/`, `decomposition.yaml`) |  |  |
| Interaction capability | NFR-1 (accessibility, devices, browsers, touch targets), FR-4 (transparency), FR-23 (mood in every situation); REQ-CLV-023 (the status card with pause, resume and stop); also CLV-024 (the files list), WFM-036 (the result is the newest message) |  |  |
| Reliability | NFR-4 (honest confidence), FR-19 (orderly shutdown, backup and restore); REQ-WFM-033 (a task can be paused and stopped); also WFM-034: a run ends at a hard cap with its result as it stands, a failing files volume does not take the report away | availability targets `not now` (Q-3): restart by hand after a crash |  |
| Security | NFR-3 (untrusted input stays data), NFR-5, NFR-6, FR-21, CON-4, CON-5; trust boundaries TB-user..TB-edit; threat model in Plan; REQ-WFM-037 (names, types and sizes of stored files are checked, nothing leaves the files volume, no delete route); an extension is code of the repository (Q-4) | | If MIA is ever exposed beyond trusted users: per-user permissions (CON-6 lifted), rate limits per account, audit log of edits, penetration test, update policy for the bill of materials |
| Maintainability | NFR-8 (database, backups, one door to the state), FR-20 (one development path), decomposition into nodes with contracts; REQ-WFM-039 (a skill is one folder with a manifest, the core names no skill); also WFM-029: the id is the command |  |  |
| Flexibility | FR-8 (model switch), FR-32 (variants); REQ-WFM-035 (a model is local or paid; the paid one gets slices and a warning) | NVIDIA and CPU-only modes exist but are not the target (3.4) |  |
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

## Added 2026-10-29 (A-26, proposal for the owner)
- Q-4 (proposed): an extension (a folder in `extensions/`) is code of the repository, reviewed like any code; the loader imports it from the repository folder at the start and installs nothing from the network or from a user. If skills are ever shared between people or installed from outside, redo the security row first (signed folders, a permission list per skill).
- Quality in use, efficiency: for a long task the owner can see where it is (numbers, not a sign of life) and can pause it. Measure in Validate: how often a review is paused or stopped by the owner, and how often it ends at a hard cap.
