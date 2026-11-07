# A-96: the 31 records whose basis was reworded since the tag (for the owner's decision)

Compared: `plan-baseline-it2-store` against the current `specs/mia/plausibility.yaml`. 31 records, no rating changed. Per record: rating, rater and date in the tag and now, the old and the new basis text.

Decision needed per group: **keep the new text**, or **restore the old text**. Nothing is changed by this file.

## FR-40
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: all 12 refining requirements (REQ-GTB-005 to 016) are rated plausible and verified by TC-GTB-016, 006 to 015 and 017; PostgreSQL is part of the stack already (rated by the owner, D-260 rule for top-level items)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-005
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: node and edge records are plain rows with a JSON column; the behaviour is fixed by an exact acceptance criterion (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-006
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: as REQ-GTB-005 (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-007
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: as REQ-GTB-005 (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-008
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: as REQ-GTB-005 (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-009
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: the registry maps a type ID to a class; no number or model quality depends on it (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-010
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: a lookup that finds no class; no number depends on it (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-011
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: jsonschema 4.23.0 is installed on the host (D-187); schema checks of small JSON fields are exact (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-012
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: a static check of imports; no number depends on it (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-013
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: versions exist for workflows and context graphs already (TC-GTB-001: both tables versioned, neither deletable) (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-014
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: the 1000-seed property test follows TC-GTB-003, which already runs at stage 1 in under 2 minutes (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-015
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: the v1 and v0 suites exist and pass today; the document form is rebuilt from records (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-016
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: a refused write leaves the stored record alone; versions are written only after the checks pass; no number depends on it (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-017
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: a header is one row with a list of member IDs and versions; no number depends on it (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-018
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: a versioned row with four fields; the same kind of record as the older tables (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-019
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: a lookup of each named member version before the write; no number depends on it (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-GTB-020
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: a lookup of the two end nodes before the write; no number depends on it (proposal of the agent, 2026-11-07; rated by the owner)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-RUN-016
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-RUN-017
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: only the owner can set a transform trusted: the account that creates accounts (TC-MIA-014), basis of D-260 (B); the rest is an exact acceptance criterion on a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-RUN-018
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-RUN-019
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-WFM-040
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-WFM-041
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-WFM-042
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-WFM-043
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-WFM-044
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-WFM-045
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-WFM-046
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-WFM-047
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-WFM-048
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)

## REQ-WFM-049
- Rating: plausible (unchanged)
- Rated: tag 2026-11-07 by maldun; now 2026-11-07 by Stefan Reiterer
- Old basis: no number, measurement or model quality depends on it; the behaviour is fixed by an exact acceptance criterion on plain data and a scripted run, no model (proposal of the agent, 2026-11-07, G-V2.MODEL; rated by the owner 2026-11-07)
- New basis: no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)
