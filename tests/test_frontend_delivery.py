"""The chat page is delivered by the backend container and the frontend has no container of its own (N-1.3 T-04; TC-VPB-005, REQ-VPB-005, REQ-FE-030).
The container check runs the MIA image with this checkout through tools/start_testing.sh; it is skipped, never weakened, where podman or the image is missing.
Run with: python tests/test_frontend_delivery.py"""
import os
import shutil
import subprocess
import sys
import unittest
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "tests"))
from test_page_requests import own_stage  # noqa: E402


class Delivery(unittest.TestCase):
    @mark.req("REQ-VPB-005", "REQ-FE-030")
    def test_the_compose_stack_has_no_service_for_the_frontend(self):
        """TC-VPB-005: the static files travel inside the image of the backend (Containerfile: COPY . MIA/); no service is named after the frontend.

        Example: deploy/compose.yaml services without frontend, web, ui, static, nginx; deploy/Containerfile contains "COPY . MIA/".
        """
        # Given: the compose stack and the Containerfile of the backend
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML is not installed")
        with open(os.path.join(ROOT, "deploy", "compose.yaml"), encoding="utf-8") as handle:
            services = yaml.safe_load(handle)["services"]
        # When: the services are looked up by the names a frontend would have
        frontend = [name for name in services if name in ("frontend", "web", "ui", "static", "nginx")]
        # Then: there is none, and the backend image carries the checkout with the static files
        self.assertEqual(frontend, [])
        with open(os.path.join(ROOT, "deploy", "Containerfile"), encoding="utf-8") as handle:
            self.assertIn("COPY . MIA/", handle.read())

    @mark.req("REQ-VPB-005", "REQ-FE-030")
    def test_the_page_and_its_scripts_come_from_the_backend_container(self):
        """TC-VPB-005: the page, sound.js and chat.js are served by the MIA image (stage chat-on-stub: the stub server inside the backend image).

        Example: GET http://127.0.0.1:8685/static/chat/sound.js -> 200 with "class VoicePlayer".
        """
        # Given: the stage chat-on-stub, the backend image with this checkout
        if shutil.which("podman") is None or subprocess.run(["podman", "image", "exists", "localhost/mia:latest"]).returncode != 0:
            self.skipTest("podman or the image localhost/mia:latest is not available")
        start = subprocess.run(["bash", os.path.join(ROOT, "tools", "start_testing.sh"), "start", "chat-on-stub"], capture_output=True, text=True)
        if own_stage(start.stdout):                    # N5: a stage that runs already is neither used nor stopped
            self.addCleanup(subprocess.run, ["bash", os.path.join(ROOT, "tools", "start_testing.sh"), "stop", "chat-on-stub"], capture_output=True)
        for path, needle in (("/", "<title>MIA</title>"), ("/static/chat/sound.js", "class VoicePlayer"), ("/static/chat/chat.js", "import")):
            # When: the page and its scripts are requested from the container
            with urllib.request.urlopen("http://127.0.0.1:8685" + path, timeout=5) as response:
                body = response.read().decode("utf-8")
                # Then: each one is there
                self.assertEqual(response.status, 200, path)
                self.assertIn(needle, body, path)


if __name__ == "__main__":
    unittest.main()
