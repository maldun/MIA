"""Order rule of the converted skills (G-V2.CONVERT, task T-CV-03c, A-123 P4, D-251): STUB until T-CV-03c.

The old runner runs the steps of a pipeline in the order of the pipeline; a graph orders independent nodes by what they read. `order_steps(graph_id, steps)` builds a graph
of data and transform nodes from an ordered list of steps and lets each step read an extra data node written by the step before it, over an edge with `role: "order"`, so
that `order_of` gives the listed order. The runner uses such an edge for the order only (REQ-RUN-035).
A step is {"id", "toolbox_id", "reads": [(data node id, name)], "writes": [(data node id, name)]}; the name is the `as` field of the edge.
The stub returns nothing, so the acceptance tests fail on an assertion.
"""


def order_steps(graph_id, steps):
    """STUB (T-CV-03c)"""
    return None
