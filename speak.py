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
import sys
# CPU thread limit ("cpu_threads" in the cfg file): the environment has to be set before numpy and onnxruntime are imported
try:
    from .cpu_threads import early_limit_from_argv, parse as parse_cpu_threads, limit_environment, onnx_session_options
    from .config import default_path as default_config
except ImportError:
    from cpu_threads import early_limit_from_argv, parse as parse_cpu_threads, limit_environment, onnx_session_options
    from config import default_path as default_config
early_limit_from_argv(sys.argv, default_cfg=default_config(os.path.split(__file__)[0]))
import wave
import tempfile
import sys
import socket
import socketserver
import time
import queue
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    from .play_media import play_sound
    from .constants import CFG_FILE, TEXT_COLS, TEXT_KEY, VOICE_KEY, EXPRESSION_FILE
    from .constants import ADDRESS_KEY, PROTOCOL_KEY, WEB_PORT_KEY, SOUND_PORT_KEY, URL_KEY
    from .constants import SPEECH_REQ, SOUND_REQ, TIME_REQ, UPLOAD_ROUTE, U8, STREAM_REQ, STREAM_END_REQ
    from .mia_logger import logger
    from .utils import split_into_sentences, split_into_lines_and_sentences, chunker 
    from .speech_text import speech_text
    from .voice_effects import settings_for as effect_settings, apply_effects
    from .utils import filter_symbol_sentences, get_websocket_url, get_url
except ImportError:
    from play_media import play_sound
    from constants import TEXT_COLS, TEXT_KEY, CFG_FILE, VOICE_KEY, EXPRESSION_FILE
    from constants import ADDRESS_KEY, PROTOCOL_KEY, WEB_PORT_KEY, SOUND_PORT_KEY, URL_KEY
    from constants import SPEECH_REQ, SOUND_REQ, TIME_REQ, UPLOAD_ROUTE, U8, STREAM_REQ, STREAM_END_REQ
    from mia_logger import logger
    from utils import split_into_sentences, split_into_lines_and_sentences, chunker 
    from speech_text import speech_text
    from voice_effects import settings_for as effect_settings, apply_effects
    from utils import filter_symbol_sentences, get_websocket_url, get_url

curr_path = os.path.split(__file__)[0]


class Speaker:
    """
    Transforms a msg into speech: Kokoro (onnxruntime) and, if wanted, the voice effect of voice_effects.py on top of it.
    (RVC voice conversion and Coqui TTS were removed on 2026-10-20: the effect gives the voice, and nothing needs torch any more.)
    """
    KOKORO_ENGINE = "kokoro"
    KOKORO_DEFAULTS = {"model":"voice/models/kokoro/kokoro-v1.0.onnx",
                       "voices":"voice/models/kokoro/voices-v1.0.bin",
                       "voice":"af_heart","speed":1.0,"lang":"en-us"}
    # sentences per spoken chunk: the first chunk is short so speech starts early,
    # the following ones are rendered while the previous chunk is playing
    FIRST_CHUNK_SENTENCES = 1
    CHUNK_SENTENCES = 1
    def __init__(self,tts_engine=KOKORO_ENGINE,kokoro_opts=None,web_port=8585,address="localhost",protocol="http",sentence_pause=0.3,cpu_threads=None,
                 tts_warmup=True,voice_effect=None,rvc_enabled=False,**_):
        # options of a configuration from before the removal (voice_model, rvc_opts, rvc_params, tts_device, tts_model ...) are ignored; the two that would change what is heard are refused
        if tts_engine != self.KOKORO_ENGINE:
            raise ValueError(f"tts_engine '{tts_engine}' is not available: the Coqui TTS engine was removed, only '{self.KOKORO_ENGINE}' is left (set \"tts_engine\": \"kokoro\" in setup_cfg.json)")
        if rvc_enabled:
            raise ValueError("RVC was removed: set \"rvc_enabled\": false in setup_cfg.json (the voice effect, \"voice_effect\", gives the voice)")
        self._tts_engine = tts_engine
        self._kokoro_opts = dict(self.KOKORO_DEFAULTS, **(kokoro_opts or {}))
        # extra wait after each chunk to cover upload and player start in the browser
        self._sentence_pause = sentence_pause
        if isinstance(web_port,int) and isinstance(address,str) and isinstance(protocol,str):
            self._url=get_url(protocol=protocol,address=address,web_port=web_port)+f"/{UPLOAD_ROUTE}"
        else:
            self._url = None

        # at most this many CPU threads for onnxruntime (Kokoro) and numpy; None = all cores
        self._cpu_threads = parse_cpu_threads(cpu_threads)
        if self._cpu_threads:
            limit_environment(self._cpu_threads)
            logger.info(f"speech: using at most {self._cpu_threads} CPU threads")

        # simple voice changer on top of the TTS: pitch, formants, robot effects; a typo in the config stops the start
        self._effect = effect_settings(voice_effect)
        if self._effect:
            logger.info(f"speech: voice effect {self._effect}")
        self.init_tts_model()
        if tts_warmup:
            self.warm_up()

    def warm_up(self):
        """
        Renders a short sentence once: the model loads its helpers on first use,
        so without this the first answer after the start is the slowest.
        """
        started = time.time()
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                self.render_voice("Hello.",os.path.join(tmp_dir,"warmup.wav"))
            logger.info(f"speech: warmed up in {time.time()-started:.1f} s")
        except Exception as exc:
            logger.warning(f"speech: warm-up failed ({exc}), the first sentence will be slower")

    @staticmethod
    def _resolve_path(path):
        """
        Relative paths are taken relative to the MIA directory.
        """
        if os.path.isabs(path) or os.path.exists(path):
            return path
        return os.path.join(curr_path,path)

    def init_tts_model(self):
        from kokoro_onnx import Kokoro      # imported here so that importing this module needs no TTS packages
        model = self._resolve_path(self._kokoro_opts["model"])
        voices = self._resolve_path(self._kokoro_opts["voices"])
        options = onnx_session_options(self._cpu_threads)
        if options is None:
            self._tts = Kokoro(model, voices)
        else:
            # same session as Kokoro makes itself, but with the thread limit
            import onnxruntime as ort
            from kokoro_onnx.session import resolve_providers
            session = ort.InferenceSession(model, sess_options=options, providers=resolve_providers())
            self._tts = Kokoro.from_session(session, voices)

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
    
    def split_into_chunks(self,msg):
        """
        Splits a msg into speakable chunks of sentences. The first chunk
        is kept short, so that speech can start as early as possible.
        """
        sentences = split_into_lines_and_sentences(msg)
        sentences = filter_symbol_sentences(sentences)
        first, rest = sentences[:self.FIRST_CHUNK_SENTENCES], sentences[self.FIRST_CHUNK_SENTENCES:]
        chunks = [first] + list(chunker(rest,self.CHUNK_SENTENCES)) if len(first) > 0 else []
        return list(map(lambda l: '\n'.join(l),chunks))

    def text2speech(self,msg,output_file):
        """
        Converts the whole msg into speech and writes it to output_file.
        Returns True if a file was written.
        """
        # no message no sound
        if len(msg.strip()) == 0:
            return False
        import soundfile as sf
        opts = self._kokoro_opts
        samples, sample_rate = self._tts.create(msg,voice=opts["voice"],speed=opts["speed"],lang=opts["lang"])
        sf.write(output_file,samples,sample_rate)
        return True
        
    def apply_effect(self,wav_file):
        """the voice effect (voice_effects.py) on a rendered file, in place"""
        import numpy as np
        import soundfile as sf
        samples, rate = sf.read(wav_file)
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        sf.write(wav_file,np.clip(apply_effects(samples,rate,self._effect),-1.0,1.0),rate,subtype="PCM_16")

    def play_voice(self,wav_file):
        play_sound(wav_file,url=self._url)
        
    def render_voice(self,msg,output_file):
        """
        Renders msg into output_file (TTS and the voice effect if there is one).
        Returns the play length in seconds (0 if nothing was rendered).
        """
        if not self.text2speech(msg,output_file):
            return 0
        if self._effect:
            self.apply_effect(output_file)
        return self.get_wav_duration(output_file)

    def text2voice(self,msg,output_file=None):
        """
        Generates a voice from text, plays it and returns the play length
        of the last played voice file.
        If output_file is given the whole msg is rendered into this file,
        otherwise the msg is spoken chunk by chunk, where the next chunk is
        rendered while the current one is playing.
        """
        if len(msg) == 0:
            return 0
        if output_file is not None:
            duration = self.render_voice(msg,output_file)
            if duration > 0:
                self.play_voice(output_file)
            return duration

        return self.speak_chunks(self.split_into_chunks(msg))

    def speak_chunks(self,chunks):
        """
        Speaks the text chunks one after another and returns the play length
        of the last played chunk. chunks can be any iterable, which may
        produce its chunks over time (e.g. sentences of an answer which is
        still being generated). Every chunk is rendered as soon as it arrives,
        while the previous one is still playing.
        """
        rendered = queue.Queue()
        finished = object()
        with tempfile.TemporaryDirectory() as tmp_dir, ThreadPoolExecutor(max_workers=1) as renderer:
            def feed():
                try:
                    for nr, chunk in enumerate(chunks):
                        fname = os.path.join(tmp_dir,f"chunk{nr:05d}.wav")
                        rendered.put((renderer.submit(self.render_voice,chunk,fname),fname))
                except Exception as exc:
                    rendered.put(exc)
                rendered.put(finished)
            threading.Thread(target=feed,daemon=True).start()

            duration = 0
            play_end = 0
            item = rendered.get()
            while item is not finished:
                if isinstance(item,Exception):
                    raise item
                future, fname = item
                chunk_duration = future.result()
                if chunk_duration > 0:
                    duration = chunk_duration
                    # wait until the previous chunk is played
                    time.sleep(max(0,play_end - time.time()))
                    self.play_voice(fname)
                    play_end = time.time() + duration + self._sentence_pause
                item = rendered.get()
        # the last chunk is waited for by the caller
        return duration


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
    
    
    def _read_stream(self,first_msg):
        """
        Generator for the sentences of a stream request,
        starting with the one from the first line.
        """
        msg = first_msg
        while True:
            if isinstance(msg,str) and len(msg.strip())>0:
                sentences = filter_symbol_sentences([speech_text(msg)])
                if len(sentences) > 0:
                    yield sentences[0]
            line = self.rfile.readline().strip()
            if len(line) == 0:
                return # connection closed
            dic = json.loads(line)
            if dic.get(STREAM_END_REQ) is True:
                return
            msg = dic.get(SPEECH_REQ)

    def handle(self):
        # self.rfile is a file-like object created by the handler;
        # we can now use e.g. readline() instead of raw recv() calls

        self.data = self.rfile.readline().strip()
        print("{} wrote:".format(self.client_address[0]))
        logger.info("{} wrote:".format(self.client_address[0])+ ' ' + "Request recieved: " + self.data.decode()) 
        print(self.data)
        msg, time_stamp = self.process_request(self.data)
        speaker = self.server.speaker
        if json.loads(self.data).get(STREAM_REQ) is True:
            # sentences follow line by line until the end marker
            duration = speaker.speak_chunks(self._read_stream(msg))
            time.sleep(duration+0.5)
            answer = "Stream played!"
            logger.info(answer+f"at {time_stamp}")
            self.wfile.write(json.dumps({SOUND_REQ:answer,TIME_REQ:time_stamp}).encode(U8))
        elif isinstance(msg,str) and len(speech_text(msg))>0:
            duration = speaker.text2voice(speech_text(msg))
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
    """a manual try of the voice: renders a sentence with the settings of the configuration (no web server) and plays it"""
    with open(default_config(curr_path),'r') as fp: cfg = json.load(fp)
    cfg["address"] = None
    s = Speaker(**cfg)
    msg = "Let's test some sentences, alright? This is a test."
    with tempfile.TemporaryDirectory() as tmp_dir:
        out = os.path.join(tmp_dir,"test.wav")
        duration = s.render_voice(msg,out)
        print(f"rendered {duration:.1f} s of speech")
        assert duration > 1
        s.play_voice(out)


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

if __name__ == "__main__":
    args = parser.parse_args()
    
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
    
