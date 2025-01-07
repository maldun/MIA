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

class Speaker:
    """
    Transforms a msg into speech using TTS and voice changers.
    """
    TTS_DEFAULT = "tts_models/de/thorsten/tacotron2-DDC"
    def __init__(self,tts_model=TTS_DEFAULT,voice_model=None,tts_device=None,gfx_version=None,voice_sample=None,voice_model=None,**_):
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
        rvc = RVCInference(device=device)
        rvc.load_model(model)
        
    def text2speech(self,msg,output_file):
        self._tts.tts_with_vc_to_file(msg, speaker_wav=self._voice_sample, file_path=output_file)
        
    def change_voice(self,wav_file_in,wav_file_out):
        rvc.infer_file(wav_file_in, wav_file_out)
    
    def play_voice(self,wav_file):
        pass

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"

if __name__ == "__main__":
    # test
    import json
    with open("setup_cfg.json",'r') as fp: cfg = json.load(fp)
    os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
    s = Speaker(**cfg)
    s.text2speech("Dies ist ein Test","../testoutput.wav")
    
