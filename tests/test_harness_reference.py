"""A-162 (REQ-EVL-014, 015) beyond the protected checks: the run, not only the target, stops on a bad reference, before any model call, and the header holds num_ctx."""
import hashlib
import os
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

import harness as H                       # noqa: E402
from markers import mark                  # noqa: E402

PIN = {"id": "MP-light", "name": "m", "digest": "sha256:x", "seed": 7, "temperature": 0, "num_ctx": 8192}


class Model:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        self.calls += 1
        return "Short."


def suite_of(cases):
    return H.Suite("s", "", {"kind": "digest", "persona": ""}, cases)


def case(cid, **ref):
    return {"id": cid, "tags": [], "input": {"kind": "summary", "skill": "x@1", "phases": [], **({"result_ref": ref} if ref else {"result": "Found 3."})}}


class RunStops(unittest.TestCase):
    @mark.req("REQ-EVL-015")
    def test_a_bad_reference_of_a_later_case_stops_the_run_before_the_first_call(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "t.txt")
            open(path, "w").write("abc")
            model = Model()
            harness = H.Harness(types.SimpleNamespace(runner=types.SimpleNamespace(model=model), skills={}))
            bad = case("late", path=path, sha256=hashlib.sha256(b"abd").hexdigest())
            with self.assertRaises(H.SuiteError) as caught:
                harness.run(suite_of([case("first"), bad]), pin=PIN)
            self.assertIn("late", str(caught.exception))
            self.assertEqual(model.calls, 0)

    @mark.req("REQ-EVL-013")
    def test_the_header_holds_the_context_length_of_the_pin(self):
        model = Model()
        harness = H.Harness(types.SimpleNamespace(runner=types.SimpleNamespace(model=model), skills={}))
        run = harness.run(suite_of([case("first")]), pin=PIN)
        self.assertEqual(run.header["pin"]["num_ctx"], 8192)


if __name__ == "__main__":
    unittest.main()
