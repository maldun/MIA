# Hand-over for the next session (written 2026-11-03): Explore of the skill rework, HLS draft waits for the owner's review

Newest hand-over; it continues `handover-2026-11-02-validate.md` (G-V1 deployed, then closed without validation, D-185). Read `CLAUDE.md`, then this file, then the files under "Read in this order".

Next free ids: **D-186, A-89, FB-07, TD-27** (the interview answers have no D-number yet, see "Not done").

## Where things stand
- **G-V1:** done and closed as accepted without validation (D-185). v0.1.0 is deployed (image `8217ecd0ccf8`, rollback image `localhost/mia:pre-v0.1.0`). Open from it: TD-25 (smoke step in `stages.yaml`), TD-26 (Tailscale phone check), FB-01 to FB-06. The VAL-001 scope (`/lookup` only, 20 answers) and the VAL-003 check sheet are kept for the next goal's exit criterion.
- **Next goal: the skill rework**, Phase 1 Explore, **draft of the HLS update committed** (`1c29d94`), not approved. Skills used: `explore-phase`, `agent-app-explore` (load them, and `agent-app`, `dev-workflow`).
- Nothing under `skills/`, `library/`, `eval/` or the protected folders was changed.

## Read in this order
1. `specs/mia/explore-skill-rework/inputs/skill_rework.md` and the two drawings `graph_structure.drawio`, `Viewer_db.drawio` (the owner's intent; the copies at the top of `specs/mia/` may be duplicates, the `inputs/` ones are the current ones).
2. `specs/mia/explore-skill-rework/research.md` (what exists today, with references; section 4 lists where the note and the code differ; section 5 lists what was not looked at).
3. `specs/mia/explore-skill-rework/interview.md` (the 11 answers of the owner).
4. `specs/mia/high-level-spec.md`: section 2 "Candidate goals of iteration 2", FR-36 to FR-45 (section 3.1), the rows marked "iteration 2" in section 4, AC-31 to AC-38, risks and plausibility rows marked "Iteration 2", and **section 8a** (decisions and the conflicts with earlier text).
5. `specs/mia/architecture.sysml`: requirement defs FR-36 to FR-45, parts `skillsWindow`, `toolbox`, `debateRunner`, `skillConverter`, `graphRecords`, `ContextGraphBuilder` (`contextStore`, `proposer`, `confirmation`). Checks: `python3 -I tools/check_sysml_model.py .` OK, `bash tools/check_sysml.sh specs/mia/architecture.sysml` 0 errors.

## The owner's answers in one place (all in `interview.md`)
1. Increments, in order: foundation (data structure, node types, DB storage, today's skills migrated), skills window with viewer/editor, context graphs and their builder, benchmarks and debates.
2. Transforms are storable and exchangeable outside MIA; a review process for them comes later. 3. Until then an imported transform is stored but not runnable; a person marks it trusted.
4. A master node's finalization criterion is a function; predefined: deterministic check, judge or vote, person approves, budget end.
5. The context graph is knowledge the agent reads at run time (a knowledge graph is one kind). A tool builds it: its own node N-6 or part of N-5 (open). 6. Sources of the builder: runs and reviews, documents, web research, manual editing.
7. A testbench is an eval suite plus budgets; a workflow becomes tested or trusted only when it passes.
8. Debates run on MIA's own runner; no framework dependency. 9. Skills are converted one by one, old and new runner side by side until the converted one passes the same suite with the same pins.
10. Every debate carries its own definition, with variants per machine. 11. Only the owner edits; others read.

## What the owner wants to review (suggested checklist)
- [ ] The wording of FR-36 to FR-45 and whether AC-31 to AC-38 say what is meant (AC numbers such as the conversion margin are left to Plan).
- [ ] **Conflicts with earlier text** (section 8a, risk rows): owner-only editing against CON-6, FR-22 and FR-30; a context graph shared by several workflows against FR-30; the graph library and dragging (FB-02: vis-network) against FR-22 "vendored, no build step, text only". Decide in Plan whether the old text is amended or the new rule narrowed.
- [ ] **Agent's assumptions, marked as such, to confirm or strike:** items from untrusted text (documents, web) and items from runs start as *proposals* and steps read only confirmed ones; a debate variant naming an unpinned model does not run; the proposed numbers (3 rounds, 5 minutes, 12 calls per debate; 50 builder items per document; 20 % of a step's context from the context graph); the six example cases in the quality notion.
- [ ] **New dependencies** (need approval, CLAUDE.md): a graph drawing library, possibly `networkx` (FB-02), a JSON-schema validator. Not decided.
- [ ] A trusted transform runs in the MIA process, and the deployed stack has `sandbox_backend: none` (TD-24): is "one person marks it trusted" acceptable until the review process exists?
- [ ] Whether FR-40 (nodes and edges as separate records) really replaces the document-per-graph form of IF-301/IF-203, which have protected contract suites (amendments in Plan).

## Not done (Explore is not finished)
- **Open interview items:** N-6 or part of N-5 (can wait for decomposition in Plan); quality targets (`quality.md` has no line for the rework); maintained or frozen (the agent assumes maintained); the example cases need the owner's confirmation; data classes of context items (confidential or not).
- **Spikes proposed, none run** (agent-app-explore step 4, throwaway code in a `spikes/` folder, spike cases are not eval cases): (a) `verify.jury`/`verify.cops` as debates on the pins, 5 to 10 cases, 3 repeats, to see rounds, seconds and quality on the 16 GB card; (b) the builder on 10 documents chosen by the owner, who checks the proposals. Record them in `explore-skill-rework/spikes.md`. The 26B model and the full stack are not run on this machine for tests (fatal CPU machine checks at shutdown, memory note `crash-fatal-mce-cpu`); use the 12B model only.
- **Not looked at** (research.md section 5): `ui/REQUIREMENTS_CORE.md`, `workflow_library.py` internals, `library.py`, the skill list in the web UI (what the skills window replaces), `run_workflow.py`, the Storage layer's PostgreSQL schema, eval suites as the possible testbench.
- The interview decisions are **not yet in `review-log.md`**. On approval of the HLS write one D-186 with the 11 answers and the conflicts, set the HLS status, and add the amendment-style entry for the revised FR-7, FR-22 and FR-30.
- `feedback/`: no FB file was made for the rework (it is the owner's direction, not a finding). FB-02 is the nearest and is cited as `NOTE-2026-11-02` in `@ChangeSource` of the model; decide whether to make an FB-07 for the note.
- No `high-level-spec.md` approval, no `quality.md` update, no shortcuts-register entry for the interim trust rule yet.

## Next steps
1. The owner reviews (checklist above) and answers the open interview items.
2. Update the HLS and the model for what the owner changes; rerun the two model checks.
3. Plan and run the two spikes if the owner wants them before Plan; record in `spikes.md`.
4. Owner approves the HLS (status *Approved*, D-186), then `plan-phase` + `agent-app-plan` in a fresh context with the HLS as input (decomposition decides N-6).

## Practicalities
- Git: name the files in `git add`; never `git add -A` or `git add specs/mia` (the owner has untracked work files there, e.g. `.$Viewer_db.drawio.bkp`). `git push` is the owner's. Co-Authored-By line on commits.
- The HLS checker needs the formats in place: FR lines `- **FR-n Name** [baseline] (status). text` (use `[–]` when there is no baseline id), AC rows `| AC-n | text | FR-ids | method | status |`, and a `requirement def <'FR-n'>` with the same text in `architecture.sysml`, plus `requirement frN`, `satisfy` and `allocate` to a leaf part.
- Run the SysML parser after every change of a `.sysml` file: `bash tools/check_sysml.sh FILE` (about 15 s).
