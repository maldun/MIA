"""Mock of IF-301, graph table definitions and validation (protected). Complexity 1: static definitions and a pure function.
It stores nothing. The real rules are written in N-3.2 and tested against the same suite."""
try:
    from . import graph_rules
except ImportError:
    import graph_rules

DEFINITIONS = {"workflows": {"versioned": True, "deletable": False}, "context_graphs": {"versioned": True, "deletable": False}}


class GraphTablesMock:
    def definitions(self):
        return {t: dict(d) for t, d in DEFINITIONS.items()}

    def validate(self, table, doc):
        if table not in DEFINITIONS:
            raise ValueError("not a graph table: %s" % table)
        broken = graph_rules.violation(doc)
        return None if broken is None else {"rule": broken[0], "detail": broken[1]}
