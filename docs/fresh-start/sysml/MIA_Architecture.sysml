/*
 * MIA system model, part 4 of 6: logical architecture.
 *
 * The decomposition follows the code base of 2026-10-24: every leaf part names the files that
 * realise it and how far it is built (metadata Implementation). Internal connections show the main
 * flows only; they are not a complete wiring diagram.
 *
 * Not modelled here: the 3D character's own internals (Godot scenes, shape keys), which are
 * documented in ui/README.md and ui/REQUIREMENTS.md.
 */
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
    item def ScholarQuery { attribute text : String; attribute until : String[0..1]; }   // date cut-off
    item def ScholarRecords;
    item def RunEvent {
        attribute run : String;              // one run id travels with every model call and request
        attribute seq : Integer;
        attribute type : String;             // typed vocabulary of REQUIREMENTS_CORE 13d
        attribute actor : String;
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
    port def EventSink { in item event : RunEvent; }

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
        part conversation : ConversationCore;
        part taskRuntime : TaskRuntime;
        part verification : VerificationSuite;
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
        interface eventsFromVerification : EventLink connect verification.events to observability.sink;
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
            doc /* Editor and chat tokens, allowed origins, content security policy. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("web_app.py", "presets_api.py"); }
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
                   consolidation (HLR-18). */
            @Implementation { :>> status = ImplementationStatus::partly; :>> modules = ("communicator.py"); }
        }
        part scheduleReminders {
            doc /* Hourly time check; target: a commitment ledger read by code. */
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
        part library {
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
        doc /* Everything is files on the host (JSON, JSON lines, Markdown, one SQLite index). Postgres behind a storage layer is postponed. */
        part files {
            doc /* data/, memories.json, long_time_history.json, presets, gestures, chat log, runs, store, library. */
            @Implementation { :>> status = ImplementationStatus::built; :>> modules = ("config.py", "constants.py"); }
        }
        part storageLayer {
            doc /* Interfaces over the file stores so a database can replace them (stage 0 of the database plan). */
            @Implementation { :>> status = ImplementationStatus::postponed; }
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
    }
}
