"""
The tables of workflows (library entries) and context graphs and their validation: IF-301, provided to the Storage layer (REQ-GTB-001, REQ-GTB-003).

Both tables are versioned and never deleted (an edit is a new version). A document is valid when graph_rules finds no broken rule, so the Storage
layer refuses a bad edit on write (TB-edit, second line of defence behind the Backend).
"""
import copy
import math
from dataclasses import dataclass, field

import jsonschema

try:
    from . import graph_rules
except ImportError:  # used as plain script / in tests
    import graph_rules

TABLES = {"workflows": {"versioned": True, "deletable": False}, "context_graphs": {"versioned": True, "deletable": False}}


def definitions():
    return {table: dict(rules) for table, rules in TABLES.items()}


def validate(table, doc):
    """None for a valid document, else {"rule", "detail"} of the first broken rule. A table that is not defined here is a ValueError (ask IF-302)."""
    if table not in TABLES:
        raise ValueError("not a graph table: %s" % (table,))
    broken = graph_rules.violation(doc)
    return None if broken is None else {"rule": broken[0], "detail": broken[1]}


# IF-301 v2 (A-90, G-V2.STORE): the graphs as separate records (REQ-GTB-005 to REQ-GTB-020).
RECORD_TABLES = ("graph_nodes", "graph_edges", "graphs", "skills")

_STOP = {"type": "object",
         "properties": {"max_repetitions": {"type": "integer", "minimum": 1}, "max_seconds": {"type": "number", "exclusiveMinimum": 0}},
         "anyOf": [{"required": ["max_repetitions"]}, {"required": ["max_seconds"]}]}
_MEMBERS = {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "version": {"type": "integer", "minimum": 1}},
                                       "required": ["id", "version"]}}
# The fixed list of workflow node types (REQ-GTB-009, REQ-GTB-011); a new type is an amendment of IF-301. The JSON field of a node names its type.
TYPE_SCHEMAS = {
    "data": {"type": "object", "properties": {"type": {"const": "data"}, "value": {}, "parameters": {"type": "object"}}, "required": ["type"]},
    "master": {"type": "object", "properties": {"type": {"const": "master"}, "toolbox_id": {"type": "string"}, "stop": _STOP, "task": {"type": "object"}},
               "required": ["type", "toolbox_id", "stop"]},
    "transform": {"type": "object", "properties": {"type": {"const": "transform"}, "toolbox_id": {"type": "string"}}, "required": ["type", "toolbox_id"]},
}
_RECORD_SCHEMAS = {
    "graph_edges": {"type": "object"},
    "graphs": {"type": "object",
               "properties": {"kind": {"enum": ["workflow", "context"]}, "context_graph_id": {"type": "string"}, "testbench_id": {"type": "string"},
                              "description": {"type": "string"}, "nodes": _MEMBERS, "edges": _MEMBERS},
               "required": ["kind", "context_graph_id", "testbench_id", "description", "nodes", "edges"]},
    "skills": {"type": "object",
               "properties": {"command": {"type": "string"}, "workflow_graph_id": {"type": "string"}, "context_graph_id": {"type": "string"}},
               "required": ["command", "workflow_graph_id", "context_graph_id"]},
}
_validators = {}


def record_definitions():
    """The four record tables, versioned and never deleted; the Storage layer keeps the versions from this (REQ-GTB-013)."""
    return {table: {"versioned": True, "deletable": False} for table in RECORD_TABLES}


def types():
    """The type IDs of the fixed list, sorted, each with its JSON schema."""
    return {type_id: copy.deepcopy(TYPE_SCHEMAS[type_id]) for type_id in sorted(TYPE_SCHEMAS)}


def _broken_path(schema, data):
    """The path of the first field that breaks the schema, as jsonschema names it (TR-GTB-003), or None. A missing required key is named by that key."""
    key = id(schema)
    if key not in _validators:                  # built once: 500 node and 500 edge records must be checked in 500 ms
        _validators[key] = jsonschema.Draft202012Validator(schema)
    errors = sorted(_validators[key].iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path])
    if not errors:
        return _non_finite_path(data)
    path = list(errors[0].absolute_path)
    if errors[0].validator == "required":
        path.append(next(k for k in errors[0].validator_value if k not in errors[0].instance))
    return ".".join(str(p) for p in path) or "data"


def _non_finite_path(value, path=()):
    """The path of the first NaN or infinity in the data, or None: JSON has no such number and a schema's bounds let it pass (as in v1, A-60)."""
    if isinstance(value, float) and not math.isfinite(value):
        return ".".join(path)
    items = value.items() if isinstance(value, dict) else enumerate(value) if isinstance(value, list) else ()
    return next((found for found in (_non_finite_path(v, path + (str(k),)) for k, v in items) if found is not None), None)


def _refusal(rule, detail):
    return {"rule": rule, "detail": detail}


def _node_schema(data, categories):
    """(schema, None) for a node's JSON field, or (None, refusal): the type comes from the fixed list, for a context graph from its categories."""
    if "type" not in data:
        return None, _refusal("schema_break", "type")
    known = TYPE_SCHEMAS if categories is None else categories
    if not isinstance(data["type"], str) or data["type"] not in known:
        return None, _refusal("unknown_type", str(data["type"]))
    return known[data["type"]], None


def _check_members(data, stored):
    """unknown_member for a header member (node or edge) whose version is not stored; a member named twice is record_identity."""
    for key, kind in (("nodes", "nodes"), ("edges", "edges")):
        ids = [member["id"] for member in data[key]]
        if len(ids) != len(set(ids)):
            return _refusal("record_identity", key)
        for member in data[key]:
            if stored is not None and member["version"] not in stored.get(kind, {}).get(member["id"], []):
                return _refusal("unknown_member", member["id"])
    return None


def _check(table, record, categories, stored, record_id=None):
    if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not record["id"]:
        return _refusal("record_identity", "id" if isinstance(record, dict) else "record")
    if record_id is not None and record_id != record["id"]:     # a header pins by the ID inside, the storage finds by the record ID (REQ-GTB-021)
        return _refusal("record_identity", "id")
    if table == "graph_edges":
        for end in ("from", "to"):
            if not isinstance(record.get(end), str) or not record[end]:
                return _refusal("record_identity", end)
    data = record.get("data")
    if not isinstance(data, dict):
        return _refusal("schema_break", "data")
    schema = _RECORD_SCHEMAS.get(table)
    if table == "graph_nodes":
        schema, refused = _node_schema(data, categories)
        if refused:
            return refused
    broken = _broken_path(schema, data)
    if broken:
        return _refusal("schema_break", broken)
    if table == "graph_edges" and stored is not None:
        for end in (record["from"], record["to"]):
            if end not in stored.get("nodes", {}):
                return _refusal("unknown_endpoint", end)
    return _check_members(data, stored) if table == "graphs" else None


def check_record(table, record, categories=None, stored=None, record_id=None):
    """None, or {"rule", "detail"} of the first broken rule of a record of graph_nodes, graph_edges, graphs or skills (REQ-GTB-010, 011, 016, 019, 020, 021).
    `record_id` is the ID the caller writes the record under: when given and different from the `id` inside the record, record_identity names `id`.
    Pure: it stores nothing and changes neither the record nor `stored`. Any record gives a rule or None, never an exception (as A-60);
    a table that is not one of the four is a ValueError."""
    if table not in RECORD_TABLES:
        raise ValueError("not a record table of the graphs: %s" % (table,))
    try:
        return _check(table, record, categories, stored, record_id)
    except Exception:                           # a malformed record (for example a header whose members are not objects) is refused, not raised
        return _refusal("record_identity", "record")


@dataclass
class DataNode:
    id: str
    value: object = None
    parameters: dict = field(default_factory=dict)


@dataclass
class TransformNode:
    id: str
    toolbox_id: str = ""


@dataclass
class MasterNode:
    id: str
    toolbox_id: str = ""
    stop: dict = field(default_factory=dict)
    task: object = None


@dataclass
class ContextNode:
    """A node of a context graph: its category (type), and the rest of its JSON field."""
    id: str
    type: str
    fields: dict = field(default_factory=dict)


# the class of each type ID (REQ-GTB-009): the type ID alone decides, so a new type is a new class here and a new schema above
CLASSES = {"data": DataNode, "transform": TransformNode, "master": MasterNode}


def to_object(record, categories=None):
    """{"object": obj} for a node record, or {"refused": {"rule", "detail"}} with the rule of check_record (REQ-GTB-009, REQ-GTB-010).
    Nothing in the record is executed: a task definition is data only (REQ-GTB-008)."""
    refused = check_record("graph_nodes", record, categories=categories)
    if refused:
        return {"refused": refused}
    data = copy.deepcopy(record["data"])
    if categories is not None:
        return {"object": ContextNode(record["id"], data.pop("type"), data)}
    type_id = data.pop("type")
    return {"object": CLASSES[type_id](record["id"], **data)}


def to_record(obj):
    """The node record of an object of a listed class; to_object(to_record(x)) equals x (REQ-GTB-014). An optional field that is None is left out."""
    if isinstance(obj, ContextNode):
        return {"id": obj.id, "data": dict({"type": obj.type}, **copy.deepcopy(obj.fields))}
    type_id = next((t for t, cls in CLASSES.items() if type(obj) is cls), None)
    if type_id is None:
        raise TypeError("not an object of a listed class: %r" % (obj,))
    data = {"type": type_id}
    data.update({name: copy.deepcopy(value) for name, value in vars(obj).items() if name != "id" and value is not None})
    if type_id == "data":
        data.setdefault("parameters", {})
    return {"id": obj.id, "data": data}


# the type of a record and the kind of the same node in the v1 document (REQ-GTB-015); a master node has no document form
_KIND_OF_TYPE = {"data": "data", "transform": "process"}
_TYPE_OF_KIND = {kind: type_id for type_id, kind in _KIND_OF_TYPE.items()}


def to_document(nodes, edges):
    """The v1 document {"nodes", "edges"} of node and edge records of one workflow, or {"refused": {"rule", "detail"}} (REQ-GTB-015).
    transform becomes kind process, data stays data; the other fields of a node go flat beside id and kind, the JSON field of an edge under
    `data` with its id, so from_document gives the records back. A master node is not_representable, any other type unknown_type."""
    document_nodes = []
    for node in nodes:
        type_id = node["data"]["type"]
        if type_id == "master":
            return {"refused": _refusal("not_representable", node["id"])}
        if type_id not in _KIND_OF_TYPE:
            return {"refused": _refusal("unknown_type", str(type_id))}
        rest = {name: copy.deepcopy(value) for name, value in node["data"].items() if name != "type"}
        document_nodes.append(dict({"id": node["id"], "kind": _KIND_OF_TYPE[type_id]}, **rest))
    document_edges = [{"id": e["id"], "from": e["from"], "to": e["to"], "data": copy.deepcopy(e["data"])} for e in edges]
    return {"document": {"nodes": document_nodes, "edges": document_edges}}


def from_document(doc):
    """{"nodes": [...], "edges": [...]} (records) of a v1 document: process becomes transform, data stays data. An edge without an id gets e1, e2, ...
    in order. The records are not checked: a v1 process node has no toolbox_id, so its record breaks the schema of transform until one is added."""
    nodes, edges = (doc.get("nodes"), doc.get("edges")) if isinstance(doc, dict) else (None, None)
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return {"refused": _refusal("node_identity", "nodes and edges must be lists")}
    records = []
    for node in nodes:
        kind = node.get("kind") if isinstance(node, dict) else None
        if kind not in _TYPE_OF_KIND:
            return {"refused": _refusal("node_identity", node.get("id") if isinstance(node, dict) else None)}
        rest = {name: copy.deepcopy(value) for name, value in node.items() if name not in ("id", "kind")}
        records.append({"id": node["id"], "data": dict({"type": _TYPE_OF_KIND[kind]}, **rest)})
    try:
        edge_records = [{"id": e.get("id", "e%d" % (n + 1)), "from": e["from"], "to": e["to"], "data": copy.deepcopy(e.get("data", {}))}
                        for n, e in enumerate(edges)]
    except (AttributeError, KeyError, TypeError):
        return {"refused": _refusal("node_identity", "an edge needs from and to")}
    return {"nodes": records, "edges": edge_records}
