"""
Tests for the whistle removal of the converted voice (voice_fix.py) with synthetic audio: speech-like sound (harmonics with moving pitch,
formant shaped, noise) with an injected tone of about 700 Hz. No models needed. Run with the MIA virtualenv: python tests/test_voice_fix.py
"""
import importlib
import os
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

RATE = 40000


def speech(seconds=2.0, f0_start=200.0, f0_end=260.0, seed=1):
    """harmonics of a gliding pitch with a vowel like envelope plus a little noise"""
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * RATE)) / RATE
    f0 = np.linspace(f0_start, f0_end, len(t))
    phase = 2 * np.pi * np.cumsum(f0) / RATE
    out = np.zeros(len(t))
    for harmonic in range(1, 30):
        freq = harmonic * f0
        envelope = 1.0 / (1 + ((freq - 600) / 400) ** 2) + 0.5 / (1 + ((freq - 1700) / 500) ** 2)
        out += envelope / harmonic ** 0.5 * np.sin(harmonic * phase)
    out += 0.02 * rng.standard_normal(len(t))
    return 0.1 * out / np.abs(out).max(), t


def with_tone(x, t, start=1.0, length=0.15, freq=700.0, amplitude=0.2):
    """a tone that fades in and out (like the whistle), its frequency wanders a little"""
    wander = freq + 4 * np.sin(2 * np.pi * 7 * t)
    tone = amplitude * np.sin(2 * np.pi * np.cumsum(wander) / RATE)
    gate = np.clip(np.minimum(t - start, start + length - t) / 0.04, 0, 1)
    return x + tone * gate


class ToneTest(unittest.TestCase):
    def setUp(self):
        self.vf = importlib.import_module("MIA.voice_fix")

    def level(self, x, start, stop, freq=700.0, width=17.0):
        spectrum = np.abs(np.fft.rfft(x[int(start * RATE):int(stop * RATE)] * np.hanning(int((stop - start) * RATE)), 1 << 16))
        freqs = np.fft.rfftfreq(1 << 16, 1 / RATE)
        band = (freqs >= freq - width) & (freqs <= freq + width)
        return 20 * np.log10(spectrum[band].max() + 1e-9)

    def test_the_tone_is_found_where_it_is(self):
        x, t = speech()
        y = with_tone(x, t)
        frames = self.vf.find_tone_frames(y, RATE, 700.0)
        times = np.nonzero(frames)[0] * self.vf.HOP / RATE
        self.assertGreater(len(times), 10)
        self.assertGreater(times.min(), 0.9)
        self.assertLess(times.max(), 1.3)

    def test_the_tone_is_much_weaker_afterwards(self):
        x, t = speech()
        y = with_tone(x, t)
        z = self.vf.suppress_tone(y, RATE, 700.0)
        before, after = self.level(y, 1.03, 1.12), self.level(z, 1.03, 1.12)
        self.assertGreater(before - after, 25)

    def test_speech_without_a_tone_is_not_touched(self):
        x, t = speech()
        z = self.vf.suppress_tone(x, RATE, 700.0)
        self.assertTrue(np.array_equal(x, z))

    def test_audio_far_from_the_tone_is_not_touched(self):
        x, t = speech()
        y = with_tone(x, t)
        z = self.vf.suppress_tone(y, RATE, 700.0)
        outside = (t < 0.7) | (t > 1.5)
        self.assertTrue(np.allclose(y[outside], z[outside], atol=1e-9))

    def test_a_gliding_voice_whose_harmonic_passes_700_hz_is_not_a_whistle(self):
        for start, end in ((200.0, 260.0), (260.0, 200.0), (150.0, 330.0)):      # the 3rd or 4th harmonic crosses 700 Hz
            x, t = speech(f0_start=start, f0_end=end)
            self.assertFalse(self.vf.find_tone_frames(x, RATE, 700.0).any(), (start, end))

    def test_a_short_blip_is_not_a_whistle(self):
        x, t = speech()
        y = with_tone(x, t, length=0.01)
        self.assertFalse(self.vf.find_tone_frames(y, RATE, 700.0).any())

    def test_a_weak_tone_is_left_alone(self):
        x, t = speech()
        y = with_tone(x, t, amplitude=0.0005)
        self.assertFalse(self.vf.find_tone_frames(y, RATE, 700.0).any())

    def test_a_tone_at_another_frequency_is_left_alone_but_can_be_found(self):
        x, t = speech()
        y = with_tone(x, t, freq=1100.0)
        self.assertTrue(np.array_equal(self.vf.suppress_tone(y, RATE, 700.0), y))
        runs = self.vf.tone_runs(y, RATE)
        self.assertTrue(any(abs(f - 1100) < 15 and seconds >= 0.07 for f, seconds in runs), runs)

    def test_the_common_tone_of_several_files_is_found_and_speech_pitch_is_not(self):
        files_with_tone = []
        for seed, start in ((1, 0.5), (2, 1.0), (3, 1.4)):
            x, t = speech(seed=seed, f0_start=180 + 30 * seed, f0_end=230 + 25 * seed)
            files_with_tone.append(self.vf.tone_runs(with_tone(x, t, start=start, length=0.2, freq=1100.0), RATE))
        frequency, share = self.vf.common_tone(files_with_tone)
        self.assertAlmostEqual(frequency, 1100.0, delta=12)
        self.assertEqual(share, 1.0)
        plain = [self.vf.tone_runs(speech(seed=seed, f0_start=180 + 30 * seed, f0_end=230 + 25 * seed)[0], RATE) for seed in (1, 2, 3)]
        self.assertLess(self.vf.common_tone(plain)[1], 0.4)

    def test_tiny_and_silent_audio(self):
        for x in (np.zeros(0), np.zeros(10), np.zeros(RATE), np.ones(100) * 0.01):
            z = self.vf.suppress_tone(x, RATE, 700.0)
            self.assertEqual(len(z), len(x))
            self.assertTrue(np.isfinite(z).all())

    def test_the_input_is_never_changed_in_place(self):
        x, t = speech()
        y = with_tone(x, t)
        copy = y.copy()
        self.vf.suppress_tone(y, RATE, 700.0)
        self.assertTrue(np.array_equal(y, copy))


class SpeakerHookTest(unittest.TestCase):
    def test_the_converted_file_is_cleaned_in_place(self):
        import soundfile as sf
        speak = importlib.import_module("MIA.speak")
        speaker = speak.Speaker.__new__(speak.Speaker)
        speaker._whistle_hz = 700.0
        x, t = speech()
        y = with_tone(x, t)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "voice.wav")
            sf.write(path, y, RATE, subtype="PCM_16")
            speaker.remove_whistle(path)
            cleaned, rate = sf.read(path)
        self.assertEqual(rate, RATE)
        self.assertEqual(len(cleaned), len(y))
        before = np.abs(np.fft.rfft(y[int(1.03 * RATE):int(1.12 * RATE)] * np.hanning(int(0.09 * RATE)), 1 << 16))
        after = np.abs(np.fft.rfft(cleaned[int(1.03 * RATE):int(1.12 * RATE)] * np.hanning(int(0.09 * RATE)), 1 << 16))
        freqs = np.fft.rfftfreq(1 << 16, 1 / RATE)
        band = (freqs > 683) & (freqs < 717)
        self.assertGreater(20 * np.log10(before[band].max() / after[band].max()), 25)

    def test_it_can_be_switched_off(self):
        speak = importlib.import_module("MIA.speak")
        calls = []
        speaker = speak.Speaker.__new__(speak.Speaker)
        speaker._whistle_hz = None
        speaker._rvc = type("Rvc", (), {"infer_file": lambda self, a, b: calls.append("infer")})()
        speaker.remove_whistle = lambda path: calls.append("remove")
        speaker.change_voice("a.wav", "b.wav")
        self.assertEqual(calls, ["infer"])
        speaker._whistle_hz = 700.0
        speaker.change_voice("a.wav", "b.wav")
        self.assertEqual(calls, ["infer", "infer", "remove"])


if __name__ == "__main__":
    unittest.main()
