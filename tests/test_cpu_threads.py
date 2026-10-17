"""
Tests for the "cpu_threads" setting (cpu_threads.py, speak.py, communicator.py).
Run with the MIA virtualenv: python tests/test_cpu_threads.py
"""
import importlib
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# the code uses relative imports as package "MIA": make the repository importable under that name
_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)


def write_cfg(folder, **values):
    path = os.path.join(folder, "cfg.json")
    with open(path, "w") as fp:
        json.dump(values, fp)
    return path


def run_python(code, timeout=120):
    """runs code in a fresh interpreter (clean thread pools) and returns its last output line"""
    env = dict(os.environ, PYTHONPATH=_LINK_DIR)
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        env.pop(name, None)
    result = subprocess.run([sys.executable, "-c", textwrap.dedent(code)], capture_output=True, text=True, timeout=timeout, env=env)
    assert result.returncode == 0, result.stderr[-1500:]
    return result.stdout.strip().splitlines()[-1]


class Parse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ct = importlib.import_module("MIA.cpu_threads")

    def test_valid_values(self):
        for value, expected in [(4, 4), ("4", 4), (" 6 ", 6), (1, 1), (4.0, 4)]:
            self.assertEqual(self.ct.parse(value), expected, value)

    def test_no_limit(self):
        for value in [None, 0, "0", -2, "-2", "", "abc", "2.5", True, False, [4], {}]:
            self.assertIsNone(self.ct.parse(value), repr(value))

    def test_environment_is_set_for_the_thread_libraries(self):
        env = {}
        self.ct.limit_environment(3, env)
        for name in ["OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
            self.assertEqual(env[name], "3")

    def test_environment_untouched_without_limit(self):
        env = {"OMP_NUM_THREADS": "12"}
        self.ct.limit_environment(None, env)
        self.ct.limit_environment(0, env)
        self.assertEqual(env, {"OMP_NUM_THREADS": "12"})

    def test_llm_options(self):
        original = {"num_ctx": 8192}
        merged = self.ct.add_to_llm_options(original, 4)
        self.assertEqual(merged, {"num_ctx": 8192, "num_thread": 4})
        self.assertEqual(original, {"num_ctx": 8192})                     # the given dict is not changed
        self.assertEqual(self.ct.add_to_llm_options(None, 4), {"num_thread": 4})
        self.assertEqual(self.ct.add_to_llm_options({"num_thread": 2}, 4), {"num_thread": 2})   # explicit wins
        self.assertEqual(self.ct.add_to_llm_options(original, None), original)                   # no limit: as before
        self.assertIsNone(self.ct.add_to_llm_options(None, None))


class ConfigFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ct = importlib.import_module("MIA.cpu_threads")

    def test_reads_the_setting(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.ct.from_config_file(write_cfg(tmp, cpu_threads=3)), 3)
            self.assertIsNone(self.ct.from_config_file(write_cfg(tmp, other=1)))
            self.assertIsNone(self.ct.from_config_file(write_cfg(tmp, cpu_threads=0)))

    def test_missing_or_broken_files_mean_no_limit(self):
        self.assertIsNone(self.ct.from_config_file("/nonexistent/cfg.json"))
        with tempfile.TemporaryDirectory() as tmp:
            broken = os.path.join(tmp, "broken.json")
            with open(broken, "w") as fp:
                fp.write("{not json")
            self.assertIsNone(self.ct.from_config_file(broken))
            with open(broken, "w") as fp:
                fp.write("[1, 2]")
            self.assertIsNone(self.ct.from_config_file(broken))

    def test_early_limit_takes_the_first_json_argument(self):
        old = {k: os.environ.get(k) for k in self.ct.THREAD_ENV_VARS}
        try:
            with tempfile.TemporaryDirectory() as tmp:
                cfg = write_cfg(tmp, cpu_threads=5)
                self.assertEqual(self.ct.early_limit_from_argv(["speak.py", "-t", cfg, "expressions.json"]), 5)
                self.assertEqual(os.environ["OMP_NUM_THREADS"], "5")
                # without a .json argument the default file is used
                self.assertEqual(self.ct.early_limit_from_argv(["speak.py", "-g"], default_cfg=write_cfg(tmp, cpu_threads=2)), 2)
                self.assertIsNone(self.ct.early_limit_from_argv(["speak.py"]))
        finally:
            for name, value in old.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value


class RealEffect(unittest.TestCase):
    """Fresh interpreters: does the limit really reach torch and onnxruntime?"""

    def test_env_set_early_limits_torch_without_any_further_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_cfg(tmp, cpu_threads=3)
            out = run_python(f"""
                import sys
                sys.argv = ['speak.py', {cfg!r}]
                from MIA.cpu_threads import early_limit_from_argv
                early_limit_from_argv(sys.argv)
                import torch                      # imported after the environment is set, like in speak.py
                print(torch.get_num_threads())
            """)
        self.assertEqual(out, "3")

    def test_without_the_setting_torch_uses_all_its_threads(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_cfg(tmp, other=1)
            out = run_python(f"""
                import sys
                sys.argv = ['speak.py', {cfg!r}]
                from MIA.cpu_threads import early_limit_from_argv
                early_limit_from_argv(sys.argv)
                import torch
                print(torch.get_num_threads())
            """)
        self.assertGreater(int(out), 3)

    def test_limit_torch_after_import(self):
        out = run_python("""
            import torch
            from MIA.cpu_threads import limit_torch
            before = torch.get_num_threads()
            limit_torch(2)
            print(before, torch.get_num_threads())
        """)
        before, after = out.split()
        self.assertGreater(int(before), 2)
        self.assertEqual(after, "2")

    def test_onnx_session_options(self):
        out = run_python("""
            from MIA.cpu_threads import onnx_session_options
            o = onnx_session_options(3)
            print(o.intra_op_num_threads, o.inter_op_num_threads, onnx_session_options(None))
        """)
        self.assertEqual(out, "3 1 None")


class CommunicatorAndSpeaker(unittest.TestCase):
    def test_communicator_passes_num_thread_to_both_models(self):
        comm_module = importlib.import_module("MIA.communicator")
        with tempfile.TemporaryDirectory() as tmp:
            kwargs = dict(history_file=os.path.join(tmp, "memories.json"), long_time_history_file=os.path.join(tmp, "long.json"),
                          version="big", version_light="small", llm_options={"num_ctx": 8192})
            comm = comm_module.Communicator(cpu_threads=4, default_profile="light", **kwargs)
            self.assertEqual(comm._profiles["full"], ("big", {"num_ctx": 8192, "num_thread": 4}))
            self.assertEqual(comm._profiles["light"], ("small", {"num_thread": 4}))
            self.assertEqual(comm.llm_options, {"num_thread": 4})   # the light profile is active
            plain = comm_module.Communicator(**kwargs)               # no setting: exactly as before
            self.assertEqual(plain._profiles["full"], ("big", {"num_ctx": 8192}))
            self.assertIsNone(plain._profiles["light"][1])

    def test_speaker_applies_the_limit(self):
        # Speaker with the model loading switched off: only the thread handling is checked
        with tempfile.TemporaryDirectory() as tmp:
            cfg = write_cfg(tmp, cpu_threads=3)
            out = run_python(f"""
                import sys
                sys.argv = ['speak.py', {cfg!r}]
                from MIA import speak
                speak.Speaker.init_tts_model = lambda self, *a: None
                speaker = speak.Speaker(tts_device="cpu", rvc_enabled=False, cpu_threads=2)
                import torch
                print(speaker._cpu_threads, torch.get_num_threads())
            """, timeout=240)
        self.assertEqual(out, "2 2")

    def test_speaker_without_setting_keeps_all_threads(self):
        out = run_python("""
            import sys
            from MIA import speak
            speak.Speaker.init_tts_model = lambda self, *a: None
            speaker = speak.Speaker(tts_device="cpu", rvc_enabled=False)
            import torch
            print(speaker._cpu_threads, torch.get_num_threads() > 3)
        """, timeout=240)
        self.assertEqual(out, "None True")

    def test_kokoro_is_built_with_the_thread_limit(self):
        with open(os.path.join(REPO, "speak.py")) as fp:
            source = fp.read()
        self.assertIn("onnx_session_options(self._cpu_threads)", source)
        self.assertIn("Kokoro.from_session(session, voices)", source)
        self.assertIn("early_limit_from_argv(sys.argv", source)
        self.assertLess(source.index("early_limit_from_argv(sys.argv"), source.index("import torch\n"), "env must be set before torch is imported")


if __name__ == "__main__":
    unittest.main(verbosity=2)
