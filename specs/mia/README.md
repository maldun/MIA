# specs/mia: the system-wide specification of MIA

Phase 1 (Explore) of the development workflow, status **Draft**, under step-by-step review.

| File | What |
|---|---|
| `high-level-spec.md` | the HLS: goal, scope, FR-1..22 (FR-20 follows in review step 3b), NFR-1..8, CON-1..7, agent profile, architecture, acceptance criteria, risks and open questions |
| `architecture.sysml` | SysML v2: vocabulary, architecture (13 subsystems, 65 parts with code files and status), agent view (10 model steps, 5 trust boundaries), requirements, satisfy / allocate / verification |
| `model/MIA_Context.sysml`, `model/MIA_Behavior.sysml` | supplements: people, concerns, external systems; chat exchange, lookup, review, consolidation, activity states |
| `baseline-requirements.md` | what the five requirement documents and the README ask for, per capability, with status, and the contradictions between them |
| `research.md` | measured facts: hardware, models, baselines, what was not looked at |
| `KNOWN_RISKS.md` | where a SysML parser is most likely to object |

Checks (from the repository root):
- `python3 -I tools/check_sysml_model.py .` ids of model and HLS agree, every requirement is satisfied and allocated, allocation paths and code files exist, baseline ids exist. It does not parse SysML.
- `python3 -I ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests` 0 errors; the warnings say `requirements.md` does not exist yet (Plan).
- `python3 -I ~/.claude/skills/agent-app/scripts/agent_check.py --spec-dir specs/mia --eval-dir eval` 20 errors that are the Plan-phase placeholders (per-step second budgets, threat ids) and the warning that no suite has a holdout split.

History: the first draft (27 requirements `HLR-01..27`, 6 SysML files) lived in `docs/fresh-start/`; the mapping is in section 3.5 of the HLS.
