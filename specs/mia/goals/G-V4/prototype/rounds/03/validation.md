# Prototype validation: G-V4, round 03 (G-V4.GRAPHSTORE.CORE)

<!-- Written for the owner after CP15, filled during and after the session. The owner, not the agent, judges. One row per outcome of the scope. -->

Validated by: –
Date: – · Prototype state: branch prototype/g-v4 · Where it ran: –

## Outcomes
| Item | What the user tried (Given / When from the outcome) | What was observed | Result (met / partly / not met / not tried) | Finding |
|---|---|---|---|---|
| FR-57 | Given the worktree, run `./proto.sh proto_checks/cp13_check.py files` and then `... postgres`: a context graph and workflow graphs of every kind of step are saved, changed twice, read and listed; look at the lines "FR-57": three versions with who and when, nothing missing, identical on both | – | not tried | – |
| FR-60 | Given the same run: the lines "FR-60": `step.write` in a workflow graph and in a context graph have separate histories, the storage refuses a step without a graph in its ID | – | not tried | – |
| NFR-16 | Given `./proto.sh proto_checks/cp15_check.py files` and `... postgres`: every write position of a save, a move and a sync is tried; read the numbers ("10/10 whole, 10/10 finished") and the note on the sync (one position leaves an earlier complete version) | – | not tried | – |

## Beyond the outcomes
-

## What this changes
| Finding | Goes to | Change |
|---|---|---|
| – | – | – |

Hand-over to Plan: the requirements of the subgoal are written with these results as evidence.
