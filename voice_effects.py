#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIA - MIA Is not an Assistant
#Copyright (C) 2017  Stefan Reiterer

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
A simple voice changer for an artificial character: effects on the TTS audio (it replaced a neural voice conversion, RVC, in October 2026). It needs a fraction
of the CPU time, and it has no whistle or other artifacts of a trained voice model.

  pitch_semitones   raises (or lowers) the pitch of the voice
  formant_shift     moves the resonances of the vocal tract (1.0 = unchanged, above 1 = a smaller head: girlish; Praat "Change gender")
  pitch_range       1.0 = the natural intonation, below 1 flattens it, 0 = monotone (robotic)
  ring_hz, ring_mix ring modulation with a low tone: metallic, robotic (the voice is multiplied with a sine; mix 0..1)
  comb_ms, comb_mix a very short echo that makes the voice resonate like a tube (metallic); the delay is in milliseconds
  bitcrush          lo-fi digital sound: the sample rate is reduced to this many Hz and the resolution to 8 bit steps (0 = off)
  sparkle_db        raises the high frequencies (above 3.5 kHz): airy, bright, "cute"

Presets (name -> settings) combine them, the settings of a preset can be changed one by one in setup_cfg.json:
  "voice_effect": {"preset": "anime_robot", "pitch_semitones": 5}
"""
import numpy as np
from scipy import signal

try:
    import parselmouth
    from parselmouth.praat import call
except ImportError:      # the effect without pitch and formant shift still works
    parselmouth = None
    call = None

DEFAULTS = {"pitch_semitones": 0.0, "formant_shift": 1.0, "pitch_range": 1.0, "ring_hz": 0.0, "ring_mix": 0.0,
            "comb_ms": 0.0, "comb_mix": 0.0, "bitcrush": 0, "sparkle_db": 0.0}

PRESETS = {
    "off": {},
    # a higher, brighter voice: young and girlish
    "anime": {"pitch_semitones": 5.0, "formant_shift": 1.13, "sparkle_db": 3.0},
    # the same with a metallic edge: a robot with an anime voice
    "anime_robot": {"pitch_semitones": 5.0, "formant_shift": 1.13, "pitch_range": 0.6, "ring_hz": 75.0, "ring_mix": 0.18,
                    "comb_ms": 3.5, "comb_mix": 0.25, "sparkle_db": 3.0},
    # a clearly artificial voice: flat intonation, ring modulation, lo-fi
    "robot": {"pitch_semitones": 1.0, "formant_shift": 1.0, "pitch_range": 0.0, "ring_hz": 60.0, "ring_mix": 0.35,
              "comb_ms": 4.0, "comb_mix": 0.35, "bitcrush": 11025},
    # even higher, for a small, cute character
    "tiny": {"pitch_semitones": 8.0, "formant_shift": 1.22, "sparkle_db": 4.0},
}

LIMITS = {"pitch_semitones": (-12.0, 14.0), "formant_shift": (0.7, 1.6), "pitch_range": (0.0, 2.0), "ring_hz": (0.0, 400.0),
          "ring_mix": (0.0, 1.0), "comb_ms": (0.0, 20.0), "comb_mix": (0.0, 1.0), "bitcrush": (0, 24000), "sparkle_db": (-12.0, 12.0)}


def settings_for(config):
    """
    The effect settings for "voice_effect" of the configuration: a preset name ("anime") or a dict {"preset": "anime", "pitch_semitones": 6}.
    Unknown names or keys and values out of range raise ValueError with a message (the speech server refuses to start with a typo).
    None / "off" / {} give an empty dict (no effect).
    """
    if config in (None, "", False):
        return {}
    if isinstance(config, str):
        config = {"preset": config}
    if not isinstance(config, dict):
        raise ValueError("voice_effect must be a preset name or an object")
    config = dict(config)
    name = config.pop("preset", None)
    if name is not None and name not in PRESETS:
        raise ValueError(f"unknown voice_effect preset '{name}' (known: {', '.join(PRESETS)})")
    settings = dict(PRESETS.get(name, {}))
    for key, value in config.items():
        if key not in DEFAULTS:
            raise ValueError(f"unknown voice_effect setting '{key}' (known: {', '.join(DEFAULTS)})")
        settings[key] = value
    for key, value in settings.items():
        low, high = LIMITS[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not low <= value <= high:
            raise ValueError(f"voice_effect '{key}' must be a number between {low} and {high}")
    return settings


def _median_pitch(sound):
    pitch = sound.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=600)
    voiced = pitch.selected_array["frequency"]
    voiced = voiced[voiced > 0]
    return float(np.median(voiced)) if len(voiced) else 0.0


def _change_voice(samples, rate, semitones, formant_shift, pitch_range):
    """pitch, formants and intonation with Praat's "Change gender" (a pitch synchronous method: good quality and fast)"""
    if parselmouth is None or (semitones == 0 and formant_shift == 1.0 and pitch_range == 1.0):
        return samples
    sound = parselmouth.Sound(samples, rate)
    median = _median_pitch(sound)
    if median <= 0:
        return samples          # no voiced speech (a breath, a click): nothing to shift
    new_median = median * 2 ** (semitones / 12.0)
    changed = call(sound, "Change gender", 75, 600, float(formant_shift), float(new_median), float(pitch_range), 1.0)
    return np.asarray(changed.values[0], dtype=np.float64)


def _ring(samples, rate, hz, mix):
    t = np.arange(len(samples)) / rate
    return samples * (1 - mix) + samples * np.sin(2 * np.pi * hz * t) * mix


def _comb(samples, rate, milliseconds, mix):
    """the voice plus a copy of itself a few milliseconds later (feedback): resonance of a tube"""
    delay = max(1, int(round(rate * milliseconds / 1000.0)))
    feedback = 0.6 * min(1.0, mix * 2.0)          # stays below 1: stable
    a = np.zeros(delay + 1)
    a[0] = 1.0
    a[delay] = -feedback
    wet = signal.lfilter([1.0], a, samples)
    return samples * (1 - mix) + wet * mix


def _bitcrush(samples, rate, target_rate):
    if target_rate <= 0 or target_rate >= rate:
        return samples
    low = signal.resample_poly(samples, int(target_rate), int(rate))
    peak = np.abs(low).max() or 1.0
    low = np.round(low / peak * 127.0) / 127.0 * peak          # 8 bit steps
    return signal.resample_poly(low, int(rate), int(target_rate))[: len(samples)]


def _sparkle(samples, rate, gain_db):
    """a shelf that raises everything above 3.5 kHz by gain_db"""
    if gain_db == 0 or rate <= 8000:
        return samples
    high = signal.butter(2, 3500.0, btype="highpass", fs=rate, output="sos")
    return samples + (10 ** (gain_db / 20.0) - 1.0) * signal.sosfilt(high, samples)


def apply_effects(samples, rate, settings):
    """
    The audio (float, mono) with the effects of settings (see settings_for); same length, never louder than the input.
    """
    samples = np.asarray(samples, dtype=np.float64)
    if len(samples) < int(rate * 0.1) or not settings:
        return samples.copy()
    peak = np.abs(samples).max()
    if peak == 0:
        return samples.copy()
    s = dict(DEFAULTS, **settings)
    out = _change_voice(samples, rate, s["pitch_semitones"], s["formant_shift"], s["pitch_range"])
    if s["ring_hz"] and s["ring_mix"]:
        out = _ring(out, rate, s["ring_hz"], s["ring_mix"])
    if s["comb_ms"] and s["comb_mix"]:
        out = _comb(out, rate, s["comb_ms"], s["comb_mix"])
    if s["bitcrush"]:
        out = _bitcrush(out, rate, s["bitcrush"])
    out = _sparkle(out, rate, s["sparkle_db"])
    # the same length as the input (Praat may differ by a few samples) and the same loudness
    if len(out) != len(samples):
        out = out[: len(samples)] if len(out) > len(samples) else np.pad(out, (0, len(samples) - len(out)))
    top = np.abs(out).max()
    if top > 0:
        out = out * (peak / top)
    return out
