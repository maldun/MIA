"""
Tests for remote access over Tailscale: tailscale_serve.py (with a fake command runner), the allowed origins for the tailnet name,
and ui/tools/remote.sh (with a fake `tailscale` program in the PATH). Tailscale itself is not needed.
Run with the MIA virtualenv: python tests/test_tailscale.py
"""
import importlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

STATUS = {"BackendState": "Running", "Self": {"DNSName": "mia.tail1234.ts.net.", "TailscaleIPs": ["100.64.0.7"], "Online": True}}


class FakeTailscale:
    """records the calls; answers `status --json` and succeeds for everything else (unless told otherwise)"""

    def __init__(self, status=STATUS, serve_code=0, serve_output=""):
        self.status = status
        self.serve_code = serve_code
        self.serve_output = serve_output
        self.calls = []

    def __call__(self, args, timeout=8, binary=None):
        self.calls.append(list(args))
        if args[:2] == ["status", "--json"]:
            if self.status is None:
                return None, "the tailscale command is not installed"
            return 0, json.dumps(self.status)
        if args[0] == "serve":
            return self.serve_code, self.serve_output
        return 0, ""


class ServeTest(unittest.TestCase):
    def setUp(self):
        self.ts = importlib.import_module("MIA.tailscale_serve")

    def test_node_info_reads_the_name_without_the_trailing_dot(self):
        info = self.ts.node_info(FakeTailscale())
        self.assertEqual(info["name"], "mia.tail1234.ts.net")
        self.assertEqual(info["state"], "Running")
        self.assertEqual(info["ips"], ["100.64.0.7"])

    def test_not_installed_not_running_and_garbage_give_none(self):
        self.assertIsNone(self.ts.node_info(FakeTailscale(status=None)))
        self.assertIsNone(self.ts.node_info(lambda args, *a, **k: (1, "Tailscale is stopped.")))
        self.assertIsNone(self.ts.node_info(lambda args, *a, **k: (0, "not json")))
        self.assertIsNone(self.ts.node_info(FakeTailscale(status={"BackendState": "NeedsLogin", "Self": {}})))

    def test_urls_and_origins(self):
        self.assertEqual(self.ts.https_url("mia.ts.net"), "https://mia.ts.net/")
        self.assertEqual(self.ts.https_url("mia.ts.net", 8443), "https://mia.ts.net:8443/")
        self.assertEqual(self.ts.origins_for("mia.ts.net"), ["https://mia.ts.net", "https://mia.ts.net:443", "http://mia.ts.net"])
        self.assertEqual(self.ts.origins_for(""), [])

    def test_start_serve_uses_the_documented_command(self):
        fake = FakeTailscale()
        result = self.ts.start_serve(8585, fake)
        self.assertTrue(result["ok"])
        self.assertEqual(result["url"], "https://mia.tail1234.ts.net/")
        self.assertIn(["serve", "--bg", "8585"], fake.calls)

    def test_start_serve_explains_why_it_cannot(self):
        result = self.ts.start_serve(8585, FakeTailscale(status=None))
        self.assertFalse(result["ok"])
        self.assertIn("not available", result["message"])
        needs_login = FakeTailscale(status={"BackendState": "NeedsLogin", "Self": {"DNSName": "mia.ts.net."}})
        result = self.ts.start_serve(8585, needs_login)
        self.assertFalse(result["ok"])
        self.assertIn("tailscale up", result["message"])
        self.assertNotIn(["serve", "--bg", "8585"], needs_login.calls)

    def test_a_failing_serve_command_shows_its_message(self):
        fake = FakeTailscale(serve_code=1, serve_output="Serve is not enabled on your tailnet. To enable, visit: https://login.tailscale.com/f/serve")
        result = self.ts.start_serve(8585, fake)
        self.assertFalse(result["ok"])
        self.assertIn("login.tailscale.com", result["message"])

    def test_stop_serve(self):
        fake = FakeTailscale()
        self.assertTrue(self.ts.stop_serve(8585, fake))
        self.assertIn(["serve", "--https=443", "8585", "off"], fake.calls)
        self.assertFalse(self.ts.stop_serve(8585, FakeTailscale(serve_code=1)))

    def test_run_without_the_program(self):
        code, message = self.ts.run(["status"], binary=None) if self.ts.find_binary() is None else (None, "installed")
        self.assertIsNone(code)


class OriginsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("MIA_TEST", "1")
        cls.wa = importlib.import_module("MIA.web_app")

    def test_the_tailnet_name_is_an_allowed_origin(self):
        origins = self.wa.build_allowed_origins("http://localhost:8585", "localhost", 8585, None, None, extra_hosts=["mia.tail1234.ts.net"])
        self.assertIn("https://mia.tail1234.ts.net", origins)
        self.assertIn("http://localhost:8585", origins)
        self.assertEqual(len(origins), len(set(origins)))

    def test_without_extra_hosts_nothing_changes(self):
        plain = self.wa.build_allowed_origins("http://localhost:8585", "localhost", 8585, 8586, "192.168.1.5")
        self.assertFalse([o for o in plain if o.endswith(".ts.net")])

    def test_a_page_from_the_tailnet_may_use_the_api_even_if_the_host_header_differs(self):
        origin = "https://mia.tail1234.ts.net"
        client = self.wa.app.test_client()
        token = self.wa.app.config["EDITOR_TOKEN_INFO"][0] or ""
        headers = {"X-MIA-Token": token, "Origin": origin}
        refused = client.post("/api/expression/match", json={"description": "sad"}, headers=headers)
        self.assertEqual(refused.status_code, 403)
        self.wa.allowed_origins.extend(self.wa.tailscale_serve.origins_for("mia.tail1234.ts.net"))
        try:
            allowed = client.post("/api/expression/match", json={"description": "sad"}, headers=headers)
            self.assertEqual(allowed.status_code, 200)
        finally:
            for item in self.wa.tailscale_serve.origins_for("mia.tail1234.ts.net"):
                self.wa.allowed_origins.remove(item)


class ScriptTest(unittest.TestCase):
    """ui/tools/remote.sh with a fake `tailscale` in the PATH"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = os.path.join(self.tmp.name, "calls.txt")
        fake = os.path.join(self.tmp.name, "tailscale")
        with open(fake, "w") as fp:
            fp.write("#!/bin/bash\necho \"$@\" >> %s\n" % self.log)
            fp.write("if [ \"$1\" = status ]; then echo '%s'; fi\n" % json.dumps(STATUS))
        os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
        self.env = dict(os.environ, PATH=self.tmp.name + os.pathsep + os.environ["PATH"])

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args):
        return subprocess.run(["bash", os.path.join(REPO, "ui", "tools", "remote.sh"), *args], capture_output=True, text=True, env=self.env, timeout=30)

    def calls(self):
        with open(self.log) as fp:
            return fp.read().splitlines()

    def test_up_publishes_the_port_and_prints_the_address(self):
        done = self.run_script("up", "8585")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("serve --bg 8585", self.calls())
        self.assertIn("https://mia.tail1234.ts.net/", done.stdout)

    def test_down_stops_it(self):
        done = self.run_script("down", "8585")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("serve --https=443 8585 off", self.calls())

    def test_status_reports_the_address(self):
        done = self.run_script("status", "1")
        self.assertIn("serve status", self.calls())
        self.assertIn("https://mia.tail1234.ts.net/", done.stdout)
        self.assertIn("does not answer", done.stdout)

    def test_unknown_action(self):
        self.assertEqual(self.run_script("explode").returncode, 2)

    def test_without_tailscale_it_says_how_to_install(self):
        env = dict(self.env, PATH="/usr/bin:/bin")
        done = subprocess.run(["bash", os.path.join(REPO, "ui", "tools", "remote.sh"), "up"], capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(done.returncode, 1)
        self.assertIn("install", done.stdout)


if __name__ == "__main__":
    unittest.main()
