"""
The harness target for a workflow of the platform (REQ-EVL-001, -004, -011): a case is one run through the interface IF-105
(contracts/IF-105-evaluation-access.md), with the model pin, seed and temperature of the run as options. The platform is whatever provides
IF-105: the mock in the tests, the Backend later. This module imports nothing of the platform (no runner, library or store), only the standard library.

suite.json target: {"kind": "workflow", "workflow": "lookup", "version": 1, "status_field": "status", "budget": {...}}
The status of a case is the output field `status_field` of a run that ended `done`; any other end is "error:<status>".
"""


class WorkflowTarget:
    def __init__(self, platform, pin_of):
        """platform: a provider of IF-105; pin_of: a function that gives the pin of the running harness ({"name", "seed", "temperature"})"""
        self.platform, self._pin_of = platform, pin_of

    def options(self, variant, suite):
        pin = self._pin_of()
        if not pin or any(pin.get(k) is None for k in ("name", "seed", "temperature")):
            raise ValueError("a workflow suite needs a pin with name, seed and temperature")
        options = {"model_pin": pin["name"], "seed": pin["seed"], "temperature": pin["temperature"]}
        budget = variant.get("budget") or suite.target.get("budget")
        if budget:
            options["budget"] = dict(budget)
        return options

    def __call__(self, case, variant, suite):
        target = suite.target
        result = self.platform.run_case(target["workflow"], target["version"], case["input"], self.options(variant, suite))
        field = target.get("status_field", "status")
        outputs = result.get("outputs") or {}
        status = outputs.get(field) if result["status"] == "done" and field in outputs else "error:" + (result["status"] if result["status"] != "done" else "no_" + field)
        return status, {"outputs": outputs, "run_id": result["run_id"], "cost": result.get("cost") or {}, "events": len(result.get("events") or [])}
