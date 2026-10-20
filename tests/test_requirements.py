"""
Tests for the split of the requirements and the lazy imports that make it possible: the core file has no torch, RVC or Coqui; the voice file has them; the heavy modules are not imported by the
modules that the web app and the research use; no fixed interpreter name is left in the start code. Run with the MIA virtualenv: python tests/test_requirements.py
"""
import ast
import glob
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def names(path):
    found = set()
    for line in open(os.path.join(REPO, path), encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith(("#", "-")):
            found.add(re.split(r"[=<>~! ;\[]", line, maxsplit=1)[0].lower().replace("_", "-"))
        elif "#egg=" in line:
            found.add(line.split("#egg=")[1].lower().replace("_", "-"))
    return found


class Files(unittest.TestCase):
    def test_the_core_has_no_gpu_or_voice_conversion_packages(self):
        core = names("requirements.txt")
        for heavy in ("torch", "torchaudio", "torchvision", "coqui-tts", "rvc-python", "fairseq", "pytorch-triton-rocm", "playsound", "opencv-python", "pyaudio"):
            self.assertNotIn(heavy, core)
        for needed in ("flask", "flask-socketio", "requests", "ollama", "pyyaml", "numpy", "scipy", "soundfile", "onnxruntime"):
            self.assertIn(needed, core)

    def test_the_voice_extras_have_them(self):
        voice = names("requirements-voice.txt")
        for package in ("torch", "coqui-tts", "rvc-python"):
            self.assertIn(package, voice)

    def test_the_freeze_of_the_development_machine_is_kept(self):
        self.assertTrue(os.path.exists(os.path.join(REPO, "requirements-freeze-py310.txt")))
        self.assertIn("torch", names("requirements-freeze-py310.txt"))


class LazyImports(unittest.TestCase):
    HEAVY = ("torch", "rvc_python", "pyaudio", "playsound", "cv2", "TTS", "fairseq")

    def test_no_heavy_module_is_imported_at_the_top_of_the_core_files(self):
        for path in sorted(glob.glob(os.path.join(REPO, "*.py"))):
            tree = ast.parse(open(path, encoding="utf-8").read())
            for node in tree.body:                                           # only the top level of the module
                found = [a.name.split(".")[0] for a in node.names] if isinstance(node, ast.Import) else ([node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module else [])
                for name in found:
                    if os.path.basename(path) in ("voice_lab.py", "install_lama.py"):
                        continue                                              # command line tools of the voice work
                    self.assertNotIn(name, self.HEAVY, "%s imports %s at the top" % (os.path.basename(path), name))

    def test_importing_the_speech_module_does_not_load_torch(self):
        code = "import sys; sys.path.insert(0, %r); import speak, play_media, cpu_threads; print('torch' in sys.modules, 'rvc_python' in sys.modules, 'cv2' in sys.modules, 'playsound' in sys.modules)" % REPO
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120, cwd=REPO)
        self.assertEqual(out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[-400:], "False False False False")

    def test_the_start_code_has_no_fixed_python_version(self):
        text = open(os.path.join(REPO, "__main__.py"), encoding="utf-8").read()
        self.assertNotIn('"python3.10"', text)
        self.assertIn("sys.executable", text)


if __name__ == "__main__":
    unittest.main()
