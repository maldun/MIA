# Review log of the HLS (step by step, started 2026-10-24)

Rule of the review: one HLS section per step; the owner confirms each step before the next starts. Decisions are recorded here with the owner's words condensed; each says which HLS sections it touches and whether the edit is done. Steps: 1 context, goal, scope; 2 constraints and environment; 3 requirements (FR, NFR); 4 agent profile; 5 architecture; 6 acceptance criteria; 7 risks and open questions.

## Step 1: context, goal, scope (answers of 2026-10-24)

| Id | Decision (owner) | Touches | Edit |
|---|---|---|---|
| D-1 | MIA becomes a **multi-user system with login** and a **database** that stores information between apps. Reverses the non-goal "multi-user operation" and lifts the postponement of `deploy/REQUIREMENTS_DB.md`. | 1, 2, NFR-6, NFR-8, CON, architecture (Persistence, access control), baseline OP-7 | scope edited in step 1; requirements in step 3 |
| D-2 | Development is **iterative**: MIA develops several skills and workflows. Success = one skill built (the literature review) **and a second skill added within 1 month**. | 1, 6 | goal edited in step 1; criterion drafted as AC-9, confirmed in step 6 |
| D-3 | Character and behaviour requirements (answer to question 3), listed below as C-1..C-8 | 3, 4, 5, 6 | recorded; applied in steps 3 to 6 |

### C-1..C-8 (owner, 2026-10-24), to be turned into requirements in step 3
- **C-1 Mood in every situation.** The character reacts with a mood in every situation and shows the expression mapped to that mood.
- **C-2 Voice.** The voice is made automatically by an open TTS (Kokoro for now), played in the browser; a post-processing step makes it sound anime-like.
- **C-3 Character exchange.** A character is easy to select from a VRoid model (`.vrm`); original and compiled files are transferred with scripting tools.
- **C-4 Editors.** Expressions and motions are adjusted in an expression editor and a motion editor; changes update automatically.
- **C-5 Persona from `calibration.txt`.** A provided `calibration.txt` makes the persona behave roughly as specified: correct names and pronouns (for example "master") and back-story bits are repeated.
- **C-6 Feedback system.** Plus/minus feedback measures overall feedback over time and allows adjustment on that metric. A small story tells what MIA receives (money, love points, ...). The mood changes with feedback and an overall score is reflected in the general mood. Categories: answer quality, reactions, character behaviour, service; points are added and subtracted per category.
- **C-7 Tasks and memos.** MIA stores tasks and memos and recites them correctly.
- **C-8 Learning from negative feedback.** Behaviour with negative feedback happens less often and, after at least 5 negative feedbacks, stops (or at most 1 % chance). On negative feedback MIA behaves shocked.

Fit with what exists: C-1, C-2 (partly), C-3 (partly), C-4 (built for expressions and gestures; "motion editor" = gesture editor), C-5 (persona exists, not measured), C-7 (hourly time check and `TASK:` convention only; ledger proposed in `REQUIREMENTS_CORE` MM1), C-6 and C-8 (new; C-8 is the "consequences" ladder BF3 plus a hard rule). Tension to settle in step 3: C-8 ("stops after 5 negatives") versus `BF4` (approval must not be the only reward, no sycophancy); and C-6 "money, love points" is a character story, not a real payment.

### Open questions raised by D-1 (to be answered before step 3)
1. Memory, persona and feedback: **per user** or one shared MIA? (2026-10-21 decision was "one shared MIA with one memory".)
2. Roles: an owner/administrator who sees everything, and ordinary users?
3. Login: local accounts with passwords, an identity provider, or the tailnet identity?
4. "Between apps": which other applications use the database?
