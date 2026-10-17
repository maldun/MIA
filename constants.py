CFG_FILE = "setup_cfg.json"
LOG_FNAME = "mia.log"

# time format
TIME_FORMAT = "%Y.%m.%d %H:%m:%S:"

# encoding
U8 = "utf-8"

# Textbox settings
BACKGROUND_COLOR = "#000000"
TEXT_COLOR = "#6cf542"
FONT_SIZE = "16px"
TEXT_ROWS = 30
TEXT_COLS = 75
TEXT_FONT = 'Arial, cursive'

# Important config keys for expressions
EXPRESSION_FILE = "expressions.json"
TEXT_KEY = "text"
PRESET_KEY = "preset"  # name of the character expression preset (default: the expression key itself)
VOICE_KEY = "voice"

# folder with the web export of the 3D character (ui/godot), relative to this folder or absolute
CHARACTER_DIR_KEY = "character_dir"
DEFAULT_CHARACTER_DIR = "ui/godot/build/web"
CHARACTER_ROUTE = "character"
EXPRESSION_EVENT = "expression"      # socket.io event MIA -> page -> character
CHARACTER_READY_EVENT = "character_ready"
# optional: port of an HTTPS proxy in front of the web app (ui/tools/https_proxy.sh). Browsers only run the
# character (and use audio worklets) in a secure context, i.e. on localhost or over HTTPS.
HTTPS_PORT_KEY = "https_port"
# custom background pictures behind the character: pictures (png, jpg, webp) in this folder (relative to this
# folder or absolute); "background_image" names the one shown at the start (default: the first one)
BACKGROUND_DIR_KEY = "background_dir"
DEFAULT_BACKGROUND_DIR = "backgrounds"
BACKGROUND_IMAGE_KEY = "background_image"
BACKGROUND_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
# expression presets shared by all devices: one json file per preset in this folder (relative to this folder or absolute);
# "editor_token": optional secret that changing presets needs (header X-MIA-Token), see presets_api.py
PRESETS_DIR_KEY = "presets_dir"
DEFAULT_PRESETS_DIR = "data/presets"
EDITOR_TOKEN_KEY = "editor_token"
TOKEN_HEADER = "X-MIA-Token"
BACKGROUND_LIST_ROUTE = "character-backgrounds.json"
BACKGROUND_ROUTE = "character-backgrounds"

# Important Config Keys for URL
ADDRESS_KEY = "address"
PROTOCOL_KEY = 'protocol'
WEB_PORT_KEY = "web_port"
SOUND_PORT_KEY = "sound_port"
URL_KEY = "url"
UPLOAD_ROUTE = "upload"
AUDIO_ROUTE = "audio"
TIME_ROUTE = "time"

# Request_types:
SPEECH_REQ = "SPEECH"
SOUND_REQ = "SOUND"
# a stream request sends sentences line by line (json) over one connection
STREAM_REQ = "STREAM" # flag in the first line of a stream
STREAM_END_REQ = "STREAM_END" # last line of a stream
TIME_REQ = "TIME"
MESSAGE_SIZE=2**12

# Keys for scheduler
TIME_INTERVAL_KEY = "clock_interval"
TIME_BEFORE_KEY = "time_before"
SIGNAL_EMOTION_KEY = "signal_emotion"
NEUTRAL_EMOTION_KEY = "neutral_emotion"

# Other
AUDIO_MIME_TYPE="audio/wav"
TASK_KEY="task"
UPDATE_TIME_TASK = "update_time"
LOCALHOST = "localhot"

# special commands
SHUTDOWN_COMMAND = "/break!"
SLEEP_COMMAND = "/goodnight!"
DREAM_COMMAND = "/dream!"
UPDATE_COMMAND = "/time!"
LIGHT_COMMAND = "/light!" # switch to the light model (saves GPU memory)
FULL_COMMAND = "/full!" # switch back to the full model

MAIN_THREAD_ID_KEY = "MAIN_THREAD_ID"

ALLOWED_ORIGIN_FILE="allowed_origins.txt"
