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
A whistle in the converted voice. Some voice models (RVC) produce a pure tone of a FIXED frequency on certain vowel sounds (the MikuAI model:
700 Hz (wandering 695-707 Hz), up to 40-60 dB above the speech around it, 100-250 ms long); the original TTS audio does not have it, and no RVC setting (pitch shift,
index, protect, pitch detection) removes it. Because the frequency is fixed, a narrow band-stop filter removes it, applied only where the
tone is present (a crossfade at the edges), so the rest of the speech stays untouched.

  find_tone_frames(x, rate, freq)   where the tone is (boolean per analysis frame)
  suppress_tone(x, rate, freq)      the audio without the tone
  tone_runs(x, rate), common_tone(...)  look for such a tone in several files of a voice, e.g. to learn the frequency of a new voice model
"""
import numpy as np
from scipy import signal

FRAME = 2048
HOP = 256
SEARCH_HZ = 14.0          # the tone wanders a little (695-707 Hz for 700): looked for within this distance of the configured frequency
SIDE_HZ = (40.0, 300.0)   # the level around it is measured in this distance from it (not too close, harmonics of the speech are there)
LOW_DB = 12.0             # frames where the tone is at least this far above its surroundings belong to it (it fades in and out over 100-250 ms) ...
HIGH_DB = 20.0            # ... if the run has a frame that is at least this far above its surroundings ...
DOMINANCE_DB = 4.0        # ... and in which the tone is this much louder than the strongest other peak of the vowel region (300-1500 Hz). In speech a
                          # harmonic that happens to be at the frequency is one of a series of similar peaks (never more than -6 dB in the
                          # test sentences), the whistle stands alone (+5 to +24 dB)
MEMBER_DOMINANCE_DB = 0.0   # frames of a run must at least be as loud as the strongest other peak
MIN_RUN_FRAMES = 5        # ... and the run lasts at least this many analysis frames (about 32 ms)
VOWEL_BAND = (300.0, 1500.0)
STOP_HZ = 34.0            # width of the band that is removed around the frequency
CASCADE = 2               # filtered twice: deeper
FADE_SECONDS = 0.015
GROW_FRAMES = 3           # the filtered part is a little longer than the detected tone


def _spectra(x, rate, size=FRAME, hop=HOP):
    x = np.pad(np.asarray(x, dtype=np.float64), (size // 2, size // 2))
    count = max(0, 1 + (len(x) - size) // hop)
    if count == 0:
        return np.zeros((0, size // 2 + 1)), np.fft.rfftfreq(size, 1 / rate)
    index = np.arange(size)[None, :] + hop * np.arange(count)[:, None]
    spectrum = np.abs(np.fft.rfft(x[index] * np.hanning(size), axis=1))
    return 20 * np.log10(spectrum + 1e-9), np.fft.rfftfreq(size, 1 / rate)


def _prominence(db, freqs, freq):
    """per frame: the highest level within SEARCH_HZ of freq minus the median level around it"""
    near = (freqs >= freq - SEARCH_HZ) & (freqs <= freq + SEARCH_HZ)
    around = ((freqs >= freq - SIDE_HZ[1]) & (freqs <= freq - SIDE_HZ[0])) | ((freqs >= freq + SIDE_HZ[0]) & (freqs <= freq + SIDE_HZ[1]))
    if not near.any() or not around.any():
        return np.zeros(len(db))
    return db[:, near].max(axis=1) - np.median(db[:, around], axis=1)


def _dominance(db, freqs, freq):
    """per frame: the level of the tone minus the strongest other peak between VOWEL_BAND (leaving out the surroundings of the tone)"""
    near = (freqs >= freq - SEARCH_HZ) & (freqs <= freq + SEARCH_HZ)
    others = (freqs >= VOWEL_BAND[0]) & (freqs <= VOWEL_BAND[1]) & (np.abs(freqs - freq) > SIDE_HZ[0])
    if not near.any() or not others.any():
        return np.full(len(db), -np.inf)
    return db[:, near].max(axis=1) - db[:, others].max(axis=1)


def find_tone_frames(x, rate, freq, low_db=LOW_DB, high_db=HIGH_DB, min_run=MIN_RUN_FRAMES, dominance_db=DOMINANCE_DB):
    """boolean per analysis frame (hop HOP samples): is the tone at freq present?"""
    db, freqs = _spectra(x, rate)
    if len(db) == 0:
        return np.zeros(0, dtype=bool)
    prominence = _prominence(db, freqs, freq)
    dominance = _dominance(db, freqs, freq)
    strong = (prominence >= high_db) & (dominance >= dominance_db)
    above = (prominence >= low_db) & (dominance >= MEMBER_DOMINANCE_DB)      # speech harmonics next to the tone do not join its run
    result = np.zeros(len(above), dtype=bool)
    start = None
    for i in range(len(above) + 1):
        inside = i < len(above) and above[i]
        if inside and start is None:
            start = i
        elif not inside and start is not None:
            if i - start >= min_run and strong[start:i].any():
                result[start:i] = True
            start = None
    return result


def _frame_mask(frames, length, rate):
    """0..1 per sample from the frame flags: grown a little, with crossfaded edges"""
    flags = np.convolve(frames.astype(float), np.ones(2 * GROW_FRAMES + 1), mode="same") > 0
    per_sample = np.repeat(flags.astype(float), HOP)[:length]
    if len(per_sample) < length:
        per_sample = np.pad(per_sample, (0, length - len(per_sample)), mode="edge")
    width = max(3, int(rate * FADE_SECONDS) | 1)
    window = np.hanning(width)
    return np.clip(np.convolve(per_sample, window / window.sum(), mode="same"), 0, 1)


def suppress_tone(x, rate, freq, low_db=LOW_DB, high_db=HIGH_DB, dominance_db=DOMINANCE_DB):
    """x without the tone at freq (a copy; unchanged where the tone is not present)"""
    x = np.asarray(x, dtype=np.float64)
    frames = find_tone_frames(x, rate, freq, low_db, high_db, MIN_RUN_FRAMES, dominance_db)
    if not frames.any() or len(x) < 64:
        return x.copy()
    sos = signal.butter(3, [freq - STOP_HZ / 2, freq + STOP_HZ / 2], btype="bandstop", fs=rate, output="sos")
    filtered = x
    for _ in range(CASCADE):
        filtered = signal.sosfiltfilt(sos, filtered)
    mask = _frame_mask(frames, len(x), rate)
    return x * (1 - mask) + filtered * mask


def tone_runs(x, rate, low=300.0, high=2500.0, prominence_db=25.0, dominance_db=6.0, wander_hz=8.0, min_seconds=0.07):
    """
    Steady tones: stretches of at least min_seconds in which the same strong, dominant peak (within wander_hz) stays, as a list of
    (frequency, seconds). The pitch of speech glides through a frequency in a few tens of milliseconds; the whistle stays for 100-250 ms.
    """
    db, freqs = _spectra(x, rate)
    band = (freqs >= low) & (freqs <= high)
    if len(db) == 0 or not band.any():
        return []
    peaks = []
    for frame in db:
        k = np.argmax(np.where(band, frame, -1e9))
        distance = np.abs(freqs - freqs[k])
        around = band & (distance >= SIDE_HZ[0]) & (distance <= SIDE_HZ[1])
        others = band & (distance > SIDE_HZ[0])
        ok = around.any() and others.any() and frame[k] - np.median(frame[around]) >= prominence_db and frame[k] - frame[others].max() >= dominance_db
        peaks.append(freqs[k] if ok else None)
    runs, current = [], []
    for f in peaks + [None]:
        if f is not None and (not current or abs(f - np.median(current)) <= wander_hz):
            current.append(f)
            continue
        if len(current) * HOP / rate >= min_seconds:
            runs.append((float(np.median(current)), len(current) * HOP / rate))
        current = [f] if f is not None else []
    return runs


def common_tone(runs_per_file, tolerance=8.0, min_seconds=0.07):
    """
    The frequency that has a steady tone in the largest share of the files, as (frequency, share of files); (None, 0.0) when there is none.
    runs_per_file: one list of (frequency, seconds) from tone_runs per file.
    """
    centres = sorted({round(f / tolerance) * tolerance for runs in runs_per_file for f, _ in runs})
    best, best_files = None, 0
    for centre in centres:
        files = sum(1 for runs in runs_per_file if sum(d for f, d in runs if abs(f - centre) <= tolerance) >= min_seconds)
        if files > best_files:
            best, best_files = centre, files
    if best is None:
        return None, 0.0
    near = [f for runs in runs_per_file for f, _ in runs if abs(f - best) <= tolerance]
    return float(np.median(near)), best_files / max(1, len(runs_per_file))
