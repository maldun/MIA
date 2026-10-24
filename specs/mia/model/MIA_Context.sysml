/*
 * MIA system model, part 2 of 6: stakeholders, concerns and system context.
 */
package MIA_Context {
    private import ScalarValues::*;
    private import MIA_Architecture::*;

    // ---------------------------------------------------------------- people

    part def Person;

    part def User :> Person {
        doc /* A trusted person with a local account (password). A handful at most. Sees and may edit everything; a change
               applies to all (CON-6). Every user is addressed as master unless the persona says otherwise. */
    }
    part def Owner :> User {
        doc /* The user who creates the accounts, administers the host, develops and researches. */
    }

    // ---------------------------------------------------------------- concerns

    concern def <'CN-1'> CompanionQuality {
        doc /* A pleasant, in-character conversation partner that feels alive: answers in seconds, a face that
               shows the mood, a voice, a history, and a page that works on a phone. */
        subject mia;
        stakeholder owner : Owner;
        stakeholder user : User;
    }
    concern def <'CN-2'> TrustworthyFacts {
        doc /* What MIA states as fact can be traced to a source or a check; "unknown" is an honest answer;
               references are never invented. */
        subject mia;
        stakeholder owner : Owner;
    }
    concern def <'CN-3'> ResearchValue {
        doc /* The project answers a research question: how far a small free local model gets inside pipelines
               with verification. Every comparison is fair, repeatable and carries its limits. */
        subject mia;
        stakeholder owner : Owner;
    }
    concern def <'CN-4'> OwnershipAndPrivacy {
        doc /* Data, models and compute stay on the owner's machines; nothing runs without the owner's consent
               on the internet; the GPU can be handed back to other programs. */
        subject mia;
        stakeholder owner : Owner;
    }
    concern def <'CN-5'> Operability {
        doc /* Install, update, back up, stop cleanly and understand what happened, without being an expert in every part. */
        subject mia;
        stakeholder owner : Owner;
    }

    // ---------------------------------------------------------------- external systems

    part def ExternalSystem;

    part def BrowserDevice :> ExternalSystem {
        doc /* Desktop or phone browser (current Chrome, Firefox, Safari iOS 16+, Android Chrome). */
        attribute isPhone : Boolean;
        port web : ~ChatPort;
        port character : ~ExpressionPort;
        port speaker : ~AudioPort;
    }
    part def OllamaServer :> ExternalSystem {
        doc /* Local model server (a container managed by MIA, or an existing Ollama at a given URL). */
        port api : ~LlmPort;
    }
    part def SearxngServer :> ExternalSystem {
        doc /* Self-hosted metasearch; DuckDuckGo is the fallback behind the same tool interface. */
        port api : ~SearchPort;
    }
    part def ScholarlyApiProvider :> ExternalSystem {
        doc /* OpenAlex, Crossref, PubMed, arXiv, Semantic Scholar: read-only, rate-limited, free. */
        port api : ~ScholarPort;
    }
    part def TailscaleDaemon :> ExternalSystem {
        doc /* Optional: HTTPS inside the owner's tailnet through tailscale serve; never funnel. */
    }
    part def HostMachine :> ExternalSystem {
        doc /* Fedora, one AMD RX 7800 XT with 16 GB (ROCm; NVIDIA and CPU also supported), 62 GB RAM, podman. */
        attribute gpuMemoryGB : Real = 16;
        attribute ramGB : Real = 62;
    }

    // ---------------------------------------------------------------- context

    part def MiaContext {
        doc /* Who and what MIA talks to. Interfaces are the typed links of MIA_Architecture. */
        part owner : Owner;
        part user : User [0..*];
        part device : BrowserDevice [1..*];
        part ollama : OllamaServer;
        part searxng : SearxngServer;
        part scholarlyApis : ScholarlyApiProvider [1..5];
        part tailnet : TailscaleDaemon [0..1];
        part host : HostMachine;
        part system : MiaSystem;

        interface chatLink : ChatLink connect device.web to system.chat;
        interface characterLink : ExpressionLink connect system.expression to device.character;
        interface audioLink : AudioLink connect system.audio to device.speaker;
        interface llmLink : LlmLink connect system.llm to ollama.api;
        interface searchLink : SearchLink connect system.search to searxng.api;
        interface scholarLink : ScholarLink connect system.scholar to scholarlyApis.api;
    }
}
