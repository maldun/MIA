# Prototype report: G-V4, round 05 (G-V4.EDIT, MVP)

Status: Prototype (reviewable draft, no product guarantees until parts are `real`) · Location: `specs/mia/goals/G-V4/prototype/rounds/05/` · Code: worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/prototype-g-v4`, branch `prototype/g-v4`
Scope: the outcomes of G-V4.EDIT not tried in round 02 (`run.md`) · Budget: 5 checkpoints of about an hour · State: CP21 done; CP22 to CP25 open

## Question
Can one editor, which knows no kind of graph, build its forms, checks and choices from a description of the graph's kind that the backend gives (FR-92, D-403, D-404, D-471 (2)), refuse to change graphs of kinds it cannot edit (FR-72, FR-73, D-602), copy a step only within its kind (FR-94), and fit into VIEW's frame in a layout the owner chooses (FB-1)?

## Hard requirements (top-level only)
FR-68 to FR-74, FR-91, FR-92, FR-94, NFR-18 of `specs/mia/goals/G-V4.EDIT/top-level-spec.md`; OC-5, OC-7, OC-9 of `specs/mia/goals/G-V4.EDIT/goal.md`.

## What was built
- **Merge of `goal/v4`** at `5dd1ca13` (RULES, VIEW and TRANSFER merged) into `prototype/g-v4` (`58473fb3`). Conflicts in `graph_model.py` and `record_tables.py` taken from `goal/v4`. The prototype's `graph_rules_proto.check` now calls the product's `graph_rule_set.rule_report`, so round 05 uses the real rule set. cp8, cp9, cp10 and cp19 pass on the merged code.
- **CP21: the profile from the backend.**
  - `graph_profiles_proto.py` holds the editor profile per kind. For each kind it lists whether it is editable (and the reason when it is not), its node types with their fields and start content, and its connection fields. The rules and "runs" come from the product registry, `graph_rule_set.kinds()`.
  - Workflow carries the three types and the fields that round 02 hard-coded. Context is answered as not editable: "Editing context graphs comes with G-V4.CONTEXT." (D-602). A kind of the registry without a profile is answered as not editable too, so a new kind never opens an editor that knows nothing about it.
  - New route `GET /api/v2/kinds` (any logged-in account). The existing `GET /api/v2/toolbox` serves the choice list.
  - `graph_app_v2/edit-model.js` and `edit-panel.js` no longer name a type, field or role. Start content, form, checks, the tool picker's filter, the "add a step" choices and the connection fields all come from the profile. A field is `text`, `json`, `number` or `choice` (fixed options, or the toolbox with a filter). Nested fields use a path (`stop.max_seconds`), and `need_one_of` covers "a loop-controlling step needs a limit".
  - `app.js` loads the kinds answer with the toolbox answer. It disables "Edit this graph" with the reason for a kind that cannot be edited, and fills the edit bar's choices from the profile.

## Findings
1. **The round 02 forms come out of the profile unchanged.** Same fields, labels, start contents and messages for the three workflow types. The only visible difference is the internal field name of the stop limits (`stop.max_repetitions` instead of `max_repetitions`), which `cp8.test.mjs` now uses.
2. **A kind the program has never seen works from its description alone** (`cp21.test.mjs`: a made-up kind `demo` with a required text, a whole number, a fixed choice and a connection field `relation`). No word of the workflow kind appears in its panel. This is the evidence for D-403's "a new kind is a new profile, not a new editor".
3. **The start content of every workflow type keeps the rules of the step itself** (`step_kind`, `stop_limit`), and each tool field's filter finds entries in the toolbox (74 processing tools, 3 controllers).
4. **Inventory: places that still name the workflow kind** (for Plan; nothing protected was changed):

| Place | What it assumes | For Plan |
|---|---|---|
| `graph_app/step-marks.js` (product, VIEW) `WORKFLOW` shapes and words, the trust marks for `transform`/`master` | the shapes, words and marks of workflow types | shape, words and marks per type from the kinds answer. Today a context graph is drawn with workflow shapes (TC-GA-025, A-175); EDIT can take it from the profile, or leave it to CONTEXT |
| `graph_app/panel.js` (product, VIEW) the left column's `toolbox_id` row and trust rows for `transform`/`master` | a node has a tool | "a type with a tool field" from the profile; also the place of TD-93 |
| `graph_api_v2.py` (product, VIEW) `steps` of route 4: trust only for `transform`/`master`, `code` from the role `code` | the workflow types and role | stays workflow-only by nature (trust is about tools), or reads "has a tool field" from the same registry; for Plan with REQ-API-027 |
| `graph_app_v2/step-marks.js`, `adapter.js`, the drawing in `app.js` (prototype page) | as the product page | not carried: the product page replaces the prototype page |
| `graph_proto_app.py` `steps_info` (prototype backend) | as `graph_api_v2.py` | not carried |

5. **One question for IF-104 v3:** in the prototype the kinds answer is open to any logged-in account, because a guest's viewer could use the words and shapes too (finding 4, row 1). The editor itself is the owner's. Plan decides whether `kinds` is a read route (session) or an owner route.

## Assumptions and choices the prototype made
| ID | Choice | Alternative | Why |
|---|---|---|---|
| ASM-9 | the profile lives in the backend, next to the registry of kinds; the page has no copy | a profile file shipped with the page | one place for kinds (D-404); a new kind needs no page release |
| ASM-10 | field names are paths into the node's data (`stop.max_seconds`) | a nested field type | keeps the form flat and the stored shape unchanged |
| ASM-11 | a kind of the registry without a profile is not editable | edit it with text fields only | an editor without a description could write content its rules never saw |

## Prototype tests (run once here; the carry-over decision decides what happens)
| Check | Command | Result |
|---|---|---|
| CP21 kinds answer, profile consistency, the JSON copy | `/home/maldun/prog/Python/venvs/mia312/bin/python proto_checks/cp21_check.py` | 15 pass, 2026-11-27, Fedora host |
| CP21 profile-driven editor, a made-up kind | `node --test proto_checks/cp21.test.mjs` | 4 pass, 2026-11-27 |
| round 02 and 04 regression after the merge | `cp8_check.py`, `cp9_check.py`, `cp10_check.py`, `cp11_check.py`, `cp19_check.py` | 24, 19, 20, 21, 14 pass |
| all prototype JS checks | `node --test "proto_checks/*.test.mjs"` | 64 pass |
