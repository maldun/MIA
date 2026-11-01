"""Finding of the merge-gate run of G-V1: the tests that load ui/tools/chat_mock_server.py (test_chat_mock_server, test_review_wiring, test_converse_behaviours) put its routes, its
401 guard and its config patch on the shared MIA.web_app, so every later test of one `unittest discover` process failed and a second load died with "overwriting an existing
endpoint function: login". The mock server now gets its own web_app (checkout_copy.load_isolated) and leaves the shared one as it found it.
Needs the app and its packages: bash tools/run_in_image.sh tests/test_mock_server_isolation.py"""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))
os.environ.update({"ANSWER_DELAY": "0.3", "EVENT_GAP": "0", "MIA_TEST": "1"})

import checkout_copy  # noqa: E402
_LINK_DIR = checkout_copy.use()
MOCK = os.path.join(REPO, "ui", "tools", "chat_mock_server.py")


class SharedAppStaysClean(unittest.TestCase):
    def test_loading_the_mock_server_twice_leaves_the_shared_web_app_as_it_was(self):
        """two loads work, and the web_app, its routes and the config hook that the other tests see are unchanged"""
        from MIA import config, web_app
        rules = sorted(rule.rule + str(sorted(rule.methods)) for rule in web_app.app.url_map.iter_rules())
        guards = list(web_app.app.before_request_funcs.get(None, []))
        ensure = config.ensure
        for _ in range(2):
            server = checkout_copy.load_isolated("chat_mock_server", MOCK)
            self.assertIsNot(server.w, web_app)
        self.assertIs(sys.modules["MIA.web_app"], web_app)
        self.assertIs(config.ensure, ensure)
        self.assertEqual(sorted(rule.rule + str(sorted(rule.methods)) for rule in web_app.app.url_map.iter_rules()), rules)
        self.assertEqual(list(web_app.app.before_request_funcs.get(None, [])), guards)

    def test_a_test_after_the_mock_server_tests_in_one_process_still_passes(self):
        """the process of the gate's unit step: the mock server's tests first, then a web_app test, one `unittest` run"""
        names = ["test_chat_mock_server", "test_review_wiring", "test_converse_behaviours", "test_audio_router", "test_chat_backend"]
        done = subprocess.run([sys.executable, "-m", "unittest", "-q"] + names, cwd=HERE, capture_output=True, text=True, timeout=240)
        self.assertEqual(done.returncode, 0, done.stderr[-1500:])

    def test_the_accounts_wiring_gets_its_own_web_app_after_a_default_one_was_imported(self):
        """test_audio_router imports the default web_app (accounts off) first; test_accounts_wiring still needs its own one with accounts on"""
        done = subprocess.run([sys.executable, "-m", "unittest", "-q", "test_audio_router", "test_accounts_wiring"], cwd=HERE, capture_output=True, text=True, timeout=240)
        self.assertEqual(done.returncode, 0, done.stderr[-1500:])


if __name__ == "__main__":
    unittest.main()
