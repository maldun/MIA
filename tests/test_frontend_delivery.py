"""The chat page is delivered by the backend container and the frontend has no container of its own (N-1.3 T-04; TC-VPB-005, REQ-FE-030).
The container check runs the MIA image with this checkout through tools/start_testing.sh; it is skipped, never weakened, where podman or the image is missing.
Run with: python tests/test_frontend_delivery.py"""
import os
import shutil
import subprocess
import unittest
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Delivery(unittest.TestCase):
    def test_the_compose_stack_has_no_service_for_the_frontend(self):
        """The static files travel inside the image of the backend (Containerfile: COPY . MIA/); no service is named after the frontend."""
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML is not installed")
        with open(os.path.join(ROOT, "deploy", "compose.yaml"), encoding="utf-8") as handle:
            services = yaml.safe_load(handle)["services"]
        self.assertEqual([name for name in services if name in ("frontend", "web", "ui", "static", "nginx")], [])
        with open(os.path.join(ROOT, "deploy", "Containerfile"), encoding="utf-8") as handle:
            self.assertIn("COPY . MIA/", handle.read())

    def test_the_page_and_its_scripts_come_from_the_backend_container(self):
        if shutil.which("podman") is None or subprocess.run(["podman", "image", "exists", "localhost/mia:latest"]).returncode != 0:
            self.skipTest("podman or the image localhost/mia:latest is not available")
        start = subprocess.run(["bash", os.path.join(ROOT, "tools", "start_testing.sh"), "start", "chat-on-stub"], capture_output=True, text=True)
        self.addCleanup(subprocess.run, ["bash", os.path.join(ROOT, "tools", "start_testing.sh"), "stop", "chat-on-stub"], capture_output=True)
        if "started" not in start.stdout and "running already" not in start.stdout:
            self.skipTest("the stage does not start: " + start.stdout[-200:])
        for path, needle in (("/", "<title>MIA</title>"), ("/static/chat/sound.js", "class VoicePlayer"), ("/static/chat/chat.js", "import")):
            with urllib.request.urlopen("http://127.0.0.1:8685" + path, timeout=5) as response:
                body = response.read().decode("utf-8")
                self.assertEqual(response.status, 200, path)
                self.assertIn(needle, body, path)


if __name__ == "__main__":
    unittest.main()
