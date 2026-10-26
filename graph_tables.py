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
