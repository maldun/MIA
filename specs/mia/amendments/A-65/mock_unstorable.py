def _unstorable(record_id, doc):
    """What IF-102 v3 refuses with invalid/schema (A-65): an id that is not text, a NUL character in a text, a number that is not finite."""
    if not isinstance(record_id, str):
        return "an id that is not text"
    stack = [record_id, doc]
    while stack:
        value = stack.pop()
        if isinstance(value, str) and "\x00" in value:
            return "a NUL character"
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            return "a number that is not finite"
        if isinstance(value, dict):
            stack.extend(value.keys())
            stack.extend(value.values())
        elif isinstance(value, (list, tuple)):
            stack.extend(value)
    return None


