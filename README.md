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

- python 3.10 to 3.12 (3.12 recommended; Python 3.10 reaches its end of life in October 2026). The core runs on 3.10, 3.11 and 3.12 (tested); the voice extras (RVC, Coqui TTS, torch) are in `requirements-voice.txt`: RVC needs 3.10, Coqui and torch 2.4.1 stop at 3.12
- rocm/cuda (works with CPU but slow....)
- docker/podman
- (Tested on Fedora 40; should work on other systems though)
- Some mp4 files for expression of feelings (set in expressions.json; can be extended shortened as needed)
- a .wav voice sample of your choice (set under option `voice_sample` in `setup_cfg.json`).
- background .jpg file of your choice (into `templates/static/background.jpg`).
- optional: a .pth model for rvc.
(I made my own with blender and collected other stuff, but I don't share due to copyright reasons. Private use is one thing, publishing another ..., but the internet is full of fun stuff so go ahead.)

### Create virtual environment (example)
- `python3.12 -m venv <venvfolder>/mia` (or `python3.11`, `python3.10`)
- `source <venvfolder>/mia/bin/activate`
- `python -m pip install -r requirements.txt` (the core: web app, chat, research, Kokoro voice) and `python -m pip install --no-deps kokoro-onnx`
- optional, for RVC, Coqui TTS and GPU torch: `python -m pip install -r requirements-voice.txt` (and the ROCm/CUDA steps below)

### Install ROCM/CUDA (Fedora; only for the voice extras, Ollama brings its own GPU runtime in its container):
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
- `python3.10 -m pip install -e .` (RVC: Python 3.10)

### Install Kokoro TTS (default tts engine):
- `python -m pip install espeakng-loader phonemizer onnxruntime "numpy==1.26.4"` (all in `requirements.txt`)
- `python -m pip install --no-deps kokoro-onnx` (it asks for numpy>=2, but works with 1.26 which rvc/coqui need)
- Download `kokoro-v1.0.onnx` and `voices-v1.0.bin` from https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 into `voice/models/kokoro/`
- Compare voices and pitch shifts with `python voice_lab.py` (writes samples to `voice/samples/lab/`)

### Clone
- `git clone https://github.com/maldun/MIA.git`
- Go into MIA folder
- Install/Check requirements in requirements.txt (`python -m pip install -r requirements.txt`; the full freeze of the development machine is `requirements-freeze-py310.txt`)

### Configuration
- The real configuration of a machine is `setup_cfg.json`. It is **not in version control** (a deployment on another machine would otherwise fight with the one in git at every commit). The tracked template is
  `setup_cfg.example.json`: it lists every option (84 at the moment; the values are those of the development machine, adjust paths, models and ports). On the first start `python -m MIA` copies the example to
  `setup_cfg.json` and says so; after that only your file is read. When a new version of MIA brings new options, they appear in the example; a test (`tests/test_config.py`) keeps the example complete.
  Two options mean something different when they are *present*, so they are not in the example: `editor_token` and `chat_token` (see below).
  After an update, `python config.py` lists the options of the example that your `setup_cfg.json` does not have yet (it only reports; the defaults apply until you add them).
- Configure setup_cfg.json to your liking (the list below describes the options; "optional" options are in the example with their default):

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
    - "gestures_dir":"data/gestures", (optional: gestures made with the gesture editor, one json file per gesture, shared by all devices like the presets; changing them needs the same token)
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
    - "rvc_pad":0.25, "tts_warmup":true, "rvc_cache_index":true, (optional: speed-ups of the voice. `tts_warmup` and `rvc_cache_index` are on by default and do not change the sound. `rvc_pad` is NOT set by default (RVC's own 1 s padding is used): RVC pads every sentence on both sides before converting it and renders the padding too, so `"rvc_pad":0.25` makes it much faster, but it may change the sound a little (a hollow sound was reported), listen before keeping it. The warm-up renders one short sentence at start, so the first answer is not slowed down by loading RVC's helper models. The RVC index (several hundred MB) is read once instead of for every sentence. Measure with `python tools/tts_benchmark.py --models-root <MIA folder>`; on a Ryzen 9 5900X: 3.2 s per sentence before, 2.2-2.5 s after, real-time factor 1.08 -> 0.74-0.83, first sentence 5.3 s -> 1.8 s. `"cpu_threads":6` halves the CPU load and is still faster than speaking (0.83), 12 is the fastest (0.74))
    - "rvc_whistle_hz":700, (optional, on by default: the MikuAI voice model produces a whistle, a pure tone of about 700 Hz on some vowels (100-250 ms, in almost every sentence); no RVC setting removes it and the Kokoro audio does not have it. After the conversion MIA removes the tone with a narrow filter, only where it is present (about 60 ms per sentence); normal speech is untouched. `0` switches it off. For another voice model find its frequency with `python tools/find_whistle.py <converted wav files>` (the frequency that comes back in several different sentences); details in `voice_fix.py`.)
    - "voice_effect":"anime", (optional, off by default: a simple voice changer on the Kokoro audio instead of (or on top of) RVC, about 100 times faster than speaking and without the artifacts of a trained model. Use it with `"rvc_enabled":false`. Presets: `anime` (pitch +5 semitones, formants +13%, a little sparkle), `anime_robot` (the same with flatter intonation, ring modulation and a metallic resonance), `robot` (monotone, ring modulation, lo-fi), `tiny` (+8 semitones, formants +22%), `off`. Single settings can be changed: `{"preset":"anime","pitch_semitones":7,"formant_shift":1.18}`; all settings are described in `voice_effects.py` (pitch_semitones, formant_shift, pitch_range 0 = monotone, ring_hz/ring_mix, comb_ms/comb_mix, bitcrush, sparkle_db). A typo stops the speech server with a message. Compare with `python tools/tts_benchmark.py --no-rvc --effect anime --save <folder>`; measured on a Ryzen 9 5900X: 0.84 s per sentence and real-time factor 0.28 (Kokoro alone) against 3.0 s and 1.03 with RVC)
    - "chat_log":"data/chat_log.jsonl", (optional: the conversation as the chat page shows it, one JSON object per line; separate from MIA's memory, so dreaming does not touch it. Stays on this machine; delete the file or use the "clear" API to remove the history)
    - "chat_log_max_messages":10000, (optional: the oldest messages are dropped above this number)
    - "chat_queue":1, (optional: how many messages may wait while MIA is answering; more are refused with a hint)
    - "chat_rate_per_minute":10, (optional: messages per minute and connection, 0 = no limit)
    - "chat_token":"a secret", (optional: token for deleting the conversation over the API; default is the editor token)
    - "moods_file":"moods.json", "mood_hold_minutes":10, (optional: the phrases of the mood line (edit them to match MIA's personality) and how long a mood stays after the last answer)
    - "expression_model":"gemma4:12b-it-qat", "expression_temperature":0.7, "feedback_log":"data/feedback_log.jsonl", (optional: expressions from a description in the expression editor. The model defaults to the one MIA is using right now (same options, so Ollama does not reload anything); the log keeps what you kept, edited or rejected, and is used as examples in later requests)
    - "tailscale":true, "public_hosts":["mia.example.ts.net"], (optional, off by default: publish MIA in your tailnet at start with `tailscale serve`; `public_hosts` are more host names pages may be loaded from. The tailnet name of this machine is found automatically if Tailscale is installed)
    - "gfx_version":"11.0.0", (flag used for roc)
    - "voice_sample":"/path/to/MIA/voice/samples/miku_vocals.wav",(voice sample for tts voice cloning)
    - "history_file":"memories.json" (MIA's memory)
    - "search_backends":["searxng","duckduckgo"], "searxng_port":8590, "searxng_url":null, "searxng_autostart":true, (the web search of the research: backends in order, the SearXNG port (the same key is read by `tools/searxng/run.sh`) or its full address for another machine, and whether MIA starts the existing container `mia-searxng` at launch when SearXNG does not answer; see ui/README.md "Core, phase 5j")
    - "search_results":8, "search_results_shown":5, "web_timeout":[5,15], "web_max_bytes":2000000, "web_max_chars":30000, (how many results a search keeps and `/search` shows; connect and read timeout in seconds; the largest page body and the longest page text the fetcher takes)
    - "research_pipeline":null, (the pipeline of the library that `/research` runs; null = the one the skill `research` names, now `research.escalate@1`)
    - "sandbox_backend":"auto", "sandbox_degrade":false, "sandbox_image":"localhost/mia-sandbox:1", (where scripts of the checks run: bubblewrap or podman, chosen per operation when "auto"; whether a weaker sandbox may be used when the strong one is missing; the image of the podman sandbox, `tools/sandbox/build_image.sh`)
    - "skills_dir":"skills", "library_dir":"library", "user_library_dir":"data/library", "library_index":"data/library.sqlite", "runs_dir":"data/runs", (the skills, the library of nodes and pipelines (shipped and your own), its index and the run log)
    - "chat_token", "editor_token": (not in the example, because their presence changes the behaviour: `editor_token` set to a text is the token for the expression editor, `""` switches the check off, missing = a random token in `editor_token_file`; `chat_token` defaults to the editor token)
    - "editor_token_file":"data/editor_token.txt", "rvc_whistle_hz":700, "rvc_cache_index":true, "tts_warmup":true, "rvc_pad":null, (see the entries above for these)

- The character on the page is a 3D model (Godot web export, see `ui/README.md`). Build it once with `ui/tools/build_web.sh`; MIA serves it under `/character/` and shows it in the page. It replaces the old pre-rendered videos.
- Configure expressions.json: every expression has a `preset` (expression of the character, see `ui/godot/presets/library.json`; default: the expression key itself), the spoken `text` and the `voice` clip (`null` = no voice clip yet).
- Set the emotions and the expressions associated with it in emotion_map.json. When the AI provides an emotion the character makes the proper expression (face, arm gesture) and the voice clip is played. The mouth moves while MIA's voice plays. **Important** The example should be the minimal set of emotion. Don't remove one of them! Emotions can be added: the prompt for the AI is built from this file (new expressions need a preset with the same name or a `preset` entry).
- What MIA's voice says (`speech_text.py`): the text for the speech is filtered. Text in single asterisks (`*smiles*`) is an expression or action and is **not spoken**
  (MIA's prompt tells the model to use it only for that, and never for emphasis); `**bold**`, `_italic_`, headings, lists, quotes, code, tables and links lose their marks
  (link texts stay, URLs and images are dropped). MIA is told to write "times" for multiplication; as a safety net `2*3` and `2 * 3` between numbers are read as "2 times 3". While an answer is still streaming, an action that is not closed yet is held back as well. The chat page still shows the full
  text. The rule is part of the calibration message (`EMOTION_QUESTION` in `communicator.py`); it reaches the model at the next start (calibration runs at every start).
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
- From outside the home network (optional, not needed at home) use Tailscale, which gives a trusted HTTPS address inside your tailnet without opening any port:
  install it (`curl -fsSL https://tailscale.com/install.sh | sh`, `sudo tailscale up`), turn on MagicDNS and HTTPS Certificates in the Tailscale admin console
  (the machine name then appears in public certificate logs), and run `ui/tools/remote.sh up` (or set `"tailscale": true` in `setup_cfg.json` and MIA does it at start
  and stops it at the end). The address is `https://<machine>.<tailnet>.ts.net/`; `ui/tools/remote.sh status|down` show and stop it. Never use `tailscale funnel` (public).
  Everyone in your tailnet can then open the chat (there is no login); presets, expression generation and "clear history" still need the editor token.
  Set `"host":"127.0.0.1"` to listen on this computer only (then the LAN HTTPS proxy no longer works). Not tried against a real Tailscale here; the commands are from Tailscale's docs.
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

### Voice clips: greeting at startup and "Hey, listen!"

The old "How can I help you?" intro is gone. In `setup_cfg.json`:
- `intro_sounds`: clips of which one is picked at random when a page loads (`Navi_Hello1`, `Navi_Hey1`). `intro_sound` is only the fallback when none of them exists.
- `attention_sounds` and `attention_chance` (0..1, 0 = never): before MIA starts talking on her own (the hourly time update) she calls out with one of these (`hey_listen`, `Navi_Hey1`) with that chance.
Missing files are skipped. Add your own clips to either list.
