/*
 * MIA system model, part 3 of 6: requirements.
 *
 * Prose, rationale and the full baseline mapping: docs/fresh-start/02_high_level_requirements.md.
 * Numbers that appear in a requirement are declared as attributes of the requirement definition, so
 * that a later change is one edit and tools can list them.
 */
package MIA_Requirements {
    private import ScalarValues::*;
    private import MIA_Common::*;
    private import MIA_Architecture::MiaSystem;

    abstract requirement def MiaRequirement {
        doc /* Common base: every requirement is about the whole system. Finer allocation to parts is
               stated with allocate in MIA_Allocation. */
        subject mia : MiaSystem;
    }

    // ================================================================ constraints

    requirement def <'CON-1'> FreeAndOpen :> MiaRequirement {
        doc /* Local models through Ollama, self-hosted search, no paid API; licence GPL-3.0-or-later. */
    }
    requirement def <'CON-2'> HardwareEnvelope :> MiaRequirement {
        doc /* One consumer GPU with 12 GB, 62 GB RAM, one language model loaded at a time. */
        attribute gpuMemoryGB : Real = 12;
        attribute loadedModels : Integer = 1;
    }
    requirement def <'CON-3'> TechnologyChoices :> MiaRequirement {
        doc /* Python 3.11 to 3.13; Godot 4.x with GDScript only and the Compatibility renderer; chat page in plain
               HTML, CSS and ES modules without a build step or UI framework. */
    }
    requirement def <'CON-4'> SecureContext :> MiaRequirement {
        doc /* The 3D character runs only on localhost or over HTTPS. */
    }
    requirement def <'CON-5'> PrivateNetworkOnly :> MiaRequirement {
        doc /* Remote access only inside a private network (Tailscale); no public port, never tailscale funnel. */
    }

    // ================================================================ interaction

    requirement def <'HLR-01'> Conversation :> MiaRequirement {
        doc /* MIA shall let the owner hold a conversation in a web browser on desktop and phone, with answers
               appearing while they are written, the ability to stop an answer, one waiting message while she is
               busy, a history that survives reload, and the same conversation visible live on every connected device. */
        attribute queuedMessages : Integer = 1;
        attribute messagesPerMinute : Integer = 10;
        @Trace { :>> baseline = ("CT-1", "CT-2", "CT-3", "CT-4", "CT-5", "CT-6", "CT-8", "CT-9", "CT-11");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'HLR-02'> EmbodiedCharacter :> MiaRequirement {
        doc /* MIA shall show her emotional state and speech through a 3D character: facial expressions that blend
               smoothly, arm gestures, a moving mouth while speaking, blinking and idle motion, driven through one
               central expression API; if the character cannot load, the chat shall still work. */
        attribute blendSeconds : Real = 0.25;
        attribute minFpsPhone : Real = 30;
        attribute minFpsDesktop : Real = 60;
        @Trace { :>> baseline = ("CH-1", "CH-3", "CH-4", "CH-5", "CH-6", "CH-10", "CH-12", "EM-1");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration, HowVerified::measurement); }
    }
    requirement def <'HLR-03'> Voice :> MiaRequirement {
        doc /* MIA shall speak her answers aloud sentence by sentence with a voice synthesised on the host,
               speaking only what is meant to be heard (no markup, no stage directions), and shall let the owner
               mute or stop her. */
        @Trace { :>> baseline = ("VO-1", "VO-2", "VO-3", "VO-4", "CT-7");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'HLR-04'> TransparencyOfStateAndMethod :> MiaRequirement {
        doc /* MIA shall tell the owner in one short line how she feels and what she is doing, and shall let the
               owner open, for any answer produced by a task, a step-by-step account of how it came about; the
               accurate description shall always come from real event data, never from a model. */
        attribute moodHoldMinutes : Integer = 10;
        @Trace { :>> baseline = ("CT-2", "LG-1", "LG-3");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'HLR-05'> OwnerShapedAppearanceAndPersona :> MiaRequirement {
        doc /* MIA shall let the owner change expressions, gestures, backgrounds, mood phrases, emotions and the
               persona as data, without changing code, and shall protect changes that affect all devices with a token. */
        @Trace { :>> baseline = ("CH-4", "CH-6", "CH-7", "CH-8", "CH-9", "CT-2", "OP-5");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'HLR-06'> AccessibleOnEveryDevice :> MiaRequirement {
        doc /* MIA shall be usable by keyboard and screen reader, in dark and light themes, with reduced motion
               respected, on widths from 320 to 2560 px in current Chrome, Firefox and Safari (iOS 16+). */
        attribute minWidthPx : Integer = 320;
        attribute maxWidthPx : Integer = 2560;
        attribute minTouchTargetPx : Integer = 44;
        @Trace { :>> baseline = ("CT-10");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }

    // ================================================================ intelligence

    requirement def <'HLR-07'> TasksAsSkills :> MiaRequirement {
        doc /* MIA shall perform each kind of work (chat, lookup, literature review, storytelling, scheduling,
               summarising) as a task defined by a human-readable skill file and a pipeline, selectable by the
               owner, with the choice never made silently for tasks that reach the internet. */
        @Trace { :>> baseline = ("TK-1", "TK-2", "RS-1", "CT-11");
                 :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'HLR-08'> WorkflowsAsData :> MiaRequirement {
        doc /* MIA shall define every pipeline and agent workflow as validated, versioned data in a library of
               reusable entries with a lifecycle (draft, tested, trusted, retired); entries proposed by a model
               shall remain drafts until the owner approves them, shown as a diff and tried on the test set first. */
        @Trace { :>> baseline = ("TK-3", "TK-4", "TK-5", "TK-10");
                 :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'HLR-09'> SmallModelStrategies :> MiaRequirement {
        doc /* MIA shall reach useful quality with small local models by splitting work into narrow steps with
               structured outputs and testable targets, by keeping every model input inside a fixed share of the
               context window, by letting code do everything code can do, and by spending more calls only when a
               target is unmet. */
        attribute cheapTryMaxCalls : Integer = 15;
        attribute contextSharePercent : Real = 50;
        @Trace { :>> baseline = ("TK-6", "TK-9", "RS-3");
                 :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'HLR-10'> ModelManagement :> MiaRequirement {
        doc /* MIA shall run on a local model server, let the owner switch between a light and a full model, free
               GPU memory on request, and say plainly when the model server is unreachable. */
        @Trace { :>> baseline = ("C-1", "C-2", "C-3", "CT-11");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }

    // ================================================================ trust

    requirement def <'HLR-11'> VerifyBeforeAsserting :> MiaRequirement {
        doc /* MIA shall check what can be checked by code first (arithmetic, dates, schemas, quotes present in
               their source, executable claims), use model judgement only for the rest, treat "unknown" and
               "unverified" as proper answers, and let a failed hard check outweigh any model verdict. */
        @Trace { :>> baseline = ("VE-1", "VE-2", "VE-4", "VE-5", "VE-7");
                 :>> verifiedBy = (HowVerified::measurement, HowVerified::test); }
    }
    requirement def <'HLR-12'> UntrustedInputStaysData :> MiaRequirement {
        doc /* MIA shall treat all text from the web, papers, PDFs and users as data that never acts as
               instruction; run model-written scripts and parse hostile documents only inside an isolating
               sandbox; and if the sandbox is missing refuse the operation instead of weakening it. */
        @Trace { :>> baseline = ("VE-3", "VE-6", "RS-7");
                 :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'HLR-13'> HonestConfidence :> MiaRequirement {
        doc /* MIA shall state how sure she is only with figures computed by code from anchored evidence, never
               show a source she did not retrieve, and report limits (contamination, small samples, missing
               access) with every result. */
        attribute maxHallucinatedReferences : Integer = 0;
        attribute minQuoteAnchoringPercent : Real = 100;
        @Trace { :>> baseline = ("RS-10", "RS-11", "EV-2");
                 :>> verifiedBy = (HowVerified::measurement); }
    }

    // ================================================================ research

    requirement def <'HLR-14'> Lookup :> MiaRequirement {
        doc /* MIA shall answer a factual question quickly with the sources and verbatim quotes that support it,
               preferring a trusted source to a model judgement, and say "unknown" when nothing supports an answer. */
        @Trace { :>> baseline = ("RS-1", "RS-6");
                 :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'HLR-15'> LiteratureReview :> MiaRequirement {
        doc /* Given a research question, an optional field scope, a cut-off date and a budget, MIA shall produce a
               structured report of the literature found: sources kept and dropped with reasons, findings per
               sub-question with verbatim anchors, conflicts between sources, an answerability figure with its
               parts, open gaps and suggested next keywords. She shall work in time slices, give an intermediate
               report with a recommendation at the end of each slice, and continue only when the owner agrees. */
        attribute firstSliceSeconds : Real = 60;
        attribute checkpointEverySources : Integer = 10;
        @Trace { :>> baseline = ("RS-2", "RS-3", "RS-4", "RS-5", "RS-7", "RS-8", "RS-9", "RS-10", "RS-12", "RS-14");
                 :>> verifiedBy = (HowVerified::measurement, HowVerified::test); }
    }
    requirement def <'HLR-16'> KnowledgeOfSources :> MiaRequirement {
        doc /* MIA shall record where a source comes from and how far she trusts it (class, venue, date,
               peer-review status, retraction or correction status read from the metadata), keep the owner's edits
               of that trust, and honour a time cut-off strictly. */
        @Trace { :>> baseline = ("RS-5", "RS-6");
                 :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'HLR-17'> MethodTransfer :> MiaRequirement {
        doc /* On request MIA shall look for methods from other fields that fit the structure of the problem,
               offering few ranked candidates marked as hypotheses unless an executable test on a toy instance
               passed. Off by default. */
        attribute defaultCandidates : Integer = 3;
        @Trace { :>> baseline = ("RS-13");
                 :>> verifiedBy = (HowVerified::measurement, HowVerified::test); }
    }

    // ================================================================ memory and behaviour

    requirement def <'HLR-18'> Memory :> MiaRequirement {
        doc /* MIA shall remember the relationship over time: keep the raw conversation, keep structured facts,
               preferences and commitments with a link back to their source, consolidate at rest, retrieve what is
               relevant within the token budget, let the owner inspect, correct and delete any record, and never
               store a fact about the owner that came from web or file text. */
        @Trace { :>> baseline = ("ME-1", "ME-2");
                 :>> verifiedBy = (HowVerified::measurement, HowVerified::test); }
    }
    requirement def <'HLR-19'> BehaviourRulesAndFeedback :> MiaRequirement {
        doc /* MIA shall detect violations of defined behaviour rules, repair them silently, record them as
               signals, and let signals change later behaviour through selection, written lessons and examples;
               reward for factual answers shall come from checks and sources, not from the owner's approval alone;
               no correction shall enter the conversation memory as a scolding. */
        @Trace { :>> baseline = ("BF-1", "BF-2", "EM-1", "EM-2");
                 :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }

    // ================================================================ observability, evaluation, learning

    requirement def <'HLR-20'> Traceability :> MiaRequirement {
        doc /* MIA shall write every run as typed, schema-checked events carrying one run id through every model
               call, web or API request and check, with secrets removed; any statement in an answer shall be
               traceable back to the query that found its source; any recorded run shall be replayable into its
               graph and reproducible offline, and two runs shall be comparable event by event. */
        @Trace { :>> baseline = ("LG-1", "LG-2", "LG-3", "LG-4");
                 :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'HLR-21'> MeasurableQuality :> MiaRequirement {
        doc /* MIA shall be evaluated by a harness that runs pipeline variants on fixed suites with repeats,
               intervals and cost counting; every behaviour change shall start with a test case; claims of
               improvement shall hold on held-out cases. */
        @Trace { :>> baseline = ("EV-1", "RS-14", "RS-15");
                 :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'HLR-22'> OptionalLearning :> MiaRequirement {
        doc /* MIA shall learn only from logged signals, only in discrete choices of configuration and graph
               weights (never model weights unless the owner decides so later), with every learned choice logged
               next to the default, switchable off and reversible. */
        @Trace { :>> baseline = ("LN-1", "RS-15");
                 :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }

    // ================================================================ operation

    requirement def <'HLR-23'> LocalFirstPrivacy :> MiaRequirement {
        doc /* MIA shall keep conversations, memory, logs and models on the host; the only data leaving the host
               shall be the text of a web search or scholarly query (and an e-mail address only if the owner
               configured one); the page shall load nothing from the internet. */
        @Trace { :>> baseline = ("C-5", "CT-10", "VE-6");
                 :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'HLR-24'> SecureAccess :> MiaRequirement {
        doc /* MIA shall be reachable from other devices only over HTTPS inside the home network or the owner's
               tailnet; require a token for actions that change shared data or delete history; check origins and
               limit message rates. */
        @Trace { :>> baseline = ("OP-4", "OP-5");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'HLR-25'> Operable :> MiaRequirement {
        doc /* MIA shall be installable and runnable from a single configuration file and one command (venv or
               compose stack), shut down in an orderly way that saves her memory, back up and restore her data,
               and report missing options after an update. */
        @Trace { :>> baseline = ("OP-1", "OP-2", "OP-3", "OP-6");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'HLR-26'> EfficientOnGivenHardware :> MiaRequirement {
        doc /* MIA shall give a chat answer's first text within seconds on the light model, keep every task under
               explicit budgets (steps, seconds, calls, tokens), and end a run that exceeds a budget with what she
               has and a statement of what is missing. */
        @Trace { :>> baseline = ("C-2", "CT-9", "RS-9");
                 :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'HLR-27'> RoomToGrow :> MiaRequirement {
        doc /* MIA shall keep her state behind storage interfaces so that several instances can later share one
               memory in a database without changing the components that use it. Postponed. */
        @Trace { :>> baseline = ("OP-7", "CT-8");
                 :>> verifiedBy = (HowVerified::inspection); }
    }

    // ================================================================ the requirement tree

    /* Usages, so that satisfy and verify can refer to them. */
    requirement miaRequirements {
        doc /* Constraints first, then the high-level requirements in the order of the prose document. */

        requirement con1 : FreeAndOpen;
        requirement con2 : HardwareEnvelope;
        requirement con3 : TechnologyChoices;
        requirement con4 : SecureContext;
        requirement con5 : PrivateNetworkOnly;

        requirement hlr01 : Conversation;
        requirement hlr02 : EmbodiedCharacter;
        requirement hlr03 : Voice;
        requirement hlr04 : TransparencyOfStateAndMethod;
        requirement hlr05 : OwnerShapedAppearanceAndPersona;
        requirement hlr06 : AccessibleOnEveryDevice;
        requirement hlr07 : TasksAsSkills;
        requirement hlr08 : WorkflowsAsData;
        requirement hlr09 : SmallModelStrategies;
        requirement hlr10 : ModelManagement;
        requirement hlr11 : VerifyBeforeAsserting;
        requirement hlr12 : UntrustedInputStaysData;
        requirement hlr13 : HonestConfidence;
        requirement hlr14 : Lookup;
        requirement hlr15 : LiteratureReview;
        requirement hlr16 : KnowledgeOfSources;
        requirement hlr17 : MethodTransfer;
        requirement hlr18 : Memory;
        requirement hlr19 : BehaviourRulesAndFeedback;
        requirement hlr20 : Traceability;
        requirement hlr21 : MeasurableQuality;
        requirement hlr22 : OptionalLearning;
        requirement hlr23 : LocalFirstPrivacy;
        requirement hlr24 : SecureAccess;
        requirement hlr25 : Operable;
        requirement hlr26 : EfficientOnGivenHardware;
        requirement hlr27 : RoomToGrow;
    }
}
