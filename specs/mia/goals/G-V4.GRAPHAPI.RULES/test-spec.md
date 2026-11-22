# Test specification: G-V4.GRAPHAPI.RULES

**Requirements:** `requirements.md` (REQ-GTB-033 to 052, REQ-WFM-162 to 165, REQ-RUN-036 to 039; changes of REQ-WFM-150, 154, 155; all approved 2026-11-22)   **High-level spec:** HR-004 to HR-006 (measures)   **Contract:** IF-301 v4 (`specs/mia/amendments/A-170/IF-301-graph-tables.md`, D-419)   **Status:** Approved by the owner (scenarios by group, 2026-11-22, D-422)

All checks are exact: every expected value is a rule name, an ID, an order, a count or an equality, so no statistical check is needed; the high-level spec has no hard bound (D-416 (4)), so no benchmark. The accepted cases (`specs/mia/goals/G-V4/accepted-cases.md`) are witnessed by TC-GTB-046 and TC-WFM-180 (AC-017) and by TC-RUN-036, TC-RUN-037 and TC-GTB-044 (AC-018). The rule set is pure, so its checks need no store; the save checks run on the files backend (HR-004 reference): a refusal happens before the first write (REQ-WFM-146), and CORE's TC-GTB-036 already shows both backends refuse alike.

Scratch run of 2026-11-22 (prototype rule set in front of the runner): no protected test needs a change (TC-RUN-016, 017, 033, 034, TC-WFM-164, 168 and the three `check_graph(...) == []` tests stay green). One unit check changes in Implement: the self-loop case of `tests/test_graph_run_findings.py` now also names `adjacency` (REQ-GTB-045).

## Test cases
| Test ID | Verifies | Level | Setup / inputs | Expected result | Limit / tolerance |
|---|---|---|---|---|---|
| TC-GTB-037 | REQ-GTB-033, REQ-GTB-034, REQ-GTB-035, REQ-GTB-036 | unit | `kinds()` | exactly the kinds `workflow` and `context`; `workflow`: the eight rule names in order, runs yes; `context`: `step_identity`, `connection_endpoints`, `duplicate_connection`, runs no; changing the returned value does not change the next answer | exact |
| TC-GTB-038 | REQ-GTB-035 | unit | a context graph with two connections `e1`, `e2` from `c1` to `c2` (no role, no name); a context graph with a cycle between steps of one category and two connected steps of one category | the first gives exactly `duplicate_connection` naming `e2`; the second gives `[]` (none of rules 2, 5 to 8 applies) | exact |
| TC-GTB-039 | REQ-GTB-037, REQ-GTB-038 | unit | a workflow graph with a connection to a missing step and two writers of one data step; a sound workflow graph; both again without the field `kind` | exactly two items, `connection_endpoints` before `single_writer`, each with its parts and the fixed sentence; the sound graph gives `[]`; without `kind` the reports are equal | exact |
| TC-GTB-040 | REQ-GTB-039 | unit | the graph of TC-GTB-039 plus a cycle, under the kinds `swarm`, `""` and `5` | exactly one item `unknown_kind` naming `swarm`, `` and `5` | exact |
| TC-GTB-041 | REQ-GTB-040 | unit | five malformed graphs: a step that is `5`, connection data that is `[]`, a step without `id`, a connection without `from`, `nodes` that is `"x"`; a graph that is a list | each returns a list, no exception, with the items of the paragraph "Malformed input" of IF-301 v4 | exact |
| TC-GTB-042 | REQ-GTB-041, REQ-GTB-042, REQ-GTB-043, REQ-GTB-044, REQ-GTB-045, REQ-GTB-046, REQ-GTB-047, REQ-GTB-048 | unit | one small graph per rule that breaks only that rule, and its sound twin (the cases in the scenario) | each broken graph gives exactly one item with that rule and the named parts; each twin gives `[]` | exact |
| TC-GTB-043 | REQ-GTB-049, REQ-GTB-050 | unit | a context graph; a graph of kind `swarm` with a cycle; a workflow graph with two writers and an unsupplied input; the converted `chat` skill with `{"input.text": "hello"}` | refused with only `kind_cannot_run` (`context`); refused with only `unknown_kind` (`swarm`); refused with `single_writer` first and the input second; ready with `[]` | exact |
| TC-GTB-044 | REQ-GTB-051 | unit | the converted `chat` skill without values; the same with a graph value on `input.text`; a data step written by another step; a settings and an order connection from data steps without values | one item `unsupplied_input`, step `step.converse`, input `input.text`; no item for the graph value, the written step, the settings and the order connection | exact |
| TC-GTB-045 | REQ-GTB-052 | contract | the contract suites of IF-301 v1, v2, v3, IF-102, IF-104 v1 (Python and JS) and IF-203, unchanged, against the v4 code | every suite passes; the suite files are byte-identical to `goal/v4` | exact |
| TC-GTB-046 | REQ-GTB-037, REQ-WFM-163, REQ-RUN-037, HR-004 | component | the AC-017 graph plus an identical connection (three rules) and a graph with a connection to a missing step, two identical connections and a data step holding `session` (three rules); each sent through `rule_report`, the save, the check route (IF-104 v2 mock) and the run, five times each | the same items, rule by rule, with the same parts in the same order and the same sentences, at every entry point and in every repeat | 0 differences |
| TC-GTB-047 | REQ-GTB-034, HR-005 | component | the cases of TC-GTB-002 and the generator of TC-GTB-003, seeds 1 to 1000, each document turned into the stored form | 0 graphs refused by the five older rules and accepted by the eight, except a stop limit that REQ-WFM-048 accepts; the newly refused graphs counted by rule and printed | 0 lost |
| TC-WFM-179 | REQ-WFM-162 | component | a workflow graph with two identical connections | the save is refused naming `duplicate_connection`; the items equal `rule_report` of the same graph; nothing stored | exact |
| TC-WFM-180 | REQ-WFM-163, REQ-WFM-150 | component | the AC-017 graph | the save is refused; the refusal carries the rule report equal to `rule_report`, `single_writer` then `cycle`; the named IDs are the parts of both rules in order; no table grew | exact |
| TC-WFM-181 | REQ-WFM-164 | unit | a sound graph, `d1 → t1 → d1`, the AC-017 graph | `check_graph` gives `[]`, `["d1", "t1", "d1"]`, the parts of `single_writer` and then those of `cycle` | exact |
| TC-WFM-182 | REQ-WFM-165 | component | an empty store; the graph ID `never` | `graph_versions("never")` and `step_history("never", "a")` each fail with `not_found`; nothing is stored | exact |
| TC-WFM-183 | REQ-WFM-154 | component | a graph with `"kind": None` | refused naming `kind`; nothing stored | exact |
| TC-WFM-184 | REQ-WFM-155 | component | a context graph with two identical connections under different IDs; one with an empty step ID | each refused naming the rule (`duplicate_connection`, `step_identity`) and its parts; nothing written | exact |
| TC-RUN-036 | REQ-RUN-036 | component | seven graphs, one per refusal reason of HR-006 (cycle, two writers, connection to a missing step, two identical connections, unsupplied input, context graph, unknown kind); a marker function per step | each run ends `refused`; every marker was called 0 times; a sound twin runs and calls its markers | exact counts |
| TC-RUN-037 | REQ-RUN-037 | component | `wf-cycle` (`D1 → T1 → D2 → T2 → D1`); a graph whose connection `X8>T1` comes from a missing step; the converted `chat` skill without values | refused naming `D1, T1, D2, T2, D1`; `X8>T1`; `input.text` | exact lists |
| TC-RUN-038 | REQ-RUN-038 | component | a graph with a cycle and an untrusted transform; the same graph without the cycle | the first refused naming the cycle, no trust status; the second refused naming the untrusted transform and its status | exact |
| TC-RUN-039 | REQ-RUN-039 | component | the TC-RUN-034 graph (`DB` read by a Stage `T` with a prepare function, no value anywhere); the same graph with a plain function for `T` | the first runs (`done`); the second is refused naming `DB` and `T` was not called | exact |
| TC-RUN-040 | REQ-RUN-036, HR-006 | component | the 15 converted skill graphs, each with a value for each of its unsupplied inputs | each run check is ready; no skill is refused by a rule | 15 of 15 |

### Contract suite IF-301 v4 (`tests/acceptance/contract/test_if_301_v4_rule_set.py`, real side and mock side)
| Test ID | Golden | Verifies | Expected result |
|---|---|---|---|
| TC-IF-301-27 | 24 | REQ-GTB-033, REQ-GTB-034, REQ-GTB-035, REQ-GTB-036 | `kinds()` as in the contract; a changed copy changes nothing |
| TC-IF-301-28 | 25 | REQ-GTB-037, REQ-GTB-038 | the converted `chat` skill gives `[]`, with and without `kind` |
| TC-IF-301-29 | 26 | REQ-GTB-037, REQ-GTB-046, REQ-GTB-048 | `single_writer ["d1"]`, then `cycle ["d1", "t1", "d1"]` |
| TC-IF-301-30 | 27 | REQ-GTB-043, REQ-GTB-048 | `connection_endpoints ["e9"]`, `single_writer ["d1"]`, no `cycle` |
| TC-IF-301-31 | 28 | REQ-GTB-035 | `duplicate_connection ["e2"]`; the context cycle gives `[]` |
| TC-IF-301-32 | 29 | REQ-GTB-039, REQ-GTB-049 | `unknown_kind` alone in both operations; `kind_cannot_run` alone for a context graph |
| TC-IF-301-33 | 30 | REQ-GTB-050, REQ-GTB-051 | `unsupplied_input` of `step.converse` at `input.text`; ready with `"hello"` and with `None` |
| TC-IF-301-34 | 31 | REQ-GTB-040 | five malformed graphs, each a list, no exception |

## Edge inputs (per rule: zero, empty, missing, at and past the limit; per pair of rules acting on the same data)
| Rule (REQ) | Edge or pair | Test ID | Expected result |
|---|---|---|---|
| REQ-GTB-041 | a slash inside a step ID (`x/y`) | TC-GTB-042 | no item (Q-4) |
| REQ-GTB-041 | the empty ID and a repeated ID in one graph | TC-GTB-042 | one item naming both |
| REQ-GTB-044 and REQ-GTB-046 | two connections from `t1` into `d` | TC-GTB-042 | `duplicate_connection` only, no `single_writer` |
| REQ-GTB-044 | two connections that differ only in `as` | TC-GTB-042 | no item |
| REQ-GTB-045 and REQ-GTB-048 | a transform connected to itself | TC-GTB-042 | `adjacency` and `cycle` (`["T1", "T1"]`) |
| REQ-GTB-043 and REQ-GTB-045 | a connection from a data step to a missing step | TC-GTB-042 | `connection_endpoints` only |
| REQ-GTB-047 | `{"max_seconds": 1.0}`, `{"max_repetitions": 0}`, `{"max_repetitions": true}`, no `stop` | TC-GTB-042 | the first valid, the other three named |
| REQ-GTB-047 and REQ-RUN-033 | a transform with two settings connections | TC-GTB-042, TC-RUN-036 | `stop_limit` naming the transform; the run is refused before REQ-RUN-033's check |
| REQ-GTB-048 | a cycle while rule 1 or rule 3 is broken | TC-GTB-042, TC-IF-301-30 | no `cycle` item |
| REQ-GTB-051 | a graph value of `null` | TC-GTB-044 | counts as no start value: named |
| REQ-GTB-051 | a given value of `None` | TC-IF-301-33 | counts as given: not named |
| REQ-GTB-049 and REQ-GTB-050 | a context graph that also breaks rule 4 | TC-GTB-043 | only `kind_cannot_run` |

## Statistical checks (M19)
None: no result of this subgoal is random or noisy. TC-GTB-047 uses the fixed generator of TC-GTB-003 over a fixed seed range as a corpus, not as a sample.

## Benchmarks and baselines
None: no hard bound and no time budget (D-416 (4)); the prototype measured 1.4 ms for a 500-step chain.

## Smoke tests (run in Phase 6, target environment)
| Test ID | Verifies | Target | Conditions | Expected result |
|---|---|---|---|---|
| SMOKE-RULES-001 | REQ-RUN-036, HR-006 | the owner's host, the installed release, a throw-away files store | the 15 skills run checked with their usual inputs; the round 04 sample `sample.broken` run | each skill ready; `sample.broken` refused naming `e2`, no step run |

## Validation criteria (checked in Phase 7)
| ID | Criterion | How we check | Who | Agreement (if numeric): margin, mean or single values, method |
|---|---|---|---|---|
| VAL-RULES-01 | FR-63 and FR-64 hold for the deployed version as they held in the prototype (round 04: AC-017, AC-018) | the owner repeats the steps of AC-017 and AC-018 on the deployed version | Stefan Reiterer (owner) | single values: every line passes |

## Scenarios
<!-- one block per check of the tables above, in plain language, approved before the check is built -->

### TC-GTB-037 – The registry names two kinds
- Verifies: REQ-GTB-033, REQ-GTB-034, REQ-GTB-035, REQ-GTB-036
- Given: the rule set of IF-301 v4, nothing else
- When: the registry of kinds is read twice, the first answer changed in between
- Then: it names exactly the kinds `workflow` and `context`
- And: `workflow` lists `step_identity`, `step_kind`, `connection_endpoints`, `duplicate_connection`, `adjacency`, `single_writer`, `stop_limit`, `cycle` in this order and can run; `context` lists `step_identity`, `connection_endpoints`, `duplicate_connection` and cannot run
- And: the second answer is unchanged by the change of the first

### TC-GTB-038 – A context graph has three rules
- Verifies: REQ-GTB-035
- Given: a context graph with steps `c1`, `c2` of one category and two connections `e1`, `e2` from `c1` to `c2` without role or name; a second context graph with `c1 → c2 → c1`
- When: each is checked
- Then: the first gives exactly one item, `duplicate_connection` naming `e2` (Q-3: rule 4 in full)
- And: the second gives an empty list: a cycle and two connected steps of one category break no rule of the context kind

### TC-GTB-039 – The rule report lists every broken rule in order
- Verifies: REQ-GTB-037, REQ-GTB-038
- Given: a workflow graph with a connection `e9` to the missing step `z` and two transforms writing the data step `d`; a sound workflow graph; both once more without the field `kind`
- When: each is checked
- Then: the broken graph gives exactly two items, `connection_endpoints` naming `e9` and then `single_writer` naming `d`, each with its fixed sentence
- And: the sound graph gives an empty list
- And: the graphs without `kind` give the same reports as with `"kind": "workflow"`

### TC-GTB-040 – An unknown kind is the only item
- Verifies: REQ-GTB-039
- Given: the broken graph of TC-GTB-039 plus a cycle, under the kinds `swarm`, the empty text and the number 5
- When: each is checked
- Then: each report is exactly one item `unknown_kind`, naming `swarm`, the empty text and `5`; none of the broken rules is listed

### TC-GTB-041 – A malformed graph never makes the check fail
- Verifies: REQ-GTB-040
- Given: six inputs: a step that is the number 5, connection data that is a list, a step without `id`, a connection without `from`, `nodes` that is the text `"x"`, and a graph that is a list
- When: each is checked
- Then: each check returns a list and no exception escapes
- And: the items are those of IF-301 v4 "Malformed input": rule 1 for the bad steps (`5`, `None`) and for `nodes` (`nodes`), rule 3 for the connection without `from`, the list data counted as empty data, rule 1 naming `graph` for the list (D-418 (2))

### TC-GTB-042 – Each rule finds what it is for, and nothing else
- Verifies: REQ-GTB-041, REQ-GTB-042, REQ-GTB-043, REQ-GTB-044, REQ-GTB-045, REQ-GTB-046, REQ-GTB-047, REQ-GTB-048
- Given: for each rule a small workflow graph that breaks only that rule, and a sound twin that differs in one place:
  - rule 1: steps `a`, `a` and `` (twin: `a`, `b`, `x/y`)
  - rule 2: a step of type `loop` (twin: type `transform`)
  - rule 3: connection `e2` from `a` to the missing `z` (twin: to `b`)
  - rule 4: `e1`, `e2` both from `d` to `t` without role and name (twin: `as` `x` and `y`)
  - rule 5: `d1 → d2` and `t1 → m1` (twin: `d1 → t1 → d2`)
  - rule 6: `t1` and `t2` both into `d` (twin: `t2` into `d2`)
  - rule 7: a master without `stop`, one with `{"max_repetitions": 0}`, a data step with `session`, a transform with two settings connections (twin: `{"max_seconds": 1.0}`, one settings connection)
  - rule 8: `d1 → t1 → d1` (twin: `d1 → t1 → d2`)
- When: each graph is checked
- Then: each broken graph gives exactly one item with its rule and the named parts (rule 8: `d1, t1, d1`); each twin gives an empty list
- And: the edge pairs of the table "Edge inputs" give the results listed there (two connections `t1 → d`: rule 4 only; a self-loop: rules 5 and 8; a cycle with a missing end: no rule 8)

### TC-GTB-043 – The run check: kind first and alone, then rules, then inputs
- Verifies: REQ-GTB-049, REQ-GTB-050
- Given: a context graph that also has two identical connections; a graph of kind `swarm` with a cycle; a workflow graph with two writers of `d` and a step reading the unsupplied `q`; the converted `chat` skill
- When: each is checked for a run, `chat` with `{"input.text": "hello"}`
- Then: the context graph is refused with only `kind_cannot_run` naming `context`; `swarm` with only `unknown_kind` naming `swarm`
- And: the workflow graph is refused with `single_writer` (`d`) first and the unsupplied input (`q`) second
- And: `chat` with its value is ready with an empty list (AC-018)

### TC-GTB-044 – An input nobody supplies is named with its step
- Verifies: REQ-GTB-051
- Given: the converted `chat` skill without values; the same with a graph value on `input.text`; a transform reading a data step another transform writes; a transform with a settings connection and an order connection from data steps that have no values; a data step whose graph value is `null`
- When: each is checked for a run, with no values given
- Then: `chat` gives one item `unsupplied_input`, step `step.converse`, input `input.text` (AC-018)
- And: the graph value, the written data step, the settings and the order connection give no item; the `null` graph value is named

### TC-GTB-045 – The document form is unchanged
- Verifies: REQ-GTB-052
- Given: the contract suites of IF-301 v1, v2 and v3, IF-102, IF-104 v1 (Python and JS) and IF-203 as they are on `goal/v4`
- When: they run against the code with IF-301 v4
- Then: every suite passes and every suite file is byte-identical to `goal/v4`

### TC-GTB-046 – The same list at every entry point
- Verifies: REQ-GTB-037, REQ-WFM-163, REQ-RUN-037, HR-004
- Given: two graphs that each break three rules: the AC-017 graph (a cycle and a second writer into one data step) plus a second, identical connection `d1 → t1` (`duplicate_connection`, `single_writer`, `cycle`; an empty step name would hide the cycle, Q-5) and a graph with a connection to a missing step, two identical connections and a data step holding `session`; a files store; the check route of IF-104 v2 as a mock that answers with the rule report (D-416 (2))
- When: each graph is checked through the rule report, saved, sent to the check route and run, five times in a row each
- Then: every entry point gives the same items, rule by rule, with the same parts in the same order and the same sentences, in all five repeats (0 differences)
- And: witnesses AC-017

### TC-GTB-047 – No old refusal is lost
- Verifies: REQ-GTB-034, HR-005
- Given: the cases of TC-GTB-002 and the generator of TC-GTB-003 with seeds 1 to 1000, each document turned into the stored form with `from_document`
- When: each graph is checked by the five older rules (document form) and by the eight rules
- Then: no graph is refused by the five and accepted by the eight, except a stop limit that REQ-WFM-048 accepts (`max_seconds: 1.0`)
- And: the graphs that only the eight refuse are counted by rule and printed (the prototype: 57, of them 42 `duplicate_connection` and 15 `single_writer`; the count is reported, not asserted)

### TC-WFM-179 – A save uses the rule set of the kind
- Verifies: REQ-WFM-162
- Given: a files store; a workflow graph with two identical connections `e1`, `e2` (a rule the five older rules lack)
- When: it is saved
- Then: the save is refused naming `duplicate_connection` with `e2`
- And: the items equal the rule report of the same graph; nothing is stored

### TC-WFM-180 – A refused save carries every broken rule
- Verifies: REQ-WFM-163, REQ-WFM-150
- Given: a files store; the AC-017 graph (a cycle `d1 → t1 → d1` and a second writer `t2 → d1`)
- When: it is saved
- Then: the save is refused and carries the rule report: `single_writer` naming `d1`, then `cycle` naming `d1, t1, d1`, equal to the rule report of the same graph
- And: the named IDs are the parts of both rules in that order, repeats kept; no table grew
- And: witnesses AC-017

### TC-WFM-181 – `check_graph` stays the flat list
- Verifies: REQ-WFM-164
- Given: a sound workflow graph; `d1 → t1 → d1`; the AC-017 graph
- When: each is checked with `check_graph`
- Then: the answers are `[]`, `["d1", "t1", "d1"]`, and `["d1", "d1", "t1", "d1"]` (the parts of `single_writer`, then those of `cycle`)

### TC-WFM-182 – A graph that was never stored has no history
- Verifies: REQ-WFM-165
- Given: an empty files store
- When: the versions of the graph `never` and the history of its step `a` are asked
- Then: each fails with the reason `not_found`
- And: the store is still empty (CORE V-3, D-414)

### TC-WFM-183 – An empty kind is refused
- Verifies: REQ-WFM-154
- Given: a files store; a graph with `"kind": None`
- When: it is saved
- Then: the save is refused naming the field `kind` and nothing is stored (CORE V-2, D-414)

### TC-WFM-184 – A context graph is saved with the rules of its kind
- Verifies: REQ-WFM-155
- Given: a files store; a context graph with two identical connections under different IDs; a context graph with an empty step ID
- When: each is saved
- Then: the first is refused naming `duplicate_connection` and the second ID; the second is refused naming `step_identity`; nothing is written (Q-3, finding 7)

### TC-RUN-036 – No step runs when the run check refuses
- Verifies: REQ-RUN-036
- Given: seven graphs, one per refusal reason of HR-006: a cycle, two writers, a connection to a missing step, two identical connections, an unsupplied input, a context graph, a graph of kind `swarm`; every step is a marker function that counts its calls; a sound twin of the first
- When: each is run
- Then: each run ends `refused` and every marker was called 0 times
- And: the sound twin runs and every one of its markers was called once (the markers can fire)
- And: witnesses AC-018

### TC-RUN-037 – A refused run names every part, repeats kept
- Verifies: REQ-RUN-037
- Given: `wf-cycle` (`D1 → T1 → D2 → T2 → D1`); a graph whose connection `X8>T1` comes from the missing step `X8`; the converted `chat` skill
- When: each is run, `chat` without values
- Then: the runs are refused naming `D1, T1, D2, T2, D1`, then `X8>T1`, then `input.text`
- And: witnesses AC-018

### TC-RUN-038 – Trust is checked after the run check
- Verifies: REQ-RUN-038
- Given: a graph with a cycle and an untrusted transform `T2`; the same graph without the cycle
- When: each is run
- Then: the first is refused naming the cycle and no trust status
- And: the second is refused naming `T2` and its status `untrusted` (REQ-RUN-017)

### TC-RUN-039 – An input a prepare function may give is not refused
- Verifies: REQ-RUN-039
- Given: the graph of TC-RUN-034 (`DB` read by the Stage `T`, no value in the graph or the run), once with a prepare function on `T` that gives nothing, once with a plain function for `T`
- When: each is run
- Then: the first runs to `done` (D-418 (1))
- And: the second is refused naming `DB` and `T` was not called

### TC-RUN-040 – Today's skills still run
- Verifies: REQ-RUN-036, HR-006
- Given: the 15 converted skill graphs, each with the value `"x"` for each of its unsupplied inputs
- When: each is checked for a run
- Then: all 15 are ready; none is refused by a rule

### TC-IF-301-27 – The registry as the contract states it
- Verifies: REQ-GTB-033, REQ-GTB-034, REQ-GTB-035, REQ-GTB-036
- Given: golden example 24 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: the registry of kinds is read, changed and read again, against both
- Then: it equals the value in the table of operations, and the change does not reach the second answer
- And: the real module and the mock give the same answer

### TC-IF-301-28 – A sound skill breaks no rule
- Verifies: REQ-GTB-037, REQ-GTB-038
- Given: golden example 25 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: the converted `chat` skill is checked with and without its `kind`, against both
- Then: both reports are empty
- And: the real module and the mock give the same answer

### TC-IF-301-29 – Several rules, in order
- Verifies: REQ-GTB-037, REQ-GTB-046, REQ-GTB-048
- Given: golden example 26 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: the graph `d1 → t1 → d1` with a second writer `t2 → d1` is checked, against both
- Then: exactly `single_writer` naming `d1`, then `cycle` naming `d1, t1, d1`
- And: the real module and the mock give the same answer

### TC-IF-301-30 – The cycle waits for known steps
- Verifies: REQ-GTB-043, REQ-GTB-048
- Given: golden example 27 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: the graph of golden 26 plus `e9` to the missing `z` is checked, against both
- Then: `connection_endpoints` naming `e9`, `single_writer` naming `d1`, and no `cycle`
- And: the real module and the mock give the same answer

### TC-IF-301-31 – Context graphs keep rule 4
- Verifies: REQ-GTB-035
- Given: golden example 28 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: a context graph with `e1`, `e2` both from `c1` to `c2`, and one with a cycle, are checked, against both
- Then: the first gives only `duplicate_connection` naming `e2`; the second gives an empty list
- And: the real module and the mock give the same answer

### TC-IF-301-32 – An unknown kind and a kind that cannot run
- Verifies: REQ-GTB-039, REQ-GTB-049
- Given: golden example 29 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: a graph of kind `swarm` with a cycle is checked and run checked, and a context graph is run checked, against both
- Then: `swarm` gives only `unknown_kind` in both; the context graph is refused with only `kind_cannot_run`
- And: the real module and the mock give the same answer

### TC-IF-301-33 – Inputs given or not
- Verifies: REQ-GTB-050, REQ-GTB-051
- Given: golden example 30 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: the converted `chat` skill is run checked without values, with `"hello"` and with `None` for `input.text`, against both
- Then: refused with one `unsupplied_input` of `step.converse` at `input.text`; ready twice
- And: the real module and the mock give the same answer

### TC-IF-301-34 – Malformed graphs
- Verifies: REQ-GTB-040
- Given: golden example 31 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: the five malformed graphs of golden 31 are checked, against both
- Then: each gives a list with the items of "Malformed input", and no exception escapes
- And: the real module and the mock give the same answer

### SMOKE-RULES-001 – Skills run, a broken graph does not
- Verifies: REQ-RUN-036, HR-006
- Given: the owner's host with the installed release; a throw-away files store
- When: each of the 15 skills is run checked with its usual inputs, and the round 04 sample `sample.broken` is run
- Then: each skill's run check is ready; `sample.broken` is refused naming `e2` and no step ran
- And: the throw-away store is removed afterwards; MIA's own store is not written
