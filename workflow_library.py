"""The library of workflows and context graphs (IF-203; REQ-WFM-002, -003, -004, -026): versioned graph documents with a lifecycle and an estimate.

Versions, history and the graph rules (cycle, adjacent data nodes, session without stopping criterion) are the job of the Storage (IF-102), which refuses
a broken document and consumes no version; this module is the only caller of those tables for workflows (REQ-WFM-025). What the Storage does not hold
is the lifecycle: status, specification and benchmark of a workflow are kept by `meta` (get(id) -> dict, put(id, dict)); the default is in memory until the
table of IF-302 for them is installed.
Errors are WorkflowLibraryError with the codes of contracts/IF-203-workflow-library.md: invalid, not_found, conflict, not_promotable.
"""
try:
    from .storage import StorageError
except ImportError:
    from storage import StorageError

KINDS = ("workflows", "context_graphs")
STATUSES = ("draft", "tested", "trusted", "retired")
NEEDS = ("specification", "benchmark")
NO_COST = {"seconds": 0.0, "calls": 0, "tokens": 0}


class WorkflowLibraryError(Exception):
    def __init__(self, code, rule=None, detail=None):
        super().__init__("%s%s" % (code, ": %s" % rule if rule else ""))
        self.code, self.rule, self.detail = code, rule, detail


class MemoryMeta:
    def __init__(self):
        self._data = {}

    def get(self, record_id):
        return dict(self._data.get(record_id, {}))

    def put(self, record_id, meta):
        self._data[record_id] = dict(meta)


def _storage_call(call, *args, **kw):
    try:
        return call(*args, **kw)
    except StorageError as err:
        raise WorkflowLibraryError(err.code, err.rule, err.detail) from err


class WorkflowLibrary:
    def __init__(self, storage, costs=None, meta=None):
        # costs: node id -> {"seconds", "calls", "tokens"} as measured by the runs (IF-202), or a function that gives them
        self._storage, self._meta = storage, meta or MemoryMeta()
        self._costs = costs if callable(costs) else (lambda: costs or {})

    @staticmethod
    def _kind(kind):
        if kind not in KINDS:
            raise WorkflowLibraryError("not_found", detail=kind)

    def list_ids(self, kind):
        self._kind(kind)
        return _storage_call(self._storage.ids, kind)

    def read(self, kind, record_id, version=None):
        self._kind(kind)
        entry = _storage_call(self._storage.get, kind, record_id, version)
        entry["status"] = self._meta.get(record_id).get("status", "draft") if kind == "workflows" else "draft"
        return entry

    def save(self, kind, record_id, doc, author, expected_version=None):
        self._kind(kind)
        return _storage_call(self._storage.put, kind, record_id, doc, author, expected_version)

    def history(self, kind, record_id):
        self._kind(kind)
        return _storage_call(self._storage.history, kind, record_id)

    def diff(self, kind, record_id, a, b):
        old, new = self.read(kind, record_id, a)["doc"], self.read(kind, record_id, b)["doc"]
        old_nodes, new_nodes = {n["id"]: n for n in old.get("nodes", [])}, {n["id"]: n for n in new.get("nodes", [])}
        old_edges = {"%s->%s" % (e["from"], e["to"]) for e in old.get("edges", [])}
        new_edges = {"%s->%s" % (e["from"], e["to"]) for e in new.get("edges", [])}
        return {"nodes_added": sorted(set(new_nodes) - set(old_nodes)), "nodes_removed": sorted(set(old_nodes) - set(new_nodes)),
                "nodes_changed": sorted(i for i in set(old_nodes) & set(new_nodes) if old_nodes[i] != new_nodes[i]),
                "edges_added": sorted(new_edges - old_edges), "edges_removed": sorted(old_edges - new_edges)}

    def restore(self, kind, record_id, version, author):
        return self.save(kind, record_id, self.read(kind, record_id, version)["doc"], author)

    def attach(self, record_id, part, doc):
        if part not in NEEDS:
            raise WorkflowLibraryError("not_found", detail=part)
        self.read("workflows", record_id)
        meta = self._meta.get(record_id)
        meta[part] = doc
        self._meta.put(record_id, meta)

    def set_status(self, record_id, status, author):
        if status not in STATUSES:
            raise WorkflowLibraryError("invalid", rule="status")
        self.read("workflows", record_id)
        meta = self._meta.get(record_id)
        missing = [part for part in NEEDS if part not in meta]
        if status in ("tested", "trusted") and missing:
            raise WorkflowLibraryError("not_promotable", detail=missing)
        meta["status"] = status
        self._meta.put(record_id, meta)
        return {"status": status}

    def estimate(self, record_id, version=None):
        """order: a topological order of the process nodes; critical path: the longest chain by seconds; sums over all nodes, a session node counts
        its maximum cycles times the cost of one cycle. The stored version was checked on save (no cycle), so the order always exists."""
        doc = self.read("workflows", record_id, version)["doc"]
        nodes = {n["id"]: n for n in doc["nodes"]}
        successors = {i: [] for i in nodes}
        predecessors = {i: [] for i in nodes}
        for edge in doc["edges"]:
            successors[edge["from"]].append(edge["to"])
            predecessors[edge["to"]].append(edge["from"])
        costs = self._costs()
        cost = {i: self._cost_of(node, costs) for i, node in nodes.items()}
        order, best, via = [], {}, {}
        waiting = {i: len(predecessors[i]) for i in nodes}
        ready = sorted(i for i in nodes if not waiting[i])
        while ready:
            i = ready.pop(0)
            order.append(i)
            prev = max(((best[p], p) for p in predecessors[i]), default=(0.0, None))
            best[i], via[i] = prev[0] + cost[i]["seconds"], prev[1]
            for j in successors[i]:
                waiting[j] -= 1
                if not waiting[j]:
                    ready.append(j)
        critical, end = [], (max(best, key=best.get) if best else None)
        while end is not None:
            critical.append(end)
            end = via[end]
        process = lambda ids: [i for i in ids if nodes[i]["kind"] == "process"]
        return {"order": process(order), "critical_path": process(reversed(critical)),
                "seconds": sum(c["seconds"] for c in cost.values()), "calls": sum(c["calls"] for c in cost.values()),
                "tokens": sum(c["tokens"] for c in cost.values())}

    @staticmethod
    def _cost_of(node, costs):
        if node["kind"] != "process":
            return dict(NO_COST)
        cost = dict(costs.get(node["id"], NO_COST))
        if node.get("session"):
            cycles = (node.get("stop") or {}).get("max_cycles") or 1
            cost = {key: value * cycles for key, value in cost.items()}
        return cost
