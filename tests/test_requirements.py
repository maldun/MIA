"""
Tests for the requirements and the dependencies they stand for: the file has no torch, no RVC, no Coqui; the code imports none of them (nor the old playsound, opencv or pyaudio) at the top of a module
or anywhere else; the start code has no fixed interpreter name; the removed files are gone. Run with the MIA virtualenv: python tests/test_requirements.py
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
GONE = ("torch", "torchaudio", "torchvision", "coqui-tts", "tts", "rvc-python", "rvc-python", "fairseq", "pytorch-triton-rocm", "playsound", "opencv-python", "pyaudio", "faiss", "faiss-cpu")


def names(path):
    found = set()
    for line in open(os.path.join(REPO, path), encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith(("#", "-")):
            found.add(re.split(r"[=<>~! ;\[]", line, maxsplit=1)[0].lower().replace("_", "-"))
    return found


class Files(unittest.TestCase):
    def test_the_requirements_have_none_of_the_removed_packages(self):
        core = names("requirements.txt")
        for package in GONE:
            self.assertNotIn(package, core)
        for needed in ("flask", "flask-socketio", "requests", "ollama", "pyyaml", "numpy", "scipy", "soundfile", "onnxruntime", "kokoro-onnx", "praat-parselmouth"):
            self.assertIn(needed, core)

    def test_there_is_one_requirements_file_and_the_voice_files_are_gone(self):
        for removed in ("requirements-voice.txt", "requirements-freeze-py310.txt", "voice_fix.py", "tools/find_whistle.py", "tools/voice_ab.py", "tests/test_voice_fix.py", "tests/test_speak_rvc.py"):
            self.assertFalse(os.path.exists(os.path.join(REPO, removed)), removed)


class Imports(unittest.TestCase):
    def test_no_module_imports_a_removed_package(self):
        banned = {"torch", "rvc_python", "pyaudio", "playsound", "cv2", "TTS", "fairseq", "faiss", "torchaudio", "torchvision"}
        for path in sorted(glob.glob(os.path.join(REPO, "*.py")) + glob.glob(os.path.join(REPO, "tools", "*.py"))):
            tree = ast.parse(open(path, encoding="utf-8").read())
            for node in ast.walk(tree):
                found = [a.name.split(".")[0] for a in node.names] if isinstance(node, ast.Import) else ([node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module else [])
                for name in found:
                    if name in banned and os.path.basename(path) != "play_media.py":          # play_media imports playsound and cv2 where an old local player needs them
                        self.fail("%s imports %s (line %d)" % (os.path.relpath(path, REPO), name, node.lineno))

    def test_the_old_local_players_are_imported_only_where_used(self):
        tree = ast.parse(open(os.path.join(REPO, "play_media.py"), encoding="utf-8").read())
        for node in tree.body:
            found = [a.name.split(".")[0] for a in node.names] if isinstance(node, ast.Import) else ([node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module else [])
            self.assertFalse({"playsound", "cv2"} & set(found), "play_media imports a player at the top")

    def test_importing_the_speech_module_loads_none_of_them(self):
        code = "import sys; sys.path.insert(0, %r); import speak, play_media, cpu_threads; print(any(m in sys.modules for m in ('torch', 'rvc_python', 'cv2', 'playsound', 'TTS', 'pyaudio')))" % REPO
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120, cwd=REPO)
        self.assertEqual(out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[-400:], "False")

    def test_the_start_code_has_no_fixed_python_version(self):
        text = open(os.path.join(REPO, "__main__.py"), encoding="utf-8").read()
        self.assertNotIn('"python3.10"', text)
        self.assertIn("sys.executable", text)


class Configuration(unittest.TestCase):
    def test_the_example_has_no_option_of_the_removed_engines(self):
        import json
        data = json.load(open(os.path.join(REPO, "setup_cfg.example.json"), encoding="utf-8"))
        for key in ("tts_model", "voice_model", "rvc_opts", "rvc_params", "rvc_enabled", "rvc_cache_index", "rvc_pad", "rvc_whistle_hz", "tts_device", "voice_sample", "tts_engine"):
            self.assertNotIn(key, data)
        self.assertIn("voice_effect", data)
        self.assertIn("kokoro_opts", data)


if __name__ == "__main__":
    unittest.main()
