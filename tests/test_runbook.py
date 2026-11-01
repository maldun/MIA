"""TC-OPR-006 / REQ-OPR-006
Run with: python tests/test_runbook.py
"""

import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                         # noqa: E402

RUNBOOK = os.path.join(REPO, "deploy", "RUNBOOK.md")
COMPOSE_FILES = ("compose.yaml", "compose.rocm.yaml", "compose.nvidia.yaml")
FLOATING = ("docker.io/ollama/ollama:latest", "docker.io/ollama/ollama:rocm", "docker.io/searxng/searxng:latest", "docker.io/library/caddy:2",
            "docker.io/library/postgres:16")                       # postgres added by D-139
DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")


def image_lines():
    """every value of an `image:` key in the compose files, without its comment"""
    found = []
    for name in COMPOSE_FILES:
        with open(os.path.join(REPO, "deploy", name), encoding="utf-8") as fp:
            for line in fp:
                match = re.match(r"\s*image:\s*(\S+)", line)
                if match:
                    found.append(match.group(1))
    return found


def section(text, heading):
    """the text under a '## heading' line up to the next '## ' line ('' when the heading is missing)"""
    parts = re.split(r"(?m)^## ", text)
    for part in parts[1:]:
        if part.startswith(heading):
            return part
    return ""


class Runbook(unittest.TestCase):
    """deploy/RUNBOOK.md and the image pins of the compose files (REQ-OPR-006, D-127, D-136)."""

    def setUp(self):
        with open(RUNBOOK, encoding="utf-8") as fp:
            self.text = fp.read()

    @mark.req('REQ-OPR-006')
    def test_the_floating_images_are_pinned_by_digest(self):
        """TC-OPR-006 (D-127): the images that used to float (ollama latest and rocm, searxng latest, caddy 2) are pinned by a sha256 digest in the compose files.

        Example: "docker.io/library/caddy:2" -> "docker.io/library/caddy:2@sha256:<64 hex digits>"
        """
        # Given: the image lines of the three compose files
        images = image_lines()
        # When: the lines of the floating images are picked
        pinned = {name: [image for image in images if image.startswith(name)] for name in FLOATING}
        # Then: each such image appears and every line of it ends in a digest
        for name, lines in pinned.items():
            self.assertTrue(lines, name)
            for image in lines:
                self.assertRegex(image, DIGEST)

    @mark.req('REQ-OPR-006')
    def test_the_base_image_of_mia_is_pinned_by_digest(self):
        """TC-OPR-006 (D-139): the base image of the mia image (python:3.12-slim) is pinned by a sha256 digest like the images of the compose files.

        Example: "FROM docker.io/library/python:3.12-slim" -> "FROM docker.io/library/python:3.12-slim@sha256:<64 hex digits>"
        """
        # Given: the Containerfile of the mia image
        with open(os.path.join(REPO, "deploy", "Containerfile"), encoding="utf-8") as fp:
            # When: its FROM lines are read
            bases = [line.split()[1] for line in fp if line.startswith("FROM ")]
        # Then: there is one, and it ends in a digest
        self.assertEqual(len(bases), 1)
        self.assertRegex(bases[0], DIGEST)

    @mark.req('REQ-OPR-001')
    def test_the_runbook_names_the_files_a_fresh_checkout_lacks(self):
        """TC-OPR-001 (D-139): the runbook says where the git-ignored character model and voice files come from, and that MIA runs without them.

        Example: section "## Files a fresh checkout lacks" names ui/godot/assets/mia.vrm, kokoro-v1.0.onnx and voices-v1.0.bin
        """
        # Given: the runbook (setUp), When: its section on the missing files is read
        part = section(self.text, "Files a fresh checkout lacks")
        # Then: it names the three files and says that the chat works without them
        for name in ("ui/godot/assets/mia.vrm", "kokoro-v1.0.onnx", "voices-v1.0.bin", "without them"):
            self.assertIn(name, part)

    @mark.req('REQ-OPR-006')
    def test_the_runbook_names_the_character_folder_the_stack_mounts(self):
        """TC-OPR-006, Verify finding F4: the stack mounts ui/godot/build/web (not mia.vrm), installed with deploy/up.sh character.

        Example: section "## Files a fresh checkout lacks" names ui/godot/build/web and deploy/up.sh character
        """
        # Given: the runbook (setUp), When: its section on the missing files is read
        part = section(self.text, "Files a fresh checkout lacks")
        # Then: it names the mounted folder and the command that fills it
        self.assertIn("ui/godot/build/web", part)
        self.assertIn("deploy/up.sh character", part)

    @mark.req('REQ-OPR-006')
    def test_the_pin_update_names_every_pinned_image_and_both_kinds_of_ollama(self):
        """TC-OPR-006, Verify finding F4: the update of the pins names every image pinned in the compose files and the Containerfile, and how to read the models of the stack's own Ollama besides a host Ollama.

        Example: "Update of the model pins" names caddy:2, ollama:latest, ollama:rocm, searxng:latest, postgres:16, python:3.12-slim, OLLAMA_URL and deploy/up.sh exec ollama
        """
        # Given: the pinned images as name:tag (compose files and the FROM line of the Containerfile)
        with open(os.path.join(REPO, "deploy", "Containerfile"), encoding="utf-8") as fp:
            bases = [line.split()[1] for line in fp if line.startswith("FROM ")]
        pinned = {image.split("@")[0].rsplit("/", 1)[-1] for image in image_lines() + bases if "@sha256:" in image}      # not the local build of mia
        # When: the part on the pins is read
        part = section(self.text, "Update of the model pins")
        # Then: each image and both ways to reach Ollama are named
        for name in sorted(pinned) + ["OLLAMA_URL", "deploy/up.sh exec ollama"]:
            self.assertIn(name, part)

    @mark.req('REQ-OPR-006')
    def test_the_runbook_has_the_four_parts_of_the_requirement(self):
        """TC-OPR-006: the runbook has start, update of the model pins, backup and restore of the database, and the retirement plan.

        Example: headings "## Start and stop", "## Update of the model pins", "## Backup and restore", "## Retirement plan"
        """
        # Given: the runbook (setUp)
        # When: its sections are looked for
        parts = [section(self.text, heading) for heading in ("Start and stop", "Update of the model pins", "Backup and restore", "Retirement plan")]
        # Then: all four are there and not empty
        for part in parts:
            self.assertGreater(len(part.strip().splitlines()), 2, part)

    @mark.req('REQ-OPR-006')
    def test_backup_and_retirement_name_the_database_and_the_digests(self):
        """TC-OPR-006: the backup part names the database and the restore command; the retirement plan ends in freezing with the model digests.

        Example: "Backup and restore" has "deploy/up.sh db" and "deploy/up.sh restore"; "Retirement plan" has "digest" and "freeze"
        """
        # Given: the runbook (setUp)
        # When: the two parts are read
        backup = section(self.text, "Backup and restore")
        retirement = section(self.text, "Retirement plan")
        # Then: they name the database, the commands and the digests
        self.assertIn("deploy/up.sh db", backup)
        self.assertIn("deploy/up.sh backup", backup)
        self.assertIn("deploy/up.sh restore", backup)
        self.assertIn("digest", retirement)
        self.assertIn("freeze", retirement)

    @mark.req('REQ-OPR-006')
    def test_the_fresh_install_check_uses_a_running_ollama(self):
        """TC-OPR-006 (D-136 item 5): the runbook says that the fresh-install check uses an Ollama that runs already and never pulls the models.

        Example: the runbook names tests/smoke/smoke_fresh_install.py, OLLAMA_URL and "never pulls"
        """
        # Given: the runbook (setUp)
        # When: the text is searched
        text = self.text
        # Then: the smoke test, the Ollama address and the rule are there
        self.assertIn("tests/smoke/smoke_fresh_install.py", text)
        self.assertIn("OLLAMA_URL", text)
        self.assertIn("never pulls", text)

    @mark.req('REQ-API-007', 'REQ-OPR-006')
    def test_runbook_and_readme_say_that_without_the_login_every_route_is_open(self):
        """D-149 (V-4, an accepted deviation): with accounts_enabled off every route is open to everyone who reaches the page (trusted users, D-131);
        the runbook and deploy/README.md say so and how to turn the login on.

        Example: both texts name accounts_enabled, "every route is open", D-131 and deploy/up.sh owner NAME
        """
        # Given: the runbook (setUp) and deploy/README.md
        with open(os.path.join(REPO, "deploy", "README.md"), encoding="utf-8") as fp:
            readme = fp.read()
        # When: both texts are searched
        texts = {"RUNBOOK.md": self.text, "README.md": readme}
        # Then: each says that the routes are open without the login, why, and how to turn it on
        for name, text in texts.items():
            for words in ("accounts_enabled", "every route is open", "D-131", "deploy/up.sh owner NAME"):
                self.assertIn(words, text, name)

if __name__ == '__main__':
    unittest.main()
