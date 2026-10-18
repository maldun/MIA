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
import threading
import multiprocessing as mp
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
from .chat_service import ChatService
from .chat_api import create_blueprint as create_chat_blueprint
from .moods import MoodTracker
FPATH = os.path.split(__file__)[0]
cfg_file = os.path.join(FPATH,CFG_FILE)
TEMPLATE_DIR = "templates"
STATIC_DIR = os.path.join(TEMPLATE_DIR,"static")
STATIC_FOLDER = os.path.join(FPATH,STATIC_DIR)

UPLOAD_DIR = os.path.join(TEMPLATE_DIR,UPLOAD_ROUTE)
UPLOAD_FOLDER = os.path.join(FPATH,UPLOAD_DIR)

AUDIO_DIR = os.path.join(TEMPLATE_DIR,AUDIO_ROUTE)
AUDIO_FOLDER= os.path.join(FPATH,AUDIO_DIR)

AUDIO_OUTFILE = "out.wav"

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
voc_exp = VoiceExpressor(web_url=WEB_URL+'/'+UPLOAD_ROUTE)

from .communicator import Communicator
comm = Communicator(**cfg)

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
def build_allowed_origins(web_url, address, web_port, https_port=None, own_ip=None):
    """
    Origins (pages) that may connect to the socket: the page served by this app, reached via localhost, the
    configured address, our own address, plain or behind the HTTPS proxy.
    """
    hosts = ["localhost", "127.0.0.1", address, own_ip]
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
    return origins

try:
    _OWN_IP = utils.get_own_ip()
except Exception:  # no network: localhost only
    _OWN_IP = None
allowed_origins = build_allowed_origins(WEB_URL, ADDRESS, WEB_PORT, cfg.get(CONST.HTTPS_PORT_KEY), _OWN_IP)
if os.path.exists(ALLOWED_ORIGIN_FILE):
    with open(ALLOWED_ORIGIN_FILE,'r') as aof:
        allowed_origins += aof.read().splitlines()

socketio = SocketIO(app,cors_allowed_origins=allowed_origins)

# expression presets of the character (REST API, files in "presets_dir"); the editor of the character uses it
preset_store = init_presets_api(app,cfg,FPATH,allowed_origins=lambda: allowed_origins)

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

def express_and_reload(expression,sound=True):
    """
    Lets the character make the expression (and plays its voice clip).
    """
    pre_exp.express(expression)
    if sound is True:
        voc_exp.express(expression)

# Create a function to handle messages from clients
@socketio.on('chat_send')
def handle_chat_send(data=None):
    """{id (client id), text}: acknowledged right away, the answer follows as chat_* events"""
    data = data if isinstance(data, dict) else {"text": data}
    return chat_service.send(data.get("text"), client_id=data.get("id"), sender=request.sid)

@socketio.on('chat_stop')
def handle_chat_stop(_=None):
    return {"stopped": chat_service.stop()}

@socketio.on('connect')
def handle_connect(_auth=None):
    """a page connected: it learns the state (busy, model, mood) right away"""
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
    # nothing to do
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
    streamer = SpeechStreamer(get_websocket_url(address=ADDRESS,protocol=PROTOCOL),SOUND_PORT)
    reactions = []
    def react(emotion):
        # only the first expression plays its sound, otherwise it would cut off the speech
        express_and_reload(comm.map_emotion(emotion),sound=len(reactions)==0)
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
    response = requests.get(url, params=req)
    logger.info(response.text)

@app.route(f"/{CONST.TIME_ROUTE}", methods=["GET"])    
def time_update_request():
    if CONST.TASK_KEY not in request.values:
        return "No data sent", 400
    tasks = request.values.getlist(CONST.TASK_KEY)
    if CONST.UPDATE_TIME_TASK in tasks:
        return time_update() 

def time_update():
    answer, filt_answer, penalty = comm.time_update(
                                        emotion_expression=express_and_reload,
                                        _test_neutral=False,
                                        _test_neutral_but_penalty=False
                                        )
     
    if answer is None:
        pass
    else:
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
    



def play_intro_sound():
    # copy intro sound
    intro_sound = cfg["intro_sound"]
    out_audio = os.path.join(AUDIO_FOLDER,AUDIO_OUTFILE)
    candidates = {intro_sound,os.path.join(app.root_path,intro_sound)}
    for c in candidates:
        if os.path.exists(c):
            shutil.copy2(c,out_audio)
            serve_audio(AUDIO_OUTFILE)
            log_msg = "Intro Audio loaded sucessfully"
            socketio.emit('audio_reload',log_msg)
            break
    else:
        log_msg = "No Intro Audio found!"
    logger.info(log_msg)
    return log_msg

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
chat_service = ChatService(socketio.emit, chat_log, mood, converse, run_command=run_chat_command,
                           model_info=lambda: (comm.version, getattr(comm, "profile", None)),
                           queue_size=cfg.get(CONST.CHAT_QUEUE_KEY, 1),
                           rate_limit=(cfg.get(CONST.CHAT_RATE_KEY, 10), 60),
                           spawn=socketio.start_background_task)
_chat_token = cfg.get(CONST.CHAT_TOKEN_KEY, app.config["EDITOR_TOKEN_INFO"][0])
app.register_blueprint(create_chat_blueprint(chat_service, token=_chat_token or None, allowed_origins=lambda: allowed_origins))

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
    play_intro_sound()
    
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
    audio_filename = os.path.join(AUDIO_FOLDER,main_fname)
    file.save(url_filename)
    #file.save(os.path.join(STATIC_FOLDER, file.filename))
    
    logger.info("File uploaded successfully")
    outfile = AUDIO_OUTFILE
    out_filename = os.path.join(AUDIO_FOLDER,AUDIO_OUTFILE)
    #send_file(url_filename,mimetype=AUDIO_MIME_TYPE,as_attachment=True,download_name=main_fname)
    #send_from_directory(url_filename,"upload",mimetype=AUDIO_MIME_TYPE,as_attachment=True,download_name=main_fname)

    shutil.move(url_filename,out_filename)
    serve_audio(outfile)
    log_msg = "Audio loaded sucessfully"
    socketio.emit('audio_reload',log_msg)
    logger.info(log_msg)
    return log_msg

@app.route(f'/{AUDIO_ROUTE}/<filename>')
def serve_audio(filename):
    mimetype="audio/wav"
    return send_from_directory(AUDIO_DIR, filename,mimetype=AUDIO_MIME_TYPE)

# @socketio.event
# def emit_audio_file():
#     filename = 'static/audio.wav'
#     sio.emit('audio', send_file(filename, 
# mimetype='audio/wav'))

@socketio.on('audio_ended')
def cleanup_audio(vid):
    logger.info('Cleanup Audio File')
    # delete the audio file that was played
    outfile = AUDIO_OUTFILE
    out_filename = os.path.join(AUDIO_FOLDER,AUDIO_OUTFILE)
    try:
        os.remove(out_filename)
        log_msg = "audio file deleted"
        socketio.emit('audio_reload',log_msg)
    except FileNotFoundError as exc:
        log_msg = str(exc)
    logger.info(log_msg)
    return log_msg


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    pre_exp.express(IDLE_EXPRESSION)
    socketio.run(app, debug=True,port=WEB_PORT)
