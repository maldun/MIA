"""
Tests for the speed-ups of MIA's voice in speak.py: the RVC index is read once, the padding of RVC, the warm-up.
No models are loaded (fakes stand in for faiss and RVC). Run with the MIA virtualenv: python tests/test_speak_rvc.py
"""
import importlib
import os
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)


class FakeIndex:
    def __init__(self, path):
        self.path = path
        self.ntotal = 5
        self.reconstructed = 0

    def reconstruct_n(self, start, count):
        self.reconstructed += 1
        return [f"vector{i}" for i in range(start, start + count)]

    def search(self, vectors, k):
        return "searched", k


class FakeFaiss:
    def __init__(self):
        self.reads = []

    def read_index(self, path):
        self.reads.append(path)
        return FakeIndex(path)

    def other_function(self):
        return "delegated"


class IndexCacheTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.speak = importlib.import_module("MIA.speak")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "voice.index")
        open(self.path, "w").close()
        self.fake = FakeFaiss()
        self.faiss = self.speak._FaissWithCache(self.fake)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_index_is_read_once(self):
        first = self.faiss.read_index(self.path)
        second = self.faiss.read_index(self.path)
        self.assertIs(first, second)
        self.assertEqual(len(self.fake.reads), 1)

    def test_all_vectors_are_copied_once(self):
        index = self.faiss.read_index(self.path)
        a = index.reconstruct_n(0, index.ntotal)
        b = index.reconstruct_n(0, index.ntotal)
        self.assertIs(a, b)
        self.assertEqual(index._index.reconstructed, 1)
        self.assertEqual(index.reconstruct_n(1, 2), ["vector1", "vector2"])     # other ranges still work

    def test_everything_else_is_passed_through(self):
        index = self.faiss.read_index(self.path)
        self.assertEqual(index.search("x", k=8), ("searched", 8))
        self.assertEqual(self.faiss.other_function(), "delegated")

    def test_a_changed_file_is_read_again(self):
        self.faiss.read_index(self.path)
        later = time.time() + 10
        os.utime(self.path, (later, later))
        self.faiss.read_index(self.path)
        self.assertEqual(len(self.fake.reads), 2)

    def test_installing_twice_does_not_wrap_twice(self):
        pipeline = importlib.import_module("rvc_python.modules.vc.pipeline")
        original = pipeline.faiss
        try:
            self.speak.cache_rvc_index()
            self.speak.cache_rvc_index()
            self.assertIsInstance(pipeline.faiss, self.speak._FaissWithCache)
            self.assertNotIsInstance(pipeline.faiss._faiss, self.speak._FaissWithCache)
        finally:
            pipeline.faiss = original


class PaddingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.speak = importlib.import_module("MIA.speak")

    def test_padding_is_whole_pitch_frames_and_aligned_with_the_voice_rate(self):
        for seconds in (0.25, 0.5, 1.0, 0.33):
            for rate in (32000, 40000, 48000):
                pad, target = self.speak.rvc_padding_samples(seconds, rate)
                self.assertEqual(pad % 160, 0)
                self.assertEqual(target * 16000, pad * rate)       # the same time at both rates
                self.assertAlmostEqual(pad / 16000, seconds, delta=0.01)
        self.assertEqual(self.speak.rvc_padding_samples(1, 40000), (16000, 40000))   # RVC's own value on a CPU
        self.assertEqual(self.speak.rvc_padding_samples(0, 40000), (160, 400))        # never zero (one frame)

    def test_the_padding_is_set_on_the_pipeline(self):
        class Pipeline:
            t_pad, t_pad_tgt, t_pad2 = 16000, 40000, 32000

        class VC:
            tgt_sr = 40000
            pipeline = Pipeline()

        class RVC:
            vc = VC()

        self.speak.set_rvc_padding(RVC(), 0.25)
        self.assertEqual((Pipeline.t_pad, Pipeline.t_pad_tgt, Pipeline.t_pad2), (16000, 40000, 32000))   # class untouched
        pipeline = RVC.vc.pipeline
        self.assertEqual((pipeline.t_pad, pipeline.t_pad_tgt, pipeline.t_pad2), (4000, 10000, 8000))


class WarmUpTest(unittest.TestCase):
    def test_a_failing_warm_up_does_not_stop_the_speech_server(self):
        speak = importlib.import_module("MIA.speak")
        speaker = speak.Speaker.__new__(speak.Speaker)
        speaker.render_voice = lambda text, path: (_ for _ in ()).throw(RuntimeError("no model"))
        speaker.warm_up()       # logs a warning, no exception

    def test_the_warm_up_renders_one_short_sentence(self):
        speak = importlib.import_module("MIA.speak")
        speaker = speak.Speaker.__new__(speak.Speaker)
        rendered = []
        speaker.render_voice = lambda text, path: rendered.append(text) or 0.5
        speaker.warm_up()
        self.assertEqual(rendered, ["Hello."])


if __name__ == "__main__":
    unittest.main()
