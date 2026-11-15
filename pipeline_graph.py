"""Pipeline-to-graph converter of the converted skills (G-V2.CONVERT, task T-CV-03d, A-123 P2 and P3, D-246): STUB until T-CV-03d.

`convert(pipeline, library_nodes, budget_seconds)` turns the JSON of a pipeline of library/pipelines into a workflow graph of data, transform and master nodes (stages are
transforms, a construct with a loop or an unbounded map is a master node with a stop criterion), or names the nodes it cannot place. The interface is the one the red tests of
T-CV-03d assume (tests/acceptance/test_pipeline_graph.py, docstring). The stub returns nothing, so the acceptance tests fail on an assertion.
"""


def convert(pipeline, library_nodes, budget_seconds):
    """STUB (T-CV-03d)"""
    return None
