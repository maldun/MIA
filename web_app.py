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

from flask import Flask, render_template, request, send_file, g, jsonify
import av
import cv2
import json
from flask_socketio import SocketIO, emit
import logging
import os
import time
import threading
import multiprocessing as mp

import markdown
from markdown import Markdown
class MyMarkdown(Markdown):
    """
    Stupid hack ...
    """
    PREFIX = "<p>"
    SUFFIX = "</p>"
    def convert(self, text,remove_paragraph=False):
        t = super().convert(text)
        if remove_paragraph is True:
            t = t.removeprefix(self.PREFIX).removesuffix(self.SUFFIX)
        return t
    # def add_paragraphs(self, text):
    #     lines = text.splitlines()
    #     lines = [self.PREFIX+line+self.

md = MyMarkdown(output_format='html')

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

with open(cfg_file,'r') as jp:
    cfg = json.load(jp)
PORT_OPT = "web_port"

from .expressor import VideoExpressor
vid_exp = VideoExpressor()

from .communicator import Communicator
comm = Communicator(**cfg)

from .speak import Speaker, split_into_lines_and_sentences
#speaker = Speaker(**cfg)


app = Flask(__name__, static_folder=static_folder)
lock = threading.Lock()

port = int(cfg[PORT_OPT])
URL_KEY = "url"
def get_socket_url(port,page="localhost",protocol='ws'):
    return {URL_KEY:f"{protocol}://{page}:{port}"}

socketio = SocketIO(app,cors_allowed_origins=get_socket_url(port,protocol='http')[URL_KEY])

#g.socket_url = f"ws://127.0.0.1:{port}/"

logger = logging.getLogger(__name__)

# Set log level to DEBUG
logger.setLevel(logging.DEBUG)

# Create a logging handler that writes logs to a file
handler = logging.FileHandler(os.path.join(fpath,LOG_FNAME))
handler.setLevel(logging.DEBUG)  # Set level here as well
logger.addHandler(handler)

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

# Create a function to handle messages from clients
@socketio.on('message')
def handle_message(message):
    logger.info("Received message: {}".format(message))
    print(f"Received message: {message}")
    express_and_reload("idle")
    time.sleep(1)
    #express_and_reload("talk")
    
    answer = ""
    partial_chunk = ""
    emotion = None
    emotion_set = False
    nr_emotions = 0
    answer_stream = comm.chat(message)
    answer_list = []
    for chunk in answer_stream:
        chunk_str = comm.handle_chunk(chunk)
        answer += chunk_str
        emotions, text = comm.extract_emotion(answer)
        if nr_emotions < len(emotions):
            emotion = emotions[nr_emotions]
            tx = text[nr_emotions]
            nr_emotions+= 1

            express_and_reload(emotion)
            emotion_set = True
        #else:
        #    filt_answer = comm.extract_emotion(answer)
        #    send_answer(filt_answer)
        filt_answer = comm.extract_text(answer)
        send_answer(filt_answer)
    
    # if nr_emotions < len(emotions) and len(text[-1]) > 0:
    #     p = mp.Process(target=speaker.text2voice, args=(text[-1],))
    #     p.run()
    
    filt_answer = comm.extract_text(answer)
    
    send_answer(filt_answer)
    comm.update_history(answer)
    comm.dump_history()
    filt_answer = comm.extract_text(answer)
    # if len(filt_answer.strip()) > 0:
    #     try:
    #         with lock:
    #             speaker.text2voice(filt_answer)
    #     except RuntimeError as rt:
    #         logger.error(str(rt))
    # wailt till finished ... clonky ...
    while os.path.exists(exchange_file):
        pass
    with open(exchange_file,'w') as fp:
        fp.write(filt_answer)
    while os.path.exists(exchange_file):
        pass
        
    send_answer(filt_answer,markdown=True)
                
    #speaker.text2voice(answer)
    
    time.sleep(1)
    #express_and_reload("talk")
    time.sleep(0.5)
    express_and_reload("idle")
    
    return "Message received successfully"


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

def send_answer(answer,markdown=False):
    logger.info("Sent answer: {}".format(answer))

    if markdown is True:
        answer = md.convert(answer)
        iframe_code_body=f"<pre>\n{answer}\n</pre>"
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
    return render_template('index.html' ,socket_url=get_socket_url(port),name=md.convert("*MIA*",remove_paragraph=True))

@socketio.on('reload_video')
def reload_video(vid):
    logger.info('Received signal to reload video')
    # Update the video source here
    url = vid
    time.sleep(0.1)
    emit('video_updated', url)

if __name__ == '__main__':
    vid_exp.express("idle")
    socketio.run(app, debug=True,port=port)
