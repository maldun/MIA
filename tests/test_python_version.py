"""
N-2.1 T-05, TC-API-011 (REQ-API-011, D-63): Python 3.12 only. The image is built on python:3.12, README.md and requirements.txt name no other version,
and in the image the tests run on 3.12 (the whole suite in the image is the evidence of AC-20).  python tests/test_python_version.py
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                          # noqa: E402

IN_A_CONTAINER = os.path.exists("/run/.containerenv") or os.path.exists("/.dockerenv")


def read(*parts):
    with open(os.path.join(REPO, *parts), encoding="utf-8") as fp:
        return fp.read()


def lines_naming_python(text):
    """the lines that say which Python MIA needs"""
    return [line for line in text.splitlines() if re.search(r"[Pp]ython ?3\.\d+|python3\.\d+", line)]


class Python312(unittest.TestCase):
    """the Backend runs on Python 3.12 only (D-63): the image is built on it, the install notes name no other version, the tests run on it"""

    @mark.req("REQ-API-011")
    def test_the_image_is_built_on_python_3_12(self):
        """TC-API-011: the Containerfile of the Backend starts from python:3.12.

        Example: FROM docker.io/library/python:3.12-slim@sha256:... -> 3.12.
        """
        # Given
        containerfile = read("deploy", "Containerfile")
        # When
        bases = re.findall(r"^FROM \S*python:(\d+\.\d+)", containerfile, re.MULTILINE)
        # Then
        self.assertEqual(bases, ["3.12"])

    @mark.req("REQ-API-011")
    def test_the_install_notes_name_python_3_12_only(self):
        """TC-API-011: every line of README.md and requirements.txt that names a Python version names 3.12 and no other.

        Example: "python 3.11 to 3.13" -> refused; "Python 3.12" -> fine.
        """
        # Given
        lines = lines_naming_python(read("README.md")) + lines_naming_python(read("requirements.txt"))
        # When
        versions = {version for line in lines for version in re.findall(r"3\.(\d+)", line)}
        # Then
        self.assertTrue(lines)
        self.assertEqual(versions - {"10", "14"}, {"12"})

    @mark.req("REQ-API-011")
    @unittest.skipUnless(IN_A_CONTAINER, "only in the MIA image (bash tools/run_in_image.sh tests/test_python_version.py)")
    def test_the_tests_run_on_python_3_12_in_the_image(self):
        """TC-API-011: in the image the interpreter of the tests is 3.12.

        Example: python --version in localhost/mia -> Python 3.12.x.
        """
        # Given
        expected = (3, 12)
        # When
        running = sys.version_info[:2]
        # Then
        self.assertEqual(running, expected)

if __name__ == "__main__":
    unittest.main()
