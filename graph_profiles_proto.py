"""PROTOTYPE round 05 CP21 (G-V4.EDIT, FR-92, D-403, D-404, D-471 (2), D-602): the editor profile of each kind of graph.

The registry of kinds is the product's (graph_rule_set.kinds(): the rule set and whether a kind can run). This module adds, per kind, what the
editor needs to build its forms without knowing any kind itself:
  editable          whether the editor may change a graph of this kind (context: not in EDIT, D-602), with `reason` when not
  node_types        [{type, name, fields, start, need_one_of?}]: the types of node, their known fields and the content of a new node
  connection_fields the known fields of a connection
A field is {name, label, input, ...}: `name` is a path into the node's `data` ("stop.max_seconds" is data["stop"]["max_seconds"]); `input` is
  text      a line of text; `required` true: not empty
  json      any JSON value; `object` true: a JSON object
  number    a number above 0 (`above`); `whole` true: a whole number
  choice    one of a list: `options` (fixed), or `list` = "toolbox" with `filter` (the toolbox answer, entries matching every key of the filter);
            `required` true: one must be chosen; `keep_unknown` true: a stored value outside the list stays choosable, marked
`need_one_of` [[field names]]: at least one of the named fields has a value (a loop-controlling step needs a stop limit).
Messages for the owner are part of the profile only where a field needs its own words (`message`); the page has the general ones.
"""
try:
    from . import graph_rule_set
except ImportError:
    import graph_rule_set

_WORKFLOW = {
    "editable": True,
    "node_types": [
        {"type": "data", "name": "data step", "start": {"type": "data"},
         "fields": [{"name": "value", "label": "value (JSON)", "input": "json"},
                    {"name": "parameters", "label": "parameters (JSON object)", "input": "json", "object": True}]},
        {"type": "transform", "name": "processing step", "start": {"type": "transform", "toolbox_id": ""},
         "fields": [{"name": "toolbox_id", "label": "tool (toolbox entry)", "input": "choice", "list": "toolbox", "filter": {"controller": False},
                     "required": True, "keep_unknown": True, "message": "A processing step needs a tool."}]},
        {"type": "master", "name": "loop-controlling step", "start": {"type": "master", "toolbox_id": "", "stop": {"max_repetitions": 1}},
         "fields": [{"name": "toolbox_id", "label": "tool (toolbox entry)", "input": "choice", "list": "toolbox", "filter": {"controller": True},
                     "required": True, "keep_unknown": True, "message": "A processing step needs a tool."},
                    {"name": "stop.max_repetitions", "label": "stop after repetitions", "input": "number", "above": 0, "whole": True},
                    {"name": "stop.max_seconds", "label": "stop after seconds", "input": "number", "above": 0}],
         "need_one_of": [{"fields": ["stop.max_repetitions", "stop.max_seconds"],
                          "message": "A loop-controlling step needs a limit: repetitions or seconds."}]},
    ],
    "connection_fields": [{"name": "role", "label": "role", "input": "choice", "options": ["", "settings", "order", "code"]},
                          {"name": "as", "label": "name", "input": "text"}],
}
_CONTEXT = {"editable": False, "reason": "Editing context graphs comes with G-V4.CONTEXT.", "node_types": [], "connection_fields": []}
PROFILES = {"workflow": _WORKFLOW, "context": _CONTEXT}


def kinds_answer():
    """the answer of GET /api/v2/kinds: per kind of the registry its rules and whether it runs (graph_rule_set), and its editor profile.
    A kind of the registry without a profile is answered as not editable, so a new kind never opens an editor that knows nothing about it."""
    out = {}
    for kind, entry in graph_rule_set.kinds().items():
        profile = PROFILES.get(kind, {"editable": False, "reason": "The editor has no description of this kind of graph.", "node_types": [], "connection_fields": []})
        out[kind] = {"rules": list(entry["rules"]), "runs": entry["runs"], **profile}
    return {"kinds": out, "unknown_reason": "The program does not know this kind of graph."}
