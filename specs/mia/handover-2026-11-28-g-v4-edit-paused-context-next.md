# Handover: G-V4.EDIT paused after prototype round 05; G-V4.CONTEXT Plan next (2026-11-28)

For the session that starts the Plan of G-V4.CONTEXT. Read `CLAUDE.md`, this file (in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4/specs/mia/` since the merge) and the line handover `handover-2026-11-27-g-v4-line-transfer-deployed.md` (still valid for everything not named here). Ways of working: decisions as a questionnaire, recommended option first; full absolute paths for files; the owner signs and ticks, the agent never sets Approved; only the owner pushes (`git push -4`); the owner's delegation for G-V4 asks again at CONTEXT (D-423), so CONTEXT's decisions are asked, not taken.

## Why CONTEXT comes first now (D-606)
The owner asked during EDIT's prototype round 05 whether EDIT makes more sense after CONTEXT, since the context graph's stored form is defined. The code shows the mismatch:
- In the stored form, a context node's type is one of its graph's **categories**, each with a **JSON schema** the node must match (`graph_tables.py` `_context_node_refusal`, `_node_schema`; REQ-GTB-024). The Storage layer checks only the shape (a non-empty text type); the category check needs the caller to pass the categories.
- EDIT's editor profile (round 05 CP21, `graph_profiles_proto.py` on `prototype/g-v4`) describes **fixed node types per kind** with simple fields (text, json, number, choice from options or from the toolbox). CP21 proved generality only for kinds of that shape.
- So EDIT would have frozen a profile language and IF-104 v3's `kinds` answer that context may not fit. Decided: CONTEXT is planned before EDIT; the principle of one editor with a profile per kind (D-403, D-404) stays.

## State
| Line | Branch, worktree | State |
|---|---|---|
| EDIT | `goal/v4.edit` at `745c53d3`, `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-edit` (from `goal/v4` at `5dd1ca13`) | Plan paused. Step 0 drafted in `specs/mia/goals/G-V4.EDIT/goal.md` (scope per item, TD-91 to TD-94 in, OC-9 and OC-10 drafted, IF-104 v3 as A-210). Decisions D-600 to D-606 in `specs/mia/review-log.md`. THR-009 updated, `rt_edit` handed to G-V4.GRAPHAPI.CODE (D-603). Not merged into `goal/v4`, not pushed |
| Prototype | `prototype/g-v4` at `2f30febd`, `/home/maldun/prog/Python/MIA/.claude/worktrees/prototype-g-v4` | Round 05 (EDIT) ran CP21 to CP23, closed by D-606; CP24 (layouts) started and paused, CP25 (owner's validation sheet) not run. `goal/v4` merged in at `58473fb3`. Not pushed |
| CONTEXT | `specs/mia/goals/G-V4.CONTEXT/` (goal.md, top-level-spec.md) | TLS approved (D-390), scope note D-403 to D-405, order line D-606. No Plan artifacts yet |

## What round 05 found that CONTEXT needs
Report: `/home/maldun/prog/Python/MIA/.claude/worktrees/prototype-g-v4/specs/mia/goals/G-V4/prototype/rounds/05/prototype-report.md`.
- **CP21:** `GET /api/v2/kinds` (prototype) answers per kind of the registry (`graph_rule_set.kinds()`) its rules, `runs`, `editable` (with a reason when false) and its profile. Context is answered `editable: false`, "Editing context graphs comes with G-V4.CONTEXT." (D-602). The page's editor (`graph_app_v2/edit-model.js`, `edit-panel.js`) names no kind. Finding 4 lists where VIEW's product page and backend still name the workflow kind (`graph_app/step-marks.js`, `graph_app/panel.js`, `graph_api_v2.py` `steps`).
- **CP22:** without a guard, a context graph can be changed through the write routes (VIEW's product backend too, IF-104 v2 routes 9 and 10; finding 6). A stored graph of an unknown kind crashes the read path with `KeyError` (product `graph_model.read_graph`; finding 7). The prototype refuses with `422 not_editable` and `422 unknown_kind`, read from the same kinds answer, so CONTEXT lifts the guard by adding its profile.
- **CP23:** a workflow step was accepted into a context graph, because the context rules do not look at step types (finding 10). The prototype's `copy-step` refuses `422 kinds_differ` naming both kinds. Finding 11: the profile's field checks live only in the page; nothing on the backend checks a node against its type's fields.
- **Finding 13:** the mismatch above, and the two proposed layouts for EDIT's editing panel (A in place, B side panel), for EDIT's Plan when it resumes.

## Open for CONTEXT's Plan step 0 (ask the owner)
1. **Who builds the editor core** (working copy, undo, keep, restore, conflicts, form from a profile): D-403 gave it to EDIT. Options: CONTEXT specifies only the context profile, rule set and run view, and EDIT builds the core for both kinds later; or CONTEXT takes the core; or a joint step.
2. **How a node type and its fields are described** when types come from a graph's categories with a JSON schema: a per-graph list in the `kinds` answer, a separate categories route, forms built from JSON schema (which subset), and where the categories of a graph are stored and read (D-403 (2): a fixed list in the context profile for now, the builder's categories later, goal C, G-V4.BUILDER).
3. **Which workflow rules are structural for a context graph** (the CONTEXT TLS risk row; RULES' registry has identity, ends and duplicates for context today), plus the category and budget rules of FR-75.
4. **The run view FR-97** (a finished run's context graph, read-only): its source (the run's events) and its interface; RUN T-04 is running and owns the run record.
5. **Number block** for CONTEXT (the line's D-460 block is at D-553; EDIT holds D-600 to D-629, A-210 to A-224; RUN D-486 and A-191; VIEW D-505; BUILDER D-522). Propose one, as D-600 did.
6. **Prototype:** whether a prototype round for the context profile pays off (D-401 foresaw one per subgoal); round 05's code (`graph_profiles_proto.py`, the kind guard, `cp21` to `cp23` checks) is the starting point.
7. The parent's open item for CONTEXT: A-189 (RUN's joint amendment of IF-301) still needs CONTEXT's and VIEW's agreement (D-483; EDIT agreed, D-604).

## Host and other sessions
- RUN T-04 (session `goal-v4-c8`, worktree `goal-v4-run`) runs real model runs on the shared Ollama server, about three hours from 2026-11-27 late; it sends a message when done. No model runs, no Ollama, don't touch `goal-v4-run`. Planning and non-model tests are fine. Check `ListAgents` before anything that would load a model.
- The live stack `mia`, `mia_db_1` and `ollama` were stopped at the line handover; `mia-searxng` runs.

## Waiting for the owner
- [ ] Push `goal/v4.edit` (`git push -4 -u origin goal/v4.edit` in its worktree) and `prototype/g-v4` (`git push -4` in its worktree).
- [x] `goal/v4.edit` (records only) merged into `goal/v4` at `ff4b3b70` on the owner's request (2026-11-28); push `goal/v4` with `git push -4`.
- [ ] The two fingerprint boxes of round 05's `run.md` (optional, the round is closed).

## Next free numbers
EDIT D-607, A-210 (A-210 is reserved for IF-104 v3); round 05's prototype IDs: CP26, ASM-13. Line and other subgoals as in the line handover.

## Start prompt for CONTEXT Plan
> Start Plan of G-V4.CONTEXT. Create the worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-context` on a new branch `goal/v4.context` from `goal/v4` (it holds the EDIT records up to D-606, the reason CONTEXT now goes before EDIT; merged at `ff4b3b70`). Read `CLAUDE.md`, `specs/mia/goals/G-V4.CONTEXT/goal.md` and `top-level-spec.md`, `specs/mia/goals/G-V4.EDIT/generality-review.md`, the decisions D-403 to D-405, D-602 and D-606 in `specs/mia/review-log.md`, and `specs/mia/handover-2026-11-28-g-v4-edit-paused-context-next.md`. Read the round 05 report `/home/maldun/prog/Python/MIA/.claude/worktrees/prototype-g-v4/specs/mia/goals/G-V4/prototype/rounds/05/prototype-report.md` (findings 4, 6, 7, 10, 11, 13) and the context parts of `graph_tables.py` (`_context_node_refusal`, `_node_schema`) and `graph_rule_set.py` (`KINDS`). Load dev-workflow, plan-phase, agent-app, agent-app-plan.
>
> Begin with step 0: ask the owner the open points of the handover's section "Open for CONTEXT's Plan step 0" as one questionnaire, recommended option first, then apply each answer (decision rows, goal record). Don't write requirements before the editor-core and profile-language questions are decided.
>
> RUN T-04 may still be running real model runs: no model runs and no Ollama use, and don't touch `goal-v4-run` or `goal-v4-edit`. Do not push; hand the owner `git push -4`.
