/*
 * MIA, high-level architecture (Phase 1, specs/mia/high-level-spec.md).
 *
 * One file, six packages, in this order:
 *   MIA_Common        status and verification enums, metadata Implementation and Trace
 *   MIA_Architecture  items, ports, interfaces, MiaSystem with 13 subsystems; leaf parts name their code files
 *   MIA_AgentView     the app agent: model steps, untrusted items, trust boundaries (agent-app conventions, 8)
 *   MIA_Requirements  constraints CON-1..5, functional FR-1..FR-19, non-functional NFR-1..NFR-8
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
        doc /* Python 3.11 to 3.13 (3.12 tested); Godot 4.6.1 with GDScript only and the Compatibility renderer; the chat page
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
               user who sent it, and one shared MIA answering all of them (D-4). */
        attribute queuedMessages : Integer = 1;
        attribute messagesPerMinute : Integer = 10;
        @Trace { :>> baseline = ("CT-1", "CT-2", "CT-3", "CT-4", "CT-5", "CT-6", "CT-8", "CT-9", "CT-11");
                 :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
    }
    requirement def <'FR-2'> EmbodiedCharacter {
        subject mia : MiaSystem;
        doc /* MIA shall show her emotional state and speech through a 3D character with smoothly blending facial expressions,
               arm gestures, a moving mouth while speaking, blinking and idle motion, driven through one central
               expression API; if the character cannot load, the chat shall still work. */
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
               approves it, shown as a diff and tried on the test set. */
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
               answer, and let a failed hard check outweigh any model verdict. */
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
               source to a model judgement, and say "unknown" when nothing supports an answer. */
        @Trace { :>> baseline = ("RS-1", "RS-6");
                 :>> verifiedBy = (HowVerified::measurement); }
    }
    requirement def <'FR-11'> LiteratureReview {
        subject mia : MiaSystem;
        doc /* Given a research question, an optional field scope, a cut-off date and a budget, MIA shall produce a structured
               report: sources kept and dropped with reasons, findings per sub-question with verbatim anchors,
               conflicts, an answerability figure with its parts, open gaps and next keywords; she works in time
               slices (first 60 s), gives an intermediate report with a recommendation at the end of each, and
               continues only when the requesting user agrees. */
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
               cases. */
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
        doc /* The first text of a chat answer appears within seconds on the light model (target to be fixed, see 6); every
               task runs under explicit budgets (steps, seconds, calls, tokens) and a run that exceeds one ends
               with what it has and says what is missing; the character runs at 30+ fps on a mid-range phone and
               60 fps on desktop. Several users share one model server: waiting messages are queued, show their
               position and are refused only when the queue is full (length set in Plan). A chat answer has
               priority over a background task: a long task (a review slice) yields the model server to waiting
               chat messages. */
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
               and writes the shared database, checks the graph rules (node identity, no two data nodes
               adjacent, cycles only inside a session) before saving, saves every edit as a new version, and
               shows the version history and a diff. */
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
               (D-14, D-16) and repeats back-story elements in fitting situations; calibration.txt is one shared
               configuration file for all users and the baseline of the persona; every user can change it (FR-5)
               and a change applies to all (D-22). How well she keeps it is measured by a persona suite in Plan. */
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
               on the same cases. */
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
               receives for the points (for example money or love points; the words are data, purely fictional,
               shown in the page). The overall score is shown over time and shifts MIA's general mood (FR-23);
               the interval over which the score is judged (one week at first) is a setting that may be changed
               (D-23). The scores are used to compare versions of workflows and behaviours over time; they never
               decide a fact (NFR-4, BF4): a minus on a factual answer opens a case for the benchmark instead of
               changing what MIA states. */
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
               error and logged. */
        attribute attentionChance : Real = 0.3;
        @Trace { :>> baseline = ("VO-3", "CT-7", "EM-1"); :>> verifiedBy = (HowVerified::test, HowVerified::demonstration); }
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
    requirement nfr7 : EfficientOnGivenHardware;
    requirement nfr8 : SharedStateInDatabase;
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
    satisfy nfr7 by mia;
    satisfy nfr8 by mia;

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
}
