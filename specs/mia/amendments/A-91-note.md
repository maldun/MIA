# A-91: the real side of the IF-301 v2 contract suite runs without a skip (G-V2.STORE, T-05)

Status: **approved in principle by the owner, 2026-11-07** (plan.md of G-V2.STORE, "Decided by the owner", point 1); the script is a draft for a look-only review, not yet run with `--do`.

What it changes: `tests/acceptance/contract/test_if_301_v2_graph_tables.py` only. The function `subject(kind)` of the suite gave the real Graph tables only when the environment variable `IF301_V2_REAL=1` was set and otherwise skipped with "N-3.2 not integrated yet". After N-3.2 (T-01 to T-03) and the Storage layer (T-04) are built, the real side is part of the suite: `subject("real")` returns the real Graph tables (loaded with the real graph rules, as for IF-301 v1), the switch and the skip go. The cases, their expected values and the mock are not touched. This is the removal of the skip that decomposition rule 3 puts into the integration step of N-3.2.

Why an amendment: the suite is a protected file (the deny rules keep the implementing agent out); the owner installs the change.

Evidence it is safe to install (reported by the implementing session, 2026-11-07): the real side of all 15 cases passes with `IF301_V2_REAL=1` on the current branch; the script checks the same after the install and fails when a case is skipped.

Not changed: `tests/helpers/contract.py`, the v1 suite, the IF-203 v0 suite (TC-GTB-015 hashes them), the mock `tests/helpers/mocks/if_301_graph_tables_v2.py`, `contracts/IF-301-graph-tables.md`.
