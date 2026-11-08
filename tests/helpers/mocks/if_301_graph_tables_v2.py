"""Mock of IF-301 v2, graph table definitions, record checks and conversion (protected; changes by amendment together with the suite).
Complexity 1: a fixed list of types (data, transform, master) and pure functions, nothing is stored (A-90, D-262 to D-266).

The real Graph tables (N-3.2) are written against the same suite. Interpretations this mock fixes where the contract text is silent
(each is a point for the amendment review, see specs/mia/goals/G-V2.STORE/handover-step4.md):
- definitions() stays the v1 result; the four new tables are in a new operation record_definitions() (owner's answer, 2026-11-07).
- types() is a dict {type ID: JSON schema}, keys sorted.
- a node object has the attributes `id` and the field names of its type (data: value, parameters; transform: toolbox_id; master: toolbox_id,
  stop, task); a context-graph node object is a ContextNode (id, type, fields).
- an edge has no type; its JSON field `data` must be an object, else schema_break with the detail `data`.
- the type of a context-graph node is in `data["type"]`, as for a workflow node.
- a field of a node's JSON field that the schema of its type does not list is schema_break naming that field, in check_record and in to_object (A-93); the
  detail is the first path in text order, a missing key counting at the path of its object, an extra field at its own path.
- context_nodes and context_edges (A-98): the Storage layer checks the shape only; with categories a node is checked as before; edge ends and header members of a context
  graph are looked up in stored["context_nodes"] and stored["context_edges"]; a record nested deeper than 200 levels and a category with an invalid schema are schema_break.
- the detail of a schema_break is the path of the field with dots; a missing required key is named as the key.
- the document form carries the other fields of a node flat beside id and kind and the JSON field of an edge under `data`; an edge of a
  v1 document without an ID gets e1, e2, ... in order.
"""
import copy
from dataclasses import dataclass, field

import jsonschema

try:
    from . import graph_rules
except ImportError:  # plain import (single test run as a script)
    import graph_rules

V1_TABLES = {"workflows": {"versioned": True, "deletable": False}, "context_graphs": {"versioned": True, "deletable": False}}
NEW_TABLES = ("graph_nodes", "graph_edges", "graphs", "skills", "context_nodes", "context_edges")
MAX_DEPTH = 200      # a record nested deeper than this is schema_break `data` (REQ-GTB-027)
MAX_VALUES = 100000  # a record with more values (every path counted) is schema_break `data` (REQ-GTB-028)

_STOP = {"type": "object",
         "properties": {"max_repetitions": {"type": "integer", "minimum": 1}, "max_seconds": {"type": "number", "exclusiveMinimum": 0}},
         "anyOf": [{"required": ["max_repetitions"]}, {"required": ["max_seconds"]}]}
_MEMBERS = {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string"}, "version": {"type": "integer", "minimum": 1}},
                                       "required": ["id", "version"]}}

# the fixed list of workflow node types: the JSON field of a node names the type ID (REQ-GTB-009, REQ-GTB-011)
TYPE_SCHEMAS = {
    "data": {"type": "object", "properties": {"type": {"const": "data"}, "value": {}, "parameters": {"type": "object"}}, "required": ["type"],
             "additionalProperties": False},
    "master": {"type": "object", "properties": {"type": {"const": "master"}, "toolbox_id": {"type": "string"}, "stop": _STOP, "task": {"type": "object"}},
               "required": ["type", "toolbox_id", "stop"], "additionalProperties": False},
    "transform": {"type": "object", "properties": {"type": {"const": "transform"}, "toolbox_id": {"type": "string"}}, "required": ["type", "toolbox_id"], "additionalProperties": False},
}
EDGE_SCHEMA = {"type": "object"}
HEADER_SCHEMA = {"type": "object",
                 "properties": {"kind": {"enum": ["workflow", "context"]}, "context_graph_id": {"type": "string"}, "testbench_id": {"type": "string"},
                                "description": {"type": "string"}, "nodes": _MEMBERS, "edges": _MEMBERS},
                 "required": ["kind", "context_graph_id", "testbench_id", "description", "nodes", "edges"]}
SKILL_SCHEMA = {"type": "object",
                "properties": {"command": {"type": "string"}, "workflow_graph_id": {"type": "string"}, "context_graph_id": {"type": "string"}},
                "required": ["command", "workflow_graph_id", "context_graph_id"]}
_VALIDATORS = {}


def _validator(schema):
    key = id(schema)
    if key not in _VALIDATORS:
        _VALIDATORS[key] = jsonschema.Draft202012Validator(schema)
    return _VALIDATORS[key]


def _extra(error):
    """The first additional field of an additionalProperties error, in sorted order (REQ-GTB-022)."""
    return min(k for k in error.instance if k not in error.schema.get("properties", {}))


def _broken_path(schema, data):
    """The path of the first field that breaks the schema, or None. The path is the validator's error path (TR-GTB-003); for a missing
    required key it is that key, appended to the path of the object that lacks it; for an additional field it is that field (A-93). The
    first is the first in the order of these paths as text, a missing key counting at the path of its object."""
    def order(error):
        return [str(p) for p in error.absolute_path] + ([_extra(error)] if error.validator == "additionalProperties" else [])

    errors = sorted(_validator(schema).iter_errors(data), key=order)
    if not errors:
        return None
    error = errors[0]
    path = list(error.absolute_path)
    if error.validator == "required":
        path.append([k for k in error.validator_value if k not in error.instance][0])
    elif error.validator == "additionalProperties":
        path.append(_extra(error))
    return ".".join(str(p) for p in path) or "data"


@dataclass
class DataNode:
    id: str
    value: object = None
    parameters: dict = field(default_factory=dict)
    type = "data"


@dataclass
class TransformNode:
    id: str
    toolbox_id: str = ""
    type = "transform"


@dataclass
class MasterNode:
    id: str
    toolbox_id: str = ""
    stop: dict = field(default_factory=dict)
    task: object = None
    type = "master"


@dataclass
class ContextNode:
    id: str
    type: str
    fields: dict = field(default_factory=dict)


def _dup(members):
    ids = [m["id"] for m in members]
    return len(ids) != len(set(ids))


def _too_deep(value):
    """True when the value is nested deeper than MAX_DEPTH levels (the record is level 1) or has more than MAX_VALUES values (a value reached by two paths counts twice);
    iterative, so the check itself cannot hit the recursion limit, and it stops at MAX_VALUES + 1 values, so a record that shares sub-objects cannot make it exponential."""
    stack, seen = [(value, 1)], 0
    while stack:
        item, depth = stack.pop()
        seen += 1
        if depth > MAX_DEPTH or seen > MAX_VALUES:
            return True
        children = item.values() if isinstance(item, dict) else item if isinstance(item, list) else ()
        stack.extend((child, depth + 1) for child in children)
    return False


def _bad_schema(schema):
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.SchemaError:
        return True
    return False


def _check_context(table, record, data, categories, stored):
    """context_nodes and context_edges (A-98): the shape; with categories the type and schema of a node; the ends of an edge in the stored context nodes."""
    if table == "context_nodes":
        type_id = data.get("type")
        if not isinstance(type_id, str) or not type_id:
            return {"rule": "schema_break", "detail": "type"}
        if categories is None:
            return None
        if type_id not in categories:
            return {"rule": "unknown_type", "detail": type_id}
        if _bad_schema(categories[type_id]):
            return {"rule": "schema_break", "detail": "type"}
        broken = _broken_path(categories[type_id], data)
        return {"rule": "schema_break", "detail": broken} if broken else None
    if stored is not None:
        for end in (record["from"], record["to"]):
            if end not in stored.get("context_nodes", {}):
                return {"rule": "unknown_endpoint", "detail": end}
    return None


def _check(table, record, categories, stored, record_id=None):
    if not isinstance(record, dict):
        return {"rule": "record_identity", "detail": "record"}
    if not isinstance(record.get("id"), str) or not record["id"]:
        return {"rule": "record_identity", "detail": "id"}
    if record_id is not None and record_id != record["id"]:      # the record is stored under the ID it carries (REQ-GTB-021)
        return {"rule": "record_identity", "detail": "id"}
    if _too_deep(record):                                        # cannot be checked (REQ-GTB-027)
        return {"rule": "schema_break", "detail": "data"}
    if table in ("graph_edges", "context_edges"):
        for end in ("from", "to"):
            if not isinstance(record.get(end), str) or not record[end]:
                return {"rule": "record_identity", "detail": end}
    data = record.get("data")
    if not isinstance(data, dict):
        return {"rule": "schema_break", "detail": "data"}
    if table in ("context_nodes", "context_edges"):
        return _check_context(table, record, data, categories, stored)
    if table in ("graph_nodes", "graph_edges"):
        schema = EDGE_SCHEMA
        if table == "graph_nodes":
            type_id = data.get("type")
            if categories is not None:
                if type_id not in categories:
                    return {"rule": "unknown_type", "detail": str(type_id)}
                if _bad_schema(categories[type_id]):
                    return {"rule": "schema_break", "detail": "type"}
                schema = categories[type_id]
            elif type_id not in TYPE_SCHEMAS:
                return {"rule": "unknown_type", "detail": str(type_id)} if "type" in data else {"rule": "schema_break", "detail": "type"}
            else:
                schema = TYPE_SCHEMAS[type_id]
        broken = _broken_path(schema, data)
        if broken:
            return {"rule": "schema_break", "detail": broken}
        if table == "graph_edges" and stored is not None:
            for end in (record["from"], record["to"]):
                if end not in stored.get("nodes", {}):
                    return {"rule": "unknown_endpoint", "detail": end}
        return None
    broken = _broken_path(HEADER_SCHEMA if table == "graphs" else SKILL_SCHEMA, data)
    if broken:
        return {"rule": "schema_break", "detail": broken}
    if table == "graphs":
        for key in ("nodes", "edges"):
            if _dup(data[key]):
                return {"rule": "record_identity", "detail": key}
        if stored is not None:
            for key in ("nodes", "edges"):
                where = ("context_" + key) if data["kind"] == "context" else key        # a context header looks in the context tables (REQ-GTB-026)
                for member in data[key]:
                    if member["version"] not in stored.get(where, {}).get(member["id"], []):
                        return {"rule": "unknown_member", "detail": member["id"]}
    return None


def _to_object(record, categories):
    refused = _check("graph_nodes", record, categories, None)
    if refused:
        return {"refused": refused}
    data, type_id = record["data"], record["data"]["type"]
    if categories is not None:
        return {"object": ContextNode(record["id"], type_id, {k: copy.deepcopy(v) for k, v in data.items() if k != "type"})}
    if type_id == "data":
        return {"object": DataNode(record["id"], copy.deepcopy(data.get("value")), copy.deepcopy(data.get("parameters", {})))}
    if type_id == "transform":
        return {"object": TransformNode(record["id"], data["toolbox_id"])}
    return {"object": MasterNode(record["id"], data["toolbox_id"], copy.deepcopy(data["stop"]), copy.deepcopy(data.get("task")))}


class GraphTablesV2Mock:
    def definitions(self):
        """Exactly as v1 (the v1 suite and REQ-GTB-001 say exactly two tables); the record tables are in record_definitions()."""
        return {t: dict(d) for t, d in V1_TABLES.items()}

    def record_definitions(self):
        """The four record tables, all versioned and not deletable; the Storage layer keeps the versions from this flag (REQ-GTB-013)."""
        return {t: {"versioned": True, "deletable": False} for t in NEW_TABLES}

    def validate(self, table, doc):
        if table not in V1_TABLES:
            raise ValueError("not a graph table: %s" % (table,))
        broken = graph_rules.violation(doc)
        return None if broken is None else {"rule": broken[0], "detail": broken[1]}

    def types(self):
        return {type_id: copy.deepcopy(TYPE_SCHEMAS[type_id]) for type_id in sorted(TYPE_SCHEMAS)}

    def check_record(self, table, record, categories=None, stored=None, record_id=None):
        if table not in NEW_TABLES:
            raise ValueError("not a record table of the graphs: %s" % (table,))
        try:
            return _check(table, record, categories, stored, record_id)
        except Exception:  # any input gives a rule or None, never an exception (A-60)
            return {"rule": "record_identity", "detail": "record"}

    def to_object(self, record, categories=None):
        try:
            return _to_object(record, categories)
        except Exception:
            return {"refused": {"rule": "record_identity", "detail": "record"}}

    def to_record(self, obj):
        if isinstance(obj, ContextNode):
            return {"id": obj.id, "data": dict({"type": obj.type}, **copy.deepcopy(obj.fields))}
        if isinstance(obj, DataNode):
            data = {"type": "data", "parameters": copy.deepcopy(obj.parameters)}
            if obj.value is not None:
                data["value"] = copy.deepcopy(obj.value)
        elif isinstance(obj, TransformNode):
            data = {"type": "transform", "toolbox_id": obj.toolbox_id}
        elif isinstance(obj, MasterNode):
            data = {"type": "master", "toolbox_id": obj.toolbox_id, "stop": copy.deepcopy(obj.stop)}
            if obj.task is not None:
                data["task"] = copy.deepcopy(obj.task)
        else:
            raise TypeError("not an object of a listed class")
        return {"id": obj.id, "data": data}

    def to_document(self, nodes, edges):
        doc_nodes = []
        for node in nodes:
            type_id = node["data"]["type"]
            if type_id == "master":
                return {"refused": {"rule": "not_representable", "detail": node["id"]}}
            if type_id not in ("data", "transform"):
                return {"refused": {"rule": "unknown_type", "detail": str(type_id)}}
            rest = {k: copy.deepcopy(v) for k, v in node["data"].items() if k != "type"}
            doc_nodes.append(dict({"id": node["id"], "kind": "process" if type_id == "transform" else "data"}, **rest))
        doc_edges = [{"id": e["id"], "from": e["from"], "to": e["to"], "data": copy.deepcopy(e["data"])} for e in edges]
        return {"document": {"nodes": doc_nodes, "edges": doc_edges}}

    def from_document(self, doc):
        nodes, edges = doc.get("nodes") if isinstance(doc, dict) else None, doc.get("edges") if isinstance(doc, dict) else None
        if not isinstance(nodes, list) or not isinstance(edges, list):
            return {"refused": {"rule": "node_identity", "detail": "nodes and edges must be lists"}}
        records = []
        for node in nodes:
            kind = node.get("kind") if isinstance(node, dict) else None
            if kind not in ("process", "data"):
                return {"refused": {"rule": "node_identity", "detail": node.get("id") if isinstance(node, dict) else None}}
            rest = {k: copy.deepcopy(v) for k, v in node.items() if k not in ("id", "kind")}
            records.append({"id": node["id"], "data": dict({"type": "transform" if kind == "process" else "data"}, **rest)})
        out = [{"id": e.get("id", "e%d" % (i + 1)), "from": e["from"], "to": e["to"], "data": copy.deepcopy(e.get("data", {}))}
               for i, e in enumerate(edges)]
        return {"nodes": records, "edges": out}
