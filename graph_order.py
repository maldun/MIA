"""Order rule of the converted skills (G-V2.CONVERT, task T-CV-03c, A-123 P4, D-251).

The old runner runs the steps of a pipeline in the order of the pipeline; a graph orders independent nodes by what they read. `order_steps(graph_id, steps)` builds a graph
of data and transform nodes from an ordered list of steps and lets each step read an extra data node written by the step before it, over an edge with `role: "order"`, so
that `order_of` gives the listed order. The runner uses such an edge for the order only (REQ-RUN-035).
A step is {"id", "toolbox_id", "reads": [(data node id, name)], "writes": [(data node id, name)]}; the name is the `as` field of the edge.
Every step after the first is chained, also when data flow already forces the order: simple, and the graph rules (alternation, one writer per data node) hold either way.
The input is not changed.
"""


def order_steps(graph_id, steps):
    nodes, edges = {}, []

    def data(node_id):
        nodes.setdefault(node_id, {"id": node_id, "data": {"type": "data"}})

    def edge(start, end, **fields):
        edges.append({"id": "%s>%s" % (start, end), "from": start, "to": end, "data": fields})

    previous = None
    for step in steps:
        nodes[step["id"]] = {"id": step["id"], "data": {"type": "transform", "toolbox_id": step["toolbox_id"]}}
        for node_id, name in step["reads"]:
            data(node_id)
            edge(node_id, step["id"], **{"as": name})
        for node_id, name in step["writes"]:
            data(node_id)
            edge(step["id"], node_id, **{"as": name})
        if previous is not None:
            # the extra data node is written by the previous step and only read for the order
            order_id = "order-" + previous
            data(order_id)
            edge(previous, order_id)
            edge(order_id, step["id"], role="order")
        previous = step["id"]
    return {"id": graph_id, "context_graph_id": "ctx-" + graph_id, "testbench_id": "", "description": "steps in the listed order",
            "nodes": list(nodes.values()), "edges": edges}
