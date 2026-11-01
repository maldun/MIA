"""Requirement markers for the acceptance tests without pytest.

The workflow's trace check looks for the text  mark.req  with a requirement id in brackets above a test. MIA's tests run with unittest, so this module gives
the same decorators without importing pytest; under pytest they are plain attributes and do not select anything.

    from markers import mark   # then use mark dot req as a decorator above a test, with the id as a string argument
"""


import unittest  # noqa: E402


class _Mark:
    @staticmethod
    def req(*ids):
        def decorate(fn):
            fn.req_ids = tuple(getattr(fn, "req_ids", ())) + tuple(ids)
            return fn
        return decorate

    @staticmethod
    def feedback(*ids):
        def decorate(fn):
            fn.feedback_ids = tuple(getattr(fn, "feedback_ids", ())) + tuple(ids)
            return fn
        return decorate

    @staticmethod
    def deferred(td):
        """a check whose target is deferred (M26, deferred.md): a strict expected failure that names its record; it fails (an unexpected success) as soon as the check passes"""
        def decorate(fn):
            fn.deferred_td = td
            return unittest.expectedFailure(fn)
        return decorate

    @staticmethod
    def statistical(fn):
        fn.statistical = True
        return fn


mark = _Mark()
