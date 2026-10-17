#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIA - MIA Is not an Assistant
#Copyright (C) 2024  Stefan Reiterer

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
Renders the same test text with different Kokoro voices and RVC pitch shifts,
to compare them by ear. Also reports the render speed (real time factor).
"""
import argparse
import json
import os
import time

try:
    from .constants import CFG_FILE
    from .speak import Speaker
except ImportError:
    from constants import CFG_FILE
    from speak import Speaker

curr_path = os.path.split(__file__)[0]
TEST_TEXT = "Hi, I'm MIA! I just woke up and I'm ready to help. Shall we look at your tasks for today?"
VOICES = ["af_heart","af_bella","af_sky","af_nicole","jf_alpha"]
PITCHES = [0,3,6]

parser = argparse.ArgumentParser(prog='voice_lab',
                                 description='Renders voice samples for comparing TTS voices and RVC pitch shifts')
parser.add_argument('cfg_file',nargs='?',default=CFG_FILE,help="configuration file")
parser.add_argument('-o','--out_dir',default=os.path.join(curr_path,"voice","samples","lab"),help="output directory")
parser.add_argument('-v','--voices',nargs='+',default=VOICES,help="kokoro voices")
parser.add_argument('-p','--pitches',nargs='+',type=int,default=PITCHES,help="RVC pitch shifts (semitones)")
parser.add_argument('-f','--f0method',default="rmvpe",help="RVC pitch method (pm, harvest, crepe, rmvpe)")
parser.add_argument('-t','--text',default=TEST_TEXT,help="text to speak")

def timed(func,*args):
    start = time.time()
    result = func(*args)
    return result, time.time() - start

def main(args):
    with open(args.cfg_file,'r') as fp:
        cfg = json.load(fp)
    # no web server needed and always use kokoro and rvc
    cfg.update(address=None,tts_engine=Speaker.KOKORO_ENGINE,rvc_enabled=True)
    speaker = Speaker(**cfg)
    os.makedirs(args.out_dir,exist_ok=True)

    for voice in args.voices:
        speaker._kokoro_opts["voice"] = voice
        tts_file = os.path.join(args.out_dir,f"{voice}_tts.wav")
        _, tts_time = timed(speaker.text2speech,args.text,tts_file)
        duration = speaker.get_wav_duration(tts_file)
        print(f"{voice}: {duration:.1f}s audio, TTS {tts_time:.2f}s (RTF {tts_time/duration:.2f})")
        for pitch in args.pitches:
            speaker._rvc.set_params(f0method=args.f0method,f0up_key=pitch)
            rvc_file = os.path.join(args.out_dir,f"{voice}_rvc{pitch:+d}.wav")
            _, rvc_time = timed(speaker.change_voice,tts_file,rvc_file)
            print(f"  pitch {pitch:+d}: RVC {rvc_time:.2f}s (RTF {rvc_time/duration:.2f}) -> {rvc_file}")

if __name__ == "__main__":
    main(parser.parse_args())
