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
import socket
import socketserver
import time

try:
    from .play_media import play_sound
    from .constants import CFG_FILE, TEXT_COLS, TEXT_KEY, VOICE_KEY, EXPRESSION_FILE
    from .constants import ADDRESS_KEY, PROTOCOL_KEY, WEB_PORT_KEY, SOUND_PORT_KEY, URL_KEY
    from .constants import SPEECH_REQ, SOUND_REQ, TIME_REQ, UPLOAD_ROUTE, U8
    from .mia_logger import logger
    from .utils import split_into_sentences, split_into_lines_and_sentences, chunker 
    from .utils import filter_symbol_sentences, get_websocket_url
except ImportError:
    from play_media import play_sound
    from constants import TEXT_COLS, TEXT_KEY, CFG_FILE, VOICE_KEY, EXPRESSION_FILE
    from constants import ADDRESS_KEY, PROTOCOL_KEY, WEB_PORT_KEY, SOUND_PORT_KEY, URL_KEY
    from constants import SPEECH_REQ, SOUND_REQ, TIME_REQ, UPLOAD_ROUTE, U8
    from mia_logger import logger
    from utils import split_into_sentences, split_into_lines_and_sentences, chunker 
    from utils import filter_symbol_sentences, get_websocket_url


class Speaker:
    """
    Transforms a msg into speech using TTS and voice changers.
    """
    TTS_DEFAULT = "tts_models/en/ljspeech/glow-tts"
    #TTS_DEFAULT = "tts_models/
    MAX_SENTENCES = 4
    def __init__(self,tts_model=TTS_DEFAULT,voice_model=None,tts_device=None,gfx_version=None,voice_sample=None,rvc_opts=None,rvc_params=None,rvc_enabled=True,
                 web_port=8585,address="localhost",protocol="http",**_):
        self._tts_model = tts_model
        self._voice = voice_model
        if rvc_opts is None: rvc_opts = {}
        if rvc_params is None: rvc_params = {}
        self._rvc_enabled = rvc_enabled
        self._rvc_opts = rvc_opts
        self._rvc_params = rvc_params
        if isinstance(web_port,int) and isinstance(address,str) and isinstance(protocol,str):
            self._url = f"{protocol}://{address}:{web_port}/{UPLOAD_ROUTE}"
        else:
            self._url = None
        
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
    
    @staticmethod
    def get_wav_duration(filename):
        """
        Computes the length of play time from
        a wav file. Returns duration in seconds.
        """
        with wave.open(filename, 'r') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            duration = frames / float(rate)
            return duration
    
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
        play_sound(wav_file,url=self._url)
        
    def text2voice(self,msg,output_file=None):
        """
        Generates a voice from text and return the play length
        of the voice file.
        """
        if len(msg) == 0:
            return 0
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
                duration = self.get_wav_duration(fname)
                return duration


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
        if SPEECH_REQ in dic and TIME_REQ in dic:
            out, time = dic[SPEECH_REQ], dic[TIME_REQ]
        else:
            out, time = None, None
        return out, time
    
    
    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls

        self.data = self.rfile.readline().strip()
        print("{} wrote:".format(self.client_address[0]))
        logger.info("{} wrote:".format(self.client_address[0])+ ' ' + "Request recieved: " + self.data.decode()) 
        print(self.data)
        msg, time_stamp = self.process_request(self.data)
        if isinstance(msg,str) and len(msg)>0:
            speaker = self.server.speaker
            duration = speaker.text2voice(msg)
            time.sleep(duration+0.5)
            # Likewise, self.wfile is a file-like object used to write back
            # to the client
            answer = "Msg played!"
            logger.info(answer+f"at {time_stamp}")
            self.wfile.write(json.dumps({SOUND_REQ:answer,TIME_REQ:time_stamp}).encode(U8))
        

class SoundServer(socketserver.TCPServer):
    """
    Derived class to enable adding a Speaker instance.
    """
    @property
    def speaker(self):
        if hasattr(self,"_speaker"):
            return self._speaker
        else:
            raise AttributeError(f"'{type(t).__name__}' object has no attribute speaker! (Set speaker first)")
    @speaker.setter
    def speaker(self,val):
        if not isinstance(val,Speaker):
            raise TypeError("Error: Object is not of type Speaker!")
        self._speaker = val

def start_server(cfg_file):
    with open(cfg_file,'r') as fp: cfg = json.load(fp)
    speaker = Speaker(**cfg)
    ADDRESS = cfg[ADDRESS_KEY]
    PROTOCOL = cfg[PROTOCOL_KEY]
    #web_port = cfg[WEB_PORT_KEY]
    SOUND_PORT = cfg[SOUND_PORT_KEY]
    
    # on localhost we don't add http or https ...
    HOST = get_websocket_url(protocol=PROTOCOL,address=ADDRESS)
    
    # Create the server, binding to localhost on port 9999
    SoundServer.allow_reuse_address=True
    with SoundServer((HOST, SOUND_PORT), SoundHandler) as sound_server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        # enable adres reuse
        sound_server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  
        sound_server.speaker = speaker
        sound_server.serve_forever()
    
                
def tests():
    # test
    with open(CFG_FILE,'r') as fp: cfg = json.load(fp)
    os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"
    # deactivae sever and enable rvc for testing
    cfg["rvc_enabled"] = True
    cfg["address"] = None
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
    duration = s.get_wav_duration("out.wav")
    assert duration > 15


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
parser.add_argument('expression_file',nargs='?',default=EXPRESSION_FILE,
                    help="file for expressions")   # positional argument
#parser.add_argument('-c', '--count')      # option that takes a value
parser.add_argument('-t', '--test',action='store_true',help="execute tests")  # on/off flag
parser.add_argument('-g', '--generate',action='store_true',help="generate expression samples. Needs cfg_file and expressions.json with text entries.")  # on/off flag
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
        generate(args.cfg_file,args.expression_file)
    else:
        cfg_file = args.cfg_file
        start_server(cfg_file)
    
