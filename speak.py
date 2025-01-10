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

import argparse
import json
import os
import torch
from TTS.api import TTS
from rvc_python.infer import RVCInference
import pyaudio  
import wave
import tempfile
import sys
import socketserver

try:
    from .play_media import play_sound
    from .constants import CFG_FILE, TEXT_COLS, TEXT_KEY, VOICE_KEY
    from .constants import ADDRESS_KEY, PROTOCOL_KEY, WEB_PORT_KEY, SOUND_PORT_KEY, URL_KEY
    from .constants import SPEECH_REQ, SOUND_REQ
    from .mia_logger import logger
    from .utils import split_into_sentences, split_into_lines_and_sentences, chunker 
    from .utils import filter_symbol_sentences, get_socket_url
except ImportError:
    from play_media import play_sound
    from constants import TEXT_COLS, TEXT_KEY, CFG_FILE, VOICE_KEY
    from constants import ADDRESS_KEY, PROTOCOL_KEY, WEB_PORT_KEY, SOUND_PORT_KEY, URL_KEY
    from constants import SPEECH_REQ, SOUND_REQ
    from mia_logger import logger
    from utils import split_into_sentences, split_into_lines_and_sentences, chunker 
    from utils import filter_symbol_sentences, get_socket_url


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
        if len(msg) == 0:
            return 
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



# Get device
# device = "cuda" if torch.cuda.is_available() else "cpu"

class SoundHandler(socketserver.StreamRequestHandler):
    """
    Socketserver handler for request handling from flask server side
    """
    REQUEST_TYPES = {SPEECH_REQ,SOUND_REQ}
    @staticmethod
    def _cut_request(data, request_type):
        if data.beginswith(request_type):
            return data.removeprefix(request_type).lstrip()
    
    @staticmethod
    def process_request(data):
        dic = json.loads(data)
        return dic
    
    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls
        self.data = self.rfile.readline().strip()
        print("{} wrote:".format(self.client_address[0]))
        logger.info("Request recieved: " + self.data.decode()) 
        print(self.data)
        req = self.process_request(data)
        print(req)
            
        # Likewise, self.wfile is a file-like object used to write back
        # to the client
        self.wfile.write(self.data.upper())

def start_server(cfg_file,exchange_file):
    with open(cfg_file,'r') as fp: cfg = json.load(fp)
    speaker = Speaker(**cfg)
    protocol = cfg[PROTOCOL_KEY]
    address = cfg[ADDRESS_KEY]
    #web_port = cfg[WEB_PORT_KEY]
    sound_port = cfg[SOUND_PORT_KEY]
    host = f'{protocol}://{address}'
    
    # # Create the server, binding to localhost on port 9999
    # with socketserver.TCPServer((host, sound_port), SoundHandler) as sound_server:
    #     # Activate the server; this will keep running until you
    #     # interrupt the program with Ctrl-C
    #     sound_server.serve_forever()
    
    while True:
        if os.path.exists(exchange_file):
            with open(exchange_file,'r') as ef:
                msg = ef.read().strip()
            logger.debug(msg)
            speaker.text2voice(msg)
            os.remove(exchange_file)
                
def tests():
    # test
    with open(CFG_FILE,'r') as fp: cfg = json.load(fp)
    os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
    s = Speaker(**cfg)
    testout1 = "../testoutput.wav"
    testout2 = "../testoutputc.wav"
    msg = "Dies ist ein Test"
    #msg = "L\u00f6we sucht das Licht\nSchatten tanzen auf dem Berg\nGeheimnisvolk schaut"
    msg = "Let's test some sentences, alright? This is a test."
    s.text2speech(msg,testout1)
    
    s.change_voice(testout1,testout2)
    s.play_voice(testout2)
    s.text2voice(msg)


def generate(cfg_file,expression_file,sound_format="wav"):
    curr_dir = os.path.split(__file__)[0]
    with open(cfg_file,'r') as fp: 
        cfg = json.load(fp)
        speaker = Speaker(**cfg)
    with open(expression_file,'r') as fp:
        expressions = json.load(fp)
    for exp, data in expressions.items():
        text = data[TEXT_KEY]
        output_file = os.path.join(curr_dir,"voice","expressions",f"{exp}.{sound_format}")
        speaker.text2voice(text,output_file=output_file)
        expressions[exp][VOICE_KEY] = output_file
    with open(expression_file,'w') as fp:
        json.dump(expressions,fp)

parser = argparse.ArgumentParser(
                  prog='speak',
                  description='Tools for voice generation and TTS',
                  usage="For service: python speak.py cfg_file expression_file, or flags -t/--test for test or -g/--generate for voice sample generation -d/--debug for debugging",
                  
                  epilog='')

parser.add_argument('cfg_file',nargs='?',default=CFG_FILE,help="configuration file")   # positional argument
parser.add_argument('exchange_file',nargs='?',default="exchange.txt",help="file for file based serving")   # positional argument
#parser.add_argument('-c', '--count')      # option that takes a value
parser.add_argument('-t', '--test',action='store_true',help="execute tests")  # on/off flag
parser.add_argument('-g', '--generate',action='store_true',help="generate expression samples. Needs cfg_file and expressions.json with text entries (instead of exchange file).")  # on/off flag
parser.add_argument('-d', '--debug',action='store_true',help="execute file with nothing else for debugging")  # on/off flag

args = parser.parse_args()

if __name__ == "__main__":
    
    if args.debug is True:
        with open(CFG_FILE,'r') as fp: cfg = json.load(fp)
        os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
        s = Speaker(**cfg)   
    elif args.test is True:
        tests()
    elif args.generate is True:
        generate(args.cfg_file,args.exchange_file)
    else:
        cfg_file = args.cfg_file
        exc_file = args.exchange_file
        exc_file=sys.argv[2]
        start_server(cfg_file,exc_file)
    
