"""Mock of IF-302, record table definitions and validation (protected). Complexity 1: static definitions and a pure function.
It stores nothing. The real schemas are written in N-3.3 and tested against the same suite."""

DEFINITIONS = {
    "history": {"versioned": True, "deletable": True}, "memory": {"versioned": True, "deletable": True},
    "votes": {"versioned": True, "deletable": False}, "tasks": {"versioned": True, "deletable": True},
    "memos": {"versioned": True, "deletable": True}, "accounts": {"versioned": True, "deletable": False},
    "presets": {"versioned": True, "deletable": False}, "gestures": {"versioned": True, "deletable": False},
    "runs": {"versioned": True, "deletable": False}, "source_trust": {"versioned": True, "deletable": False},
}
REQUIRED = {"memory": ("text", "source"), "votes": ("user", "subject", "category", "value"), "tasks": ("text",), "memos": ("text",),
            "runs": ("workflow", "workflow_version", "model_pin", "benchmark_version")}
CATEGORIES = ("answer_quality", "reactions", "character_behaviour", "service")


class RecordTablesMock:
    def definitions(self):
        return {t: dict(d) for t, d in DEFINITIONS.items()}

    def validate(self, table, doc):
        if table not in DEFINITIONS:
            raise ValueError("not a record table: %s" % table)
        for field in REQUIRED.get(table, ()):
            if not isinstance(doc, dict) or field not in doc:
                return {"rule": "schema", "detail": field}
        if table == "votes" and (doc["category"] not in CATEGORIES or doc["value"] not in (1, -1)):
            return {"rule": "category" if doc["category"] not in CATEGORIES else "schema", "detail": doc["category"] if doc["category"] not in CATEGORIES else "value"}
        return None
