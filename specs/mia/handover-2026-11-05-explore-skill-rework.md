# Hand-over for the next session (written 2026-11-05): Explore of the skill rework, owner review done, spike C waits for the marking

Newest hand-over; it continues `handover-2026-11-03-explore-skill-rework.md`. Read `CLAUDE.md`, then this file. Skills: `explore-phase`, `agent-app-explore`, `agent-app`, `dev-workflow`. Phase: **still Explore**; the HLS is a draft, not approved.

Next free ids: **D-186, A-89, FB-07, TD-27** (unchanged; the interview answers have no D-number yet).

## Where things stand
- Branch `worktree-explore-ctx-graph` (commits from `11976df` to the last one of this session, all docs, forms and spike scripts; nothing under `skills/`, `library/`, `eval/` or protected folders). **Merge into master with** `git merge --ff-only worktree-explore-ctx-graph` in the main checkout (the owner's untracked files there stay untouched; never `git add -A`).
- The interview log `explore-skill-rework/interview.md` now holds **20 answers** (rows 12 to 20 are new in this session); the HLS (`high-level-spec.md`) and `architecture.sysml` follow them. Checks run after the last model change: `python3 -I tools/check_sysml_model.py .` OK (40 acceptance criteria), `bash tools/check_sysml.sh specs/mia/architecture.sysml` 0 errors.

## New decisions of this session (details in `interview.md` rows 12 to 20)
- **Context graphs are referenced by ID** (12): a skill names exactly one, skills may share one, the chat has one (skill record `chat`); a trusted skill pins the version, a draft follows the latest; a new version marks dependent testbenches stale; every item has a data class (16).
- **LightRAG** is a candidate engine, not decided (13): FR-41/FR-42 stay engine-neutral, our ID+JSON records are the master copy, builder output enters as proposals.
- **N-6 (context-graph builder) is a standalone node and container**, separate from N-5 (18).
- **FR-46 skill subwindow and spoken-only chat** (14, 15): the chat holds only spoken text; questions are spoken in the chat, answers are given in the chat, a confirmation of each answer is in the subwindow; layout: character box, chat left of it, skill window below it. AC-39.
- **FR-47 snapshots of the skill set**, skills are maintained (18). AC-40.
- **Graph viewer** (17): vis-network (the owner's choice, Plan pins version and licence), raw JSON editing validated by the server, proposals dashed, one viewer with two layouts, a debate opens in another view with the same layout, phone view-only, "used by", diff overlay, optional live highlight.
- **Fan-in:** a data node has at most one writing transform. **A debate's inner graph is embedded** in the master node's JSON.
- **Numbers are configuration values with defaults** (19): debate 3 rounds / 12 calls / 5 min; builder 50 items and 5 min per document; 20 % of a step's context, capped at about 1 500 tokens. Fine-tuning belongs to Validation.
- **Example cases** (20): 14 of 16 confirmed, 2 changed; the empty "review report" row is still open.

## Spike C (LightRAG on the 12B), record in `explore-skill-rework/spikes.md`
- Run done: 30 runs, 0 errors, 37 min; thinking off, hash-vector embeddings (retrieval side unknown). Pages of 12 000 characters: 70 to 130 s, 45 to 80 nodes, 23 to 67 edges.
- **Bar (owner):** at least 68 % of marked items right and at most 5 % invented (the agent's reading of the shares is in `spikes.md`, to confirm).
- **Waiting for the owner:** `explore-skill-rework/forms/spike-c-marking.html` (195 sampled items with source passages). The owner saves `spike-c-marks.json`; then compute the shares against the bar and report right / useless / wrong / invented per document and the missing-items notes.
- **Then:** run option 1 (own builder on MIA's runner, a model step with schema, proposals with quote) on the **same documents** (`spikes/lightrag/docs/`, kept in the repo) against the same bar; decide LightRAG go or no-go in the owner's presence. Stages 1 to 3 of the model plan (16K, 26B, other machine) only if stage 0 falls short and the owner agrees (`pseudo-code-review.md` section 4).
- Rebuild the setup: Python 3.12 venv (outside `requirements.txt`), `pip install lightrag-hku==1.5.7 ollama`, Ollama with `gemma4:12b-it-qat`. The scripts in `spikes/lightrag/` (`run_spike.py`, `run_all.sh`, `fetch_docs.py`, `make_marking.py`) still carry the old job paths of the venv, the documents and the output; change the paths at the top of `run_all.sh`. The first venv and the raw run output were in the job's temp folder and are gone with the job; the marking page keeps the sampled items and their passages.

## Open for the owner (Explore is not finished)
1. Marking of spike C, and confirmation of the reading of the bar.
2. The empty "review report" example case (what a good report on a small question looks like).
3. Spike (a): `verify.jury` / `verify.cops` as debates on the 12B (not run); the debate numbers stay guesses until then.
4. Open from the earlier hand-over: quality targets in `quality.md` for the rework; the conflicts for Plan (owner-only editing against CON-6 and FR-22; whether FR-40's separate records replace the document form of IF-301/IF-203 with their protected contract suites); the trust rule for transforms while `sandbox_backend: none` (TD-24).
5. On approval of the HLS: one D-186 with the 20 answers and the conflicts, HLS status *Approved*, amendment-style entry for FR-7, FR-22, FR-30, shortcuts-register entry for the interim trust rule, then `plan-phase` + `agent-app-plan` in a fresh context (decomposition places N-6).

## Findings of the review of the owner's sketch
`explore-skill-rework/pseudo-code-review.md` (sections 2 to 5): ten findings on `inputs/workflow_graph.py` (bugs, missing trust check, run record, type registry, debate loop and budgets, skill record), effects of shared context graphs, the LightRAG fit table, the staged model plan. The sketch and the owner's edit of `inputs/skill_rework.md` (LightRAG line) are uncommitted in the owner's checkout.

## Practicalities
- The model server runs on the host (port 11434; 12B, 26B and two coder models pulled; no embedding model). The owner says crashes stopped after the BIOS changes; still keep runs short and the 26B for stage 2 only.
- Commands in a worktree session: keep Bash commands plain (no `cd` to computed paths, no variables as program arguments); write scripts to files and run them.
- Git: name the files in `git add`; `git push` is the owner's; Co-Authored-By line on commits.
