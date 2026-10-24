/*
 * MIA system model, part 1 of 6: shared vocabulary.
 *
 * Files of the model (one package each, load them together):
 *   MIA_Common.sysml        this file: status values, metadata used by the other files
 *   MIA_Context.sysml       stakeholders, concerns, external systems, system context
 *   MIA_Requirements.sysml  constraints and the 27 high-level requirements (HLR-01 .. HLR-27)
 *   MIA_Architecture.sysml  logical architecture, interfaces, mapping to the code base
 *   MIA_Behavior.sysml      main behaviours (chat exchange, lookup, review, consolidation, activity)
 *   MIA_Allocation.sysml    satisfy / allocate relations and verification cases
 *
 * Baseline: docs/fresh-start/01_current_requirements.md
 * Requirements in prose: docs/fresh-start/02_high_level_requirements.md
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
        attribute baseline : String[0..*];  // ids in docs/fresh-start/01_current_requirements.md
        attribute verifiedBy : HowVerified[1..*];
    }
}
