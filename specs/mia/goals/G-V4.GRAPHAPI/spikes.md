# Spike: does a networkx graph carry everything the runner needs? (G-V4.GRAPHAPI)

Throwaway, 2026-11-20, scratch code only (networkx 3.7 installed with `pip --target` into the session scratchpad, not into the venv or `requirements.txt`). Cases: the 15 converted skill graphs and 500 random small graphs (seed 7, with self loops). No model used.

| Question | Result |
|---|---|
| Does a `MultiDiGraph` built from the stored graph keep every node and edge attribute (type, stop, role, `as`, settings values)? | 15 of 15 graphs, identical |
| Does `topological_sort` give an order in which every edge points forward and every node appears? | 15 of 15 |
| Would a plain `DiGraph` lose edges? | none in these 15 graphs; but two edges between the same two nodes (F6) are not refused by any rule, so the loader must use `MultiDiGraph` (edge key = edge id) |
| Does networkx agree with `find_cycle` on cycle yes or no? | 500 of 500 random graphs |

## What it means
- The loader is a few lines (nodes with their `data`, edges keyed by id), and order and cycle check come from the library instead of `find_cycle` and `order_of`.
- Not covered: the equivalence of a full run (needs the stage functions and models), the rules R1 to R5 on the graph, master nodes, performance (graphs have at most 54 nodes).
- The decision of the owner about code in graphs (D-360) needs the threat entry in `research.md` before Plan.
