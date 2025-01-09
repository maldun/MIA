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

import json
import os
import torch
from TTS.api import TTS
from rvc_python.infer import RVCInference
import pyaudio  
import wave
import tempfile
import sys

try:
    from .play_media import play_sound
except ImportError:
    from play_media import play_sound

# -*- coding: utf-8 -*-
import re
alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|edu|me)"
digits = "([0-9])"
multiple_dots = r'\.{2,}'

def split_into_sentences(text: str) -> list[str]:
    """
    Split the text into sentences.
    (Source: https://stackoverflow.com/a/31505798)
    
    If the text contains substrings "<prd>" or "<stop>", they would lead 
    to incorrect splitting because they are used as markers for splitting.

    :param text: text to be split into sentences
    :type text: str

    :return: list of sentences
    :rtype: list[str]
    """
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    text = re.sub(multiple_dots, lambda match: "<prd>" * len(match.group(0)) + "<stop>", text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = [s.strip() for s in sentences]
    if sentences and not sentences[-1]: sentences = sentences[:-1]
    return sentences

def split_into_lines_and_sentences(msg: str)->list[str]:
    """
    Converts a msg consisting of lines and breaks those lines into sentences.
    """
    lines = msg.splitlines()
    lines = [line for line in lines if len(line)>0]
    result = []
    for line in lines:
        result += split_into_sentences(line)
    return result

def chunker(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def filter_symbol_sentences(sentences):
    """
    Filters out sentences which consist only of symbols
    """
    regex = alphabets+r'+?'
    comp = re.compile(regex)
    proper_sentences = [s for s in sentences if len(comp.findall(s))>0]
    return proper_sentences

class Speaker:
    """
    Transforms a msg into speech using TTS and voice changers.
    """
    TTS_DEFAULT = "tts_models/en/ljspeech/glow-tts"
    #TTS_DEFAULT = "tts_models/
    MAX_SENTENCES = 4
    def __init__(self,tts_model=TTS_DEFAULT,voice_model=None,tts_device=None,gfx_version=None,voice_sample=None,rvc_opts=None,rvc_params=None,rvc_enabled=True,**_):
        self._tts_model = tts_model
        self._voice = voice_model
        if rvc_opts is None: rvc_opts = {}
        if rvc_params is None: rvc_params = {}
        self._rvc_enabled = rvc_enabled
        self._rvc_opts = rvc_opts
        self._rvc_params = rvc_params
        
        if gfx_version is not None:
            os.environ["HSA_OVERRIDE_GFX_VERSION"] = gfx_version
        
        if tts_device is None:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self._device = tts_device
        
        self._voice_sample = voice_sample
        self._voice_model = voice_model
        self.init_tts_model(self._tts_model,self._device)
        if self._rvc_enabled is True:
            self.init_rvc_model(self._voice_model,self._device)
        

    def init_tts_model(self,tts_model,device):
        self._tts = TTS(model_name=tts_model).to(device)
        
    def init_rvc_model(self,model,device):
        self._rvc = RVCInference(device=device) #+":0")
        
        self._rvc.load_model(model,**self._rvc_opts)
        self._rvc.set_params(**self._rvc_params)
                             #f0up_key=2, protect=0.5,
                             #f0method= "pm")  # (harvest, crepe, rmvpe, pm)
        
    def text2speech(self,msg,output_file):
        # no message no sound
        if len(msg.strip()) == 0:
            return 
        
        sentences = split_into_lines_and_sentences(msg)
        sentences = filter_symbol_sentences(sentences)
        chunks = list(chunker(sentences,self.MAX_SENTENCES))
        chunks = list(map(lambda l: '\n'.join(l),chunks))
        if len(chunks) > 1:
            # play only max sentences for now
            self._tts.tts_with_vc_to_file(chunks[0], speaker_wav=self._voice_sample, file_path=output_file)
        elif len(chunks) == 1:
            self._tts.tts_with_vc_to_file(chunks[0], speaker_wav=self._voice_sample, file_path=output_file)
        # else nothing
        
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
                if self._rvc_enabled is True:
                    self.text2speech(msg,fpin.name)
                    self.change_voice(fpin.name,fname)
                    self.play_voice(fname)
                else:
                    self.text2speech(msg,fname)
                    self.play_voice(fname)

def watchdog(cfg_file,exchange_file):
    with open(cfg_file,'r') as fp: cfg = json.load(fp)
    speaker = Speaker(**cfg)
    while True:
        if os.path.exists(exchange_file):
            with open(exchange_file,'r') as ef:
                msg = ef.read().strip()
            speaker.text2voice(msg)
            os.remove(exchange_file)
                
                
            

# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"

def tests():
    # test
    # with open("setup_cfg.json",'r') as fp: cfg = json.load(fp)
    # os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
    # s = Speaker(**cfg)
    testout1 = "../testoutput.wav"
    testout2 = "../testoutputc.wav"
    #msg = "Dies ist ein Test"
    #msg = "L\u00f6we sucht das Licht\nSchatten tanzen auf dem Berg\nGeheimnisvolk schaut"
    msg = "Let's test some sentences, alright? This is a test."
    #s.text2speech(msg,testout1)
    
    #s.change_voice(testout1,testout2)
    #s.play_voice(testout2)
    #s.text2voice(msg)
    msg2 = """
     /_/\ 
     ( ^ - ^ ) 
     >___<

     The kitty's snoozing!
    """
    expected = ["The kitty's snoozing!"]
    result = filter_symbol_sentences(split_into_lines_and_sentences(msg2))
    assert expected==result

TEST_KEYWORD = "test"

if __name__ == "__main__":
    
    # very primitive .. build a server later
    cfg_file=sys.argv[1]
    if cfg_file.lower()==TEST_KEYWORD:
        tests()
    else:
        exc_file=sys.argv[2]
        watchdog(cfg_file,exc_file)
    
