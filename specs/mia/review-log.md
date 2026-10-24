# Review log of the HLS (step by step, started 2026-10-24)

Rule of the review: one HLS section per step; the owner confirms each step before the next starts. Decisions are recorded here with the owner's words condensed; each says which HLS sections it touches and whether the edit is done. Steps: 1 context, goal, scope; 2 constraints and environment; 3 requirements (FR, NFR); 4 agent profile; 5 architecture; 6 acceptance criteria; 7 risks and open questions.

## Step 1: context, goal, scope (answers of 2026-10-24)

| Id | Decision (owner) | Touches | Edit |
|---|---|---|---|
| D-1 | MIA becomes a **multi-user system with login** and a **database** that stores information between apps. Reverses the non-goal "multi-user operation" and lifts the postponement of `deploy/REQUIREMENTS_DB.md`. | 1, 2, NFR-6, NFR-8, CON, architecture (Persistence, access control), baseline OP-7 | scope edited in step 1; requirements in step 3 |
| D-2 | Development is **iterative**: MIA develops several skills and workflows. Success = one skill built (the literature review) **and a second skill added within 1 month**. | 1, 6 | goal edited in step 1; criterion drafted as AC-9, confirmed in step 6 |
| D-3 | Character and behaviour requirements (answer to question 3), listed below as CR-1..CR-8 | 3, 4, 5, 6 | recorded; applied in steps 3 to 6 |

### CR-1..CR-8 (owner, 2026-10-24; first called C-1..C-8, renamed because the baseline has constraints C-1..C-7), to be turned into requirements in step 3
- **CR-1 Mood in every situation.** The character reacts with a mood in every situation and shows the expression mapped to that mood.
- **CR-2 Voice.** The voice is made automatically by an open TTS (Kokoro for now), played in the browser; a post-processing step makes it sound anime-like.
- **CR-3 Character exchange.** A character is easy to select from a VRoid model (`.vrm`); original and compiled files are transferred with scripting tools.
- **CR-4 Editors.** Expressions and motions are adjusted in an expression editor and a motion editor; changes update automatically.
- **CR-5 Persona from `calibration.txt`.** A provided `calibration.txt` makes the persona behave roughly as specified: correct names and pronouns (for example "master") and back-story bits are repeated.
- **CR-6 Feedback system.** Plus/minus feedback measures overall feedback over time and allows adjustment on that metric. A small story tells what MIA receives (money, love points, ...). The mood changes with feedback and an overall score is reflected in the general mood. Categories: answer quality, reactions, character behaviour, service; points are added and subtracted per category.
- **CR-7 Tasks and memos.** MIA stores tasks and memos and recites them correctly.
- **CR-8 Learning from negative feedback.** Behaviour with negative feedback happens less often and, after at least 5 negative feedbacks, stops (or at most 1 % chance). On negative feedback MIA behaves shocked.

Fit with what exists: CR-1, CR-2 (partly), CR-3 (partly), CR-4 (built for expressions and gestures; "motion editor" = gesture editor), CR-5 (persona exists, not measured), CR-7 (hourly time check and `TASK:` convention only; ledger proposed in `REQUIREMENTS_CORE` MM1), CR-6 and CR-8 (new; CR-8 is the "consequences" ladder BF3 plus a hard rule). Tension to settle in step 3: CR-8 ("stops after 5 negatives") versus `BF4` (approval must not be the only reward, no sycophancy); and CR-6 "money, love points" is a character story, not a real payment.

### Open questions raised by D-1 (to be answered before step 3)
1. Memory, persona and feedback: **per user** or one shared MIA? (2026-10-21 decision was "one shared MIA with one memory".)
2. Roles: an owner/administrator who sees everything, and ordinary users?
3. Login: local accounts with passwords, an identity provider, or the tailnet identity?
4. "Between apps": which other applications use the database?

### Answers to the questions of step 1 (owner, 2026-10-24)
| Id | Decision | Touches | Edit |
|---|---|---|---|
| D-4 | **One shared MIA**: one memory, one persona, one feedback score for all users (keeps the decision of 2026-10-21). | 3 (FR-14, NFR-8), 5 (Persistence), DB plan | recorded; applied in step 3 |
| D-5 | **All users can see everything** (no per-user privacy inside MIA). Consequence to state in the data classes: anything one user tells MIA may be visible to every other user. | 3, 4 (data classes), NFR-5 | recorded; applied in steps 3 and 4 |
| D-6 | **Local accounts with passwords.** Needs: password hashing, session handling, login throttling, an account-creation path (no self-registration by default?), tokens replaced by accounts. | 3 (NFR-6), 4, 5 (access control) | recorded; applied in step 3 |
| D-7 | **Which apps share the database is undecided**; an agent may be added later. The database is therefore for MIA's own state first, behind storage interfaces; the "between apps" interface is deferred. | 3 (NFR-8), 7 | recorded; open question in step 7 |

### Proposed requirement from the question "are workflows and skills development covered?"
Covered today: FR-6 (a task is a skill file plus a pipeline), FR-7 (workflows as validated, versioned library data with a lifecycle; model-made entries stay drafts), FR-17 (suites and baselines), FR-18 (learning). **Not covered: the authoring path itself**, which D-2 makes the success measure ("a second skill within one month"). Proposed **FR-20 Skill development path** (decision D-8, for step 3): MIA shall provide one documented path to add a skill: a skill file and pipeline built from library nodes, validated before use; a suite with people-labelled cases and a holdout and a recorded baseline before the skill is trusted; the skill declares its model, tools, budgets and trust boundaries; a new skill stays a draft until the owner promotes it; and the time from idea to a promoted skill is recorded, so that the one-month criterion (AC-9) can be checked. Open for step 3: who may author skills in a multi-user system (all users, per D-5?).

### Corrections of 2026-10-24 (owner), after step 1
| Id | Decision | Touches | Edit |
|---|---|---|---|
| D-9 | **A graph app** visualises and edits the graph workflows and **uses the database**. This **reverses** the decision of 2026-10-22 that no viewer or editor is built (`REQUIREMENTS_CORE` section 10, G1/G2; baseline TK-10). It is also the first answer to "which apps share the database" (D-7). | 1 (scope), 3 (new FR), 5 (new part), baseline TK-10, CORE 10 | scope and baseline edited; requirement in step 3 |
| D-10 | **Trusted users only; everyone may edit**: skills, workflows, presets, persona; when something changes it changes for all. Assumption: a handful of trusted users. Consequence: FR-20 authoring is open to every user; no roles inside MIA; every change must be a new immutable version with author and time, so a change can be seen and undone (L3 of the library). A model's edit still stays a proposal (G3). | 2 (constraint), 3 (FR-7, FR-20, NFR-6) | constraint added in step 2; rest in step 3 |

### Step 2: constraints and environment (HLS 3.3, 3.4), edited 2026-10-24
- CON-2 extended: with several users one model server serves one request at a time, the others queue (open for step 3: queue length and fairness).
- CON-4 extended: passwords are sent only over HTTPS or on localhost.
- **CON-6 (new)** trusted users: a handful, all see and edit everything, a change applies to all (D-5, D-10).
- **CON-7 (new)** shared database reachable by MIA and the graph app, state behind storage interfaces; the engine is not decided here (the 2026-10-21 plan assumed PostgreSQL because SQLite on a shared volume is not safe across machines).
- 3.4 environment: a handful of users on phones and computers in the home network and the tailnet; the compose stack gains a database service and the graph app; backups include the database.
- Questions left for the owner: (a) is PostgreSQL acceptable as the engine (a container, `deploy/REQUIREMENTS_DB.md`)? (b) the graph app: a web page served by MIA in the same stack as the chat (plain HTML/JS, vendored library such as Cytoscape.js or D3, no build step), or a separate program? (c) are accounts created by the owner only, or may a user register?

### Answers of 2026-10-24 to the questions of step 2
| Id | Decision | Touches | Edit |
|---|---|---|---|
| D-11 | **PostgreSQL in a container** is the database. The graph app is **plain HTML/JavaScript** in the same stack as the chat, like the ArangoDB web graph view; each node is a JSON dictionary edited directly as text; text data only. | CON-7, NFR-8, FR-22, architecture, `deploy/REQUIREMENTS_DB.md` | applied in step 3a |
| D-12 | **Only the owner creates accounts.** Users may change their own password afterwards. | FR-21 | applied in step 3a |

### Step 3a: multi-user, database and graph app (edited 2026-10-24)
New: **FR-21 Accounts and login**, **FR-22 Graph app**. Rewritten: **FR-1** (several users, attribution, queue), **FR-5** (every user, changes apply to all, author recorded), **FR-7** (every edit a new immutable version with author and time), **NFR-5** (nothing private between users, stated at login), **NFR-6** (accounts instead of tokens), **NFR-7** (queue with position), **NFR-8** (PostgreSQL in a container; was "room to grow, postponed"), **CON-7**. Architecture: 13 subsystems (new `graphApp` with graphView, nodeEditor, versionStore, graphValidator), `webApp.accountService`, `persistence.database`. `deploy/REQUIREMENTS_DB.md` and baseline OP-7 no longer say postponed. **FR-20 (skill development path)** is reserved and comes with step 3b.

Assumption to confirm (A-1): `L1` of the library says files are the truth and SQLite only an index. With the graph app on the database, **entries edited in the graph app live in the database**; the shipped entries in `library/` are seeded into it and can be exported back to files for review in git. Without this decision the graph app and the files would drift apart.

### Decision on A-1 (owner, 2026-10-24)
| Id | Decision | Touches | Edit |
|---|---|---|---|
| D-13 | **Library entries live in the database; there is a file format to export them and to seed the database from files.** Shipped entries in `library/` are seeded; an export writes entries back to files for review in git. Replaces `L1` ("files are the truth") for the multi-user system. | FR-7, FR-22, NFR-8, CORE 4a L1/L2 | recorded; text applied in step 3b |

### Step 3b, chunk 1 (edited 2026-10-24): FR-20 and CR-1 to CR-5
| Request | Becomes | Status in the code base |
|---|---|---|
| D-8 skill path | **FR-20 Skill development path** (every user; suite, holdout, baseline, draft until promoted, time recorded); **AC-9** one-month criterion | tools exist (`tools/library.py promote`, `tools/eval.py`); the scaffold and the time record are new |
| CR-1 mood in every situation | **FR-23** (mood map, all situations, fallback neutral, settles over time) | partly: mood from emotion keyword and activity (`moods.py`, `emotion_map.json`) |
| CR-2 voice | **FR-3** rewritten (open TTS, replaceable, anime post-processing, plays in the browser) | built: Kokoro with `voice_effect` anime |
| CR-3 character exchange | **FR-24** (`.vrm` selection, transfer of original and compiled files, mapping of expressions) | partly: scripts for the Blender route; direct `.vrm` and the mapping to another model are new; **doubtful** (shape keys differ per model) |
| CR-4 editors | **FR-5** rewritten (expression editor and motion editor, live update on all devices) | built (the motion editor is the gesture editor) |
| CR-5 persona from `calibration.txt` | **FR-25** (names, pronouns, back story; measured by a persona suite) | partly: file is sent at every start, behaviour unmeasured |

Open for the owner (CR-5 with several users): the persona says "master". Does MIA call **every** user "master" (one shared persona, D-4), or the account name, or both ("master" plus the name)?

### Confirmations and additions of 2026-10-24 (owner)
| Id | Decision | Touches | Edit |
|---|---|---|---|
| D-14 | Chunk 1 of step 3b confirmed. **MIA calls every user "master"** (one shared persona, the same form of address for all). | FR-25 | applied |
| D-15 | **New requirement FR-26**: every workflow has a specification of inputs and outputs and measurable criteria, with a benchmark (test set, development and held-out parts, baseline), so that it can be verified and optimised. Was **not** covered before: FR-7 (validated versioned data), FR-17 (a harness exists), FR-20 (a path with a suite) and NFR-2 (structured outputs) touch it, but none demands a written specification per workflow with criteria. | FR-26 (new), FR-20 (points to it), AC-10 | applied |

### Step 3b, chunk 2 (drafted 2026-10-24): CR-6, CR-7, CR-8
| Id | Decision | Edit |
|---|---|---|
| D-16 | FR-26 and AC-10 confirmed. **FR-25: "master" for every user by default, unless `calibration.txt` specifies otherwise.** Chunk 2 drafted from the owner's description. | applied |

New: **FR-27 Feedback and points** (CR-6), **FR-28 Tasks and memos** (CR-7), **FR-29 Adaptation to negative feedback** (CR-8); FR-23 (mood) now also takes the overall score; **AC-11** (after 5 net negatives at most 1 percent in 1000 opportunities), **AC-12** (50 tasks and memos recited word for word).

Design choices I made while drafting; each is the owner's to overrule:
1. **Points:** a plus adds and a minus subtracts a number of points in the category voted for; the value per vote and the weight per category are settings; the overall score is the weighted sum of the four categories. The "story" (money, love points) is data: a text per category, fictional.
2. **Whose votes:** all users' votes count equally (shared MIA, trusted users), each attributed.
3. **Mood:** the overall score shifts the general mood through a moving window (length set in Plan), so one vote does not stick forever.
4. **"Adjust on that metric":** read as: compare workflow and behaviour versions over time by their feedback score (FR-26 benchmark remains the decision basis); feedback never changes a fact (conflict with BF4 resolved by scope).
5. **Attribution:** a minus must name the behaviour it is about; if a message contains several (gesture, expression, phrase), the vote asks which one. Every reaction therefore carries behaviour ids.
6. **Stopping:** "at least 5 times it should stop (or 1 % or less)" is written as: after at least 5 net negative votes the chance is at most 1 % per opportunity; positive votes can restore it; the exact curve is fixed in Plan. Net = negatives minus positives.
7. **Scope of FR-29:** style and reactions only (gestures, expressions, recurring phrases, kinds of reaction), never facts, safety checks or the persona's names.
8. **Tasks and memos:** read back from the records by code, never regenerated; stored in the shared database; all users see and may change them.

### Step 3c: old requirements checked against the new decisions (edited 2026-10-24)
| Change | Why |
|---|---|
| FR-4, FR-6, FR-8, FR-12, FR-14, FR-15, FR-11: "the owner" became "every user" / "a user" / "the requesting user" | CON-6: every user sees and edits everything; FR-8: any user may switch the model, the switch applies to all and asks for confirmation |
| FR-15 points to FR-29 for the adaptation to votes; FR-18 learns from signals "including the votes of FR-27"; FR-16: every run is attributed to the user who started it | multi-user and the feedback system |
| FR-19: the owner creates the first account at installation; the database is part of backup and restore | D-6, D-11, D-12 |
| NFR-7: **a chat answer has priority over a background task**; a long task such as a review slice yields the model server to waiting chat messages | one model server shared by several users (CON-2) |
| HLS: a "Users and stakeholders" table was added to section 1 (it was missing since the first draft) | the stakeholders of the first draft were lost when the draft was replaced |
| SysML context: `Guest` ("no login") replaced by `User`; `Owner` is a `User` | accounts for all |
| Tooling: all requirement docs in `architecture.sysml` are now **generated from the HLS sentences**, and `tools/check_sysml_model.py` fails when they differ. First run of the check found two docs where `textwrap` had split words at hyphens; fixed | one source of truth |

Not changed in step 3 (they belong to later steps): the agent profile (4: tasks, autonomy, data classes with attributed votes and shared visibility, example cases), architecture decisions table (5), acceptance criteria (6), risks (7).

### Step 4 (agent profile), edited 2026-10-24
| Id | Decision | Edit |
|---|---|---|
| D-17 | **New FR-30 Workflow context graph**: every workflow is accompanied by a context graph that users can adapt. *My reading, to confirm:* a graph of the concepts, entities, source types and relations the workflow works with, and the views that say what each step sees within its token budget; stored in the database, editable in the graph app, each run builds its run graph from it. The per-run graph of `context_graph.py` exists; a stored graph per workflow is new. FR-26 now lists it as part of the workflow's specification. | FR-30, FR-26, SysML |
| D-18 | **Quality notion for chat in character** (owner): *this is MIA* = (i) behaves as `calibration.txt` notes, measured statistically with check dialogues; (ii) reactions fit the personality, tested statistically against check dialogues; (iii) an overall positive feedback score after a fixed interval (1 week as baseline). *Not MIA* = the inversions. AC-8 rewritten as three parts; the "missing" rows of the quality notion replaced. | quality notion, AC-8 |
| D-19 | **Data classes**: all votes, scores, tasks, memos and context graphs are *shared inside MIA, private from outside*; account data and password hashes are secret and never logged. | data classes |
| D-20 | **"Yes, ask" on the autonomy of feedback adaptation** (my reading): MIA reduces a behaviour gradually and tells users with a note they can undo, and **asks before a behaviour is nearly stopped** (the 5th net negative). To confirm. | autonomy table |
| – | Added to the autonomy table: tasks and memos, workflow edits (a user edit is a new validated version that applies to all), account creation (owner only), vote adaptation. New trust boundary **TB-edit** (users edit workflows and prompts for everyone); it is named in the agent view in step 5. | agent profile |

### Confirmations and changes of 2026-10-24 (owner), then step 5 (architecture)
| Id | Decision | Edit |
|---|---|---|
| D-21 | **One context graph per workflow and one for the chat as a whole**, stored and adaptable; the **per-run graph is dropped as a general mechanism** and kept only for tasks that need working memory (for example extending a keyword search). FR-30 rewritten. The event log (FR-16) stays the source of truth for what happened; the replay and explain tools stay as tools. Note for `REQUIREMENTS_CORE` 13c: CG6 and CG11 (the graph of a run is a view of the log) are narrowed accordingly. | FR-30, decisions table, allocation (no more observability.contextGraph for FR-30) |
| D-22 | **`calibration.txt` is one shared configuration file for all users** and the baseline of the persona (not private). | FR-25, data classes, shortcuts |
| D-23 | The interval of the feedback criterion is **one week at first and a setting**. | FR-27, AC-8 |
| – | D-20 confirmed: MIA asks only before a behaviour is nearly stopped (the fifth net negative). Steps 3c and 4 are confirmed. | – |

Step 5: overview rewritten (13 subsystems, PostgreSQL, accounts, graph app); the key-decisions table now lists database, one shared MIA, accounts, context graphs, chat priority, votes on style only, and the graph app (the earlier rows "Postgres postponed" and "viewer dropped" are replaced); the agent view has the edit boundary TB-edit (`WorkflowEdit` item, `GraphEditor`, `WorkflowValidator`, a flow between them).

Open for step 5: **where do the benchmark data live?** FR-26 says a workflow's specification and benchmark are stored with it in the library (the database). The agent-app workflow protects `eval/suites/` and `eval/baselines/` as **files in git** (protected, reviewed, holdout hygiene). Recommendation: suites, cases and baselines stay files in `eval/` (versioned in git, protected); the workflow entry in the database references them by suite id and version, and the **results** (runs, scores, votes) are stored in the database. To confirm.

### Confirmation and a gap found by the owner (2026-10-24)
| Id | Decision | Edit |
|---|---|---|
| D-24 | **Benchmark data**: cases, suites and baselines stay as files in `eval/` (protected, in git); the workflow entry in the database references them by suite id and version; run results are stored in the database. Step 5 confirmed. | FR-26 |
| D-25 | **Voice lines were missing from the HLS** (the owner asked). Baseline `VO-3` (clips per expression in `expressions.json`, intro sounds, attention sounds with a chance of 0.3) was only in a bracket of FR-3, never stated. New **FR-31 Voice lines**: greeting, a line per mood or expression, an attention call before MIA speaks on her own, a shocked line on a negative vote; data, editable by every user, chosen at random among several, silent when missing. **AC-13**. New part `voice.voiceLines`. Risk noted: some clips (`Navi_*.wav`) look like game samples and are outside git. | FR-31, FR-3, FR-23, autonomy, risks, AC-13 |

### Sweep of the baseline against the HLS (2026-10-24)
Method (`tools/sweep_baseline.py`, reproducible): for each of the 90 baseline rows, the distinctive words of the row (backticked terms and words of 6 or more letters) are counted in the HLS text **without** its id brackets; rows with low coverage and rows that no bracket cites are read by hand. Result: 80 of 90 rows are cited in a bracket; 10 are not.

| Row | Finding | Action |
|---|---|---|
| VO-3 | found earlier by the owner (voice lines) | FR-31 |
| TK-7, TK-8, CH-11, CT-12 | storytelling, character variants, chat extras: proposed, never decided | listed under "Not decided yet" in the scope; the owner chooses the **second skill** |
| CT-13 | non-goal list was incomplete and said accounts are out of scope | HLS non-goals completed; baseline row corrected |
| G-1, G-2, C-4, C-6, C-7 | covered by section 1, CON-1, CON-3 and the scope, not by a bracket | no change |
| CT-1, CT-8, CT-6 | layout, chat log separate from memory and deletable, connection state and drafts were cited but not stated | added to FR-2 and FR-1 |
| VE-4, RS-3, RS-8, RS-12, EV-2 | verification styles behind hard checks, top-down levels, stop by a check in code, cross-field aliases, judge calibration were cited but not stated | added to FR-9, FR-11, FR-17 |
| CH-6, CT-3, CT-4, CT-5, CT-7, others between 0.45 and 0.65 | detail that belongs to the detailed documents (`ui/REQUIREMENTS_CHAT.md` and others) | no change |

| Id | Decision | Edit |
|---|---|---|
| D-26 | If the game samples (`Navi_*.wav`) do not exist, **create the default lines with the TTS** ("Hello!", "Hey!", "Listen!" as the file names suggest, plus one per mood); this mitigates the licensing risk. | FR-31, risk table |

### Decisions of 2026-10-24 after the sweep, and step 6 (acceptance criteria)
| Id | Decision | Edit |
|---|---|---|
| D-27 | **Storytelling is just another skill**, noted as a future skill. **The second skill is the lookup** (the one that exists today), added through the path of FR-20 within one month of the literature review. **A character variant per workflow**; a workflow without one uses the chat's. New **FR-32**. The sweep is confirmed. | scope (future features), AC-9, FR-32 |
| D-28 | **Chat extras**: only **regenerate** and **speak again** are built in the first version (FR-1); export, search within the conversation, accent presets and German texts are noted as future features. **`/search` calls SearXNG and lists the findings** (FR-10), as today. | FR-1, FR-10, scope |
| – | **Step 6**: section 6 rebuilt as one table of 26 criteria (AC-1 to AC-26), each with the requirements it covers, the way it is checked and a state (*confirmed* for the owner's own criteria, *proposed* for the others). New criteria: AC-14 accounts, AC-15 database and shared changes, AC-16 graph app, AC-17 character and variants, AC-18 feedback, AC-19 performance with chat priority, AC-20 constraints, AC-21 transparency, AC-22 small-model strategies and learning, AC-23 model management and search, AC-24 memory (later), AC-25 behaviour rules, AC-26 method transfer (optional). The checker now fails when a requirement is covered by no criterion. | HLS section 6, checker |

### Step 6 follow-up (2026-10-24): AC-19 confirmed; what AC-2, AC-24 and AC-26 depend on
AC-19 (chat stays responsive while a review runs; chat priority) is confirmed (D-29). The three criteria that cannot be met by a first release, and why:

| Criterion | Requirement | Missing dependencies (all verified today) |
|---|---|---|
| **AC-2** verification gate beats the single voice on the holdout | FR-9 (the code is built) | (1) **no suite has a holdout split** (`agent_check` rule A6 warns for all 10 suites); (2) the near-miss part has **3 distinct claims**, the decision needs 30+ (`eval/baselines/verdicts-styles.md`); (3) labels were set **by one person**, a second labeller is needed for the holdout; (4) **model digests unknown** (Ollama was not running), so no pin; (5) all baselines are for the **light model** only; (6) the gate itself is not chosen yet (number check plus cops is the candidate of the worked example in the skill). |
| **AC-24** memory beats today's dreaming | FR-14 (only the early summary design exists) | (1) **no memory test set** exists and today's dreaming has **no measured baseline**; (2) structured memory records with provenance need the **database (NFR-8, not built)** and the storage layer; (3) retrieval at answer time needs embeddings on the CPU (not built); (4) consolidation at rest, the verified-write rule, the digest and a memory page for users (all proposed, `REQUIREMENTS_CORE` MM1 to MM7). |
| **AC-26** method transfer finds the known method in its top 3 | FR-13 (optional, off by default) | (1) needs the **review pipeline** (FR-11: phases 2d to 6 not built: full text, baseline, screening, roles); (2) the **field graph** and the **template catalogue** (RV49 to RV52) do not exist; (3) the problem-signature step and the transfer scout (RV43, RV54) are not built; (4) the **retro-discovery cases** (RV47) exist only as two cases from the owner's own papers (z-transform, Gröbner bases; the models may have seen them) plus squaring the square; (5) the executable tests need the sandbox (built). |

Proposed state for the first release: AC-2 is *in scope but blocked* (the work list is the holdout, the near-miss claims, a second labeller and the pins; all are Plan tasks); AC-24 and AC-26 are *later* (not in the first version). To be confirmed by the owner.

### Holdout and near-miss claims from open data (built 2026-10-24)
The owner works alone, so there is no second labeller (D-30). The labels of two open sources serve as the independent labels; the owner audits a sample.
- `tools/make_external_suite.py`: **VitaminC** (CC BY-SA 3.0; claim, evidence, SUPPORTS / REFUTES / NOT ENOUGH INFO; contrastive groups kept together) and **Wikidata** (CC0; true value and a seeded false twin: factor, swapped digits, unit off by 10, year off; at least 5 percent apart). Seeded sampling; **split by a hash of the pair id** (about a third to holdout), so nobody has to read the holdout; writes `data/eval-external/` (git-ignored): suites `verdicts_vitaminc[.holdout]`, `verdicts_wikidata[.holdout]`, a blind `audit/sample_sheet.csv` (opaque ids, about 20 % of the pairs), `audit/key.json`, `manifest.json` with counts and a hash of the id lists. Tags `number`, `pair:`, `family:`, `source:`, `labelsrc:`, `label:people`, `split:`, `req:AC-2`.
- `tools/label_agreement.py`: your labels against the key: agreement, Cohen's kappa, confusion table, the differing ids (`ambiguous.txt`).
- `tests/test_external_suite.py`: 10 offline tests (split, twins, cleaning, pairs stay together, the sheet does not reveal the truth, kappa, agreement tool). **A real flaw found by them:** the Wikidata case ids end in `-true`/`-false` and would have leaked the answer on the blind sheet; the sheet now uses opaque ids.
- Tried against the live sources: 30 VitaminC groups gave 114 cases, 40 Wikidata pairs gave 74 cases, the audit sheet 36 rows; dev cases read and found sensible.
- **Open points for the owner:** (1) the VitaminC cases should stay out of git (the licence may not be compatible with GPL-3.0); (2) copy or link the generated suites into `eval/suites/` yourself (protected folder); (3) label the audit sheet, run the agreement tool, tag the differing cases `ambiguous`; (4) record the single-labeller limitation in `eval-spec.md` in Plan; (5) both sources are in the training data of the models (Wikipedia, Wikidata), so memory can inflate results on the no-evidence pairs.

### Reproducible reruns (owner, 2026-10-24)
| Id | Decision | Edit |
|---|---|---|
| D-31 | **AC-2 gains a reproducibility part (b):** reruns on the same input and the same sources deliver the same verdicts and the same set of facts and statements (same number of facts; order and wording may differ). The owner saw vastly different outputs when calling the old version several times. FR-9 and FR-10 state it; FR-26 makes stability a criterion of every workflow. | AC-2, FR-9, FR-10, FR-26, risk table |

Notes for Plan: (1) the existing baselines already measure stability for the verdict styles (`eval/baselines/verdicts-styles.md`: single 100 %, cops 96 %, trial 92 %), so the verdict step itself is mostly stable; the large differences of the old version more likely come from the **lookup pipeline**: live web results change between runs, the order of search results and fetched pages differs, and extraction and synthesis then see different material. (2) The first measurement therefore separates the causes: run on the recorded web (`FixtureWebSession`) with a pinned seed and temperature 0, then repeat live with stored sources. (3) "Same facts" needs a matching rule in code, not a model: normalise the numbers, the entities and the anchored quote of each statement; two statements are the same fact when these match; wording and order are ignored. (4) A seed and `temperature` are part of the model pin in `eval-spec.md`.

### Progress output and speed of the suite builder (owner asked, 2026-10-24)
The first version was silent until the end and could take 20 minutes or more: the Hugging Face rows API needs about 30 seconds for some pages and the script read 40 of them. Changed in `tools/make_external_suite.py`: VitaminC is **one download of the 29 MB test file** (kept in `<out>/.cache`, no more paging); every step prints a progress line with the elapsed time (download percent, rows read, usable groups, each Wikidata query with its row count, a final summary); raw answers are cached so a repeat takes seconds. Measured on this host: **about 2 minutes** for a cold run (VitaminC download started after about a minute of server wait, then 3 seconds; Wikidata about a minute), about 10 seconds with a warm cache. A **bug in the Wikidata queries** was found by the row counts: mountains need the property *elevation above sea level* (P2044), not *height* (P2048) (2 rows before, 300 now); the thresholds for towers and bridges were relaxed. A run with `--n-wikidata 150` now gives the 150 pairs asked for in four families (towers, rivers, bridges, mountains), `--n-vitaminc 150` gives 150 contrastive groups (about 510 cases of 6,560 usable groups in the test split).

### Step 7 (risks and open questions) and the suites in place (2026-10-24)
| Id | Decision | Edit |
|---|---|---|
| D-32 | The owner generated the suites with 150 VitaminC groups and 150 Wikidata pairs (812 cases: VitaminC 342 dev and 170 holdout, Wikidata 184 dev and 116 holdout, audit sheet 166 rows) and puts them under `eval/`; **no change of AC-2 needed**. About 110 wrong claims in the holdout give about 85 percent power for the paired comparison; a holdout run with single voice and cops, 3 repeats, takes about 1.8 hours. Labelling the whole audit sheet is not needed: the sheet is shuffled, so the first 60 rows are a random sample for the agreement tool. | AC-2 state, plausibility row of FR-9 |
| D-33 | The proposed state of AC-24 and AC-26 (later, not in the first version) is confirmed; AC-19 is confirmed (D-29). | AC table |
| – | Step 7: the risk table was rebuilt with a state per row (21 rows: 1 resolved, 5 mitigated, 2 accepted, 1 deferred, 12 open); new risks from today's decisions: login security, migration to PostgreSQL, any user can break a workflow for everyone, the other requirement documents now disagree with the HLS, one person doing everything, the benchmark sources are in the training data, the VitaminC licence; five open questions for the owner (pins, latency number, check dialogues and `calibration.txt`, answer language, order of the work in Plan). | HLS section 7 |

### Answers to the five open questions and the confirmation of step 7 (owner, 2026-10-24)
| Id | Decision | Edit |
|---|---|---|
| – | **Step 7 confirmed.** | status line |
| D-34 | Model pins confirmed (`gemma4:12b-it-qat`, `gemma4:26b`); digests, seed and temperature to be recorded when Ollama is up. **A chat answer shows its first text within 10 seconds** on the light model. | NFR-7, AC-19, risk table |
| D-35 | The coding agent **may read `calibration.txt`**; it is treated as a **parameter file**. The owner declined to have it read right now (the `ls` was refused), so it is read in Plan when the check dialogues are drafted. | FR-25, data classes, risk table |
| D-36 | **English only** for now (answers and questions); German texts and other languages are future features. | scope, risk table |
| D-37 | **The order of the work is switched: (E) the lookup before (D) the literature review.** The lookup exists, is simpler and becomes the documented example workflow (specification, context graph, benchmark, the path of FR-20) for all later workflows. **Consequence for the success criterion (D-2, AC-9), to confirm:** the first skill through the path is the lookup, and the literature review is added within one month of the lookup's promotion; before, it was the other way round. | section 1, AC-9, order of the work |
