# A-111: IF-203 v1, the part `transforms` (proposal, owner G-V2.TOOLBOX)

Status: **proposed** (Draft, 2026-11-11), waiting for the owner's approval; the install script is `tools/apply_amendment_a111.sh` (tried on a scratch copy, idempotent, IF-203 v0 -> v1). The mock, the suite and the real library (T-06) exist and agree with this text; storage: the code in the table `transforms` (IF-302 v9, A-112), trust and lifecycle in `transform_meta` (IF-302 v8, A-110). Text for the owner to read before the contract suite is installed (D-188). It fills in the `transforms` part of A-90 ("new kinds `skills`, `transforms`, `snapshots`"); the snapshot part is A-121 (G-V2.CONVERT), the kind `skills` is MODEL's. `contracts/` is not changed by this note. The mock and the suite that fix it are staged in `specs/mia/goals/G-V2.TOOLBOX/red-tests/` (`helpers/mocks/if_203_transforms.py`, `acceptance/contract/test_if_203_v1_transforms.py`).

## Operations (addition to the table of IF-203)
| Name | Input | Output | Notes |
|---|---|---|---|
| `list_ids("transforms")`, `read("transforms", id, version=None)`, `save("transforms", id, doc, author, expected_version=None)`, `history("transforms", id)` | as for the other kinds | as for the other kinds | `doc` is {id, version, inputs, outputs, code}; every save is a new immutable version of the record; `read` also gives `trust` and `lifecycle` |
| first `save` of an id | | | creates the meta record (IF-302 table `transform_meta`, A-110) with trust `untrusted` and lifecycle `draft`; a later save leaves the meta record as it is (REQ-WFM-092) |
| `get_meta(id)` | | `{"trust","lifecycle", and the optional "reason","evidence","baseline_allowed","shipped","changed_by"}` | |
| `get_trust(id)`, `get_lifecycle(id)` | | the value | read side of the two setters (also assumed by A-121) |
| `set_trust(id, trust, author)` | `untrusted`, `trusted` | `{"trust"}` | the rule who may set it (owner only for trusted, REQ-WFM-054) belongs to the Workflow management, not to the library |
| `set_lifecycle(id, lifecycle, author, evidence=None)` | `draft`, `tested`, `retired` | `{"lifecycle"}` | `evidence` is stored when given; the rule that `tested` needs it is the Workflow management's (REQ-WFM-067) |
| `set_meta(id, author, **fields)` | trust, lifecycle, reason, evidence, baseline_allowed (boolean), shipped (boolean), changed_by | the meta record | one new version of the meta record; `changed_by` is set to the author |

## Errors (addition)
| Condition | Signal | Afterwards |
|---|---|---|
| a value outside the lists, or an optional field of the wrong type or an unknown field | `ServiceError("invalid", rule="schema", detail=<field>)` | the meta record is unchanged |
| unknown id, version or kind | `not_found` | nothing changed |
| stale `expected_version` | `conflict` with `detail.current` | nothing changed |

## Golden examples
1. A new transform is untrusted and draft; a second save is version 2 (TC-IF-203-05).
2. Trusted and tested (evidence `run-1`) survive version 2; version 1 still reads its own document (TC-IF-203-06).
3. `fine` is refused for both statuses with the field as detail, the statuses stay (TC-IF-203-07).
4. Optional fields are kept; a boolean field with a text is refused (TC-IF-203-08); unknown ids and stale versions (TC-IF-203-09).

## Version history (addition)
| Version | Date | Change | Amendment |
|---|---|---|---|
| v1 | proposed | the kind `transforms` and its meta record | A-90, A-111 |

## Open points for the owner
1. The names `get_meta` and `set_meta` (the tests of the toolbox only use the library through them, plus `set_trust` and `set_lifecycle`).
2. Whether the check number range TC-IF-203-05..09 collides with CONVERT's or MODEL's suites (check at install time).
3. The real provider is built in T-06; until then the real variants of the suite are red by design.

## Status of the open points (2026-11-11, after T-06)
1. Names `get_meta` and `set_meta`: unchanged in the mock, the suite, the real library and the script; a rename now touches four places.
2. Numbers TC-IF-203-05..09: rechecked, no other branch (master, goal/v3, goal/v2.model, goal/v2.convert) uses a number above 04.
3. The real provider is built (T-06): the five real variants of the suite pass.
Still for the owner: approve the text, run `bash tools/apply_amendment_a111.sh` (look only), then `--do`, commit "contracts: A-111 installed". A-121 (CONVERT) and the kind `skills` (MODEL) edit the same file: whoever installs second gets an anchor error from the script and merges by hand.
