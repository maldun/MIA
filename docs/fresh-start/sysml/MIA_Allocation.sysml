/*
 * MIA system model, part 6 of 6: satisfaction, allocation and verification.
 *
 * Two levels, on purpose:
 *   satisfy   a requirement is satisfied by the system as a whole (the subject of every requirement is MiaSystem);
 *   allocate  the part or parts that carry it. Parts whose Implementation status is proposed, partly or
 *             postponed mean the requirement is not fully met yet; that is the gap list of
 *             docs/fresh-start/02_high_level_requirements.md section 4.
 */
package MIA_Allocation {
    private import MIA_Architecture::*;
    private import MIA_Requirements::miaRequirements::*;
    private import VerificationCases::*;

    // ---------------------------------------------------------------- satisfy

    satisfy con1 by mia;
    satisfy con2 by mia;
    satisfy con3 by mia;
    satisfy con4 by mia;
    satisfy con5 by mia;
    satisfy hlr01 by mia;
    satisfy hlr02 by mia;
    satisfy hlr03 by mia;
    satisfy hlr04 by mia;
    satisfy hlr05 by mia;
    satisfy hlr06 by mia;
    satisfy hlr07 by mia;
    satisfy hlr08 by mia;
    satisfy hlr09 by mia;
    satisfy hlr10 by mia;
    satisfy hlr11 by mia;
    satisfy hlr12 by mia;
    satisfy hlr13 by mia;
    satisfy hlr14 by mia;
    satisfy hlr15 by mia;
    satisfy hlr16 by mia;
    satisfy hlr17 by mia;
    satisfy hlr18 by mia;
    satisfy hlr19 by mia;
    satisfy hlr20 by mia;
    satisfy hlr21 by mia;
    satisfy hlr22 by mia;
    satisfy hlr23 by mia;
    satisfy hlr24 by mia;
    satisfy hlr25 by mia;
    satisfy hlr26 by mia;
    satisfy hlr27 by mia;

    // ---------------------------------------------------------------- allocate

    // constraints
    allocate con1 to mia.operation.composeStack;
    allocate con1 to mia.taskRuntime.modelManager;
    allocate con2 to mia.taskRuntime.modelManager;
    allocate con3 to mia.frontEnd.chatPage;
    allocate con3 to mia.frontEnd.characterRenderer;
    allocate con4 to mia.operation.httpsAccess;
    allocate con5 to mia.operation.httpsAccess;

    // interaction
    allocate hlr01 to mia.frontEnd.chatPage;
    allocate hlr01 to mia.webApp.chatService;
    allocate hlr01 to mia.webApp.chatLog;
    allocate hlr01 to mia.conversation.communicator;
    allocate hlr02 to mia.frontEnd.characterRenderer;
    allocate hlr02 to mia.frontEnd.hostBridge;
    allocate hlr02 to mia.conversation.expressor;
    allocate hlr03 to mia.voice.textFilter;
    allocate hlr03 to mia.voice.synthesizer;
    allocate hlr03 to mia.voice.voiceEffect;
    allocate hlr03 to mia.voice.streamer;
    allocate hlr03 to mia.frontEnd.audioPlayer;
    allocate hlr04 to mia.webApp.moodTracker;
    allocate hlr04 to mia.observability.runLog;
    allocate hlr04 to mia.observability.explainTool;
    allocate hlr05 to mia.webApp.presetsApi;
    allocate hlr05 to mia.webApp.accessControl;
    allocate hlr05 to mia.frontEnd.expressionEditor;
    allocate hlr06 to mia.frontEnd.chatPage;

    // intelligence
    allocate hlr07 to mia.taskRuntime.skillStore;
    allocate hlr07 to mia.taskRuntime.pipelineRunner;
    allocate hlr07 to mia.taskRuntime.storytelling;
    allocate hlr07 to mia.research.lookup;
    allocate hlr08 to mia.taskRuntime.library;
    allocate hlr08 to mia.taskRuntime.workflowGraph;
    allocate hlr08 to mia.learning.approvalGate;
    allocate hlr09 to mia.taskRuntime.planner;
    allocate hlr09 to mia.taskRuntime.pipelineRunner;
    allocate hlr10 to mia.taskRuntime.modelManager;
    allocate hlr10 to mia.operation.configuration;

    // trust
    allocate hlr11 to mia.verification.hardChecks;
    allocate hlr11 to mia.verification.verificationStyles;
    allocate hlr11 to mia.verification.claimExtractor;
    allocate hlr12 to mia.verification.sandbox;
    allocate hlr12 to mia.verification.webBroker;
    allocate hlr12 to mia.research.pdfReader;
    allocate hlr12 to mia.research.webTools;
    allocate hlr13 to mia.research.reviewPipeline;
    allocate hlr13 to mia.research.reviewCases;
    allocate hlr13 to mia.evaluation.judgeCalibration;

    // research
    allocate hlr14 to mia.research.lookup;
    allocate hlr14 to mia.research.webTools;
    allocate hlr14 to mia.research.sourceTrust;
    allocate hlr15 to mia.research.reviewRequest;
    allocate hlr15 to mia.research.reviewPipeline;
    allocate hlr15 to mia.research.scholarClients;
    allocate hlr15 to mia.research.pdfReader;
    allocate hlr15 to mia.research.reviewCases;
    allocate hlr16 to mia.research.scholarClients;
    allocate hlr16 to mia.research.sourceTrust;
    allocate hlr17 to mia.research.methodTransfer;

    // memory and behaviour
    allocate hlr18 to mia.conversation.memory;
    allocate hlr18 to mia.conversation.scheduleReminders;
    allocate hlr19 to mia.conversation.behaviourRules;

    // observability, evaluation, learning
    allocate hlr20 to mia.observability.runLog;
    allocate hlr20 to mia.observability.contentStore;
    allocate hlr20 to mia.observability.contextGraph;
    allocate hlr20 to mia.observability.explainTool;
    allocate hlr20 to mia.observability.reproducer;
    allocate hlr21 to mia.evaluation.harness;
    allocate hlr21 to mia.evaluation.suites;
    allocate hlr22 to mia.learning.router;
    allocate hlr22 to mia.learning.banditOverVariants;
    allocate hlr22 to mia.learning.approvalGate;

    // operation
    allocate hlr23 to mia.webApp.accessControl;
    allocate hlr23 to mia.observability.webLog;
    allocate hlr23 to mia.persistence.files;
    allocate hlr24 to mia.operation.httpsAccess;
    allocate hlr24 to mia.webApp.accessControl;
    allocate hlr25 to mia.operation.configuration;
    allocate hlr25 to mia.operation.launcher;
    allocate hlr25 to mia.operation.shutdownSequence;
    allocate hlr25 to mia.operation.composeStack;
    allocate hlr26 to mia.taskRuntime.pipelineRunner;
    allocate hlr26 to mia.taskRuntime.modelManager;
    allocate hlr26 to mia.research.reviewRequest;
    allocate hlr27 to mia.persistence.storageLayer;

    // ---------------------------------------------------------------- verification cases
    // Only the requirements whose verification needs more than a unit test are given a case here; the rest are
    // covered by the test suites named in the Trace metadata of the requirement.

    verification def ConversationCheck {
        doc /* Socket tests with a stub model (send, stream, stop, queue, two clients see the same), browser checks at
               360x740, 768x1024 and 1440x900 in both themes, and the manual phone checklist. */
        subject mia : MiaSystem;
        objective { verify hlr01; }
        return verdict : VerdictKind;
    }

    verification def VerifyBeforeAssertingCheck {
        doc /* Harness suites hard_checks, computable, verdicts and web_checks; precision of fail flags, false passes,
               coverage per check, agreement with the style verdicts, calibration, and the share of errors that
               verifier and generator have in common. */
        subject mia : MiaSystem;
        objective { verify hlr11; }
        return verdict : VerdictKind;
    }

    verification def UntrustedInputCheck {
        doc /* Injected-instruction pages in the research suites, sandbox escape and resource-limit tests, a sandbox
               that is missing must make the script check unavailable (never weaker). */
        subject mia : MiaSystem;
        objective { verify hlr12; }
        return verdict : VerdictKind;
    }

    verification def HonestConfidenceCheck {
        doc /* Review benchmark: hallucinated references must be 0, quote anchoring 100 percent, answerability
               compared with outcomes (calibration plot), contamination stated in every result. */
        subject mia : MiaSystem;
        objective { verify hlr13; }
        return verdict : VerdictKind;
    }

    verification def LiteratureReviewCheck {
        doc /* Tiers 0 to 3 of the review ladder: toy world (offline, in the test suite), textbook level, expert
               reviews, held-out recent reviews. Source recall and precision, violations of the cut-off, conclusion
               agreement, cross-field recall, calls, tokens and seconds, repeated with intervals. Development half
               for tuning, held-out half reported once. */
        subject mia : MiaSystem;
        objective { verify hlr15; }
        return verdict : VerdictKind;
    }

    verification def TraceabilityCheck {
        doc /* A recorded run is replayed into its graph and reproduced offline; the new graph equals the old one;
               a broken log is reported, never turned into a wrong graph; a token fed to the writer does not
               appear in the log. */
        subject mia : MiaSystem;
        objective { verify hlr20; }
        return verdict : VerdictKind;
    }

    verification def PrivacyCheck {
        doc /* Strict content security policy; a browser test that records every request the page makes and finds
               none outside the host; the web log lists every query that left the machine. */
        subject mia : MiaSystem;
        objective { verify hlr23; }
        return verdict : VerdictKind;
    }
}
