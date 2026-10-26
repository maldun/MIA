"""Errors shared by the mocks of IF-101..IF-104 (protected; changes by amendment together with the suites)."""


class StorageError(Exception):
    """IF-102. code: invalid | not_found | conflict | immutable | unknown_table; rule: the broken graph rule for code invalid."""

    def __init__(self, code, rule=None, detail=None):
        super().__init__("%s%s" % (code, ": %s" % rule if rule else ""))
        self.code, self.rule, self.detail = code, rule, detail


class ApiError(Exception):
    """IF-101 and IF-104. status: 401 unauthenticated, 404 not found, 409 conflict, 422 invalid, 429 throttled, 503 queue full."""

    def __init__(self, status, code, rule=None, detail=None):
        super().__init__("%s %s%s" % (status, code, ": %s" % rule if rule else ""))
        self.status, self.code, self.rule, self.detail = status, code, rule, detail


class ServiceError(Exception):
    """IF-201..IF-204 (calls between the children of the Backend). code: empty_text | queue_full | unknown_workflow | invalid |
    not_found | conflict | not_promotable | unavailable | no_line; rule: the broken graph rule for code invalid."""

    def __init__(self, code, rule=None, detail=None):
        super().__init__("%s%s" % (code, ": %s" % rule if rule else ""))
        self.code, self.rule, self.detail = code, rule, detail


class ModelServerError(Exception):
    """IF-103. code: unreachable | timeout | bad_output."""

    def __init__(self, code, detail=None):
        super().__init__(code)
        self.code, self.detail = code, detail
