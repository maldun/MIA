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

from expressor import VideoExpressor
vid_exp = VideoExpressor()

# constants and paths
fpath = os.path.split(__file__)[0]
TEMPLATE_DIR = "templates"
STATIC_DIR = os.path.join(TEMPLATE_DIR,"static")
static_folder = os.path.join(fpath,STATIC_DIR)
LOG_FNAME = "mia.log"
CFG_FILE = os.path.join("..","setup_cfg.json")
with open(CFG_FILE,'r') as jp:
    cfg = json.load(jp)
PORT_OPT = "web_port"


app = Flask(__name__, static_folder=static_folder)

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


# Create a function to handle messages from clients
@socketio.on('message')
def handle_message(message):
    logger.info("Received message: {}".format(message))
    print(f"Received message: {message}")
    with open("testmsg.txt",'w') as fp:
        fp.write(message)
    new_vid = vid_exp.express("idle")
    reload_video(new_vid)
    return "Message received successfully"



@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info('Rendering index.html template')
    print("Rendering index.html template")
    return render_template('index.html' ,socket_url=get_socket_url(port),name="ich")

@socketio.on('reload_video')
def reload_video(vid):
    print('Received signal to reload video')
    # Update the video source here
    url = vid
    emit('video_updated', url)


if __name__ == '__main__':
    vid_exp.express("greet")
    socketio.run(app, debug=True,port=port)
