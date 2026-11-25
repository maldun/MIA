# A-189: rule 3 names a connection without a non-empty text ID (G-V4.GRAPHAPI.RUN T-02, 2026-11-25)

Status: **for the owner's decision (D-483); a joint amendment of IF-301, which is frozen at G-V4.**

- Found in T-02 before any code changed: `load` leaves out a connection whose ID is missing, not text or repeated (REQ-GTB-057), so the rules that
  move onto the loaded graph (REQ-GTB-059) no longer see it. Probes against v4: a connection without an ID between two data steps was `adjacency
  ["None"]` and would be nothing; a connection with the ID 5 that closes a cycle was `cycle` and would be nothing; a repeated `e1` that makes a second
  writer was `duplicate_connection` plus `single_writer` and would keep only `duplicate_connection`. With nothing reported, `GraphModel.save_graph`
  reaches `_scoped` and raises `KeyError: 'id'` (reproduced with the rule report switched off). REQ-GTB-060 said "for every stored form".
- Owner's choice (questionnaire, 2026-11-25): rule 3 (`connection_endpoints`, on the stored form) also names a connection whose ID is not a non-empty
  text; a repeated ID is named by rule 4 as before; REQ-GTB-060 holds for stored forms whose connections have unique non-empty text IDs. None of the
  oracle's inputs (15 converted graphs, 500 random graphs, golden 24 to 31) has such a connection, so the oracle stays valid.
- Changed: REQ-GTB-043 (changed copy in the goal's `requirements.md`, Draft), REQ-GTB-060 (text and rationale; its Status line still says Approved:
  set it to Draft and approve again, as for REQ-WFM-167), IF-301 text (rule 3, malformed input, "What changes against v4" item 4, golden 36, decision 20,
  version history), the v5 mock (`_broken` overrides rule 3), the v5 suite (TC-IF-301-39), the real-side check TC-GTB-053 in `test_graph_loader.py`,
  the goal's `test-spec.md` and `test-requirements.md` (TR-RUN-001, 007, 010 apply to the new checks).
- Not changed: the sentence of rule 3 ("a connection leads to or from a step that does not exist"), because a new sentence would change the oracle's
  answers for golden 27 and 31; say so if a better sentence is wanted (another amendment, with the oracle re-recorded).
- Install: `bash tools/apply_amendment_a189.sh` (diff), then `--do`. Expected after the install, before the T-02 code: TC-GTB-053 red (the save of the
  graph without an ID raises today), TC-IF-301-39 green on the mock side and red on the real side, everything else as before.
