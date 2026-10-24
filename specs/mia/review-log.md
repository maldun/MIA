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
