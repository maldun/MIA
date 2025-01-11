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
    - "version":"llama3.2", (ollama model)
    - "mode":"rocm", (gpu flag, check ollama docker docu)
    - "timeout":3, (timeout setting for video refresh)
    - "web_port":8585, (port for web-app)
    - "address":"localhost", (adress)
    - "protocol":"http", (web protocol used for site)
    - "tts_model":"tts_models/en/ljspeech/glow-tts", (tts model; see TTS docu)
    - "voice_model":"/path/to/MIA/voice/models/modelname/model.pth", (optional: voice model for rvc)
    - "rvc_opts":{"index_path":"/path/to/MIA/voice/models/modelname/model.index","version":"v2"},
    - "rvc_params":{"f0method":"pm"},  (for these see python-rvc docu)
    - "rvc_enabled":false, (enable,disable rvc)
    - "tts_device":"cpu", (device for tts, either cuda/cpu, for some reason cpu worked better ...)
    - "gfx_version":"11.0.0", (flag used for roc)
    - "voice_sample":"/path/to/MIA/voice/samples/miku_vocals.wav",(voice sample for tts voice cloning)
    - "history_file":"memories.json" (MIA's memory)

- Configure expressions.json with expressions and associated .mp4 files
- Set the emotions and the expressions associated with it in emotion_map.json. When the AI provides an emotion the proper video is loaded.
- Some configurations are found in `constants.py` which can be adjusted like textbox settings.
    - CFG_FILE = "setup_cfg.json" (cfg file to use)
    - LOG_FNAME = "mia.log" (log file)
    - BACKGROUND_COLOR = "#000000" 
    - TEXT_COLOR = "#6cf542" 
    - FONT_SIZE = "16px" 
    - TEXT_ROWS = 15 
    - TEXT_COLS = 60
    - TEXT_FONT = '"Brush Script MT", cursive'
- Generate expressions with `python -m python3.10 -i speak.py setup_cfg.json expressions.json --generate`
    
- First time: go into the MIA folder and run `install_lama.py setup_cfg.json -f`. The docker will start. You can chat a little and then exit with `/bye`.

Usage:
===================

- Start: Activate virtual env and start: `python -m MIA`.
- Open Webbrowser on `localhost:<web_port>`
- *Hint*: KDE has a web browser plugin as desktop app ...


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
- Add shutdown button
- Make Package
- Make better input field.
- Clock
- zip memories or find another way (let the LLM extract for example)
