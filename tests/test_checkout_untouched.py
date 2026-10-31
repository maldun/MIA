"""
The guard of D-169: the tests that import MIA's code leave nothing in the checkout (data/, setup_cfg.json, mia.log or any other file).
Each such test file runs in its own process; the checkout's files (without .git and __pycache__) are compared before and after.
The files are those that use the shared setup tests/checkout_copy.py, and those that wrote into the checkout before it (the survey of D-169).
Needs flask: run with the image:  bash tools/run_in_image.sh tests/test_checkout_untouched.py   (about a minute)
"""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


WROTE_BEFORE = ("test_audio_router", "test_author_in_records", "test_character_integration", "test_character_stack", "test_chat_backend",
                "test_chat_mock_server", "test_chat_page", "test_converse_behaviours", "test_cpu_threads", "test_expression_llm", "test_gestures_api",
                "test_internal_auth", "test_ollama_remote", "test_persona_prompt", "test_presets_api", "test_requirements", "test_review_wiring",
                "test_runner_model_server", "test_shutdown_database", "test_shutdown", "test_skill_path_doc", "test_speech_repair", "test_speech_service",
                "test_speech_stop", "test_speech_text", "test_tailscale", "test_voice_effects")


def checkout_files():
    """every file of the checkout with its time and size, without .git and the bytecode caches"""
    found = {}
    for folder, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for name in files:
            path = os.path.join(folder, name)
            info = os.lstat(path)
            found[os.path.relpath(path, REPO)] = (info.st_mtime_ns, info.st_size)
    return found


def files_to_run():
    """the test files that use the shared setup, and those that wrote into the checkout before it"""
    names = set(WROTE_BEFORE)
    for name in os.listdir(HERE):
        if name.startswith("test_") and name.endswith(".py") and name != os.path.basename(__file__):
            with open(os.path.join(HERE, name), encoding="utf-8") as fp:
                if "import checkout_copy" in fp.read():
                    names.add(name[:-3])
    return sorted(os.path.join(HERE, name + ".py") for name in names)


class CheckoutUntouched(unittest.TestCase):
    def test_the_tests_that_import_mia_leave_nothing_in_the_checkout(self):
        """D-169: a run of every test file that imports MIA's code leaves no new or changed file in the checkout.

        Example: before the shared setup, tests/test_chat_page.py left data/, setup_cfg.json and mia.log -> this test failed and named them.
        """
        # Given: the files of the checkout
        before = checkout_files()
        # When: each test file runs in its own process (its own result does not matter here)
        for path in files_to_run():
            subprocess.run([sys.executable, path], cwd=HERE, capture_output=True, timeout=300)
        # Then: nothing is new or changed
        after = checkout_files()
        left = sorted(path for path, stamp in after.items() if before.get(path) != stamp)
        self.assertEqual(left, [], "files left or changed in the checkout: %s" % left[:20])


if __name__ == "__main__":
    unittest.main()
