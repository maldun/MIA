"""The library of workflows and context graphs (IF-203; REQ-WFM-002, -003, -004, -026): versioned graph documents with a lifecycle and an estimate.

Versions, history and the graph rules (cycle, adjacent data nodes, session without stopping criterion) are the job of the Storage (IF-102), which refuses
a broken document and consumes no version; this module is the only caller of those tables for workflows (REQ-WFM-025). What the Storage does not hold
is the lifecycle: status, specification and benchmark of a workflow are one record of the table `workflow_meta` (IF-302 v3, amendment A-15), a new version
for every change, so that who promoted what and when stays in the history. `meta` (get(id) -> dict, put(id, dict, author)) can be replaced in tests.
Errors are WorkflowLibraryError with the codes of contracts/IF-203-workflow-library.md: invalid, not_found, conflict, not_promotable.
"""
try:
    from .storage import StorageError
    from . import context_graph
except ImportError:
    from storage import StorageError
    import context_graph

KINDS = ("workflows", "context_graphs", "transforms")
STATUSES = ("draft", "tested", "trusted", "retired")
NEEDS = ("specification", "benchmark")
TRANSFORM_META = "transform_meta"
# the fields of a transform's meta record and their types (None: checked by the table, which knows the two lists of values)
TRANSFORM_FIELDS = {"trust": None, "lifecycle": None, "reason": str, "evidence": str, "baseline_allowed": bool, "shipped": bool, "changed_by": str}
DEFAULT_STEP_BUDGET = 800          # tokens of the view of a step whose node names no budget (the default of context_graph.render)
NO_COST = {"seconds": 0.0, "calls": 0, "tokens": 0}


class WorkflowLibraryError(Exception):
    def __init__(self, code, rule=None, detail=None):
        super().__init__("%s%s" % (code, ": %s" % rule if rule else ""))
        self.code, self.rule, self.detail = code, rule, detail


class TableMeta:
    TABLE = "workflow_meta"

    def __init__(self, storage):
        self._storage = storage

    def get(self, record_id):
        try:
            return self._storage.get(self.TABLE, record_id)["doc"]
        except StorageError as err:
            if err.code == "not_found":
                return {}
            raise

    def put(self, record_id, meta, author):
        self._storage.put(self.TABLE, record_id, dict(meta, status=meta.get("status", "draft")), author)


def _storage_call(call, *args, **kw):
    try:
        return call(*args, **kw)
    except StorageError as err:
        raise WorkflowLibraryError(err.code, err.rule, err.detail) from err


class WorkflowLibrary:
    def __init__(self, storage, costs=None, meta=None):
        # costs: node id -> {"seconds", "calls", "tokens"} as measured by the runs (IF-202), or a function that gives them
        self._storage, self._meta = storage, meta or TableMeta(storage)
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
        if kind == "transforms":
            return self._read_transform(record_id, version)
        entry = _storage_call(self._storage.get, kind, record_id, version)
        entry["status"] = self._meta.get(record_id).get("status", "draft") if kind == "workflows" else "draft"
        return entry

    def save(self, kind, record_id, doc, author, expected_version=None):
        self._kind(kind)
        if kind == "transforms":
            return self._save_transform(record_id, doc, author, expected_version)
        for node in (doc.get("nodes") if isinstance(doc, dict) and isinstance(doc.get("nodes"), list) else []):
            budget = node.get("budget_tokens") if isinstance(node, dict) else None
            if budget is not None and (isinstance(budget, bool) or not isinstance(budget, int) or budget < 1):
                raise WorkflowLibraryError("invalid", rule="budget_tokens", detail=node.get("id"))      # REQ-WFM-008
        if kind == "workflows" and isinstance(doc, dict) and doc.get("variant") is not None and not (isinstance(doc["variant"], str) and doc["variant"].strip()):
            raise WorkflowLibraryError("invalid", rule="variant", detail=doc["variant"])      # REQ-WFM-010: the name of a character variant
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

    def attach(self, record_id, part, doc, author="library"):
        if part not in NEEDS:
            raise WorkflowLibraryError("not_found", detail=part)
        self.read("workflows", record_id)
        meta = self._meta.get(record_id)
        meta[part] = doc
        self._meta.put(record_id, meta, author)

    def set_status(self, record_id, status, author):
        if status not in STATUSES:
            raise WorkflowLibraryError("invalid", rule="status")
        self.read("workflows", record_id)
        meta = self._meta.get(record_id)
        missing = [part for part in NEEDS if part not in meta]
        if status in ("tested", "trusted") and missing:
            raise WorkflowLibraryError("not_promotable", detail=missing)
        meta["status"] = status
        self._meta.put(record_id, meta, author)
        return {"status": status}

    def promotion_record(self, record_id):
        """REQ-WFM-007: the two time stamps of a skill: `idea` is the time of its first version, `promoted` the time of the first step out of draft
        (tested or trusted), None while it is a draft. Both come from the history the Storage keeps, so nothing extra is written."""
        idea = self.history("workflows", record_id)[0]["time"]
        promoted = None
        for entry in _storage_call(self._storage.history, TableMeta.TABLE, record_id) if self._has_meta(record_id) else []:
            if self._storage.get(TableMeta.TABLE, record_id, entry["version"])["doc"]["status"] in ("tested", "trusted"):
                promoted = entry["time"]
                break
        return {"idea": idea, "promoted": promoted}

    def _has_meta(self, record_id):
        return record_id in self._storage.ids(TableMeta.TABLE)

    def step_view(self, record_id, events, step=None):
        """REQ-WFM-008: the view of the run `events` that fits the token budget of `step`. The stored context graph with the id of the workflow (or `chat`) is the
        design-time template: its process node `step` may carry `budget_tokens`; the graph itself is rebuilt from the events (context_graph.replay) and never stored.
        Returns {"text", "budget_tokens", "expanded"}; `expanded` are the groups shown in detail."""
        template = self.read("context_graphs", record_id)["doc"]
        budget = DEFAULT_STEP_BUDGET
        if step is not None:
            node = next((n for n in template["nodes"] if n["id"] == step and n["kind"] == "process"), None)
            if node is None:
                raise WorkflowLibraryError("not_found", detail=step)
            budget = node.get("budget_tokens", budget)
        view = context_graph.default_view(context_graph.replay(events))
        text, expanded = context_graph.render(view, budget_tokens=budget)
        return {"text": text, "budget_tokens": budget, "expanded": expanded}

    def variant_of(self, record_id, version=None):
        """REQ-WFM-010: the character variant the workflow names (the key `variant` of its document), or None; the chat service sends it to the frontend while the workflow runs"""
        return self.read("workflows", record_id, version)["doc"].get("variant")

    def check_budget(self, record_id, budget, version=None):
        """REQ-WFM-009: the estimate and the budgets it exceeds (seconds, calls, tokens; a key that is absent is unlimited). The run itself is refused by the
        Workflow execution (IF-202 `refused`)."""
        estimate = self.estimate(record_id, version)
        return {"estimate": estimate, "exceeded": [key for key in ("seconds", "calls", "tokens") if key in budget and estimate[key] > budget[key]]}

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

    # --- the kind `transforms` (IF-203 v1, A-111, G-V2.TOOLBOX): the code in the table `transforms`, trust and lifecycle in `transform_meta` (A-110, A-112) ---
    # A new version of the code leaves the meta record as it is (REQ-WFM-092); who may set a value is the rule of the toolbox, not of the library.

    def _read_transform(self, record_id, version):
        entry = _storage_call(self._storage.get, "transforms", record_id, version)
        meta = self.get_meta(record_id)
        entry.update(trust=meta["trust"], lifecycle=meta["lifecycle"])
        return entry

    def _save_transform(self, record_id, doc, author, expected_version):
        saved = _storage_call(self._storage.put, "transforms", record_id, doc, author, expected_version)
        if record_id not in self._storage.ids(TRANSFORM_META):      # the first save of an id: untrusted and draft
            _storage_call(self._storage.put, TRANSFORM_META, record_id, {"trust": "untrusted", "lifecycle": "draft", "changed_by": author}, author)
        return saved

    def get_meta(self, record_id):
        self._known_transform(record_id)
        return _storage_call(self._storage.get, TRANSFORM_META, record_id)["doc"]

    def get_trust(self, record_id):
        return self.get_meta(record_id)["trust"]

    def get_lifecycle(self, record_id):
        return self.get_meta(record_id)["lifecycle"]

    def set_meta(self, record_id, author, **fields):
        """One new version of the meta record with these fields; `changed_by` is the author. A value outside the lists, a field of the wrong type or an unknown
        field is invalid/schema with the field as detail, and nothing changes."""
        meta = dict(self.get_meta(record_id))
        for name, value in fields.items():
            if name not in TRANSFORM_FIELDS:
                raise WorkflowLibraryError("invalid", rule="schema", detail=name)
            if TRANSFORM_FIELDS[name] is not None and type(value) is not TRANSFORM_FIELDS[name]:
                raise WorkflowLibraryError("invalid", rule="schema", detail=name)
        meta.update(fields, changed_by=author)
        _storage_call(self._storage.put, TRANSFORM_META, record_id, meta, author)      # trust and lifecycle values are checked by the table
        return meta

    def set_trust(self, record_id, trust, author):
        return {"trust": self.set_meta(record_id, author, trust=trust)["trust"]}

    def set_lifecycle(self, record_id, lifecycle, author, evidence=None):
        fields = {"lifecycle": lifecycle}
        if evidence is not None:
            fields["evidence"] = evidence
        return {"lifecycle": self.set_meta(record_id, author, **fields)["lifecycle"]}

    def _known_transform(self, record_id):
        if record_id not in self._storage.ids("transforms"):
            raise WorkflowLibraryError("not_found", detail=record_id)
