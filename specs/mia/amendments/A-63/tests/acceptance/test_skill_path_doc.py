"""
TC-EVL-006 (N-4.1 T-06): the document of the skill path (docs/skill-path.md) has every step, its examples run with the fake model, and its links resolve.
A fenced block marked `python run` or `bash run` is executed from the repository root (`bash run exit=1` says that exit code 1 is the expected result).
Protected since A-63 (D-164). Run: python tests/acceptance/test_skill_path_doc.py
"""
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))
from markers import mark                              # noqa: E402

DOC = os.path.join(REPO, "docs", "skill-path.md")
STEPS = ["idea", "skill file and pipeline", "validation", "specification and benchmark", "declaration", "draft and promotion", "time record"]


def read():
    with open(DOC, encoding="utf-8") as fp:
        return fp.read()


def blocks(text):
    """[(language, options, code)] of the fenced blocks marked `run`"""
    found = []
    for m in re.finditer(r"^```(\w+) run([^\n]*)\n(.*?)^```", text, re.M | re.S):
        found.append((m.group(1), m.group(2).strip(), m.group(3)))
    return found


class SkillPathDoc(unittest.TestCase):
    @mark.req("REQ-EVL-006")
    def test_every_step_has_a_section(self):
        """TC-EVL-006: the document of the skill path has a section for each of its seven steps.

        Example: idea, skill file and pipeline, validation, specification and benchmark, declaration, draft and promotion, time record -> one heading each.
        """
        headings = [h.lower() for h in re.findall(r"^##+ (?:Step \d+: )?(.+)$", read(), re.M)]
        for step in STEPS:
            self.assertTrue(any(step in h for h in headings), "no section for: " + step)

    @mark.req("REQ-EVL-006")
    def test_the_lookup_is_the_example(self):
        """TC-EVL-006: the lookup (the research pipeline research.baseline) is the example of the document.

        Example: docs/skill-path.md mentions "lookup" and "research.baseline".
        """
        text = read().lower()
        self.assertIn("lookup", text)
        self.assertIn("research.baseline", text)

    @mark.req("REQ-EVL-006")
    def test_the_examples_run_with_the_fake_model(self):
        """TC-EVL-006: the shell and Python examples marked `run` in the document run from the repository root with a scripted model.

        Example: each block exits with 0, or with the code its marker names (`exit=1` for check_baselines.py while baselines are missing).
        """
        # Given: the marked blocks, at least two of each language
        found = blocks(read())
        self.assertGreaterEqual(len([b for b in found if b[0] == "python"]), 2)
        self.assertGreaterEqual(len([b for b in found if b[0] == "bash"]), 2)
        env = dict(os.environ, PYTHONPATH=REPO, PYTHONDONTWRITEBYTECODE="1")
        # When / Then: each one runs with its expected exit code
        for language, options, code in found:
            expected = int(re.search(r"exit=(\d+)", options).group(1)) if "exit=" in options else 0
            command = [sys.executable, "-c", code] if language == "python" else ["bash", "-c", "set -u\n" + code]
            done = subprocess.run(command, cwd=REPO, env=env, capture_output=True, text=True, timeout=300)
            self.assertEqual(done.returncode, expected, "%s block failed:\n%s\n%s\n%s" % (language, code, done.stdout[-800:], done.stderr[-800:]))

    @mark.req("REQ-EVL-006")
    def test_the_links_resolve(self):
        """TC-EVL-006: every relative link of the document points to an existing file.

        Example: [ui/README.md](../ui/README.md) -> the file exists; http links are not followed.
        """
        # Given: the folder of the document
        base = os.path.dirname(DOC)
        # When / Then: each relative link target exists
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", read()):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            self.assertTrue(os.path.exists(os.path.normpath(os.path.join(base, target))), "broken link: " + target)


if __name__ == "__main__":
    unittest.main()
