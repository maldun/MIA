"""
TC-TLS-005 (REQ-TLS-005): sandbox or refuse. Without an isolating sandbox run_script of the door (tool_calls.py) is unavailable and no backend is asked;
with one, the script runs there. A PDF (a hostile document) is not converted without the wall of pdf_text.py. The backends are fakes; nothing runs for real.
Run with: python tests/test_tool_calls_sandbox.py
"""

import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                   # noqa: E402
import pdf_text                                            # noqa: E402
from sandbox import NoSandbox, SandboxResult, SandboxRouter  # noqa: E402
from tool_calls import ToolCalls                           # noqa: E402

SCRIPT = "result = {'holds': data['a'] + data['b'] == 4, 'values': {'sum': data['a'] + data['b']}}\nprint(data['a'] + data['b'])"
RUN = {"id": "r1", "limits": {}}


class FakeBackend:
    """records every script it is asked to run; `available` False stands for a removed sandbox"""

    def __init__(self, name, available):
        self.name, self.available = name, available
        self.reason = "" if available else "removed for the test"
        self.runs = []

    def info(self):
        return {"name": self.name, "available": self.available, "reason": self.reason}

    def run(self, code, data=None, **kwargs):
        self.runs.append(code)
        return SandboxResult("ok", result={"holds": True, "values": {"sum": 4}}, stdout="4\n", backend=self.name)


def router(bubblewrap, podman):
    return SandboxRouter({"bubblewrap": FakeBackend("bubblewrap", bubblewrap), "podman": FakeBackend("podman", podman)})


class SandboxOrRefuseTests(unittest.TestCase):

    @mark.req("REQ-TLS-005")
    def test_without_a_sandbox_a_script_is_unavailable(self):
        """TC-TLS-005: without a sandbox, run_script is unavailable.

        Example: ToolCalls().call(RUN, "run_script", ...) -> {"status": "unavailable", "stdout": ""}
        """
        # Given: ToolCalls() with no sandbox
        out = ToolCalls().call(RUN, "run_script", {"code": SCRIPT, "inputs": {"a": 2, "b": 2}})
        # Then: status is unavailable
        self.assertEqual(out["output"], {"status": "unavailable", "stdout": ""})
        # Then: trust is still code
        self.assertEqual(out["trust"], "code")

    @mark.req("REQ-TO-005")
    def test_with_the_sandbox_removed_nothing_runs(self):
        """TC-TLS-005: with both backends unavailable, nothing runs.

        Example: router(False, False) -> both backend run lists empty
        """
        # Given: a router with both backends unavailable
        sandbox = router(False, False)
        out = ToolCalls(sandbox=sandbox).call(RUN, "run_script", {"code": SCRIPT, "inputs": {"a": 2, "b": 2}})
        # Then: output is unavailable
        self.assertEqual(out["output"], {"status": "unavailable", "stdout": ""})
        # Then: bubblewrap runs is empty
        self.assertEqual(sandbox.backends["bubblewrap"].runs, [])
        # Then: podman runs is empty
        self.assertEqual(sandbox.backends["podman"].runs, [])

    @mark.req("REQ-TLS-005")
    def test_a_sandbox_switched_off_by_configuration_runs_nothing(self):
        """TC-TLS-005: a forced 'none' sandbox runs nothing.

        Example: SandboxRouter(..., force="none") -> status unavailable
        """
        # Given: a forced 'none' sandbox
        sandbox = SandboxRouter({"none": NoSandbox()}, force="none")
        out = ToolCalls(sandbox=sandbox).call(RUN, "run_script", {"code": SCRIPT, "inputs": {"a": 2, "b": 2}})
        # Then: output is unavailable
        self.assertEqual(out["output"], {"status": "unavailable", "stdout": ""})

    @mark.req("REQ-TLS-005")
    def test_with_a_sandbox_the_script_runs_there(self):
        """TC-TLS-005: with a usable backend, the script runs.

        Example: bubblewrap available -> status ok, stdout 4\n, result pass
        """
        # Given: bubblewrap available, podman unavailable
        sandbox = router(True, False)
        out = ToolCalls(sandbox=sandbox).call(RUN, "run_script", {"code": SCRIPT, "inputs": {"a": 2, "b": 2}})
        # Then: status ok and stdout 4\n
        self.assertEqual((out["output"]["status"], out["output"]["stdout"]), ("ok", "4\n"))
        # Then: result status pass
        self.assertEqual(out["output"]["result"]["status"], "pass")
        # Then: bubblewrap ran the script
        self.assertEqual(sandbox.backends["bubblewrap"].runs, [SCRIPT])
        # Then: podman did not run it
        self.assertEqual(sandbox.backends["podman"].runs, [])

    @mark.req("REQ-TLS-005")
    def test_a_pdf_is_not_converted_without_the_wall(self):
        """TC-TLS-005: pdf_to_text fails without a usable sandbox.

        Example: mock tools to return no bubblewrap -> PdfUnavailable
        """
        # Given: mock tools and subprocess
        with mock.patch.object(pdf_text, "tools", return_value=(None, "/usr/bin/pdftotext", None)), mock.patch("subprocess.Popen") as popen:
            # When: convert a fake pdf
            with self.assertRaises(pdf_text.PdfUnavailable):
                pdf_text.pdf_to_text(b"%PDF-1.4\n%hostile\n")
            # Then: subprocess was never called
            popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
