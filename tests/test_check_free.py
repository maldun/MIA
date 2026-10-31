"""Licence and dependency check (N-4.2 T-04): TC-OPR-009 (REQ-OPR-009). Run with: python tests/test_check_free.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, os.path.join(HERE, "helpers"))

import check_free                                # noqa: E402
from markers import mark                         # noqa: E402


class FreeAndOpen(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder, True)

    def write(self, name, text):
        """a file in the temporary folder; returns its path"""
        path = os.path.join(self.folder, name)
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(text)
        return path

    def web_log(self, *urls):
        """a web log (data/runs/web-YYYY-MM.jsonl form) with one fetch line per url; returns its path"""
        lines = [json.dumps({"at": "2026-10-31T10:00:00Z", "kind": "fetch", "url": url, "status": 200}) for url in urls]
        lines.append(json.dumps({"at": "2026-10-31T10:00:01Z", "kind": "search", "query": "api.openai.com pricing"}))
        return self.write("web-2026-10.jsonl", "\n".join(lines) + "\n")

    @mark.req('REQ-OPR-009')
    def test_the_licence_of_mia_is_gpl_3_or_later(self):
        """TC-OPR-009: the LICENSE and README.md of this repository give GPL-3.0-or-later.

        Example: the repository -> no licence problem.
        """
        # Given: this repository
        repo = REPO
        # When: its licence is checked
        problems = check_free.licence_problems(repo)
        # Then: nothing is wrong
        self.assertEqual(problems, [])

    @mark.req('REQ-OPR-009')
    def test_another_licence_is_reported(self):
        """TC-OPR-009: a LICENSE with another text is a problem.

        Example: LICENSE "MIT License" -> one problem.
        """
        # Given: a repository with an MIT licence and the README of MIA
        self.write("LICENSE", "MIT License\n")
        shutil.copyfile(os.path.join(REPO, "README.md"), os.path.join(self.folder, "README.md"))
        # When: its licence is checked
        problems = check_free.licence_problems(self.folder)
        # Then: one problem
        self.assertEqual(len(problems), 1)

    @mark.req('REQ-OPR-009')
    def test_the_requirement_files_of_mia_list_no_paid_api_client(self):
        """TC-OPR-009: requirements.txt and requirements-db.txt list no paid-API client library.

        Example: Flask, ollama, psycopg -> nothing found.
        """
        # Given: the requirement files of this repository
        paths = [os.path.join(REPO, "requirements.txt"), os.path.join(REPO, "requirements-db.txt")]
        # When: they are checked
        found = check_free.paid_packages(paths)
        # Then: none is a paid-API client
        self.assertEqual(found, [])

    @mark.req('REQ-OPR-009')
    def test_a_paid_api_client_is_found_whatever_its_spelling(self):
        """TC-OPR-009: a paid-API client is found with a version, extras, another case or _ for -.

        Example: "OpenAI>=1.0", "anthropic[bedrock]==0.40", "google_generativeai" -> three packages.
        """
        # Given: a requirement file with three paid-API clients and two free packages
        path = self.write("requirements.txt", "# comment\nFlask==3.1.0\nOpenAI>=1.0\nanthropic[bedrock]==0.40\ngoogle_generativeai\nollama==0.6.3\n")
        # When: it is checked
        found = check_free.paid_packages([path])
        # Then: exactly the three, with their lines' package names normalized
        self.assertEqual(found, [(path, "openai"), (path, "anthropic"), (path, "google-generativeai")])

    @mark.req('REQ-OPR-009')
    def test_a_paid_api_host_in_the_web_log_is_found(self):
        """TC-OPR-009: a fetch of a paid API host (or a host below it) in the web log is found; a search query that names it is not.

        Example: https://api.openai.com/v1/models and https://eu.api.anthropic.com/x -> two hosts; https://de.wikipedia.org/ -> nothing.
        """
        # Given: a web log with two paid hosts and a free one
        path = self.web_log("https://de.wikipedia.org/wiki/Graz", "https://api.openai.com/v1/models", "https://eu.api.anthropic.com/x")
        # When: it is checked
        found = check_free.paid_hosts([path])
        # Then: the two paid hosts with their line numbers
        self.assertEqual(found, [(path, 2, "api.openai.com"), (path, 3, "eu.api.anthropic.com")])

    @mark.req('REQ-OPR-009')
    def test_the_command_says_free_and_open_or_names_the_problem(self):
        """TC-OPR-009: the command exits 0 on this repository with a clean log and 1 with a paid host in the log.

        Example: a log with wikipedia only -> exit 0, "free and open"; a log with api.openai.com -> exit 1, the host named.
        """
        # Given: a clean web log and one with a paid host
        clean = self.web_log("https://de.wikipedia.org/wiki/Graz")
        paid = self.write("web-2026-11.jsonl", json.dumps({"kind": "fetch", "url": "https://api.openai.com/v1/models"}) + "\n")
        command = [sys.executable, os.path.join(REPO, "tools", "check_free.py"), "--repo", REPO, "--log"]
        # When: the command checks each
        good = subprocess.run(command + [clean], capture_output=True, text=True, timeout=60)
        bad = subprocess.run(command + [paid], capture_output=True, text=True, timeout=60)
        # Then: the first passes, the second names the host
        self.assertEqual(good.returncode, 0)
        self.assertTrue(good.stdout.startswith("free and open"))
        self.assertEqual(bad.returncode, 1)
        self.assertIn("api.openai.com", bad.stdout)

if __name__ == '__main__':
    unittest.main()
