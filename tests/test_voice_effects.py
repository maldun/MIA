"""
Tests for the simple voice changer (voice_effects.py) with synthetic voices, and its place in the speech pipeline (speak.py).
Run with the MIA virtualenv: python tests/test_voice_effects.py
"""
import importlib
import os
import sys
import tempfile
import time
import unittest

import numpy as np
import parselmouth
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

RATE = 24000


def voice(seconds=1.5, f0_start=200.0, f0_end=200.0, seed=1):
    """vowel like sound: harmonics of a (gliding) pitch with formants, a little noise"""
    rng = np.random.default_rng(seed)
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    f0 = np.linspace(f0_start, f0_end, n)
    phase = 2 * np.pi * np.cumsum(f0) / RATE
    out = np.zeros(n)
    for harmonic in range(1, 40):
        freq = harmonic * f0
        gain = 1.0 / (1 + ((freq - 700) / 300) ** 2) + 0.6 / (1 + ((freq - 1800) / 400) ** 2) + 0.3 / (1 + ((freq - 2900) / 500) ** 2)
        out += gain / harmonic ** 0.4 * np.sin(harmonic * phase)
    out += 0.01 * rng.standard_normal(n)
    out *= np.hanning(n) ** 0.3
    return 0.5 * out / np.abs(out).max()


def pitch_of(x, rate=RATE):
    f0 = parselmouth.Sound(x, rate).to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=900).selected_array["frequency"]
    f0 = f0[f0 > 0]
    return float(np.median(f0)), float(np.std(f0))


def centroid(x, rate=RATE):
    spectrum = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    freqs = np.fft.rfftfreq(len(x), 1 / rate)
    return float((freqs * spectrum).sum() / spectrum.sum())


class SettingsTest(unittest.TestCase):
    def setUp(self):
        self.ve = importlib.import_module("MIA.voice_effects")

    def test_nothing_means_no_effect(self):
        for config in (None, "", False, "off", {}, {"preset": "off"}):
            self.assertEqual(self.ve.settings_for(config), {}, config)

    def test_presets_by_name_or_object(self):
        self.assertEqual(self.ve.settings_for("anime"), self.ve.PRESETS["anime"])
        self.assertEqual(self.ve.settings_for({"preset": "anime"}), self.ve.PRESETS["anime"])
        self.assertEqual(set(self.ve.PRESETS), {"off", "anime", "anime_robot", "robot", "tiny"})

    def test_single_settings_override_the_preset(self):
        settings = self.ve.settings_for({"preset": "anime", "pitch_semitones": 7})
        self.assertEqual(settings["pitch_semitones"], 7)
        self.assertEqual(settings["formant_shift"], self.ve.PRESETS["anime"]["formant_shift"])
        self.assertEqual(self.ve.settings_for({"ring_hz": 50, "ring_mix": 0.2}), {"ring_hz": 50, "ring_mix": 0.2})

    def test_typos_and_nonsense_are_refused_with_a_message(self):
        for config in ("animee", {"preset": "nope"}, {"pitch": 3}, {"pitch_semitones": "high"}, {"pitch_semitones": 40}, {"formant_shift": 0},
                       {"ring_mix": 2}, {"pitch_semitones": True}, 5, ["anime"]):
            with self.assertRaises(ValueError, msg=str(config)):
                self.ve.settings_for(config)
        with self.assertRaisesRegex(ValueError, "known: off, anime"):
            self.ve.settings_for("animee")


class EffectTest(unittest.TestCase):
    def setUp(self):
        self.ve = importlib.import_module("MIA.voice_effects")
        self.x = voice()

    def apply(self, config, x=None):
        return self.ve.apply_effects(self.x if x is None else x, RATE, self.ve.settings_for(config))

    def test_no_settings_return_the_same_audio_as_a_copy(self):
        y = self.apply({})
        self.assertTrue(np.array_equal(y, self.x))
        self.assertIsNot(y, self.x)

    def test_the_pitch_goes_up_by_the_asked_number_of_semitones(self):
        before = pitch_of(self.x)[0]
        for semitones in (3, 5, 8):
            after = pitch_of(self.apply({"pitch_semitones": semitones}))[0]
            self.assertAlmostEqual(after / before, 2 ** (semitones / 12), delta=0.06, msg=semitones)

    def test_the_pitch_can_go_down(self):
        self.assertLess(pitch_of(self.apply({"pitch_semitones": -4}))[0], pitch_of(self.x)[0] * 0.85)

    def test_formant_shift_brightens_without_changing_the_pitch(self):
        before = pitch_of(self.x)[0]
        y = self.apply({"formant_shift": 1.25})
        self.assertAlmostEqual(pitch_of(y)[0], before, delta=before * 0.05)
        self.assertGreater(centroid(y), centroid(self.x) * 1.05)

    def test_the_anime_preset_is_higher_and_brighter(self):
        y = self.apply("anime")
        self.assertGreater(pitch_of(y)[0], pitch_of(self.x)[0] * 1.25)
        self.assertGreater(centroid(y), centroid(self.x))

    def test_pitch_range_zero_makes_the_voice_monotone(self):
        gliding = voice(f0_start=150.0, f0_end=260.0)
        natural = pitch_of(self.apply({"pitch_range": 1.0, "pitch_semitones": 1}, gliding))[1]
        flat = pitch_of(self.apply({"pitch_range": 0.0, "pitch_semitones": 1}, gliding))[1]
        self.assertLess(flat, natural * 0.3)
        self.assertGreater(natural, 15)

    def test_ring_modulation_adds_sidebands(self):
        y = self.apply({"ring_hz": 75, "ring_mix": 0.5})
        self.assertFalse(np.allclose(y, self.x))
        self.assertTrue(np.isfinite(y).all())

    def test_comb_and_bitcrush_stay_stable_on_long_audio(self):
        long = voice(seconds=20.0)
        for config in ({"comb_ms": 4.0, "comb_mix": 1.0}, {"bitcrush": 8000}, "robot"):
            y = self.apply(config, long)
            self.assertTrue(np.isfinite(y).all(), config)
            self.assertLessEqual(np.abs(y).max(), np.abs(long).max() * 1.0001, config)

    def test_length_and_loudness_are_kept_for_every_preset(self):
        for name in self.ve.PRESETS:
            y = self.apply(name)
            self.assertEqual(len(y), len(self.x), name)
            self.assertLessEqual(np.abs(y).max(), np.abs(self.x).max() * 1.0001, name)
            if name != "off":
                self.assertGreater(np.abs(y).max(), np.abs(self.x).max() * 0.99, name)

    def test_silence_noise_and_tiny_audio_do_not_break(self):
        rng = np.random.default_rng(3)
        for x in (np.zeros(RATE), 0.05 * rng.standard_normal(RATE), np.zeros(10), voice(seconds=0.05), np.zeros(0)):
            for name in ("anime", "robot"):
                y = self.ve.apply_effects(x, RATE, self.ve.settings_for(name))
                self.assertEqual(len(y), len(x))
                self.assertTrue(np.isfinite(y).all())

    def test_the_input_is_not_changed(self):
        copy = self.x.copy()
        self.apply("anime_robot")
        self.assertTrue(np.array_equal(self.x, copy))

    def test_it_is_much_faster_than_speaking(self):
        long = voice(seconds=10.0)
        started = time.perf_counter()
        self.apply("anime_robot", long)
        self.assertLess(time.perf_counter() - started, 10.0 * 0.15)


class SpeakerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.speak = importlib.import_module("MIA.speak")

    def make(self, effect):
        speaker = self.speak.Speaker.__new__(self.speak.Speaker)
        speaker._rvc_enabled = False
        speaker._effect = importlib.import_module("MIA.voice_effects").settings_for(effect)
        return speaker

    def test_a_rendered_file_gets_the_effect(self):
        speaker = self.make("anime")
        x = voice()

        def fake_tts(msg, path):
            sf.write(path, x, RATE, subtype="PCM_16")
            return True

        speaker.text2speech = fake_tts
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.wav")
            duration = speaker.render_voice("Hello.", path)
            y, rate = sf.read(path)
        self.assertEqual(rate, RATE)
        self.assertAlmostEqual(duration, len(x) / RATE, delta=0.05)
        self.assertGreater(pitch_of(y)[0], pitch_of(x)[0] * 1.25)

    def test_without_an_effect_the_file_is_as_rendered(self):
        speaker = self.make(None)
        x = voice()
        speaker.text2speech = lambda msg, path: sf.write(path, x, RATE, subtype="PCM_16") or True
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.wav")
            speaker.render_voice("Hello.", path)
            y, _ = sf.read(path)
        self.assertLess(np.abs(y - x).max(), 1e-3)

    def test_a_typo_in_the_configuration_stops_the_start_with_a_clear_message(self):
        with self.assertRaisesRegex(ValueError, "unknown voice_effect preset 'animee'"):
            self.speak.Speaker(tts_engine="kokoro", rvc_enabled=False, voice_effect="animee")


if __name__ == "__main__":
    unittest.main()
