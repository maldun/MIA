# A-89: FR-7, FR-22 and FR-30 revised by the skill rework

Status: **proposed** (draft; applied to `requirements.md` and `baseline-requirements.md` in Plan of iteration 2). Decision: D-186 (owner, 2026-11-05), interview rows 12, 17, 22.

## What changes
| Requirement | Change |
|---|---|
| FR-7 Workflows as data | revised by FR-37: a workflow is a directed acyclic graph of data, transform and master nodes; the graph rules (unique identity, no cycle, stopping criterion) stay; storage as separate node and edge records (FR-40) |
| FR-22 Graph app | the library is vis-network (the owner's choice, row 17; Plan pins version and licence) and the page may be built with it; raw JSON editing validated by the server; **only the owner marks a transform trusted, everyone else edits data nodes and graphs** (exception to CON-6) |
| FR-30 Workflow context graph | revised by FR-41: context graphs are referenced by ID (a skill names exactly one, skills may share one, the chat has one); a trusted skill pins a version, a draft follows the latest; a new version marks dependent testbenches stale |
| CON-6 | exception: marking a transform trusted is the owner's act |

## Not done here
`requirements.md` and `baseline-requirements.md` are plan-phase artifacts and are not touched in Explore. Interfaces IF-301 and IF-203 and their protected contract suites change only through a plan amendment.

## Later amendments (decided 2026-11-07, D-187)
- Workflows get the same two independent states as transforms (trust: untrusted/trusted; lifecycle: draft/tested/retired) instead of the mixed list of REQ-WFM-002. Not in G-V2; REQ-WFM-002 stays as it is until that amendment.
