"""
Renders the same sentences (with many s, f, th and p sounds) with different RVC settings and measures two typical artifacts: jumps of the
pitch (octave errors) and tonal whistling in the unvoiced parts. Folder 0_kokoro_raw has the voice WITHOUT RVC: if a sound is already
there, it comes from Kokoro, not from the voice model. Listen to the folders, compare A_current with the others.

Run with the MIA virtualenv from the MIA folder (MIA does not have to run):
  python tools/voice_ab.py --models-root <MIA folder with voice/models> --out /tmp/voice_ab
"""
import argparse
import json
import os
import sys
import tempfile

import numpy as np
import parselmouth
import soundfile as sf

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--models-root", default=None, help="MIA folder that has voice/models (default: this folder)")
parser.add_argument("--out", default=os.path.join(tempfile.gettempdir(), "voice_ab"), help="folder for the rendered WAV files")
args = parser.parse_args()

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = args.models_root or REPO
link = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(link, "MIA"))
sys.path.insert(0, link)
from MIA.config import default_path as default_config  # noqa: E402
cfg = json.load(open(default_config(REPO)))
cfg["kokoro_opts"] = dict(cfg["kokoro_opts"], model=os.path.join(MODELS, "voice/models/kokoro/kokoro-v1.0.onnx"),
                          voices=os.path.join(MODELS, "voice/models/kokoro/voices-v1.0.bin"))
cfg["tts_warmup"] = False
from MIA.speak import Speaker  # noqa: E402

OUT = args.out
SENTENCES = [
    "She sells seashells by the seashore.",
    "Thirty-three thieves thought they thrilled the throne.",
    "Peter Piper picked a peck of pickled peppers.",
    "Fresh fish and fine fruit for everyone, please.",
    "I think you were right, and that makes me very happy.",
]
VARIANTS = {
    "A_current": {},
    "B_protect010": {"protect": 0.1},
    "C_index025": {"index_rate": 0.25},
    "D_noindex": {"index_rate": 0.0},
    "E_noshift": {"f0up_key": 0},
    "F_protect010_index025": {"protect": 0.1, "index_rate": 0.25},
}

sp = Speaker(**cfg)
base = dict(cfg.get("rvc_params", {}))
os.makedirs(OUT, exist_ok=True)
raw_dir = os.path.join(OUT, "0_kokoro_raw")
os.makedirs(raw_dir, exist_ok=True)
raws = []
for i, text in enumerate(SENTENCES, 1):
    path = os.path.join(raw_dir, f"s{i}.wav")
    sp.text2speech(text, path)
    raws.append(path)


def read(path):
    data, rate = sf.read(path)
    return (data if data.ndim == 1 else data.mean(axis=1)), rate


def metrics(path):
    x, rate = read(path)
    snd = parselmouth.Sound(x, rate)
    pitch = snd.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=900)
    f0 = pitch.selected_array["frequency"]
    voiced = f0 > 0
    semis = 12 * np.log2(np.where(voiced, f0, 1) / 100.0)
    jumps = 0
    pairs = 0
    for a, b, va, vb in zip(semis[:-1], semis[1:], voiced[:-1], voiced[1:]):
        if va and vb:
            pairs += 1
            if abs(b - a) > 5:
                jumps += 1
    # tonal whistle in the unvoiced parts: spectral flatness 3-10 kHz in frames without pitch (1 = noise like, low = a tone)
    n, hop = 1024, 512
    flat = []
    window = np.hanning(n)
    for start in range(0, len(x) - n, hop):
        centre = (start + n / 2) / rate
        index = min(int(centre / 0.01), len(voiced) - 1)
        frame = x[start:start + n]
        if voiced[index] or np.sqrt(np.mean(frame ** 2)) < 0.01:
            continue
        spec = np.abs(np.fft.rfft(frame * window)) ** 2
        freqs = np.fft.rfftfreq(n, 1 / rate)
        band = spec[(freqs > 3000) & (freqs < 10000)] + 1e-12
        flat.append(np.exp(np.mean(np.log(band))) / np.mean(band))
    median = float(np.median(f0[voiced])) if voiced.any() else 0
    return jumps, pairs, (float(np.mean(flat)) if flat else float("nan")), median


print(f"{'variant':24} {'pitch jumps >5 st':>18} {'unvoiced flatness (1 = noise)':>30} {'median F0 Hz':>13}")
rows = {}
for name, extra in [("0_kokoro_raw", None)] + list(VARIANTS.items()):
    total_j = total_p = 0
    flats = []
    medians = []
    for i, raw in enumerate(raws, 1):
        if extra is None:
            path = raw
        else:
            folder = os.path.join(OUT, name)
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, f"s{i}.wav")
            sp._rvc.set_params(**dict(base, **extra))
            sp.change_voice(raw, path)
        j, p, flat, med = metrics(path)
        total_j += j
        total_p += p
        flats.append(flat)
        medians.append(med)
    print(f"{name:24} {total_j:>9} of {total_p:<6} {np.nanmean(flats):>30.3f} {np.mean(medians):>13.0f}")
