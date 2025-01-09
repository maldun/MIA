==============================
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
- Configure setup_cfg.json to your liking (my settings are included as an example)
- Configure expressions.json with expressions and associated .mp4 files
- First time: go into the MIA folder and run `install_lama.py setup_cfg.json -f`. The docker will start. You can chat a little and then exit with `/bye`.

Usage:
===================

- Start: Activate virtual env and start: `python -m MIA`.
- Open Webbrowser on `localhost:<web_port>`
- *Hint*: KDE has a web browser plugin as desktop app ...

Notes
==================
- It may be necessary to reset before if docker makes problem ... e.g. with podman do `podman system reset`
- Setup rocm properly and install with `python3.10 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0`
- Also set your GLX proeprly with AMD cards, in my case it was: `os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"` check the correct one for your card!
- Downloads of bark can be faulty re-download fine_2.pt manually if you want to use bark for tts.

Programm Structure
==================

- Ollama Container running as service.
- speaker Server: Handles TTS requests (currently file based, http server planned for later).
- memories.json: Memory of MIA, shouldn't be too big even after longer time.
- webapp: Flask app to handle communication with Computer
- HTML Site: Web interface.
- vids and expressions.json: Set the emotions 

Tasks
=====

- Communication: Communication with the user
- Expression of feelings
- Talking with the user (via TTS)
