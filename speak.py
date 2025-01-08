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

import os
import torch
from TTS.api import TTS
from rvc_python.infer import RVCInference
import pyaudio  
import wave
import tempfile

try:
    from .play_media import play_sound
except ImportError:
    from play_media import play_sound

class Speaker:
    """
    Transforms a msg into speech using TTS and voice changers.
    """
    TTS_DEFAULT = "tts_models/en/ljspeech/glow-tts"
    #TTS_DEFAULT = "tts_models/
    def __init__(self,tts_model=TTS_DEFAULT,voice_model=None,tts_device=None,gfx_version=None,voice_sample=None,**_):
        self._tts_model = tts_model
        self._voice = voice_model
        if gfx_version is not None:
            os.environ["HSA_OVERRIDE_GFX_VERSION"] = gfx_version
        
        if tts_device is None:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self._device = tts_device
        
        self._voice_sample = voice_sample
        self._voice_model = voice_model
        self.init_tts_model(self._tts_model,self._device)
        self.init_rvc_model(self._voice_model,self._device)
        

    def init_tts_model(self,tts_model,device):
        self._tts = TTS(model_name=tts_model).to(device)
        
    def init_rvc_model(self,model,device):
        self._rvc = RVCInference(device=device+":0")
        self._rvc.load_model(model) #,index_path="/home/maldun/Downloads/MikuAI/added_IVF3010_Flat_nprobe_1_v2.index",version='v2')
        self._rvc.set_params(f0up_key=0, protect=0.3,f0method="crepe")
        
    def text2speech(self,msg,output_file):
        self._tts.tts_with_vc_to_file(msg, speaker_wav=self._voice_sample, file_path=output_file)
        
    def change_voice(self,wav_file_in,wav_file_out):
        self._rvc.infer_file(wav_file_in, wav_file_out)
    
    def play_voice(self,wav_file):
        play_sound(wav_file)
        
    def text2voice(self,msg,output_file=None):
        with tempfile.NamedTemporaryFile(delete=True) as fpin:
            with tempfile.NamedTemporaryFile(delete=True) as fpout:
                if output_file is not None:
                    fname = output_file
                else:
                    fname = fpout.name
                
                self.text2speech(msg,fpin.name)
                self.change_voice(fpin.name,fname)
                self.play_voice(fname)
                #self.play_voice(fpin.name)
                
                # fin = "in.wav"
                # fout="out.wav"
                # self.text2speech(msg,fin)
                # self.change_voice(fin,fout)
                # self.play_voice(fout)

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"

if __name__ == "__main__":
    # test
    import json
    with open("setup_cfg.json",'r') as fp: cfg = json.load(fp)
    os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
    s = Speaker(**cfg)
    testout1 = "../testoutput.wav"
    testout2 = "../testoutputc.wav"
    #msg = "Dies ist ein Test"
    #msg = "L\u00f6we sucht das Licht\nSchatten tanzen auf dem Berg\nGeheimnisvolk schaut"
    msg = "Let's test some sentences, alright? This is a test."
    #s.text2speech(msg,testout1)
    
    #s.change_voice(testout1,testout2)
    #s.play_voice(testout2)
    #s.text2voice(msg)
    
