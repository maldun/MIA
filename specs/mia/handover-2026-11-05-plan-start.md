# Hand-over for the next session (written 2026-11-05): Explore of the skill rework is finished, start Plan

Newest hand-over; it continues `handover-2026-11-05-explore-skill-rework.md`. Read `CLAUDE.md`, then this file. Skills: `plan-phase`, `agent-app-plan`, `decomposition`, `agent-app`, `dev-workflow`. Phase: **Plan of iteration 2 (the skill rework)**. The HLS is **approved** (owner, 2026-11-05, **D-186**, after reading `explore-skill-rework/forms/hls-reading-guide.html`).

Next free ids: **D-187, A-90, FB-07, TD-27, SC-10** (A-89 is the draft note for FR-7, FR-22, FR-30; SC-09 is the interim trust rule).

## Where things stand
- Branch `worktree-explore-ctx-graph`, all commits docs, forms and spike scripts; nothing under `skills/`, `library/`, `eval/` or protected folders. **Merge into master first** (the owner's untracked files in the main checkout stay untouched; never `git add -A`): `git merge --ff-only worktree-explore-ctx-graph`. Untracked and not mine: `explore-skill-rework/forms/example-cases-answers.json`.
- `interview.md` holds 22 rows. Checks after the last model change: `python3 -I tools/check_sysml_model.py .` OK (40 acceptance criteria). The trace check shows warnings that are not from this work (TD-26, no test requirements yet).

## Decisions that shape Plan (details in `interview.md`)
- Context graphs by ID, shareable, version pinning for trusted skills (12); every item has a data class (16). Fan-in: a data node has at most one writing transform; a debate's inner graph is embedded in the master node's JSON.
- **N-6 context-graph builder is a standalone node and container** (18). **Engine (row 21, spike C): LightRAG is not used.** On the owner's marks LightRAG had 85.6 % right but **7.7 % invented** (bar: 68 % right, at most 5 % invented). The own builder (option 1: sentence-border chunks, JSON-schema model step, a quote per item, every name checked against the whole document) had 93.1 % right and 0 % invented on 72 marked items. Candidate requirement text for FR-42 in Plan: "A proposal is refused when a name it uses does not occur in the source document; every relation carries the sentence that states it." Option 1 needs a **larger marked sample** in Plan; refused 45 of 761 proposals, 36 of them relation quotes without both ends (over-strict on pronouns).
- A model's reading as judge is **not** usable: the agent's blind labels against the owner's marks gave kappa 0.11 (target 0.6). A judge, if wanted, must be calibrated on `spikes/lightrag/owner-marks-*.json` first.
- **Spike (a), debates on the 12B** (`spikes.md`, `spikes/debate/`): the jury as a debate fixed the near-miss numbers (29 of 30 right, 0 false passes, mean 4.6 calls, 7.3 s); the cops debate did not improve on the one-shot form (23 of 30). Caps 3 rounds / 12 calls / 5 minutes never fired (at most 9 calls, 23 s). 10 own claims only, no ranking. **Requirement for Plan:** a debate step needs a retry or fallback for a malformed (cut-off) JSON reply.
- Numbers are configuration values with defaults (19): debate 3 rounds / 12 calls / 5 min; builder 50 items and 5 min per document; 20 % of a step's context, capped at about 1 500 tokens.
- FR-46 skill subwindow and spoken-only chat; FR-47 snapshots; graph viewer with vis-network (the owner's choice, **Plan pins version and licence**).
- Example cases confirmed (20); the review-report case (3 rows) accepted (22). Quality targets: `quality.md` Q-5 (22).

## Conflicts for Plan, with the accepted resolutions (row 22, A-89, SC-09)
1. Owner-only trust marking against CON-6 and FR-22: everyone edits data nodes and graphs, only the owner marks a transform trusted; an exception to CON-6, an amendment of FR-22.
2. FR-40 (separate node and edge records) against IF-301 and IF-203 and their protected contract suites: a plan amendment, the document form stays readable during the transition.
3. Imported transforms are stored untrusted and not runnable by default; interim rule while `sandbox_backend: none` (TD-24) in `shortcuts-register.md` SC-09.

## Left open for Plan (D-186)
- Numbers in AC-31 to AC-40 (for example the conversion margin).
- Dependencies, need approval: vis-network (chosen), a JSON-schema validator and `networkx` (undecided). No dependency is added without it.
- Open licences of public benchmarks (`explore-skill-rework/public-benchmarks.md`): SciERC has none stated; SciFact is CC BY-NC 2.0; Re-DocRED data terms rest on DocRED's MIT; BIPIA has CC BY-SA parts and data that may not be redistributed. Adopting any set needs a plan decision, fixed splits and a contamination note; the agent sets no truth labels.
- Unchanged from before: HLS goals A to D are candidates and are scoped again in Plan (M33); `decomposition` places N-6; amendment-style entries for FR-7, FR-22, FR-30 go into `requirements.md` and `baseline-requirements.md` from the note A-89.
- Not done in Explore: the FB item for the rework (it is the owner's direction); the validation of v0.1.0 (carried forward by D-185); Tailscale phone check (TD-26).

## Practicalities
- Host: model server on port 11434 (12B, 26B, two coder models, llama3.2; no embedding model). The 26B and the full stack are not run on this machine for tests; keep runs short (crash history in the memory note). Use the 12B.
- Spike code: `spikes/lightrag/` (`score_marks.py`, `option1.py`, `make_marking_option1.py`, `run_all.sh [OUTDIR]`, `option1-run/` raw output), `spikes/debate/` (`debate_spike.py`, `run1.jsonl`). Throwaway, not part of the product; spike cases are not eval cases.
- In a worktree session keep Bash commands plain (no `cd` to computed paths); write scripts to files and run them.
- Git: name the files in `git add`; `git push` is the owner's; Co-Authored-By line on commits. Misreading note: "HLS approval" was once recorded as an approval by mistake and reverted; approval needs the owner's explicit "I approve".
