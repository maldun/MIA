"""
Looks for the whistle (a pure tone of a fixed frequency) in converted voice files and tells the frequency, e.g. for a new RVC voice model.
Use WAV files made by RVC (python tools/voice_ab.py renders some into its output folder, or the files MIA uploads); the more sentences the better.

  python tools/find_whistle.py /tmp/voice_ab/A_current/*.wav
  python tools/find_whistle.py --check 700 /tmp/voice_ab/A_current/*.wav     how much of the audio the filter at 700 Hz would touch

Then set "rvc_whistle_hz" in setup_cfg.json (0 switches the removal off). The frequency of the MikuAI model is 700 Hz.
"""
import argparse
import os
import sys

import numpy as np
import soundfile as sf

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
import voice_fix  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--check", type=float, default=None, help="frequency (Hz) to test: how many frames are flagged")
    args = parser.parse_args()

    candidates = []
    names = []
    for path in args.files:
        samples, rate = sf.read(path)
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        candidates.append(voice_fix.tone_runs(samples, rate))
        names.append(os.path.basename(path))
        if args.check:
            flagged = voice_fix.find_tone_frames(samples, rate, args.check)
            print(f"{names[-1]:44} flagged at {args.check:.0f} Hz: {int(flagged.sum())} of {len(flagged)} frames ({flagged.mean():.0%})")
    frequency, share = voice_fix.common_tone(candidates)
    if len(candidates) < 3:
        print("\nNeeds at least 3 files (the whistle is the frequency that comes back in different sentences).")
    elif frequency and share >= 0.4:
        print(f"\nwhistle: about {frequency:.0f} Hz, found in {share:.0%} of the {len(candidates)} files; set \"rvc_whistle_hz\": {round(frequency)}")
    else:
        where = f" (the most common frequency, {frequency:.0f} Hz, is in only {share:.0%} of the files)" if frequency else ""
        print(f"\nno whistle found{where}: nothing to remove for this voice (\"rvc_whistle_hz\": 0)")


if __name__ == "__main__":
    main()
