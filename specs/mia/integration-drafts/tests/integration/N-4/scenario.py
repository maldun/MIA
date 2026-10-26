"""Scenario of N-4 (Evaluation and operation): the harness reaches the platform only through IF-105 (protected).
The scenario is the part of the harness contract that is visible from outside: every run of a case carries the pin, seed and temperature in its header,
repeats of a case with a fake model agree, missing options and an unknown pin are refused. Step 0 runs it on the mock of IF-105. Step 1 lets the real
harness (N-4.1) do the calling, step 2 adds the operation layer (N-4.2: compose stack and configuration); both need their node in READY. The cases that need the
stack (TC-N4-001 to -003) run in stage 3 on the compose stack and are not in this scenario."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "helpers", "mocks"))
from errors import ServiceError  # noqa: E402

OPTIONS = {"model_pin": "MP-light", "seed": 7, "temperature": 0, "budget": {"calls": 15}}
MARKS = {0: [], 1: ["REQ-OPS-001", "REQ-OPS-004"], 2: ["REQ-OPS-007", "REQ-OPS-013"]}


def code_of(call):
    try:
        call()
    except ServiceError as err:
        return err.code
    raise AssertionError("no ServiceError raised")


def run(p, t):
    evaluation = p["IF-105"]
    t.assertIn("lookup", [w["id"] for w in evaluation.workflows()])

    # three repeats of one case: header with the options, equal outputs, the cost summed from the runs
    runs = [evaluation.run_case("lookup", 1, {"question": "q%d" % (n % 1)}, OPTIONS) for n in range(3)]
    for r in runs:
        t.assertEqual(r["status"], "done")
        t.assertEqual(r["events"][0]["options"], {"model_pin": "MP-light", "seed": 7, "temperature": 0})
    t.assertEqual(len({str(r["outputs"]) for r in runs}), 1)
    total = {k: sum(r["cost"][k] for r in runs) for k in ("steps", "seconds", "calls", "tokens")}
    t.assertEqual(total["calls"], 3 * runs[0]["cost"]["calls"])

    # a run is never started without the options that make it reproducible
    t.assertEqual(code_of(lambda: evaluation.run_case("lookup", 1, {}, {"model_pin": "MP-light", "temperature": 0})), "bad_options")
    t.assertEqual(code_of(lambda: evaluation.run_case("lookup", 1, {}, dict(OPTIONS, model_pin="MP-huge"))), "pin_unavailable")
    t.assertEqual(code_of(lambda: evaluation.run_case("nothing", 1, {}, OPTIONS)), "unknown_workflow")
