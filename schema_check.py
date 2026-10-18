"""
A small JSON schema checker for the structured outputs of the pipelines (ui/REQUIREMENTS_CORE.md 3, S2). It knows the part of JSON schema that
the stage schemas use: type, enum, properties, required, additionalProperties, items, minItems, maxItems, minLength, maxLength, minimum, maximum.
check() returns a list of readable problems (empty = the value fits), which are also what a retry tells the model.
"""

_TYPES = {
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
    "null": lambda v: v is None,
}


def check(value, schema, path="$"):
    problems = []
    kinds = schema.get("type")
    if kinds is not None:
        kinds = [kinds] if isinstance(kinds, str) else list(kinds)
        if not any(_TYPES[k](value) for k in kinds if k in _TYPES):
            return ["%s: expected %s, got %s" % (path, "/".join(kinds), type(value).__name__)]
    if "enum" in schema and value not in schema["enum"]:
        problems.append("%s: %r is not one of %s" % (path, value, schema["enum"]))
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            problems.append("%s: shorter than %d characters" % (path, schema["minLength"]))
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            problems.append("%s: longer than %d characters" % (path, schema["maxLength"]))
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            problems.append("%s: below %s" % (path, schema["minimum"]))
        if "maximum" in schema and value > schema["maximum"]:
            problems.append("%s: above %s" % (path, schema["maximum"]))
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            problems.append("%s: fewer than %d items" % (path, schema["minItems"]))
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            problems.append("%s: more than %d items" % (path, schema["maxItems"]))
        if "items" in schema:
            for index, item in enumerate(value):
                problems += check(item, schema["items"], "%s[%d]" % (path, index))
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                problems.append("%s: missing '%s'" % (path, key))
        for key, item in value.items():
            if key in properties:
                problems += check(item, properties[key], "%s.%s" % (path, key))
            elif schema.get("additionalProperties") is False:
                problems.append("%s: unexpected '%s'" % (path, key))
    return problems
