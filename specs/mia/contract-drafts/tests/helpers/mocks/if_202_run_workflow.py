"""Mock of IF-202, running a workflow (protected). Complexity 3: budgets, an event stream and measured costs.
Scripted workflows with an estimate (known before the run) and an actual cost; it makes no model call and does no real verification or research."""
try:
    from .errors import ServiceError
except ImportError:
    from errors import ServiceError

KEYS = ("steps", "seconds", "calls", "tokens")
LOOKUP = {"outputs": {"answer": "42", "sources": 2},
          "estimate": {"steps": 3, "seconds": 9.0, "calls": 3, "tokens": 1800}, "cost": {"steps": 3, "seconds": 9.0, "calls": 3, "tokens": 1800},
          "node_costs": {"search": {"seconds": 2.0, "calls": 0, "tokens": 0}, "judge": {"seconds": 5.0, "calls": 3, "tokens": 1500}}}
DRIFTING = {"outputs": {"answer": "late"}, "estimate": {"steps": 2, "seconds": 4.0, "calls": 2, "tokens": 900},
            "cost": {"steps": 2, "seconds": 4.0, "calls": 4, "tokens": 900}, "node_costs": {}}
DEFAULT = {"lookup": {"1": LOOKUP}, "drifting": {"1": DRIFTING}}


class RunWorkflowMock:
    def __init__(self, workflows=None):
        self.workflows = workflows or DEFAULT
        self._runs = 0

    def run(self, workflow, version, inputs, budget, user):
        """status: refused (the estimate exceeds a budget, nothing is started), budget_exhausted (the run exceeds a budget; partial outputs), done."""
        script = self.workflows.get(workflow, {}).get(str(version))
        if script is None:
            raise ServiceError("unknown_workflow")
        self._runs += 1
        run_id = "r%d" % self._runs
        event = lambda kind, **payload: {"type": kind, "run_id": run_id, "user": user, **payload}
        events = [event("run_start", workflow=workflow, version=version)]
        budget = budget or {}
        too_big = [k for k in KEYS if k in budget and script["estimate"].get(k, 0) > budget[k]]
        over = [k for k in KEYS if k in budget and script["cost"].get(k, 0) > budget[k]]
        if too_big:
            status, outputs, missing = "refused", {}, too_big
        elif over:
            status, outputs, missing = "budget_exhausted", {"partial": True}, over
        else:
            status, outputs, missing = "done", dict(script["outputs"]), []
        events.append(event("run_end", status=status, missing=missing))
        return {"run_id": run_id, "status": status, "outputs": outputs, "missing": missing, "events": events}

    def costs(self, workflow, node_id):
        for script in self.workflows.get(workflow, {}).values():
            if node_id in script.get("node_costs", {}):
                return dict(script["node_costs"][node_id])
        return None
