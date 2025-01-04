from flask import Flask, render_template, request, send_file
import cv2
import av
from flask_socketio import SocketIO, emit
import logging
import os

fpath = os.path.split(__file__)[0]
TEMPLATE_DIR = "templates"
STATIC_DIR = os.path.join(TEMPLATE_DIR,"static")
static_folder = os.path.join(fpath,STATIC_DIR)
LOG_FNAME = "mia.log"

app = Flask(__name__, static_folder=static_folder)
socketio = SocketIO(app)

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
    return "Message received successfully"

@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info('Rendering index.html template')
    print("Rendering index.html template")
  
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)
