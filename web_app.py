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
import av
import cv2
import json
from flask_socketio import SocketIO, emit
import logging
import os
import time
import threading
import multiprocessing as mp
import shutil


# constants and paths
from .constants import CFG_FILE, LOG_FNAME, TEXT_COLOR, FONT_SIZE, BACKGROUND_COLOR
from .constants import TEXT_ROWS, TEXT_COLS, TEXT_FONT
fpath = os.path.split(__file__)[0]
cfg_file = os.path.join(fpath,CFG_FILE)
exchange_file = os.path.join(fpath,"exchange.txt")
TEMPLATE_DIR = "templates"
STATIC_DIR = os.path.join(TEMPLATE_DIR,"static")
static_folder = os.path.join(fpath,STATIC_DIR)
ANSWER_FILE = os.path.join(static_folder,"answer.html")

UPLOAD_DIR = os.path.join(TEMPLATE_DIR,"upload")
upload_folder = os.path.join(fpath,UPLOAD_DIR)
AUDIO_DIR = os.path.join(TEMPLATE_DIR,"audio")
audio_folder = os.path.join(fpath,AUDIO_DIR)

AUDIO_OUTFILE = "out.wav"

with open(cfg_file,'r') as jp:
    cfg = json.load(jp)
PORT_OPT = "web_port"
TIMEOUT_OPT = "timeout"

from .expressor import VideoExpressor, VoiceExpressor
vid_exp = VideoExpressor()
voc_exp = VoiceExpressor()

from .communicator import Communicator
comm = Communicator(**cfg)

from .utils import MyMarkdown, cut_down_lines, split_into_lines_and_sentences, chunker
md = MyMarkdown(output_format='html')

app = Flask(__name__, static_folder=static_folder)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
lock = threading.Lock()
app.config['MAX_CONTENT_LENGTH'] = 100*1024**2  # 16 MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


port = int(cfg[PORT_OPT])
timeout = int(cfg[TIMEOUT_OPT])
URL_KEY = "url"
def get_socket_url(port,page="localhost",protocol='ws'):
    return {URL_KEY:f"{protocol}://{page}:{port}"}

socketio = SocketIO(app,cors_allowed_origins=get_socket_url(port,protocol='http')[URL_KEY])

#g.socket_url = f"ws://127.0.0.1:{port}/"

from .mia_logger import logger

logger.debug('Start Logging')
print("start")

# Video file path
VIDEO_FILE = "/home/maldun/prog/Python/MIA/expressor/vids/greet000.mp4"

def get_video_frames(video_path):
    logger.info("Getting video frames")
    # Open the video file using av
    with open(video_path, 'rb') as f:
        stream = av.open(f)
        for packet in stream.decode():
            yield packet.to_image()
    return "Video frames retrieved successfully"


def express_and_reload(expression):
    new_vid = vid_exp.express(expression)
    reload_video(new_vid)
    voc_exp.express(expression)

# Create a function to handle messages from clients
@socketio.on('message')
def handle_message(message):
    logger.info("Received message: {}".format(message))
    print(f"Received message: {message}")
    result = process_message(message)
    logger.info(str(message))
    
    log_msg="Message received successfully"
    logger.info(log_msg)
    return log_msg

def penalize(answer):
    emotions, text = comm.extract_emotion(answer)
    penalty = comm.penalize(emotions,text)
    if isinstance(penalty,str):
        logger.info("Penalty!: " + str(penalty))
        time.sleep(timeout/2)
        process_message(penalty)
    elif penalty is None:
        return
    

def process_message(message):
    #express_and_reload("idle")
    time.sleep(1)
    #express_and_reload("talk")
    
    # answer = ""
    # partial_chunk = ""
    # emotion = None
    # emotion_set = False
    # nr_emotions = 0
    # answer_stream = comm.chat(message)
    # answer_list = []
    # for chunk in answer_stream:
    #     chunk_str = comm.handle_chunk(chunk)
    #     answer += chunk_str
    #     emotions, text = comm.extract_emotion(answer)
    #     if nr_emotions < len(emotions):
    #         emotion = emotions[nr_emotions]
    #         #tx = text[nr_emotions]
    #         nr_emotions+= 1
    #         express_and_reload(emotion)
    # 
    #     filt_answer = comm.extract_text(answer)
    #     send_answer(filt_answer)
    
#     filt_answer = comm.extract_text(answer)
#     
#     send_answer(filt_answer)
#     comm.update_history(answer)
#     comm.dump_history()

    answer, filt_answer = comm.exchange(message,
                                        emotion_reaction=express_and_reload,
                                        update_message=send_answer,
                                        filter_message=True)

    # wailt till finished ... clonky ...
    while os.path.exists(exchange_file):
        pass
    with open(exchange_file,'w') as fp:
        fp.write(filt_answer)
    while os.path.exists(exchange_file):
        pass
        
    send_answer(filt_answer,markdown=True)
    if len(filt_answer) == 0:
        # if no speech wait a bit
        time.sleep(timeout)
    
    penalize(answer)
    time.sleep(2)
    express_and_reload("idle")
    
    return "Message processed successfully"


iframe_code_header=f"""
<!DOCTYPE html>
<html>
<style>
body {{
     background-color: {BACKGROUND_COLOR};
     color: {TEXT_COLOR};
     font-size: {FONT_SIZE};
     font-family: {TEXT_FONT};
    }}
</style>
<body>
    """

iframe_code_footer="""
</body>
</html>
"""
# add markdown module
markdown_source='<script type="module" src="https://md-block.verou.me/md-block.js"></script>'

def send_answer(answer,markdown=False):
    logger.info("Sent answer: {}".format(answer))

    if markdown is True:
        #answer = md.convert(answer)
        answer = cut_down_lines(answer)
        iframe_code_body=markdown_source+'\n'+f'<md-block>\n{answer}\n</md-block>'
    else:
        answer=answer.lstrip()
        css_style=f"background-color: {BACKGROUND_COLOR};color: {TEXT_COLOR};font-size: {FONT_SIZE};font-family: {TEXT_FONT};"
        iframe_code_body=f'<textarea id="answerTextArea" style="{css_style}" rows="{TEXT_ROWS}" cols="{TEXT_COLS}">\n'
        iframe_code_body+=answer
        iframe_code_body+="</textarea>"

    iframe_code = "\n".join([iframe_code_header,iframe_code_body,iframe_code_footer])
    with open(ANSWER_FILE,'w') as af:
        af.write(iframe_code)
    emit('answer',answer)

@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info('Rendering index.html template')
    print("Rendering index.html template")
    vid_exp.express("idle")
    return render_template('index.html' ,socket_url=get_socket_url(port),name=md.convert("*MIA*",remove_paragraph=True))

@socketio.on('reload_video')
def reload_video(vid):
    logger.info('Received signal to reload video')
    # Update the video source here
    url = vid
    time.sleep(0.1)
    emit('video_updated', url)


@app.route("/upload", methods=["POST"])
def upload_sound_file():
    if "file" not in request.files:
        return "No file part", 400
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400
    
    main_fname = os.path.split(file.filename)[1]
    url_filename = os.path.join(upload_folder,main_fname)
    audio_filename = os.path.join(audio_folder,main_fname)
    file.save(url_filename)
    #file.save(os.path.join(static_folder, file.filename))
    
    logger.info("File uploaded successfully")
    mimetype="audio/wav"
    outfile = AUDIO_OUTFILE
    out_filename = os.path.join(audio_folder,AUDIO_OUTFILE)
    #send_file(url_filename,mimetype=mimetype,as_attachment=True,download_name=main_fname)
    #send_from_directory(url_filename,"upload",mimetype=mimetype,as_attachment=True,download_name=main_fname)

    shutil.move(url_filename,out_filename)
    serve_audio(outfile)
    log_msg = "Audio loaded sucessfully"
    socketio.emit('audio_reload',log_msg)
    logger.info(log_msg)
    return log_msg

@app.route('/audio/<filename>')
def serve_audio(filename):
    mimetype="audio/wav"
    return send_from_directory(AUDIO_DIR, filename,mimetype=mimetype)

# @socketio.event
# def emit_audio_file():
#     filename = 'static/audio.wav'
#     sio.emit('audio', send_file(filename, 
# mimetype='audio/wav'))

@socketio.on('audio_ended')
def cleanup_audio(vid):
    logger.info('Cleanup Audio File')
    # Update the video source here
    outfile = AUDIO_OUTFILE
    out_filename = os.path.join(audio_folder,AUDIO_OUTFILE)
    os.remove(out_filename)
    log_msg = "audio file deleted"
    logger.info(log_msg)
    emit('audio_reload',log_msg)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    vid_exp.express("idle")
    socketio.run(app, debug=True,port=port)
