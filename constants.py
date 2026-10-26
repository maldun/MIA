CFG_FILE = "setup_cfg.json"
LOG_FNAME = "mia.log"

# time format
TIME_FORMAT = "%Y.%m.%d %H:%m:%S:"

# encoding
U8 = "utf-8"

# Textbox settings
TEXT_COLS = 75

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
SKILLS_DIR_KEY = "skills_dir"                   # skill files (ui/REQUIREMENTS_CORE.md 3)
DEFAULT_SKILLS_DIR = "skills"
LIBRARY_DIR_KEY = "library_dir"                 # the shipped nodes and pipelines (ui/REQUIREMENTS_CORE.md 4a)
DEFAULT_LIBRARY_DIR = "library"
USER_LIBRARY_DIR_KEY = "user_library_dir"       # the entries of the user and of models, plus the status decisions
DEFAULT_USER_LIBRARY_DIR = "data/library"
LIBRARY_INDEX_KEY = "library_index"             # the SQLite index (can be deleted, it is rebuilt)
DEFAULT_LIBRARY_INDEX = "data/library.sqlite"
RUNS_DIR_KEY = "runs_dir"                       # the log of the runs (data for evaluation and learning)
DEFAULT_RUNS_DIR = "data/runs"
RESEARCH_PIPELINE_KEY = "research_pipeline"     # the pipeline of the library that /research runs (None: the one the skill `research` names)
DEFAULT_RESEARCH_PIPELINE = None
SEARCH_RESULTS_SHOWN_KEY = "search_results_shown"   # how many results /search shows
DEFAULT_SEARCH_RESULTS_SHOWN = 5
GESTURES_DIR_KEY = "gestures_dir"
DEFAULT_GESTURES_DIR = "data/gestures"
DEFAULT_PRESETS_DIR = "data/presets"

# chat (ui/REQUIREMENTS_CHAT.md 6)
CHAT_LOG_KEY = "chat_log"                      # append-only conversation log (not MIA's memory)
DEFAULT_CHAT_LOG = "data/chat_log.jsonl"
CHAT_LOG_MAX_KEY = "chat_log_max_messages"
CHAT_QUEUE_KEY = "chat_queue"                  # how many messages may wait while MIA answers
CHAT_RATE_KEY = "chat_rate_per_minute"         # messages per minute and connection, 0 = no limit
CHAT_TOKEN_KEY = "chat_token"                  # token for deleting the conversation (default: the editor token)
ACCOUNTS_KEY = "accounts_enabled"              # login, session and logout (N-2.1); off until the other routes are protected too (T-02)
ACCOUNTS_DIR_KEY = "accounts_dir"              # the folder of the file storage that holds the accounts
PERSONA_FILE_KEY = "persona_file"              # the persona of the chat as a shared JSON file (IF-101 persona)
CHANGES_LOG_KEY = "changes_log"                # who changed what (REQ-API-009), one JSON line per change
MOODS_FILE_KEY = "moods_file"
DEFAULT_MOODS_FILE = "moods.json"
MOOD_HOLD_KEY = "mood_hold_minutes"

# expressions from a description (ui/REQUIREMENTS.md 4.6)
EXPRESSION_MODEL_KEY = "expression_model"              # default: the model MIA is using right now
EXPRESSION_TEMPERATURE_KEY = "expression_temperature"
DEFAULT_EXPRESSION_TEMPERATURE = 0.7
FEEDBACK_LOG_KEY = "feedback_log"

# remote access (ui/REQUIREMENTS.md 4.8)
TAILSCALE_KEY = "tailscale"                    # true: MIA publishes itself in your tailnet with `tailscale serve` at start
PUBLIC_HOSTS_KEY = "public_hosts"              # more host names pages may be loaded from (e.g. a reverse proxy), besides the tailnet name
DEFAULT_FEEDBACK_LOG = "data/feedback_log.jsonl"
EDITOR_TOKEN_KEY = "editor_token"            # "" or false: no token; missing: a token is generated on first start
EDITOR_TOKEN_FILE_KEY = "editor_token_file"
DEFAULT_EDITOR_TOKEN_FILE = "data/editor_token.txt"
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
