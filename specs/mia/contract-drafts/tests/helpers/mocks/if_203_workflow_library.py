"""Mock of IF-203, the workflow library of the Workflow management (protected). Complexity 2: an in-memory library on the storage mock.
It does not hold the specification and benchmark records themselves, only that they are attached."""
try:
    from .errors import ServiceError, StorageError
    from .if_102_storage import StorageMock
except ImportError:
    from errors import ServiceError, StorageError
    from if_102_storage import StorageMock

KINDS = ("workflows", "context_graphs")
STATUSES = ("draft", "tested", "trusted", "retired")
NEEDS = ("specification", "benchmark")


def _wrap(fn):
    try:
        return fn()
    except StorageError as err:
        raise ServiceError(err.code, rule=err.rule, detail=err.detail)


class WorkflowLibraryMock:
    def __init__(self, costs=None):
        self.storage = StorageMock()
        self.costs = costs or {}                 # node id -> {"seconds", "calls", "tokens"}, as IF-202 `costs` would deliver
        self._status, self._attached = {}, {}

    def _kind(self, kind):
        if kind not in KINDS:
            raise ServiceError("not_found", detail=kind)

    def list_ids(self, kind):
        self._kind(kind)
        return _wrap(lambda: self.storage.ids(kind))

    def read(self, kind, record_id, version=None):
        self._kind(kind)
        entry = _wrap(lambda: self.storage.get(kind, record_id, version))
        entry["status"] = self._status.get((kind, record_id), "draft")
        return entry

    def save(self, kind, record_id, doc, author, expected_version=None):
        self._kind(kind)
        result = _wrap(lambda: self.storage.put(kind, record_id, doc, author, expected_version))
        self._status.setdefault((kind, record_id), "draft")
        return result

    def history(self, kind, record_id):
        self._kind(kind)
        return _wrap(lambda: self.storage.history(kind, record_id))

    def diff(self, kind, record_id, a, b):
        old, new = self.read(kind, record_id, a)["doc"], self.read(kind, record_id, b)["doc"]
        on, nn = {n["id"]: n for n in old.get("nodes", [])}, {n["id"]: n for n in new.get("nodes", [])}
        oe, ne = {"%s->%s" % (e["from"], e["to"]) for e in old.get("edges", [])}, {"%s->%s" % (e["from"], e["to"]) for e in new.get("edges", [])}
        return {"nodes_added": sorted(set(nn) - set(on)), "nodes_removed": sorted(set(on) - set(nn)),
                "nodes_changed": sorted(i for i in set(on) & set(nn) if on[i] != nn[i]),
                "edges_added": sorted(ne - oe), "edges_removed": sorted(oe - ne)}

    def restore(self, kind, record_id, version, author):
        return self.save(kind, record_id, self.read(kind, record_id, version)["doc"], author)

    def attach(self, record_id, part, doc):
        if part not in NEEDS:
            raise ServiceError("not_found", detail=part)
        self._attached.setdefault(record_id, {})[part] = doc

    def set_status(self, record_id, status, author):
        if status not in STATUSES:
            raise ServiceError("invalid", rule="status")
        self.read("workflows", record_id)
        missing = [p for p in NEEDS if p not in self._attached.get(record_id, {})]
        if status in ("tested", "trusted") and missing:
            raise ServiceError("not_promotable", detail=missing)
        self._status[("workflows", record_id)] = status
        return {"status": status}

    def estimate(self, record_id, version=None):
        """Order = a topological order of the process nodes; the critical path is the longest chain by seconds. A session node counts
        its maximum cycles times the cost of one cycle."""
        doc = self.read("workflows", record_id, version)["doc"]
        nodes = {n["id"]: n for n in doc["nodes"]}
        succ = {i: [] for i in nodes}
        indeg = {i: 0 for i in nodes}
        for e in doc["edges"]:
            succ[e["from"]].append(e["to"])
            indeg[e["to"]] += 1
        ready, order = sorted(i for i in nodes if indeg[i] == 0), []
        while ready:
            i = ready.pop(0)
            order.append(i)
            for j in succ[i]:
                indeg[j] -= 1
                if indeg[j] == 0:
                    ready.append(j)
        cost = {}
        for i, n in nodes.items():
            if n["kind"] != "process":
                cost[i] = {"seconds": 0.0, "calls": 0, "tokens": 0}
                continue
            c = dict(self.costs.get(i, {"seconds": 0.0, "calls": 0, "tokens": 0}))
            if n.get("session"):
                cycles = (n.get("stop") or {}).get("max_cycles") or 1
                c = {k: v * cycles for k, v in c.items()}
            cost[i] = c
        best, path = {}, {}
        for i in order:
            prev = max(((best[p], p) for p in nodes if i in succ[p]), default=(0.0, None))
            best[i] = prev[0] + cost[i]["seconds"]
            path[i] = prev[1]
        end = max(best, key=best.get) if best else None
        critical = []
        while end is not None:
            critical.append(end)
            end = path[end]
        return {"order": [i for i in order if nodes[i]["kind"] == "process"], "critical_path": [i for i in reversed(critical) if nodes[i]["kind"] == "process"],
                "seconds": sum(c["seconds"] for c in cost.values()), "calls": sum(c["calls"] for c in cost.values()), "tokens": sum(c["tokens"] for c in cost.values())}
