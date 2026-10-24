"""
BM-GATE-001 (specs/number-gate/test-spec.md, verifies NFR-BUD-001): the median time per claim of the verification gate on MP-light is at most 10 seconds.

Protocol: 100 claims, 50 from the dev split of each of verdicts_vitaminc and verdicts_wikidata, chosen with harness.sample_cases(cases, 100, seed 7) so that pairs stay together;
3 warm-up claims first (not counted); one run of each claim with the pipeline verify.number_gate@1, temperature 0, seed 7, on the reference host (RX 7800 XT 16 GB, Ollama in podman,
OLLAMA_MAX_LOADED_MODELS=1); the result is the median of the seconds per claim from the records of the run.
Regression rule: a median that is more than 20 % above the baseline in benchmarks/baseline.json fails; the baseline is measured at task T-06.

RED BY DESIGN: this benchmark needs the gate (verify.number_gate@1), harness.sample_cases and the pin options of the harness (REQ-EVAL-003, REQ-EVAL-004), which are tasks of plan.md;
until then it stops with the message below. The protected folder benchmarks/ changes only through a plan amendment.
Run with: python benchmarks/bm_gate_001.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

BUDGET_SECONDS = 10.0
REGRESSION = 1.20


def main():
    try:
        import harness
        runnable = hasattr(harness, "sample_cases") and harness.sample_cases([], 0, 0) is not None
    except Exception:
        runnable = False
    sample = harness.sample_cases([{"id": "x", "tags": ["pair:x"]}, {"id": "y", "tags": ["pair:x"]}], 2, 7) if runnable else []
    if not sample:
        print("BM-GATE-001 is not runnable yet: it needs verify.number_gate@1, harness.sample_cases and the pin options of the harness (plan.md tasks). Red by design.")
        return 2
    # the measurement itself is written with the tasks that provide the parts above (T-06); it must print the median and compare it with BUDGET_SECONDS and baseline.json
    print("BM-GATE-001: measurement not written yet")
    return 2


if __name__ == "__main__":
    sys.exit(main())
