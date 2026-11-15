"""Mock of IF-302, record table definitions and validation (protected). Complexity 1: static definitions and a pure function.
It stores nothing. The real schemas are written in N-3.3 and tested against the same suite."""

DEFINITIONS = {
    "history": {"versioned": True, "deletable": True}, "memory": {"versioned": True, "deletable": True},
    "votes": {"versioned": True, "deletable": False}, "tasks": {"versioned": True, "deletable": True},
    "memos": {"versioned": True, "deletable": True}, "accounts": {"versioned": True, "deletable": False},
    "presets": {"versioned": True, "deletable": False}, "gestures": {"versioned": True, "deletable": False},
    "runs": {"versioned": True, "deletable": False}, "source_trust": {"versioned": True, "deletable": False},
    "cases": {"versioned": True, "deletable": False}, "behaviours": {"versioned": True, "deletable": False},      # v1 (amendment A-08)
    "workflow_meta": {"versioned": True, "deletable": False},      # v3 (amendment A-15): status, specification and benchmark of a workflow
    "reports": {"versioned": True, "deletable": False},      # v4/v5 (amendments A-23, A-24): the finished report of a task
    "transform_meta": {"versioned": True, "deletable": False},      # v8 (amendment A-110): trust and lifecycle of a transform, one record per transform id
    "transforms": {"versioned": True, "deletable": False},      # v9 (amendment A-112): the versioned code of a transform, one record per transform id
}
REQUIRED = {"reports": ("task", "skill", "skill_version", "question", "account", "model_pin", "report"), "workflow_meta": ("status",), "cases": ("question", "answer", "status"), "behaviours": ("name", "net", "votes"),"memory": ("text", "source"), "votes": ("user", "subject", "category", "value"), "tasks": ("text",), "memos": ("text",),
            "runs": ("workflow", "workflow_version", "model_pin", "benchmark_version"),
            "transform_meta": ("trust", "lifecycle"), "transforms": ("id", "version")}
CATEGORIES = ("answer_quality", "reactions", "character_behaviour", "service")
MEMORY_FIELDS = {"kind": ("fact", "preference", "commitment"), "status": ("active", "replaced")}      # v2 (amendment A-10): optional, checked when present
TRANSFORM_META_FIELDS = {"trust": ("untrusted", "trusted"), "lifecycle": ("draft", "tested", "retired")}      # v8 (amendment A-110): exact values, the optional fields are free


class RecordTablesMock:
    def definitions(self):
        return {t: dict(d) for t, d in DEFINITIONS.items()}

    def validate(self, table, doc):
        if table not in DEFINITIONS:
            raise ValueError("not a record table: %s" % table)
        if not isinstance(doc, dict):      # v6 (amendment A-61): in every table, also those without a required field
            return {"rule": "schema", "detail": "a document must be a mapping"}
        for field in REQUIRED.get(table, ()):
            if field not in doc:
                return {"rule": "schema", "detail": field}
        if table == "memory":
            for field, allowed in MEMORY_FIELDS.items():
                if field in doc and doc[field] not in allowed:
                    return {"rule": "schema", "detail": field}
        if table == "transform_meta":
            for field, allowed in TRANSFORM_META_FIELDS.items():
                if doc[field] not in allowed:
                    return {"rule": "schema", "detail": field}
        if table == "transforms":      # v9 (amendment A-112): inputs, outputs and code are free, an empty, missing or null code is valid
            if not isinstance(doc["id"], str) or not doc["id"]:
                return {"rule": "schema", "detail": "id"}
            if type(doc["version"]) is not int or doc["version"] < 1:      # a bool or a float is no version number (as for the vote value)
                return {"rule": "schema", "detail": "version"}
        if table == "workflow_meta" and doc["status"] not in ("draft", "tested", "trusted", "retired"):
            return {"rule": "schema", "detail": "status"}
        if table == "votes" and doc["category"] not in CATEGORIES:
            return {"rule": "category", "detail": doc["category"]}
        if table == "votes" and (type(doc["value"]) is not int or doc["value"] not in (1, -1)):      # v6 (A-61): a bool or a float equal to 1 is no vote value
            return {"rule": "schema", "detail": "value"}
        return None
