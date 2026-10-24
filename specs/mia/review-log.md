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
