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
# CPU thread limit ("cpu_threads" in the cfg file): the environment has to be set before numpy and torch are imported
try:
    from .cpu_threads import early_limit_from_argv, parse as parse_cpu_threads, limit_environment, limit_torch, onnx_session_options
    from .config import default_path as default_config
except ImportError:
    from cpu_threads import early_limit_from_argv, parse as parse_cpu_threads, limit_environment, limit_torch, onnx_session_options
    from config import default_path as default_config
early_limit_from_argv(sys.argv, default_cfg=default_config(os.path.split(__file__)[0]))
# torch and rvc_python are imported where they are used (RVC and Coqui, or a GPU check): Kokoro with the voice effect runs without them. pyaudio was imported here but is not used.
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
    from .voice_fix import suppress_tone
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
    from voice_fix import suppress_tone
    from voice_effects import settings_for as effect_settings, apply_effects
    from utils import filter_symbol_sentences, get_websocket_url, get_url

curr_path = os.path.split(__file__)[0]


class _CachedIndex:
    """
    A faiss index together with all its vectors. RVC needs both for every sentence; rvc_python reads
    the index file (several hundred MB) and copies all vectors again on every call.
    """
    def __init__(self,index):
        self._index = index
        self._vectors = index.reconstruct_n(0,index.ntotal)

    def reconstruct_n(self,start,count):
        if start == 0 and count == self._index.ntotal:
            return self._vectors   # only read by RVC, never changed
        return self._index.reconstruct_n(start,count)

    def __getattr__(self,name):
        return getattr(self._index,name)


class _FaissWithCache:
    """faiss for RVC's pipeline: read_index keeps the last index (and its vectors) in memory"""
    def __init__(self,faiss_module):
        self._faiss = faiss_module
        self._cache = {}

    def read_index(self,path,*args):
        key = (os.path.abspath(path),os.path.getmtime(path))
        if key not in self._cache:
            self._cache.clear()   # one voice at a time
            self._cache[key] = _CachedIndex(self._faiss.read_index(path,*args))
        return self._cache[key]

    def __getattr__(self,name):
        return getattr(self._faiss,name)


HUBERT_RATE = 16000   # RVC works at 16 kHz internally
RVC_WINDOW = 160      # one pitch frame


def rvc_padding_samples(seconds,target_rate):
    """(samples at 16 kHz, samples at the voice's rate) for a padding: whole pitch frames, so both cuts stay aligned"""
    frames = max(1,round(seconds*HUBERT_RATE/RVC_WINDOW))
    pad = frames*RVC_WINDOW
    return pad, pad*target_rate//HUBERT_RATE


def set_rvc_padding(rvc,seconds):
    """
    RVC pads every piece of audio with this much on both sides before converting it (default on a CPU: 1 s).
    The voice generator renders the padding too, so for short sentences most of the work is padding.
    """
    pipeline = rvc.vc.pipeline
    pad, pad_target = rvc_padding_samples(seconds,rvc.vc.tgt_sr)
    pipeline.t_pad = pad
    pipeline.t_pad_tgt = pad_target
    pipeline.t_pad2 = pad*2
    logger.info(f"speech: RVC padding {pad/HUBERT_RATE:.2f} s")


def cache_rvc_index():
    """the index of the voice is read once instead of once per sentence"""
    from rvc_python.modules.vc import pipeline as rvc_pipeline
    if not isinstance(rvc_pipeline.faiss,_FaissWithCache):
        rvc_pipeline.faiss = _FaissWithCache(rvc_pipeline.faiss)

def _torch_cuda_available():
    """is there a GPU for the TTS: False when torch is not installed (Kokoro runs on onnxruntime)"""
    try:
        import torch
    except ImportError:
        return False
    return torch.cuda.is_available()


class Speaker:
    """
    Transforms a msg into speech using TTS and voice changers.
    """
    TTS_DEFAULT = "tts_models/en/ljspeech/glow-tts"
    #TTS_DEFAULT = "tts_models/
    COQUI_ENGINE = "coqui"
    KOKORO_ENGINE = "kokoro"
    KOKORO_DEFAULTS = {"model":"voice/models/kokoro/kokoro-v1.0.onnx",
                       "voices":"voice/models/kokoro/voices-v1.0.bin",
                       "voice":"af_heart","speed":1.0,"lang":"en-us"}
    # sentences per spoken chunk: the first chunk is short so speech starts early,
    # the following ones are rendered while the previous chunk is playing
    FIRST_CHUNK_SENTENCES = 1
    CHUNK_SENTENCES = 1
    def __init__(self,tts_model=TTS_DEFAULT,voice_model=None,tts_device=None,gfx_version=None,voice_sample=None,rvc_opts=None,rvc_params=None,rvc_enabled=True,
                 web_port=8585,address="localhost",protocol="http",tts_engine=COQUI_ENGINE,kokoro_opts=None,sentence_pause=0.3,cpu_threads=None,
                 rvc_cache_index=True,tts_warmup=True,rvc_pad=None,rvc_whistle_hz=700.0,voice_effect=None,**_):
        self._tts_engine = tts_engine
        self._kokoro_opts = dict(self.KOKORO_DEFAULTS, **(kokoro_opts or {}))
        # extra wait after each chunk to cover upload and player start in the browser
        self._sentence_pause = sentence_pause
        self._tts_model = tts_model
        self._voice = voice_model
        if rvc_opts is None: rvc_opts = {}
        if rvc_params is None: rvc_params = {}
        self._rvc_enabled = rvc_enabled
        self._rvc_opts = rvc_opts
        self._rvc_params = rvc_params
        if isinstance(web_port,int) and isinstance(address,str) and isinstance(protocol,str):
            #self._url = f"{protocol}://{address}:{web_port}/{UPLOAD_ROUTE}"
            self._url=get_url(protocol=protocol,address=address,web_port=web_port)+f"/{UPLOAD_ROUTE}"
        else:
            self._url = None
        
        if gfx_version is not None:
            os.environ["HSA_OVERRIDE_GFX_VERSION"] = gfx_version

        # at most this many CPU threads for torch (RVC, Coqui) and onnxruntime (Kokoro); None = all cores
        self._cpu_threads = parse_cpu_threads(cpu_threads)
        if self._cpu_threads:
            limit_environment(self._cpu_threads)
            limit_torch(self._cpu_threads)
            logger.info(f"speech: using at most {self._cpu_threads} CPU threads")
        
        if tts_device is None:
            self._device = "cuda" if _torch_cuda_available() else "cpu"
        else:
            self._device = tts_device
        
        self._voice_sample = voice_sample
        self._voice_model = voice_model
        self._rvc_cache_index = rvc_cache_index
        self._rvc_pad = rvc_pad
        # the voice model whistles at a fixed frequency on some vowels: removed after the conversion (0 / null = off), see voice_fix.py
        self._whistle_hz = float(rvc_whistle_hz) if rvc_whistle_hz else None
        # simple voice changer on top of the TTS (and of RVC, if that is on): pitch, formants, robot effects; a typo in the config stops the start
        self._effect = effect_settings(voice_effect)
        if self._effect:
            logger.info(f"speech: voice effect {self._effect}")
        self.init_tts_model(self._tts_model,self._device)
        if self._rvc_enabled is True:
            self.init_rvc_model(self._voice_model,self._device)
        if tts_warmup:
            self.warm_up()

    def warm_up(self):
        """
        Renders a short sentence once: RVC loads its helper models (hubert, rmvpe) and the
        index on first use, so without this the first answer after the start is the slowest.
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

    def init_tts_model(self,tts_model,device):
        # engines are imported lazily so that only the used one has to be installed
        if self._tts_engine == self.KOKORO_ENGINE:
            from kokoro_onnx import Kokoro
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
        elif self._tts_engine == self.COQUI_ENGINE:
            from TTS.api import TTS
            self._tts = TTS(model_name=tts_model).to(device)
        else:
            raise ValueError(f"Unknown tts_engine '{self._tts_engine}'!")
        
    def init_rvc_model(self,model,device):
        import torch
        from rvc_python.infer import RVCInference        # the voice model needs the "voice" extras (requirements-voice.txt)
        # torch >= 2.6 loads only weights by default, but the hubert model
        # used by rvc contains a fairseq Dictionary
        if hasattr(torch.serialization,"add_safe_globals"):
            from fairseq.data.dictionary import Dictionary
            torch.serialization.add_safe_globals([Dictionary])
        self._rvc = RVCInference(device=device) #+":0")

        self._rvc.load_model(model,**self._rvc_opts)
        self._rvc.set_params(**self._rvc_params)
        if self._rvc_cache_index:
            cache_rvc_index()
        if self._rvc_pad is not None:
            set_rvc_padding(self._rvc,self._rvc_pad)
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
        if self._tts_engine == self.KOKORO_ENGINE:
            import soundfile as sf
            opts = self._kokoro_opts
            samples, sample_rate = self._tts.create(msg,voice=opts["voice"],speed=opts["speed"],lang=opts["lang"])
            sf.write(output_file,samples,sample_rate)
        else:
            self._tts.tts_with_vc_to_file(msg, speaker_wav=self._voice_sample, file_path=output_file)
        return True
        
    def change_voice(self,wav_file_in,wav_file_out):
        self._rvc.infer_file(wav_file_in, wav_file_out)
        if self._whistle_hz:
            self.remove_whistle(wav_file_out)

    def apply_effect(self,wav_file):
        """the voice changer (voice_effects.py) on a rendered file, in place"""
        import numpy as np
        import soundfile as sf
        samples, rate = sf.read(wav_file)
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        sf.write(wav_file,np.clip(apply_effects(samples,rate,self._effect),-1.0,1.0),rate,subtype="PCM_16")

    def remove_whistle(self,wav_file):
        """removes the tone that the voice model produces on some sounds (only where it is present), in place"""
        import numpy as np
        import soundfile as sf
        samples, rate = sf.read(wav_file)
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        cleaned = suppress_tone(samples,rate,self._whistle_hz)
        sf.write(wav_file,np.clip(cleaned,-1.0,1.0),rate,subtype="PCM_16")
    
    def play_voice(self,wav_file):
        play_sound(wav_file,url=self._url)
        
    def render_voice(self,msg,output_file):
        """
        Renders msg into output_file (TTS and voice change if enabled).
        Returns the play length in seconds (0 if nothing was rendered).
        """
        if self._rvc_enabled is True:
            with tempfile.NamedTemporaryFile(suffix=".wav") as fpin:
                if not self.text2speech(msg,fpin.name):
                    return 0
                self.change_voice(fpin.name,output_file)
        elif not self.text2speech(msg,output_file):
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
    
