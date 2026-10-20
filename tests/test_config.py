"""
Tests for the configuration split: setup_cfg.json (the real file of a machine, not in git) and setup_cfg.example.json (tracked template with every option). The first start copies the example, the tools
fall back to it, and the example must list every option the code reads (so that it cannot go stale). Run with the MIA virtualenv: python tests/test_config.py
"""
import glob
import json
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import config as C                                    # noqa: E402
import web_tools                                      # noqa: E402

EXAMPLE = os.path.join(REPO, "setup_cfg.example.json")
# options that mean something different when they are present, so they cannot be listed with a neutral value (README.md explains them)
OMITTED = {"editor_token", "chat_token"}
# names found by the scan below that are not options of the file
NOT_OPTIONS = {"options", "profile", "EDITOR_TOKEN_INFO"}


def options_read_by_the_code():
    constants = {}
    for line in open(os.path.join(REPO, "constants.py"), encoding="utf-8"):
        match = re.match(r'(\w+_KEY)\s*=\s*"(\w+)"', line)
        if match:
            constants[match.group(1)] = match.group(2)
    found = {}
    for path in glob.glob(os.path.join(REPO, "*.py")) + glob.glob(os.path.join(REPO, "tools", "*.py")):
        text = open(path, encoding="utf-8").read()
        for match in re.finditer(r"""(?:cfg|config|options|settings|opts|self\._cfg|cfg_dict)\.get\(\s*(?:["'](\w+)["']|CONST\.(\w+_KEY)|(\w+_KEY))""", text):
            key = match.group(1) or constants.get(match.group(2) or match.group(3))
            if key:
                found.setdefault(key, set()).add(os.path.basename(path))
        for match in re.finditer(r"""cfg\[["'](\w+)["']\]""", text):
            found.setdefault(match.group(1), set()).add(os.path.basename(path))
    return found


class Loader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, content):
        with open(os.path.join(self.folder, name), "w", encoding="utf-8") as fp:
            fp.write(content)

    def test_the_first_start_copies_the_example(self):
        self.write("setup_cfg.example.json", '{"port": 1}')
        path, created = C.ensure(self.folder)
        self.assertEqual((os.path.basename(path), created), ("setup_cfg.json", True))
        self.assertEqual(json.load(open(path)), {"port": 1})

    def test_an_existing_configuration_is_never_overwritten(self):
        self.write("setup_cfg.example.json", '{"port": 1}')
        self.write("setup_cfg.json", '{"port": 99}')
        path, created = C.ensure(self.folder)
        self.assertFalse(created)
        self.assertEqual(json.load(open(path)), {"port": 99})
        self.assertEqual(json.load(open(os.path.join(self.folder, "setup_cfg.example.json"))), {"port": 1})

    def test_a_second_call_after_the_copy_creates_nothing_more(self):
        self.write("setup_cfg.example.json", '{"port": 1}')
        C.ensure(self.folder)
        self.assertFalse(C.ensure(self.folder)[1])

    def test_without_either_file_the_error_says_which(self):
        with self.assertRaises(FileNotFoundError) as caught:
            C.ensure(self.folder)
        self.assertIn("setup_cfg.example.json", str(caught.exception))

    def test_missing_options_are_listed_without_touching_the_file(self):
        self.write("setup_cfg.example.json", '{"port": 1, "new_option": [1, 2], "searxng_autostart": true}')
        self.write("setup_cfg.json", '{"port": 99}')
        before = open(os.path.join(self.folder, "setup_cfg.json")).read()
        self.assertEqual(C.missing(self.folder), {"new_option": [1, 2], "searxng_autostart": True})
        self.assertEqual(open(os.path.join(self.folder, "setup_cfg.json")).read(), before)

    def test_without_a_real_file_everything_is_missing(self):
        self.write("setup_cfg.example.json", '{"a": 1, "b": 2}')
        self.assertEqual(C.missing(self.folder), {"a": 1, "b": 2})

    def test_the_command_line_report(self):
        import subprocess
        self.write("setup_cfg.example.json", '{"port": 1, "new_option": "x"}')
        self.write("setup_cfg.json", '{"port": 99}')
        out = subprocess.run([sys.executable, os.path.join(REPO, "config.py"), self.folder], capture_output=True, text=True, timeout=30).stdout
        self.assertIn('"new_option": "x"', out)
        self.assertNotIn('"port"', out)
        self.write("setup_cfg.json", '{"port": 99, "new_option": "mine"}')
        out = subprocess.run([sys.executable, os.path.join(REPO, "config.py"), self.folder], capture_output=True, text=True, timeout=30).stdout
        self.assertIn("has every option", out)

    def test_tools_read_the_real_file_or_else_the_example(self):
        self.write("setup_cfg.example.json", "{}")
        self.assertTrue(C.default_path(self.folder).endswith("setup_cfg.example.json"))
        self.write("setup_cfg.json", "{}")
        self.assertTrue(C.default_path(self.folder).endswith("setup_cfg.json"))


class Example(unittest.TestCase):
    def test_it_is_valid_json_with_the_options_of_this_machine(self):
        data = json.load(open(EXAMPLE, encoding="utf-8"))
        for key in ("version", "version_light", "searxng_port", "searxng_autostart", "web_port", "sound_port", "voice_effect"):
            self.assertIn(key, data)
        self.assertGreaterEqual(len(data), 70)

    def test_every_option_the_code_reads_is_in_the_example(self):
        data = json.load(open(EXAMPLE, encoding="utf-8"))
        missing = {key: sorted(files) for key, files in options_read_by_the_code().items() if key not in data and key not in OMITTED and key not in NOT_OPTIONS}
        self.assertEqual(missing, {}, "add these options to setup_cfg.example.json (and describe them in README.md)")

    def test_the_options_that_change_meaning_when_present_are_not_listed(self):
        data = json.load(open(EXAMPLE, encoding="utf-8"))
        for key in OMITTED:
            self.assertNotIn(key, data)

    def test_the_listed_defaults_are_the_defaults_of_the_code(self):
        data = json.load(open(EXAMPLE, encoding="utf-8"))
        bare = web_tools.build_web_tools({}, None)[1]
        listed = web_tools.build_web_tools({k: data[k] for k in ("search_backends", "search_results", "web_timeout", "web_max_bytes", "web_max_chars")}, None)[1]
        self.assertEqual((listed.max_results, [b.name for b in listed.backends]), (bare.max_results, [b.name for b in bare.backends]))
        self.assertEqual(data["searxng_url"] or web_tools.searxng_url({}), web_tools.searxng_url({}))

    def test_the_real_file_is_not_tracked_and_the_example_is(self):
        ignore = open(os.path.join(REPO, ".gitignore"), encoding="utf-8").read().splitlines()
        self.assertIn("setup_cfg.json", ignore)
        self.assertNotIn("setup_cfg.example.json", ignore)

    def test_no_secret_is_in_the_example(self):
        text = open(EXAMPLE, encoding="utf-8").read().casefold()
        for word in ("token", "secret", "password"):
            self.assertNotIn('"%s"' % word, text)


if __name__ == "__main__":
    unittest.main()
