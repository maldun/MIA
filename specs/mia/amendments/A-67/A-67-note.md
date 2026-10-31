# A-67 – IF-302 v7: the deletable tables in full; the IF-302 reason in contract.py

**Decision:** D-170 (owner, 2026-10-31), N-3.3 re-verification R1 and R2. **Status:** draft, not installed. **Install:** `bash tools/apply_amendment_a67.sh --do` on goal/v1.

- **R2:** IF-302 named only `memory`, `tasks`, `memos` (deletable) and `votes`, `runs` (not). Code and mock make `history` deletable too and every other table not. v7 says "deletable are exactly `history`, `memory`, `tasks`, `memos`", and TC-IF-302-01 compares the whole set. Before, a provider with `history` not deletable or `source_trust` deletable passed the suite.
- **R1:** `tests/helpers/contract.py` gives IF-302 the reason "unused: real_subject gives record_tables", as A-60 did for IF-301.

No code changes: `record_tables.py` and the mock already define exactly these four deletable tables. Every file is built from the installed one at install time, so A-62, A-65 and A-66 may come before or after. Version and status of IF-302 in `decomposition.yaml` stay for the gate (D-170).
