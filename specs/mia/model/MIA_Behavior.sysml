/*
 * MIA system model, part 5 of 6: behaviour.
 *
 * Five behaviours, in the order of how far they are built:
 *   ChatExchange     built      one message, one answer, expression, voice, log
 *   MiaActivity      built      the activity shown in the status line
 *   LookupRun        built      quick fact check with sources
 *   LiteratureReviewRun partly  stages R0 to R8 of REQUIREMENTS_RESEARCH; the slice rule (ReviewRunStates) is
 *                               built as Budget.extend, the stages themselves are proposed
 *   Consolidation    proposed   "dreaming" as target design (today: summary of the history)
 *
 * Actions describe the order of steps, not their implementation. Loops (the repair round of the lookup, the
 * rounds of an agent session) are stated in the docs of the steps, because the number of rounds is behaviour
 * of the orchestrator and is recorded in the log, not fixed in the graph (REQUIREMENTS_CORE PG12).
 */
package MIA_Behavior {
    private import ScalarValues::*;
    private import MIA_Architecture::*;

    // ---------------------------------------------------------------- items

    item def Question { attribute text : String; }
    item def Claim { attribute text : String; }
    item def Passage { attribute quote : String; attribute source : String; attribute anchorFound : Boolean; }
    item def Answer { attribute text : String; attribute status : String; }   // answered or unknown
    item def ResearchQuestion {
        attribute text : String;
        attribute cutOffDate : String[0..1];
    }
    item def Budget {
        attribute sliceSeconds : Real;
        attribute maxCalls : Integer;
        attribute maxTokens : Integer;
        attribute maxApiRequests : Integer;
    }
    item def ReviewReport {
        attribute answerabilityPercent : Real;
        attribute isIntermediate : Boolean;
    }
    item def Recommendation { attribute continueRun : Boolean; attribute reason : String; }

    // signals for the state machines
    item def MessageReceived;
    item def FirstTextArrived;
    item def AnswerFinished;
    item def SpeechEnded;
    item def DreamRequested;
    item def DreamFinished;
    item def ModelUnreachable;
    item def ModelReachable;
    item def LimitReached;
    item def SufficiencyReached;
    item def OwnerContinues;
    item def OwnerStops;

    // ---------------------------------------------------------------- chat exchange

    action def ChatExchange {
        doc /* From a typed message to a shown, spoken and logged answer. The socket handler acknowledges at once;
               everything below runs in a background task, one exchange at a time. */
        in item userMessage : ChatMessage;
        out item answer : ChatMessage;

        action validate {
            doc /* Length, control characters, rate limit; commands are recognised on the server. */
        }
        action enqueue {
            doc /* One place in the queue while MIA is busy; otherwise refused with a hint. */
        }
        action assemblePrompt {
            doc /* Persona, memory, recent turns; target: retrieved memories and lessons within the token budget. */
        }
        action streamAnswer {
            doc /* Tokens from the model server, deltas to all devices (at most about 20 per second). A stop request
                   ends it and keeps the text received so far. */
        }
        action splitEmotion {
            doc /* The emotion keyword is cut out of the text; a missing one is repaired, not scolded (target). */
        }
        action expressCharacter {
            doc /* Preset and gesture for the emotion, mood line from the mood tracker. */
        }
        action speakAnswer {
            doc /* Filtered text, sentence by sentence; voice clip for the expression. */
        }
        action recordMessage {
            doc /* Chat log (visible messages) and run log (events); memory gets the exchange. */
        }

        first start;
        then validate;
        then enqueue;
        then assemblePrompt;
        then streamAnswer;
        then splitEmotion;
        then expressCharacter;
        then speakAnswer;
        then recordMessage;
        then done;
    }

    // ---------------------------------------------------------------- lookup

    action def LookupRun {
        doc /* Quick fact check (formerly "research"). Nothing starts a web search except the owner's command.
               The cheap first try comes first; a gap round (at most two) is requested only for unmet targets. */
        in item question : Question;
        out item result : Answer;

        action understand {
            doc /* Rewrite the question; decide whether search is needed at all. */
        }
        action plan {
            doc /* Router in code: compound questions get a typed plan, others the cheap try; plan checks in code. */
        }
        action search {
            doc /* SearXNG with DuckDuckGo fallback; results merged and ranked; every query logged. */
        }
        action fetch {
            doc /* Page text cleaned in code; private addresses blocked; injection signals flagged. */
        }
        action extract {
            doc /* Passages copied verbatim; code checks that each quote occurs in its page. */
        }
        action synthesise {
            doc /* Answer in the user's language from extracted passages only, with numbered sources. */
        }
        action verify {
            doc /* Hard checks first; a style only for open claims; the verifier sees claim and passage only. */
        }
        action repair {
            doc /* Unsupported claims removed or marked unverified; a contradiction may trigger one more search round. */
        }
        action report {
            doc /* Answer, sources with quotes, an honesty line, the status block. */
        }

        first start;
        then understand;
        then plan;
        then search;
        then fetch;
        then extract;
        then synthesise;
        then verify;
        then repair;
        then report;
        then done;
    }

    // ---------------------------------------------------------------- literature review

    action def LiteratureReviewRun {
        doc /* Stages R0 to R8 of REQUIREMENTS_RESEARCH, under a budget in slices (see ReviewRunStates). Every stage
               writes typed events; every model call sees a view of the context graph that fits its token budget. */
        in item question : ResearchQuestion;
        in item budget : Budget;
        out item report : ReviewReport;

        action intake {
            doc /* R0: question, date cut-off, budget; one clarifying question if the question is ambiguous. */
        }
        action analyse {
            doc /* R1: system analyser: structure, sub-questions, fields from the field graph, inclusion criteria,
                   targets a check can test. */
        }
        action components {
            doc /* R2: component determiner: experts, keyword sets per expert, merged and normalised by code. */
        }
        action acquire {
            doc /* R3: scholarly APIs and web search; de-duplicate; metadata incl. retraction status; cut-off applied. */
        }
        action screenAbstracts {
            doc /* R4 stage 1: abstract and conclusion, several votes, recall-oriented, borderline goes on. */
        }
        action screenPieces {
            doc /* R4 stage 2: full text (open access) cut into pieces by code; relevant pieces extracted verbatim
                   with an anchor check. */
        }
        action weigh {
            doc /* R5: source trust, study design, recency; one weight per finding, computed by code. */
        }
        action synthesise {
            doc /* R6: findings per sub-question, conflicts, open slots; gap check; one citation step. */
        }
        action judge {
            doc /* R7: answerability per sub-question and overall, computed by code from anchored evidence. */
        }
        action compose {
            doc /* R8: report: method with PRISMA-like counts, sources table, findings, conflicts, limits, gaps. */
        }

        first start;
        then intake;
        then analyse;
        then components;
        then acquire;
        then screenAbstracts;
        then screenPieces;
        then weigh;
        then synthesise;
        then judge;
        then compose;
        then done;
    }

    /* The slice discipline of RV30a around the stages above. The orchestrator is code; the recommendation comes
       from what the last slice achieved (new relevant sources kept, new anchored findings, open slots closed). */
    state def ReviewRunStates {
        entry; then running;

        state running;
        state intermediateReport {
            doc /* Report so far, with a recommendation (continue or stop, and why). Nothing continues by itself. */
        }
        state finished;

        transition first running accept LimitReached then intermediateReport;
        transition first running accept SufficiencyReached then finished;
        transition first running accept OwnerStops then finished;
        transition first intermediateReport accept OwnerContinues then running;
        transition first intermediateReport accept OwnerStops then finished;
    }

    // ---------------------------------------------------------------- consolidation

    action def Consolidation {
        doc /* Target design of "dreaming" (REQUIREMENTS_CORE MM2, proposed). Today MIA summarises the whole history,
               summarises the summaries and starts a new history; that is the baseline this must beat. */
        in item episodesSinceLastRun;
        out item digest;

        action selectEpisodes;
        action extractCandidates {
            doc /* Facts, preferences, commitments as structured records with source message ids. */
        }
        action verifyAgainstSource {
            doc /* A candidate must be supported by its source message; web or file text never becomes a fact about the owner. */
        }
        action merge {
            doc /* Add, update, contradict (keep both, mark the older one) or no-op. */
        }
        action summariseTopics {
            doc /* Summaries that link back to their sources: an index into the episodes, not a replacement. */
        }
        action decay;
        action writeDigest {
            doc /* "What I took from today", which the owner can correct. */
        }

        first start;
        then selectEpisodes;
        then extractCandidates;
        then verifyAgainstSource;
        then merge;
        then summariseTopics;
        then decay;
        then writeDigest;
        then done;
    }

    // ---------------------------------------------------------------- activity shown to the user

    state def MiaActivity {
        doc /* The activity of the status line (chat_status.activity). The mood is the emotion of the latest
               message and is kept separately by the mood tracker. */
        entry; then idle;

        state idle;
        state thinking;
        state speaking;
        state dreaming;
        state offline;

        transition first idle accept MessageReceived then thinking;
        transition first thinking accept FirstTextArrived then speaking;
        transition first thinking accept AnswerFinished then idle;
        transition first speaking accept SpeechEnded then idle;
        transition first idle accept DreamRequested then dreaming;
        transition first dreaming accept DreamFinished then idle;
        transition first idle accept ModelUnreachable then offline;
        transition first thinking accept ModelUnreachable then offline;
        transition first offline accept ModelReachable then idle;
    }
}
