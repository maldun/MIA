"""Report of missing options (N-4.2 T-01): TC-OPR-003, REQ-OPR-003. Run with: python tests/test_missing_options.py"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))

import config                                    # noqa: E402
from markers import mark                         # noqa: E402

EXAMPLE = os.path.join(REPO, "setup_cfg.example.json")
REMOVED = ("web_port", "voice_effect")
REPORTED = re.compile(r'^  "(\w+)": ')


class MissingOptions(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder, True)
        shutil.copyfile(EXAMPLE, os.path.join(self.folder, "setup_cfg.example.json"))
        with open(EXAMPLE, encoding="utf-8") as fp:
            self.example = json.load(fp)

    def write_config_without(self, names):
        """setup_cfg.json = the example with the options in `names` removed"""
        mine = {key: value for key, value in self.example.items() if key not in names}
        with open(os.path.join(self.folder, "setup_cfg.json"), "w", encoding="utf-8") as fp:
            json.dump(mine, fp, indent=2)

    def report(self):
        """the stdout of the command line report `python config.py <folder>`"""
        return subprocess.run([sys.executable, os.path.join(REPO, "config.py"), self.folder], capture_output=True, text=True, timeout=30).stdout

    @mark.req("REQ-OPR-003")
    def test_two_removed_options_are_named_and_no_others(self):
        """TC-OPR-003: a configuration with two options of the example removed; missing() names exactly these two.

        Example: setup_cfg.json without web_port and voice_effect -> {"web_port": ..., "voice_effect": ...}.
        """
        # Given: the example lists every option; the configuration lacks two of them
        self.write_config_without(REMOVED)
        # When: the missing options are asked for
        found = config.missing(self.folder)
        # Then: both are named with the value of the example, and no other
        self.assertEqual(found, {name: self.example[name] for name in REMOVED})

    @mark.req("REQ-OPR-003")
    def test_the_command_line_report_names_both_and_no_others(self):
        """TC-OPR-003: the report printed by config.py names the two removed options and no others.

        Example: setup_cfg.json without web_port and voice_effect -> two report lines, "web_port" and "voice_effect".
        """
        # Given: the configuration lacks two options of the example
        self.write_config_without(REMOVED)
        # When: the report is printed
        out = self.report()
        # Then: exactly these two option lines appear
        named = [m.group(1) for m in (REPORTED.match(line) for line in out.splitlines()) if m]
        self.assertEqual(sorted(named), sorted(REMOVED))

    @mark.req("REQ-OPR-003")
    def test_a_complete_configuration_reports_nothing_missing(self):
        """TC-OPR-003: with no option removed the report names no option.

        Example: setup_cfg.json equal to the example -> {} and no option line.
        """
        # Given: the configuration has every option of the example
        self.write_config_without(())
        # When: the missing options are asked for and the report is printed
        found = config.missing(self.folder)
        out = self.report()
        # Then: nothing is missing
        self.assertEqual(found, {})
        self.assertEqual([line for line in out.splitlines() if REPORTED.match(line)], [])

    @mark.req("REQ-OPR-003")
    def test_the_start_warning_names_both_and_no_others(self):
        """TC-OPR-003: the warning MIA prints at start names the two removed options and no others; a complete configuration gives no warning.

        Example: setup_cfg.json without web_port and voice_effect -> "Warning: ..." with two option lines; nothing removed -> None.
        """
        # Given: the configuration lacks two options of the example
        self.write_config_without(REMOVED)
        # When: the start warning is made
        text = config.warning(self.folder)
        # Then: it is a warning with exactly these two option lines
        self.assertTrue(text.startswith("Warning: "))
        named = [m.group(1) for m in (REPORTED.match(line) for line in text.splitlines()) if m]
        self.assertEqual(sorted(named), sorted(REMOVED))
        # And: with every option present there is no warning
        self.write_config_without(())
        self.assertIsNone(config.warning(self.folder))

    @mark.req("REQ-OPR-003")
    def test_mia_prints_the_warning_at_start(self):
        """TC-OPR-003 (D-120 Q2): __main__.py prints config.warning after it made sure setup_cfg.json exists.

        Example: __main__.py has "ensure_config(fpath)" and, after it, a print of "config_warning(fpath)".
        """
        # Given: the start code of MIA
        with open(os.path.join(REPO, "__main__.py"), encoding="utf-8") as fp:
            source = fp.read()
        # When: the call of the warning is looked for
        at = source.find("config_warning(fpath)")
        # Then: it is imported from config and comes after ensure_config
        self.assertIn("from .config import ensure as ensure_config, warning as config_warning", source)
        self.assertGreater(at, source.find("ensure_config(fpath)"))
        self.assertGreater(source.find("ensure_config(fpath)"), 0)


if __name__ == "__main__":
    unittest.main()
