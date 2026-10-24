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

## Viewing and validating the model (SysML v2)
The reference tool is the OMG pilot implementation (`Systems-Modeling/SysML-v2-Pilot-Implementation`, release `2026-09`, asset `jupyter-sysml-kernel-0.63.0.zip`, 126 MB, contains a Java jar and the standard library). It runs as a Jupyter kernel; `%viz` draws diagrams with Graphviz. Needs Java and `dot` (both installed on the development host). Steps, read from the release's own `install.py` (not run by the coding agent; run them yourself):

```
python3 -m venv ~/venvs/sysml && ~/venvs/sysml/bin/pip install jupyterlab
unzip jupyter-sysml-kernel-0.63.0.zip -d ~/sysml-kernel
~/venvs/sysml/bin/python ~/sysml-kernel/install.py --sys-prefix --graphviz-path /usr/bin/dot
~/venvs/sysml/bin/jupyter lab        # new notebook, kernel "SysML"
```

In a notebook cell, paste or load the six files (all packages must be known to the kernel), then for example `%viz --view=tree MIA_Architecture::MiaSystem`. A parse error in a cell is the real syntax check that `KNOWN_RISKS.md` is waiting for. The kernel's `%help` lists the magic commands. The matching JupyterLab extension (`jupyterlab-sysml-0.63.0.tgz`, syntax highlighting) is an optional second asset of the same release.
