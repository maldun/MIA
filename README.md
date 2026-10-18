MIA - MIA Is not an Assistant
==============================

    Copyright (C) 2024  Stefan Reiterer

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Attempt to create my own virtual assistant. This project can be seen as long term and evolving.
It is not the goal to make state of the art algorithms, but to deepen my understanding of machine learning, by trying out to automate everyday tasks, and machine communication. It's also fun
to have your own virtual waifu ....

Installation
==================

Prerequisites:
--------------

- python >= 3.10 (if you want rvc running then currently it is 3.10)
- rocm/cuda (works with CPU but slow....)
- docker/podman
- (Tested on Fedora 40; should work on other systems though)
- Some mp4 files for expression of feelings (set in expressions.json; can be extended shortened as needed)
- a .wav voice sample of your choice (set under option `voice_sample` in `setup_cfg.json`).
- background .jpg file of your choice (into `templates/static/background.jpg`).
- optional: a .pth model for rvc.
(I made my own with blender and collected other stuff, but I don't share due to copyright reasons. Private use is one thing, publishing another ..., but the internet is full of fun stuff so go ahead.)

### Create virtual environment (example)
- `python -m venv <venvfolder>/mia`
- `<venvfolder>/mia/bin/activate`

### Install ROCM/CUDA (Fedora):
- `sudo usermod -a -G video $LOGNAME`
- `sudo dnf install rocminfo`
- `sudo dnf install rocm-opencl`
-  `sudo dnf install rocm-clinfo`
- `sudo dnf install rocm-hip`
- `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0`

- (Source: https://medium.com/@anvesh.jhuboo/rocm-pytorch-on-fedora-51224563e5be)

### Install coqui-ai tts:
- `git clone https://github.com/idiap/coqui-ai-TTS.git`
- `pip install -e .[all,dev,notebooks]  # Select the relevant extras`

### Install python-rvc (Optional):
- `git clone https://github.com/daswer123/rvc-python`
- `python3.10 -m pip install -e .`

### Install Kokoro TTS (default tts engine):
- `python3.10 -m pip install espeakng-loader phonemizer onnxruntime "numpy==1.26.4"`
- `python3.10 -m pip install --no-deps kokoro-onnx` (it asks for numpy>=2, but works with 1.26 which rvc/coqui need)
- Download `kokoro-v1.0.onnx` and `voices-v1.0.bin` from https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 into `voice/models/kokoro/`
- Compare voices and pitch shifts with `python3.10 voice_lab.py` (writes samples to `voice/samples/lab/`)

### Clone
- `git clone https://github.com/maldun/MIA.git`
- Go into MIA folder
- Install/Check requirements in requirments.txt (`python -m pip install -r requirments.txt`)

### Configuration
- (my settings are included as an example)
- Configure setup_cfg.json to your liking (here my default)

    - "name":"ollama", (docker name)
    - "docker":"docker", (docker executable e.g. podman as alernative; Fedora symlinks podman)
    - "port":11434, (ollama port)
    - "version":"gemma4:26b", (ollama model)
    - "llm_options":{"num_ctx":8192}, (ollama model options, e.g. context size)
    - "version_light":"gemma4:12b-it-qat", (optional: smaller model; switch with /light! and back with /full!, e.g. if the GPU is needed for other programs)
    - "llm_options_light":{"num_ctx":8192}, (options of the light model)
    - "keep_alive":"30m", (how long the model stays loaded after a request; avoids cold starts, e.g. for the hourly time check)
    - "think":false, (thinking mode of the model; leave out for model default)
    - "mode":"rocm", (gpu flag, check ollama docker docu)
    - "timeout":3, (pause in seconds before the character returns to the idle expression)
    - "character_dir":"ui/godot/build/web", (optional: folder with the web export of the 3D character, see ui/README.md)
    - "https_port":8586, (optional: `python -m MIA` starts an HTTPS proxy on this port in front of the web app, see "Access from other computers")
    - "host":"0.0.0.0", (optional: address the web app listens on; default all addresses, i.e. localhost and LAN)
    - "shutdown_pause":1.0, (optional: seconds between the shutdown steps, see "Stopping MIA")
    - "presets_dir":"data/presets", (optional: folder with the expression presets of the character, one json file per preset, shared by all devices; filled with the default presets on first use)
    - "editor_token":"a secret", (optional: the token that changing presets in the expression editor needs; reading is open. If the key is missing, a random token is created on the first start in `data/editor_token.txt` (not in version control) and printed when MIA starts; "" switches the token off)
    - "background_dir":"backgrounds", (optional: folder with background pictures for the character, see backgrounds/README.md)
    - "background_image":"room.jpg", (optional: picture shown at the start, default: the first one)
    - "web_port":8585, (port for web-app)
    - "address":"localhost", (adress)
    - "protocol":"http", (web protocol used for site)
    - "tts_engine":"kokoro", (tts engine: kokoro or coqui)
    - "kokoro_opts":{"voice":"af_heart","speed":1.0,"lang":"en-us"}, (kokoro settings; "model" and "voices" paths can be set too)
    - "tts_model":"tts_models/en/ljspeech/glow-tts", (tts model for coqui engine; see TTS docu)
    - "voice_model":"/path/to/MIA/voice/models/modelname/model.pth", (optional: voice model for rvc)
    - "rvc_opts":{"index_path":"/path/to/MIA/voice/models/modelname/model.index","version":"v2"},
    - "rvc_params":{"f0method":"rmvpe","f0up_key":3},  (for these see python-rvc docu)
    - "rvc_enabled":true, (enable,disable rvc)
    - "sentence_pause":0.3, (extra pause in seconds between spoken sentences)
    - "tts_device":"cpu", (device for tts, either cuda/cpu, for some reason cpu worked better ...)
    - "cpu_threads":4, (optional, off by default: at most this many CPU threads for the speech process (torch for RVC/Coqui, onnxruntime for Kokoro, numpy) and for Ollama's runner (`num_thread`); without it (or 0) every library uses all cores. A lower number puts less load on the CPU at the price of slower speech. An explicit "num_thread" in "llm_options" wins. After changing it the first request reloads the model once.)
    - "chat_log":"data/chat_log.jsonl", (optional: the conversation as the chat page shows it, one JSON object per line; separate from MIA's memory, so dreaming does not touch it. Stays on this machine; delete the file or use the "clear" API to remove the history)
    - "chat_log_max_messages":10000, (optional: the oldest messages are dropped above this number)
    - "chat_queue":1, (optional: how many messages may wait while MIA is answering; more are refused with a hint)
    - "chat_rate_per_minute":10, (optional: messages per minute and connection, 0 = no limit)
    - "chat_token":"a secret", (optional: token for deleting the conversation over the API; default is the editor token)
    - "moods_file":"moods.json", "mood_hold_minutes":10, (optional: the phrases of the mood line (edit them to match MIA's personality) and how long a mood stays after the last answer)
    - "expression_model":"gemma4:12b-it-qat", "expression_temperature":0.7, "feedback_log":"data/feedback_log.jsonl", (optional: expressions from a description in the expression editor. The model defaults to the one MIA is using right now (same options, so Ollama does not reload anything); the log keeps what you kept, edited or rejected, and is used as examples in later requests)
    - "gfx_version":"11.0.0", (flag used for roc)
    - "voice_sample":"/path/to/MIA/voice/samples/miku_vocals.wav",(voice sample for tts voice cloning)
    - "history_file":"memories.json" (MIA's memory)

- The character on the page is a 3D model (Godot web export, see `ui/README.md`). Build it once with `ui/tools/build_web.sh`; MIA serves it under `/character/` and shows it in the page. It replaces the old pre-rendered videos.
- Configure expressions.json: every expression has a `preset` (expression of the character, see `ui/godot/presets/library.json`; default: the expression key itself), the spoken `text` and the `voice` clip (`null` = no voice clip yet).
- Set the emotions and the expressions associated with it in emotion_map.json. When the AI provides an emotion the character makes the proper expression (face, arm gesture) and the voice clip is played. The mouth moves while MIA's voice plays. **Important** The example should be the minimal set of emotion. Don't remove one of them! Emotions can be added: the prompt for the AI is built from this file (new expressions need a preset with the same name or a `preset` entry).
- Some configurations are found in `constants.py` which can be adjusted like textbox settings.
    - CFG_FILE = "setup_cfg.json" (cfg file to use)
    - LOG_FNAME = "mia.log" (log file)
    - TEXT_COLS = 60
- Generate expressions with `python -m python3.10 -i speak.py setup_cfg.json expressions.json --generate`
- Add Optional: add favicon.ico in templates/static, Add intro_sound (.wav). to setup_cfg.json.

    
- First time: go into the MIA folder and run `install_lama.py setup_cfg.json -f`. The docker will start. You can chat a little and then exit with `/bye`.

Usage:
===================

- Start: Activate virtual env and start: `python -m MIA`.
- Open Webbrowser on `localhost:<web_port>`
- *Hint*: KDE has a web browser plugin as desktop app ...

Expression editor:
===================

The link "Edit expressions" in MIA's page (or `/character/?editor`) opens the character with the slider editor: one slider per shape key
(eyes, brows, mouth, head, other), a filter, load / reset / save as new / overwrite / rename / delete. Presets are saved on MIA's server
(`presets_dir`), so a preset made on the phone is there on every other device a few seconds later. Presets that MIA's emotions use
(`expressions.json`) cannot be deleted or renamed by accident. Changing presets needs a token: MIA creates one on the first start (`data/editor_token.txt`, readable only by you) and prints it when it starts;
the editor asks for it once per device and remembers it in the browser. `"editor_token"` in `setup_cfg.json` sets your own token, `""` switches it off.
Without the server the character uses its bundled presets.

Stopping MIA:
===================

Ctrl+C in the terminal, the commands `/break!` and `/goodnight!` (the latter lets MIA dream first) and SIGTERM all lead to the same orderly shutdown:
MIA saves its history, stops the HTTPS proxy and then the speech process, one step after the other with a pause of `shutdown_pause` seconds in between.
The helper processes run in their own session, so Ctrl+C reaches only MIA. Before, everything was signalled at the same instant and the commands killed the whole process group.
A helper that does not end within 10 seconds is killed. The Ollama container keeps running.

Access from other computers or phones (HTTPS):
===================

The 3D character only runs in a *secure context*: on `localhost` or over HTTPS. Opening `http://<lan address>:<web_port>` from another device
(or on this computer via the LAN address) fails with a message that HTTPS is needed.

- On this computer use `http://localhost:<web_port>`.
- For other devices set `"https_port":8586` in `setup_cfg.json` and install `openssl` and `socat` (`sudo dnf install openssl socat`).
  `python -m MIA` then starts an HTTPS proxy together with MIA (and stops it with MIA) and prints the addresses:
  `https://<lan address>:8586` (also `https://localhost:8586`). A self-signed certificate is created in `ui/certs` on the first start.
- Use the HTTPS port only with `https://`: `https://localhost:<web_port>` does not work, the web port speaks plain HTTP.
- The browser warns once about the certificate (Advanced > continue). Import `ui/certs/mia.crt` as trusted certificate to avoid that.
- Without MIA the proxy can be started by hand: `ui/tools/https_proxy.sh 8586 127.0.0.1:<web_port>`.
- From outside the home network use Tailscale (`tailscale serve`), which provides a trusted HTTPS address without opening ports.
- Special Commands:
    - /dream! : MIA summarizes her memories and a new chat is started based on this summy.
    - /goodnight! : shuts down MIA and let her dream
    - /break! : shuts down MIA (service). Re-Start where you left of, so itś like she is on break.
    - /light! : switches to the light model (`version_light`) and unloads the full one, to free GPU memory for other programs.
    - /full! : switches back to the full model.


Programm Structure
==================

- Ollama Container running as service.
- speaker Server: Handles TTS requests via socketserver.
- memories.json: Memory of MIA, shouldn't be too big even after longer time.
- webapp: Flask app to handle communication with Computer
- HTML Site: Web interface.
- media files for expressions and background.

```
MIA ..> LLM Server <---
 |         |          |
 |         v          |
  ...> Speak Server   | 
 |         |          |
 |         v          |
  ...> Web App <----------> media
  
( ...> : Starts; ---> communicates with)
``` 
Tasks
=====

- Communication: Communication with the user
- Expression of feelings
- Talking with the user (via TTS)

Notes
==================
- It may be necessary to reset before if docker makes problem ... e.g. with podman do `podman system reset`
- Setup rocm properly and install with `python3.10 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0`
- Also set your GLX proeprly with AMD cards, in my case it was: `os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"` check the correct one for your card!
- Downloads of bark can be faulty re-download fine_2.pt manually if you want to use bark for tts.
- This is tested for my setup. When other test it and hare intall notes I am happy to share them.
- Check if browser allows autoplay of sound files.

ToDo 
=====

- improve performance of TTS and RVC
- Make Package
- Make better input field.
- zip memories or find another way (let the LLM extract for example)
