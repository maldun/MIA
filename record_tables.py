"""
The ten record tables and their validation: IF-302, provided to the Storage layer (REQ-RTB-001 to REQ-RTB-006).

All tables are versioned. Deletable are only the records a user may remove (history, memory, tasks, memos); votes, accounts, run results, presets, gestures
and source trust keep every version. validate() checks what the tables must be able to rely on and nothing else: required fields, the four vote
categories and the vote value. It never changes a document (a task or memo comes back word for word, FR-28).
"""

TABLES = {name: {"versioned": True, "deletable": name in ("history", "memory", "tasks", "memos")}
          for name in ("history", "memory", "votes", "tasks", "memos", "accounts", "presets", "gestures", "runs", "source_trust")}
REQUIRED = {"memory": ("text", "source"), "votes": ("user", "subject", "category", "value"), "tasks": ("text",), "memos": ("text",),
            "runs": ("workflow", "workflow_version", "model_pin", "benchmark_version")}
CATEGORIES = ("answer_quality", "reactions", "character_behaviour", "service")


def definitions():
    return {table: dict(rules) for table, rules in TABLES.items()}


def validate(table, doc):
    """None for a valid document, else {"rule": "schema" | "category", "detail"}. A table that is not defined here is a ValueError (ask IF-301)."""
    if table not in TABLES:
        raise ValueError("not a record table: %s" % (table,))
    required = REQUIRED.get(table, ())
    if not isinstance(doc, dict):
        return {"rule": "schema", "detail": "a document must be a mapping"}
    for field in required:
        if field not in doc:
            return {"rule": "schema", "detail": field}
    if table == "votes":
        if doc["category"] not in CATEGORIES:
            return {"rule": "category", "detail": doc["category"]}
        if isinstance(doc["value"], bool) or doc["value"] not in (1, -1):
            return {"rule": "schema", "detail": "value"}
    return None
