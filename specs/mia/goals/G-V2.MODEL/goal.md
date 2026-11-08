# Goal G-V2.MODEL – Skill record and graph model

Drafted 2026-11-07 when the owner asked to split G-V2 into four subgoals for review and build (cut: STORE, MODEL, TRUST, CONVERT).

- Kind: subgoal
- Parent: G-V2
- Statement: A skill is one versioned record that names its command, workflow graph and context graph, and its graph consists of data, transform and master nodes under fixed rules.
- Exit criterion: OC-1, OC-2, OC-3, with the checks of its requirements below, and VAL-009 (`specs/mia/test-spec.md`) in the Validate of G-V2
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v2.model
- Subgoals: –
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a skill, when someone looks at what it is made of, then one description gives its command, its steps and the knowledge it uses | FR-36, FR-37, OC-2 |
| OC-2 | Given a description that breaks a rule of the graph (two writers of one piece of data, a loop, a second skill with the same command), when it is saved, then it is refused and the reason is given | FR-36, FR-37, OC-2 |
| OC-3 | Given a graph with steps in order, when it runs, then every step runs after the data it needs; a step that needs a decision from the owner, or a step that is not trusted, stops the run before it starts and says which one | FR-37, FR-38, OC-3 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| networkx | real | graph rules (D-187) |
| jsonschema | real | description check (D-187) |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| further cut | keep together | 14 items in scope, one chain | 2026-11-07 |

## Scope
Top-level items it serves: FR-36, FR-37. Requirements by ID (inside G-V2's scope):

| Item | In/Out | Reason |
|---|---|---|
| REQ-WFM-040 | in | |
| REQ-WFM-041 | in | |
| REQ-WFM-042 | in | |
| REQ-WFM-043 | in | |
| REQ-WFM-044 | in | |
| REQ-WFM-045 | in | |
| REQ-WFM-046 | in | |
| REQ-WFM-047 | in | |
| REQ-WFM-048 | in | |
| REQ-WFM-049 | in | |
| REQ-RUN-016 | in | |
| REQ-RUN-017 | in | |
| REQ-RUN-018 | in | |
| REQ-RUN-019 | in | added at review 2026-11-07 (failed node stops the run) |
| IF-301 | in | frozen at G-V2 (A-90, approved 2026-11-07); used through its mock until the provider is merged |
| IF-203 | in | frozen at G-V2 (A-90, approved 2026-11-07); used through its mock until the provider is merged |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.3 workflow management (skill record, graph model) | real |  |
| N-2.4.1 pipeline runner | real | topological order, refusal of untrusted nodes, master nodes run like transforms |
| N-3.2 graph tables | stand-in | IF-301 v2 mock until G-V2.STORE is merged |

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|
| – | – | see parent G-V2 |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| – | – | no subgoals |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | HLS of iteration 2 approved 2026-11-05 (D-186) |
| Plan | done | requirements REQ-WFM-040..049 and REQ-RUN-016..019 and checks approved (D-262..D-264, review of 2026-11-07); red tests installed (tags `plan-baseline-it2-model`, `plan-baseline-it2-model-installed`); `plan.md` approved 2026-11-07 (Step 5); amendments A-105 to A-107 (D-306 to D-308); T-08 to T-10 added after the Verify runs |
| Implement | done | T-01 to T-10 done (task commits in `plan.md` order, `handover-implement.md`); there is no `implementation-log.md` (accepted deviation F-11) |
| Verify | done | `goals/G-V2.MODEL/verification-report.md`: four runs by fresh reviewers; the fourth (commit `74525e4`) found no open finding above low; the owner accepted the open lows as deviations and re-approved TC-WFM-047, TR-MODEL-003 and TR-MODEL-001 on 2026-11-08 (D-309): **Verified with accepted deviations** |
| Commit | done | master (with G-V2.STORE) merged into `goal/v2.model` without conflicts (`735c983`); trace_check 547 = master's, goal, contract and PostgreSQL suites and JS tests green; merged into master by the owner as `971d388` on 2026-11-08; no version and no tag (subgoal of G-V2); requirement statuses Draft to Verified in this update |
| Deploy | empty | skill record, graph model, run order and the loader wiring inside the backend: nothing that users can reach on its own; delivered with the iteration goal G-V2 |
| Validate | open | |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|

## Answer to the STORE/parent session about the node types (2026-11-07)
Question: exact fields of the JSON field per node type of IF-301 v2 (draft `amendments/A-90-draft-IF-301-v2.md`, D-262, D-263). **Status: proposal of the MODEL session; my requirements (REQ-WFM-043 to 049) fix the rules, not the field names, so the owner confirms the names below.** `contracts/` and the draft are untouched.

| Type ID | Field (besides `type`) | JSON kind | Required | From |
|---|---|---|---|---|
| `data` | `value` | any JSON | optional | REQ-WFM-049 ("apart from its value") |
| `data` | `parameters` | object | optional (empty object if absent) | REQ-WFM-049 |
| `transform` | `toolbox_id` | string | required | REQ-GTB-007 |
| `master` | `stop` | object with `max_repetitions` (integer, at least 1) and/or `max_seconds` (number, above 0) | required; schema rule `minProperties: 1` holds "at least one" | REQ-WFM-048, REQ-GTB-008 |
| `master` | `task` | object, shape open | required in the draft, **open**: see point 1 | REQ-GTB-008 |

Type IDs are `data`, `transform`, `master`. No field of mine for edges. A rule a node schema cannot hold: none inside a node. The graph rules (two data nodes in a row, one writer per data node, no cycle, the order of the nodes) are checked by the Workflow management on the whole graph (D-262 point 1; REQ-WFM-043 to 048).

Answers to a), b), c):
- **a)** The graph description (ID, context graph ID, testbench ID, description; REQ-WFM-044) lives on the **graph**, not on a node. The draft's table puts "the four fields of the graph description" in the `data` row: that is a mistake of the placeholder, please correct it. The testbench ID may be empty.
- **b)** The Workflow management reads and checks **records** (`{id, data}` of a node, `{id, from, to, data}` of an edge). It builds no objects of its own. It calls `to_object` only where a class is needed, and it writes through the Storage layer, which calls `check_record`. Planned module `graph_model.py` works on records (plan T-01).
- **c)** Missing in the draft, for the owner to decide:
  1. **Master node, what runs it.** REQ-RUN-018 (owner, 2026-11-07) runs a master node like a transform. Then the node needs the same `toolbox_id` as a transform, and `task` (debate definition, FR-39, a later goal) may be optional and free-form. Proposal: `toolbox_id` required, `task` optional, `stop` required.
  2. **Graph record.** In the record form there is no record for the graph itself (ID, context graph ID, testbench ID, description). The `workflows` table is the document form (v1). Which table holds the graph header in the record form?
  3. **Membership.** A node record `{id, data}` and an edge record name no graph and no graph version. How does a read of "graph X, version n" find its nodes and edges? An operation, or a field `graph_id` and version, is missing.
  4. **Skill record** (REQ-WFM-040: ID, command, workflow graph ID, context graph ID, versioned). No requirement of the Graph tables or the Record tables names a table for it. Which table, and does STORE or MODEL provide it?
  5. **Error from the Storage layer** on a refused record: the draft says the rule and nothing is stored. The Workflow management needs the rule and detail passed on to the caller (REQ-WFM-043 to 048 name the node, edge or data node in the refusal).

Merge conflict in `architecture.sysml`: already resolved in `a220637` (master's version, then `gen_node_requirements_model.py` and `check_sysml.sh`, both OK).
