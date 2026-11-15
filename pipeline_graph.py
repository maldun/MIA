"""Pipeline-to-graph converter of the converted skills (G-V2.CONVERT, task T-CV-03d, A-123 P2 and P3, D-246, D-252).

`convert(pipeline, library_nodes, budget_seconds)` turns the JSON of a pipeline of library/pipelines into a workflow graph and returns
{"graph", "inputs", "result", "notes", "refused"}; it is pure (no store, no model, no network). `library_nodes` maps a node ID to its JSON.
- IDs: a call is the transform `step.<id>` (toolbox ID = the library node ID), a variable the data node `var.<name>` (written again: `var.<name>#2`, `#3`), a pipeline input
  `input.<field>`, a literal of a wire `literal.<step id>.<parameter>` (the literal is `value`), the settings of a construct `settings.<step id>`.
- A wire becomes edges into the step named by `as` (the parameter); the output becomes an edge `as: "output"` into the variable. A reference with a field (`$raw.claims`) goes
  through the pick transform `pick.<step>.<parameter>` (code.pick_field, settings node {"path": ...}, writes `var.pick.<step>.<parameter>`).
- A branch, map or loop is ONE node `control.<kind>` with the settings node {"construct", "node"}; it reads every variable its JSON refers to (edge name = variable name,
  `input.<field>` for an input) and writes every variable assigned inside as a new version. It is a master node when it contains a map or a loop (stop: the largest loop `max`
  as `max_repetitions` and `max_seconds` = the skill budget), otherwise a transform. A map without a bound of its own is noted.
- Steps and picks are chained in the order of the pipeline (graph_order.order_steps). What cannot be placed (a library node that is missing, an unknown node kind, an unknown
  variable, an ID used twice) refuses the whole pipeline: graph None, `refused` = [{"node", "reason"}] (the skill stays on the old runner, REQ-WFM-057).
"""
try:
    from .graph_order import order_steps
except ImportError:
    from graph_order import order_steps

CONSTRUCTS = ("branch", "map", "loop")
PICK = "code.pick_field"


def _children(node):
    return [c for key in ("body", "then", "else") for c in node.get(key) or [] if isinstance(c, dict)]


def _inside(node):
    """the nodes below a construct, depth first"""
    found = []
    for child in _children(node):
        found.append(child)
        found += _inside(child)
    return found


def _refs(value):
    """the references of a JSON text in order: `$name.path` strings and the `ref` of a condition"""
    found = []
    if isinstance(value, str):
        if value.startswith("$"):
            found.append(value[1:])
    elif isinstance(value, dict):
        for key, item in value.items():
            if key == "ref" and isinstance(item, str):
                found.append(item)
            else:
                found += _refs(item)
    elif isinstance(value, list):
        for item in value:
            found += _refs(item)
    return found


def _refusals(nodes, library_nodes):
    """the nodes of a list (and below) that cannot be placed"""
    refused = []
    for node in nodes:
        if "use" in node:
            if str(node["use"]).split("@")[0] not in library_nodes:
                refused.append({"node": node.get("id"), "reason": "the library node %s is not available" % node["use"]})
        elif node.get("kind") in CONSTRUCTS:
            refused += _refusals(_children(node), library_nodes)
        else:
            refused.append({"node": node.get("id"), "reason": "node kind %s has no place in a graph" % node.get("kind")})
    return refused


def convert(pipeline, library_nodes, budget_seconds):
    nodes = pipeline.get("nodes") or []
    ids = [n.get("id") for n in nodes]
    refused = _refusals(nodes, library_nodes) + [{"node": i, "reason": "the node ID is used twice"} for i in sorted(set(x for x in ids if ids.count(x) > 1))]
    if refused:
        return _result(None, {}, None, [], refused)

    graph_id = "%s@%s" % (pipeline["id"], pipeline["version"])
    versions = {}        # variable name -> number of writes so far
    inputs = {}          # field -> data node ID
    values = {}          # data node ID -> value (literals and settings)
    steps, notes = [], []
    settings_edges = set()   # (data node ID, step ID) pairs that are settings, not named inputs
    masters = {}         # step ID -> stop

    def variable_node(name):
        return "var.%s" % name if versions[name] == 1 else "var.%s#%d" % (name, versions[name])

    def write(name):
        versions[name] = versions.get(name, 0) + 1
        return variable_node(name)

    def source(name, step_id):
        """data node ID of the variable `name` (or an input field) or None when unknown"""
        if name == "input":
            return None
        if name.startswith("input."):
            field = name.split(".")[1]
            inputs.setdefault(field, "input." + field)
            return inputs[field]
        return variable_node(name) if name in versions else None

    def refuse(step_id, reason):
        refused.append({"node": step_id, "reason": reason})

    for node in nodes:
        step_id = "step." + node["id"]
        if "use" in node:
            reads = []
            for parameter, wire in (node.get("wire") or {}).items():
                if isinstance(wire, str) and wire.startswith("$"):
                    parts = wire[1:].split(".")
                    # a field of an input is `input.<field>`: the field is the variable, the rest of the path is picked
                    head = ".".join(parts[:2]) if parts[0] == "input" else parts[0]
                    path = ".".join(parts[2:] if parts[0] == "input" else parts[1:])
                    found = source(head, step_id)
                    if found is None:
                        refuse(node["id"], "the variable %s is not known at this step" % head)
                    elif path:
                        pick = "pick.%s.%s" % (node["id"], parameter)
                        settings = "settings." + pick
                        values[settings] = {"path": path}
                        out = "var." + pick
                        steps.append({"id": pick, "toolbox_id": PICK, "reads": [(found, "value"), (settings, None)], "writes": [(out, "output")]})
                        settings_edges.add((settings, pick))
                        reads.append((out, parameter))
                    else:
                        reads.append((found, parameter))
                else:
                    literal = "literal.%s.%s" % (node["id"], parameter)
                    values[literal] = wire
                    reads.append((literal, parameter))
            writes = [(write(node["output"]), "output")] if node.get("output") else []
            steps.append({"id": step_id, "toolbox_id": str(node["use"]).split("@")[0], "reads": reads, "writes": writes})
            continue
        # a construct: one node that reads what its JSON refers to and writes what it assigns
        below = _inside(node)
        assigned = []
        for item in [node] + below:
            if item.get("output") and item["output"] not in assigned:
                assigned.append(item["output"])
        local = {item["as"] for item in [node] + below if item.get("kind") == "map" and item.get("as")}
        reads, seen = [], set()
        for ref in _refs(node):
            head = ".".join(ref.split(".")[:2]) if ref.startswith("input.") else ref.split(".")[0]
            if head in seen:
                continue
            seen.add(head)
            found = source(head, step_id)
            if found is not None:
                reads.append((found, head))
            elif head not in assigned and head not in local:
                refuse(node["id"], "the variable %s is not known at this step" % head)
        settings = "settings." + step_id[len("step."):]
        values[settings] = {"construct": node["kind"], "node": node}
        settings_edges.add((settings, step_id))
        reads.append((settings, None))
        writes = [(write(name), name) for name in assigned]
        steps.append({"id": step_id, "toolbox_id": "control." + node["kind"], "reads": reads, "writes": writes})
        for item in [node] + below:
            if item.get("kind") == "map" and "max" not in item:
                notes.append("the map %s has no bound of its own: stopped by max_seconds only" % item["id"])
        if any(item.get("kind") in ("map", "loop") for item in [node] + below):
            stop = {"max_seconds": budget_seconds}
            maxima = [item["max"] for item in [node] + below if item.get("kind") == "loop" and "max" in item]
            if maxima:
                stop["max_repetitions"] = max(maxima)
            masters[step_id] = stop

    result = pipeline.get("result")
    result_node = source(result, "result") if result else None
    if result and result_node is None:
        refuse("result", "the result variable %s is never written" % result)
    all_ids = [s["id"] for s in steps]
    if len(all_ids) != len(set(all_ids)):
        refuse("graph", "a step ID is used twice after the names of the picks are made")
    if refused:
        return _result(None, {}, None, notes, refused)

    graph = order_steps(graph_id, steps)
    by_id = {n["id"]: n["data"] for n in graph["nodes"]}
    clash = [i for i in values if i in {s["id"] for s in steps}]
    if clash or len(by_id) != len(graph["nodes"]):
        return _result(None, {}, None, notes, [{"node": "graph", "reason": "a node ID is used twice: %s" % ", ".join(clash)}])
    for node_id, value in values.items():
        by_id[node_id]["value"] = value
    for step_id, stop in masters.items():
        by_id[step_id]["type"] = "master"
        by_id[step_id]["stop"] = stop
    for edge in graph["edges"]:
        if (edge["from"], edge["to"]) in settings_edges:
            edge["data"] = {"role": "settings"}
    return _result(graph, inputs, result_node, notes, [])


def _result(graph, inputs, result, notes, refused):
    return {"graph": graph, "inputs": inputs, "result": result, "notes": notes, "refused": refused}
