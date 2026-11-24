"""The random workflow graphs of G-V4.GRAPHAPI.RUN (TR-RUN-003, protected, changed only by an amendment).

random_graphs(): 500 workflow graphs from random.Random(7), 2 to 8 steps of the types data, transform and master, connections between any two steps of the
graph, self loops and parallel connections included (the rules refuse them, the loader must keep them). Only step IDs that exist are drawn, so the broken
rules are the structural ones the graph builds by chance. acyclic() tells whether `order_of` reaches every step; the count of acyclic graphs is stored
with the oracle (tests/helpers/run_oracle.json), so a changed generator cannot make a check easier.
"""
import random

from rules_graphs import connection, data, graph, master, transform

SEED, COUNT = 7, 500
MAKERS = {"data": data, "transform": transform, "master": master}


def random_graphs():
    rng = random.Random(SEED)
    graphs = []
    for index in range(COUNT):
        size = rng.randint(2, 8)
        nodes = [MAKERS[rng.choice(["data", "transform", "master"])]("s%d" % i) for i in range(size)]
        ids = [n["id"] for n in nodes]
        edges = [connection("e%d" % (k + 1), rng.choice(ids), rng.choice(ids)) for k in range(rng.randint(0, 2 * size))]
        graphs.append(graph(nodes, edges, kind="workflow", graph_id="random-%03d" % index))
    return graphs


def acyclic(graph_dict, order_of):
    return len(order_of(graph_dict)) == len(graph_dict["nodes"])
