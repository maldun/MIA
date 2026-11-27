# A-190: the answer step of a stored graph, and the graph run on its own (G-V4.GRAPHAPI.RUN T-03, 2026-11-27)

Status: **for the owner's approval (D-485).** Within RUN's own line of work; no frozen requirement and no interface (IF-301) changes.

- Found in T-03: the stored form of a graph names no answer step. A run from the store takes the answer from the data step the skill's pipeline names as
  its `result` (converted in memory for that name only; the stored graph is what runs), as the in-memory converted run does. Research has 22 data steps
  that no step reads; its answer is `var.answer#2`. No requirement said so. Owner (questionnaire, 2026-11-27): "We specify this behavior as a
  requirement. It makes sense, not every step wants to give an answer." -> **REQ-RUN-046** (Draft), checked by **TC-RUN-048** (each of the six
  skills from its stored graph gives the answer the oracle recorded for the old runner).
- Owner (questionnaire, 2026-11-27, raised from the decision of the TRANSFER session that packaging the runner belongs to RUN): re-use of the graph
  runner outside MIA means a **module boundary only**, specified together with the answer step -> **REQ-RUN-047** (Draft): `graph_run.py` and
  `graph_rule_set.py` import only the standard library, networkx and each other; checked by **TC-RUN-049** (inspection with `ast`, with a sound twin).
  For it `order_of` moves from `graph_model.py` into `graph_rule_set.py`; `graph_model.order_of` stays the same function for its callers (TC-WFM-185, 186).
- Also in T-03 on the owner's word (same questionnaire): `run_explain show` prints `graph <id>, version <n>` for a run from the store (the
  demonstrator of T-03; `run_explain.py` was not in T-03's Touches). Not part of this amendment's protected material; recorded in the plan's Touches.
- Changed: the goal's `requirements.md` (REQ-RUN-046, 047 new, Draft; group table), `test-spec.md` (TC-RUN-048, 049: rows, edge inputs, scenarios),
  `test-requirements.md` (TR-RUN-002, 005, 007, 009 apply to the new checks; TR-RUN-007 names two more defects), `plan.md` (T-03: implements,
  tests, touches, defects), `tests/acceptance/test_stored_graph_run.py` (TC-RUN-048), `tests/acceptance/test_run_graph_order.py` (TC-RUN-049).
- Open point (not decided here): if an edited stored graph has no data step with the result's ID, the run today ends `done` with no answer (None).
  An error naming the missing step would be clearer; that is another requirement, if wanted.
- Install: `bash tools/apply_amendment_a190.sh` (diff), then `--do`. Expected right after the install, before the rest of the T-03 code:
  TC-RUN-048 green, TC-RUN-049 red (`graph_run.py` still imports `graph_model`), everything else in the two files green.
