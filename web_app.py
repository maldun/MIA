#MIA - MIA Is not an Assistant
#Copyright (C) 2017  Stefan Reiterer

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

from flask import Flask, render_template, request, send_file, g, jsonify, send_from_directory
from flask import current_app
import datetime
import json
import mimetypes
from flask_socketio import SocketIO, emit
import logging
import os
import time
import types
import threading
import multiprocessing as mp
import random
import re
import shutil
import signal
import socket
import sys
import requests
from flask_apscheduler import APScheduler

# constants and paths
from .constants import CFG_FILE, LOG_FNAME, TIME_FORMAT, MESSAGE_SIZE
from .constants import ADDRESS_KEY, PROTOCOL_KEY, WEB_PORT_KEY, SOUND_PORT_KEY, URL_KEY, U8
from .constants import AUDIO_ROUTE, UPLOAD_ROUTE, AUDIO_MIME_TYPE, SPEECH_REQ, SOUND_REQ, TIME_REQ
from . import constants as CONST
from .speech_stream import SpeechStreamer
from .shutdown import request_shutdown
from .presets_api import init_presets_api
from .chat_log import ChatLog
from .chat_service import ChatService, behaviours_from_file, settled
from .chat_api import create_blueprint as create_chat_blueprint
from . import accounts_api
from .chat_ops_api import create_chat_ops_blueprint
from .items_api import create_items_blueprint
from .trust_persona_api import create_trust_persona_blueprint
from .persona import read_persona
from .internal_auth import ensure_token, internal_headers
from .storage import Storage
from .storage_files import FileBackend
from .moods import MoodTracker
from .memory_records import MemoryRecords, memory_hooks
from .speech_text import speech_text
from . import research_chat
from . import searxng_control
from .audio_router import AudioRouter
from . import behaviour
from . import events as events_module
from .content_store import ContentStore
from . import source_trust
from . import broker as broker_module
from . import checks
from . import sandbox as sandbox_module
from .core import Core
from .library import Library
from .pipeline import Tool
from .pipeline_model import OllamaModel
from . import web_tools
from .web_tools import build_web_tools
from .extension_loader import load_extensions
from .file_store import FileStore
from .files_api import create_files_blueprint
from .model_class import ModelClasses
from .model_gate import make_model_command, make_prepare
from .task_registry import TaskRegistry
from .workflow_voice import speaker_for
from .workflow_library import WorkflowLibrary
from .scholar import build_scholar
from . import tailscale_serve
FPATH = os.path.split(__file__)[0]
cfg_file = os.path.join(FPATH,CFG_FILE)
if os.path.basename(cfg_file) == "setup_cfg.json":
    from .config import ensure as _ensure_config
    cfg_file, _ = _ensure_config(FPATH)         # the first start on a new machine: setup_cfg.json is made from setup_cfg.example.json
TEMPLATE_DIR = "templates"
STATIC_DIR = os.path.join(TEMPLATE_DIR,"static")
STATIC_FOLDER = os.path.join(FPATH,STATIC_DIR)

UPLOAD_DIR = os.path.join(TEMPLATE_DIR,UPLOAD_ROUTE)
UPLOAD_FOLDER = os.path.join(FPATH,UPLOAD_DIR)

AUDIO_DIR = os.path.join(TEMPLATE_DIR,AUDIO_ROUTE)
AUDIO_FOLDER= os.path.join(FPATH,AUDIO_DIR)

with open(cfg_file,'r') as jp:
    cfg = json.load(jp)
TIMEOUT_OPT = "timeout"

from .utils import MyMarkdown, get_url, get_websocket_url, get_timestamp
from . import utils
md = MyMarkdown(output_format='html')

WEB_PORT = int(cfg[WEB_PORT_KEY])
SOUND_PORT = int(cfg[SOUND_PORT_KEY])
TIMEOUT = int(cfg[TIMEOUT_OPT])
PROTOCOL = cfg[PROTOCOL_KEY]
ADDRESS = cfg[ADDRESS_KEY]

WEB_URL = get_url(web=True,**cfg)

from .expressor import PresetExpressor, VoiceExpressor
from .play_media import play_sound
from .voice_lines import VoiceLines, mood_names
voc_exp = VoiceExpressor(web_url=WEB_URL+'/'+UPLOAD_ROUTE)

from .communicator import Communicator
comm = Communicator(**cfg)
_persona_file = os.path.join(FPATH, cfg.get(CONST.PERSONA_FILE_KEY, "data/persona.json"))
comm.persona_provider = lambda: read_persona(_persona_file)          # the persona saved on the page is the system message of every call (REQ-CHA-008)

app = Flask(__name__, static_folder=STATIC_FOLDER)
# add scheduler
TIME_UPDATE_INTERVAL = cfg[CONST.TIME_INTERVAL_KEY]
# initialize scheduler
scheduler = APScheduler()
# set configuration values
scheduler.api_enabled = True
# start scheduler
scheduler.init_app(app)
scheduler.start()

# upload folder
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
lock = threading.Lock()
app.config['MAX_CONTENT_LENGTH'] = 100*1024**2  # 100 MB

ALLOWED_ORIGIN_FILE=os.path.join(app.root_path,CONST.ALLOWED_ORIGIN_FILE)
def build_allowed_origins(web_url, address, web_port, https_port=None, own_ip=None, extra_hosts=()):
    """
    Origins (pages) that may connect to the socket: the page served by this app, reached via localhost, the
    configured address, our own address, plain or behind the HTTPS proxy.
    """
    hosts = ["localhost", "127.0.0.1", address, own_ip] + [h for h in extra_hosts if h]
    origins_extra = []
    for host in extra_hosts:      # tailnet name, reverse proxy: through `tailscale serve` the page comes from https://<name>
        origins_extra += tailscale_serve.origins_for(host)
    ports = {"http": web_port}
    if https_port:
        ports["https"] = https_port
    origins = [web_url]
    for scheme, port in ports.items():
        for host in hosts:
            if host:
                origin = f"{scheme}://{host}:{port}"
                if origin not in origins:
                    origins.append(origin)
    return origins + [o for o in origins_extra if o not in origins]

try:
    _OWN_IP = utils.get_own_ip()
except Exception:  # no network: localhost only
    _OWN_IP = None
def _remote_hosts():
    """the name of this machine in the tailnet (if Tailscale runs) and the configured "public_hosts" """
    hosts = list(cfg.get(CONST.PUBLIC_HOSTS_KEY, []))
    hosts += [h.strip() for h in os.environ.get("MIA_PUBLIC_HOSTS", "").split(",") if h.strip()]          # compose: the addresses the stack is reached by
    info = tailscale_serve.node_info() if tailscale_serve.find_binary() else None
    if info:
        hosts.append(info["name"])
    return hosts

# port of an HTTPS front that MIA does not start itself (compose: Caddy), as the browser sees it
_PUBLIC_HTTPS_PORT = os.environ.get("MIA_PUBLIC_HTTPS_PORT") or cfg.get("public_https_port")
allowed_origins = build_allowed_origins(WEB_URL, ADDRESS, WEB_PORT, cfg.get(CONST.HTTPS_PORT_KEY) or _PUBLIC_HTTPS_PORT, _OWN_IP, extra_hosts=_remote_hosts())
if os.environ.get("MIA_PUBLIC_PORT"):          # compose: the port the stack publishes MIA on (MIA_PORT), if not the one inside
    allowed_origins += [o for o in build_allowed_origins(WEB_URL, ADDRESS, int(os.environ["MIA_PUBLIC_PORT"]), None, _OWN_IP, extra_hosts=_remote_hosts()) if o not in allowed_origins]
if os.path.exists(ALLOWED_ORIGIN_FILE):
    with open(ALLOWED_ORIGIN_FILE,'r') as aof:
        allowed_origins += aof.read().splitlines()

socketio = SocketIO(app,cors_allowed_origins=allowed_origins)

# expression presets of the character (REST API, files in "presets_dir"); the editor of the character uses it
def expression_llm(messages, schema):
    """the language model for expressions from a description: MIA's Ollama server, answers must follow the JSON schema"""
    reply = comm.client.chat(model=cfg.get(CONST.EXPRESSION_MODEL_KEY) or comm.version, messages=messages, format=schema, stream=False,
                             options={**(comm.llm_options or {}), "temperature": cfg.get(CONST.EXPRESSION_TEMPERATURE_KEY, CONST.DEFAULT_EXPRESSION_TEMPERATURE)},      # same options as the chat: no model reload
                             think=False, keep_alive=comm.keep_alive)
    return reply["message"]["content"]

preset_store = init_presets_api(app,cfg,FPATH,allowed_origins=lambda: allowed_origins,llm=expression_llm,
                                model_name=lambda: cfg.get(CONST.EXPRESSION_MODEL_KEY) or comm.version)

#g.socket_url = f"ws://127.0.0.1:{port}/"

# the 3D character (Godot web export, see ui/) is shown in the page; expressions are sent to it as events
mimetypes.add_type("application/wasm", ".wasm")
CHARACTER_FOLDER = cfg.get(CONST.CHARACTER_DIR_KEY, CONST.DEFAULT_CHARACTER_DIR)
if not os.path.isabs(CHARACTER_FOLDER):
    CHARACTER_FOLDER = os.path.join(FPATH, CHARACTER_FOLDER)
BACKGROUND_FOLDER = cfg.get(CONST.BACKGROUND_DIR_KEY, CONST.DEFAULT_BACKGROUND_DIR)
if not os.path.isabs(BACKGROUND_FOLDER):
    BACKGROUND_FOLDER = os.path.join(FPATH, BACKGROUND_FOLDER)

from .mia_logger import logger

logger.debug('Start Logging')
print("start")


def send_expression(preset):
    """
    Tells all connected pages to let the character play the expression preset.
    (socketio.emit like everywhere else, emit alone is fragile outside the flask context)
    """
    socketio.emit(CONST.EXPRESSION_EVENT, {"name": preset})

pre_exp = PresetExpressor(send=send_expression)
IDLE_EXPRESSION = "idle"

def express_and_reload(expression,sound=True,line=None):
    """
    Lets the character make the expression (and plays its voice clip, or the line of the mood when there is one).
    """
    pre_exp.express(expression)
    if sound is True:
        if line:
            play_sound(line,url=WEB_URL+'/'+UPLOAD_ROUTE)
        else:
            voc_exp.express(expression)

# Create a function to handle messages from clients
@socketio.on('chat_send')
def handle_chat_send(data=None):
    """{id (client id), text}: acknowledged right away, the answer follows as chat_* events"""
    data = data if isinstance(data, dict) else {"text": data}
    account = _account_sockets.account_of(request.sid) if _account_sockets is not None else None
    if account:
        _account_changes.record(account, "chat_send", "")                    # who wrote (REQ-API-009); the text is not recorded
    return chat_service.send(data.get("text"), client_id=data.get("id"), sender=account or request.sid, author=account)       # the rate limit is per user (REQ-API-007), the message keeps its author

@socketio.on('chat_stop')
def handle_chat_stop(_=None):
    return {"stopped": chat_service.stop()}

@socketio.on('connect')
def handle_connect(_auth=None):
    """a page connected: it learns the state (busy, model, mood) right away"""
    if _account_sockets is not None:
        accounts_api.guard_connect(_account_sockets)                  # no session, no socket (IF-101)
    audio_router.connect(request.sid)
    emit('chat_status', chat_service.status())

def penalize(penalty):
    """
    Sometimes an LLM hickups ... we send a 
    "penalty" to correct the behavior and have
    a little fun with it ...
    """
    if isinstance(penalty,str):
        logger.info("Penalty!: " + str(penalty))
        time.sleep(TIMEOUT/2)
        process_message(penalty)
    elif penalty is None:
        return
 
def send_voice_request(msg):
    """
    Sends meesage asking for text2speech conversion.
    Sends Timestamp for control.
    """
    # nothing to do (the voice does not read markdown marks or *actions*)
    msg = speech_text(msg)
    if len(msg) == 0:
        return
    HOST = get_websocket_url(address=ADDRESS,protocol=PROTOCOL)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Connect to server and send data
        sock.connect((HOST, SOUND_PORT))
        timestamp = get_timestamp()
        request = {SPEECH_REQ:msg,TIME_REQ:timestamp}
        request = json.dumps(request) + '\n'
        sock.sendall(bytes(request, U8))
        # Receive data from the server and shut down
        received = str(sock.recv(MESSAGE_SIZE), U8)
        received = json.loads(received)
        if SOUND_REQ in received and TIME_REQ in received:
            if received[TIME_REQ] == timestamp:
                logger.info("Speech played!")
            else:
                logger.info("Something went wrong on Sound Server Side!")

def switch_model(profile):
    """
    Switches the model profile and reports the result in the UI.
    """
    if comm.set_profile(profile):
        msg = f"Switched to {profile} model ({comm.version})."
    else:
        msg = f"No {profile} model configured!"
    logger.info(msg)
    return msg

def handle_special_commands(message):
    """
    Some special commands to make usage easier!
    Returns True if the message was a command which is completely
    handled, so that it must not be sent to the model.
    """
    cmd=message.strip().lower()
    match cmd:
        case CONST.LIGHT_COMMAND:
            switch_model(comm.LIGHT_PROFILE)
            return True
        case CONST.FULL_COMMAND:
            switch_model(comm.FULL_PROFILE)
            return True
        case CONST.SHUTDOWN_COMMAND:
            quit_msg="Have a break MIA"
            logger.info(quit_msg)
            # same orderly path as Ctrl+C (only this process is signalled, not the whole process group)
            request_shutdown()
            return True
        case CONST.DREAM_COMMAND:
            dream_msg="sweet Dreams MIA"
            logger.info(dream_msg)
            comm.emulate_dreaming()
            return True
        case CONST.SLEEP_COMMAND:
            quit_msg="Goodnight MIA"
            logger.info(quit_msg)
            comm.emulate_dreaming()
            request_shutdown()
            return True
        case CONST.UPDATE_COMMAND:
            time_update()
            return True
    return False
            
            

def process_message(message):
    # special commands go here
    if handle_special_commands(message):
        return "Command processed successfully"
    converse(message)
    return "Message processed successfully"

def converse(message,on_delta=None,on_emotion=None,should_stop=None):
    """
    The exchange with MIA: the model answers (streamed), the character reacts, the speech streams along.
    on_delta(text) gets the filtered text so far, on_emotion(keyword) every emotion keyword, should_stop() ends the answer
    early (the text received so far stays). Returns the filtered answer.
    """
    time.sleep(1)
    
    # MIA starts to speak while the answer is still generated
    streamer = SpeechStreamer(get_websocket_url(address=ADDRESS,protocol=PROTOCOL),SOUND_PORT,
                              repair=lambda text: behaviour.apply_rules(text)["text"],settle=settled)      # the voice speaks the repaired text the page shows (REQ-CHA-014)
    reactions, played = [], []
    def react(emotion):
        # only the first expression plays its sound, otherwise it would cut off the speech
        expression = comm.map_emotion(emotion)
        if chat_service.show_behaviour(expression):          # a gesture with many net minus votes is shown rarely (REQ-CHA-017); the mood still goes to the page
            express_and_reload(expression,sound=len(played)==0,line=voice_lines.pick(emotion) if len(played)==0 else None)
            played.append(expression)
        reactions.append(emotion)
        if on_emotion is not None:
            on_emotion(emotion)
    def update(text):
        streamer.update(text)
        if on_delta is not None:
            on_delta(text)
    try:
        answer, filt_answer, penalty = comm.exchange(message,
                                            emotion_reaction=react,
                                            update_message=update,
                                            filter_message=True,
                                            map_emotions_to_reactions=False,
                                            should_stop=should_stop)
    except Exception:
        streamer.abort()
        express_and_reload("idle",sound=False)      # no answer: the character does not stay in the pose of the last reaction
        raise

    if should_stop is not None and should_stop():
        streamer.abort()
        express_and_reload("idle",sound=False)
        return filt_answer

    streamer.finish(filt_answer)
    streamer.wait()
    if len(filt_answer) == 0:
        # if no speech wait a bit
        time.sleep(TIMEOUT)
    
    penalize(penalty)
    time.sleep(2)
    express_and_reload("idle",sound=True)
    return filt_answer




# interval time update
# direct scheduling is for losers ...
# so we make a (cron) job which sends a request back to us.
@scheduler.task('cron', id='time_update', hour="0-23",#seconds=TIME_UPDATE_INTERVAL,
                misfire_grace_time=TIME_UPDATE_INTERVAL//10)
def time_update_trigger():
    #print("Trigggggger!!!!!!")
    url=WEB_URL + '/' + CONST.TIME_ROUTE
    req={CONST.TASK_KEY:CONST.UPDATE_TIME_TASK}
    response = requests.get(url, params=req, headers=internal_headers())
    logger.info(response.text)

@app.route(f"/{CONST.TIME_ROUTE}", methods=["GET"])    
def time_update_request():
    if CONST.TASK_KEY not in request.values:
        return "No data sent", 400
    tasks = request.values.getlist(CONST.TASK_KEY)
    if CONST.UPDATE_TIME_TASK in tasks:
        return time_update() 

def time_update():
    try:
        chat_service.recite_due()          # tasks that have fallen due are read from their records, word for word, by code (REQ-CHA-019)
    except Exception:
        logger.exception("reciting the due tasks failed")
    answer, filt_answer, penalty = comm.time_update(
                                        emotion_expression=express_and_reload,
                                        _test_neutral=False,
                                        _test_neutral_but_penalty=False
                                        )
     
    if answer is None:
        pass
    else:
        maybe_call_attention()
        send_voice_request(filt_answer)
        emotions, _ = comm.extract_emotion(answer)
        chat_service.post_assistant(filt_answer, emotion=emotions[0] if emotions else None, auto=True)
        time.sleep(TIMEOUT-1)
        express_and_reload("idle",sound=True)
    if penalty is not None:
        process_message(penalty)
        log_msg = "Time update processed, but penalty"
    else:
        log_msg = "Time update processed successfully"
    logger.info(log_msg)
    return log_msg
    



AUDIO_KEEP = 12      # the latest lines stay on disk (every line has its own file, nothing is shared between pages)
audio_router = AudioRouter(lambda event, payload, to=None: socketio.emit(event, payload, to=to) if to else socketio.emit(event, payload))

def line_serials(folder):
    """the serial numbers of the line-<serial>.wav files in folder"""
    found = []
    for f in os.listdir(folder):
        match = re.fullmatch(r"line-(\d+)\.wav", f)
        if match:
            found.append(int(match.group(1)))
    return found

def publish_audio(source_path, message, move=False):
    """moves (an upload) or copies (the intro sound) a rendered line to its own file and tells the page that plays the voice; returns the serial number"""
    os.makedirs(AUDIO_FOLDER, exist_ok=True)
    # continue after the lines of an earlier run: the cleanup below keeps the highest names, a new line-000001 would be removed at once
    serial = audio_router.next_serial(after=max(line_serials(AUDIO_FOLDER), default=0))
    name = f"line-{serial:06d}.wav"
    target = os.path.join(AUDIO_FOLDER, name)
    if move:
        shutil.move(source_path, target)
    else:
        shutil.copy2(source_path, target)
    old_files = sorted(f for f in os.listdir(AUDIO_FOLDER) if f.startswith("line-") and f.endswith(".wav"))
    for old in old_files[:-AUDIO_KEEP]:
        try:
            os.remove(os.path.join(AUDIO_FOLDER, old))
        except OSError:
            pass
    audio_router.announce(f"/{AUDIO_ROUTE}/{name}", serial, message)
    return serial

def find_sound(path):
    """the file of a configured sound (as given, or relative to the program folder); None when it is missing"""
    for candidate in (path, os.path.join(app.root_path, path)):
        if os.path.isfile(candidate):
            return candidate
    return None

def pick_sound(sounds):
    """a random one of the configured sounds that exist"""
    found = [f for f in (find_sound(s) for s in sounds) if f]
    return random.choice(found) if found else None

def play_intro_sound():
    # the intro sound is played by the page that loaded (it claims the voice and asks for it);
    # "intro_sounds" is a list of clips (one is picked at random), "intro_sound" the single fallback
    sounds = list(cfg.get("intro_sounds") or []) or [cfg["intro_sound"]]
    chosen = pick_sound(sounds) or pick_sound([cfg["intro_sound"]])
    if chosen:
        publish_audio(chosen, "intro")
        log_msg = "Intro Audio loaded sucessfully: " + os.path.basename(chosen)
    else:
        log_msg = "No Intro Audio found!"
    logger.info(log_msg)
    return log_msg

def maybe_call_attention():
    """sometimes MIA calls out before she starts talking on her own ("Hey, listen!"); the chance is "attention_chance" (0 = never)"""
    sounds = cfg.get("attention_sounds") or []
    if not sounds or random.random() >= float(cfg.get("attention_chance", 0.0)):
        return False
    chosen = pick_sound(sounds)
    if chosen:
        publish_audio(chosen, "attention")
    return bool(chosen)

#address=ADDRESS,port=WEB_PORT
# --- the chat: log, mood, background processing (chat_service.py) -----------------------------------------------
def run_chat_command(command):
    """runs a slash command; returns the text of the system note"""
    if command == CONST.LIGHT_COMMAND:
        return switch_model(comm.LIGHT_PROFILE)
    if command == CONST.FULL_COMMAND:
        return switch_model(comm.FULL_PROFILE)
    handle_special_commands(command)
    return {CONST.DREAM_COMMAND: "MIA has sorted her memories.",
            CONST.UPDATE_COMMAND: "The time was sent to MIA.",
            CONST.SLEEP_COMMAND: "Goodnight! MIA is shutting down ...",
            CONST.SHUTDOWN_COMMAND: "MIA is shutting down ..."}.get(command)

def _own_path(key, default):
    path = cfg.get(key, default)
    return path if os.path.isabs(path) else os.path.join(FPATH, path)

chat_log = ChatLog(_own_path(CONST.CHAT_LOG_KEY, CONST.DEFAULT_CHAT_LOG),
                   max_messages=cfg.get(CONST.CHAT_LOG_MAX_KEY, 10000))
mood = MoodTracker(_own_path(CONST.MOODS_FILE_KEY, CONST.DEFAULT_MOODS_FILE),
                   hold_minutes=cfg.get(CONST.MOOD_HOLD_KEY, 10))
voice_lines = VoiceLines(os.path.join(FPATH, "library", "voice_lines.json"), VoiceExpressor.DEFAULT_PATH, mood_names(os.path.join(FPATH, CONST.DEFAULT_MOODS_FILE)),
                         log=logger.warning)                  # the line a mood says (REQ-CHA-007)
# the tasks of MIA as skills with pipelines (ui/REQUIREMENTS_CORE.md); the chat is the first one
pipeline_model = OllamaModel(comm.client, lambda profile: getattr(comm, "_profiles", {}).get(profile),
                             lambda: (comm.version, comm.llm_options), keep_alive=comm.keep_alive)
_runs_dir = _own_path(CONST.RUNS_DIR_KEY, CONST.DEFAULT_RUNS_DIR)
# prompts, answers and the pages that were read are kept in full, by hash (content_store.py); conversations only with "store_chat_texts"; old texts go after "store_days"
content_store = ContentStore(_own_path("store_dir", "data/store"))
content_store.prune(cfg.get("store_days", 90))
_source_trust = source_trust.build_trust(cfg)
_web_tools, _web_search, _web_client = build_web_tools(cfg, _runs_dir, store=content_store, trust=_source_trust.for_url)          # search (SearXNG, DuckDuckGo as fallback) and page fetcher with the safety rules
_scholar, _scholar_http = build_scholar(cfg, _runs_dir)          # OpenAlex, Crossref, PubMed, arXiv: creating them touches no network
try:        # is SearXNG running? if not, say why searches use the fallback (and start the container if the user wants it: "searxng_autostart")
    _searx = searxng_control.ensure_searxng(cfg)
    (logger.info if _searx["reachable"] or not _searx["wanted"] else logger.warning)("web search: %s", _searx["message"])
except Exception as _exc:
    logger.warning("web search: SearXNG could not be checked (%s)", _exc)
library = Library(_own_path(CONST.LIBRARY_DIR_KEY, CONST.DEFAULT_LIBRARY_DIR), _own_path(CONST.USER_LIBRARY_DIR_KEY, CONST.DEFAULT_USER_LIBRARY_DIR),
                  _own_path(CONST.LIBRARY_INDEX_KEY, CONST.DEFAULT_LIBRARY_INDEX))
for _path, _problem in library.errors.items():
    logger.warning("library entry %s: %s", _path, _problem)
# the sandbox for scripts (bubblewrap for ordinary calculations, podman for exposed ones; probed when first needed) and the broker that gives a script web access through the same safety rules
sandbox_router = sandbox_module.create_router(cfg)
_environment_cache = {"at": 0.0, "value": None}


def _run_environment():
    """written into the run_start event of every run (13d): code version, hash of the configuration (secrets removed), the models with their digests; looked up at most once a minute"""
    if _environment_cache["value"] is None or time.monotonic() - _environment_cache["at"] > 60:
        names = [n for n in (cfg.get("version"), cfg.get("version_light")) if n]
        _environment_cache.update(at=time.monotonic(), value=events_module.environment(cfg, root=FPATH, models=events_module.model_digests(comm.client, names)))
    return _environment_cache["value"]


core = Core(_own_path(CONST.SKILLS_DIR_KEY, CONST.DEFAULT_SKILLS_DIR), library, _runs_dir, model=pipeline_model, sandbox=sandbox_router, environment=_run_environment,
            store=content_store, store_texts=(lambda name: True) if cfg.get("store_chat_texts") else None,
            broker_factory=lambda: broker_module.WebBroker(broker_module.web_handlers(_web_search, _web_client)),
            tools={name: Tool(*pair) for name, pair in _web_tools.items()},
            functions={"chunk_text": web_tools.chunk_text, "untrusted": web_tools.untrusted, "injection_signals": web_tools.injection_signals,
                       **checks.build_web_checks(_web_tools["web_search"][0], _web_tools["fetch_page"][0])})
for _name, _problems in core.check(functions={"converse": None}).items():
    logger.warning("skill %s: %s", _name, "; ".join(_problems))

def run_chat_exchange(text, on_delta, on_emotion, should_stop):
    """the answer of the chat skill: the pipeline runs `converse` (the exchange with MIA) and reports its steps to the page"""
    result = core.run("chat", {"text": text}, on_event=lambda event: chat_service.pipeline_event(event), should_stop=should_stop,
                      functions={"converse": lambda text: converse(text, on_delta, on_emotion, should_stop)})
    if result.status == "error":
        raise RuntimeError(result.error)
    behaviour.record_signals(core.run_log, result.run_id, result.answer or "", node="converse")     # the violations of the text the model wrote are signals (BF2); the chat service repairs the text silently before the page sees it, and nobody is scolded
    return result.answer

def speak_answer(text):
    """MIA says the answer of a research (not its list of sources)"""
    spoken = speech_text(text)
    if not spoken:
        return
    streamer = SpeechStreamer(get_websocket_url(address=ADDRESS, protocol=PROTOCOL), SOUND_PORT)
    streamer.finish(spoken)
    streamer.wait()

_db_dir = os.path.join(FPATH, cfg.get(CONST.ACCOUNTS_DIR_KEY, "data/db"))
_votes_store = Storage(FileBackend(_db_dir))                  # the votes table (REQ-CHA-015); the accounts use the same folder
_workflow_library = WorkflowLibrary(_votes_store)             # IF-203 on the same storage; the review workflow is its first entry (a draft)

def run_memory_skill(inputs):
    """the skill memory_write: what to remember from one message of the user"""
    result = core.run("memory_write", inputs)
    if result.status != "done":
        raise RuntimeError(result.error)
    return result.answer

_remember = None
if cfg.get(CONST.STRUCTURED_MEMORY_KEY, False):               # off by default: one more call of the light model after every plain chat turn
    comm.memory_provider, _remember = memory_hooks(MemoryRecords(_votes_store, budget_tokens=cfg.get(CONST.MEMORY_BUDGET_KEY, 400)), run_memory_skill)
# REQ-WFM-029: the tasks register themselves; the chat core names none of them. A new skill adds one line here (later: its own folder, see the extension rule of 2026-10-29)
# REQ-WFM-029, -039: the tasks are the extensions in the folder `extensions/` (lookup, search, review, ...); the chat core names none of them. A new skill is a new folder there.
_services = types.SimpleNamespace(
    core=core, cfg=cfg, scholar=_scholar, web_get=_web_client.get, library=_workflow_library,
    web_search=lambda: _web_tools["web_search"][0],
    pipeline_event=lambda event: chat_service.pipeline_event(event), note_sources=lambda sources: chat_service.note_sources(sources),   # the chat service is built below
    speaker=lambda task: speaker_for(cfg, task, speak_answer),                      # one voice rule for all tasks (workflow_voice.py)
    trust_for_url=lambda: source_trust.build_trust(cfg).for_url)
_tasks = TaskRegistry()
_extension_problems = load_extensions(__package__ + ".extensions", os.path.join(FPATH, "extensions"), _tasks, _services)
for _problem in _extension_problems:
    print("an extension was not loaded: %s" % _problem)
# the files volume (REQ-WFM-037): a folder of its own, movable by `files_dir`; limits in bytes; nothing is deleted by MIA
_file_store = FileStore(os.path.join(FPATH, cfg.get("files_dir", "data/files")), max_file_bytes=cfg.get("files_max_bytes", 1 << 30), max_total_bytes=cfg.get("files_max_total_bytes", 50 << 30))
_model_classes = ModelClasses(os.path.join(FPATH, cfg.get("model_classes_file", "data/model_classes.json")))
_model_host = lambda: (str(cfg.get("ollama_host") or "localhost").replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]) or "localhost"
chat_service = ChatService(socketio.emit, chat_log, mood, run_chat_exchange, run_command=run_chat_command,
                           tasks=_tasks, skill_options=cfg.get("skill_options"), files=_file_store, unavailable={p.split(":")[0] for p in _extension_problems},
                           prepare_task=make_prepare(_model_classes, lambda: comm.version, _model_host, lambda text: chat_service.note(text)),
                           argument_commands={"model": make_model_command(_model_classes, lambda: comm.version, _model_host)},
                           review_timeout=cfg.get("review_answer_seconds", 1800),
                           model_info=lambda: (comm.version, getattr(comm, "profile", None)),
                           queue_size=cfg.get(CONST.CHAT_QUEUE_KEY, 5 if cfg.get(CONST.ACCOUNTS_KEY, False) else 1),
                           user_limit=2 if cfg.get(CONST.ACCOUNTS_KEY, False) else 0,           # IF-101: 5 waiting in all, 2 per account
                           rate_limit=(cfg.get(CONST.CHAT_RATE_KEY, 10), 60),
                           spawn=socketio.start_background_task, votes=_votes_store,
                           behaviours=behaviours_from_file(os.path.join(FPATH, cfg.get(CONST.BEHAVIOURS_FILE_KEY, "library/behaviours.json"))),
                           reputable=cfg.get(CONST.REPUTABLE_TRUST_KEY, 0.6),
                           repair=lambda text: behaviour.apply_rules(text)["text"], remember=_remember)         # the stream is held back and repaired silently (REQ-CHA-014)
app.register_blueprint(create_chat_ops_blueprint(chat_service))
app.register_blueprint(create_files_blueprint(_file_store))
app.register_blueprint(create_items_blueprint(_votes_store, socketio.emit))
app.register_blueprint(create_trust_persona_blueprint(os.path.join(FPATH, cfg.get("source_trust_file") or "data/source_trust.json"),      # the file build_trust reads
                                                      os.path.join(FPATH, cfg.get(CONST.PERSONA_FILE_KEY, "data/persona.json")), socketio.emit))
_chat_token = cfg.get(CONST.CHAT_TOKEN_KEY, app.config["EDITOR_TOKEN_INFO"][0])
app.register_blueprint(create_chat_blueprint(chat_service, token=_chat_token or None, allowed_origins=lambda: allowed_origins))

# login, session and logout (N-2.1 T-01). Off by default: the other routes are not protected by the session before T-02, and the old page has no login.
# Create the first account with `python tools/accounts_cli.py create NAME`.
_account_sockets = None
if cfg.get(CONST.ACCOUNTS_KEY, False):
    _account_store = _votes_store
    _account_changes = accounts_api.ChangeLog(os.path.join(FPATH, cfg.get(CONST.CHANGES_LOG_KEY, "data/changes.jsonl")))
    _account_service, _account_sockets = accounts_api.install(
        app, socketio, _account_store, changes=_account_changes, allowed_origins=lambda: allowed_origins,
        open_paths=("/",), open_prefixes=("/static/",),                       # the page and its files; the character, backgrounds and audio need the session
        internal_paths=(f"/{UPLOAD_ROUTE}", f"/{CONST.TIME_ROUTE}"), internal_token=ensure_token())      # our own speech process and scheduler

# the chat page loads only its own files: no inline scripts, no external hosts (ui/REQUIREMENTS_CHAT.md, 8)
CHAT_PAGE_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; "
    "connect-src 'self'; frame-src 'self'; media-src 'self' blob:; object-src 'none'; base-uri 'none'; "
    "form-action 'self'; frame-ancestors 'self'"
)

@app.after_request
def chat_page_headers(response):
    if request.path == '/' or request.path.startswith('/static/chat/'):
        response.headers.setdefault('Content-Security-Policy', CHAT_PAGE_CSP)
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('Referrer-Policy', 'same-origin')
    return response

@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info('Rendering index.html template')
    print("Rendering index.html template")
    # start server
    renderer = render_template('index.html' ,socket_url=get_url(json=True,**cfg),name=md.convert("*MIA*",remove_paragraph=True))
    return renderer

@socketio.on(CONST.CHARACTER_READY_EVENT)
def character_ready(_=None):
    """
    A page loaded the character: show the current expression (idle after the start).
    """
    send_expression(pre_exp.current or pre_exp.express(IDLE_EXPRESSION))

def list_backgrounds():
    """
    Names of the pictures in the backgrounds folder (sorted) and the one to show first.
    """
    if not os.path.isdir(BACKGROUND_FOLDER):
        return [], ""
    files = sorted(f for f in os.listdir(BACKGROUND_FOLDER)
                   if f.lower().endswith(CONST.BACKGROUND_EXTENSIONS) and os.path.isfile(os.path.join(BACKGROUND_FOLDER, f)))
    wanted = cfg.get(CONST.BACKGROUND_IMAGE_KEY)
    return files, (wanted if wanted in files else (files[0] if files else ""))

@app.route(f"/{CONST.BACKGROUND_LIST_ROUTE}")
def character_background_list():
    files, default = list_backgrounds()
    response = jsonify({"files": files, "default": default})
    response.headers["Cache-Control"] = "no-cache"
    return response

@app.route(f"/{CONST.BACKGROUND_ROUTE}/<path:filename>")
def character_background(filename):
    """
    Delivers one background picture (only pictures, only from the backgrounds folder).
    """
    if filename not in list_backgrounds()[0]:
        return "No such background picture", 404
    response = send_from_directory(BACKGROUND_FOLDER, filename)
    response.headers["Cache-Control"] = "no-cache"
    return response

@app.route(f"/{CONST.CHARACTER_ROUTE}/")
def character_index():
    return character_file("index.html")

@app.route(f"/{CONST.CHARACTER_ROUTE}/<path:filename>")
def character_file(filename):
    """
    Serves the web export of the 3D character with the right MIME types (incl. .wasm).
    """
    if not os.path.isdir(CHARACTER_FOLDER):
        return (f"Character not built yet. Run ui/tools/build_web.sh (expected in {CHARACTER_FOLDER}).", 404)
    response = send_from_directory(CHARACTER_FOLDER, filename)
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.route(f"/{UPLOAD_ROUTE}", methods=["POST"])
def upload_sound_file():
    if "file" not in request.files:
        return "No file part", 400
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400
    main_fname = os.path.split(file.filename)[1]
    url_filename = os.path.join(UPLOAD_FOLDER,main_fname)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file.save(url_filename)
    logger.info("File uploaded successfully")
    publish_audio(url_filename, "line", move=True)
    log_msg = "Audio loaded sucessfully"
    logger.info(log_msg)
    return log_msg

@app.route(f'/{AUDIO_ROUTE}/<filename>')
def serve_audio(filename):
    response = send_from_directory(AUDIO_DIR, filename,mimetype=AUDIO_MIME_TYPE)
    response.headers["Cache-Control"] = "no-store"
    return response

# @socketio.event
# def emit_audio_file():
#     filename = 'static/audio.wav'
#     sio.emit('audio', send_file(filename, 
# mimetype='audio/wav'))

@socketio.on('audio_claim')
def handle_audio_claim(data=None):
    """a page that is visible / used asks to play the voice; a page that was just loaded (initial) also gets the intro sound"""
    if audio_router.claim(request.sid) and isinstance(data, dict) and data.get("initial"):
        play_intro_sound()
    return {"owner": audio_router.target() == request.sid}

@socketio.on('audio_ended')
def audio_ended(data=None):
    """playback of a line ended (informational: every line has its own file, which is removed later)"""
    return "ok"

@socketio.on('disconnect')
def handle_disconnect(_reason=None):
    if _account_sockets is not None:
        accounts_api.forget_socket(_account_sockets)
    audio_router.disconnect(request.sid)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    pre_exp.express(IDLE_EXPRESSION)
    socketio.run(app, debug=True,port=WEB_PORT)
