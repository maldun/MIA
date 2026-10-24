# MIA fresh start: requirements baseline, high-level requirements, SysML v2 model

Started 2026-10-24. Order of reading:

1. `01_current_requirements.md`: what the five requirement documents and the README ask for today, per capability, with status (built / partly / proposed / postponed / dropped), the quantified targets, and **12 places where the sources contradict each other or are out of date**.
2. `02_high_level_requirements.md`: stakeholders, five constraints, 27 high-level requirements (HLR-01 to HLR-27) with rationale, baseline ids and verification method, the gap between today and target, and the decisions needed before the model is final.
3. `sysml/`: the same requirements and the system as a SysML v2 textual model.

| File | Content |
|---|---|
| `sysml/MIA_Common.sysml` | status and verification enums, metadata `Implementation` and `Trace` |
| `sysml/MIA_Context.sysml` | owner and guest, five concerns, external systems (Ollama, SearXNG, scholarly APIs, Tailscale, browser devices, host), system context with typed interfaces |
| `sysml/MIA_Requirements.sysml` | constraints and HLR-01 to HLR-27 as `requirement def` with `Trace` to the baseline, plus the usage tree `miaRequirements` |
| `sysml/MIA_Architecture.sysml` | items, ports and interfaces; `MiaSystem` with 12 subsystems and 59 leaf parts, each naming its code files and status |
| `sysml/MIA_Behavior.sysml` | `ChatExchange`, `LookupRun`, `LiteratureReviewRun`, `Consolidation` as actions; `MiaActivity` and `ReviewRunStates` as state machines |
| `sysml/MIA_Allocation.sysml` | `satisfy` by the system, `allocate` to the carrying parts, seven verification cases |

## How the layers relate

```
detailed requirements (ui/REQUIREMENTS_*.md)        keep: they refine the HLRs
        │  Trace.baseline (ids of 01_...)
        ▼
HLR-xx (MIA_Requirements)  ──satisfy──►  mia : MiaSystem
        │                                     │ allocate
        │ verify                              ▼
        ▼                          leaf parts with Implementation{status, modules}
verification def  (MIA_Allocation)          ──► files in the repository
```

A requirement is fully met when every part allocated to it has status `built`. Parts that are `partly`, `proposed` or `postponed` are the work list; `02_...` section 4 summarises it.

## Checking the model

No SysML v2 tool was available offline (the Sensmetry parser needs a licence key; the pilot implementation could not be downloaded), so **the textual syntax has not been parsed by a SysML tool**. It was written against the SysML v2 textual notation (2023 to 2025 releases) with conservative constructs, and checked by `tools/check_sysml_model.py`, which verifies:

- balanced brackets in every file;
- the requirement ids of the model and of `02_...` are the same set;
- every requirement has a `satisfy`, an `allocate`, and a usage in the tree;
- every `allocate` target is a real part of the subsystem it names;
- every code file named in `Implementation.modules` exists in the repository;
- every baseline id cited by a requirement exists in `01_...`.

Run it with `python3 -I tools/check_sysml_model.py .` from the repository root. To parse the model for real, load the six files together in the SysML v2 pilot implementation (Jupyter kernel or Eclipse plug-in) or in Syside, and fix whatever the parser reports; the likeliest places are listed in `docs/fresh-start/KNOWN_RISKS.md`.
