"""
Preflight of the model side of a deployment (Phase 6, deploy/preflight_agent.py from the agent-app-deploy skill, unchanged; deploy/preflight.sh wraps it).
Markers: REQ-OPR-006 (runbook: update of the model pins) and REQ-OPR-001 (one file, one command: the target is checked first).   python tests/test_preflight.py
"""
import json
import os
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))
sys.path.insert(0, os.path.join(REPO, "deploy"))

from markers import mark                          # noqa: E402
import preflight_agent                            # noqa: E402

SPEC = os.path.join(REPO, "specs", "mia", "eval-spec.md")
LIGHT = "sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3"
FULL = "sha256:001e5dafc3c77684c2307ebc6ab8e336e10c9b18eca52acf547d72fc83c3ca8c"


def fake_ollama(models):
    """a local server that answers /api/version, /api/tags and /api/ps like Ollama; returns (url, stop)"""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = {"/api/version": {"version": "0.40.5"}, "/api/tags": {"models": models}, "/api/ps": {"models": []}}.get(self.path)
            self.send_response(200 if body is not None else 404)
            self.end_headers()
            self.wfile.write(json.dumps(body or {}).encode())

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d" % server.server_port, server.shutdown


def run(url):
    return subprocess.run([sys.executable, os.path.join(REPO, "deploy", "preflight_agent.py"), "--pins", SPEC, "--ollama", url], capture_output=True, text=True)


class Pins(unittest.TestCase):
    @mark.req("REQ-OPR-006")
    def test_the_pins_of_the_eval_spec_equal_the_pins_of_the_tools_and_the_compose_config(self):
        """Given the pin table of eval-spec.md, When it is compared with tools/eval.py and deploy/setup_cfg.compose.json, Then the model and the digest agree"""
        pins = preflight_agent.pins_from(__import__("pathlib").Path(SPEC))
        self.assertEqual(sorted(pins), ["MP-full", "MP-light"])
        self.assertEqual(pins["MP-light"]["digest"], LIGHT)
        self.assertEqual(pins["MP-full"]["digest"], FULL)
        with open(os.path.join(REPO, "tools", "eval.py"), encoding="utf-8") as fp:
            source = fp.read()
        self.assertIn(pins["MP-light"]["model"], source)
        self.assertIn(LIGHT, source)
        with open(os.path.join(REPO, "deploy", "setup_cfg.compose.json"), encoding="utf-8") as fp:
            config = json.load(fp)
        self.assertEqual(config["version_light"], pins["MP-light"]["model"])
        self.assertEqual(config["version"], pins["MP-full"]["model"])


class Server(unittest.TestCase):
    @mark.req("REQ-OPR-006")
    def test_a_server_that_holds_both_pinned_models_passes(self):
        """Given a server with both models at the pinned digests, When the preflight runs, Then it exits 0 and says PASS for both pins"""
        url, stop = fake_ollama([{"name": "gemma4:12b-it-qat", "digest": LIGHT}, {"name": "gemma4:26b", "digest": FULL}])
        try:
            out = run(url)
        finally:
            stop()
        self.assertEqual(out.returncode, 0, out.stdout)
        self.assertEqual(out.stdout.count("| PASS |"), 3)

    @mark.req("REQ-OPR-006")
    def test_a_changed_digest_stops_the_deployment(self):
        """Given the light model under another digest (a tag that moved), When the preflight runs, Then it exits 1 and names the model change"""
        url, stop = fake_ollama([{"name": "gemma4:12b-it-qat", "digest": "sha256:" + "ab" * 32}, {"name": "gemma4:26b", "digest": FULL}])
        try:
            out = run(url)
        finally:
            stop()
        self.assertEqual(out.returncode, 1)
        self.assertIn("model changed", out.stdout)

    @mark.req("REQ-OPR-006")
    def test_a_missing_model_and_an_unreachable_server_stop_the_deployment(self):
        """Given a server without the full model, and then no server, When the preflight runs, Then both exit 1"""
        url, stop = fake_ollama([{"name": "gemma4:12b-it-qat", "digest": LIGHT}])
        try:
            missing = run(url)
        finally:
            stop()
        self.assertEqual(missing.returncode, 1)
        self.assertIn("not present", missing.stdout)
        self.assertEqual(run("http://127.0.0.1:9").returncode, 1)


class HostScript(unittest.TestCase):
    """deploy/preflight.sh: the host checks round the model check; a stub podman and a fake server stand in for the real ones"""

    def script(self, url, with_podman=True, **extra):
        import tempfile
        stubs = tempfile.mkdtemp()
        if with_podman:
            path = os.path.join(stubs, "podman")
            with open(path, "w") as fp:
                fp.write("#!/bin/sh\nexit 0\n")
            os.chmod(path, 0o755)
        env = dict(os.environ, OLLAMA_URL=url, PATH=stubs + ":/usr/bin:/bin:" + os.path.dirname(__import__("shutil").which("python3") or sys.executable), MIA_PREFLIGHT_MIN_GB="1", PODMAN="podman" if with_podman else "no-such-podman", **extra)
        return subprocess.run(["bash", os.path.join(REPO, "deploy", "preflight.sh")], capture_output=True, text=True, env=env, cwd=REPO)

    @mark.req("REQ-OPR-001")
    def test_a_host_with_podman_and_the_pinned_models_passes_and_names_what_a_fresh_checkout_lacks(self):
        """Given podman, a server with both pins and a checkout, When deploy/preflight.sh runs, Then it exits 0 and prints Preflight OK"""
        url, stop = fake_ollama([{"name": "gemma4:12b-it-qat", "digest": LIGHT}, {"name": "gemma4:26b", "digest": FULL}])
        try:
            out = self.script(url)
        finally:
            stop()
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("Preflight OK", out.stdout)
        self.assertIn("sandbox_backend", out.stdout)

    @mark.req("REQ-OPR-001")
    def test_the_kokoro_check_follows_mia_kokoro_dir_and_wants_both_files(self):
        """Given MIA_KOKORO_DIR with no files, with one file, and with both, When deploy/preflight.sh runs, Then it warns naming the folder and the missing file, and is quiet with both"""
        import tempfile
        url, stop = fake_ollama([{"name": "gemma4:12b-it-qat", "digest": LIGHT}, {"name": "gemma4:26b", "digest": FULL}])
        try:
            folder = tempfile.mkdtemp()
            empty = self.script(url, MIA_KOKORO_DIR=folder)
            open(os.path.join(folder, "kokoro-v1.0.onnx"), "w").close()
            half = self.script(url, MIA_KOKORO_DIR=folder)
            open(os.path.join(folder, "voices-v1.0.bin"), "w").close()
            full = self.script(url, MIA_KOKORO_DIR=folder)
        finally:
            stop()
        self.assertIn("WARN: kokoro-v1.0.onnx missing in " + folder, empty.stdout)
        self.assertIn("WARN: voices-v1.0.bin missing in " + folder, half.stdout)
        self.assertNotIn("kokoro-v1.0.onnx missing", half.stdout)
        self.assertIn("ok:   Kokoro voice files in " + folder, full.stdout)
        self.assertEqual(full.returncode, 0, full.stdout)

    @mark.req("REQ-OPR-001")
    def test_no_podman_and_a_moved_digest_each_stop_it(self):
        """Given no podman, and then a moved digest, When deploy/preflight.sh runs, Then it exits 1 and says which"""
        url, stop = fake_ollama([{"name": "gemma4:12b-it-qat", "digest": LIGHT}, {"name": "gemma4:26b", "digest": FULL}])
        try:
            no_podman = self.script(url, with_podman=False)
        finally:
            stop()
        self.assertEqual(no_podman.returncode, 1)
        self.assertIn("FAIL: podman", no_podman.stdout + no_podman.stderr)
        url, stop = fake_ollama([{"name": "gemma4:12b-it-qat", "digest": "sha256:" + "cd" * 32}, {"name": "gemma4:26b", "digest": FULL}])
        try:
            moved = self.script(url)
        finally:
            stop()
        self.assertEqual(moved.returncode, 1)
        self.assertIn("model changed", moved.stdout)


if __name__ == "__main__":
    unittest.main()
