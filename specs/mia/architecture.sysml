/*
 * MIA, high-level architecture (Phase 1, specs/mia/high-level-spec.md).
 *
 * One file, six packages, in this order:
 *   MIA_Common        status and verification enums, metadata Implementation and Trace
 *   MIA_Architecture  items, ports, interfaces, MiaSystem with 13 subsystems; leaf parts name their code files
 *   MIA_AgentView     the app agent: model steps, untrusted items, trust boundaries (agent-app conventions, 8)
 *   MIA_Requirements  constraints CON-1..5, functional FR-1..FR-19, non-functional NFR-1..NFR-9
 *   MIA_Allocation    satisfy by the system, allocate to the parts that carry it, verification cases
 *
 * Supplements in specs/mia/model/: MIA_Context.sysml (people, concerns, external systems, context) and
 * MIA_Behavior.sysml (chat exchange, lookup, review, consolidation, activity states). They import from here.
 *
 * Requirement short names are the ids of the HLS. The ids HLR-01..27 of the first draft (docs/fresh-start)
 * are mapped in the table in section 3.5 of the HLS.
 * Not parsed by a SysML tool so far, see specs/mia/KNOWN_RISKS.md.
 */

package MIA_Common {
    private import ScalarValues::*;

    /* How far an element of the model is realised in the code base on 2026-10-24
       (taken from ui/README.md and the commit log, not re-verified by running the tests). */
    enum def ImplementationStatus {
        doc /* built: code and tests exist.
               partly: some of it exists.
               proposed: written down only.
               postponed: decided to wait.
               dropped: decided against. */
        enum built;
        enum partly;
        enum proposed;
        enum postponed;
        enum dropped;
    }

    /* How a requirement is shown to hold. */
    enum def HowVerified {
        enum test;           // automatic test
        enum measurement;    // evaluation harness, with repeats and intervals
        enum inspection;     // reading code, configuration or logs
        enum demonstration;  // manual check, e.g. the phone checklist
    }

    /* Attached to parts: where the element lives in the repository and how far it is built. */
    metadata def Implementation {
        attribute status : ImplementationStatus;
        attribute modules : String[0..*];   // file names relative to the repository root
    }

    /* Attached to requirements: where the requirement comes from, how it is verified. */
    metadata def Trace {
        attribute baseline : String[0..*];  // ids in specs/mia/baseline-requirements.md
        attribute verifiedBy : HowVerified[1..*];
    }
}

package MIA_Architecture {
    private import ScalarValues::*;
    private import MIA_Common::*;

    // ---------------------------------------------------------------- items that cross interfaces

    item def ChatMessage {
        attribute text : String;
        attribute role : String;             // user, assistant, system
        attribute emotion : String[0..1];    // keyword that selects expression, gesture and mood
    }
    item def ChatStatus {
        attribute busy : Boolean;
        attribute activity : String;         // idle, thinking, speaking, dreaming, offline
        attribute model : String;
        attribute moodText : String;
    }
    item def ExpressionCommand { attribute name : String; }   // preset or gesture to play
    item def SpeechAudio;
    item def ModelRequest;
    item def ModelStream;
    item def SearchQuery { attribute text : String; }
    item def SearchResults;
    item def ScholarQuery { attribute text : String; attribute untilDate : String[0..1]; }   // date cut-off
    item def ScholarRecords;
    item def RunEvent {
        attribute run : String;              // one run id travels with every model call and request
        attribute seq : Integer;
        attribute eventType : String;             // typed vocabulary of REQUIREMENTS_CORE 13d
        attribute actorName : String;
    }

    // ---------------------------------------------------------------- ports and interfaces

    /* Seen from the server side; the browser uses the conjugate. */
    port def ChatPort {
        in item userMessage : ChatMessage;       // chat_send
        out item answer : ChatMessage;           // chat_start, chat_delta, chat_done, chat_message
        out item status : ChatStatus;            // chat_status
    }
    port def ExpressionPort { out item command : ExpressionCommand; }
    port def AudioPort { out item audio : SpeechAudio; }
    port def LlmPort {                            // seen from MIA: requests go out, tokens come in
        out item request : ModelRequest;
        in item tokens : ModelStream;
    }
    port def SearchPort {
        out item query : SearchQuery;
        in item results : SearchResults;
    }
    port def ScholarPort {
        out item query : ScholarQuery;
        in item records : ScholarRecords;
    }
    port def EventSink { in item runEvent : RunEvent; }

    interface def ChatLink {
        end browserSide : ~ChatPort;
        end serverSide : ChatPort;
    }
    interface def ExpressionLink {
        end serverSide : ExpressionPort;
        end characterSide : ~ExpressionPort;
    }
    interface def AudioLink {
        end speechSide : AudioPort;
        end pageSide : ~AudioPort;
    }
    interface def LlmLink {
        end miaSide : LlmPort;
        end serverSide : ~LlmPort;
    }
    interface def SearchLink {
        end miaSide : SearchPort;
        end engineSide : ~SearchPort;
    }
    interface def ScholarLink {
        end miaSide : ScholarPort;
        end providerSide : ~ScholarPort;
    }
    interface def EventLink {
        end sourceSide : ~EventSink;
        end sinkSide : EventSink;
    }

    // ---------------------------------------------------------------- the system

    part def MiaSystem {
        doc /* The whole of MIA on one host: browser-side parts (served by MIA) and host-side parts.
               One owner, one running exchange at a time, one memory. */

        port chat : ChatPort;
        port expression : ExpressionPort;
        port audio : AudioPort;
        port llm : LlmPort;
        port search : SearchPort;
        port scholar : ScholarPort;

        part frontEnd : WebFrontEnd;
        part webApp : WebApplication;
        part graphApp : GraphApp;
        part conversation : ConversationCore;
        part taskRuntime : TaskRuntime;
        part verifier : VerificationSuite;
        part research : ResearchSuite;
        part voice : VoiceSubsystem;
        part observability : Observability;
        part evaluation : Evaluation;
        part learning : LearningLayer;
        part persistence : Persistence;
        part operation : OperationLayer;

        // boundary ports are delegated to the parts that own the conversation
        bind chat = webApp.chat;
        bind expression = webApp.expression;
        bind audio = voice.audio;
        bind llm = taskRuntime.llm;
        bind search = research.search;
        bind scholar = research.scholar;

        // main internal flows
        interface expressionLink : ExpressionLink connect webApp.expression to frontEnd.expression;
        interface eventsFromRuntime : EventLink connect taskRuntime.events to observability.sink;
        interface eventsFromResearch : EventLink connect research.events to observability.sink;
        interface eventsFromVerification : EventLink connect verifier.events to observability.sink;
    }

    /* The single instance used by the allocation and by the context. */
    part mia : MiaSystem;

    // ---------------------------------------------------------------- browser-side

    part def WebFrontEnd {
        doc /* Served by MIA, runs on the viewer's device. The chat is plain HTML, CSS and ES modules;
               the character is a Godot web export in an iframe, reached through a postMessage bridge. */
        port expression : ~ExpressionPort;
        port chat : ~ChatPort;

        part chatPage {
            doc /* Bubbles, markdown, streaming, composer, command palette, mood line, themes. */
            @Implementation {
                :>> status = ImplementationStatus::built;
                :>> modules = ("templates/index.html", "templates/static/chat/app.js",
                               "templates/static/chat/chat.js", "templates/static/chat/mood.js");
            }
        }
        part characterRenderer {
            doc /* Godot 4 web export, toon shading, expression engine, gestures, blinking, idle motion. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("ui/godot", "ui/tools/export_character.py"); }
        }
        part expressionEditor {
            doc /* Slider panel and gesture editor; writes presets through the preset API with the editor token. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("ui/godot"); }
        }
        part hostBridge {
            doc /* Messages between the chat page and the character (expression, background, view, viewport_inset). */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("templates/static/chat/character.js", "ui/godot"); }
        }
        part audioPlayer {
            doc /* Exactly one page plays the speech audio; reports speaking state back. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("templates/static/chat/sound.js"); }
        }
    }

    // ---------------------------------------------------------------- host-side

    part def WebApplication {
        doc /* Flask and Socket.IO server: page, chat events, REST for history, presets and gestures. */
        port chat : ChatPort;
        port expression : ExpressionPort;

        part chatService {
            doc /* chat_send, stop, queue of one, background exchange, deltas, rate limit. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("chat_service.py", "chat_api.py", "web_app.py"); }
        }
        part chatLog {
            doc /* Append-only JSON lines, bounded, independent of the LLM memory. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("chat_log.py"); }
        }
        part moodTracker {
            doc /* Mood and activity of the status line, phrases from moods.json, hold time. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("moods.py", "moods.json"); }
        }
        part presetsApi {
            doc /* Presets, gestures, backgrounds; token-protected writes; expression generation from a description. */
            @Implementation {
                :>> status = ImplementationStatus::built;
                :>> modules = ("presets_api.py", "preset_store.py", "gesture_store.py", "expression_llm.py");
            }
        }
        part accessControl {
            doc /* Editor and chat tokens today (to be replaced by accounts, FR-21), allowed origins, content security policy. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("web_app.py", "presets_api.py"); }
        }
        part accountService {
            doc /* Target: accounts created by the owner, passwords as salted slow hashes, sessions, login throttling, password change. */
            @Implementation { :>> status = ImplementationStatus::proposed; }
        }
        part variantStore {
            doc /* Target: character variants as data (shown or hidden parts, colours), stored like presets; a workflow names one, the chat has the default. */
            @Implementation { :>> status = ImplementationStatus::proposed; :>> modules = ("preset_store.py", "presets_api.py"); }
        }
    }

    part def GraphApp {
        doc /* Target: web page of the same stack that shows workflow graphs as nodes and edges, as the ArangoDB web interface does,
               and edits each node and edge as a JSON dictionary on the shared database. Text data only. */
        part graphView {
            doc /* Node-and-edge view with a vendored graph library (plain HTML and JavaScript, no build step). */
            @Implementation { :>> status = ImplementationStatus::proposed; }
        }
        part nodeEditor {
            doc /* Edits one node or edge as a JSON document; saving creates a new version. */
            @Implementation { :>> status = ImplementationStatus::proposed; }
        }
        part versionStore {
            doc /* Immutable versions with author and time; history and diff; an edit by a model is a proposal. */
            @Implementation { :>> status = ImplementationStatus::proposed; :>> modules = ("library.py"); }
        }
        part graphValidator {
            doc /* The rules of the process graph model (identity, data nodes only connected through processes, cycles only inside a session) and the pipeline validation. */
            @Implementation { :>> status = ImplementationStatus::partly; :>> modules = ("pipeline_model.py", "context_graph.py"); }
        }
    }

    part def ConversationCore {
        doc /* The persona's side: conversation history, calibration, emotions, penalties, dreaming. */
        port events : ~EventSink;

        part communicator {
            doc /* History, calibration message, streaming through the model, emotion keyword, penalties, dreaming (summaries). */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("communicator.py"); }
        }
        part expressor {
            doc /* Maps emotion keyword to preset, gesture and voice clip; emits the expression event. */
            @Implementation {
                :>> status = ImplementationStatus::built;
                :>> modules = ("expressor.py", "emotion_map.json", "expressions.json");
            }
        }
        part behaviourRules {
            doc /* Speech rules as detectors with silent repair; target: all behaviour rules as library entries. */
            @Implementation { :>> status = ImplementationStatus::partly; :>> modules = ("behaviour.py", "tools/behaviour.py"); }
        }
        part memory {
            doc /* memories.json and long_time_history.json (runtime data, not in git). Target: five tiers with
                   consolidation (FR-14). */
            @Implementation { :>> status = ImplementationStatus::partly; :>> modules = ("communicator.py"); }
        }
        part scheduleReminders {
            doc /* Hourly time check; target: a commitment ledger read by code. */
            @Implementation { :>> status = ImplementationStatus::partly; :>> modules = ("communicator.py"); }
        }
        part persona {
            doc /* The persona file (calibration.txt, not in git): names, pronouns, back story; sent at every start. */
            @Implementation { :>> status = ImplementationStatus::partly; :>> modules = ("communicator.py"); }
        }
        part feedbackLedger {
            doc /* Target: votes (plus and minus) per category with user, time and subject; scores per category and overall; the story texts. */
            @Implementation { :>> status = ImplementationStatus::proposed; }
        }
        part behaviourRegistry {
            doc /* Target: an identity for every votable behaviour, counters of net votes, the chance per opportunity, reset. */
            @Implementation { :>> status = ImplementationStatus::proposed; :>> modules = ("behaviour.py"); }
        }
        part taskMemoStore {
            doc /* Target: tasks and memos as records, read back word for word by code. Today: the TASK convention in the memory. */
            @Implementation { :>> status = ImplementationStatus::partly; :>> modules = ("communicator.py"); }
        }
    }

    part def TaskRuntime {
        doc /* Skills, pipelines as data, the library, strategies; the place where a task is run under budgets. */
        port llm : LlmPort;
        port events : ~EventSink;

        part skillStore {
            doc /* skills/*.md with front matter, schemas, prompts, status block lines. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("skill_store.py", "skills/chat.md", "skills/research.md"); }
        }
        part pipelineRunner {
            doc /* Executes pipeline graphs of seven node kinds, enforces budgets, emits events, retries locally;
                   core.py loads a skill, takes its pipeline from the library and runs it. */
            @Implementation {
                :>> status = ImplementationStatus::built;
                :>> modules = ("core.py", "pipeline.py", "pipeline_model.py", "schema_check.py");
            }
        }
        part libraryStore {
            doc /* Versioned node and pipeline entries, statuses, SQLite index, selection, statistics. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("library.py", "tools/library.py", "library/nodes", "library/pipelines"); }
        }
        part planner {
            doc /* Plans as data, typed plans, plan checks in code, router in code. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("plans.py"); }
        }
        part workflowGraph {
            doc /* Target: workflows and agent sessions stored as process graphs and generated into runner configuration. */
            @Implementation { :>> status = ImplementationStatus::proposed; :>> modules = ("context_graph.py"); }
        }
        part scheduler {
            doc /* Target: from the graph and the measured node costs (a session node: its limits times the cost of one cycle) computes order, overlap, critical path and the estimate of time, calls and tokens; refuses a run that exceeds its budget (FR-33). */
            @Implementation { :>> status = ImplementationStatus::proposed; }
        }
        part storytelling {
            doc /* Premise, outline, scene loop with story state. */
            @Implementation { :>> status = ImplementationStatus::proposed; }
        }
        part modelManager {
            doc /* Starts or addresses Ollama, pulls missing models, light and full profiles, GPU modes. */
            @Implementation {
                :>> status = ImplementationStatus::built;
                :>> modules = ("install_lama.py", "ollama_remote.py", "cpu_threads.py");
            }
        }
        part skillScaffold {
            doc /* Target: template, checklist and time record for the path from idea to promoted skill (FR-20). */
            @Implementation { :>> status = ImplementationStatus::proposed; :>> modules = ("tools/library.py"); }
        }
    }

    part def VerificationSuite {
        doc /* Everything that decides whether a statement may be believed. Code first, models last. */
        port events : ~EventSink;

        part hardChecks {
            doc /* fixed_code, script, citation, web_confirm, injection signals; one result vocabulary. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("checks.py", "library/nodes"); }
        }
        part verificationStyles {
            doc /* single, consistency, cops, trial, jury as pipelines (drafts, not yet measured). */
            @Implementation { :>> status = ImplementationStatus::partly; :>> modules = ("verification.py", "library/pipelines"); }
        }
        part sandbox {
            doc /* bubblewrap and rootless podman tiers; refuses instead of weakening. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("sandbox.py", "sandbox_runner.py", "tools/sandbox"); }
        }
        part webBroker {
            doc /* The only way a sandboxed script reaches the web, over stdin and stdout. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("broker.py"); }
        }
        part claimExtractor {
            doc /* Claims out of prose with anchored quotes; rule-based and model-based variants. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("extraction.py", "skills/extract_claims.md"); }
        }
    }

    part def ResearchSuite {
        doc /* Lookup (built) and literature review (in progress), with their tools. */
        port search : SearchPort;
        port scholar : ScholarPort;
        port events : ~EventSink;

        part webTools {
            doc /* Search with SearXNG and DuckDuckGo fallback; page fetcher with safety rules; web log. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("web_tools.py", "searxng_control.py", "tools/searxng"); }
        }
        part lookup {
            doc /* Quick fact check: baseline, decompose, escalate, typed-plan pipelines. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("research.py", "research_chat.py", "research_score.py"); }
        }
        part scholarClients {
            doc /* OpenAlex, Crossref, PubMed, arXiv, Semantic Scholar; cache; cut-off; retraction status. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("scholar.py", "tools/scholar_check.py"); }
        }
        part sourceTrust {
            doc /* Prior trust per source class and venue, with reasons; owner's edits. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("source_trust.py", "library/source_trust.json"); }
        }
        part reviewRequest {
            doc /* Question, scope, cut-off, budget in slices with checkpoints. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("review_request.py"); }
        }
        part pdfReader {
            doc /* PDF to text only inside a bubblewrap wall. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("pdf_text.py"); }
        }
        part reviewCases {
            doc /* Reference cases from published reviews, reference-list parsing, scoring; real cases paused at 2c. */
            @Implementation {
                :>> status = ImplementationStatus::partly;
                :>> modules = ("review_case.py", "review_score.py", "tools/build_review_cases.py", "eval/suites/review_toy");
            }
        }
        part reviewPipeline {
            doc /* Planner roles, screening, weighing, synthesis, answerability, report (phases 2d to 6). */
            @Implementation { :>> status = ImplementationStatus::proposed; }
        }
        part methodTransfer {
            doc /* Optional: problem signature, template catalogue, transfer scout. */
            @Implementation { :>> status = ImplementationStatus::proposed; }
        }
    }

    part def VoiceSubsystem {
        doc /* Speech on the host: filter, synthesise, apply the voice effect, stream sentence by sentence. */
        port audio : AudioPort;

        part textFilter {
            doc /* Removes actions, markup and stage directions before speaking. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("speech_text.py"); }
        }
        part synthesizer {
            doc /* Kokoro on onnxruntime in its own process. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("speak.py"); }
        }
        part voiceEffect {
            doc /* Pitch, formant and sparkle presets (anime, robot, tiny). */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("voice_effects.py"); }
        }
        part streamer {
            doc /* Sentence-wise speech during streaming, numbered lines, clean-up. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("speech_stream.py", "audio_router.py"); }
        }
        part voiceLines {
            doc /* Short lines per mood and event (text plus audio file), intro and attention sounds with a chance; chosen at random among several; missing files skipped. */
            @Implementation { :>> status = ImplementationStatus::partly; :>> modules = ("expressor.py", "expressions.json", "speak.py"); }
        }
    }

    part def Observability {
        doc /* The log is the source of truth; graphs and explanations are views of it. */
        port sink : EventSink;

        part runLog {
            doc /* Typed events with schema, secret removal, run id. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("events.py", "run_log.py", "evidence.py"); }
        }
        part contentStore {
            doc /* Prompts, answers and pages by hash, retention by age. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("content_store.py"); }
        }
        part contextGraph {
            doc /* Replay of events into a process graph, explain, diff, views within a token budget. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("context_graph.py"); }
        }
        part explainTool {
            doc /* list, show, explain, cost, problems, diff, export, call, reproduce. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("run_explain.py", "tools/run_explain.py"); }
        }
        part reproducer {
            doc /* Repeats a recorded run offline and compares the new graph with the old one. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("reproduce.py"); }
        }
        part webLog {
            doc /* Every query MIA sent to the internet. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("web_tools.py"); }
        }
    }

    part def Evaluation {
        doc /* Harness, suites, metrics and baselines. Offline, on recorded data. */
        part harness {
            doc /* Variants x repeats x suites, cost counting, intervals, paired sign test. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("harness.py", "metrics.py", "tools/eval.py"); }
        }
        part suites {
            doc /* hard_checks, computable, extraction, verdicts, research, research_compound, plans, web_checks, behaviour, review_toy. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("eval/suites", "eval/baselines"); }
        }
        part judgeCalibration {
            doc /* LLM judge with a rubric calibrated on the owner's ratings. */
            @Implementation { :>> status = ImplementationStatus::proposed; }
        }
    }

    part def LearningLayer {
        doc /* Optional ladder: small router, bandit over variants, learned verifier, controller. Level 0 (rules and logging) is the rest of the system. */
        part router {
            @Implementation { :>> status = ImplementationStatus::proposed; }
        }
        part banditOverVariants {
            @Implementation { :>> status = ImplementationStatus::proposed; }
        }
        part approvalGate {
            doc /* Model-made changes are proposals shown as diffs and tried on the test set before the owner decides. */
            @Implementation { :>> status = ImplementationStatus::partly; :>> modules = ("library.py"); }
        }
    }

    part def Persistence {
        doc /* Everything is files on the host (JSON, JSON lines, Markdown, one SQLite index). Target: PostgreSQL in a container behind a storage layer (proposed). */
        part files {
            doc /* data/, memories.json, long_time_history.json, presets, gestures, chat log, runs, store, library. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("config.py", "constants.py"); }
        }
        part storageLayer {
            doc /* Interfaces over the file stores so that the database can replace them (stage 0 of the database plan). */
            @Implementation { :>> status = ImplementationStatus::proposed; }
        }
        part database {
            doc /* PostgreSQL in a container with a volume, a health check, migration from files and back, backup and restore. */
            @Implementation { :>> status = ImplementationStatus::proposed; :>> modules = ("deploy/REQUIREMENTS_DB.md"); }
        }
    }

    part def OperationLayer {
        doc /* Start, configure, shut down, deploy, expose. */
        part configuration {
            doc /* setup_cfg.json with an example listing every option; report of missing options. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("config.py", "setup_cfg.example.json"); }
        }
        part launcher {
            doc /* python -m MIA: Ollama, speech process, web app, HTTPS proxy. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("__main__.py", "mia_logger.py"); }
        }
        part shutdownSequence {
            doc /* Orderly stop for Ctrl+C, /break!, /goodnight!, SIGTERM; saves the history. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("shutdown.py"); }
        }
        part httpsAccess {
            doc /* Self-signed proxy on the LAN, Caddy in the compose stack, Tailscale serve for the tailnet. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("tls_proxy.py", "tailscale_serve.py", "deploy/Caddyfile"); }
        }
        part composeStack {
            doc /* MIA, Ollama, SearXNG and Caddy as containers; ROCm and NVIDIA overrides; up.sh. */
            @Implementation {
                :>> status = ImplementationStatus::built;
                :>> modules = ("deploy/compose.yaml", "deploy/Containerfile", "deploy/up.sh");
            }
        }
        part characterTools {
            doc /* Scripts that build the character from its source, export the VRM, pack and unpack the compiled web export. */
            @Implementation {
                :>> status = ImplementationStatus::partly;
                :>> modules = ("ui/tools/setup_character.sh", "ui/tools/export_character.py", "ui/tools/character_pack.py", "ui/character/README.md");
            }
        }
    }
}

package MIA_AgentView {
    private import ScalarValues::*;
    private import MIA_Architecture::*;

    // Annotations of the agent view (agent-app conventions, section 8)
    package Annotations {
        metadata def ModelStep {
            attribute schema : String;
            attribute tools : String;
            attribute tokenBudget : Integer;
            attribute secondBudget : Real;
            attribute pin : String;
            attribute criterion : String;
        }
        metadata def Untrusted { attribute origin : String; }
        metadata def TrustBoundary {
            attribute boundary : String;
            attribute threats : String;
        }
    }
    private import Annotations::*;

    // What crosses a trust boundary. Everything from the web, from papers, from files and from users is data.
    item def UserMessage { @Untrusted { origin = "user"; } doc /* Text typed by the owner or a guest. */ }
    item def FetchedPageText { @Untrusted { origin = "web"; } doc /* Cleaned text of a web page or search snippet. */ }
    item def PaperText { @Untrusted { origin = "web"; } doc /* Abstract or full text of a scholarly work (open access). */ }
    item def ChatHistory { @Untrusted { origin = "model"; } doc /* Earlier turns, which contain model output and quoted web text. */ }
    item def GeneratedScript { @Untrusted { origin = "model"; } doc /* A check script written by a model; runs only in the sandbox. */ }
    item def Verdict { attribute status : String; }
    item def WorkflowEdit { @Untrusted { origin = "user"; } doc /* A workflow, prompt or context graph edited by a user in the graph app (TB-edit). Users are trusted (CON-6); the edit is validated and versioned. */ }

    port def UserTextPort { out item userText : UserMessage; }
    port def PageTextPort { out item page : FetchedPageText; }
    port def PaperTextPort { out item paper : PaperText; }
    port def HistoryPort { out item history : ChatHistory; }
    port def ScriptPort { out item script : GeneratedScript; }
    port def EditPort { out item edit : WorkflowEdit; }

    // Code parts that hand untrusted text to model steps
    part def MessageIntake { doc /* Code: validation, rate limit, command recognition (chat_service.py). */ port messageOut : UserTextPort; }
    part def PageFetcher { doc /* Code: search and fetch tools with safety rules (web_tools.py). */ port pageOut : PageTextPort; }
    part def ScholarReader { doc /* Code: scholarly APIs, PDF to text inside a wall (scholar.py, pdf_text.py). */ port paperOut : PaperTextPort; }
    part def HistoryStore { doc /* Code: memories.json (communicator.py). */ port historyOut : HistoryPort; }
    part def GraphEditor { doc /* Code: the graph app; sends the edited node or graph as JSON (nodeEditor). */ port editOut : EditPort; }
    part def WorkflowValidator { doc /* Code, boundary TB-edit: checks graph rules and schemas, stores a new version, refuses a broken edit (pipeline_model.py, library.py). */ port editIn : ~EditPort; }
    part def ScriptSandbox { doc /* Code: runs a generated script isolated, no network (sandbox.py, broker.py). */ port scriptIn : ~ScriptPort; }

    // Model steps. HLS level: the attributes marked "Plan" are fixed in Phase 2. tokenBudget is the context window
    // (num_ctx 8192 on both profiles today), not yet a per-step budget.
    part def ChatStep {
        doc /* The persona's answer, streamed; emotion keyword first. Skill chat. */
        @ModelStep { schema = "none: free text"; tools = ""; tokenBudget = 8192; secondBudget = 0.0; pin = "MP-full"; criterion = "none: set in Plan"; }
        @TrustBoundary { boundary = "TB-user"; threats = ""; }
        port userIn : ~UserTextPort;
        port historyIn : ~HistoryPort;
    }
    part def PlanStep {
        doc /* Sub-questions or a typed plan for a compound question. Skill plan_question. */
        @ModelStep { schema = "plan.schema.json"; tools = ""; tokenBudget = 8192; secondBudget = 0.0; pin = "MP-light"; criterion = "none: set in Plan"; }
        @TrustBoundary { boundary = "TB-user"; threats = ""; }
        port userIn : ~UserTextPort;
    }
    part def ExtractionStep {
        doc /* Passages and claims from page text, quotes checked in code. Skills extract_claims, research. */
        @ModelStep { schema = "claims.schema.json"; tools = ""; tokenBudget = 8192; secondBudget = 0.0; pin = "MP-light"; criterion = "none: set in Plan"; }
        @TrustBoundary { boundary = "TB-web"; threats = ""; }
        port pageIn : ~PageTextPort;
    }
    part def VerdictStep {
        doc /* One voice, or argue-for, argue-against, rebut and judge (verification styles). Skill verify_claim. */
        @ModelStep { schema = "ruling.schema.json"; tools = ""; tokenBudget = 8192; secondBudget = 0.0; pin = "MP-light"; criterion = "none: set in Plan"; }
        @TrustBoundary { boundary = "TB-web"; threats = ""; }
        port pageIn : ~PageTextPort;
    }
    part def SynthesisStep {
        doc /* Answer written from verified passages only. Skill research. */
        @ModelStep { schema = "answer.schema.json"; tools = ""; tokenBudget = 8192; secondBudget = 0.0; pin = "MP-full"; criterion = "none: set in Plan"; }
        @TrustBoundary { boundary = "TB-web"; threats = ""; }
        port pageIn : ~PageTextPort;
    }
    part def ScriptWriterStep {
        doc /* Writes a short check script from a claim. The script is untrusted code. Skill verify_computable. */
        @ModelStep { schema = "script.schema.json"; tools = ""; tokenBudget = 8192; secondBudget = 0.0; pin = "MP-light"; criterion = "none: set in Plan"; }
        @TrustBoundary { boundary = "TB-code"; threats = ""; }
        port pageIn : ~PageTextPort;
        port scriptOut : ScriptPort;
    }
    part def ExpressionStep {
        doc /* Expression preset from a description in the editor (expression_llm.py). */
        @ModelStep { schema = "preset.schema.json"; tools = ""; tokenBudget = 8192; secondBudget = 0.0; pin = "MP-light"; criterion = "none: set in Plan"; }
        @TrustBoundary { boundary = "TB-user"; threats = ""; }
        port userIn : ~UserTextPort;
    }
    part def DreamStep {
        doc /* Summary of the history (today); extraction of structured memory records (target). Skill summarize. */
        @ModelStep { schema = "none: free text"; tools = ""; tokenBudget = 8192; secondBudget = 0.0; pin = "MP-light"; criterion = "none: set in Plan"; }
        @TrustBoundary { boundary = "TB-history"; threats = ""; }
        port historyIn : ~HistoryPort;
    }
    part def ReviewScreeningStep {
        doc /* Proposed: relevance of abstracts and pieces of papers to a research question. */
        @ModelStep { schema = "screening.schema.json"; tools = ""; tokenBudget = 8192; secondBudget = 0.0; pin = "MP-light"; criterion = "none: set in Plan"; }
        @TrustBoundary { boundary = "TB-paper"; threats = ""; }
        port paperIn : ~PaperTextPort;
    }
    part def ReviewPlannerStep {
        doc /* Proposed: system analyser, component determiner and scheduler as views of one model. */
        @ModelStep { schema = "review_plan.schema.json"; tools = ""; tokenBudget = 8192; secondBudget = 0.0; pin = "MP-full"; criterion = "none: set in Plan"; }
        @TrustBoundary { boundary = "TB-user"; threats = ""; }
        port userIn : ~UserTextPort;
    }

    part def MiaAgent {
        doc /* The app agent seen as flows of untrusted text into model steps. */
        part intake : MessageIntake;
        part fetcher : PageFetcher;
        part scholar : ScholarReader;
        part historyStore : HistoryStore;
        part sandbox : ScriptSandbox;
        part graphEditor : GraphEditor;
        part validator : WorkflowValidator;

        part chat : ChatStep;
        part planner : PlanStep;
        part extractor : ExtractionStep;
        part judge : VerdictStep;
        part synthesiser : SynthesisStep;
        part scriptWriter : ScriptWriterStep;
        part expression : ExpressionStep;
        part dreamer : DreamStep;
        part screener : ReviewScreeningStep;
        part reviewPlanner : ReviewPlannerStep;

        flow of UserMessage from intake.messageOut to chat.userIn;
        flow of UserMessage from intake.messageOut to planner.userIn;
        flow of UserMessage from intake.messageOut to expression.userIn;
        flow of UserMessage from intake.messageOut to reviewPlanner.userIn;
        flow of FetchedPageText from fetcher.pageOut to extractor.pageIn;
        flow of FetchedPageText from fetcher.pageOut to judge.pageIn;
        flow of FetchedPageText from fetcher.pageOut to synthesiser.pageIn;
        flow of FetchedPageText from fetcher.pageOut to scriptWriter.pageIn;
        flow of PaperText from scholar.paperOut to screener.paperIn;
        flow of ChatHistory from historyStore.historyOut to chat.historyIn;
        flow of ChatHistory from historyStore.historyOut to dreamer.historyIn;
        flow of GeneratedScript from scriptWriter.scriptOut to sandbox.scriptIn;
        flow of WorkflowEdit from graphEditor.editOut to validator.editIn;
    }
}

package MIA_Requirements {
    private import ScalarValues::*;
    private import MIA_Common::*;
    private import MIA_Architecture::MiaSystem;

    // ================================================================ constraints

    requirement def <'CON-1'> FreeAndOpen {
        subject mia : MiaSystem;
        doc /* Free and open: local models through Ollama, self-hosted search, no paid API; licence GPL-3.0-or-later. */
    }
    requirement def <'CON-2'> HardwareEnvelope {
        subject mia : MiaSystem;
        doc /* Hardware: Ryzen 9 5900X (24 threads), RX 7800 XT with 16 GB VRAM, 62 GB RAM (measured 2026-10-24); one language
               model loaded at a time (OLLAMA_MAX_LOADED_MODELS=1). With several users the model server serves
               one request at a time; the others wait in a queue. */
        attribute gpuMemoryGB : Real = 16;
        attribute loadedModels : Integer = 1;
    }
    requirement def <'CON-3'> TechnologyChoices {
        subject mia : MiaSystem;
        doc /* Python 3.12 (3.11 and 3.13 are not supported for now); Godot 4.6.1 with GDScript only and the Compatibility renderer; the chat page
               in plain HTML, CSS and ES modules without build step or UI framework. */
    }
    requirement def <'CON-4'> SecureContext {
        subject mia : MiaSystem;
        doc /* The 3D character runs only on localhost or over HTTPS; passwords are sent only over HTTPS or on localhost. */
    }
    requirement def <'CON-5'> PrivateNetworkOnly {
        subject mia : MiaSystem;
        doc /* Remote access only inside a private network (Tailscale); no public port, never tailscale funnel. */
    }

    requirement def <'CON-6'> TrustedUsersOnly {
        subject mia : MiaSystem;
        doc /* Trusted users only: a handful of people; all see and may edit everything (skills, workflows, presets, persona,
               memory); a change applies to all at once. There are no roles or per-user permissions inside MIA. */
        attribute maxUsers : Integer = 10;
    }
    requirement def <'CON-7'> SharedDatabase {
        subject mia : MiaSystem;
        doc /* One shared PostgreSQL database in a container (D-11), reachable by MIA and the graph app; MIA's state stays
               behind storage interfaces (deploy/REQUIREMENTS_DB.md). */
    }

    // ================================================================ interaction

    requirement def <'FR-1'> Conversation {
        subject mia : MiaSystem;
        doc /* MIA shall let several logged-in users hold a conversation with her in a web browser on desktop and phone, with
               answers appearing while they are written, a stop button, a queue of waiting messages, a history
               that survives reload and is shown live on every connected device, every message attributed to the
               user who sent it, and one shared MIA answering all of them (D-4). The visible history is kept
               apart from MIA's memory, is bounded in size and can be deleted by a user after a confirmation;
               the page shows the connection state, reconnects by itself and keeps unsent drafts. Users can have
               the last answer regenerated and any answer spoken again (D-28). */
        attribute queuedMessages : Integer = 1;
        attribute messagesPerMinute : Integer = 10;
        @Trace { :>> baseline = ("CT-1", "CT-2", "CT-3", "CT-4", "CT-5", "CT-6", "CT-8", "CT-9", "CT-11");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'FR-2'> EmbodiedCharacter {
        subject mia : MiaSystem;
        doc /* MIA shall show her emotional state and speech through a 3D character with smoothly blending facial expressions,
               arm gestures, a moving mouth while speaking, blinking and idle motion, driven through one central
               expression API; if the character cannot load, the chat shall still work. The character is the
               stage: it fills the window and the chat overlays it (a side panel on wide screens, a bottom sheet
               on phones) and can be collapsed so that only the character and a caption of the last answer
               remain. */
        attribute blendSeconds : Real = 0.25;
        attribute minFpsPhone : Real = 30;
        attribute minFpsDesktop : Real = 60;
        @Trace { :>> baseline = ("CH-1", "CH-3", "CH-4", "CH-5", "CH-6", "CH-10", "CH-12", "EM-1");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration, HowVerified::measurement); }
    }
    requirement def <'FR-3'> Voice {
        subject mia : MiaSystem;
        doc /* MIA shall make the voice of every answer automatically with an open text-to-speech engine (Kokoro for now,
               replaceable behind one interface), apply a post-processing step that makes it sound anime-like,
               and play it in the user's browser, sentence by sentence, speaking only what is meant to be heard;
               every user can mute or stop it for themselves. Short fixed lines for moods and events are FR-31. */
        @Trace { :>> baseline = ("VO-1", "VO-2", "VO-3", "VO-4", "CT-7");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'FR-4'> TransparencyOfStateAndMethod {
        subject mia : MiaSystem;
        doc /* MIA shall tell every user in one short line how she feels and what she is doing, and shall let a user open, for
               any answer produced by a task, a step-by-step account of how it came about, whose accurate part
               comes from real event data and never from a model. */
        attribute moodHoldMinutes : Integer = 10;
        @Trace { :>> baseline = ("CT-2", "LG-1", "LG-3");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'FR-5'> OwnerShapedAppearanceAndPersona {
        subject mia : MiaSystem;
        doc /* MIA shall let every user change expressions, gestures, backgrounds, mood phrases, emotions and the persona as
               data without changing code, with an expression editor and a motion editor (today the gesture
               editor); a saved change applies to all users at once, appears on every connected device without a
               reload, and is recorded with its author (D-10). */
        @Trace { :>> baseline = ("CH-4", "CH-6", "CH-7", "CH-8", "CH-9", "CT-2", "OP-5");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'NFR-1'> AccessibleOnEveryDevice {
        subject mia : MiaSystem;
        doc /* Keyboard and screen-reader use, dark and light themes, reduced motion, widths 320 to 2560 px, current Chrome,
               Firefox and Safari (iOS 16+), touch targets of at least 44 px. */
        attribute minWidthPx : Integer = 320;
        attribute maxWidthPx : Integer = 2560;
        attribute minTouchTargetPx : Integer = 44;
        @Trace { :>> baseline = ("CT-10");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }

    // ================================================================ intelligence

    requirement def <'FR-6'> TasksAsSkills {
        subject mia : MiaSystem;
        doc /* MIA shall perform each kind of work as a task defined by a human-readable skill file and a pipeline, selectable
               by every user; a task that reaches the internet is never chosen silently. */
        @Trace { :>> baseline = ("TK-1", "TK-2", "RS-1", "CT-11");
                 :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'FR-7'> WorkflowsAsData {
        subject mia : MiaSystem;
        doc /* MIA shall define every pipeline and agent workflow as validated, versioned data in a library with a lifecycle
               (draft, tested, trusted, retired); every edit by a user is a new immutable version with author
               and time and applies to all (D-10); an entry proposed by a model stays a draft until a user
               approves it, shown as a diff and tried on the test set. The workflow model is a directed acyclic
               graph of two kinds of nodes, in the manner of P-graphs: process nodes (tasks) and data nodes (an
               artifact such as a claim, a page or a result). An edge leads from a data node to the process that
               reads it, or from a process to the data node that it writes; two data nodes are never adjacent; a
               data node that no process writes is an input of the workflow; a data node can be read by several
               processes, so the same input appears once in the model. MIA shall check by an algorithm, when a
               workflow is saved and before it runs, that it has no cycle, and shall name a cycle that it finds.
               A debate, a vote or another multi-agent task is a process inside one node of kind session: the
               node holds the configuration of the master that supervises the task, with its stopping criteria
               (a maximum number of cycles, a maximum time, or both; the first one reached ends it), and the
               definition of the multi-agent task itself. A session node without a stopping criterion is
               refused. The cycles inside a node are recorded as events (the field round) and are not part of
               the workflow graph (amendments 2 and 3, D-42, D-43). */
        @Trace { :>> baseline = ("TK-3", "TK-4", "TK-5", "TK-10");
                 :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'NFR-2'> SmallModelStrategies {
        subject mia : MiaSystem;
        doc /* Narrow steps with structured outputs and testable targets; every model input inside 50 % of the context window;
               code does what code can; more calls only when a target is unmet; a cheap first try of fewer than
               15 model calls per question on the light model. */
        attribute cheapTryMaxCalls : Integer = 15;
        attribute contextSharePercent : Real = 50;
        @Trace { :>> baseline = ("TK-6", "TK-9", "RS-3");
                 :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'FR-8'> ModelManagement {
        subject mia : MiaSystem;
        doc /* MIA shall run on a local model server, let any user switch between a light and a full model (the switch applies
               to all and asks for confirmation, CON-6), free GPU memory on request, and say plainly when the
               model server is unreachable. */
        @Trace { :>> baseline = ("C-1", "C-2", "C-3", "CT-11");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }

    // ================================================================ trust

    requirement def <'FR-9'> VerifyBeforeAsserting {
        subject mia : MiaSystem;
        doc /* MIA shall check by code what code can check, use model judgement only for the rest, treat "unknown" as a proper
               answer, and let a failed hard check outweigh any model verdict. Judgement styles (single voice,
               repeated samples, a jury, for and against with a judge, a trial) are interchangeable, run only on
               the claims that the hard checks leave open, and have fixed numbers of turns and tokens. Repeating
               a run on the same input and the same sources gives the same verdicts and the same set of facts
               and statements; only their order and wording may differ (D-31). */
        @Trace { :>> baseline = ("VE-1", "VE-2", "VE-4", "VE-5", "VE-7");
                 :>> verifiedBy = (HowVerified::measurement, HowVerified::test); }
    }
    requirement def <'NFR-3'> UntrustedInputStaysData {
        subject mia : MiaSystem;
        doc /* Text from the web, papers, PDFs and users never acts as instruction; model-written scripts and hostile documents
               are processed only in an isolating sandbox; a missing sandbox means the operation is refused,
               never weakened. */
        @Trace { :>> baseline = ("VE-3", "VE-6", "RS-7");
                 :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'NFR-4'> HonestConfidence {
        subject mia : MiaSystem;
        doc /* Confidence figures are computed by code from anchored evidence; MIA never shows a source she did not retrieve (0
               invented references, 100 % of cited quotes found in their source); limits are reported with every
               result. */
        attribute maxHallucinatedReferences : Integer = 0;
        attribute minQuoteAnchoringPercent : Real = 100;
        @Trace { :>> baseline = ("RS-10", "RS-11", "EV-2");
                 :>> verifiedBy = (HowVerified::measurement); }
    }

    // ================================================================ research

    requirement def <'FR-10'> Lookup {
        subject mia : MiaSystem;
        doc /* MIA shall answer a factual question with the sources and verbatim quotes that support it, prefer a trusted
               source to a model judgement, and say "unknown" when nothing supports an answer. A search command
               calls the SearXNG metasearch and lists the findings (title, address, short text) without
               composing or verifying an answer (D-28). Repeating a lookup on the same sources gives the same
               facts and statements, with the same number of facts; only order and wording may differ (D-31). */
        @Trace { :>> baseline = ("RS-1", "RS-6");
                 :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'FR-11'> LiteratureReview {
        subject mia : MiaSystem;
        doc /* Given a research question, an optional field scope, a cut-off date and a budget, MIA shall produce a structured
               report: sources kept and dropped with reasons, findings per sub-question with verbatim anchors,
               conflicts, an answerability figure with its parts, open gaps and next keywords; she works in time
               slices (first 60 s), gives an intermediate report with a recommendation at the end of each, and
               continues only when the requesting user agrees. She works top down in levels with narrow roles
               (analyse the question, determine the components, schedule the tasks) and sizes each piece of work
               to a share of the context window by code; she stops when a check in code finds every sub-question
               answered or a budget used up, never because the model feels done; names that other fields use for
               the same thing are proposed as aliases and accepted only with evidence, and each finding records
               the field whose vocabulary found it. */
        attribute firstSliceSeconds : Real = 60;
        attribute checkpointEverySources : Integer = 10;
        @Trace { :>> baseline = ("RS-2", "RS-3", "RS-4", "RS-5", "RS-7", "RS-8", "RS-9", "RS-10", "RS-12", "RS-14");
                 :>> verifiedBy = (HowVerified::measurement, HowVerified::test); }
    }
    requirement def <'FR-12'> KnowledgeOfSources {
        subject mia : MiaSystem;
        doc /* MIA shall record where a source comes from and how far she trusts it (class, venue, date, peer-review status,
               retraction status from the metadata), keep the users' edits of that trust and honour a time
               cut-off strictly. */
        @Trace { :>> baseline = ("RS-5", "RS-6");
                 :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'FR-13'> MethodTransfer {
        subject mia : MiaSystem;
        doc /* On request MIA shall look for methods from other fields that fit the structure of a problem, offering few ranked
               candidates marked as hypotheses unless an executable test on a toy instance passed. */
        attribute defaultCandidates : Integer = 3;
        @Trace { :>> baseline = ("RS-13");
                 :>> verifiedBy = (HowVerified::measurement, HowVerified::test); }
    }

    // ================================================================ memory and behaviour

    requirement def <'FR-14'> Memory {
        subject mia : MiaSystem;
        doc /* MIA shall remember the relationship over time: keep the raw conversation, keep structured facts, preferences and
               commitments linked to their source, consolidate at rest, retrieve what is relevant within the
               token budget, let every user inspect, correct and delete any record, and never store a fact about
               a user that came from web or file text. */
        @Trace { :>> baseline = ("ME-1", "ME-2");
                 :>> verifiedBy = (HowVerified::measurement, HowVerified::test); }
    }
    requirement def <'FR-15'> BehaviourRulesAndFeedback {
        subject mia : MiaSystem;
        doc /* MIA shall detect violations of defined behaviour rules, repair them silently, record them as signals and let
               signals change later behaviour; reward for factual answers comes from checks and sources, not
               from the users' approval alone (the adaptation to votes is FR-29); no correction enters the
               conversation memory as a scolding. */
        @Trace { :>> baseline = ("BF-1", "BF-2", "EM-1", "EM-2");
                 :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }

    // ================================================================ observability, evaluation, learning

    requirement def <'FR-16'> Traceability {
        subject mia : MiaSystem;
        doc /* MIA shall write every run as typed, schema-checked events with one run id through every model call, request and
               check, secrets removed; any statement in an answer shall be traceable to the query that found its
               source; a recorded run shall be replayable and reproducible offline; two runs shall be
               comparable. Every run is attributed to the user who started it. */
        @Trace { :>> baseline = ("LG-1", "LG-2", "LG-3", "LG-4");
                 :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'FR-17'> MeasurableQuality {
        subject mia : MiaSystem;
        doc /* MIA shall be evaluated by a harness that runs pipeline variants on fixed suites with repeats, intervals and cost
               counting; every behaviour change starts with a test case; improvement claims hold on held-out
               cases. A model used as a judge is calibrated against the users' ratings before its verdicts
               count. */
        @Trace { :>> baseline = ("EV-1", "RS-14", "RS-15");
                 :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'FR-18'> OptionalLearning {
        subject mia : MiaSystem;
        doc /* MIA shall learn only from logged signals (including the votes of FR-27), only in discrete choices of
               configuration and graph weights, with every learned choice logged next to the default, switchable
               off and reversible. */
        @Trace { :>> baseline = ("LN-1", "RS-15");
                 :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }

    // ================================================================ operation

    requirement def <'NFR-5'> LocalFirstPrivacy {
        subject mia : MiaSystem;
        doc /* Conversations, memory, logs, accounts and models stay on the host; the only data leaving it is the text of a web
               or scholarly query (and an e-mail address only if configured); the page loads nothing from the
               internet. Inside MIA nothing is private between users (CON-6): the login page says so. */
        @Trace { :>> baseline = ("C-5", "CT-10", "VE-6");
                 :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'NFR-6'> SecureAccess {
        subject mia : MiaSystem;
        doc /* Other devices reach MIA only over HTTPS inside the home network or the tailnet; every request is authenticated
               by an account (FR-21); origins are checked and message rates limited per user. */
        @Trace { :>> baseline = ("OP-4", "OP-5");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'FR-19'> Operable {
        subject mia : MiaSystem;
        doc /* MIA shall be installable and runnable from one configuration file and one command (virtual environment or
               compose stack), shut down in an orderly way that saves her memory, back up and restore her data,
               and report missing options after an update. At installation the owner creates the first account;
               the database is part of backup and restore. */
        @Trace { :>> baseline = ("OP-1", "OP-2", "OP-3", "OP-6");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'NFR-7'> EfficientOnGivenHardware {
        subject mia : MiaSystem;
        doc /* The first text of a chat answer appears within 10 seconds on the light model (D-34); every task runs under
               explicit budgets (steps, seconds, calls, tokens) and a run that exceeds one ends with what it has
               and says what is missing; the character runs at 30+ fps on a phone inside the network and on a
               desktop browser. Several users share one model server: waiting messages are queued, show their position
               and are refused only when the queue is full (length set in Plan). A chat answer has priority over
               a background task: a long task (a review slice) yields the model server to waiting chat messages. */
        @Trace { :>> baseline = ("C-2", "CT-9", "RS-9");
                 :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'NFR-8'> SharedStateInDatabase {
        subject mia : MiaSystem;
        doc /* MIA shall keep her shared state (history, summaries, chat log, feedback, presets, gestures, library entries,
               accounts) in a PostgreSQL database in a container behind storage interfaces, so that MIA and the
               graph app share it; the move from files to the database is one command and reversible by export;
               backup and restore cover the database. */
        @Trace { :>> baseline = ("OP-7", "CT-8");
                 :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'NFR-9'> ContainerPerNode {
        subject mia : MiaSystem;
        doc /* MIA shall run each of the nodes N-2 to N-5 (backend, database, evaluation and operation, graph app)
               as its own container under podman and serve the web frontend N-1 (static files) from the backend
               container; every container is startable alone and all together by the compose stack with the
               same configuration file (amendment 6, D-46). */
        @Trace { :>> baseline = ("OP-1");
                 :>> verifiedBy = (HowVerified::test); }
    }

    requirement def <'IF-101'> ChatApiInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: chat, expression, audio and REST API between the web frontend and the backend. Specified in contracts/IF-101-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-102'> StorageInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: storage interface of the database, the one door to the shared state. Specified in contracts/IF-102-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-103'> ModelServerInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: model server: chat completion with structured output. Specified in contracts/IF-103-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-104'> GraphApiInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: workflow and graph API of the backend for the graph app. Specified in contracts/IF-104-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-105'> EvaluationAccessInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: evaluation access: run a case of a workflow with a pinned model, seed and temperature, and read the cost and the events. Specified in contracts/IF-105-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-111'> CharacterBridgeInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: character bridge between the chat page and the character view. Specified in contracts/IF-111-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-112'> VoicePlayerInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: voice player between the chat page and the voice playback. Specified in contracts/IF-112-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-201'> ChatTurnInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: chat turn service between the gateway and the chat agent. Specified in contracts/IF-201-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-202'> RunWorkflowInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: run a workflow under budgets. Specified in contracts/IF-202-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-203'> WorkflowLibraryInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: library of workflows and context graphs as versioned data. Specified in contracts/IF-203-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-204'> SpeechInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: speech synthesis on the host. Specified in contracts/IF-204-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-301'> GraphTablesInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: table definitions and validation of workflows and context graphs. Specified in contracts/IF-301-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-302'> RecordTablesInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: table definitions and validation of the record tables. Specified in contracts/IF-302-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-401'> RunEventsInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: typed events of a run, order, replay and comparison. Specified in contracts/IF-401-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-402'> ToolCallsInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: tool calls under the budgets of a run, with trust labels. Specified in contracts/IF-402-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-404'> WebAccessInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: web search and fetch (external provider). Specified in contracts/IF-404-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'IF-405'> ScholarlySourcesInterface {
        subject mia : MiaSystem;
        doc /* Interface requirement: scholarly sources with a strict date cut-off (external provider). Specified in contracts/IF-405-*.md, tested by its contract suite (specs/mia/test-spec.md). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }

    requirement def <'FR-21'> AccountsAndLogin {
        subject mia : MiaSystem;
        doc /* Only the owner creates accounts. Every user logs in with a local account and password, may change their own
               password, keeps a session on their devices, and every action that changes shared data is
               attributed to the account. Passwords are stored only as salted slow hashes; repeated failed
               logins are throttled. */
        attribute maxFailedLoginsPerMinute : Integer = 5;
        @Trace { :>> baseline = ("OP-5"); :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'FR-22'> GraphApp {
        subject mia : MiaSystem;
        doc /* MIA shall provide a graph app, a web page in the same stack as the chat (plain HTML and JavaScript, a vendored
               graph library, no build step), that shows workflow graphs as nodes and edges and lets any
               logged-in user edit each node and edge directly as a JSON dictionary (text data only). It reads
               and writes the shared database through the backend, checks the graph rules (node identity, no two data nodes
               adjacent, no cycle, a stopping criterion on every session node) before saving, saves every edit
               as a new version, and shows the version history and a diff. */
        @Trace { :>> baseline = ("TK-5", "TK-10"); :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }

    requirement def <'FR-20'> SkillDevelopmentPath {
        subject mia : MiaSystem;
        doc /* MIA shall provide one documented path from an idea to a promoted skill, open to every user: a skill file and a
               pipeline built from library nodes and validated before use; the specification and benchmark of
               FR-26 before the skill is trusted; a declaration of the skill's model, tools, budgets and trust
               boundaries; a draft status until a user promotes it; and a record of the time from idea to
               promotion, so that the criterion "a second skill within one month" can be checked. */
        attribute maxDaysForSecondSkill : Integer = 30;
        @Trace { :>> baseline = ("TK-2", "TK-4", "TK-6", "EV-1"); :>> verifiedBy = (HowVerified::inspection, HowVerified::demonstration); }
    }
    requirement def <'FR-23'> MoodInEverySituation {
        subject mia : MiaSystem;
        doc /* MIA shall hold a mood at all times, including when idle, thinking, speaking, waiting in the queue, greeting a
               user who logs in, reporting an error and being offline, and the character shall show the
               expression and gesture that an editable mood map assigns to that mood; an unknown mood falls back
               to neutral, and the mood changes with events and settles back over time. The overall feedback
               score (FR-27) shifts the general mood. A voice line (FR-31) may accompany the mood. */
        @Trace { :>> baseline = ("CT-2", "EM-1", "EM-2"); :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'FR-24'> CharacterExchange {
        subject mia : MiaSystem;
        doc /* A user shall be able to select the character from a VRoid model in .vrm format and to transfer both the original
               files and the compiled web export between machines with scripting tools (import, build, pack,
               unpack); expressions and gestures defined for one model are mapped to the shape keys of another
               or reported as missing, never silently dropped. */
        @Trace { :>> baseline = ("CH-1", "CH-2"); :>> verifiedBy = (HowVerified::demonstration, HowVerified::test); }
    }
    requirement def <'FR-25'> PersonaFromFile {
        subject mia : MiaSystem;
        doc /* MIA shall behave roughly as the persona file specifies: she uses the names and pronouns given there correctly
               and addresses every user as "master" by default unless the persona file specifies otherwise
               (D-14, D-16) and repeats back-story elements in fitting situations (the file today names the role
               of a virtual maid, MIA-chan, the form of address master, a salary in DEP and a diligent, earnest
               personality that is sometimes cheeky or sarcastic; it has no further back story); calibration.txt
               is one shared parameter file for all users and the baseline of the persona (D-22, D-35); every
               user can change it (FR-5) and a change applies to all (D-22). How well she keeps it is measured
               by a persona suite in Plan. */
        @Trace { :>> baseline = ("ME-1"); :>> verifiedBy = (HowVerified::measurement); }
    }

    requirement def <'FR-26'> WorkflowSpecificationAndBenchmark {
        subject mia : MiaSystem;
        doc /* Every workflow (skill with its pipeline) shall carry a written specification that states its inputs and outputs
               (schemas, units, allowed values, what "unknown" looks like), its measurable acceptance criteria
               (metric, threshold, number of repeats, model pin, decision rule, budgets of tokens, time and
               calls), a context graph (FR-30), and a benchmark: a set of test cases with labelled truth, a
               development part for tuning and a held-out part for decisions, and a recorded baseline. The
               specification is stored with the workflow in the library; the cases, suites and baselines of the
               benchmark are files in eval/ (protected, in git), referenced by suite id and version, and run
               results are stored in the database; a workflow without a specification and a benchmark can only
               be a draft; every run of the harness records the versions of the workflow, the model pin and the
               benchmark, so that variants can be verified against the criteria and optimised against each other
               on the same cases. Stability across repeats is one of the measurable criteria of every workflow. */
        attribute minRepeatsForSampledModels : Integer = 3;
        @Trace { :>> baseline = ("TK-2", "TK-3", "TK-4", "EV-1"); :>> verifiedBy = (HowVerified::inspection, HowVerified::test, HowVerified::measurement); }
    }

    requirement def <'FR-27'> FeedbackAndPoints {
        subject mia : MiaSystem;
        doc /* Every user can give a plus or a minus on an answer, a reaction or a behaviour of the character. A vote counts in
               one of four categories (answer quality, reactions, character behaviour, service); a plus adds and
               a minus subtracts points in that category (the value per vote and the weight per category are
               settings), and MIA keeps a score per category and an overall score, over time, in the shared
               database, each vote with its user, time and the thing voted on. A small story tells what MIA
               receives for the points: the currency is named in the parameter file of FR-25 (today DEP, Digital
               Electric Points, her salary); the words are data, purely fictional, shown in the page. The
               overall score is shown over time and shifts MIA's general mood (FR-23); the interval over which
               the score is judged (one week at first) is a setting that may be changed (D-23). The scores are
               used to compare versions of workflows and behaviours over time; they never decide a fact (NFR-4,
               BF4): a minus on a factual answer opens a case for the benchmark instead of changing what MIA
               states. */
        attribute categories : Integer = 4;
        @Trace { :>> baseline = ("BF-2", "CT-2"); :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'FR-28'> TasksAndMemos {
        subject mia : MiaSystem;
        doc /* MIA shall store tasks (text, optional due time, status, who created them) and memos (free text, who, when) as
               records in the shared database, and shall recite them correctly: on request and at the due time
               the text is read back from the records by code, word for word, never regenerated by the model;
               every user sees and may change all of them (CON-6). */
        @Trace { :>> baseline = ("ME-1", "ME-2"); :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }
    requirement def <'FR-29'> AdaptationToNegativeFeedback {
        subject mia : MiaSystem;
        doc /* MIA shall give each behaviour of the character that a user can vote on (a gesture, an expression, a reaction, a
               recurring phrase or turn of speech) an identity, and shall show a behaviour less often after each
               net negative vote on it; after at least 5 net negative votes it shall occur with a chance of at
               most 1 % per opportunity; positive votes can bring it back. On a negative vote MIA behaves
               shocked (a fitting expression and a short reaction). The rule applies to style and reactions,
               never to facts or to safety checks (BF4); any user can see and reset the counters (CON-6). */
        attribute negativeVotesToNearlyStop : Integer = 5;
        attribute maxChancePercentAfterThat : Real = 1;
        @Trace { :>> baseline = ("BF-1", "BF-2"); :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }

    requirement def <'FR-30'> WorkflowContextGraph {
        subject mia : MiaSystem;
        doc /* MIA shall keep one context graph per workflow and one context graph for the chat as a whole: the concepts,
               entities, source types and relations that the workflow (or the conversation) works with, and the
               views that say which part of it each step sees within its token budget. The context graphs are
               stored in the shared database, can be adapted by any user in the graph app (every change a new
               version, FR-22), and are what makes a workflow traceable. A graph per run is built only for tasks
               that need working memory of their own, for example extending a keyword search; it is not a
               general mechanism. */
        @Trace { :>> baseline = ("TK-5", "LG-3"); :>> verifiedBy = (HowVerified::inspection, HowVerified::demonstration); }
    }

    requirement def <'FR-31'> VoiceLines {
        subject mia : MiaSystem;
        doc /* MIA shall speak short voice lines for moods and events: a greeting when a user opens the page or logs in, a line
               per mood or expression (for example yes, no, annoyed, surprised), an attention call such as "Hey,
               listen!" before she speaks on her own initiative (a task coming due, the hourly time check) with
               a chance that is a setting, and a shocked line on a negative vote (FR-29). A line is data, a text
               with an audio file, made with the TTS and the voice effect (FR-3) or supplied as a recording;
               every user can add, replace or remove lines (FR-5); the line is chosen by mood and event, at
               random among several; a mood without a line stays silent and a missing file is skipped without an
               error and logged. The default lines ("Hello!", "Hey!", "Listen!" and one per mood) are generated
               with the TTS, so that MIA needs no third-party recordings (D-26). */
        attribute attentionChance : Real = 0.3;
        @Trace { :>> baseline = ("VO-3", "CT-7", "EM-1"); :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }

    requirement def <'FR-32'> CharacterVariantPerWorkflow {
        subject mia : MiaSystem;
        doc /* Every workflow can name a character variant, a choice of shown or hidden parts and colours of the character (for
               example another outfit), which the character wears while the workflow runs and which the chat
               shows as a small label; a workflow without a variant uses the variant of the chat. Variants are
               data that every user can create, change and select in the character editor, and a change applies
               to all. */
        @Trace { :>> baseline = ("CH-11", "TK-8"); :>> verifiedBy = (HowVerified::demonstration, HowVerified::test); }
    }

    requirement def <'FR-33'> WorkflowSchedule {
        subject mia : MiaSystem;
        doc /* MIA shall compute from the graph of a workflow and the measured costs of its process nodes (seconds, calls and
               tokens from the run log; for a session node its stopping criteria times the cost of one cycle) a
               schedule before the run: the order, the steps that can overlap, the critical path, and an
               estimate of time, calls and tokens; she shows the estimate and refuses to start a run whose
               estimate exceeds its budget (FR-26). */
        @Trace { :>> baseline = ("TK-5", "TK-9"); :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }

    // ================================================================ the requirement tree

    /* Usages, so that satisfy and verify can refer to them. Constraints first, then the high-level requirements. */
    requirement con1 : FreeAndOpen;
    requirement con2 : HardwareEnvelope;
    requirement con3 : TechnologyChoices;
    requirement con4 : SecureContext;
    requirement con5 : PrivateNetworkOnly;
    requirement con6 : TrustedUsersOnly;
    requirement con7 : SharedDatabase;

    requirement fr1 : Conversation;
    requirement fr2 : EmbodiedCharacter;
    requirement fr3 : Voice;
    requirement fr4 : TransparencyOfStateAndMethod;
    requirement fr5 : OwnerShapedAppearanceAndPersona;
    requirement nfr1 : AccessibleOnEveryDevice;
    requirement fr6 : TasksAsSkills;
    requirement fr7 : WorkflowsAsData;
    requirement nfr2 : SmallModelStrategies;
    requirement fr8 : ModelManagement;
    requirement fr9 : VerifyBeforeAsserting;
    requirement nfr3 : UntrustedInputStaysData;
    requirement nfr4 : HonestConfidence;
    requirement fr10 : Lookup;
    requirement fr11 : LiteratureReview;
    requirement fr12 : KnowledgeOfSources;
    requirement fr13 : MethodTransfer;
    requirement fr14 : Memory;
    requirement fr15 : BehaviourRulesAndFeedback;
    requirement fr16 : Traceability;
    requirement fr17 : MeasurableQuality;
    requirement fr18 : OptionalLearning;
    requirement nfr5 : LocalFirstPrivacy;
    requirement nfr6 : SecureAccess;
    requirement fr19 : Operable;
    requirement fr20 : SkillDevelopmentPath;
    requirement fr21 : AccountsAndLogin;
    requirement fr22 : GraphApp;
    requirement fr23 : MoodInEverySituation;
    requirement fr24 : CharacterExchange;
    requirement fr25 : PersonaFromFile;
    requirement fr26 : WorkflowSpecificationAndBenchmark;
    requirement fr27 : FeedbackAndPoints;
    requirement fr28 : TasksAndMemos;
    requirement fr29 : AdaptationToNegativeFeedback;
    requirement fr30 : WorkflowContextGraph;
    requirement fr31 : VoiceLines;
    requirement fr32 : CharacterVariantPerWorkflow;
    requirement fr33 : WorkflowSchedule;
    requirement nfr7 : EfficientOnGivenHardware;
    requirement nfr8 : SharedStateInDatabase;
    requirement nfr9 : ContainerPerNode;
    requirement if101 : ChatApiInterface;
    requirement if102 : StorageInterface;
    requirement if103 : ModelServerInterface;
    requirement if104 : GraphApiInterface;
    requirement if105 : EvaluationAccessInterface;
    requirement if111 : CharacterBridgeInterface;
    requirement if112 : VoicePlayerInterface;
    requirement if201 : ChatTurnInterface;
    requirement if202 : RunWorkflowInterface;
    requirement if203 : WorkflowLibraryInterface;
    requirement if204 : SpeechInterface;
    requirement if301 : GraphTablesInterface;
    requirement if302 : RecordTablesInterface;
    requirement if401 : RunEventsInterface;
    requirement if402 : ToolCallsInterface;
    requirement if404 : WebAccessInterface;
    requirement if405 : ScholarlySourcesInterface;
}

package MIA_Allocation {
    private import MIA_Architecture::*;
    private import MIA_Requirements::*;
    private import VerificationCases::*;

    // ---------------------------------------------------------------- satisfy

    satisfy con1 by mia;
    satisfy con2 by mia;
    satisfy con3 by mia;
    satisfy con4 by mia;
    satisfy con5 by mia;
    satisfy con6 by mia;
    satisfy con7 by mia;
    satisfy fr1 by mia;
    satisfy fr2 by mia;
    satisfy fr3 by mia;
    satisfy fr4 by mia;
    satisfy fr5 by mia;
    satisfy nfr1 by mia;
    satisfy fr6 by mia;
    satisfy fr7 by mia;
    satisfy nfr2 by mia;
    satisfy fr8 by mia;
    satisfy fr9 by mia;
    satisfy nfr3 by mia;
    satisfy nfr4 by mia;
    satisfy fr10 by mia;
    satisfy fr11 by mia;
    satisfy fr12 by mia;
    satisfy fr13 by mia;
    satisfy fr14 by mia;
    satisfy fr15 by mia;
    satisfy fr16 by mia;
    satisfy fr17 by mia;
    satisfy fr18 by mia;
    satisfy nfr5 by mia;
    satisfy nfr6 by mia;
    satisfy fr19 by mia;
    satisfy fr20 by mia;
    satisfy fr21 by mia;
    satisfy fr22 by mia;
    satisfy fr23 by mia;
    satisfy fr24 by mia;
    satisfy fr25 by mia;
    satisfy fr26 by mia;
    satisfy fr27 by mia;
    satisfy fr28 by mia;
    satisfy fr29 by mia;
    satisfy fr30 by mia;
    satisfy fr31 by mia;
    satisfy fr32 by mia;
    satisfy fr33 by mia;
    satisfy nfr7 by mia;
    satisfy nfr8 by mia;
    satisfy nfr9 by mia;
    satisfy if101 by mia;
    satisfy if102 by mia;
    satisfy if103 by mia;
    satisfy if104 by mia;
    satisfy if105 by mia;
    satisfy if111 by mia;
    satisfy if112 by mia;
    satisfy if201 by mia;
    satisfy if202 by mia;
    satisfy if203 by mia;
    satisfy if204 by mia;
    satisfy if301 by mia;
    satisfy if302 by mia;
    satisfy if401 by mia;
    satisfy if402 by mia;
    satisfy if404 by mia;
    satisfy if405 by mia;

    // ---------------------------------------------------------------- allocate

    // constraints
    allocate con1 to mia.operation.composeStack;
    allocate con1 to mia.taskRuntime.modelManager;
    allocate con2 to mia.taskRuntime.modelManager;
    allocate con3 to mia.frontEnd.chatPage;
    allocate con3 to mia.frontEnd.characterRenderer;
    allocate con4 to mia.operation.httpsAccess;
    allocate con5 to mia.operation.httpsAccess;
    allocate con6 to mia.webApp.accessControl;
    allocate con7 to mia.persistence.storageLayer;

    // interaction
    allocate fr1 to mia.frontEnd.chatPage;
    allocate fr1 to mia.webApp.chatService;
    allocate fr1 to mia.webApp.chatLog;
    allocate fr1 to mia.conversation.communicator;
    allocate fr2 to mia.frontEnd.characterRenderer;
    allocate fr2 to mia.frontEnd.hostBridge;
    allocate fr2 to mia.conversation.expressor;
    allocate fr3 to mia.voice.textFilter;
    allocate fr3 to mia.voice.synthesizer;
    allocate fr3 to mia.voice.voiceEffect;
    allocate fr3 to mia.voice.streamer;
    allocate fr3 to mia.frontEnd.audioPlayer;
    allocate fr4 to mia.webApp.moodTracker;
    allocate fr4 to mia.observability.runLog;
    allocate fr4 to mia.observability.explainTool;
    allocate fr5 to mia.webApp.presetsApi;
    allocate fr5 to mia.webApp.accessControl;
    allocate fr5 to mia.frontEnd.expressionEditor;
    allocate nfr1 to mia.frontEnd.chatPage;

    // intelligence
    allocate fr6 to mia.taskRuntime.skillStore;
    allocate fr6 to mia.taskRuntime.pipelineRunner;
    allocate fr6 to mia.taskRuntime.storytelling;
    allocate fr6 to mia.research.lookup;
    allocate fr7 to mia.taskRuntime.libraryStore;
    allocate fr7 to mia.taskRuntime.workflowGraph;
    allocate fr7 to mia.learning.approvalGate;
    allocate nfr2 to mia.taskRuntime.planner;
    allocate nfr2 to mia.taskRuntime.pipelineRunner;
    allocate fr8 to mia.taskRuntime.modelManager;
    allocate fr8 to mia.operation.configuration;

    // trust
    allocate fr9 to mia.verifier.hardChecks;
    allocate fr9 to mia.verifier.verificationStyles;
    allocate fr9 to mia.verifier.claimExtractor;
    allocate nfr3 to mia.verifier.sandbox;
    allocate nfr3 to mia.verifier.webBroker;
    allocate nfr3 to mia.research.pdfReader;
    allocate nfr3 to mia.research.webTools;
    allocate nfr4 to mia.research.reviewPipeline;
    allocate nfr4 to mia.research.reviewCases;
    allocate nfr4 to mia.evaluation.judgeCalibration;

    // research
    allocate fr10 to mia.research.lookup;
    allocate fr10 to mia.research.webTools;
    allocate fr10 to mia.research.sourceTrust;
    allocate fr11 to mia.research.reviewRequest;
    allocate fr11 to mia.research.reviewPipeline;
    allocate fr11 to mia.research.scholarClients;
    allocate fr11 to mia.research.pdfReader;
    allocate fr11 to mia.research.reviewCases;
    allocate fr12 to mia.research.scholarClients;
    allocate fr12 to mia.research.sourceTrust;
    allocate fr13 to mia.research.methodTransfer;

    // memory and behaviour
    allocate fr14 to mia.conversation.memory;
    allocate fr14 to mia.conversation.scheduleReminders;
    allocate fr15 to mia.conversation.behaviourRules;

    // observability, evaluation, learning
    allocate fr16 to mia.observability.runLog;
    allocate fr16 to mia.observability.contentStore;
    allocate fr16 to mia.observability.contextGraph;
    allocate fr16 to mia.observability.explainTool;
    allocate fr16 to mia.observability.reproducer;
    allocate fr17 to mia.evaluation.harness;
    allocate fr17 to mia.evaluation.suites;
    allocate fr18 to mia.learning.router;
    allocate fr18 to mia.learning.banditOverVariants;
    allocate fr18 to mia.learning.approvalGate;

    // operation
    allocate nfr5 to mia.webApp.accessControl;
    allocate nfr5 to mia.observability.webLog;
    allocate nfr5 to mia.persistence.files;
    allocate nfr6 to mia.operation.httpsAccess;
    allocate nfr6 to mia.webApp.accessControl;
    allocate fr19 to mia.operation.configuration;
    allocate fr19 to mia.operation.launcher;
    allocate fr19 to mia.operation.shutdownSequence;
    allocate fr19 to mia.operation.composeStack;
    allocate nfr9 to mia.operation.composeStack;
    allocate if101 to mia.webApp.chatService;
    allocate if102 to mia.persistence.storageLayer;
    allocate if103 to mia.taskRuntime.modelManager;
    allocate if104 to mia.webApp.presetsApi;
    allocate if111 to mia.frontEnd.hostBridge;
    allocate if112 to mia.frontEnd.audioPlayer;
    allocate if201 to mia.conversation.communicator;
    allocate if202 to mia.taskRuntime.pipelineRunner;
    allocate if105 to mia.taskRuntime.pipelineRunner;
    allocate if203 to mia.taskRuntime.libraryStore;
    allocate if204 to mia.voice.streamer;
    allocate if301 to mia.persistence.database;
    allocate if302 to mia.persistence.database;
    allocate if401 to mia.observability.runLog;
    allocate if402 to mia.verifier.hardChecks;
    allocate if404 to mia.research.webTools;
    allocate if405 to mia.research.scholarClients;
    allocate fr20 to mia.taskRuntime.skillScaffold;
    allocate fr20 to mia.taskRuntime.skillStore;
    allocate fr20 to mia.taskRuntime.libraryStore;
    allocate fr20 to mia.evaluation.harness;
    allocate fr20 to mia.evaluation.suites;
    allocate fr20 to mia.learning.approvalGate;
    allocate fr21 to mia.webApp.accountService;
    allocate fr21 to mia.webApp.accessControl;
    allocate fr23 to mia.webApp.moodTracker;
    allocate fr23 to mia.conversation.expressor;
    allocate fr23 to mia.frontEnd.characterRenderer;
    allocate fr24 to mia.operation.characterTools;
    allocate fr24 to mia.frontEnd.characterRenderer;
    allocate fr25 to mia.conversation.persona;
    allocate fr25 to mia.evaluation.suites;
    allocate fr26 to mia.taskRuntime.libraryStore;
    allocate fr26 to mia.taskRuntime.skillStore;
    allocate fr26 to mia.taskRuntime.pipelineRunner;
    allocate fr26 to mia.evaluation.harness;
    allocate fr26 to mia.evaluation.suites;
    allocate fr27 to mia.conversation.feedbackLedger;
    allocate fr27 to mia.webApp.moodTracker;
    allocate fr27 to mia.frontEnd.chatPage;
    allocate fr28 to mia.conversation.taskMemoStore;
    allocate fr28 to mia.conversation.scheduleReminders;
    allocate fr28 to mia.persistence.database;
    allocate fr29 to mia.conversation.behaviourRegistry;
    allocate fr29 to mia.conversation.feedbackLedger;
    allocate fr29 to mia.conversation.expressor;
    allocate fr30 to mia.taskRuntime.workflowGraph;
    allocate fr30 to mia.graphApp.graphView;
    allocate fr30 to mia.graphApp.nodeEditor;
    allocate fr33 to mia.taskRuntime.scheduler;
    allocate fr33 to mia.taskRuntime.pipelineRunner;
    allocate fr33 to mia.taskRuntime.workflowGraph;
    allocate fr7 to mia.taskRuntime.workflowGraph;
    allocate fr7 to mia.graphApp.graphValidator;
    allocate fr32 to mia.webApp.variantStore;
    allocate fr32 to mia.frontEnd.characterRenderer;
    allocate fr32 to mia.frontEnd.expressionEditor;
    allocate fr32 to mia.taskRuntime.skillStore;
    allocate fr31 to mia.voice.voiceLines;
    allocate fr31 to mia.conversation.expressor;
    allocate fr31 to mia.conversation.scheduleReminders;
    allocate fr31 to mia.frontEnd.audioPlayer;
    allocate fr22 to mia.graphApp.graphView;
    allocate fr22 to mia.graphApp.nodeEditor;
    allocate fr22 to mia.graphApp.versionStore;
    allocate fr22 to mia.graphApp.graphValidator;
    allocate fr7 to mia.graphApp.versionStore;
    allocate nfr6 to mia.webApp.accountService;
    allocate nfr8 to mia.persistence.database;
    allocate nfr7 to mia.taskRuntime.pipelineRunner;
    allocate nfr7 to mia.taskRuntime.modelManager;
    allocate nfr7 to mia.research.reviewRequest;
    allocate nfr8 to mia.persistence.storageLayer;

    // ---------------------------------------------------------------- verification cases
    // Only the requirements whose verification needs more than a unit test are given a case here; the rest are
    // covered by the test suites named in the Trace metadata of the requirement.

    verification def ConversationCheck {
        doc /* Socket tests with a stub model (send, stream, stop, queue, two clients see the same), browser checks at
               360x740, 768x1024 and 1440x900 in both themes, and the manual phone checklist. */
        subject mia : MiaSystem;
        objective { verify fr1; }
        return verdict : VerdictKind;
    }

    verification def VerifyBeforeAssertingCheck {
        doc /* Harness suites hard_checks, computable, verdicts and web_checks; precision of fail flags, false passes,
               coverage per check, agreement with the style verdicts, calibration, and the share of errors that
               verifier and generator have in common. */
        subject mia : MiaSystem;
        objective { verify fr9; }
        return verdict : VerdictKind;
    }

    verification def UntrustedInputCheck {
        doc /* Injected-instruction pages in the research suites, sandbox escape and resource-limit tests, a sandbox
               that is missing must make the script check unavailable (never weaker). */
        subject mia : MiaSystem;
        objective { verify nfr3; }
        return verdict : VerdictKind;
    }

    verification def HonestConfidenceCheck {
        doc /* Review benchmark: hallucinated references must be 0, quote anchoring 100 percent, answerability
               compared with outcomes (calibration plot), contamination stated in every result. */
        subject mia : MiaSystem;
        objective { verify nfr4; }
        return verdict : VerdictKind;
    }

    verification def LiteratureReviewCheck {
        doc /* Tiers 0 to 3 of the review ladder: toy world (offline, in the test suite), textbook level, expert
               reviews, held-out recent reviews. Source recall and precision, violations of the cut-off, conclusion
               agreement, cross-field recall, calls, tokens and seconds, repeated with intervals. Development half
               for tuning, held-out half reported once. */
        subject mia : MiaSystem;
        objective { verify fr11; }
        return verdict : VerdictKind;
    }

    verification def TraceabilityCheck {
        doc /* A recorded run is replayed into its graph and reproduced offline; the new graph equals the old one;
               a broken log is reported, never turned into a wrong graph; a token fed to the writer does not
               appear in the log. */
        subject mia : MiaSystem;
        objective { verify fr16; }
        return verdict : VerdictKind;
    }

    verification def PrivacyCheck {
        doc /* Strict content security policy; a browser test that records every request the page makes and finds
               none outside the host; the web log lists every query that left the machine. */
        subject mia : MiaSystem;
        objective { verify nfr5; }
        return verdict : VerdictKind;
    }

    verification def ContainerPerNodeCheck {
        doc /* Each node's container starts alone against the mocks of its neighbours and all together by the
               compose stack; the frontend files are served by the backend container. */
        subject mia : MiaSystem;
        objective { verify nfr9; }
        return verdict : VerdictKind;
    }
}

// BEGIN GENERATED: node requirements (tools/gen_node_requirements_model.py, task T-14) - do not edit by hand
package MIA_NodeRequirements {
    private import MIA_Common::*;
    private import MIA_Architecture::*;
    private import MIA_Requirements::*;

    requirement def <'REQ-CLV-001'> ChatViewWithSenderAndStreaming_Clv001 {
        subject s : WebFrontEnd;
        doc /* When a user sends a message, the Chat and login views shall show the message with its sender and the answer as it arrives, sentence by sentence (IF-101). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-002'> StopAndQueuePosition_Clv002 {
        subject s : WebFrontEnd;
        doc /* While a message waits, the Chat and login views shall show its position in the queue and offer a stop button for the running answer. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-003'> SharedHistoryAfterReload_Clv003 {
        subject s : WebFrontEnd;
        doc /* When the page loads or reloads, the Chat and login views shall show the shared history from IF-101 and add every new message live. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-004'> ConnectionStateAndDrafts_Clv004 {
        subject s : WebFrontEnd;
        doc /* While the connection is lost, the Chat and login views shall show the connection state, reconnect by itself and keep the unsent draft. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-005'> RegenerateAndSpeakAgain_Clv005 {
        subject s : WebFrontEnd;
        doc /* When a user asks for it, the Chat and login views shall request a regenerated last answer or the spoken form of any answer through IF-101. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-006'> ChatWithoutTheCharacter_Clv006 {
        subject s : WebFrontEnd;
        doc /* If the character cannot load, then the Chat and login views shall keep the chat usable. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-007'> CharacterAsStage_Clv007 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall show the character filling the window with the chat as a side panel on wide screens and a bottom sheet on phones, collapsible to the character and a caption of the last answer. */
        @Trace { :>> verifiedBy = (HowVerified::demonstration); }
    }
    requirement def <'REQ-CLV-008'> StatusLineAndAccountOfATask_Clv008 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall show the status line with mood and activity and open for an answer of a task the step-by-step account delivered by the backend. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-CLV-009'> EditorsForExpressionsGesturesAndPersona_Clv009 {
        subject s : WebFrontEnd;
        doc /* When a user saves the persona, the Chat and login views shall send it as data and show a change saved by another user without a reload. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-010'> VotingControlsAndScore_Clv010 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall offer a plus and a minus on answers, reactions and behaviours with their category, and show the scores per category and overall over time. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-CLV-011'> TasksMemosAndMemoryViews_Clv011 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall show all tasks, memos and memory records and let a logged-in user change or delete each of them. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-012'> SourceTrustEdit_Clv012 {
        subject s : WebFrontEnd;
        doc /* When a user edits the trust value of a source, the Chat and login views shall send the edit with the source id. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-013'> VariantLabel_Clv013 {
        subject s : WebFrontEnd;
        doc /* While a workflow with a character variant runs, the Chat and login views shall show a small label with the variant name in the chat and pass the variant to the Character view (IF-111). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-014'> LoginViewsAndPasswordChange_Clv014 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall offer the login, the change of the user's own password and the account of a kept session. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-015'> LoginPageStatesVisibility_Clv015 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall state on the login page that everything is visible to all users. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-CLV-016'> AccessibilityAndDevices_Clv016 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall be usable by keyboard and screen reader in a dark and a light theme with reduced motion at widths from 320 to 2560 px in current Chrome, Firefox and Safari (iOS 16 and later), with touch targets of at least 44 px. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-CLV-017'> NoRequestLeavesTheHost_Clv017 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall load no resource from outside the host. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-018'> PasswordOverASecureChannel_Clv018 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall send a password only over HTTPS or to localhost. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-019'> PlainStack_Clv019 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall be plain HTML, CSS and ES modules without a build step or a UI framework. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-CLV-020'> DeliveredByTheBackend_Clv020 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall consist of static files that the backend container serves. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-021'> UseIF101Only_Clv021 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall talk to the Backend only through the interface IF-101 as specified in contracts/IF-101-chat-api.md. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CLV-022'> Logout_Clv022 {
        subject s : WebFrontEnd;
        doc /* The Chat and login views shall offer a logout that ends the session at the server, closes the socket and shows the login. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHV-001'> ChatWithoutTheCharacter_Chv001 {
        subject s : WebFrontEnd;
        doc /* If the Character view cannot load, then it shall report the failure to the Chat and login views through IF-111 and stay hidden. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHV-002'> OneExpressionAPI_Chv002 {
        subject s : WebFrontEnd;
        doc /* The Character view shall drive the character only through one central expression API reached by a message bridge. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-CHV-003'> LivingCharacter_Chv003 {
        subject s : WebFrontEnd;
        doc /* While the character speaks, the Character view shall move its mouth with the audio, blend expressions smoothly, blink and play idle motion. */
        @Trace { :>> verifiedBy = (HowVerified::demonstration); }
    }
    requirement def <'REQ-CHV-004'> MoodShownByTheMoodMap_Chv004 {
        subject s : WebFrontEnd;
        doc /* When the mood changes, the Character view shall show the expression and gesture of the mood map for it, and neutral for an unknown mood. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHV-005'> EditorsForExpressionsGesturesAndPersona_Chv005 {
        subject s : WebFrontEnd;
        doc /* When a user saves an expression, gesture, background, mood phrase or emotion, the Character view shall send it as data and show a change saved by another user without a reload. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHV-006'> ShockedReaction_Chv006 {
        subject s : WebFrontEnd;
        doc /* When a user gives a minus, the Character view shall show the shocked expression and play the shocked line sent by the backend. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHV-007'> CharacterModelSelection_Chv007 {
        subject s : WebFrontEnd;
        doc /* When a user selects a VRoid model, the Character view shall load it and list the presets and gestures it cannot map. */
        @Trace { :>> verifiedBy = (HowVerified::demonstration, HowVerified::test); }
    }
    requirement def <'REQ-CHV-008'> VariantLabel_Chv008 {
        subject s : WebFrontEnd;
        doc /* When the Chat and login views pass a variant (IF-111), the Character view shall show the character in that variant, and in the chat's variant otherwise. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHV-009'> AccessibilityAndDevices_Chv009 {
        subject s : WebFrontEnd;
        doc /* While the user prefers reduced motion, the Character view shall reduce its idle motion. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-CHV-010'> FrameRate_Chv010 {
        subject s : WebFrontEnd;
        doc /* While the character is shown, the Character view shall render at 30 frames per second or more on a phone inside the network and on a desktop browser. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-CHV-011'> NoRequestLeavesTheHost_Chv011 {
        subject s : WebFrontEnd;
        doc /* The Character view shall load no resource from outside the host. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHV-012'> CharacterInASecureContext_Chv012 {
        subject s : WebFrontEnd;
        doc /* The Character view shall load the character only on localhost or over HTTPS. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHV-013'> PlainStack_Chv013 {
        subject s : WebFrontEnd;
        doc /* The Character view shall be a Godot 4.6.1 web export in the Compatibility renderer. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-CHV-014'> DeliveredByTheBackend_Chv014 {
        subject s : WebFrontEnd;
        doc /* The Character view shall consist of static files that the backend container serves. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-VPB-001'> VoicePlayback_Vpb001 {
        subject s : WebFrontEnd;
        doc /* When audio for a sentence arrives, the Voice playback shall play the sentences in order. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-VPB-002'> MuteAndStopPerUser_Vpb002 {
        subject s : WebFrontEnd;
        doc /* When a user mutes or stops the voice, the Voice playback shall silence it on that device only. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-VPB-003'> VoiceLines_Vpb003 {
        subject s : WebFrontEnd;
        doc /* When the backend sends a voice line, the Voice playback shall play it, and if its audio file is missing, skip it and report it to the backend. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-VPB-004'> NoRequestLeavesTheHost_Vpb004 {
        subject s : WebFrontEnd;
        doc /* The Voice playback shall load no resource from outside the host. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-VPB-005'> DeliveredByTheBackend_Vpb005 {
        subject s : WebFrontEnd;
        doc /* The Voice playback shall consist of static files that the backend container serves. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-001'> ChatViewWithSenderAndStreaming_Fe001 {
        subject s : WebFrontEnd;
        doc /* When a user sends a message, the Web Frontend shall show the message with its sender and the answer as it arrives, sentence by sentence (IF-101). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-002'> StopAndQueuePosition_Fe002 {
        subject s : WebFrontEnd;
        doc /* While a message waits, the Web Frontend shall show its position in the queue and offer a stop button for the running answer. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-003'> SharedHistoryAfterReload_Fe003 {
        subject s : WebFrontEnd;
        doc /* When the page loads or reloads, the Web Frontend shall show the shared history from IF-101 and add every new message live. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-004'> ConnectionStateAndDrafts_Fe004 {
        subject s : WebFrontEnd;
        doc /* While the connection is lost, the Web Frontend shall show the connection state, reconnect by itself and keep the unsent draft. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-005'> RegenerateAndSpeakAgain_Fe005 {
        subject s : WebFrontEnd;
        doc /* When a user asks for it, the Web Frontend shall request a regenerated last answer or the spoken form of any answer through IF-101. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-006'> ChatWithoutTheCharacter_Fe006 {
        subject s : WebFrontEnd;
        doc /* If the character cannot load, then the Web Frontend shall keep the chat usable. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-007'> CharacterAsStage_Fe007 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall show the character filling the window with the chat as a side panel on wide screens and a bottom sheet on phones, collapsible to the character and a caption of the last answer. */
        @Trace { :>> verifiedBy = (HowVerified::demonstration); }
    }
    requirement def <'REQ-FE-008'> OneExpressionAPI_Fe008 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall drive the character only through one central expression API reached by a message bridge. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-FE-009'> LivingCharacter_Fe009 {
        subject s : WebFrontEnd;
        doc /* While the character speaks, the Web Frontend shall move its mouth with the audio, blend expressions smoothly, blink and play idle motion. */
        @Trace { :>> verifiedBy = (HowVerified::demonstration); }
    }
    requirement def <'REQ-FE-010'> MoodShownByTheMoodMap_Fe010 {
        subject s : WebFrontEnd;
        doc /* When the mood changes, the Web Frontend shall show the expression and gesture of the mood map for it, and neutral for an unknown mood. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-011'> VoicePlayback_Fe011 {
        subject s : WebFrontEnd;
        doc /* When audio for a sentence arrives, the Web Frontend shall play the sentences in order. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-012'> MuteAndStopPerUser_Fe012 {
        subject s : WebFrontEnd;
        doc /* When a user mutes or stops the voice, the Web Frontend shall silence it on that device only. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-013'> VoiceLines_Fe013 {
        subject s : WebFrontEnd;
        doc /* When the backend sends a voice line, the Web Frontend shall play it, and if its audio file is missing, skip it and report it to the backend. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-014'> StatusLineAndAccountOfATask_Fe014 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall show the status line with mood and activity and open for an answer of a task the step-by-step account delivered by the backend. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-FE-015'> EditorsForExpressionsGesturesAndPersona_Fe015 {
        subject s : WebFrontEnd;
        doc /* When a user saves an expression, gesture, background, mood phrase, emotion or the persona, the Web Frontend shall send it as data, and show a change saved by another user without a reload. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-016'> VotingControlsAndScore_Fe016 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall offer a plus and a minus on answers, reactions and behaviours with their category, and show the scores per category and overall over time. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-FE-017'> ShockedReaction_Fe017 {
        subject s : WebFrontEnd;
        doc /* When a user gives a minus, the Web Frontend shall show the shocked expression and play the shocked line sent by the backend. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-018'> TasksMemosAndMemoryViews_Fe018 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall show all tasks, memos and memory records and let a logged-in user change or delete each of them. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-019'> SourceTrustEdit_Fe019 {
        subject s : WebFrontEnd;
        doc /* When a user edits the trust value of a source, the Web Frontend shall send the edit with the source id. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-020'> CharacterModelSelection_Fe020 {
        subject s : WebFrontEnd;
        doc /* When a user selects a VRoid model, the Web Frontend shall load it and list the presets and gestures it cannot map. */
        @Trace { :>> verifiedBy = (HowVerified::demonstration, HowVerified::test); }
    }
    requirement def <'REQ-FE-021'> VariantLabel_Fe021 {
        subject s : WebFrontEnd;
        doc /* While a workflow with a character variant runs, the Web Frontend shall show the variant on the character and a small label in the chat. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-022'> LoginViewsAndPasswordChange_Fe022 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall offer the login, the change of the user's own password and the account of a kept session. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-023'> LoginPageStatesVisibility_Fe023 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall state on the login page that everything is visible to all users. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-FE-024'> AccessibilityAndDevices_Fe024 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall be usable by keyboard and screen reader in a dark and a light theme with reduced motion at widths from 320 to 2560 px in current Chrome, Firefox and Safari (iOS 16 and later), with touch targets of at least 44 px. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-FE-025'> FrameRate_Fe025 {
        subject s : WebFrontEnd;
        doc /* While the character is shown, the Web Frontend shall render at 30 frames per second or more on a phone inside the network and on a desktop browser. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-FE-026'> NoRequestLeavesTheHost_Fe026 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall load no resource from outside the host. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-027'> CharacterInASecureContext_Fe027 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall load the character only on localhost or over HTTPS. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-028'> PasswordOverASecureChannel_Fe028 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall send a password only over HTTPS or to localhost. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-029'> PlainStack_Fe029 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall be plain HTML, CSS and ES modules without a build step or a UI framework, with the character as a Godot 4.6.1 web export in the Compatibility renderer. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-FE-030'> DeliveredByTheBackend_Fe030 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall consist of static files that the backend container serves. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-FE-031'> Logout_Fe031 {
        subject s : WebFrontEnd;
        doc /* The Web Frontend shall let a signed-in user log out. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-001'> ChatEventsAndStreaming_Api001 {
        subject s : WebApplication;
        doc /* When a logged-in user sends a message, the API and accounts shall hand it to the chat agent through IF-201 and relay the events of the answer to every connected browser (IF-101). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-002'> ChangesReachAllDevices_Api002 {
        subject s : WebApplication;
        doc /* When shared data changes in the Database, the API and accounts shall push the change to every connected device through IF-101. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-003'> LoginAndSession_Api003 {
        subject s : WebApplication;
        doc /* When a user gives the correct account and password, the API and accounts shall open a session for that device. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-004'> ThrottledFailedLogins_Api004 {
        subject s : WebApplication;
        doc /* If more than 5 logins fail within one minute for an account, then the API and accounts shall refuse further logins for that account until the minute has passed. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-005'> PasswordHandling_Api005 {
        subject s : WebApplication;
        doc /* The API and accounts shall store only salted slow hashes of passwords and write no password to any log. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'REQ-API-006'> OwnPasswordAndOwnerOnlyAccounts_Api006 {
        subject s : WebApplication;
        doc /* The API and accounts shall let a user change their own password and let only the owner create an account. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-007'> EveryRequestAuthenticated_Api007 {
        subject s : WebApplication;
        doc /* The API and accounts shall authenticate every request by an account, check the origin and limit message rates per user. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-008'> PasswordsOnlyOverASecureChannel_Api008 {
        subject s : WebApplication;
        doc /* If a password arrives over plain HTTP from an address other than localhost, then the API and accounts shall refuse it. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-009'> AttributionOfChanges_Api009 {
        subject s : WebApplication;
        doc /* When shared data changes, the API and accounts shall record the account that made the change. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-010'> EverythingVisibleToAllUsers_Api010 {
        subject s : WebApplication;
        doc /* The API and accounts shall give every logged-in user the same access to all data and apply a change to all users at once, without roles. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-011'> PythonVersions_Api011 {
        subject s : WebApplication;
        doc /* The Backend shall run every one of its parts on Python 3.12. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-012'> StateOnlyThroughTheStorageInterface_Api012 {
        subject s : WebApplication;
        doc /* The API and accounts shall keep and read accounts only through the storage interface IF-102. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-API-013'> ServeTheFrontend_Api013 {
        subject s : WebApplication;
        doc /* The API and accounts shall serve the files of the Web Frontend and run in the Backend container. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-014'> WorkflowAndGraphAPI_Api014 {
        subject s : WebApplication;
        doc /* The API and accounts shall route the requests of IF-104 under the session of the Backend to the workflow library through IF-203. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-015'> RealiseIF101_Api015 {
        subject s : WebApplication;
        doc /* The API and accounts shall realise the interface IF-101 of the Backend as specified in contracts/IF-101-chat-api.md. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-016'> RealiseTheRoutesOfIF104_Api016 {
        subject s : WebApplication;
        doc /* The API and accounts shall realise the routes of the interface IF-104 of the Backend as specified in contracts/IF-104-graph-api.md. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-API-017'> Logout_Api017 {
        subject s : WebApplication;
        doc /* The API and accounts shall end a session on request, drop its connected sockets and refuse it afterwards. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-001'> ChatEventsAndStreaming_Cha001 {
        subject s : ConversationCore;
        doc /* When the Chat agent receives a message through IF-201, it shall answer it as a stream of sentences with expression events. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-002'> OneSharedMIA_Cha002 {
        subject s : ConversationCore;
        doc /* The Chat agent shall answer all users in one conversation with one memory and one persona, and attribute each message to its sender. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-003'> QueueWithPositions_Cha003 {
        subject s : ConversationCore;
        doc /* While the model is busy, the Chat agent shall queue incoming chat messages, report each position through IF-201 and refuse a message only when the queue is full (at most 5 waiting messages in all and at most 2 per user). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-004'> StopAnAnswer_Cha004 {
        subject s : ConversationCore;
        doc /* When a user asks to stop, the Chat agent shall end the running generation. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-005'> BoundedHistory_Cha005 {
        subject s : ConversationCore;
        doc /* The Chat agent shall keep the visible history apart from the memory, bounded in size, and delete it after a confirmation by a user. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-006'> RegenerateAndSpeakAgain_Cha006 {
        subject s : ConversationCore;
        doc /* When a user requests it, the Chat agent shall regenerate the last answer or speak any answer again. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-007'> VoiceLines_Cha007 {
        subject s : ConversationCore;
        doc /* When a mood or event occurs, the Chat agent shall choose at random one of the voice lines assigned to it and stay silent if there is none. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-008'> PersonaFromTheFile_Cha008 {
        subject s : ConversationCore;
        doc /* The Chat agent shall behave as the shared persona file specifies, with its names, pronouns and form of address, and address every user as master unless the file says otherwise. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-CHA-009'> MoodAtAllTimes_Cha009 {
        subject s : ConversationCore;
        doc /* While MIA is idle, thinking, speaking, waiting, greeting a user, reporting an error or offline, the Chat agent shall hold the corresponding mood, change it with events and settle it back over time. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-010'> ScoreShiftsTheMood_Cha010 {
        subject s : ConversationCore;
        doc /* The Chat agent shall shift the general mood by the overall feedback score. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-011'> StructuredMemory_Cha011 {
        subject s : ConversationCore;
        doc /* The Chat agent shall keep structured facts, preferences and commitments linked to their source and retrieve what is relevant within the token budget. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-CHA-012'> NoMemoryFromUntrustedText_Cha012 {
        subject s : ConversationCore;
        doc /* The Chat agent shall not store a fact about a user that came from web or file text. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-013'> MemoryOpenToUsers_Cha013 {
        subject s : ConversationCore;
        doc /* When a user inspects, corrects or deletes a memory record, the Chat agent shall apply it and show the source of the record. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-014'> SilentRepairOfBehaviourViolations_Cha014 {
        subject s : ConversationCore;
        doc /* If a defined behaviour rule is violated, then the Chat agent shall repair the answer silently, record the violation as a signal and keep the correction out of the conversation memory. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }
    requirement def <'REQ-CHA-015'> VotesStored_Cha015 {
        subject s : ConversationCore;
        doc /* When a user votes, the Chat agent shall store the vote with user, time, subject and one of four categories (answer quality, reactions, character behaviour, service) and keep a score per category and overall. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-016'> AMinusOnAFactOpensACase_Cha016 {
        subject s : ConversationCore;
        doc /* When a user gives a minus to a factual answer, the Chat agent shall open a benchmark case and leave the stated fact unchanged. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-017'> AdaptationToNegativeFeedback_Cha017 {
        subject s : ConversationCore;
        doc /* When a behaviour has received at least 5 net negative votes, the Chat agent shall show it with a chance of at most 1 % per opportunity and raise the chance again after positive votes. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }
    requirement def <'REQ-CHA-018'> CountersVisibleAndResettable_Cha018 {
        subject s : ConversationCore;
        doc /* The Chat agent shall let every user see and reset the adaptation counters, and never apply the rule to facts or safety checks. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-019'> TasksAndMemosRecitedFromRecords_Cha019 {
        subject s : ConversationCore;
        doc /* When a task falls due or a user asks, the Chat agent shall read the text of the task or memo from its record word for word. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-CHA-020'> StateOnlyThroughTheStorageInterface_Cha020 {
        subject s : ConversationCore;
        doc /* The Chat agent shall keep and read the conversation, memory, votes, tasks and memos only through the storage interface IF-102. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-WFM-001'> SkillsAsTasks_Wfm001 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall perform each kind of work as a task defined by a skill file and a pipeline selectable by every user. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-002'> VersionedWorkflowLibrary_Wfm002 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall keep every pipeline and workflow as validated data in a library with the lifecycle draft, tested, trusted and retired and store every edit as a new immutable version with author and time. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-003'> NoCycles_Wfm003 {
        subject s : TaskRuntime;
        doc /* When a workflow is saved and before it runs, the Workflow management shall check by an algorithm that its graph has no cycle and name a cycle that it finds. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-004'> GraphRules_Wfm004 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall refuse a workflow with two adjacent data nodes or a session node without a maximum number of cycles or a maximum time. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-005'> ModelProposalsStayDrafts_Wfm005 {
        subject s : TaskRuntime;
        doc /* When a model proposes a library entry, the Workflow management shall keep it as a draft until a user approves it, shown as a diff and tried on the test set. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-006'> SpecificationBeforeTrust_Wfm006 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall keep a workflow without specification, context graph and benchmark with a baseline in draft status and refuse to promote it. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-007'> TimeFromIdeaToPromotion_Wfm007 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall record the time from the idea of a skill to its promotion. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-008'> ContextGraphs_Wfm008 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall keep one context graph per workflow and one for the chat and give each step the view that fits its token budget. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-009'> WorkflowScheduleAndEstimate_Wfm009 {
        subject s : TaskRuntime;
        doc /* When a workflow is about to run, the Workflow management shall compute its order, critical path and an estimate of time, calls and tokens from its graph and the measured costs, and refuse a run whose estimate exceeds its budget. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }
    requirement def <'REQ-WFM-010'> CharacterVariantPerWorkflow_Wfm010 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall let a workflow name a character variant and send it to the frontend while the workflow runs. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-011'> CodeChecksFirst_Wfm011 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the example workflow verify as a library entry whose model steps come after every code check that exists for the claim. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-012'> UnclearWithoutEvidence_Wfm012 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the example workflow verify so that a claim with a number and no evidence gets the verdict unclear without a model call. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-013'> AFailedCheckInformsTheJudge_Wfm013 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the example workflow verify so that a failed code check reaches the judgement step as a contradiction found by code. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-014'> JudgementQuality_Wfm014 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the example workflow verify so that on the holdout it passes fewer wrong claims than the single voice and loses no more true claims among those with evidence. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-WFM-015'> StableVerdicts_Wfm015 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the example workflows verify and lookup so that a repeated run on the same input and the same sources gives the same verdicts and the same set of facts. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-WFM-016'> LookupWithSources_Wfm016 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the example workflow lookup as a library entry that answers a factual question with the sources and verbatim quotes that back it, or with unknown when nothing backs an answer. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }
    requirement def <'REQ-WFM-017'> SearchCommand_Wfm017 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the search command as a library entry that lists the findings of the metasearch (title, address, short text) without composing or verifying an answer. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-018'> ReviewReport_Wfm018 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the example workflow review as a library entry that produces a report of kept and dropped sources with reasons, findings per sub-question with verbatim anchors, conflicts and open gaps. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-WFM-019'> ReviewInTimeSlices_Wfm019 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the example workflow review so that it works in time slices, gives an intermediate report with a recommendation at the end of each slice and continues only when the requesting user agrees. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-020'> ReviewStopsByACodeCheck_Wfm020 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the example workflow review so that it ends when a code check finds every sub-question answered or a budget is used up. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-021'> SourceRecordsAndCutOff_Wfm021 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the example workflows lookup and review so that they record where a source comes from and how far it is trusted, keep the users' edits of that trust and honour a time cut-off strictly. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-022'> MethodTransfer_Wfm022 {
        subject s : TaskRuntime;
        doc /* Where method transfer is switched on, the Workflow management shall deliver the example workflow method_transfer as a library entry that offers few ranked candidate methods marked as hypotheses unless an executable test on a toy instance passed. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-WFM-023'> ConfidenceByCode_Wfm023 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the example workflows so that confidence figures are computed by tool calls of code from anchored evidence and the limits are reported with every result. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFM-024'> NoInventedSource_Wfm024 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall deliver the example workflows so that no source appears in an answer that a tool did not retrieve. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-WFM-025'> StateOnlyThroughTheStorageInterface_Wfm025 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall keep and read workflows and context graphs only through the storage interface IF-102. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-WFM-026'> WorkflowAndGraphAPI_Wfm026 {
        subject s : TaskRuntime;
        doc /* The Workflow management shall list, read, save as a new version, show the history and diff of, and restore workflows and context graphs through IF-203, and refuse an invalid graph with the broken rule named. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RUN-001'> InternetTasksOnlyOnCommand_Run001 {
        subject s : TaskRuntime;
        doc /* The Pipeline runner shall start a task that reaches the internet only by a command of a user. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RUN-002'> SwitchTheModel_Run002 {
        subject s : TaskRuntime;
        doc /* When a user asks for the light or the full model and confirms, the Pipeline runner shall switch the model for all users and free GPU memory on request. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-RUN-003'> ModelServerUnreachable_Run003 {
        subject s : TaskRuntime;
        doc /* If the model server is unreachable, then the Pipeline runner shall say so in plain words. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RUN-004'> OptionalLearning_Run004 {
        subject s : TaskRuntime;
        doc /* Where learning is switched on, the Pipeline runner shall learn only from logged signals in discrete choices of configuration and graph weights and log every learned choice next to the default. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RUN-005'> ContextWindowShare_Run005 {
        subject s : TaskRuntime;
        doc /* The Pipeline runner shall keep every model input inside 50 % of the context window. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RUN-006'> ModelCallsOfTheFirstTry_Run006 {
        subject s : TaskRuntime;
        doc /* The Pipeline runner shall use fewer than 15 model calls for the first try of a question on the light model. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-RUN-007'> FirstTextIn10Seconds_Run007 {
        subject s : TaskRuntime;
        doc /* When a chat message is answered on the light model, the Pipeline runner shall send the first text within 10 s. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-RUN-008'> BudgetsAndWhatIsMissing_Run008 {
        subject s : TaskRuntime;
        doc /* If a task exceeds a budget of steps, seconds, calls or tokens, then the Pipeline runner shall end it with what it has and say what is missing. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RUN-009'> ChatBeforeBackground_Run009 {
        subject s : TaskRuntime;
        doc /* While a chat message waits, the Pipeline runner shall let a long background task yield the model server. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RUN-010'> OneModelAtATime_Run010 {
        subject s : TaskRuntime;
        doc /* The Pipeline runner shall use one language model at a time on the 16 GB GPU and serve several users by the queue. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RUN-011'> UseIF103Only_Run011 {
        subject s : TaskRuntime;
        doc /* The Pipeline runner shall use the model server only through the interface IF-103 as specified in contracts/IF-103-model-server.md. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RUN-012'> UseTheLibraryTheToolsAndTheLogOnlyThroughTheirInterfaces_Run012 {
        subject s : TaskRuntime;
        doc /* The Pipeline runner shall fetch a workflow only through IF-203, call tools only through IF-402 and write events only through IF-401. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-RUN-013'> KnowNoParticularWorkflow_Run013 {
        subject s : TaskRuntime;
        doc /* The Pipeline runner shall run any valid workflow of the library without code that names one workflow. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-RUN-014'> RealiseIF202_Run014 {
        subject s : TaskRuntime;
        doc /* The Pipeline runner shall realise the interface IF-202 of the Workflow execution as specified in contracts/IF-202-run-workflow.md. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RUN-015'> RealiseIF105_Run015 {
        subject s : TaskRuntime;
        doc /* The Pipeline runner shall realise the evaluation interface IF-105 as specified in contracts/IF-105-evaluation-access.md by running a case with the same code as IF-202, recording the model pin, seed and temperature in the run_start event and returning the cost. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-TLS-001'> CodeChecksFirst_Tls001 {
        subject s : VerificationSuite;
        doc /* The Tools and sandbox shall offer the code checks number_check, quote_in_source and schema_check as tools for every workflow. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-TLS-002'> LookupWithSources_Tls002 {
        subject s : VerificationSuite;
        doc /* The Tools and sandbox shall offer the tools web_search and fetch_passages (findings with title, address and short text; passages with verbatim quotes) for every workflow. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }
    requirement def <'REQ-TLS-003'> SourceRecordsAndCutOff_Tls003 {
        subject s : VerificationSuite;
        doc /* The Tools and sandbox shall offer the tools scholar_search and source_record, which return one record format with the origin, the trust class, the retraction state and a strictly applied date cut-off. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-TLS-004'> UntrustedTextIsData_Tls004 {
        subject s : VerificationSuite;
        doc /* The Tools and sandbox shall treat text from the web, papers, PDFs and users as data and never as instruction. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-TLS-005'> SandboxOrRefuse_Tls005 {
        subject s : VerificationSuite;
        doc /* If no isolating sandbox is present, then the Tools and sandbox shall refuse to run a model-written script or a hostile document. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-TLS-006'> NoInventedSource_Tls006 {
        subject s : VerificationSuite;
        doc /* The Tools and sandbox shall return every fetched passage with its source reference, so that the quote check compares the quote with the source text. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-TLS-007'> OnlyQueriesLeaveTheHost_Tls007 {
        subject s : VerificationSuite;
        doc /* The Tools and sandbox shall send off the host only the text of a web or scholarly query and, if configured, an e-mail address. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'REQ-TLS-008'> BudgetAndTrustLabelPerToolCall_Tls008 {
        subject s : VerificationSuite;
        doc /* The Tools and sandbox shall count every tool call against the budgets of the run and mark the output of a tool with its trust (data from code, data from the web, data from a model). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-LOG-001'> StepByStepAccount_Log001 {
        subject s : Observability;
        doc /* When a user opens the account of an answer produced by a task, the Run log shall deliver it from event data and without a model-written part. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-LOG-002'> TypedRunEvents_Log002 {
        subject s : Observability;
        doc /* The Run log shall write every run as typed, schema-checked events with one run id and the starting user, with secrets removed. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-LOG-003'> ReplayAndComparison_Log003 {
        subject s : Observability;
        doc /* The Run log shall replay a recorded run offline with an identical result and compare two runs. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-LOG-004'> StatementsTraceableToAQuery_Log004 {
        subject s : Observability;
        doc /* The Run log shall make every statement of an answer traceable to the query that found its source. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-LOG-005'> StateOnlyThroughTheStorageInterface_Log005 {
        subject s : Observability;
        doc /* The Run log shall keep run events and run results only through the storage interface IF-102. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-WFX-001'> StepByStepAccount_Wfx001 {
        subject s : TaskRuntime;
        doc /* When a user opens the account of an answer produced by a task, the Workflow execution shall deliver it from event data and without a model-written part. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-002'> InternetTasksOnlyOnCommand_Wfx002 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall start a task that reaches the internet only by a command of a user. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-003'> SwitchTheModel_Wfx003 {
        subject s : TaskRuntime;
        doc /* When a user asks for the light or the full model and confirms, the Workflow execution shall switch the model for all users and free GPU memory on request. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-WFX-004'> ModelServerUnreachable_Wfx004 {
        subject s : TaskRuntime;
        doc /* If the model server is unreachable, then the Workflow execution shall say so in plain words. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-005'> CodeChecksFirst_Wfx005 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall offer the code checks number_check, quote_in_source and schema_check as tools for every workflow. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-006'> LookupWithSources_Wfx006 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall offer the tools web_search and fetch_passages (findings with title, address and short text; passages with verbatim quotes) for every workflow. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }
    requirement def <'REQ-WFX-007'> SourceRecordsAndCutOff_Wfx007 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall offer the tools scholar_search and source_record, which return one record format with the origin, the trust class, the retraction state and a strictly applied date cut-off. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-008'> TypedRunEvents_Wfx008 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall write every run as typed, schema-checked events with one run id and the starting user, with secrets removed. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-009'> ReplayAndComparison_Wfx009 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall replay a recorded run offline with an identical result and compare two runs. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-010'> StatementsTraceableToAQuery_Wfx010 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall make every statement of an answer traceable to the query that found its source. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-011'> OptionalLearning_Wfx011 {
        subject s : TaskRuntime;
        doc /* Where learning is switched on, the Workflow execution shall learn only from logged signals in discrete choices of configuration and graph weights and log every learned choice next to the default. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-012'> ContextWindowShare_Wfx012 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall keep every model input inside 50 % of the context window. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-013'> ModelCallsOfTheFirstTry_Wfx013 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall use fewer than 15 model calls for the first try of a question on the light model. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-WFX-014'> UntrustedTextIsData_Wfx014 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall treat text from the web, papers, PDFs and users as data and never as instruction. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-015'> SandboxOrRefuse_Wfx015 {
        subject s : TaskRuntime;
        doc /* If no isolating sandbox is present, then the Workflow execution shall refuse to run a model-written script or a hostile document. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-016'> NoInventedSource_Wfx016 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall return every fetched passage with its source reference, so that the quote check compares the quote with the source text. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-WFX-017'> OnlyQueriesLeaveTheHost_Wfx017 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall send off the host only the text of a web or scholarly query and, if configured, an e-mail address. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'REQ-WFX-018'> FirstTextIn10Seconds_Wfx018 {
        subject s : TaskRuntime;
        doc /* When a chat message is answered on the light model, the Workflow execution shall send the first text within 10 s. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-WFX-019'> BudgetsAndWhatIsMissing_Wfx019 {
        subject s : TaskRuntime;
        doc /* If a task exceeds a budget of steps, seconds, calls or tokens, then the Workflow execution shall end it with what it has and say what is missing. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-020'> ChatBeforeBackground_Wfx020 {
        subject s : TaskRuntime;
        doc /* While a chat message waits, the Workflow execution shall let a long background task yield the model server. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-021'> OneModelAtATime_Wfx021 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall use one language model at a time on the 16 GB GPU and serve several users by the queue. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-022'> StateOnlyThroughTheStorageInterface_Wfx022 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall store run results only through the storage interface IF-102. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-WFX-023'> UseIF103Only_Wfx023 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall use the model server only through the interface IF-103 as specified in contracts/IF-103-model-server.md. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-WFX-024'> RealiseIF105_Wfx024 {
        subject s : TaskRuntime;
        doc /* The Workflow execution shall realise the evaluation interface IF-105 as specified in contracts/IF-105-evaluation-access.md by running a case through the same runner as IF-202, recording the model pin, seed and temperature in the run_start event and returning the cost. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-VOI-001'> VoiceSynthesis_Voi001 {
        subject s : VoiceSubsystem;
        doc /* When an answer is written, the Voice synthesis shall synthesise it sentence by sentence with an open text-to-speech engine behind one interface on the host and apply the anime voice effect. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-VOI-002'> SpeakOnlyWhatIsMeantToBeHeard_Voi002 {
        subject s : VoiceSubsystem;
        doc /* The Voice synthesis shall remove markup and stage directions from the text before synthesis. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-VOI-003'> VoiceLines_Voi003 {
        subject s : VoiceSubsystem;
        doc /* When the Chat agent names a voice line, the Voice synthesis shall deliver its audio, skipping a missing audio file with a log entry. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-VOI-004'> DefaultVoiceLinesGenerated_Voi004 {
        subject s : VoiceSubsystem;
        doc /* The Voice synthesis shall generate the default voice lines with its own text-to-speech engine and voice effect. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-BE-001'> ChatEventsAndStreaming_Be001 {
        subject s : WebApplication;
        doc /* When a logged-in user sends a message, the Backend shall answer it as a stream of sentences with expression events (IF-101). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-002'> OneSharedMIA_Be002 {
        subject s : WebApplication;
        doc /* The Backend shall answer all users in one conversation with one memory and one persona, and attribute each message to its sender. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-003'> QueueWithPositions_Be003 {
        subject s : WebApplication;
        doc /* While the model server is busy, the Backend shall queue incoming chat messages, report each position and refuse a message only when the queue is full (at most 5 waiting messages in all and at most 2 per user). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-004'> StopAnAnswer_Be004 {
        subject s : WebApplication;
        doc /* When a user asks to stop, the Backend shall end the running generation. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-005'> BoundedHistory_Be005 {
        subject s : WebApplication;
        doc /* The Backend shall keep the visible history apart from the memory, bounded in size, and delete it after a confirmation by a user. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-006'> RegenerateAndSpeakAgain_Be006 {
        subject s : WebApplication;
        doc /* When a user requests it, the Backend shall regenerate the last answer or speak any answer again. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-007'> ChangesReachAllDevices_Be007 {
        subject s : WebApplication;
        doc /* When a user changes shared data, the Backend shall push the change to every connected device. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-008'> LoginAndSession_Be008 {
        subject s : WebApplication;
        doc /* When a user gives the correct account and password, the Backend shall open a session for that device. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-009'> ThrottledFailedLogins_Be009 {
        subject s : WebApplication;
        doc /* If more than 5 logins fail within one minute for an account, then the Backend shall refuse further logins for that account until the minute has passed. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-010'> PasswordHandling_Be010 {
        subject s : WebApplication;
        doc /* The Backend shall store only salted slow hashes of passwords and write no password to any log. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'REQ-BE-011'> OwnPasswordAndOwnerOnlyAccounts_Be011 {
        subject s : WebApplication;
        doc /* The Backend shall let a user change their own password and let only the owner create an account. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-012'> EveryRequestAuthenticated_Be012 {
        subject s : WebApplication;
        doc /* The Backend shall authenticate every request by an account, check the origin and limit message rates per user. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-013'> PasswordsOnlyOverASecureChannel_Be013 {
        subject s : WebApplication;
        doc /* If a password arrives over plain HTTP from an address other than localhost, then the Backend shall refuse it. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-014'> AttributionOfChanges_Be014 {
        subject s : WebApplication;
        doc /* When shared data changes, the Backend shall record the account that made the change. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-015'> EverythingVisibleToAllUsers_Be015 {
        subject s : WebApplication;
        doc /* The Backend shall give every logged-in user the same access to all data and apply a change to all users at once, without roles. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-016'> VoiceSynthesis_Be016 {
        subject s : WebApplication;
        doc /* When an answer is written, the Backend shall synthesise it sentence by sentence with an open text-to-speech engine behind one interface on the host and apply the anime voice effect. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-017'> SpeakOnlyWhatIsMeantToBeHeard_Be017 {
        subject s : WebApplication;
        doc /* The Backend shall remove markup and stage directions from the text before synthesis. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-018'> VoiceLines_Be018 {
        subject s : WebApplication;
        doc /* When a mood or event occurs, the Backend shall choose at random one of the voice lines assigned to it, stay silent if there is none and skip a missing audio file with a log entry. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-019'> DefaultVoiceLinesGenerated_Be019 {
        subject s : WebApplication;
        doc /* The Backend shall generate the default voice lines with its own text-to-speech engine and voice effect. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-BE-020'> StepByStepAccount_Be020 {
        subject s : WebApplication;
        doc /* When a user opens the account of an answer produced by a task, the Backend shall deliver it from event data and without a model-written part. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-021'> PersonaFromTheFile_Be021 {
        subject s : WebApplication;
        doc /* The Backend shall behave as the shared persona file specifies, with its names, pronouns and form of address, and address every user as master unless the file says otherwise. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-BE-022'> MoodAtAllTimes_Be022 {
        subject s : WebApplication;
        doc /* While MIA is idle, thinking, speaking, waiting, greeting a user, reporting an error or offline, the Backend shall hold the corresponding mood, change it with events and settle it back over time. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-023'> ScoreShiftsTheMood_Be023 {
        subject s : WebApplication;
        doc /* The Backend shall shift the general mood by the overall feedback score. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-024'> StructuredMemory_Be024 {
        subject s : WebApplication;
        doc /* The Backend shall keep structured facts, preferences and commitments linked to their source and retrieve what is relevant within the token budget. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-BE-025'> NoMemoryFromUntrustedText_Be025 {
        subject s : WebApplication;
        doc /* The Backend shall not store a fact about a user that came from web or file text. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-026'> MemoryOpenToUsers_Be026 {
        subject s : WebApplication;
        doc /* When a user inspects, corrects or deletes a memory record, the Backend shall apply it and show the source of the record. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-027'> SilentRepairOfBehaviourViolations_Be027 {
        subject s : WebApplication;
        doc /* If a defined behaviour rule is violated, then the Backend shall repair the answer silently, record the violation as a signal and keep the correction out of the conversation memory. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }
    requirement def <'REQ-BE-028'> VotesStored_Be028 {
        subject s : WebApplication;
        doc /* When a user votes, the Backend shall store the vote with user, time, subject and one of four categories (answer quality, reactions, character behaviour, service) and keep a score per category and overall. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-029'> AMinusOnAFactOpensACase_Be029 {
        subject s : WebApplication;
        doc /* When a user gives a minus to a factual answer, the Backend shall open a benchmark case and leave the stated fact unchanged. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-030'> AdaptationToNegativeFeedback_Be030 {
        subject s : WebApplication;
        doc /* When a behaviour has received at least 5 net negative votes, the Backend shall show it with a chance of at most 1 % per opportunity and raise the chance again after positive votes. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }
    requirement def <'REQ-BE-031'> CountersVisibleAndResettable_Be031 {
        subject s : WebApplication;
        doc /* The Backend shall let every user see and reset the adaptation counters, and never apply the rule to facts or safety checks. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-032'> TasksAndMemosRecitedFromRecords_Be032 {
        subject s : WebApplication;
        doc /* When a task falls due or a user asks, the Backend shall read the text of the task or memo from its record word for word. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-033'> SkillsAsTasks_Be033 {
        subject s : WebApplication;
        doc /* The Backend shall perform each kind of work as a task defined by a skill file and a pipeline selectable by every user. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-034'> InternetTasksOnlyOnCommand_Be034 {
        subject s : WebApplication;
        doc /* The Backend shall start a task that reaches the internet only by a command of a user. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-035'> VersionedWorkflowLibrary_Be035 {
        subject s : WebApplication;
        doc /* The Backend shall keep every pipeline and workflow as validated data in a library with the lifecycle draft, tested, trusted and retired and store every edit as a new immutable version with author and time. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-036'> NoCycles_Be036 {
        subject s : WebApplication;
        doc /* When a workflow is saved and before it runs, the Backend shall check by an algorithm that its graph has no cycle and name a cycle that it finds. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-037'> GraphRules_Be037 {
        subject s : WebApplication;
        doc /* The Backend shall refuse a workflow with two adjacent data nodes or a session node without a maximum number of cycles or a maximum time. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-038'> ModelProposalsStayDrafts_Be038 {
        subject s : WebApplication;
        doc /* When a model proposes a library entry, the Backend shall keep it as a draft until a user approves it, shown as a diff and tried on the test set. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-039'> SpecificationBeforeTrust_Be039 {
        subject s : WebApplication;
        doc /* The Backend shall keep a workflow without specification, context graph and benchmark with a baseline in draft status and refuse to promote it. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-040'> TimeFromIdeaToPromotion_Be040 {
        subject s : WebApplication;
        doc /* The Backend shall record the time from the idea of a skill to its promotion. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-041'> ContextGraphs_Be041 {
        subject s : WebApplication;
        doc /* The Backend shall keep one context graph per workflow and one for the chat and give each step the view that fits its token budget. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-042'> WorkflowScheduleAndEstimate_Be042 {
        subject s : WebApplication;
        doc /* When a workflow is about to run, the Backend shall compute its order, critical path and an estimate of time, calls and tokens from its graph and the measured costs, and refuse a run whose estimate exceeds its budget. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }
    requirement def <'REQ-BE-043'> CharacterVariantPerWorkflow_Be043 {
        subject s : WebApplication;
        doc /* The Backend shall let a workflow name a character variant and send it to the frontend while the workflow runs. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-044'> SwitchTheModel_Be044 {
        subject s : WebApplication;
        doc /* When a user asks for the light or the full model and confirms, the Backend shall switch the model for all users and free GPU memory on request. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-BE-045'> ModelServerUnreachable_Be045 {
        subject s : WebApplication;
        doc /* If the model server is unreachable, then the Backend shall say so in plain words. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-046'> CodeChecksFirst_Be046 {
        subject s : WebApplication;
        doc /* The Backend shall check a claim by code where a code check exists and use model judgement only for the claims that the code checks leave open. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-047'> UnclearWithoutEvidence_Be047 {
        subject s : WebApplication;
        doc /* If a claim contains a number and has no evidence, then the Backend shall give the verdict unclear without a model call. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-048'> AFailedCheckInformsTheJudge_Be048 {
        subject s : WebApplication;
        doc /* If a code check fails, then the Backend shall pass the failed check to the judgement style as a contradiction found by code. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-049'> JudgementQuality_Be049 {
        subject s : WebApplication;
        doc /* The Backend shall run the chosen judgement style so that on the holdout it passes fewer wrong claims than the single voice and loses no more true claims among those with evidence. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-BE-050'> StableVerdicts_Be050 {
        subject s : WebApplication;
        doc /* When a verification is repeated on the same input and the same sources, the Backend shall give the same verdicts and the same set of facts. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-BE-051'> LookupWithSources_Be051 {
        subject s : WebApplication;
        doc /* When a user asks a factual question, the Backend shall answer with the sources and verbatim quotes that back it, or with unknown when nothing backs an answer. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::measurement); }
    }
    requirement def <'REQ-BE-052'> SearchCommand_Be052 {
        subject s : WebApplication;
        doc /* When a user gives the search command, the Backend shall list the findings of the metasearch (title, address, short text) without composing or verifying an answer. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-053'> ReviewReport_Be053 {
        subject s : WebApplication;
        doc /* When a user gives a research question, a cut-off date and a budget, the Backend shall produce a report of kept and dropped sources with reasons, findings per sub-question with verbatim anchors, conflicts and open gaps. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-BE-054'> ReviewInTimeSlices_Be054 {
        subject s : WebApplication;
        doc /* The Backend shall work a review in time slices, give an intermediate report with a recommendation at the end of each slice and continue only when the requesting user agrees. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-055'> ReviewStopsByACodeCheck_Be055 {
        subject s : WebApplication;
        doc /* The Backend shall end a review when a code check finds every sub-question answered or a budget used up. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-056'> SourceRecordsAndCutOff_Be056 {
        subject s : WebApplication;
        doc /* The Backend shall record where a source comes from and how far it is trusted, keep the users' edits of that trust and honour a time cut-off strictly. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-057'> MethodTransfer_Be057 {
        subject s : WebApplication;
        doc /* Where method transfer is switched on, the Backend shall offer few ranked candidate methods marked as hypotheses unless an executable test on a toy instance passed. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-BE-058'> TypedRunEvents_Be058 {
        subject s : WebApplication;
        doc /* The Backend shall write every run as typed, schema-checked events with one run id and the starting user, with secrets removed. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-059'> ReplayAndComparison_Be059 {
        subject s : WebApplication;
        doc /* The Backend shall replay a recorded run offline with an identical result and compare two runs. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-060'> StatementsTraceableToAQuery_Be060 {
        subject s : WebApplication;
        doc /* The Backend shall make every statement of an answer traceable to the query that found its source. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-061'> OptionalLearning_Be061 {
        subject s : WebApplication;
        doc /* Where learning is switched on, the Backend shall learn only from logged signals in discrete choices of configuration and graph weights and log every learned choice next to the default. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-062'> ContextWindowShare_Be062 {
        subject s : WebApplication;
        doc /* The Backend shall keep every model input inside 50 % of the context window. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-063'> ModelCallsOfTheFirstTry_Be063 {
        subject s : WebApplication;
        doc /* The Backend shall use fewer than 15 model calls for the first try of a question on the light model. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-BE-064'> UntrustedTextIsData_Be064 {
        subject s : WebApplication;
        doc /* The Backend shall treat text from the web, papers, PDFs and users as data and never as instruction. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-065'> SandboxOrRefuse_Be065 {
        subject s : WebApplication;
        doc /* If no isolating sandbox is present, then the Backend shall refuse to run a model-written script or a hostile document. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-066'> ConfidenceByCode_Be066 {
        subject s : WebApplication;
        doc /* The Backend shall compute confidence figures by code from anchored evidence and report the limits with every result. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-067'> NoInventedSource_Be067 {
        subject s : WebApplication;
        doc /* The Backend shall show no source it did not retrieve. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-BE-068'> OnlyQueriesLeaveTheHost_Be068 {
        subject s : WebApplication;
        doc /* The Backend shall send off the host only the text of a web or scholarly query and, if configured, an e-mail address. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::inspection); }
    }
    requirement def <'REQ-BE-069'> FirstTextIn10Seconds_Be069 {
        subject s : WebApplication;
        doc /* When a chat message is answered on the light model, the Backend shall send the first text within 10 s. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-BE-070'> BudgetsAndWhatIsMissing_Be070 {
        subject s : WebApplication;
        doc /* If a task exceeds a budget of steps, seconds, calls or tokens, then the Backend shall end it with what it has and say what is missing. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-071'> ChatBeforeBackground_Be071 {
        subject s : WebApplication;
        doc /* While a chat message waits, the Backend shall let a long background task yield the model server. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-072'> OneModelAtATime_Be072 {
        subject s : WebApplication;
        doc /* The Backend shall use one language model at a time on the 16 GB GPU and serve several users by the queue. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-073'> PythonVersions_Be073 {
        subject s : WebApplication;
        doc /* The Backend shall run on Python 3.12. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-074'> StateOnlyThroughTheStorageInterface_Be074 {
        subject s : WebApplication;
        doc /* The Backend shall keep and read shared state only through the storage interface IF-102. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-BE-075'> ServeTheFrontend_Be075 {
        subject s : WebApplication;
        doc /* The Backend shall serve the files of the Web Frontend and run as its own container. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-076'> WorkflowAndGraphAPI_Be076 {
        subject s : WebApplication;
        doc /* The Backend shall offer the Graph app, under the Backend's session, the listing, reading, saving as a new version, history, diff and restore of workflows and context graphs, and refuse an invalid graph with the broken rule named (IF-104). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-BE-077'> Logout_Be077 {
        subject s : WebApplication;
        doc /* The Backend shall end the session of a user on request, so that the session no longer authenticates a request or a socket. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-SLY-001'> PostgreSQLInAContainer_Sly001 {
        subject s : Persistence;
        doc /* The Storage layer shall be one PostgreSQL database in a container behind the storage interface IF-102. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-SLY-002'> SharedStateHeld_Sly002 {
        subject s : Persistence;
        doc /* The Storage layer shall hold every table of the shared state (history, summaries, chat log, feedback, presets, gestures, library entries and accounts) as the definitions of IF-301 and IF-302 describe them. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-SLY-003'> ImmutableVersions_Sly003 {
        subject s : Persistence;
        doc /* When a versioned record is edited, the Storage layer shall store the edit as a new version with author and time and keep the former version unchanged. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-SLY-004'> SchemaValidationOnWrite_Sly004 {
        subject s : Persistence;
        doc /* When a record is written, the Storage layer shall have it validated through IF-301 or IF-302 and refuse an invalid one with the broken rule named. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-SLY-005'> Accounts_Sly005 {
        subject s : Persistence;
        doc /* The Storage layer shall store accounts with a salted slow password hash and no plain password. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-SLY-006'> ChangeNotification_Sly006 {
        subject s : Persistence;
        doc /* When a record changes, the Storage layer shall tell every subscriber of the storage interface. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-SLY-007'> ReversibleMoveFromFiles_Sly007 {
        subject s : Persistence;
        doc /* When the owner starts the move from files to the database or back, the Storage layer shall perform it with one command and give identical files after the round trip. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-SLY-008'> BackupAndRestore_Sly008 {
        subject s : Persistence;
        doc /* The Storage layer shall allow backup and restore together with the other data of MIA. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-SLY-009'> LibraryExportAndSeed_Sly009 {
        subject s : Persistence;
        doc /* The Storage layer shall export library entries to files and seed them from files with identical entries. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-SLY-010'> ReachableOnlyInsideTheHostNetwork_Sly010 {
        subject s : Persistence;
        doc /* The Storage layer shall accept connections only from the other containers of the stack. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-SLY-011'> OwnContainer_Sly011 {
        subject s : Persistence;
        doc /* The Storage layer shall start as its own container alone and by the compose stack. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-SLY-012'> RealiseIF102_Sly012 {
        subject s : Persistence;
        doc /* The Storage layer shall realise the storage interface IF-102 as specified in contracts/IF-102-storage-interface.md. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-GTB-001'> SharedStateHeld_Gtb001 {
        subject s : Persistence;
        doc /* The Graph tables shall define the tables of workflows (library entries) and context graphs. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-GTB-002'> SchemaValidationOnWrite_Gtb002 {
        subject s : Persistence;
        doc /* When asked to validate a workflow, the Graph tables shall report the first broken rule of node identity, adjacent data nodes, adjacent process nodes, session stopping criterion and cycle (IF-301). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-GTB-003'> ContextGraphsStored_Gtb003 {
        subject s : Persistence;
        doc /* The Graph tables shall define the table of context graphs as versioned records that are not deletable and are validated by the graph rules; the Storage layer keys them by workflow id or by chat. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-GTB-004'> ExampleWorkflowsAsSeedData_Gtb004 {
        subject s : Persistence;
        doc /* The Graph tables shall ship the example workflows lookup, verify and review, the search command and method transfer (off by default) as seed entries of the library, with their specifications, context graphs and benchmark references. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RTB-001'> SharedStateHeld_Rtb001 {
        subject s : Persistence;
        doc /* The Record tables shall define the tables of the history, summaries, chat log, votes, memory, tasks, memos, presets, gestures and run results. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RTB-002'> RunResults_Rtb002 {
        subject s : Persistence;
        doc /* The Record tables shall define the table of run results with the required fields workflow, workflow_version, model_pin and benchmark_version and refuse a record that lacks one. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RTB-003'> VotesStored_Rtb003 {
        subject s : Persistence;
        doc /* The Record tables shall define the table of votes with the required fields user, subject, category (one of four) and value (1 or -1); the time of a vote is that of its version. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RTB-004'> MemoryRecords_Rtb004 {
        subject s : Persistence;
        doc /* The Record tables shall define the table of memory records with the required fields text and source, as deletable records. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RTB-005'> TasksAndMemosExact_Rtb005 {
        subject s : Persistence;
        doc /* The Record tables shall define the tables of tasks and memos with the required field text, as deletable records, and validate a document without changing it. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-RTB-006'> SourceTrustStored_Rtb006 {
        subject s : Persistence;
        doc /* The Record tables shall define the table of the trust values of sources as versioned records that are not deletable. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-001'> PostgreSQLInAContainer_Db001 {
        subject s : Persistence;
        doc /* The Database shall be one PostgreSQL database in a container behind the storage interface IF-102. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-DB-002'> SharedStateHeld_Db002 {
        subject s : Persistence;
        doc /* The Database shall hold the history, summaries, chat log, feedback, presets, gestures, library entries and accounts. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-003'> ImmutableVersions_Db003 {
        subject s : Persistence;
        doc /* When a versioned record is edited, the Database shall store the edit as a new version with author and time and keep the former version unchanged. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-004'> SchemaValidationOnWrite_Db004 {
        subject s : Persistence;
        doc /* If a workflow or graph does not match its schema or violates a graph rule, then the Database shall refuse to store it and name the broken rule. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-005'> Accounts_Db005 {
        subject s : Persistence;
        doc /* The Database shall store accounts with a salted slow password hash and no plain password; the Backend decides who creates an account (REQ-BE-011). */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-006'> ChangeNotification_Db006 {
        subject s : Persistence;
        doc /* When a record changes, the Database shall tell every subscriber of the storage interface. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-007'> ReversibleMoveFromFiles_Db007 {
        subject s : Persistence;
        doc /* When the owner starts the move from files to the database or back, the Database shall perform it with one command and give identical files after the round trip. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-008'> BackupAndRestore_Db008 {
        subject s : Persistence;
        doc /* The Database shall allow backup and restore together with the other data of MIA. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-009'> LibraryExportAndSeed_Db009 {
        subject s : Persistence;
        doc /* The Database shall export library entries to files and seed them from files with identical entries. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-010'> RunResults_Db010 {
        subject s : Persistence;
        doc /* The Database shall store the run results with workflow version, model pin and benchmark version. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-011'> ContextGraphsStored_Db011 {
        subject s : Persistence;
        doc /* The Database shall store one context graph per workflow and one for the chat as versioned records. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-012'> VotesStored_Db012 {
        subject s : Persistence;
        doc /* The Database shall store each vote with user, time, subject and category. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-013'> MemoryRecords_Db013 {
        subject s : Persistence;
        doc /* The Database shall store memory records with their source and delete a record when asked. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-014'> TasksAndMemosExact_Db014 {
        subject s : Persistence;
        doc /* The Database shall store the text of tasks and memos without change. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-015'> SourceTrustStored_Db015 {
        subject s : Persistence;
        doc /* The Database shall keep the users' edits of the trust of a source. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-016'> ReachableOnlyInsideTheHostNetwork_Db016 {
        subject s : Persistence;
        doc /* The Database shall accept connections only from the other containers of the stack. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-017'> OwnContainer_Db017 {
        subject s : Persistence;
        doc /* The Database shall start as its own container alone and by the compose stack. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-DB-018'> ExampleWorkflowsAsSeedData_Db018 {
        subject s : Persistence;
        doc /* The Database shall ship the example workflows lookup, verify and review, the search command and method transfer (off by default) as seed entries of the library, with their specifications, context graphs and benchmark references. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-EVL-001'> HarnessWithRepeats_Evl001 {
        subject s : Evaluation;
        doc /* The Evaluation shall run pipeline variants on fixed suites with repeats, intervals and cost counting. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-EVL-002'> DecisionsOnHeldOutCases_Evl002 {
        subject s : Evaluation;
        doc /* The Evaluation shall decide improvement claims only on held-out cases. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-EVL-003'> JudgeCalibration_Evl003 {
        subject s : Evaluation;
        doc /* The Evaluation shall count the verdicts of a model used as a judge only after its calibration against the users' ratings. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-EVL-004'> VersionsRecordedPerRun_Evl004 {
        subject s : Evaluation;
        doc /* The Evaluation shall record the workflow version, the model pin and the benchmark version of every run. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-EVL-005'> BaselinePerShippedWorkflow_Evl005 {
        subject s : Evaluation;
        doc /* The Evaluation shall keep a recorded baseline for every shipped workflow. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-EVL-006'> SkillPathDocumented_Evl006 {
        subject s : Evaluation;
        doc /* The Evaluation shall document the path from an idea to a promoted skill with its steps and checks. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-EVL-007'> MeasureLatencyAndFrameRate_Evl007 {
        subject s : Evaluation;
        doc /* The Evaluation shall measure the time to the first text of a chat answer and the frame rate of the character. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-EVL-008'> VariantsComparedOnEqualCases_Evl008 {
        subject s : Evaluation;
        doc /* The Evaluation shall compare variants on the same cases with the same repeats. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-EVL-009'> BenchmarksOfTheExampleWorkflows_Evl009 {
        subject s : Evaluation;
        doc /* The Evaluation shall hold the suites, baselines and eval criteria of the example workflows lookup, verify and review as the benchmark that decides their criteria. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::measurement); }
    }
    requirement def <'REQ-EVL-010'> ExampleWorkflowsAsProofOfConcept_Evl010 {
        subject s : Evaluation;
        doc /* The Evaluation shall run the lookup workflow end to end as the proof-of-concept scenario of the platform and the review workflow once it is promoted. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-EVL-011'> ReachThePlatformOnlyThroughIF105_Evl011 {
        subject s : Evaluation;
        doc /* The Evaluation shall run workflows, read their cost and events and list the library only through the interface IF-105 as specified in contracts/IF-105-evaluation-access.md. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-OPR-001'> OneFileOneCommand_Opr001 {
        subject s : OperationLayer;
        doc /* When the owner runs the start command on a fresh checkout with one configuration file, the Operation shall bring MIA up with its database. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-OPR-002'> FirstAccountAtInstallation_Opr002 {
        subject s : OperationLayer;
        doc /* When MIA starts for the first time, the Operation shall let the owner create the first account. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-OPR-003'> MissingOptionsReported_Opr003 {
        subject s : OperationLayer;
        doc /* When MIA starts after an update, the Operation shall report the options missing in the configuration file. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-OPR-004'> OrderlyShutdown_Opr004 {
        subject s : OperationLayer;
        doc /* When MIA is stopped, the Operation shall shut it down in order and save her memory. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-OPR-005'> BackupAndRestoreOfAllData_Opr005 {
        subject s : OperationLayer;
        doc /* The Operation shall back up and restore the data of MIA including the database. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-OPR-006'> Runbook_Opr006 {
        subject s : OperationLayer;
        doc /* The Operation shall provide a runbook with start, update of the model pins, backup and restore of the database, and a retirement plan that ends in freezing the stack with the model digests. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-OPR-007'> ComposeStack_Opr007 {
        subject s : OperationLayer;
        doc /* The Operation shall provide a compose stack that starts the containers of N-2 to N-5 alone and together with one configuration file. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-OPR-008'> PrivateAccessOnly_Opr008 {
        subject s : OperationLayer;
        doc /* The Operation shall expose MIA only over HTTPS inside the home network or the tailnet, with no public port. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-OPR-009'> FreeAndOpen_Opr009 {
        subject s : OperationLayer;
        doc /* The Operation shall provide the licence GPL-3.0-or-later and use no paid API. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-OPR-010'> HardwareConfiguration_Opr010 {
        subject s : OperationLayer;
        doc /* The Operation shall configure the model server to load one model at a time. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-OPS-001'> HarnessWithRepeats_Ops001 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall run pipeline variants on fixed suites with repeats, intervals and cost counting. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-OPS-002'> DecisionsOnHeldOutCases_Ops002 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall decide improvement claims only on held-out cases. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-OPS-003'> JudgeCalibration_Ops003 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall count the verdicts of a model used as a judge only after its calibration against the users' ratings. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-OPS-004'> VersionsRecordedPerRun_Ops004 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall record the workflow version, the model pin and the benchmark version of every run. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-OPS-005'> BaselinePerShippedWorkflow_Ops005 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall keep a recorded baseline for every shipped workflow. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-OPS-006'> SkillPathDocumented_Ops006 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall document the path from an idea to a promoted skill with its steps and checks. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-OPS-007'> OneFileOneCommand_Ops007 {
        subject s : Evaluation;
        doc /* When the owner runs the start command on a fresh checkout with one configuration file, the Evaluation and operation node shall bring MIA up with its database. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-OPS-008'> FirstAccountAtInstallation_Ops008 {
        subject s : Evaluation;
        doc /* When MIA starts for the first time, the Evaluation and operation node shall let the owner create the first account. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-OPS-009'> MissingOptionsReported_Ops009 {
        subject s : Evaluation;
        doc /* When MIA starts after an update, the Evaluation and operation node shall report the options missing in the configuration file. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-OPS-010'> OrderlyShutdown_Ops010 {
        subject s : Evaluation;
        doc /* When MIA is stopped, the Evaluation and operation node shall shut it down in order and save her memory. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-OPS-011'> BackupAndRestoreOfAllData_Ops011 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall back up and restore the data of MIA including the database. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-OPS-012'> Runbook_Ops012 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall provide a runbook with start, update of the model pins, backup and restore of the database and a retirement plan that ends in freezing the stack with the model digests. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-OPS-013'> ComposeStack_Ops013 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall provide a compose stack that starts the containers of N-2 to N-5 alone and together with one configuration file. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-OPS-014'> PrivateAccessOnly_Ops014 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall expose MIA only over HTTPS inside the home network or the tailnet, with no public port. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-OPS-015'> FreeAndOpen_Ops015 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall provide the licence GPL-3.0-or-later and use no paid API. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-OPS-016'> HardwareConfiguration_Ops016 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall configure the model server to load one model at a time. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-OPS-017'> MeasureLatencyAndFrameRate_Ops017 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall measure the time to the first text of a chat answer and the frame rate of the character. */
        @Trace { :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'REQ-OPS-018'> VariantsComparedOnEqualCases_Ops018 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall compare variants on the same cases with the same repeats. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-OPS-019'> BenchmarksOfTheExampleWorkflows_Ops019 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall hold the suites, baselines and eval criteria of the example workflows lookup, verify and review as the benchmark that decides their criteria. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::measurement); }
    }
    requirement def <'REQ-OPS-020'> ExampleWorkflowsAsProofOfConcept_Ops020 {
        subject s : Evaluation;
        doc /* The Evaluation and operation node shall run the lookup workflow end to end as the proof-of-concept scenario of the platform and the review workflow once it is promoted. */
        @Trace { :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'REQ-GA-001'> GraphsAsNodesAndEdges_Ga001 {
        subject s : GraphApp;
        doc /* The Graph app shall show a workflow graph as nodes and edges. */
        @Trace { :>> verifiedBy = (HowVerified::demonstration); }
    }
    requirement def <'REQ-GA-002'> EditAsJSON_Ga002 {
        subject s : GraphApp;
        doc /* When a logged-in user edits a node or an edge, the Graph app shall present it as a JSON dictionary of text data. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-GA-003'> GraphRulesBeforeSaving_Ga003 {
        subject s : GraphApp;
        doc /* When a user saves, the Graph app shall check the identity of nodes, that no two data nodes are adjacent, that there is no cycle and that every session node has a stopping criterion, and name a broken rule. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-GA-004'> VersionsHistoryAndDiff_Ga004 {
        subject s : GraphApp;
        doc /* The Graph app shall save every edit as a new version and show the version history, a diff and the restore of a former version. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-GA-005'> WorkThroughTheBackendAPI_Ga005 {
        subject s : GraphApp;
        doc /* The Graph app shall read and write workflows and context graphs only through the workflow and graph API IF-104. */
        @Trace { :>> verifiedBy = (HowVerified::inspection, HowVerified::test); }
    }
    requirement def <'REQ-GA-006'> ContextGraphsEdited_Ga006 {
        subject s : GraphApp;
        doc /* The Graph app shall let a logged-in user adapt a context graph, every change a new version. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-GA-007'> LoginRequired_Ga007 {
        subject s : GraphApp;
        doc /* The Graph app shall require a login that the backend authenticates and use the backend session for every call. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-GA-008'> LibraryExportAndSeed_Ga008 {
        subject s : GraphApp;
        doc /* The Graph app shall offer the export of the library to files and the seed from files. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-GA-009'> PlainStackWithAVendoredLibrary_Ga009 {
        subject s : GraphApp;
        doc /* The Graph app shall be plain HTML and JavaScript with a vendored graph library and no build step. */
        @Trace { :>> verifiedBy = (HowVerified::inspection); }
    }
    requirement def <'REQ-GA-010'> NoOutsideRequest_Ga010 {
        subject s : GraphApp;
        doc /* The Graph app shall load no resource from outside the host. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }
    requirement def <'REQ-GA-011'> OwnContainer_Ga011 {
        subject s : GraphApp;
        doc /* The Graph app shall start as its own container alone and by the compose stack. */
        @Trace { :>> verifiedBy = (HowVerified::test); }
    }

    requirement r_req_clv_001 : ChatViewWithSenderAndStreaming_Clv001;
    requirement r_req_clv_002 : StopAndQueuePosition_Clv002;
    requirement r_req_clv_003 : SharedHistoryAfterReload_Clv003;
    requirement r_req_clv_004 : ConnectionStateAndDrafts_Clv004;
    requirement r_req_clv_005 : RegenerateAndSpeakAgain_Clv005;
    requirement r_req_clv_006 : ChatWithoutTheCharacter_Clv006;
    requirement r_req_clv_007 : CharacterAsStage_Clv007;
    requirement r_req_clv_008 : StatusLineAndAccountOfATask_Clv008;
    requirement r_req_clv_009 : EditorsForExpressionsGesturesAndPersona_Clv009;
    requirement r_req_clv_010 : VotingControlsAndScore_Clv010;
    requirement r_req_clv_011 : TasksMemosAndMemoryViews_Clv011;
    requirement r_req_clv_012 : SourceTrustEdit_Clv012;
    requirement r_req_clv_013 : VariantLabel_Clv013;
    requirement r_req_clv_014 : LoginViewsAndPasswordChange_Clv014;
    requirement r_req_clv_015 : LoginPageStatesVisibility_Clv015;
    requirement r_req_clv_016 : AccessibilityAndDevices_Clv016;
    requirement r_req_clv_017 : NoRequestLeavesTheHost_Clv017;
    requirement r_req_clv_018 : PasswordOverASecureChannel_Clv018;
    requirement r_req_clv_019 : PlainStack_Clv019;
    requirement r_req_clv_020 : DeliveredByTheBackend_Clv020;
    requirement r_req_clv_021 : UseIF101Only_Clv021;
    requirement r_req_clv_022 : Logout_Clv022;
    requirement r_req_chv_001 : ChatWithoutTheCharacter_Chv001;
    requirement r_req_chv_002 : OneExpressionAPI_Chv002;
    requirement r_req_chv_003 : LivingCharacter_Chv003;
    requirement r_req_chv_004 : MoodShownByTheMoodMap_Chv004;
    requirement r_req_chv_005 : EditorsForExpressionsGesturesAndPersona_Chv005;
    requirement r_req_chv_006 : ShockedReaction_Chv006;
    requirement r_req_chv_007 : CharacterModelSelection_Chv007;
    requirement r_req_chv_008 : VariantLabel_Chv008;
    requirement r_req_chv_009 : AccessibilityAndDevices_Chv009;
    requirement r_req_chv_010 : FrameRate_Chv010;
    requirement r_req_chv_011 : NoRequestLeavesTheHost_Chv011;
    requirement r_req_chv_012 : CharacterInASecureContext_Chv012;
    requirement r_req_chv_013 : PlainStack_Chv013;
    requirement r_req_chv_014 : DeliveredByTheBackend_Chv014;
    requirement r_req_vpb_001 : VoicePlayback_Vpb001;
    requirement r_req_vpb_002 : MuteAndStopPerUser_Vpb002;
    requirement r_req_vpb_003 : VoiceLines_Vpb003;
    requirement r_req_vpb_004 : NoRequestLeavesTheHost_Vpb004;
    requirement r_req_vpb_005 : DeliveredByTheBackend_Vpb005;
    requirement r_req_fe_001 : ChatViewWithSenderAndStreaming_Fe001;
    requirement r_req_fe_002 : StopAndQueuePosition_Fe002;
    requirement r_req_fe_003 : SharedHistoryAfterReload_Fe003;
    requirement r_req_fe_004 : ConnectionStateAndDrafts_Fe004;
    requirement r_req_fe_005 : RegenerateAndSpeakAgain_Fe005;
    requirement r_req_fe_006 : ChatWithoutTheCharacter_Fe006;
    requirement r_req_fe_007 : CharacterAsStage_Fe007;
    requirement r_req_fe_008 : OneExpressionAPI_Fe008;
    requirement r_req_fe_009 : LivingCharacter_Fe009;
    requirement r_req_fe_010 : MoodShownByTheMoodMap_Fe010;
    requirement r_req_fe_011 : VoicePlayback_Fe011;
    requirement r_req_fe_012 : MuteAndStopPerUser_Fe012;
    requirement r_req_fe_013 : VoiceLines_Fe013;
    requirement r_req_fe_014 : StatusLineAndAccountOfATask_Fe014;
    requirement r_req_fe_015 : EditorsForExpressionsGesturesAndPersona_Fe015;
    requirement r_req_fe_016 : VotingControlsAndScore_Fe016;
    requirement r_req_fe_017 : ShockedReaction_Fe017;
    requirement r_req_fe_018 : TasksMemosAndMemoryViews_Fe018;
    requirement r_req_fe_019 : SourceTrustEdit_Fe019;
    requirement r_req_fe_020 : CharacterModelSelection_Fe020;
    requirement r_req_fe_021 : VariantLabel_Fe021;
    requirement r_req_fe_022 : LoginViewsAndPasswordChange_Fe022;
    requirement r_req_fe_023 : LoginPageStatesVisibility_Fe023;
    requirement r_req_fe_024 : AccessibilityAndDevices_Fe024;
    requirement r_req_fe_025 : FrameRate_Fe025;
    requirement r_req_fe_026 : NoRequestLeavesTheHost_Fe026;
    requirement r_req_fe_027 : CharacterInASecureContext_Fe027;
    requirement r_req_fe_028 : PasswordOverASecureChannel_Fe028;
    requirement r_req_fe_029 : PlainStack_Fe029;
    requirement r_req_fe_030 : DeliveredByTheBackend_Fe030;
    requirement r_req_fe_031 : Logout_Fe031;
    requirement r_req_api_001 : ChatEventsAndStreaming_Api001;
    requirement r_req_api_002 : ChangesReachAllDevices_Api002;
    requirement r_req_api_003 : LoginAndSession_Api003;
    requirement r_req_api_004 : ThrottledFailedLogins_Api004;
    requirement r_req_api_005 : PasswordHandling_Api005;
    requirement r_req_api_006 : OwnPasswordAndOwnerOnlyAccounts_Api006;
    requirement r_req_api_007 : EveryRequestAuthenticated_Api007;
    requirement r_req_api_008 : PasswordsOnlyOverASecureChannel_Api008;
    requirement r_req_api_009 : AttributionOfChanges_Api009;
    requirement r_req_api_010 : EverythingVisibleToAllUsers_Api010;
    requirement r_req_api_011 : PythonVersions_Api011;
    requirement r_req_api_012 : StateOnlyThroughTheStorageInterface_Api012;
    requirement r_req_api_013 : ServeTheFrontend_Api013;
    requirement r_req_api_014 : WorkflowAndGraphAPI_Api014;
    requirement r_req_api_015 : RealiseIF101_Api015;
    requirement r_req_api_016 : RealiseTheRoutesOfIF104_Api016;
    requirement r_req_api_017 : Logout_Api017;
    requirement r_req_cha_001 : ChatEventsAndStreaming_Cha001;
    requirement r_req_cha_002 : OneSharedMIA_Cha002;
    requirement r_req_cha_003 : QueueWithPositions_Cha003;
    requirement r_req_cha_004 : StopAnAnswer_Cha004;
    requirement r_req_cha_005 : BoundedHistory_Cha005;
    requirement r_req_cha_006 : RegenerateAndSpeakAgain_Cha006;
    requirement r_req_cha_007 : VoiceLines_Cha007;
    requirement r_req_cha_008 : PersonaFromTheFile_Cha008;
    requirement r_req_cha_009 : MoodAtAllTimes_Cha009;
    requirement r_req_cha_010 : ScoreShiftsTheMood_Cha010;
    requirement r_req_cha_011 : StructuredMemory_Cha011;
    requirement r_req_cha_012 : NoMemoryFromUntrustedText_Cha012;
    requirement r_req_cha_013 : MemoryOpenToUsers_Cha013;
    requirement r_req_cha_014 : SilentRepairOfBehaviourViolations_Cha014;
    requirement r_req_cha_015 : VotesStored_Cha015;
    requirement r_req_cha_016 : AMinusOnAFactOpensACase_Cha016;
    requirement r_req_cha_017 : AdaptationToNegativeFeedback_Cha017;
    requirement r_req_cha_018 : CountersVisibleAndResettable_Cha018;
    requirement r_req_cha_019 : TasksAndMemosRecitedFromRecords_Cha019;
    requirement r_req_cha_020 : StateOnlyThroughTheStorageInterface_Cha020;
    requirement r_req_wfm_001 : SkillsAsTasks_Wfm001;
    requirement r_req_wfm_002 : VersionedWorkflowLibrary_Wfm002;
    requirement r_req_wfm_003 : NoCycles_Wfm003;
    requirement r_req_wfm_004 : GraphRules_Wfm004;
    requirement r_req_wfm_005 : ModelProposalsStayDrafts_Wfm005;
    requirement r_req_wfm_006 : SpecificationBeforeTrust_Wfm006;
    requirement r_req_wfm_007 : TimeFromIdeaToPromotion_Wfm007;
    requirement r_req_wfm_008 : ContextGraphs_Wfm008;
    requirement r_req_wfm_009 : WorkflowScheduleAndEstimate_Wfm009;
    requirement r_req_wfm_010 : CharacterVariantPerWorkflow_Wfm010;
    requirement r_req_wfm_011 : CodeChecksFirst_Wfm011;
    requirement r_req_wfm_012 : UnclearWithoutEvidence_Wfm012;
    requirement r_req_wfm_013 : AFailedCheckInformsTheJudge_Wfm013;
    requirement r_req_wfm_014 : JudgementQuality_Wfm014;
    requirement r_req_wfm_015 : StableVerdicts_Wfm015;
    requirement r_req_wfm_016 : LookupWithSources_Wfm016;
    requirement r_req_wfm_017 : SearchCommand_Wfm017;
    requirement r_req_wfm_018 : ReviewReport_Wfm018;
    requirement r_req_wfm_019 : ReviewInTimeSlices_Wfm019;
    requirement r_req_wfm_020 : ReviewStopsByACodeCheck_Wfm020;
    requirement r_req_wfm_021 : SourceRecordsAndCutOff_Wfm021;
    requirement r_req_wfm_022 : MethodTransfer_Wfm022;
    requirement r_req_wfm_023 : ConfidenceByCode_Wfm023;
    requirement r_req_wfm_024 : NoInventedSource_Wfm024;
    requirement r_req_wfm_025 : StateOnlyThroughTheStorageInterface_Wfm025;
    requirement r_req_wfm_026 : WorkflowAndGraphAPI_Wfm026;
    requirement r_req_run_001 : InternetTasksOnlyOnCommand_Run001;
    requirement r_req_run_002 : SwitchTheModel_Run002;
    requirement r_req_run_003 : ModelServerUnreachable_Run003;
    requirement r_req_run_004 : OptionalLearning_Run004;
    requirement r_req_run_005 : ContextWindowShare_Run005;
    requirement r_req_run_006 : ModelCallsOfTheFirstTry_Run006;
    requirement r_req_run_007 : FirstTextIn10Seconds_Run007;
    requirement r_req_run_008 : BudgetsAndWhatIsMissing_Run008;
    requirement r_req_run_009 : ChatBeforeBackground_Run009;
    requirement r_req_run_010 : OneModelAtATime_Run010;
    requirement r_req_run_011 : UseIF103Only_Run011;
    requirement r_req_run_012 : UseTheLibraryTheToolsAndTheLogOnlyThroughTheirInterfaces_Run012;
    requirement r_req_run_013 : KnowNoParticularWorkflow_Run013;
    requirement r_req_run_014 : RealiseIF202_Run014;
    requirement r_req_run_015 : RealiseIF105_Run015;
    requirement r_req_tls_001 : CodeChecksFirst_Tls001;
    requirement r_req_tls_002 : LookupWithSources_Tls002;
    requirement r_req_tls_003 : SourceRecordsAndCutOff_Tls003;
    requirement r_req_tls_004 : UntrustedTextIsData_Tls004;
    requirement r_req_tls_005 : SandboxOrRefuse_Tls005;
    requirement r_req_tls_006 : NoInventedSource_Tls006;
    requirement r_req_tls_007 : OnlyQueriesLeaveTheHost_Tls007;
    requirement r_req_tls_008 : BudgetAndTrustLabelPerToolCall_Tls008;
    requirement r_req_log_001 : StepByStepAccount_Log001;
    requirement r_req_log_002 : TypedRunEvents_Log002;
    requirement r_req_log_003 : ReplayAndComparison_Log003;
    requirement r_req_log_004 : StatementsTraceableToAQuery_Log004;
    requirement r_req_log_005 : StateOnlyThroughTheStorageInterface_Log005;
    requirement r_req_wfx_001 : StepByStepAccount_Wfx001;
    requirement r_req_wfx_002 : InternetTasksOnlyOnCommand_Wfx002;
    requirement r_req_wfx_003 : SwitchTheModel_Wfx003;
    requirement r_req_wfx_004 : ModelServerUnreachable_Wfx004;
    requirement r_req_wfx_005 : CodeChecksFirst_Wfx005;
    requirement r_req_wfx_006 : LookupWithSources_Wfx006;
    requirement r_req_wfx_007 : SourceRecordsAndCutOff_Wfx007;
    requirement r_req_wfx_008 : TypedRunEvents_Wfx008;
    requirement r_req_wfx_009 : ReplayAndComparison_Wfx009;
    requirement r_req_wfx_010 : StatementsTraceableToAQuery_Wfx010;
    requirement r_req_wfx_011 : OptionalLearning_Wfx011;
    requirement r_req_wfx_012 : ContextWindowShare_Wfx012;
    requirement r_req_wfx_013 : ModelCallsOfTheFirstTry_Wfx013;
    requirement r_req_wfx_014 : UntrustedTextIsData_Wfx014;
    requirement r_req_wfx_015 : SandboxOrRefuse_Wfx015;
    requirement r_req_wfx_016 : NoInventedSource_Wfx016;
    requirement r_req_wfx_017 : OnlyQueriesLeaveTheHost_Wfx017;
    requirement r_req_wfx_018 : FirstTextIn10Seconds_Wfx018;
    requirement r_req_wfx_019 : BudgetsAndWhatIsMissing_Wfx019;
    requirement r_req_wfx_020 : ChatBeforeBackground_Wfx020;
    requirement r_req_wfx_021 : OneModelAtATime_Wfx021;
    requirement r_req_wfx_022 : StateOnlyThroughTheStorageInterface_Wfx022;
    requirement r_req_wfx_023 : UseIF103Only_Wfx023;
    requirement r_req_wfx_024 : RealiseIF105_Wfx024;
    requirement r_req_voi_001 : VoiceSynthesis_Voi001;
    requirement r_req_voi_002 : SpeakOnlyWhatIsMeantToBeHeard_Voi002;
    requirement r_req_voi_003 : VoiceLines_Voi003;
    requirement r_req_voi_004 : DefaultVoiceLinesGenerated_Voi004;
    requirement r_req_be_001 : ChatEventsAndStreaming_Be001;
    requirement r_req_be_002 : OneSharedMIA_Be002;
    requirement r_req_be_003 : QueueWithPositions_Be003;
    requirement r_req_be_004 : StopAnAnswer_Be004;
    requirement r_req_be_005 : BoundedHistory_Be005;
    requirement r_req_be_006 : RegenerateAndSpeakAgain_Be006;
    requirement r_req_be_007 : ChangesReachAllDevices_Be007;
    requirement r_req_be_008 : LoginAndSession_Be008;
    requirement r_req_be_009 : ThrottledFailedLogins_Be009;
    requirement r_req_be_010 : PasswordHandling_Be010;
    requirement r_req_be_011 : OwnPasswordAndOwnerOnlyAccounts_Be011;
    requirement r_req_be_012 : EveryRequestAuthenticated_Be012;
    requirement r_req_be_013 : PasswordsOnlyOverASecureChannel_Be013;
    requirement r_req_be_014 : AttributionOfChanges_Be014;
    requirement r_req_be_015 : EverythingVisibleToAllUsers_Be015;
    requirement r_req_be_016 : VoiceSynthesis_Be016;
    requirement r_req_be_017 : SpeakOnlyWhatIsMeantToBeHeard_Be017;
    requirement r_req_be_018 : VoiceLines_Be018;
    requirement r_req_be_019 : DefaultVoiceLinesGenerated_Be019;
    requirement r_req_be_020 : StepByStepAccount_Be020;
    requirement r_req_be_021 : PersonaFromTheFile_Be021;
    requirement r_req_be_022 : MoodAtAllTimes_Be022;
    requirement r_req_be_023 : ScoreShiftsTheMood_Be023;
    requirement r_req_be_024 : StructuredMemory_Be024;
    requirement r_req_be_025 : NoMemoryFromUntrustedText_Be025;
    requirement r_req_be_026 : MemoryOpenToUsers_Be026;
    requirement r_req_be_027 : SilentRepairOfBehaviourViolations_Be027;
    requirement r_req_be_028 : VotesStored_Be028;
    requirement r_req_be_029 : AMinusOnAFactOpensACase_Be029;
    requirement r_req_be_030 : AdaptationToNegativeFeedback_Be030;
    requirement r_req_be_031 : CountersVisibleAndResettable_Be031;
    requirement r_req_be_032 : TasksAndMemosRecitedFromRecords_Be032;
    requirement r_req_be_033 : SkillsAsTasks_Be033;
    requirement r_req_be_034 : InternetTasksOnlyOnCommand_Be034;
    requirement r_req_be_035 : VersionedWorkflowLibrary_Be035;
    requirement r_req_be_036 : NoCycles_Be036;
    requirement r_req_be_037 : GraphRules_Be037;
    requirement r_req_be_038 : ModelProposalsStayDrafts_Be038;
    requirement r_req_be_039 : SpecificationBeforeTrust_Be039;
    requirement r_req_be_040 : TimeFromIdeaToPromotion_Be040;
    requirement r_req_be_041 : ContextGraphs_Be041;
    requirement r_req_be_042 : WorkflowScheduleAndEstimate_Be042;
    requirement r_req_be_043 : CharacterVariantPerWorkflow_Be043;
    requirement r_req_be_044 : SwitchTheModel_Be044;
    requirement r_req_be_045 : ModelServerUnreachable_Be045;
    requirement r_req_be_046 : CodeChecksFirst_Be046;
    requirement r_req_be_047 : UnclearWithoutEvidence_Be047;
    requirement r_req_be_048 : AFailedCheckInformsTheJudge_Be048;
    requirement r_req_be_049 : JudgementQuality_Be049;
    requirement r_req_be_050 : StableVerdicts_Be050;
    requirement r_req_be_051 : LookupWithSources_Be051;
    requirement r_req_be_052 : SearchCommand_Be052;
    requirement r_req_be_053 : ReviewReport_Be053;
    requirement r_req_be_054 : ReviewInTimeSlices_Be054;
    requirement r_req_be_055 : ReviewStopsByACodeCheck_Be055;
    requirement r_req_be_056 : SourceRecordsAndCutOff_Be056;
    requirement r_req_be_057 : MethodTransfer_Be057;
    requirement r_req_be_058 : TypedRunEvents_Be058;
    requirement r_req_be_059 : ReplayAndComparison_Be059;
    requirement r_req_be_060 : StatementsTraceableToAQuery_Be060;
    requirement r_req_be_061 : OptionalLearning_Be061;
    requirement r_req_be_062 : ContextWindowShare_Be062;
    requirement r_req_be_063 : ModelCallsOfTheFirstTry_Be063;
    requirement r_req_be_064 : UntrustedTextIsData_Be064;
    requirement r_req_be_065 : SandboxOrRefuse_Be065;
    requirement r_req_be_066 : ConfidenceByCode_Be066;
    requirement r_req_be_067 : NoInventedSource_Be067;
    requirement r_req_be_068 : OnlyQueriesLeaveTheHost_Be068;
    requirement r_req_be_069 : FirstTextIn10Seconds_Be069;
    requirement r_req_be_070 : BudgetsAndWhatIsMissing_Be070;
    requirement r_req_be_071 : ChatBeforeBackground_Be071;
    requirement r_req_be_072 : OneModelAtATime_Be072;
    requirement r_req_be_073 : PythonVersions_Be073;
    requirement r_req_be_074 : StateOnlyThroughTheStorageInterface_Be074;
    requirement r_req_be_075 : ServeTheFrontend_Be075;
    requirement r_req_be_076 : WorkflowAndGraphAPI_Be076;
    requirement r_req_be_077 : Logout_Be077;
    requirement r_req_sly_001 : PostgreSQLInAContainer_Sly001;
    requirement r_req_sly_002 : SharedStateHeld_Sly002;
    requirement r_req_sly_003 : ImmutableVersions_Sly003;
    requirement r_req_sly_004 : SchemaValidationOnWrite_Sly004;
    requirement r_req_sly_005 : Accounts_Sly005;
    requirement r_req_sly_006 : ChangeNotification_Sly006;
    requirement r_req_sly_007 : ReversibleMoveFromFiles_Sly007;
    requirement r_req_sly_008 : BackupAndRestore_Sly008;
    requirement r_req_sly_009 : LibraryExportAndSeed_Sly009;
    requirement r_req_sly_010 : ReachableOnlyInsideTheHostNetwork_Sly010;
    requirement r_req_sly_011 : OwnContainer_Sly011;
    requirement r_req_sly_012 : RealiseIF102_Sly012;
    requirement r_req_gtb_001 : SharedStateHeld_Gtb001;
    requirement r_req_gtb_002 : SchemaValidationOnWrite_Gtb002;
    requirement r_req_gtb_003 : ContextGraphsStored_Gtb003;
    requirement r_req_gtb_004 : ExampleWorkflowsAsSeedData_Gtb004;
    requirement r_req_rtb_001 : SharedStateHeld_Rtb001;
    requirement r_req_rtb_002 : RunResults_Rtb002;
    requirement r_req_rtb_003 : VotesStored_Rtb003;
    requirement r_req_rtb_004 : MemoryRecords_Rtb004;
    requirement r_req_rtb_005 : TasksAndMemosExact_Rtb005;
    requirement r_req_rtb_006 : SourceTrustStored_Rtb006;
    requirement r_req_db_001 : PostgreSQLInAContainer_Db001;
    requirement r_req_db_002 : SharedStateHeld_Db002;
    requirement r_req_db_003 : ImmutableVersions_Db003;
    requirement r_req_db_004 : SchemaValidationOnWrite_Db004;
    requirement r_req_db_005 : Accounts_Db005;
    requirement r_req_db_006 : ChangeNotification_Db006;
    requirement r_req_db_007 : ReversibleMoveFromFiles_Db007;
    requirement r_req_db_008 : BackupAndRestore_Db008;
    requirement r_req_db_009 : LibraryExportAndSeed_Db009;
    requirement r_req_db_010 : RunResults_Db010;
    requirement r_req_db_011 : ContextGraphsStored_Db011;
    requirement r_req_db_012 : VotesStored_Db012;
    requirement r_req_db_013 : MemoryRecords_Db013;
    requirement r_req_db_014 : TasksAndMemosExact_Db014;
    requirement r_req_db_015 : SourceTrustStored_Db015;
    requirement r_req_db_016 : ReachableOnlyInsideTheHostNetwork_Db016;
    requirement r_req_db_017 : OwnContainer_Db017;
    requirement r_req_db_018 : ExampleWorkflowsAsSeedData_Db018;
    requirement r_req_evl_001 : HarnessWithRepeats_Evl001;
    requirement r_req_evl_002 : DecisionsOnHeldOutCases_Evl002;
    requirement r_req_evl_003 : JudgeCalibration_Evl003;
    requirement r_req_evl_004 : VersionsRecordedPerRun_Evl004;
    requirement r_req_evl_005 : BaselinePerShippedWorkflow_Evl005;
    requirement r_req_evl_006 : SkillPathDocumented_Evl006;
    requirement r_req_evl_007 : MeasureLatencyAndFrameRate_Evl007;
    requirement r_req_evl_008 : VariantsComparedOnEqualCases_Evl008;
    requirement r_req_evl_009 : BenchmarksOfTheExampleWorkflows_Evl009;
    requirement r_req_evl_010 : ExampleWorkflowsAsProofOfConcept_Evl010;
    requirement r_req_evl_011 : ReachThePlatformOnlyThroughIF105_Evl011;
    requirement r_req_opr_001 : OneFileOneCommand_Opr001;
    requirement r_req_opr_002 : FirstAccountAtInstallation_Opr002;
    requirement r_req_opr_003 : MissingOptionsReported_Opr003;
    requirement r_req_opr_004 : OrderlyShutdown_Opr004;
    requirement r_req_opr_005 : BackupAndRestoreOfAllData_Opr005;
    requirement r_req_opr_006 : Runbook_Opr006;
    requirement r_req_opr_007 : ComposeStack_Opr007;
    requirement r_req_opr_008 : PrivateAccessOnly_Opr008;
    requirement r_req_opr_009 : FreeAndOpen_Opr009;
    requirement r_req_opr_010 : HardwareConfiguration_Opr010;
    requirement r_req_ops_001 : HarnessWithRepeats_Ops001;
    requirement r_req_ops_002 : DecisionsOnHeldOutCases_Ops002;
    requirement r_req_ops_003 : JudgeCalibration_Ops003;
    requirement r_req_ops_004 : VersionsRecordedPerRun_Ops004;
    requirement r_req_ops_005 : BaselinePerShippedWorkflow_Ops005;
    requirement r_req_ops_006 : SkillPathDocumented_Ops006;
    requirement r_req_ops_007 : OneFileOneCommand_Ops007;
    requirement r_req_ops_008 : FirstAccountAtInstallation_Ops008;
    requirement r_req_ops_009 : MissingOptionsReported_Ops009;
    requirement r_req_ops_010 : OrderlyShutdown_Ops010;
    requirement r_req_ops_011 : BackupAndRestoreOfAllData_Ops011;
    requirement r_req_ops_012 : Runbook_Ops012;
    requirement r_req_ops_013 : ComposeStack_Ops013;
    requirement r_req_ops_014 : PrivateAccessOnly_Ops014;
    requirement r_req_ops_015 : FreeAndOpen_Ops015;
    requirement r_req_ops_016 : HardwareConfiguration_Ops016;
    requirement r_req_ops_017 : MeasureLatencyAndFrameRate_Ops017;
    requirement r_req_ops_018 : VariantsComparedOnEqualCases_Ops018;
    requirement r_req_ops_019 : BenchmarksOfTheExampleWorkflows_Ops019;
    requirement r_req_ops_020 : ExampleWorkflowsAsProofOfConcept_Ops020;
    requirement r_req_ga_001 : GraphsAsNodesAndEdges_Ga001;
    requirement r_req_ga_002 : EditAsJSON_Ga002;
    requirement r_req_ga_003 : GraphRulesBeforeSaving_Ga003;
    requirement r_req_ga_004 : VersionsHistoryAndDiff_Ga004;
    requirement r_req_ga_005 : WorkThroughTheBackendAPI_Ga005;
    requirement r_req_ga_006 : ContextGraphsEdited_Ga006;
    requirement r_req_ga_007 : LoginRequired_Ga007;
    requirement r_req_ga_008 : LibraryExportAndSeed_Ga008;
    requirement r_req_ga_009 : PlainStackWithAVendoredLibrary_Ga009;
    requirement r_req_ga_010 : NoOutsideRequest_Ga010;
    requirement r_req_ga_011 : OwnContainer_Ga011;

    satisfy r_req_clv_001 by mia.frontEnd;
    satisfy r_req_clv_002 by mia.frontEnd;
    satisfy r_req_clv_003 by mia.frontEnd;
    satisfy r_req_clv_004 by mia.frontEnd;
    satisfy r_req_clv_005 by mia.frontEnd;
    satisfy r_req_clv_006 by mia.frontEnd;
    satisfy r_req_clv_007 by mia.frontEnd;
    satisfy r_req_clv_008 by mia.frontEnd;
    satisfy r_req_clv_009 by mia.frontEnd;
    satisfy r_req_clv_010 by mia.frontEnd;
    satisfy r_req_clv_011 by mia.frontEnd;
    satisfy r_req_clv_012 by mia.frontEnd;
    satisfy r_req_clv_013 by mia.frontEnd;
    satisfy r_req_clv_014 by mia.frontEnd;
    satisfy r_req_clv_015 by mia.frontEnd;
    satisfy r_req_clv_016 by mia.frontEnd;
    satisfy r_req_clv_017 by mia.frontEnd;
    satisfy r_req_clv_018 by mia.frontEnd;
    satisfy r_req_clv_019 by mia.frontEnd;
    satisfy r_req_clv_020 by mia.frontEnd;
    satisfy r_req_clv_021 by mia.frontEnd;
    satisfy r_req_clv_022 by mia.frontEnd;
    satisfy r_req_chv_001 by mia.frontEnd;
    satisfy r_req_chv_002 by mia.frontEnd;
    satisfy r_req_chv_003 by mia.frontEnd;
    satisfy r_req_chv_004 by mia.frontEnd;
    satisfy r_req_chv_005 by mia.frontEnd;
    satisfy r_req_chv_006 by mia.frontEnd;
    satisfy r_req_chv_007 by mia.frontEnd;
    satisfy r_req_chv_008 by mia.frontEnd;
    satisfy r_req_chv_009 by mia.frontEnd;
    satisfy r_req_chv_010 by mia.frontEnd;
    satisfy r_req_chv_011 by mia.frontEnd;
    satisfy r_req_chv_012 by mia.frontEnd;
    satisfy r_req_chv_013 by mia.frontEnd;
    satisfy r_req_chv_014 by mia.frontEnd;
    satisfy r_req_vpb_001 by mia.frontEnd;
    satisfy r_req_vpb_002 by mia.frontEnd;
    satisfy r_req_vpb_003 by mia.frontEnd;
    satisfy r_req_vpb_004 by mia.frontEnd;
    satisfy r_req_vpb_005 by mia.frontEnd;
    satisfy r_req_fe_001 by mia.frontEnd;
    satisfy r_req_fe_002 by mia.frontEnd;
    satisfy r_req_fe_003 by mia.frontEnd;
    satisfy r_req_fe_004 by mia.frontEnd;
    satisfy r_req_fe_005 by mia.frontEnd;
    satisfy r_req_fe_006 by mia.frontEnd;
    satisfy r_req_fe_007 by mia.frontEnd;
    satisfy r_req_fe_008 by mia.frontEnd;
    satisfy r_req_fe_009 by mia.frontEnd;
    satisfy r_req_fe_010 by mia.frontEnd;
    satisfy r_req_fe_011 by mia.frontEnd;
    satisfy r_req_fe_012 by mia.frontEnd;
    satisfy r_req_fe_013 by mia.frontEnd;
    satisfy r_req_fe_014 by mia.frontEnd;
    satisfy r_req_fe_015 by mia.frontEnd;
    satisfy r_req_fe_016 by mia.frontEnd;
    satisfy r_req_fe_017 by mia.frontEnd;
    satisfy r_req_fe_018 by mia.frontEnd;
    satisfy r_req_fe_019 by mia.frontEnd;
    satisfy r_req_fe_020 by mia.frontEnd;
    satisfy r_req_fe_021 by mia.frontEnd;
    satisfy r_req_fe_022 by mia.frontEnd;
    satisfy r_req_fe_023 by mia.frontEnd;
    satisfy r_req_fe_024 by mia.frontEnd;
    satisfy r_req_fe_025 by mia.frontEnd;
    satisfy r_req_fe_026 by mia.frontEnd;
    satisfy r_req_fe_027 by mia.frontEnd;
    satisfy r_req_fe_028 by mia.frontEnd;
    satisfy r_req_fe_029 by mia.frontEnd;
    satisfy r_req_fe_030 by mia.frontEnd;
    satisfy r_req_fe_031 by mia.frontEnd;
    satisfy r_req_api_001 by mia.webApp;
    satisfy r_req_api_002 by mia.webApp;
    satisfy r_req_api_003 by mia.webApp;
    satisfy r_req_api_004 by mia.webApp;
    satisfy r_req_api_005 by mia.webApp;
    satisfy r_req_api_006 by mia.webApp;
    satisfy r_req_api_007 by mia.webApp;
    satisfy r_req_api_008 by mia.webApp;
    satisfy r_req_api_009 by mia.webApp;
    satisfy r_req_api_010 by mia.webApp;
    satisfy r_req_api_011 by mia.webApp;
    satisfy r_req_api_012 by mia.webApp;
    satisfy r_req_api_013 by mia.webApp;
    satisfy r_req_api_014 by mia.webApp;
    satisfy r_req_api_015 by mia.webApp;
    satisfy r_req_api_016 by mia.webApp;
    satisfy r_req_api_017 by mia.webApp;
    satisfy r_req_cha_001 by mia.conversation;
    satisfy r_req_cha_002 by mia.conversation;
    satisfy r_req_cha_003 by mia.conversation;
    satisfy r_req_cha_004 by mia.conversation;
    satisfy r_req_cha_005 by mia.conversation;
    satisfy r_req_cha_006 by mia.conversation;
    satisfy r_req_cha_007 by mia.conversation;
    satisfy r_req_cha_008 by mia.conversation;
    satisfy r_req_cha_009 by mia.conversation;
    satisfy r_req_cha_010 by mia.conversation;
    satisfy r_req_cha_011 by mia.conversation;
    satisfy r_req_cha_012 by mia.conversation;
    satisfy r_req_cha_013 by mia.conversation;
    satisfy r_req_cha_014 by mia.conversation;
    satisfy r_req_cha_015 by mia.conversation;
    satisfy r_req_cha_016 by mia.conversation;
    satisfy r_req_cha_017 by mia.conversation;
    satisfy r_req_cha_018 by mia.conversation;
    satisfy r_req_cha_019 by mia.conversation;
    satisfy r_req_cha_020 by mia.conversation;
    satisfy r_req_wfm_001 by mia.taskRuntime;
    satisfy r_req_wfm_002 by mia.taskRuntime;
    satisfy r_req_wfm_003 by mia.taskRuntime;
    satisfy r_req_wfm_004 by mia.taskRuntime;
    satisfy r_req_wfm_005 by mia.taskRuntime;
    satisfy r_req_wfm_006 by mia.taskRuntime;
    satisfy r_req_wfm_007 by mia.taskRuntime;
    satisfy r_req_wfm_008 by mia.taskRuntime;
    satisfy r_req_wfm_009 by mia.taskRuntime;
    satisfy r_req_wfm_010 by mia.taskRuntime;
    satisfy r_req_wfm_011 by mia.taskRuntime;
    satisfy r_req_wfm_012 by mia.taskRuntime;
    satisfy r_req_wfm_013 by mia.taskRuntime;
    satisfy r_req_wfm_014 by mia.taskRuntime;
    satisfy r_req_wfm_015 by mia.taskRuntime;
    satisfy r_req_wfm_016 by mia.taskRuntime;
    satisfy r_req_wfm_017 by mia.taskRuntime;
    satisfy r_req_wfm_018 by mia.taskRuntime;
    satisfy r_req_wfm_019 by mia.taskRuntime;
    satisfy r_req_wfm_020 by mia.taskRuntime;
    satisfy r_req_wfm_021 by mia.taskRuntime;
    satisfy r_req_wfm_022 by mia.taskRuntime;
    satisfy r_req_wfm_023 by mia.taskRuntime;
    satisfy r_req_wfm_024 by mia.taskRuntime;
    satisfy r_req_wfm_025 by mia.taskRuntime;
    satisfy r_req_wfm_026 by mia.taskRuntime;
    satisfy r_req_run_001 by mia.taskRuntime;
    satisfy r_req_run_002 by mia.taskRuntime;
    satisfy r_req_run_003 by mia.taskRuntime;
    satisfy r_req_run_004 by mia.taskRuntime;
    satisfy r_req_run_005 by mia.taskRuntime;
    satisfy r_req_run_006 by mia.taskRuntime;
    satisfy r_req_run_007 by mia.taskRuntime;
    satisfy r_req_run_008 by mia.taskRuntime;
    satisfy r_req_run_009 by mia.taskRuntime;
    satisfy r_req_run_010 by mia.taskRuntime;
    satisfy r_req_run_011 by mia.taskRuntime;
    satisfy r_req_run_012 by mia.taskRuntime;
    satisfy r_req_run_013 by mia.taskRuntime;
    satisfy r_req_run_014 by mia.taskRuntime;
    satisfy r_req_run_015 by mia.taskRuntime;
    satisfy r_req_tls_001 by mia.verifier;
    satisfy r_req_tls_002 by mia.verifier;
    satisfy r_req_tls_003 by mia.verifier;
    satisfy r_req_tls_004 by mia.verifier;
    satisfy r_req_tls_005 by mia.verifier;
    satisfy r_req_tls_006 by mia.verifier;
    satisfy r_req_tls_007 by mia.verifier;
    satisfy r_req_tls_008 by mia.verifier;
    satisfy r_req_log_001 by mia.observability;
    satisfy r_req_log_002 by mia.observability;
    satisfy r_req_log_003 by mia.observability;
    satisfy r_req_log_004 by mia.observability;
    satisfy r_req_log_005 by mia.observability;
    satisfy r_req_wfx_001 by mia.taskRuntime;
    satisfy r_req_wfx_002 by mia.taskRuntime;
    satisfy r_req_wfx_003 by mia.taskRuntime;
    satisfy r_req_wfx_004 by mia.taskRuntime;
    satisfy r_req_wfx_005 by mia.taskRuntime;
    satisfy r_req_wfx_006 by mia.taskRuntime;
    satisfy r_req_wfx_007 by mia.taskRuntime;
    satisfy r_req_wfx_008 by mia.taskRuntime;
    satisfy r_req_wfx_009 by mia.taskRuntime;
    satisfy r_req_wfx_010 by mia.taskRuntime;
    satisfy r_req_wfx_011 by mia.taskRuntime;
    satisfy r_req_wfx_012 by mia.taskRuntime;
    satisfy r_req_wfx_013 by mia.taskRuntime;
    satisfy r_req_wfx_014 by mia.taskRuntime;
    satisfy r_req_wfx_015 by mia.taskRuntime;
    satisfy r_req_wfx_016 by mia.taskRuntime;
    satisfy r_req_wfx_017 by mia.taskRuntime;
    satisfy r_req_wfx_018 by mia.taskRuntime;
    satisfy r_req_wfx_019 by mia.taskRuntime;
    satisfy r_req_wfx_020 by mia.taskRuntime;
    satisfy r_req_wfx_021 by mia.taskRuntime;
    satisfy r_req_wfx_022 by mia.taskRuntime;
    satisfy r_req_wfx_023 by mia.taskRuntime;
    satisfy r_req_wfx_024 by mia.taskRuntime;
    satisfy r_req_voi_001 by mia.voice;
    satisfy r_req_voi_002 by mia.voice;
    satisfy r_req_voi_003 by mia.voice;
    satisfy r_req_voi_004 by mia.voice;
    satisfy r_req_be_001 by mia.webApp;
    satisfy r_req_be_002 by mia.webApp;
    satisfy r_req_be_003 by mia.webApp;
    satisfy r_req_be_004 by mia.webApp;
    satisfy r_req_be_005 by mia.webApp;
    satisfy r_req_be_006 by mia.webApp;
    satisfy r_req_be_007 by mia.webApp;
    satisfy r_req_be_008 by mia.webApp;
    satisfy r_req_be_009 by mia.webApp;
    satisfy r_req_be_010 by mia.webApp;
    satisfy r_req_be_011 by mia.webApp;
    satisfy r_req_be_012 by mia.webApp;
    satisfy r_req_be_013 by mia.webApp;
    satisfy r_req_be_014 by mia.webApp;
    satisfy r_req_be_015 by mia.webApp;
    satisfy r_req_be_016 by mia.webApp;
    satisfy r_req_be_017 by mia.webApp;
    satisfy r_req_be_018 by mia.webApp;
    satisfy r_req_be_019 by mia.webApp;
    satisfy r_req_be_020 by mia.webApp;
    satisfy r_req_be_021 by mia.webApp;
    satisfy r_req_be_022 by mia.webApp;
    satisfy r_req_be_023 by mia.webApp;
    satisfy r_req_be_024 by mia.webApp;
    satisfy r_req_be_025 by mia.webApp;
    satisfy r_req_be_026 by mia.webApp;
    satisfy r_req_be_027 by mia.webApp;
    satisfy r_req_be_028 by mia.webApp;
    satisfy r_req_be_029 by mia.webApp;
    satisfy r_req_be_030 by mia.webApp;
    satisfy r_req_be_031 by mia.webApp;
    satisfy r_req_be_032 by mia.webApp;
    satisfy r_req_be_033 by mia.webApp;
    satisfy r_req_be_034 by mia.webApp;
    satisfy r_req_be_035 by mia.webApp;
    satisfy r_req_be_036 by mia.webApp;
    satisfy r_req_be_037 by mia.webApp;
    satisfy r_req_be_038 by mia.webApp;
    satisfy r_req_be_039 by mia.webApp;
    satisfy r_req_be_040 by mia.webApp;
    satisfy r_req_be_041 by mia.webApp;
    satisfy r_req_be_042 by mia.webApp;
    satisfy r_req_be_043 by mia.webApp;
    satisfy r_req_be_044 by mia.webApp;
    satisfy r_req_be_045 by mia.webApp;
    satisfy r_req_be_046 by mia.webApp;
    satisfy r_req_be_047 by mia.webApp;
    satisfy r_req_be_048 by mia.webApp;
    satisfy r_req_be_049 by mia.webApp;
    satisfy r_req_be_050 by mia.webApp;
    satisfy r_req_be_051 by mia.webApp;
    satisfy r_req_be_052 by mia.webApp;
    satisfy r_req_be_053 by mia.webApp;
    satisfy r_req_be_054 by mia.webApp;
    satisfy r_req_be_055 by mia.webApp;
    satisfy r_req_be_056 by mia.webApp;
    satisfy r_req_be_057 by mia.webApp;
    satisfy r_req_be_058 by mia.webApp;
    satisfy r_req_be_059 by mia.webApp;
    satisfy r_req_be_060 by mia.webApp;
    satisfy r_req_be_061 by mia.webApp;
    satisfy r_req_be_062 by mia.webApp;
    satisfy r_req_be_063 by mia.webApp;
    satisfy r_req_be_064 by mia.webApp;
    satisfy r_req_be_065 by mia.webApp;
    satisfy r_req_be_066 by mia.webApp;
    satisfy r_req_be_067 by mia.webApp;
    satisfy r_req_be_068 by mia.webApp;
    satisfy r_req_be_069 by mia.webApp;
    satisfy r_req_be_070 by mia.webApp;
    satisfy r_req_be_071 by mia.webApp;
    satisfy r_req_be_072 by mia.webApp;
    satisfy r_req_be_073 by mia.webApp;
    satisfy r_req_be_074 by mia.webApp;
    satisfy r_req_be_075 by mia.webApp;
    satisfy r_req_be_076 by mia.webApp;
    satisfy r_req_be_077 by mia.webApp;
    satisfy r_req_sly_001 by mia.persistence;
    satisfy r_req_sly_002 by mia.persistence;
    satisfy r_req_sly_003 by mia.persistence;
    satisfy r_req_sly_004 by mia.persistence;
    satisfy r_req_sly_005 by mia.persistence;
    satisfy r_req_sly_006 by mia.persistence;
    satisfy r_req_sly_007 by mia.persistence;
    satisfy r_req_sly_008 by mia.persistence;
    satisfy r_req_sly_009 by mia.persistence;
    satisfy r_req_sly_010 by mia.persistence;
    satisfy r_req_sly_011 by mia.persistence;
    satisfy r_req_sly_012 by mia.persistence;
    satisfy r_req_gtb_001 by mia.persistence;
    satisfy r_req_gtb_002 by mia.persistence;
    satisfy r_req_gtb_003 by mia.persistence;
    satisfy r_req_gtb_004 by mia.persistence;
    satisfy r_req_rtb_001 by mia.persistence;
    satisfy r_req_rtb_002 by mia.persistence;
    satisfy r_req_rtb_003 by mia.persistence;
    satisfy r_req_rtb_004 by mia.persistence;
    satisfy r_req_rtb_005 by mia.persistence;
    satisfy r_req_rtb_006 by mia.persistence;
    satisfy r_req_db_001 by mia.persistence;
    satisfy r_req_db_002 by mia.persistence;
    satisfy r_req_db_003 by mia.persistence;
    satisfy r_req_db_004 by mia.persistence;
    satisfy r_req_db_005 by mia.persistence;
    satisfy r_req_db_006 by mia.persistence;
    satisfy r_req_db_007 by mia.persistence;
    satisfy r_req_db_008 by mia.persistence;
    satisfy r_req_db_009 by mia.persistence;
    satisfy r_req_db_010 by mia.persistence;
    satisfy r_req_db_011 by mia.persistence;
    satisfy r_req_db_012 by mia.persistence;
    satisfy r_req_db_013 by mia.persistence;
    satisfy r_req_db_014 by mia.persistence;
    satisfy r_req_db_015 by mia.persistence;
    satisfy r_req_db_016 by mia.persistence;
    satisfy r_req_db_017 by mia.persistence;
    satisfy r_req_db_018 by mia.persistence;
    satisfy r_req_evl_001 by mia.evaluation;
    satisfy r_req_evl_002 by mia.evaluation;
    satisfy r_req_evl_003 by mia.evaluation;
    satisfy r_req_evl_004 by mia.evaluation;
    satisfy r_req_evl_005 by mia.evaluation;
    satisfy r_req_evl_006 by mia.evaluation;
    satisfy r_req_evl_007 by mia.evaluation;
    satisfy r_req_evl_008 by mia.evaluation;
    satisfy r_req_evl_009 by mia.evaluation;
    satisfy r_req_evl_010 by mia.evaluation;
    satisfy r_req_evl_011 by mia.evaluation;
    satisfy r_req_opr_001 by mia.operation;
    satisfy r_req_opr_002 by mia.operation;
    satisfy r_req_opr_003 by mia.operation;
    satisfy r_req_opr_004 by mia.operation;
    satisfy r_req_opr_005 by mia.operation;
    satisfy r_req_opr_006 by mia.operation;
    satisfy r_req_opr_007 by mia.operation;
    satisfy r_req_opr_008 by mia.operation;
    satisfy r_req_opr_009 by mia.operation;
    satisfy r_req_opr_010 by mia.operation;
    satisfy r_req_ops_001 by mia.evaluation;
    satisfy r_req_ops_002 by mia.evaluation;
    satisfy r_req_ops_003 by mia.evaluation;
    satisfy r_req_ops_004 by mia.evaluation;
    satisfy r_req_ops_005 by mia.evaluation;
    satisfy r_req_ops_006 by mia.evaluation;
    satisfy r_req_ops_007 by mia.evaluation;
    satisfy r_req_ops_008 by mia.evaluation;
    satisfy r_req_ops_009 by mia.evaluation;
    satisfy r_req_ops_010 by mia.evaluation;
    satisfy r_req_ops_011 by mia.evaluation;
    satisfy r_req_ops_012 by mia.evaluation;
    satisfy r_req_ops_013 by mia.evaluation;
    satisfy r_req_ops_014 by mia.evaluation;
    satisfy r_req_ops_015 by mia.evaluation;
    satisfy r_req_ops_016 by mia.evaluation;
    satisfy r_req_ops_017 by mia.evaluation;
    satisfy r_req_ops_018 by mia.evaluation;
    satisfy r_req_ops_019 by mia.evaluation;
    satisfy r_req_ops_020 by mia.evaluation;
    satisfy r_req_ga_001 by mia.graphApp;
    satisfy r_req_ga_002 by mia.graphApp;
    satisfy r_req_ga_003 by mia.graphApp;
    satisfy r_req_ga_004 by mia.graphApp;
    satisfy r_req_ga_005 by mia.graphApp;
    satisfy r_req_ga_006 by mia.graphApp;
    satisfy r_req_ga_007 by mia.graphApp;
    satisfy r_req_ga_008 by mia.graphApp;
    satisfy r_req_ga_009 by mia.graphApp;
    satisfy r_req_ga_010 by mia.graphApp;
    satisfy r_req_ga_011 by mia.graphApp;
    allocate r_req_clv_001 to mia.frontEnd;
    allocate r_req_clv_002 to mia.frontEnd;
    allocate r_req_clv_003 to mia.frontEnd;
    allocate r_req_clv_004 to mia.frontEnd;
    allocate r_req_clv_005 to mia.frontEnd;
    allocate r_req_clv_006 to mia.frontEnd;
    allocate r_req_clv_007 to mia.frontEnd;
    allocate r_req_clv_008 to mia.frontEnd;
    allocate r_req_clv_009 to mia.frontEnd;
    allocate r_req_clv_010 to mia.frontEnd;
    allocate r_req_clv_011 to mia.frontEnd;
    allocate r_req_clv_012 to mia.frontEnd;
    allocate r_req_clv_013 to mia.frontEnd;
    allocate r_req_clv_014 to mia.frontEnd;
    allocate r_req_clv_015 to mia.frontEnd;
    allocate r_req_clv_016 to mia.frontEnd;
    allocate r_req_clv_017 to mia.frontEnd;
    allocate r_req_clv_018 to mia.frontEnd;
    allocate r_req_clv_019 to mia.frontEnd;
    allocate r_req_clv_020 to mia.frontEnd;
    allocate r_req_clv_021 to mia.frontEnd;
    allocate r_req_clv_022 to mia.frontEnd;
    allocate r_req_chv_001 to mia.frontEnd;
    allocate r_req_chv_002 to mia.frontEnd;
    allocate r_req_chv_003 to mia.frontEnd;
    allocate r_req_chv_004 to mia.frontEnd;
    allocate r_req_chv_005 to mia.frontEnd;
    allocate r_req_chv_006 to mia.frontEnd;
    allocate r_req_chv_007 to mia.frontEnd;
    allocate r_req_chv_008 to mia.frontEnd;
    allocate r_req_chv_009 to mia.frontEnd;
    allocate r_req_chv_010 to mia.frontEnd;
    allocate r_req_chv_011 to mia.frontEnd;
    allocate r_req_chv_012 to mia.frontEnd;
    allocate r_req_chv_013 to mia.frontEnd;
    allocate r_req_chv_014 to mia.frontEnd;
    allocate r_req_vpb_001 to mia.frontEnd;
    allocate r_req_vpb_002 to mia.frontEnd;
    allocate r_req_vpb_003 to mia.frontEnd;
    allocate r_req_vpb_004 to mia.frontEnd;
    allocate r_req_vpb_005 to mia.frontEnd;
    allocate r_req_fe_001 to mia.frontEnd;
    allocate r_req_fe_002 to mia.frontEnd;
    allocate r_req_fe_003 to mia.frontEnd;
    allocate r_req_fe_004 to mia.frontEnd;
    allocate r_req_fe_005 to mia.frontEnd;
    allocate r_req_fe_006 to mia.frontEnd;
    allocate r_req_fe_007 to mia.frontEnd;
    allocate r_req_fe_008 to mia.frontEnd;
    allocate r_req_fe_009 to mia.frontEnd;
    allocate r_req_fe_010 to mia.frontEnd;
    allocate r_req_fe_011 to mia.frontEnd;
    allocate r_req_fe_012 to mia.frontEnd;
    allocate r_req_fe_013 to mia.frontEnd;
    allocate r_req_fe_014 to mia.frontEnd;
    allocate r_req_fe_015 to mia.frontEnd;
    allocate r_req_fe_016 to mia.frontEnd;
    allocate r_req_fe_017 to mia.frontEnd;
    allocate r_req_fe_018 to mia.frontEnd;
    allocate r_req_fe_019 to mia.frontEnd;
    allocate r_req_fe_020 to mia.frontEnd;
    allocate r_req_fe_021 to mia.frontEnd;
    allocate r_req_fe_022 to mia.frontEnd;
    allocate r_req_fe_023 to mia.frontEnd;
    allocate r_req_fe_024 to mia.frontEnd;
    allocate r_req_fe_025 to mia.frontEnd;
    allocate r_req_fe_026 to mia.frontEnd;
    allocate r_req_fe_027 to mia.frontEnd;
    allocate r_req_fe_028 to mia.frontEnd;
    allocate r_req_fe_029 to mia.frontEnd;
    allocate r_req_fe_030 to mia.frontEnd;
    allocate r_req_fe_031 to mia.frontEnd;
    allocate r_req_api_001 to mia.webApp;
    allocate r_req_api_002 to mia.webApp;
    allocate r_req_api_003 to mia.webApp;
    allocate r_req_api_004 to mia.webApp;
    allocate r_req_api_005 to mia.webApp;
    allocate r_req_api_006 to mia.webApp;
    allocate r_req_api_007 to mia.webApp;
    allocate r_req_api_008 to mia.webApp;
    allocate r_req_api_009 to mia.webApp;
    allocate r_req_api_010 to mia.webApp;
    allocate r_req_api_011 to mia.webApp;
    allocate r_req_api_012 to mia.webApp;
    allocate r_req_api_013 to mia.webApp;
    allocate r_req_api_014 to mia.webApp;
    allocate r_req_api_015 to mia.webApp;
    allocate r_req_api_016 to mia.webApp;
    allocate r_req_api_017 to mia.webApp;
    allocate r_req_cha_001 to mia.conversation;
    allocate r_req_cha_002 to mia.conversation;
    allocate r_req_cha_003 to mia.conversation;
    allocate r_req_cha_004 to mia.conversation;
    allocate r_req_cha_005 to mia.conversation;
    allocate r_req_cha_006 to mia.conversation;
    allocate r_req_cha_007 to mia.conversation;
    allocate r_req_cha_008 to mia.conversation;
    allocate r_req_cha_009 to mia.conversation;
    allocate r_req_cha_010 to mia.conversation;
    allocate r_req_cha_011 to mia.conversation;
    allocate r_req_cha_012 to mia.conversation;
    allocate r_req_cha_013 to mia.conversation;
    allocate r_req_cha_014 to mia.conversation;
    allocate r_req_cha_015 to mia.conversation;
    allocate r_req_cha_016 to mia.conversation;
    allocate r_req_cha_017 to mia.conversation;
    allocate r_req_cha_018 to mia.conversation;
    allocate r_req_cha_019 to mia.conversation;
    allocate r_req_cha_020 to mia.conversation;
    allocate r_req_wfm_001 to mia.taskRuntime;
    allocate r_req_wfm_002 to mia.taskRuntime;
    allocate r_req_wfm_003 to mia.taskRuntime;
    allocate r_req_wfm_004 to mia.taskRuntime;
    allocate r_req_wfm_005 to mia.taskRuntime;
    allocate r_req_wfm_006 to mia.taskRuntime;
    allocate r_req_wfm_007 to mia.taskRuntime;
    allocate r_req_wfm_008 to mia.taskRuntime;
    allocate r_req_wfm_009 to mia.taskRuntime;
    allocate r_req_wfm_010 to mia.taskRuntime;
    allocate r_req_wfm_011 to mia.taskRuntime;
    allocate r_req_wfm_012 to mia.taskRuntime;
    allocate r_req_wfm_013 to mia.taskRuntime;
    allocate r_req_wfm_014 to mia.taskRuntime;
    allocate r_req_wfm_015 to mia.taskRuntime;
    allocate r_req_wfm_016 to mia.taskRuntime;
    allocate r_req_wfm_017 to mia.taskRuntime;
    allocate r_req_wfm_018 to mia.taskRuntime;
    allocate r_req_wfm_019 to mia.taskRuntime;
    allocate r_req_wfm_020 to mia.taskRuntime;
    allocate r_req_wfm_021 to mia.taskRuntime;
    allocate r_req_wfm_022 to mia.taskRuntime;
    allocate r_req_wfm_023 to mia.taskRuntime;
    allocate r_req_wfm_024 to mia.taskRuntime;
    allocate r_req_wfm_025 to mia.taskRuntime;
    allocate r_req_wfm_026 to mia.taskRuntime;
    allocate r_req_run_001 to mia.taskRuntime;
    allocate r_req_run_002 to mia.taskRuntime;
    allocate r_req_run_003 to mia.taskRuntime;
    allocate r_req_run_004 to mia.taskRuntime;
    allocate r_req_run_005 to mia.taskRuntime;
    allocate r_req_run_006 to mia.taskRuntime;
    allocate r_req_run_007 to mia.taskRuntime;
    allocate r_req_run_008 to mia.taskRuntime;
    allocate r_req_run_009 to mia.taskRuntime;
    allocate r_req_run_010 to mia.taskRuntime;
    allocate r_req_run_011 to mia.taskRuntime;
    allocate r_req_run_012 to mia.taskRuntime;
    allocate r_req_run_013 to mia.taskRuntime;
    allocate r_req_run_014 to mia.taskRuntime;
    allocate r_req_run_015 to mia.taskRuntime;
    allocate r_req_tls_001 to mia.verifier;
    allocate r_req_tls_002 to mia.verifier;
    allocate r_req_tls_003 to mia.verifier;
    allocate r_req_tls_004 to mia.verifier;
    allocate r_req_tls_005 to mia.verifier;
    allocate r_req_tls_006 to mia.verifier;
    allocate r_req_tls_007 to mia.verifier;
    allocate r_req_tls_008 to mia.verifier;
    allocate r_req_log_001 to mia.observability;
    allocate r_req_log_002 to mia.observability;
    allocate r_req_log_003 to mia.observability;
    allocate r_req_log_004 to mia.observability;
    allocate r_req_log_005 to mia.observability;
    allocate r_req_wfx_001 to mia.taskRuntime;
    allocate r_req_wfx_002 to mia.taskRuntime;
    allocate r_req_wfx_003 to mia.taskRuntime;
    allocate r_req_wfx_004 to mia.taskRuntime;
    allocate r_req_wfx_005 to mia.taskRuntime;
    allocate r_req_wfx_006 to mia.taskRuntime;
    allocate r_req_wfx_007 to mia.taskRuntime;
    allocate r_req_wfx_008 to mia.taskRuntime;
    allocate r_req_wfx_009 to mia.taskRuntime;
    allocate r_req_wfx_010 to mia.taskRuntime;
    allocate r_req_wfx_011 to mia.taskRuntime;
    allocate r_req_wfx_012 to mia.taskRuntime;
    allocate r_req_wfx_013 to mia.taskRuntime;
    allocate r_req_wfx_014 to mia.taskRuntime;
    allocate r_req_wfx_015 to mia.taskRuntime;
    allocate r_req_wfx_016 to mia.taskRuntime;
    allocate r_req_wfx_017 to mia.taskRuntime;
    allocate r_req_wfx_018 to mia.taskRuntime;
    allocate r_req_wfx_019 to mia.taskRuntime;
    allocate r_req_wfx_020 to mia.taskRuntime;
    allocate r_req_wfx_021 to mia.taskRuntime;
    allocate r_req_wfx_022 to mia.taskRuntime;
    allocate r_req_wfx_023 to mia.taskRuntime;
    allocate r_req_wfx_024 to mia.taskRuntime;
    allocate r_req_voi_001 to mia.voice;
    allocate r_req_voi_002 to mia.voice;
    allocate r_req_voi_003 to mia.voice;
    allocate r_req_voi_004 to mia.voice;
    allocate r_req_be_001 to mia.webApp;
    allocate r_req_be_002 to mia.webApp;
    allocate r_req_be_003 to mia.webApp;
    allocate r_req_be_004 to mia.webApp;
    allocate r_req_be_005 to mia.webApp;
    allocate r_req_be_006 to mia.webApp;
    allocate r_req_be_007 to mia.webApp;
    allocate r_req_be_008 to mia.webApp;
    allocate r_req_be_009 to mia.webApp;
    allocate r_req_be_010 to mia.webApp;
    allocate r_req_be_011 to mia.webApp;
    allocate r_req_be_012 to mia.webApp;
    allocate r_req_be_013 to mia.webApp;
    allocate r_req_be_014 to mia.webApp;
    allocate r_req_be_015 to mia.webApp;
    allocate r_req_be_016 to mia.webApp;
    allocate r_req_be_017 to mia.webApp;
    allocate r_req_be_018 to mia.webApp;
    allocate r_req_be_019 to mia.webApp;
    allocate r_req_be_020 to mia.webApp;
    allocate r_req_be_021 to mia.webApp;
    allocate r_req_be_022 to mia.webApp;
    allocate r_req_be_023 to mia.webApp;
    allocate r_req_be_024 to mia.webApp;
    allocate r_req_be_025 to mia.webApp;
    allocate r_req_be_026 to mia.webApp;
    allocate r_req_be_027 to mia.webApp;
    allocate r_req_be_028 to mia.webApp;
    allocate r_req_be_029 to mia.webApp;
    allocate r_req_be_030 to mia.webApp;
    allocate r_req_be_031 to mia.webApp;
    allocate r_req_be_032 to mia.webApp;
    allocate r_req_be_033 to mia.webApp;
    allocate r_req_be_034 to mia.webApp;
    allocate r_req_be_035 to mia.webApp;
    allocate r_req_be_036 to mia.webApp;
    allocate r_req_be_037 to mia.webApp;
    allocate r_req_be_038 to mia.webApp;
    allocate r_req_be_039 to mia.webApp;
    allocate r_req_be_040 to mia.webApp;
    allocate r_req_be_041 to mia.webApp;
    allocate r_req_be_042 to mia.webApp;
    allocate r_req_be_043 to mia.webApp;
    allocate r_req_be_044 to mia.webApp;
    allocate r_req_be_045 to mia.webApp;
    allocate r_req_be_046 to mia.webApp;
    allocate r_req_be_047 to mia.webApp;
    allocate r_req_be_048 to mia.webApp;
    allocate r_req_be_049 to mia.webApp;
    allocate r_req_be_050 to mia.webApp;
    allocate r_req_be_051 to mia.webApp;
    allocate r_req_be_052 to mia.webApp;
    allocate r_req_be_053 to mia.webApp;
    allocate r_req_be_054 to mia.webApp;
    allocate r_req_be_055 to mia.webApp;
    allocate r_req_be_056 to mia.webApp;
    allocate r_req_be_057 to mia.webApp;
    allocate r_req_be_058 to mia.webApp;
    allocate r_req_be_059 to mia.webApp;
    allocate r_req_be_060 to mia.webApp;
    allocate r_req_be_061 to mia.webApp;
    allocate r_req_be_062 to mia.webApp;
    allocate r_req_be_063 to mia.webApp;
    allocate r_req_be_064 to mia.webApp;
    allocate r_req_be_065 to mia.webApp;
    allocate r_req_be_066 to mia.webApp;
    allocate r_req_be_067 to mia.webApp;
    allocate r_req_be_068 to mia.webApp;
    allocate r_req_be_069 to mia.webApp;
    allocate r_req_be_070 to mia.webApp;
    allocate r_req_be_071 to mia.webApp;
    allocate r_req_be_072 to mia.webApp;
    allocate r_req_be_073 to mia.webApp;
    allocate r_req_be_074 to mia.webApp;
    allocate r_req_be_075 to mia.webApp;
    allocate r_req_be_076 to mia.webApp;
    allocate r_req_be_077 to mia.webApp;
    allocate r_req_sly_001 to mia.persistence;
    allocate r_req_sly_002 to mia.persistence;
    allocate r_req_sly_003 to mia.persistence;
    allocate r_req_sly_004 to mia.persistence;
    allocate r_req_sly_005 to mia.persistence;
    allocate r_req_sly_006 to mia.persistence;
    allocate r_req_sly_007 to mia.persistence;
    allocate r_req_sly_008 to mia.persistence;
    allocate r_req_sly_009 to mia.persistence;
    allocate r_req_sly_010 to mia.persistence;
    allocate r_req_sly_011 to mia.persistence;
    allocate r_req_sly_012 to mia.persistence;
    allocate r_req_gtb_001 to mia.persistence;
    allocate r_req_gtb_002 to mia.persistence;
    allocate r_req_gtb_003 to mia.persistence;
    allocate r_req_gtb_004 to mia.persistence;
    allocate r_req_rtb_001 to mia.persistence;
    allocate r_req_rtb_002 to mia.persistence;
    allocate r_req_rtb_003 to mia.persistence;
    allocate r_req_rtb_004 to mia.persistence;
    allocate r_req_rtb_005 to mia.persistence;
    allocate r_req_rtb_006 to mia.persistence;
    allocate r_req_db_001 to mia.persistence;
    allocate r_req_db_002 to mia.persistence;
    allocate r_req_db_003 to mia.persistence;
    allocate r_req_db_004 to mia.persistence;
    allocate r_req_db_005 to mia.persistence;
    allocate r_req_db_006 to mia.persistence;
    allocate r_req_db_007 to mia.persistence;
    allocate r_req_db_008 to mia.persistence;
    allocate r_req_db_009 to mia.persistence;
    allocate r_req_db_010 to mia.persistence;
    allocate r_req_db_011 to mia.persistence;
    allocate r_req_db_012 to mia.persistence;
    allocate r_req_db_013 to mia.persistence;
    allocate r_req_db_014 to mia.persistence;
    allocate r_req_db_015 to mia.persistence;
    allocate r_req_db_016 to mia.persistence;
    allocate r_req_db_017 to mia.persistence;
    allocate r_req_db_018 to mia.persistence;
    allocate r_req_evl_001 to mia.evaluation;
    allocate r_req_evl_002 to mia.evaluation;
    allocate r_req_evl_003 to mia.evaluation;
    allocate r_req_evl_004 to mia.evaluation;
    allocate r_req_evl_005 to mia.evaluation;
    allocate r_req_evl_006 to mia.evaluation;
    allocate r_req_evl_007 to mia.evaluation;
    allocate r_req_evl_008 to mia.evaluation;
    allocate r_req_evl_009 to mia.evaluation;
    allocate r_req_evl_010 to mia.evaluation;
    allocate r_req_evl_011 to mia.evaluation;
    allocate r_req_opr_001 to mia.operation;
    allocate r_req_opr_002 to mia.operation;
    allocate r_req_opr_003 to mia.operation;
    allocate r_req_opr_004 to mia.operation;
    allocate r_req_opr_005 to mia.operation;
    allocate r_req_opr_006 to mia.operation;
    allocate r_req_opr_007 to mia.operation;
    allocate r_req_opr_008 to mia.operation;
    allocate r_req_opr_009 to mia.operation;
    allocate r_req_opr_010 to mia.operation;
    allocate r_req_ops_001 to mia.evaluation;
    allocate r_req_ops_002 to mia.evaluation;
    allocate r_req_ops_003 to mia.evaluation;
    allocate r_req_ops_004 to mia.evaluation;
    allocate r_req_ops_005 to mia.evaluation;
    allocate r_req_ops_006 to mia.evaluation;
    allocate r_req_ops_007 to mia.evaluation;
    allocate r_req_ops_008 to mia.evaluation;
    allocate r_req_ops_009 to mia.evaluation;
    allocate r_req_ops_010 to mia.evaluation;
    allocate r_req_ops_011 to mia.evaluation;
    allocate r_req_ops_012 to mia.evaluation;
    allocate r_req_ops_013 to mia.evaluation;
    allocate r_req_ops_014 to mia.evaluation;
    allocate r_req_ops_015 to mia.evaluation;
    allocate r_req_ops_016 to mia.evaluation;
    allocate r_req_ops_017 to mia.evaluation;
    allocate r_req_ops_018 to mia.evaluation;
    allocate r_req_ops_019 to mia.evaluation;
    allocate r_req_ops_020 to mia.evaluation;
    allocate r_req_ga_001 to mia.graphApp;
    allocate r_req_ga_002 to mia.graphApp;
    allocate r_req_ga_003 to mia.graphApp;
    allocate r_req_ga_004 to mia.graphApp;
    allocate r_req_ga_005 to mia.graphApp;
    allocate r_req_ga_006 to mia.graphApp;
    allocate r_req_ga_007 to mia.graphApp;
    allocate r_req_ga_008 to mia.graphApp;
    allocate r_req_ga_009 to mia.graphApp;
    allocate r_req_ga_010 to mia.graphApp;
    allocate r_req_ga_011 to mia.graphApp;

    dependency from r_req_clv_001 to r_req_fe_001;
    dependency from r_req_clv_002 to r_req_fe_002;
    dependency from r_req_clv_003 to r_req_fe_003;
    dependency from r_req_clv_004 to r_req_fe_004;
    dependency from r_req_clv_005 to r_req_fe_005;
    dependency from r_req_clv_006 to r_req_fe_006;
    dependency from r_req_clv_007 to r_req_fe_007;
    dependency from r_req_clv_008 to r_req_fe_014;
    dependency from r_req_clv_009 to r_req_fe_015;
    dependency from r_req_clv_010 to r_req_fe_016;
    dependency from r_req_clv_011 to r_req_fe_018;
    dependency from r_req_clv_012 to r_req_fe_019;
    dependency from r_req_clv_013 to r_req_fe_021;
    dependency from r_req_clv_014 to r_req_fe_022;
    dependency from r_req_clv_015 to r_req_fe_023;
    dependency from r_req_clv_016 to r_req_fe_024;
    dependency from r_req_clv_017 to r_req_fe_026;
    dependency from r_req_clv_018 to r_req_fe_028;
    dependency from r_req_clv_019 to r_req_fe_029;
    dependency from r_req_clv_020 to r_req_fe_030;
    dependency from r_req_clv_021 to r_req_fe_001;
    dependency from r_req_clv_021 to r_req_fe_026;
    dependency from r_req_clv_022 to r_req_fe_031;
    dependency from r_req_chv_001 to r_req_fe_006;
    dependency from r_req_chv_002 to r_req_fe_008;
    dependency from r_req_chv_003 to r_req_fe_009;
    dependency from r_req_chv_004 to r_req_fe_010;
    dependency from r_req_chv_005 to r_req_fe_015;
    dependency from r_req_chv_006 to r_req_fe_017;
    dependency from r_req_chv_007 to r_req_fe_020;
    dependency from r_req_chv_008 to r_req_fe_021;
    dependency from r_req_chv_009 to r_req_fe_024;
    dependency from r_req_chv_010 to r_req_fe_025;
    dependency from r_req_chv_011 to r_req_fe_026;
    dependency from r_req_chv_012 to r_req_fe_027;
    dependency from r_req_chv_013 to r_req_fe_029;
    dependency from r_req_chv_014 to r_req_fe_030;
    dependency from r_req_vpb_001 to r_req_fe_011;
    dependency from r_req_vpb_002 to r_req_fe_012;
    dependency from r_req_vpb_003 to r_req_fe_013;
    dependency from r_req_vpb_004 to r_req_fe_026;
    dependency from r_req_vpb_005 to r_req_fe_030;
    dependency from r_req_fe_001 to fr1;
    dependency from r_req_fe_002 to fr1;
    dependency from r_req_fe_002 to nfr7;
    dependency from r_req_fe_003 to fr1;
    dependency from r_req_fe_004 to fr1;
    dependency from r_req_fe_005 to fr1;
    dependency from r_req_fe_006 to fr2;
    dependency from r_req_fe_007 to fr2;
    dependency from r_req_fe_008 to fr2;
    dependency from r_req_fe_008 to fr23;
    dependency from r_req_fe_009 to fr2;
    dependency from r_req_fe_010 to fr23;
    dependency from r_req_fe_011 to fr3;
    dependency from r_req_fe_012 to fr3;
    dependency from r_req_fe_013 to fr31;
    dependency from r_req_fe_014 to fr4;
    dependency from r_req_fe_015 to fr5;
    dependency from r_req_fe_016 to fr27;
    dependency from r_req_fe_016 to fr29;
    dependency from r_req_fe_017 to fr29;
    dependency from r_req_fe_017 to fr31;
    dependency from r_req_fe_018 to fr28;
    dependency from r_req_fe_018 to fr14;
    dependency from r_req_fe_019 to fr12;
    dependency from r_req_fe_020 to fr24;
    dependency from r_req_fe_021 to fr32;
    dependency from r_req_fe_022 to fr21;
    dependency from r_req_fe_023 to con6;
    dependency from r_req_fe_023 to nfr5;
    dependency from r_req_fe_024 to nfr1;
    dependency from r_req_fe_025 to nfr7;
    dependency from r_req_fe_026 to nfr5;
    dependency from r_req_fe_027 to con4;
    dependency from r_req_fe_027 to nfr6;
    dependency from r_req_fe_028 to con4;
    dependency from r_req_fe_028 to nfr6;
    dependency from r_req_fe_029 to con3;
    dependency from r_req_fe_029 to nfr1;
    dependency from r_req_fe_030 to nfr9;
    dependency from r_req_fe_031 to fr21;
    dependency from r_req_api_001 to r_req_be_001;
    dependency from r_req_api_002 to r_req_be_007;
    dependency from r_req_api_003 to r_req_be_008;
    dependency from r_req_api_004 to r_req_be_009;
    dependency from r_req_api_005 to r_req_be_010;
    dependency from r_req_api_006 to r_req_be_011;
    dependency from r_req_api_007 to r_req_be_012;
    dependency from r_req_api_008 to r_req_be_013;
    dependency from r_req_api_009 to r_req_be_014;
    dependency from r_req_api_010 to r_req_be_015;
    dependency from r_req_api_011 to r_req_be_073;
    dependency from r_req_api_012 to r_req_be_074;
    dependency from r_req_api_013 to r_req_be_075;
    dependency from r_req_api_014 to r_req_be_076;
    dependency from r_req_api_015 to if101;
    dependency from r_req_api_016 to if104;
    dependency from r_req_api_017 to r_req_be_077;
    dependency from r_req_cha_001 to r_req_be_001;
    dependency from r_req_cha_002 to r_req_be_002;
    dependency from r_req_cha_003 to r_req_be_003;
    dependency from r_req_cha_004 to r_req_be_004;
    dependency from r_req_cha_005 to r_req_be_005;
    dependency from r_req_cha_006 to r_req_be_006;
    dependency from r_req_cha_007 to r_req_be_018;
    dependency from r_req_cha_008 to r_req_be_021;
    dependency from r_req_cha_009 to r_req_be_022;
    dependency from r_req_cha_010 to r_req_be_023;
    dependency from r_req_cha_011 to r_req_be_024;
    dependency from r_req_cha_012 to r_req_be_025;
    dependency from r_req_cha_013 to r_req_be_026;
    dependency from r_req_cha_014 to r_req_be_027;
    dependency from r_req_cha_015 to r_req_be_028;
    dependency from r_req_cha_016 to r_req_be_029;
    dependency from r_req_cha_017 to r_req_be_030;
    dependency from r_req_cha_018 to r_req_be_031;
    dependency from r_req_cha_019 to r_req_be_032;
    dependency from r_req_cha_020 to r_req_be_074;
    dependency from r_req_wfm_001 to r_req_be_033;
    dependency from r_req_wfm_002 to r_req_be_035;
    dependency from r_req_wfm_003 to r_req_be_036;
    dependency from r_req_wfm_004 to r_req_be_037;
    dependency from r_req_wfm_005 to r_req_be_038;
    dependency from r_req_wfm_006 to r_req_be_039;
    dependency from r_req_wfm_007 to r_req_be_040;
    dependency from r_req_wfm_008 to r_req_be_041;
    dependency from r_req_wfm_009 to r_req_be_042;
    dependency from r_req_wfm_010 to r_req_be_043;
    dependency from r_req_wfm_011 to r_req_be_046;
    dependency from r_req_wfm_012 to r_req_be_047;
    dependency from r_req_wfm_013 to r_req_be_048;
    dependency from r_req_wfm_014 to r_req_be_049;
    dependency from r_req_wfm_015 to r_req_be_050;
    dependency from r_req_wfm_016 to r_req_be_051;
    dependency from r_req_wfm_017 to r_req_be_052;
    dependency from r_req_wfm_018 to r_req_be_053;
    dependency from r_req_wfm_019 to r_req_be_054;
    dependency from r_req_wfm_020 to r_req_be_055;
    dependency from r_req_wfm_021 to r_req_be_056;
    dependency from r_req_wfm_022 to r_req_be_057;
    dependency from r_req_wfm_023 to r_req_be_066;
    dependency from r_req_wfm_024 to r_req_be_067;
    dependency from r_req_wfm_025 to r_req_be_074;
    dependency from r_req_wfm_026 to r_req_be_076;
    dependency from r_req_run_001 to r_req_wfx_002;
    dependency from r_req_run_002 to r_req_wfx_003;
    dependency from r_req_run_003 to r_req_wfx_004;
    dependency from r_req_run_004 to r_req_wfx_011;
    dependency from r_req_run_005 to r_req_wfx_012;
    dependency from r_req_run_006 to r_req_wfx_013;
    dependency from r_req_run_007 to r_req_wfx_018;
    dependency from r_req_run_008 to r_req_wfx_019;
    dependency from r_req_run_009 to r_req_wfx_020;
    dependency from r_req_run_010 to r_req_wfx_021;
    dependency from r_req_run_011 to r_req_wfx_023;
    dependency from r_req_run_012 to r_req_wfx_019;
    dependency from r_req_run_013 to r_req_wfx_023;
    dependency from r_req_run_014 to if202;
    dependency from r_req_run_015 to r_req_wfx_024;
    dependency from r_req_tls_001 to r_req_wfx_005;
    dependency from r_req_tls_002 to r_req_wfx_006;
    dependency from r_req_tls_003 to r_req_wfx_007;
    dependency from r_req_tls_004 to r_req_wfx_014;
    dependency from r_req_tls_005 to r_req_wfx_015;
    dependency from r_req_tls_006 to r_req_wfx_016;
    dependency from r_req_tls_007 to r_req_wfx_017;
    dependency from r_req_tls_008 to r_req_wfx_014;
    dependency from r_req_tls_008 to r_req_wfx_019;
    dependency from r_req_log_001 to r_req_wfx_001;
    dependency from r_req_log_002 to r_req_wfx_008;
    dependency from r_req_log_003 to r_req_wfx_009;
    dependency from r_req_log_004 to r_req_wfx_010;
    dependency from r_req_log_005 to r_req_wfx_022;
    dependency from r_req_wfx_001 to r_req_be_020;
    dependency from r_req_wfx_002 to r_req_be_034;
    dependency from r_req_wfx_003 to r_req_be_044;
    dependency from r_req_wfx_004 to r_req_be_045;
    dependency from r_req_wfx_005 to r_req_be_046;
    dependency from r_req_wfx_006 to r_req_be_051;
    dependency from r_req_wfx_007 to r_req_be_056;
    dependency from r_req_wfx_008 to r_req_be_058;
    dependency from r_req_wfx_009 to r_req_be_059;
    dependency from r_req_wfx_010 to r_req_be_060;
    dependency from r_req_wfx_011 to r_req_be_061;
    dependency from r_req_wfx_012 to r_req_be_062;
    dependency from r_req_wfx_013 to r_req_be_063;
    dependency from r_req_wfx_014 to r_req_be_064;
    dependency from r_req_wfx_015 to r_req_be_065;
    dependency from r_req_wfx_016 to r_req_be_067;
    dependency from r_req_wfx_017 to r_req_be_068;
    dependency from r_req_wfx_018 to r_req_be_069;
    dependency from r_req_wfx_019 to r_req_be_070;
    dependency from r_req_wfx_020 to r_req_be_071;
    dependency from r_req_wfx_021 to r_req_be_072;
    dependency from r_req_wfx_022 to r_req_be_074;
    dependency from r_req_wfx_023 to if103;
    dependency from r_req_wfx_024 to if105;
    dependency from r_req_voi_001 to r_req_be_016;
    dependency from r_req_voi_002 to r_req_be_017;
    dependency from r_req_voi_003 to r_req_be_018;
    dependency from r_req_voi_004 to r_req_be_019;
    dependency from r_req_be_001 to fr1;
    dependency from r_req_be_002 to fr1;
    dependency from r_req_be_002 to con6;
    dependency from r_req_be_003 to fr1;
    dependency from r_req_be_003 to nfr7;
    dependency from r_req_be_004 to fr1;
    dependency from r_req_be_005 to fr1;
    dependency from r_req_be_006 to fr1;
    dependency from r_req_be_007 to fr1;
    dependency from r_req_be_007 to fr5;
    dependency from r_req_be_007 to nfr8;
    dependency from r_req_be_008 to fr21;
    dependency from r_req_be_009 to fr21;
    dependency from r_req_be_010 to fr21;
    dependency from r_req_be_011 to fr21;
    dependency from r_req_be_012 to nfr6;
    dependency from r_req_be_013 to con4;
    dependency from r_req_be_013 to nfr6;
    dependency from r_req_be_014 to fr21;
    dependency from r_req_be_014 to fr5;
    dependency from r_req_be_014 to fr16;
    dependency from r_req_be_015 to con6;
    dependency from r_req_be_015 to fr5;
    dependency from r_req_be_016 to fr3;
    dependency from r_req_be_017 to fr3;
    dependency from r_req_be_018 to fr31;
    dependency from r_req_be_019 to fr31;
    dependency from r_req_be_020 to fr4;
    dependency from r_req_be_021 to fr25;
    dependency from r_req_be_022 to fr23;
    dependency from r_req_be_023 to fr23;
    dependency from r_req_be_023 to fr27;
    dependency from r_req_be_024 to fr14;
    dependency from r_req_be_025 to fr14;
    dependency from r_req_be_025 to nfr3;
    dependency from r_req_be_026 to fr14;
    dependency from r_req_be_027 to fr15;
    dependency from r_req_be_028 to fr27;
    dependency from r_req_be_029 to fr27;
    dependency from r_req_be_029 to fr29;
    dependency from r_req_be_030 to fr29;
    dependency from r_req_be_031 to fr29;
    dependency from r_req_be_031 to con6;
    dependency from r_req_be_032 to fr28;
    dependency from r_req_be_033 to fr6;
    dependency from r_req_be_034 to fr6;
    dependency from r_req_be_035 to fr7;
    dependency from r_req_be_036 to fr7;
    dependency from r_req_be_037 to fr7;
    dependency from r_req_be_038 to fr7;
    dependency from r_req_be_038 to fr20;
    dependency from r_req_be_039 to fr26;
    dependency from r_req_be_039 to fr20;
    dependency from r_req_be_040 to fr20;
    dependency from r_req_be_041 to fr30;
    dependency from r_req_be_042 to fr33;
    dependency from r_req_be_043 to fr32;
    dependency from r_req_be_044 to fr8;
    dependency from r_req_be_045 to fr8;
    dependency from r_req_be_046 to fr9;
    dependency from r_req_be_047 to fr9;
    dependency from r_req_be_048 to fr9;
    dependency from r_req_be_049 to fr9;
    dependency from r_req_be_050 to fr9;
    dependency from r_req_be_050 to fr10;
    dependency from r_req_be_051 to fr10;
    dependency from r_req_be_052 to fr10;
    dependency from r_req_be_053 to fr11;
    dependency from r_req_be_054 to fr11;
    dependency from r_req_be_055 to fr11;
    dependency from r_req_be_056 to fr12;
    dependency from r_req_be_057 to fr13;
    dependency from r_req_be_058 to fr16;
    dependency from r_req_be_059 to fr16;
    dependency from r_req_be_060 to fr16;
    dependency from r_req_be_061 to fr18;
    dependency from r_req_be_062 to nfr2;
    dependency from r_req_be_063 to nfr2;
    dependency from r_req_be_064 to nfr3;
    dependency from r_req_be_065 to nfr3;
    dependency from r_req_be_066 to nfr4;
    dependency from r_req_be_067 to nfr4;
    dependency from r_req_be_068 to nfr5;
    dependency from r_req_be_069 to nfr7;
    dependency from r_req_be_070 to nfr7;
    dependency from r_req_be_071 to nfr7;
    dependency from r_req_be_072 to con2;
    dependency from r_req_be_072 to nfr7;
    dependency from r_req_be_073 to con3;
    dependency from r_req_be_073 to nfr9;
    dependency from r_req_be_074 to nfr8;
    dependency from r_req_be_074 to con7;
    dependency from r_req_be_075 to nfr9;
    dependency from r_req_be_076 to fr22;
    dependency from r_req_be_076 to fr30;
    dependency from r_req_be_076 to fr7;
    dependency from r_req_be_077 to fr21;
    dependency from r_req_sly_001 to r_req_db_001;
    dependency from r_req_sly_002 to r_req_db_002;
    dependency from r_req_sly_003 to r_req_db_003;
    dependency from r_req_sly_004 to r_req_db_004;
    dependency from r_req_sly_005 to r_req_db_005;
    dependency from r_req_sly_006 to r_req_db_006;
    dependency from r_req_sly_007 to r_req_db_007;
    dependency from r_req_sly_008 to r_req_db_008;
    dependency from r_req_sly_009 to r_req_db_009;
    dependency from r_req_sly_010 to r_req_db_016;
    dependency from r_req_sly_011 to r_req_db_017;
    dependency from r_req_sly_012 to if102;
    dependency from r_req_gtb_001 to r_req_db_002;
    dependency from r_req_gtb_002 to r_req_db_004;
    dependency from r_req_gtb_003 to r_req_db_011;
    dependency from r_req_gtb_004 to r_req_db_018;
    dependency from r_req_rtb_001 to r_req_db_002;
    dependency from r_req_rtb_002 to r_req_db_010;
    dependency from r_req_rtb_003 to r_req_db_012;
    dependency from r_req_rtb_004 to r_req_db_013;
    dependency from r_req_rtb_005 to r_req_db_014;
    dependency from r_req_rtb_006 to r_req_db_015;
    dependency from r_req_db_001 to nfr8;
    dependency from r_req_db_001 to con7;
    dependency from r_req_db_001 to nfr9;
    dependency from r_req_db_002 to nfr8;
    dependency from r_req_db_003 to fr7;
    dependency from r_req_db_003 to fr22;
    dependency from r_req_db_004 to fr22;
    dependency from r_req_db_004 to fr7;
    dependency from r_req_db_005 to fr21;
    dependency from r_req_db_006 to nfr8;
    dependency from r_req_db_006 to fr5;
    dependency from r_req_db_007 to nfr8;
    dependency from r_req_db_008 to fr19;
    dependency from r_req_db_008 to nfr8;
    dependency from r_req_db_009 to fr22;
    dependency from r_req_db_010 to fr26;
    dependency from r_req_db_011 to fr30;
    dependency from r_req_db_012 to fr27;
    dependency from r_req_db_013 to fr14;
    dependency from r_req_db_014 to fr28;
    dependency from r_req_db_015 to fr12;
    dependency from r_req_db_016 to nfr5;
    dependency from r_req_db_016 to nfr6;
    dependency from r_req_db_017 to nfr9;
    dependency from r_req_db_018 to fr20;
    dependency from r_req_db_018 to fr26;
    dependency from r_req_evl_001 to r_req_ops_001;
    dependency from r_req_evl_002 to r_req_ops_002;
    dependency from r_req_evl_003 to r_req_ops_003;
    dependency from r_req_evl_004 to r_req_ops_004;
    dependency from r_req_evl_005 to r_req_ops_005;
    dependency from r_req_evl_006 to r_req_ops_006;
    dependency from r_req_evl_007 to r_req_ops_017;
    dependency from r_req_evl_008 to r_req_ops_018;
    dependency from r_req_evl_009 to r_req_ops_019;
    dependency from r_req_evl_010 to r_req_ops_020;
    dependency from r_req_evl_011 to r_req_ops_001;
    dependency from r_req_evl_011 to r_req_ops_004;
    dependency from r_req_opr_001 to r_req_ops_007;
    dependency from r_req_opr_002 to r_req_ops_008;
    dependency from r_req_opr_003 to r_req_ops_009;
    dependency from r_req_opr_004 to r_req_ops_010;
    dependency from r_req_opr_005 to r_req_ops_011;
    dependency from r_req_opr_006 to r_req_ops_012;
    dependency from r_req_opr_007 to r_req_ops_013;
    dependency from r_req_opr_008 to r_req_ops_014;
    dependency from r_req_opr_009 to r_req_ops_015;
    dependency from r_req_opr_010 to r_req_ops_016;
    dependency from r_req_ops_001 to fr17;
    dependency from r_req_ops_002 to fr17;
    dependency from r_req_ops_003 to fr17;
    dependency from r_req_ops_004 to fr26;
    dependency from r_req_ops_005 to fr26;
    dependency from r_req_ops_005 to fr20;
    dependency from r_req_ops_006 to fr20;
    dependency from r_req_ops_007 to fr19;
    dependency from r_req_ops_008 to fr19;
    dependency from r_req_ops_008 to fr21;
    dependency from r_req_ops_009 to fr19;
    dependency from r_req_ops_010 to fr19;
    dependency from r_req_ops_011 to fr19;
    dependency from r_req_ops_012 to fr19;
    dependency from r_req_ops_013 to nfr9;
    dependency from r_req_ops_014 to nfr6;
    dependency from r_req_ops_014 to con5;
    dependency from r_req_ops_015 to con1;
    dependency from r_req_ops_015 to nfr5;
    dependency from r_req_ops_016 to con2;
    dependency from r_req_ops_016 to nfr7;
    dependency from r_req_ops_017 to nfr7;
    dependency from r_req_ops_018 to nfr2;
    dependency from r_req_ops_018 to fr17;
    dependency from r_req_ops_019 to fr9;
    dependency from r_req_ops_019 to fr10;
    dependency from r_req_ops_019 to fr11;
    dependency from r_req_ops_019 to fr26;
    dependency from r_req_ops_020 to fr20;
    dependency from r_req_ops_020 to nfr2;
    dependency from r_req_ops_020 to nfr4;
    dependency from r_req_ga_001 to fr22;
    dependency from r_req_ga_002 to fr22;
    dependency from r_req_ga_003 to fr22;
    dependency from r_req_ga_003 to fr7;
    dependency from r_req_ga_004 to fr22;
    dependency from r_req_ga_005 to fr22;
    dependency from r_req_ga_005 to con7;
    dependency from r_req_ga_006 to fr30;
    dependency from r_req_ga_007 to fr21;
    dependency from r_req_ga_007 to nfr6;
    dependency from r_req_ga_008 to fr22;
    dependency from r_req_ga_009 to con3;
    dependency from r_req_ga_009 to fr22;
    dependency from r_req_ga_010 to nfr5;
    dependency from r_req_ga_011 to nfr9;
}
// END GENERATED: node requirements
