"""Mock of IF-105, the evaluation access of the Backend for the harness (protected). Complexity 2: a fake runner that echoes its options.
It makes no model call; the pins it knows are the two of the project. Built on the mock of IF-202."""
try:
    from .errors import ServiceError
    from .if_202_run_workflow import RunWorkflowMock
except ImportError:
    from errors import ServiceError
    from if_202_run_workflow import RunWorkflowMock

PINS = ("MP-light", "MP-full")
REQUIRED = ("model_pin", "seed", "temperature")


class EvaluationAccessMock:
    def __init__(self, workflows=None):
        self._runner = RunWorkflowMock(workflows)
        self._events = {}

    def workflows(self):
        return [{"id": w, "versions": sorted(int(v) for v in versions), "status": "draft"} for w, versions in sorted(self._runner.workflows.items())]

    def run_case(self, workflow, version, inputs, options):
        missing = [k for k in REQUIRED if not isinstance(options, dict) or k not in options]
        if missing:
            raise ServiceError("bad_options", detail=missing)
        if options["model_pin"] not in PINS:
            raise ServiceError("pin_unavailable", detail=options["model_pin"])
        result = self._runner.run(workflow, version, inputs, options.get("budget"), "harness", options={k: options[k] for k in REQUIRED})
        self._events[result["run_id"]] = result["events"]
        return dict(result, options=dict(options))

    def events(self, run_id):
        if run_id not in self._events:
            raise ServiceError("unknown_run")
        return list(self._events[run_id])
