"""STUB (G-V4.GRAPHAPI.RULES, Plan step 4): the rule set of graphs, IF-301 v4 (A-170) - registry of kinds, rule report, run check.

Only the names exist, so the red acceptance tests import and fail on their assertions; task T-01 of
specs/mia/goals/G-V4.GRAPHAPI.RULES/plan.md writes the module (from the prototype's graph_rules_proto.py, reuse map R3).
The document form keeps graph_rules.py (Q-6)."""


def kinds():
    """the registry of kinds: {kind: {"rules": [...], "runs": bool}} (REQ-GTB-033 to 036); not built yet"""
    return {}


def rule_report(graph):
    """every broken rule of the graph's kind in the registry's order (REQ-GTB-037 to 048); not built yet"""
    return [{"rule": "not_built", "parts": [], "text": "the rule set is not built yet"}]


def run_check(graph, given=None):
    """what stops a run before its first step (REQ-GTB-049 to 051); not built yet"""
    return {"status": "not_built", "broken": []}
