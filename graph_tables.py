"""
The tables of workflows (library entries) and context graphs and their validation: IF-301, provided to the Storage layer (REQ-GTB-001, REQ-GTB-003).

Both tables are versioned and never deleted (an edit is a new version). A document is valid when graph_rules finds no broken rule, so the Storage
layer refuses a bad edit on write (TB-edit, second line of defence behind the Backend).
"""
try:
    from . import graph_rules
except ImportError:  # used as plain script / in tests
    import graph_rules

TABLES = {"workflows": {"versioned": True, "deletable": False}, "context_graphs": {"versioned": True, "deletable": False}}


def definitions():
    return {table: dict(rules) for table, rules in TABLES.items()}


def validate(table, doc):
    """None for a valid document, else {"rule", "detail"} of the first broken rule. A table that is not defined here is a ValueError (ask IF-302)."""
    if table not in TABLES:
        raise ValueError("not a graph table: %s" % (table,))
    broken = graph_rules.violation(doc)
    return None if broken is None else {"rule": broken[0], "detail": broken[1]}


# IF-301 v2 (A-90, G-V2.STORE): stubs so the red tests import. Each returns a wrong-but-valid value; N-3.2 Implement replaces them.
def record_definitions():
    return {}


def types():
    return {}


def check_record(table, record, categories=None, stored=None):
    return None


def to_object(record, categories=None):
    return {"refused": {"rule": "unknown_type", "detail": ""}}


def to_record(obj):
    return {}


def to_document(nodes, edges):
    return {"document": {"nodes": [], "edges": []}}


def from_document(doc):
    return {"nodes": [], "edges": []}
