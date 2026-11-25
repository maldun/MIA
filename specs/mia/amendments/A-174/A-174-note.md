# A-174 – IF-104 v2 case IDs renumbered (G-V4.VIEW)

**Decided:** D-440 (1), owner, 2026-11-22. **Installs:** `bash tools/apply_amendment_a174.sh --do` (the owner runs it, or says "approved").

The A-171 suites numbered the v2 cases TC-IF-104-06 to 16; TC-IF-104-06 and 07 were already v1 cases (A-60, A-66). The v2 cases become TC-IF-104-17 to 27 (installed n becomes n + 11). Changed: the case IDs in `tests/acceptance/contract/test_if_104_v2_graph_api.py` and `.test.mjs`, nothing else. Not changed: the staged A-171 copies (a record of what was installed then), the contract text (it names no case), the v1 suites. Outside the protected files the same decision updates the "Verified by" lines of REQ-API-018 to 050 in `specs/mia/goals/G-V4.VIEW/requirements.md` and the test spec.
